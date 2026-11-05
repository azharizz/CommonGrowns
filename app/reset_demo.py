"""Wipe all live state and load the background companies for a clean demo. Run with the worker stopped.
Keeps the Switch identity and checkpoint. Usage: COMMONGROWN_DATA=/var/lib/commongrown python reset_demo.py"""
import json
import shutil
import sqlite3

from commongrown.config import DATA, ROOT
from commongrown.exchange import Exchange
from commongrown.models import Opportunity
from commongrown.state import State

EXTRA = [("TechSprint Expo", "seed-f", "free", 0, "L0"), ("NimbusID", "seed-g", "free", 0, "L1"),
         ("Samudra Systems", "seed-h", "free", 0, "L2"), ("SiamPack Distribution", "seed-i", "free", 0, "L1")]

for name in ("accounts.db", "chroma", "companies", "shared"):
    path = DATA / name
    shutil.rmtree(path, ignore_errors=True) if path.is_dir() else path.unlink(missing_ok=True)
state = State(DATA / "accounts.db")
state.seed_accounts()
with state.connect() as db:
    db.executemany("INSERT OR IGNORE INTO accounts VALUES (?, ?, ?, ?, ?)", EXTRA)
exchange = Exchange.open(DATA / "chroma")
for item in json.load(open(ROOT / "seeds" / "demo_background.json")):
    opp = Opportunity.from_dict(item)
    exchange.upsert(opp, state.account(opp.company)["verified_level"])
    state.register_opportunity(opp)
print("reset ok; background opportunities:", [i["opp_id"] for i in json.load(open(ROOT / "seeds" / "demo_background.json"))])
