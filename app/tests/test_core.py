import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock

from commongrown.models import Opportunity, private_overlap, validate_match
from commongrown.state import State
from commongrown.exchange import Exchange, publish
from commongrown.briefs import BriefFactory, CreditGate, VerifiedBrief


def opportunity(**changes):
    data = dict(opp_id="A1", company="NusaConf", seeks="Sponsors for a tech event",
                offers="Reach 5,000 tech attendees", budget_min=50000,
                budget_max=100000, region="Indonesia", categories=["Cloud", "AI"],
                audience="Tech professionals", status="open")
    return Opportunity.from_dict(data | changes)


def match():
    return dict(opp_id="B1", company="CloudKita", verdict="strong",
                headline="Cloud audience and public budgets align.",
                fits={key: {"verdict": "yes", "evidence": ["Public opportunity"]}
                      for key in ("business", "commercial", "capability", "strategic")},
                gains={"source": "Sponsor funding", "counterpart": "Brand exposure"},
                risks=["Confirm category exclusivity"], missing_info=["Attendee seniority"],
                pitch_angle="Reach Indonesian tech buyers", next_step="Confirm audience")


class ModelTests(unittest.TestCase):
    def test_rejects_private_fields_and_invalid_budgets(self):
        for change in ({"private_notes": "secret"}, {"budget_min": -1},
                       {"budget_min": 100001}, {"budget_max": float("nan")},
                       {"budget_min": True}, {"budget_min": None},
                       {"opp_id": "../secret"}, {"verified_level": "L2"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                opportunity(**change)

    def test_private_overlap_has_no_numbers_and_handles_touching_ranges(self):
        self.assertEqual(private_overlap({"min": 40, "max": 100}, {"min": 60, "max": 90}),
                         {"compatible": True, "overlap": "broad"})
        self.assertEqual(private_overlap({"min": 40, "max": 60}, {"min": 60, "max": 90}),
                         {"compatible": True, "overlap": "narrow"})
        self.assertEqual(private_overlap({"min": 40, "max": 50}, {"min": 60, "max": 90}),
                         {"compatible": False, "overlap": "none"})
        with self.assertRaises(ValueError):
            private_overlap({"min": 5, "max": 1}, {"min": 0, "max": 9})

    def test_llm_output_is_validated(self):
        self.assertEqual(validate_match(match(), "B1", "CloudKita"), match())
        for change in ({"opp_id": "wrong"}, {"verdict": "amazing"}, {"fits": {}},
                       {"secret": "unexpected"}, {"risks": "not a list"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_match(match() | change, "B1", "CloudKita")


class StateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = State(Path(self.temp.name) / "accounts.db")
        self.state.seed_accounts()
        self.state.register_opportunity(opportunity())
        self.state.register_opportunity(opportunity(opp_id="B1", company="CloudKita"))

    def test_seed_is_idempotent_and_topup_validates(self):
        self.state.topup("CloudKita", 2)
        self.state.seed_accounts()
        self.assertEqual(self.state.account("CloudKita")["credits"], 2)
        for amount in (-1, 0, True, 1.5):
            with self.assertRaises(ValueError):
                self.state.topup("CloudKita", amount)

    def test_publish_requires_exact_approved_draft_and_owner(self):
        opp = opportunity()
        digest = self.state.draft(opp, "Rina")
        exchange = Mock()
        with self.assertRaises(ValueError):
            publish(self.state, exchange, opp, digest)
        with self.assertRaises(ValueError):
            self.state.approve(digest, "Budi", "approve", "switch-message-1")
        with self.assertRaises(ValueError):
            self.state.approve(digest, "Rina", "maybe", "switch-message-1")
        self.state.approve(digest, "Rina", "approve", "switch-message-1")
        with self.assertRaises(ValueError):
            publish(self.state, exchange, opportunity(offers="Changed"), digest)
        publish(self.state, exchange, opp, digest)
        exchange.upsert.assert_called_once_with(opp, "L1")

    def test_new_draft_revokes_old_approval(self):
        old = opportunity()
        digest = self.state.draft(old, "Rina")
        self.state.approve(digest, "Rina", "approve", "m1")
        self.state.draft(opportunity(offers="Revised"), "Rina")
        with self.assertRaises(ValueError):
            publish(self.state, Mock(), old, digest)

    def test_republishing_changed_terms_requires_new_interest(self):
        self.state.interest("A1", "B1", "NusaConf", "Rina", "m1")
        self.state.interest("A1", "B1", "CloudKita", "Budi", "m2")
        self.state.register_opportunity(opportunity())
        self.assertTrue(self.state.is_mutual("A1", "B1"))
        self.state.register_opportunity(opportunity(budget_min=70000))
        self.assertFalse(self.state.is_mutual("A1", "B1"))

    def test_mutual_interest_and_shared_document_approval(self):
        self.assertFalse(self.state.interest("A1", "B1", "NusaConf", "Rina", "m1"))
        with self.assertRaises(ValueError):
            self.state.interest("A1", "B1", "CloudKita", "Rina", "m2")
        with self.assertRaises(ValueError):
            self.state.require_mutual("A1", "B1")
        self.assertTrue(self.state.interest("B1", "A1", "CloudKita", "Budi", "m2"))
        self.state.require_mutual("A1", "B1")
        with self.assertRaises(ValueError):
            self.state.interest("A1", "B1", "SecureNusa", "seed-c", "m3")
        self.state.bind_room("A1", "B1", "switch-room-123")
        payload = {"position": "Discuss published terms", "questions": ["Speaking slot?"]}
        for company, actor in (("NusaConf", "Rina"), ("CloudKita", "Budi")):
            fingerprint = self.state.stage_shared("A1", "B1", company, actor, payload)
            with self.assertRaises(ValueError):
                self.state.shared_context("A1", "B1")
            self.state.approve_shared("A1", "B1", company, actor, fingerprint, "m4")
        self.assertEqual(len(self.state.shared_context("A1", "B1")["positions"]), 2)
        self.state.withdraw("A1", "B1", "NusaConf", "Rina")
        with self.assertRaises(ValueError):
            self.state.require_mutual("A1", "B1")

    def test_credit_gate_refunds_failure_and_replays_success(self):
        product = Mock(cost=3, kind="verified")
        product.generate.side_effect = RuntimeError("LLM failed")
        gated = CreditGate(product, self.state)
        with self.assertRaises(RuntimeError):
            gated.deliver("NusaConf", "request-1", "A1:B1")
        self.assertEqual(self.state.account("NusaConf")["credits"], 10)
        product.generate.side_effect = None
        product.generate.return_value = {"brief": "Approved public facts"}
        first = gated.deliver("NusaConf", "request-1", "A1:B1")
        self.assertEqual(first, gated.deliver("NusaConf", "request-1", "A1:B1"))
        self.assertEqual(self.state.account("NusaConf")["credits"], 7)
        self.assertEqual(product.generate.call_count, 2)
        with self.assertRaises(ValueError):
            gated.deliver("NusaConf", "request-1", "A1:C1")

    def test_locked_brief_does_no_work(self):
        product = Mock(cost=1, kind="full")
        result = CreditGate(product, self.state).deliver("CloudKita", "r1", "B1:A1")
        self.assertTrue(result["locked"])
        product.generate.assert_not_called()

    def test_range_check_needs_separate_consent_from_both_sides(self):
        with self.assertRaises(ValueError):
            self.state.range_consent("A1", "B1", "NusaConf", "Rina", "m1")
        self.state.interest("A1", "B1", "NusaConf", "Rina", "m1")
        self.state.interest("A1", "B1", "CloudKita", "Budi", "m2")
        self.state.range_consent("A1", "B1", "NusaConf", "Rina", "m3")
        with self.assertRaises(ValueError):
            self.state.require_range_consent("A1", "B1")
        self.state.range_consent("A1", "B1", "CloudKita", "Budi", "m4")
        self.state.require_range_consent("A1", "B1")
        self.state.withdraw("A1", "B1", "NusaConf", "Rina")
        self.state.interest("A1", "B1", "NusaConf", "Rina", "m5")
        with self.assertRaises(ValueError):
            self.state.require_range_consent("A1", "B1")

    def test_concurrent_requests_cannot_overspend(self):
        product = Mock(cost=3, kind="verified")
        product.generate.return_value = {"brief": "public"}
        gate = CreditGate(product, self.state)
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda i: gate.deliver("NusaConf", f"r{i}", "A1:B1"), range(4)))
        self.assertEqual(sum(bool(r.get("locked")) for r in results), 1)
        self.assertEqual(self.state.account("NusaConf")["credits"], 1)


class ExchangeTests(unittest.TestCase):
    def test_two_documents_and_fixed_public_metadata(self):
        collection = Mock()
        Exchange(collection).upsert(opportunity(), "L1")
        args = collection.upsert.call_args.kwargs
        self.assertEqual(args["ids"], ["A1:seeks", "A1:offers"])
        self.assertEqual([m["kind"] for m in args["metadatas"]], ["seeks", "offers"])
        self.assertNotIn("private", json.dumps(args))

    def test_retrieval_filters_and_reverse_query(self):
        collection = Mock()
        collection.count.return_value = 12
        collection.query.return_value = {"ids": [[]], "metadatas": [[]], "distances": [[]]}
        Exchange(collection).candidates(opportunity())
        calls = collection.query.call_args_list
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0].kwargs["query_texts"], [opportunity().seeks])
        self.assertEqual(calls[1].kwargs["query_texts"], [opportunity().offers])
        query = json.dumps(calls[0].kwargs["where"])
        for value in ('"offers"', '"open"', '"$lte": 100000', '"$gte": 50000', '"Indonesia"'):
            self.assertIn(value, query)

    def test_factory_uses_verified_decorator_and_rejects_unknown(self):
        ranker = Mock(return_value=match())
        product = BriefFactory.create("verified", ranker=ranker,
                                      verification={"level": "L2", "evidence": ["Demo flag"]})
        self.assertIsInstance(product, VerifiedBrief)
        self.assertEqual(product.cost, 3)
        self.assertEqual(product.generate()["verification"]["level"], "L2")
        with self.assertRaises(ValueError):
            BriefFactory.create("premium", ranker=ranker)


if __name__ == "__main__":
    unittest.main()
