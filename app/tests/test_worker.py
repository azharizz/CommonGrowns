import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from commongrown.worker import Worker, authorize
from commongrown.state import State
from test_core import opportunity


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = State(self.root / "accounts.db")
        self.state.seed_accounts()
        self.a = opportunity()
        self.b = opportunity(opp_id="B1", company="CloudKita")
        for opp in (self.a, self.b):
            self.state.register_opportunity(opp)
        self.config = {"users": {"user-rina": "NusaConf", "user-budi": "CloudKita"},
                       "rooms": {"private-a": {"kind": "private", "company": "NusaConf"},
                                 "private-b": {"kind": "private", "company": "CloudKita"},
                                 "exchange": {"kind": "exchange"},
                                 "deal": {"kind": "deal", "opportunities": ["A1", "B1"]}}}
        self.exchange = Mock()
        self.exchange.get.side_effect = lambda key: {"A1": self.a, "B1": self.b}[key]
        self.llm = Mock()
        self.llm.generate.return_value = {"reply": "Please review the public draft", "draft": None}
        self.worker = Worker(self.state, self.exchange, self.llm, self.config, self.root)

    def event(self, sender="user-rina", room="private-a", body="Hello", message="m1"):
        return {"room_id": room, "payload": {"sender": sender, "message_id": message,
                "body": body, "addressed": True}}

    def test_identity_comes_from_trusted_sender_not_message_company(self):
        for sender, room in (("user-budi", "private-a"), ("unknown", "private-a"), ("user-rina", "unknown")):
            with self.assertRaises(ValueError):
                authorize(self.config, self.state, sender, room)
        result = authorize(self.config, self.state, "user-rina", "private-a")
        self.assertEqual(result.company, "NusaConf")

    def test_private_histories_never_cross_companies_or_rooms(self):
        self.worker.handle(self.event(body="RINA_ONLY_SECRET", message="m1"))
        self.worker.handle(self.event(sender="user-budi", room="private-b", body="BUDI_ONLY_SECRET", message="m2"))
        prompt = self.llm.generate.call_args.args[0]
        self.assertNotIn("RINA_ONLY_SECRET", prompt)
        self.worker.handle(self.event(body="Continue", message="m3"))
        prompt = self.llm.generate.call_args.args[0]
        self.assertIn("RINA_ONLY_SECRET", prompt)
        self.assertNotIn("BUDI_ONLY_SECRET", prompt)
        self.assertTrue((self.root / "companies").is_dir())

    def test_public_room_never_loads_private_chat_and_blocks_paid_brief(self):
        self.worker.handle(self.event(body="RINA_ONLY_SECRET"))
        self.llm.reset_mock()
        with self.assertRaises(ValueError):
            self.worker.handle(self.event(room="exchange", body="/brief A1 B1 full", message="m2"))
        self.worker.handle(self.event(room="exchange", body="help", message="m3"))
        self.llm.generate.assert_not_called()

    def test_two_private_rooms_for_same_company_have_separate_histories(self):
        self.config["rooms"]["private-a-other"] = {"kind": "private", "company": "NusaConf"}
        self.worker.handle(self.event(body="FIRST_ROOM_ONLY"))
        self.worker.handle(self.event(room="private-a-other", body="New conversation", message="m2"))
        self.assertNotIn("FIRST_ROOM_ONLY", self.llm.generate.call_args.args[0])

    def test_successful_publication_requires_direct_human_approval(self):
        result = self.worker.handle(self.event(body="/draft " + json.dumps(self.a.to_dict())))
        self.exchange.upsert.assert_not_called()
        self.worker.handle(self.event(body="/approve " + result["approval"], message="m2"))
        self.exchange.upsert.assert_called_once_with(self.a, "L1")

    def test_retries_are_idempotent_and_changed_payload_is_rejected(self):
        first = self.worker.handle(self.event())
        self.assertEqual(first, self.worker.handle(self.event()))
        self.assertEqual(self.llm.generate.call_count, 1)
        with self.assertRaises(ValueError):
            self.worker.handle(self.event(body="changed"))

    def test_unaddressed_message_does_no_work(self):
        event = self.event()
        event["payload"]["addressed"] = False
        self.assertIsNone(self.worker.handle(event))
        self.llm.generate.assert_not_called()

    def test_deal_access_requires_mutual_interest_and_bound_room(self):
        with self.assertRaises(ValueError):
            authorize(self.config, self.state, "user-rina", "deal")
        self.state.interest("A1", "B1", "NusaConf", "Rina", "m1")
        self.state.interest("A1", "B1", "CloudKita", "Budi", "m2")
        with self.assertRaises(ValueError):
            authorize(self.config, self.state, "user-rina", "deal")
        self.state.bind_room("A1", "B1", "deal")
        self.assertEqual(authorize(self.config, self.state, "user-rina", "deal").kind, "deal")
        self.state.withdraw("A1", "B1", "NusaConf", "Rina")
        with self.assertRaises(ValueError):
            authorize(self.config, self.state, "user-rina", "deal")

    def test_draft_cannot_spoof_another_company(self):
        command = "/draft " + json.dumps(self.b.to_dict())
        with self.assertRaises(ValueError):
            self.worker.handle(self.event(body=command))
        self.exchange.upsert.assert_not_called()

    def test_private_notes_are_company_scoped_and_never_shared(self):
        self.worker.handle(self.event(body='/private {"notes":"RINA_PRIVATE","ranges":{}}'))
        self.worker.handle(self.event(body="continue", message="m2"))
        self.assertIn("RINA_PRIVATE", self.llm.generate.call_args.args[0])
        self.worker.handle(self.event(sender="user-budi", room="private-b", body="continue", message="m3"))
        self.assertNotIn("RINA_PRIVATE", self.llm.generate.call_args.args[0])

    def test_failed_generation_does_not_store_a_successful_turn(self):
        self.llm.generate.side_effect = RuntimeError("model unavailable")
        with self.assertRaises(RuntimeError):
            self.worker.handle(self.event())
        self.llm.generate.side_effect = None
        self.worker.handle(self.event())
        self.assertEqual(self.llm.generate.call_count, 2)


