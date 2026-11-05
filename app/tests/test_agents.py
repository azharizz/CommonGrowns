import unittest
from unittest.mock import Mock

from commongrown.ai import Matcher, prepare_meeting
from test_core import match, opportunity


class AgentTests(unittest.TestCase):
    def test_matcher_rejects_fabricated_company_and_no_fit_is_allowed(self):
        llm = Mock()
        matcher = Matcher(llm)
        target = opportunity(opp_id="B1", company="CloudKita", budget_min=60000, budget_max=120000)
        llm.generate.return_value = match() | {"company": "Invented"}
        with self.assertRaises(ValueError):
            matcher.rank(opportunity(), target)
        llm.generate.return_value = match() | {"verdict": "none"}
        self.assertEqual(matcher.rank(opportunity(), target)["verdict"], "none")

    def test_hard_budget_conflict_cannot_be_strong(self):
        llm = Mock()
        llm.generate.return_value = match()
        target = opportunity(opp_id="B1", company="CloudKita", budget_min=5000, budget_max=10000)
        result = Matcher(llm).rank(opportunity(), target)
        self.assertEqual(result["verdict"], "weak")
        self.assertEqual(result["fits"]["commercial"]["verdict"], "no")

    def test_meeting_output_requires_all_deliverables(self):
        llm = Mock()
        llm.generate.return_value = {"draft_proposal": "Draft", "sticking_points": {"NusaConf": ["Price"], "CloudKita": ["Audience"]},
                                     "open_questions": ["Speaking slot?"], "agenda": ["Confirm objectives", "Agree next steps"]}
        context = {"positions": {"NusaConf": {}, "CloudKita": {}}, "room_id": "room"}
        result = prepare_meeting(llm, context)
        self.assertEqual(result["status"], "draft_for_human_review")
        llm.generate.return_value = {"draft_proposal": "incomplete"}
        with self.assertRaises(ValueError):
            prepare_meeting(llm, context)
