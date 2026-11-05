import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from commongrown.worker import EXTRACT_SCHEMA, INTAKE_SCHEMA, Worker, authorize
from commongrown.state import State
from test_core import opportunity


class Fixture(unittest.TestCase):
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



class WorkerTests(Fixture):
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


def fact(key, value, kind="need", public=True, member="owner", snippet="said so"):
    return {"key": key, "kind": kind, "value": value, "public": public, "member": member, "snippet": snippet}


class GroupBase(Fixture):
    """A company chat group: the bot is added, /setup links it, people just talk."""
    def say(self, body, sender="tg-owner", room="group-1", message=None, addressed=True, name=None):
        self.n = getattr(self, "n", 0) + 1
        payload = {"sender": sender, "message_id": message or f"g{self.n}", "body": body, "addressed": addressed}
        if name:
            payload["sender_name"] = name
        return self.worker.handle({"room_id": room, "payload": payload})

    def chat(self, n=3, sender="tg-member"):
        for i in range(n):
            self.say(f"we need sponsors for our summit {i}", addressed=False, sender=sender)

    def setUp(self):
        super().setUp()
        self.extract = {"facts": [], "conflicts": [], "suggest": False, "summary": ""}
        self.draft = {"reply": "Drafted.", "draft": dict(self.a.to_dict(), opp_id="X", company="whoever")}
        self.prompts = []
        self.llm.generate.side_effect = self.fake

    def fake(self, prompt, schema):
        self.prompts.append(prompt)
        if schema is EXTRACT_SCHEMA:
            return self.extract
        if schema is INTAKE_SCHEMA:
            return self.draft
        raise AssertionError("unexpected schema")


class SelfServeGroupTests(GroupBase):
    def test_unlinked_group_gets_onboarding_and_ignores_chatter(self):
        self.assertIsNone(self.say("hello", addressed=False))
        self.assertIn("/setup", self.say("hi bot")["reply"])
        self.llm.generate.assert_not_called()

    def test_setup_creates_company_with_starter_credits_owner_and_listens(self):
        self.assertIn("Acme Corp", self.say("/setup Acme Corp")["reply"])
        status = self.say("/status")
        self.assertEqual((status["credits"], status["mode"]), (3, "listen"))
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

    def test_mention_mode_reads_nothing(self):
        self.say("/setup Acme Corp")
        self.say("/mode mention")
        self.chat(5)
        self.assertEqual(self.state.buffer("group-1"), [])
        self.llm.generate.assert_not_called()

    def test_bots_own_messages_are_not_buffered(self):
        self.say("/setup Acme Corp")
        self.say("Linked this group", sender="@commongrown:x", addressed=False, name="commongrown")
        self.assertEqual(self.state.buffer("group-1"), [])

    def test_fromchat_without_any_facts_is_rejected(self):
        self.say("/setup Acme Corp")
        with self.assertRaises(ValueError):
            self.say("/fromchat")