class SelfServeGroupTests(WorkerTests):
    """Add the bot to a group, link a company, listen, draft from chat."""
    def say(self, body, sender="tg-owner", room="group-1", message=None, addressed=True, name=None):
        self.n = getattr(self, "n", 0) + 1
        payload = {"sender": sender, "message_id": message or f"g{self.n}", "body": body, "addressed": addressed}
        if name:
            payload["sender_name"] = name
        return self.worker.handle({"room_id": room, "payload": payload})

    def test_unlinked_group_gets_onboarding_and_ignores_chatter(self):
        self.assertIsNone(self.say("hello", addressed=False))
        self.assertIn("/setup", self.say("hi bot")["reply"])
        self.llm.generate.assert_not_called()

    def test_setup_creates_company_with_starter_credits_and_owner(self):
        result = self.say("/setup Acme Corp")
        self.assertIn("Acme Corp", result["reply"])
        self.assertEqual(self.say("/status")["credits"], 3)
        self.assertEqual(self.state.group("group-1")["owner"], "tg-owner")
        with self.assertRaises(ValueError):          # not the owner
            self.say("/status", sender="tg-other")
        with self.assertRaises(ValueError):          # group already linked
            self.say("/setup Other Co")

    def test_cannot_take_existing_or_static_companies(self):
        for name in ("CloudKita", "cloudkita", "NusaConf"):
            with self.assertRaises(ValueError):
                self.say(f"/setup {name}", room="g-" + name)
        self.config["allow_claim_seeded"] = True      # demo flag: seeded companies only, never static users
        with self.assertRaises(ValueError):          # bound to user-rina, not this sender
            self.say("/setup NusaConf", room="g-x")
        self.assertIn("NusaConf", self.say("/setup NusaConf", sender="user-rina", room="g-z")["reply"])
        self.assertIn("SecureNusa", self.say("/setup securenusa", room="g-y")["reply"])

    def test_mention_mode_stores_nothing_and_listen_mode_gathers_evidence(self):
        self.say("/setup Acme Corp")                      # listening by default, after a visible notice
        self.say("/mode mention")
        self.say("we need sponsors", addressed=False)
        self.assertEqual(self.say("/status")["evidence_messages"], 0)
        self.assertIn("Listen mode ON", self.say("/mode listen")["reply"])
        self.say("we need sponsors for our conference", addressed=False)
        self.say("/hidden command text", addressed=False)
        self.assertEqual(self.say("/status")["evidence_messages"], 1)
        self.assertIn("Deleted 1", self.say("/forget")["reply"])
        self.assertEqual(self.say("/status")["evidence_messages"], 0)

    def test_bots_own_messages_are_not_evidence(self):
        self.say("/setup Acme Corp")
        self.say("/mode listen")
        self.say("Linked this group", sender="@commongrown:x", addressed=False, name="commongrown")
        self.assertEqual(self.say("/status")["evidence_messages"], 0)

    def test_fromchat_stages_draft_with_forced_identity_and_verified_quotes(self):
        self.say("/setup Acme Corp")
        self.say("/mode listen")
        self.say("We run a 500 person dev conference in Jakarta and need a sponsor", addressed=False)
        draft = dict(self.a.to_dict(), opp_id="A1", company="NusaConf")
        self.llm.generate.return_value = {"reply": "Found it.", "draft": draft,
                                          "evidence": ["need a sponsor", "invented quote"]}
        result = self.say("/fromchat")
        self.assertEqual(result["publish_exactly"]["company"], "Acme Corp")
        self.assertNotEqual(result["publish_exactly"]["opp_id"], "A1")
        self.assertEqual(result["evidence"], ["need a sponsor"])
        self.exchange.upsert.assert_not_called()
        self.say("/approve " + result["approval"])
        self.exchange.upsert.assert_called_once()
        self.assertEqual(self.say("/status")["opportunities"], [result["publish_exactly"]["opp_id"]])

    def test_fromchat_without_evidence_is_rejected(self):
        self.say("/setup Acme Corp")
        with self.assertRaises(ValueError):
            self.say("/fromchat")


