import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import Mock, patch

from commongrown.cli import brief, parser_for, seed
from commongrown.models import Opportunity
from commongrown.state import State
from test_core import opportunity


class CommandTests(unittest.TestCase):
    def test_all_entrypoints_have_help(self):
        for command in ("seed", "draft", "publish", "search", "brief", "overlap", "credits", "deal"):
            self.assertIn("usage:", parser_for(command).format_help())

    def test_public_fixtures_have_six_opportunities_and_no_private_fields(self):
        path = Path(__file__).resolve().parents[1] / "seeds" / "opportunities.json"
        data = json.loads(path.read_text())
        rows = [Opportunity.from_dict(item) for item in data]
        self.assertEqual(len(rows), 6)
        self.assertEqual(len({row.company for row in rows}), 5)
        self.assertEqual([row.opp_id for row in rows if row.company == "CloudKita"], ["B1", "B2"])
        serialized = json.dumps(data).lower()
        for secret in ("ceiling", "floor", "discount", "cash is tight", "18%"):
            self.assertNotIn(secret, serialized)

    def test_seed_preserves_live_edits_and_excludes_a_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            state = State(Path(directory) / "accounts.db")
            edited = opportunity(opp_id="B1", company="CloudKita", offers="Live approved edits")
            exchange = Mock()

            def existing(key):
                if key == "B1":
                    return edited
                raise ValueError("missing")

            exchange.get.side_effect = existing
            with patch("commongrown.cli.private_path", side_effect=lambda company: Path(directory) / f"{company}.json"):
                result = seed(state, exchange, False)
                notes = (Path(directory) / "NusaConf.json").read_text()
                seed(state, exchange, False)
                self.assertEqual(notes, (Path(directory) / "NusaConf.json").read_text())
            self.assertNotIn("A1", result["seeded"])
            self.assertNotIn("B1", [call.args[0].opp_id for call in exchange.upsert.call_args_list])

    @patch("commongrown.cli.AgentModel")
    def test_zero_credit_cli_brief_never_calls_model(self, create_model):
        with tempfile.TemporaryDirectory() as directory:
            state = State(Path(directory) / "accounts.db")
            state.seed_accounts()
            source = opportunity(opp_id="B1", company="CloudKita")
            target = opportunity()
            for item in (source, target):
                state.register_opportunity(item)
            exchange = Mock()
            exchange.get.side_effect = [source, target]
            args = Namespace(source="B1", counterpart="A1", actor="Budi", request_id="r1")
            self.assertTrue(brief(state, exchange, args, "verified")["locked"])
            create_model.assert_not_called()