class KnowledgeTests(GroupBase):
    """The company's requirements and facts are what we keep; the chat is not."""
    def setUp(self):
        super().setUp()
        self.say("/setup Acme Corp")
        self.extract = {"facts": [fact("seeks", "Sponsors for NusaTech Summit"),
                                  fact("audience", "About 5,000 tech professionals", "fact", member="member 1")],
                        "conflicts": [], "suggest": False, "summary": ""}

    def test_messages_become_facts_and_the_chat_is_deleted(self):
        self.chat(3)
        self.assertEqual([f["key"] for f in self.state.facts("Acme Corp")], ["audience", "seeks"])
        self.assertEqual(self.state.buffer("group-1"), [])           # nothing but the summary is kept
        self.assertEqual(self.say("/status")["facts_known"], 2)

    def test_model_sees_stable_member_labels_never_real_chat_ids(self):
        self.chat(2, sender="tg-member")
        self.say("we have a booth to offer", addressed=False, sender="tg-owner")
        prompt = self.prompts[-1]
        self.assertIn("member 1", prompt)
        self.assertIn("owner", prompt)
        self.assertNotIn("tg-member", prompt)
        self.assertNotIn("tg-owner", prompt)

    def test_newer_statement_replaces_the_older_value(self):
        self.chat(3)
        self.extract = {"facts": [fact("audience", "About 8,000 tech professionals", "fact")], "conflicts": [],
                        "suggest": False, "summary": ""}
        self.state.set_watch("group-1", checked=0)
        self.chat(3)
        audience = [f for f in self.state.facts("Acme Corp") if f["key"] == "audience"]
        self.assertEqual([f["value"] for f in audience], ["About 8,000 tech professionals"])

    def test_fact_sources_are_only_anonymous_labels(self):
        self.extract["facts"] = [fact("seeks", "Sponsors", member="@switch-telegram-ec9:server"),
                                 fact("audience", "5,000", "fact", member="member 2")]
        self.chat(3)
        self.assertEqual({f["key"]: f["source"] for f in self.state.facts("Acme Corp")},
                         {"seeks": "team", "audience": "member 2"})

    def test_confidential_facts_are_kept_private_everywhere(self):
        self.extract = {"facts": [fact("seeks", "Sponsors for the summit"), fact("floor", "Our floor is 40k USD", "constraint", public=False),
                                  fact("region", "Indonesia", "fact"), fact("audience", "5,000 people", "fact"),
                                  fact("offers", "Booth and keynote", "offer")], "conflicts": [], "suggest": False, "summary": ""}
        self.chat(3)
        view = self.say("/facts")
        self.assertEqual(view["facts_view"]["private_count"], 1)
        self.assertNotIn("floor", json.dumps(view["facts_view"]["facts"]))
        from commongrown.render import render
        self.assertNotIn("40k", render(view))
        self.assertIn("confidential", render(view))
        self.say("/fromchat")
        self.assertNotIn("40k", self.prompts[-1])                      # the drafting model never sees it either

    def test_conflicts_are_flagged_not_guessed_and_clear_when_settled(self):
        self.extract = {"facts": [], "conflicts": [{"key": "budget_range", "note": "owner says 50k, member 1 says 80k"}],
                        "suggest": False, "summary": ""}
        self.chat(3)
        self.assertEqual(self.say("/status")["open_questions"], 1)
        from commongrown.render import render
        self.assertIn("owner says 50k", render(self.say("/facts")))
        self.extract = {"facts": [fact("budget_range", "50k to 80k USD", "constraint")], "conflicts": [], "suggest": False, "summary": ""}
        self.state.set_watch("group-1", checked=0)
        self.chat(3)
        self.assertEqual(self.say("/status")["open_questions"], 0)

    def test_forget_wipes_facts_and_pending_messages(self):
        self.chat(3)
        self.say("one more thing", addressed=False)
        self.assertIn("Forgot", self.say("/forget")["reply"])
        self.assertEqual(self.state.facts("Acme Corp"), [])
        self.assertEqual(self.state.buffer("group-1"), [])

    def test_failed_summary_keeps_messages_for_a_retry(self):
        self.llm.generate.side_effect = RuntimeError("model down")
        with self.assertRaises(RuntimeError):
            self.chat(3)
        self.assertEqual(len(self.state.buffer("group-1")), 3)

    def test_fromchat_builds_the_draft_from_facts_with_forced_identity(self):
        self.extract["facts"] = [fact("seeks", "Sponsors"), fact("offers", "Booth", "offer", snippet="we can give a booth")]
        self.chat(3)
        staged = self.say("/fromchat")
        self.assertEqual(staged["publish_exactly"]["company"], "Acme Corp")
        self.assertNotEqual(staged["publish_exactly"]["opp_id"], "A1")
        self.assertIn("owner: said so", staged["evidence"])
        self.exchange.upsert.assert_not_called()
        self.say("/approve " + staged["approval"])
        self.exchange.upsert.assert_called_once()
        self.assertEqual(self.say("/status")["opportunities"], [staged["publish_exactly"]["opp_id"]])


class ProactiveTests(GroupBase):
    """People just talk; the bot notices a need, asks, and only the owner's 'yes' moves things forward."""
    def setUp(self):
        super().setUp()
        self.say("/setup Acme Corp")
        self.extract = {"facts": [fact("seeks", "Sponsors for NusaTech Summit"), fact("offers", "Booth", "offer")],
                        "conflicts": [], "suggest": True, "summary": "you're looking for sponsors for NusaTech Summit"}

    def test_quiet_until_enough_messages_and_only_asks_once(self):
        self.assertIsNone(self.say("we need sponsors", addressed=False))
        self.llm.generate.assert_not_called()
        self.say("we need sponsors 2", addressed=False)
        ask = self.say("we need sponsors 3", addressed=False)
        self.assertIn("looking for sponsors", ask["reply"])
        self.llm.generate.reset_mock()
        self.chat(6)                                                  # already asked: no repeated suggestions
        self.assertEqual(self.say("/status")["facts_known"], 2)

    def test_no_suggestion_when_nothing_concrete(self):
        self.extract = {"facts": [], "conflicts": [], "suggest": False, "summary": ""}
        self.say("lunch?", addressed=False)
        self.say("sure", addressed=False)
        self.assertIsNone(self.say("pizza", addressed=False))

    def test_only_owner_yes_counts_and_nothing_publishes_without_two_yeses(self):
        self.chat(3)
        self.assertIsNone(self.say("yes", sender="tg-member", addressed=False))     # not the owner
        staged = self.say("yes", addressed=False)                                   # first yes: draft only
        self.assertIn("publish_exactly", staged)
        self.exchange.upsert.assert_not_called()
        self.exchange.candidates.return_value = []
        self.exchange.get.side_effect = lambda key: self.a                          # the newly published opportunity
        done = self.say("yes", addressed=False)                                     # second yes: publish + matches
        self.exchange.upsert.assert_called_once()
        self.assertIn("published", done)
        self.assertEqual(done["headlines"], [])

    def test_no_cancels_and_stops_asking_for_a_while(self):
        self.chat(3)
        self.assertIn("won't publish", self.say("no", addressed=False)["reply"])
        self.llm.generate.reset_mock()
        self.chat(5)                                                                 # cooldown: no new model call
        self.llm.generate.assert_not_called()
        self.exchange.upsert.assert_not_called()

    def test_unaddressed_model_failure_never_publishes(self):
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
             "facts_known": 2, "facts_private": 1, "open_questions": 0, "opportunities": []},
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
        self.assertIn("• need sponsors", out)
        self.assertIn("Reply “yes”", out)
        self.assertNotIn('"seeks"', out)