class ProactiveTests(WorkerTests):
    """People just talk; the bot notices a need, asks, and only the owner's 'yes' moves things forward."""
    def say(self, body, sender="tg-owner", room="group-1", message=None, addressed=True, name=None):
        self.n = getattr(self, "n", 0) + 1
        payload = {"sender": sender, "message_id": message or f"g{self.n}", "body": body, "addressed": addressed}
        if name:
            payload["sender_name"] = name
        return self.worker.handle({"room_id": room, "payload": payload})

    def setUp(self):
        super().setUp()
        self.say("/setup Acme Corp")
        self.llm.generate.reset_mock()
        self.draft = dict(self.a.to_dict(), opp_id="X", company="whoever")

    def chat(self, n=3):
        for i in range(n):
            self.say(f"we need sponsors for our summit {i}", addressed=False, sender="tg-member")

    def detect(self, found=True):
        return {"found": found, "summary": "you're looking for sponsors for NusaTech Summit"}

    def test_setup_listens_by_default_with_a_notice(self):
        self.assertEqual(self.say("/status")["mode"], "listen")

    def test_quiet_until_enough_messages_and_only_asks_once(self):
        self.llm.generate.return_value = self.detect()
        self.assertIsNone(self.say("we need sponsors", addressed=False))
        self.llm.generate.assert_not_called()
        self.say("we need sponsors 2", addressed=False)
        ask = self.say("we need sponsors 3", addressed=False)
        self.assertIn("looking for sponsors", ask["reply"])
        self.llm.generate.reset_mock()
        self.chat(6)                                      # already asked: no repeated suggestions
        self.llm.generate.assert_not_called()

    def test_no_suggestion_when_nothing_concrete(self):
        self.llm.generate.return_value = self.detect(found=False)
        self.assertIsNone(self.say("lunch?", addressed=False))
        self.say("sure", addressed=False)
        self.assertIsNone(self.say("pizza", addressed=False))

    def test_only_owner_yes_counts_and_nothing_publishes_without_two_yeses(self):
        self.llm.generate.return_value = self.detect()
        self.chat(3)
        self.assertIsNone(self.say("yes", sender="tg-member", addressed=False))     # not the owner
        self.llm.generate.return_value = {"reply": "Found it.", "draft": self.draft, "evidence": ["need sponsors"]}
        staged = self.say("yes", addressed=False)                                   # first yes: draft only
        self.assertIn("publish_exactly", staged)
        self.exchange.upsert.assert_not_called()
        self.exchange.candidates.return_value = []
        self.exchange.get.side_effect = lambda key: self.a      # the newly published opportunity
        done = self.say("yes", addressed=False)                                     # second yes: publish + matches
        self.exchange.upsert.assert_called_once()
        self.assertIn("published", done)
        self.assertEqual(done["headlines"], [])

    def test_no_cancels_and_stops_asking_for_a_while(self):
        self.llm.generate.return_value = self.detect()
        self.chat(3)
        self.assertIn("won't publish", self.say("no", addressed=False)["reply"])
        self.llm.generate.reset_mock()
        self.chat(5)                                                                 # cooldown: no new model call
        self.llm.generate.assert_not_called()
        self.exchange.upsert.assert_not_called()

    def test_member_chatter_never_publishes_and_unaddressed_failures_stay_silent(self):
        self.llm.generate.side_effect = RuntimeError("model down")
        with self.assertRaises(RuntimeError):             # the transport layer swallows this for unaddressed chatter
            self.chat(3)
        self.exchange.upsert.assert_not_called()


class RenderTests(unittest.TestCase):
    def test_every_reply_shape_is_plain_text_not_json(self):
        from commongrown.render import render
        match = {"opp_id": "B1", "company": "CloudKita", "verdict": "strong", "headline": "Good fit", "retrieval": "qualified"}
        samples = [
            {"reply": "hello"},
            {"headlines": [match], "source": "A1"},
            {"headlines": [], "message": "No candidates found"},
            {"published": "A1", "approval": "h", "headlines": [match], "source": "A1"},
            {"company": "Acme", "plan": "free", "credits": 3, "verified_level": "L0", "mode": "listen",
             "evidence_messages": 2, "opportunities": []},
            {"locked": True, "credits": 0, "cost": 1, "message": "x"},
            {"compatible": True, "overlap": "broad"},
            {"mutual": False}, {"approved": True},
        ]
        for sample in samples:
            out = render(sample)
            self.assertTrue(out)
            self.assertNotIn("{", out)
        self.assertIn("Strong match", render(samples[1]))
        self.assertIn("/brief A1 <ID> full", render(samples[1]))
        self.assertIn("Published", render(samples[3]))

    def test_draft_shows_budget_and_quotes_without_json(self):
        from commongrown.render import render
        draft = {"opp_id": "G1", "company": "Acme", "seeks": "Sponsors", "offers": "Booth", "budget_min": 50000,
                 "budget_max": 100000, "region": "Indonesia", "categories": ["AI"], "audience": "5,000", "status": "open"}
        out = render({"publish_exactly": draft, "approval": "abc", "evidence": ["need sponsors"]})
        self.assertIn("$50,000–$100,000", out)
        self.assertIn("“need sponsors”", out)
        self.assertIn("Reply “yes”", out)
        self.assertNotIn('"seeks"', out)
