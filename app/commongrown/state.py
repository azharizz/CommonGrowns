import json
import re
import sqlite3
import time
from contextlib import contextmanager, nullcontext
from pathlib import Path

from .models import canonical, digest, identifier, text


ACCOUNTS = [
    ("NusaConf", "Rina", "paid", 10, "L1"),
    ("CloudKita", "Budi", "paid", 0, "L2"),
    ("SecureNusa", "seed-c", "free", 0, "L0"),
    ("PromptWorks", "seed-d", "free", 0, "L0"),
    ("BatikMesin Supply", "seed-e", "free", 0, "L0"),
]


STARTER_CREDITS = 3
BUFFER_TTL = 24 * 3600      # raw messages are only input for the next summary, never an archive
BUFFER_PER_ROOM = 40
FACT_KINDS = ("need", "offer", "constraint", "fact")
MAX_FACTS = 60


def label(value):
    """Only anonymous labels are ever stored or shown as a fact's source."""
    return value if isinstance(value, str) and re.fullmatch(r"owner|member \d{1,3}", value) else "team"


class State:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS accounts (
                    company TEXT PRIMARY KEY, owner TEXT NOT NULL, plan TEXT NOT NULL,
                    credits INTEGER NOT NULL CHECK(credits >= 0), verified_level TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS drafts (
                    opp_id TEXT PRIMARY KEY, company TEXT NOT NULL, digest TEXT NOT NULL,
                    payload TEXT NOT NULL, approved_by TEXT, message_id TEXT);
                CREATE TABLE IF NOT EXISTS opportunities (
                    opp_id TEXT PRIMARY KEY, company TEXT NOT NULL, revision TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS interests (
                    pair TEXT NOT NULL, company TEXT NOT NULL, actor TEXT NOT NULL,
                    message_id TEXT NOT NULL, PRIMARY KEY(pair, company));
                CREATE TABLE IF NOT EXISTS orders (
                    company TEXT NOT NULL, request_id TEXT NOT NULL, fingerprint TEXT NOT NULL,
                    cost INTEGER NOT NULL, result TEXT NOT NULL,
                    PRIMARY KEY(company, request_id));
                CREATE TABLE IF NOT EXISTS rooms (
                    pair TEXT PRIMARY KEY, room_id TEXT NOT NULL UNIQUE);
                CREATE TABLE IF NOT EXISTS range_consents (
                    pair TEXT NOT NULL, company TEXT NOT NULL, message_id TEXT NOT NULL,
                    PRIMARY KEY(pair, company));
                CREATE TABLE IF NOT EXISTS groups (
                    room_id TEXT PRIMARY KEY, company TEXT NOT NULL UNIQUE, owner TEXT NOT NULL,
                    mode TEXT NOT NULL DEFAULT 'mention' CHECK(mode IN ('mention', 'listen')));
                CREATE TABLE IF NOT EXISTS evidence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, room_id TEXT NOT NULL, message_id TEXT NOT NULL,
                    sender TEXT NOT NULL, body TEXT NOT NULL, created REAL NOT NULL, UNIQUE(room_id, message_id));
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, company TEXT NOT NULL, key TEXT NOT NULL,
                    kind TEXT NOT NULL, value TEXT NOT NULL, public INTEGER NOT NULL,
                    source TEXT NOT NULL, snippet TEXT NOT NULL, updated REAL NOT NULL, UNIQUE(company, key));
                CREATE TABLE IF NOT EXISTS conflicts (
                    company TEXT NOT NULL, key TEXT NOT NULL, note TEXT NOT NULL, created REAL NOT NULL,
                    PRIMARY KEY(company, key));
                CREATE TABLE IF NOT EXISTS members (
                    room_id TEXT NOT NULL, sender TEXT NOT NULL, label TEXT NOT NULL, PRIMARY KEY(room_id, sender));
                CREATE TABLE IF NOT EXISTS watch (
                    room_id TEXT PRIMARY KEY, stage TEXT NOT NULL DEFAULT 'idle',
                    digest TEXT, marker INTEGER NOT NULL DEFAULT 0, checked REAL NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS shared (
                    pair TEXT NOT NULL, company TEXT NOT NULL, payload TEXT NOT NULL,
                    digest TEXT NOT NULL, approved_by TEXT, message_id TEXT,
                    PRIMARY KEY(pair, company));
            """)
        self.path.chmod(0o600)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=180)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def seed_accounts(self):
        with self.connect() as db:
            db.executemany("INSERT OR IGNORE INTO accounts VALUES (?, ?, ?, ?, ?)", ACCOUNTS)

    def register_opportunity(self, opportunity, db=None):
        self.account(opportunity.company)
        revision = digest(opportunity.to_dict())
        with (self.connect() if db is None else nullcontext(db)) as db:
            row = db.execute("SELECT company, revision FROM opportunities WHERE opp_id=?", (opportunity.opp_id,)).fetchone()
            if row and row["company"] != opportunity.company:
                raise ValueError("Opportunity belongs to another company")
            if row and row["revision"] != revision:
                for table in ("interests", "shared", "range_consents"):
                    db.execute(f"DELETE FROM {table} WHERE instr(':' || pair || ':', ?) > 0",
                               (f":{opportunity.opp_id}:",))
            db.execute("INSERT INTO opportunities VALUES (?, ?, ?) ON CONFLICT(opp_id) DO UPDATE SET revision=excluded.revision",
                       (opportunity.opp_id, opportunity.company, revision))

    # --- self-serve company groups (a chat group = one company) ---
    def group(self, room_id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM groups WHERE room_id=?", (room_id,)).fetchone()
        return dict(row) if row else None

    def register_group(self, room_id, company, owner, claim_existing=False):
        """Link a chat group to a company. The linking sender becomes the owner (only they can approve/spend)."""
        text(room_id, "room ID", 300)
        text(owner, "owner", 300)
        company = text(company, "company name", 60).strip()
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 ._&-]{1,59}", company):
            raise ValueError("Company name: 2-60 letters, digits, spaces or . _ & -")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM groups WHERE room_id=?", (room_id,)).fetchone():
                raise ValueError("This group is already linked to a company")
            account = db.execute("SELECT * FROM accounts WHERE lower(company)=lower(?)", (company,)).fetchone()
            if account:
                company = account["company"]
                if not claim_existing:
                    raise ValueError("That company already exists; ask the operator to link it")
            if db.execute("SELECT 1 FROM groups WHERE company=?", (company,)).fetchone():
                raise ValueError("That company is already linked to another group")
            if account:
                db.execute("UPDATE accounts SET owner=? WHERE company=?", (owner, company))
            else:
                db.execute("INSERT INTO accounts VALUES (?, ?, 'free', ?, 'L0')", (company, owner, STARTER_CREDITS))
            db.execute("INSERT INTO groups(room_id, company, owner) VALUES (?, ?, ?)", (room_id, company, owner))
        return self.account(company)

    def set_mode(self, room_id, mode):
        if mode not in ("mention", "listen"):
            raise ValueError("Mode must be listen or mention")
        with self.connect() as db:
            db.execute("UPDATE groups SET mode=? WHERE room_id=?", (mode, room_id))

    def member_label(self, room_id, sender, db):
        """Stable, anonymous per-group label: 'owner' or 'member N'. Real chat IDs are never shown to the model."""
        row = db.execute("SELECT label FROM members WHERE room_id=? AND sender=?", (room_id, sender)).fetchone()
        if row:
            return row["label"]
        group = db.execute("SELECT owner FROM groups WHERE room_id=?", (room_id,)).fetchone()
        if group and group["owner"] == sender:
            label = "owner"
        else:
            label = "member %d" % (db.execute("SELECT COUNT(*) FROM members WHERE room_id=? AND label!='owner'", (room_id,)).fetchone()[0] + 1)
        db.execute("INSERT INTO members VALUES (?, ?, ?)", (room_id, sender, label))
        return label

    def add_evidence(self, room_id, message_id, sender, body):
        """Buffer one message as input for the next summary. Not an archive: cleared once summarized."""
        body = body.strip()[:2000] if isinstance(body, str) else ""
        if not body or body.startswith("/") or not isinstance(message_id, str) or not isinstance(sender, str):
            return False
        now = time.time()
        with self.connect() as db:
            label = self.member_label(room_id, sender, db)
            db.execute("INSERT OR IGNORE INTO evidence(room_id, message_id, sender, body, created) VALUES (?,?,?,?,?)",
                       (room_id, message_id[:300], label, body, now))
            db.execute("DELETE FROM evidence WHERE created < ?", (now - BUFFER_TTL,))
            db.execute("""DELETE FROM evidence WHERE room_id=? AND id NOT IN
                (SELECT id FROM evidence WHERE room_id=? ORDER BY id DESC LIMIT ?)""",
                       (room_id, room_id, BUFFER_PER_ROOM))
        return True

    def buffer(self, room_id):
        with self.connect() as db:
            rows = db.execute("SELECT id, sender, body FROM evidence WHERE room_id=? ORDER BY id", (room_id,)).fetchall()
        return [{"id": r["id"], "member": r["sender"], "body": r["body"][:500]} for r in rows]

    def clear_buffer(self, room_id, upto):
        with self.connect() as db:
            db.execute("DELETE FROM evidence WHERE room_id=? AND id<=?", (room_id, upto))

    def facts(self, company, public_only=False):
        with self.connect() as db:
            rows = db.execute("SELECT key, kind, value, public, source, snippet FROM facts WHERE company=?"
                              + (" AND public=1" if public_only else "") + " ORDER BY kind, key", (company,)).fetchall()
        return [dict(r) for r in rows]

    def conflicts(self, company):
        with self.connect() as db:
            return [dict(r) for r in db.execute("SELECT key, note FROM conflicts WHERE company=? ORDER BY key", (company,))]

    def apply_facts(self, company, facts, conflicts):
        """Merge a summary update. Same key = newer value replaces the old one (corrections win)."""
        now = time.time()
        with self.connect() as db:
            for f in facts:
                if f["kind"] not in FACT_KINDS or not re.fullmatch(r"[a-z0-9_]{2,40}", f["key"]):
                    continue
                db.execute("""INSERT INTO facts(company, key, kind, value, public, source, snippet, updated)
                    VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(company, key) DO UPDATE SET kind=excluded.kind,
                    value=excluded.value, public=excluded.public, source=excluded.source,
                    snippet=excluded.snippet, updated=excluded.updated""",
                           (company, f["key"], f["kind"], text(f["value"], "fact", 300).strip(), 1 if f["public"] else 0,
                            label(f["member"]), str(f["snippet"])[:200], now))
                db.execute("DELETE FROM conflicts WHERE company=? AND key=?", (company, f["key"]))
            for c in conflicts:
                if re.fullmatch(r"[a-z0-9_]{2,40}", c["key"]):
                    db.execute("INSERT OR REPLACE INTO conflicts VALUES (?,?,?,?)",
                               (company, c["key"], text(c["note"], "conflict", 300).strip(), now))
            db.execute("""DELETE FROM facts WHERE company=? AND id NOT IN
                (SELECT id FROM facts WHERE company=? ORDER BY updated DESC, id DESC LIMIT ?)""", (company, company, MAX_FACTS))

    def watch(self, room_id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM watch WHERE room_id=?", (room_id,)).fetchone()
        return dict(row) if row else {"room_id": room_id, "stage": "idle", "digest": None, "marker": 0, "checked": 0.0}

    def set_watch(self, room_id, **fields):
        current = self.watch(room_id) | fields
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO watch VALUES (?, ?, ?, ?, ?)",
                       (room_id, current["stage"], current["digest"], current["marker"], current["checked"]))

    def new_evidence(self, room_id):
        """(messages since the last proactive check, newest evidence id)."""
        marker = self.watch(room_id)["marker"]
        with self.connect() as db:
            count = db.execute("SELECT COUNT(*) FROM evidence WHERE room_id=? AND id>?", (room_id, marker)).fetchone()[0]
            newest = db.execute("SELECT COALESCE(MAX(id), 0) FROM evidence WHERE room_id=?", (room_id,)).fetchone()[0]
        return count, newest

    def forget(self, room_id, company):
        with self.connect() as db:
            n = db.execute("DELETE FROM facts WHERE company=?", (company,)).rowcount
            db.execute("DELETE FROM conflicts WHERE company=?", (company,))
            db.execute("DELETE FROM evidence WHERE room_id=?", (room_id,))
            db.execute("DELETE FROM members WHERE room_id=?", (room_id,))
        return n

    def status(self, company, room_id=None):
        account = self.account(company)
        facts = self.facts(company)
        with self.connect() as db:
            opps = [r["opp_id"] for r in db.execute("SELECT opp_id FROM opportunities WHERE company=?", (company,))]
            group = db.execute("SELECT mode FROM groups WHERE company=?", (company,)).fetchone()
        return {"company": company, "plan": account["plan"], "credits": account["credits"],
                "verified_level": account["verified_level"], "mode": group["mode"] if group else None,
                "facts_known": len(facts), "facts_private": sum(1 for f in facts if not f["public"]),
                "open_questions": len(self.conflicts(company)), "opportunities": opps}

    def participants(self, left, right):
        self.pair(left, right)
        with self.connect() as db:
            rows = db.execute("SELECT company FROM opportunities WHERE opp_id IN (?, ?)", (left, right)).fetchall()
        companies = {r["company"] for r in rows}
        if len(rows) != 2 or len(companies) != 2:
            raise ValueError("Choose published opportunities from two different companies")
        return companies

    def account(self, company):
        with self.connect() as db:
            row = db.execute("SELECT * FROM accounts WHERE company = ?", (company,)).fetchone()
        if row is None:
            raise ValueError("Unknown company; run seed.py first")
        return dict(row)

    def owner(self, company, actor):
        if self.account(company)["owner"] != actor:
            raise ValueError("Only the company's linked human can approve this action")

    def topup(self, company, amount):
        if type(amount) is not int or not 0 < amount <= 1000000:
            raise ValueError("Top-up must be a positive integer up to 1,000,000")
        self.account(company)
        with self.connect() as db:
            db.execute("UPDATE accounts SET credits = credits + ? WHERE company = ?", (amount, company))
        return self.account(company)

    def draft(self, opportunity, actor):
        self.owner(opportunity.company, actor)
        payload = opportunity.to_dict()
        fingerprint = digest(payload)
        with self.connect() as db:
            existing = db.execute("SELECT company FROM drafts WHERE opp_id = ?", (opportunity.opp_id,)).fetchone()
            if existing and existing["company"] != opportunity.company:
                raise ValueError("Opportunity belongs to another company")
            db.execute("""INSERT INTO drafts VALUES (?, ?, ?, ?, NULL, NULL)
                ON CONFLICT(opp_id) DO UPDATE SET digest=excluded.digest, payload=excluded.payload,
                approved_by=NULL, message_id=NULL""",
                       (opportunity.opp_id, opportunity.company, fingerprint, canonical(payload)))
        return fingerprint

    def approve(self, fingerprint, actor, response, message_id):
        if response.strip().lower() != "approve":
            raise ValueError("Explicit 'approve' is required")
        text(message_id, "Switch message ID", 300)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM drafts WHERE digest = ?", (fingerprint,)).fetchone()
            if row is None:
                raise ValueError("Draft does not exist or has changed")
            self.owner(row["company"], actor)
            db.execute("UPDATE drafts SET approved_by=?, message_id=? WHERE digest=?",
                       (actor, message_id, fingerprint))

    def require_approved(self, opportunity, fingerprint):
        with self.connect() as db:
            row = db.execute("SELECT * FROM drafts WHERE opp_id=?", (opportunity.opp_id,)).fetchone()
        if (not row or not row["approved_by"] or row["digest"] != fingerprint
                or digest(opportunity.to_dict()) != fingerprint):
            raise ValueError("This exact draft needs human approval before publication")

    @staticmethod
    def pair(left, right):
        identifier(left)
        identifier(right)
        if left == right:
            raise ValueError("Choose two different opportunities")
        return ":".join(sorted((left, right)))

    def interest(self, left, right, company, actor, message_id):
        self.owner(company, actor)
        if company not in self.participants(left, right):
            raise ValueError("Company is not a participant in this match")
        text(message_id, "Switch message ID", 300)
        pair = self.pair(left, right)
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO interests VALUES (?, ?, ?, ?)",
                       (pair, company, actor, message_id))
        return self.is_mutual(left, right)

    def is_mutual(self, left, right):
        with self.connect() as db:
            rows = db.execute("SELECT company FROM interests WHERE pair=?", (self.pair(left, right),)).fetchall()
        return {r["company"] for r in rows} == self.participants(left, right)

    def require_mutual(self, left, right):
        if not self.is_mutual(left, right):
            raise ValueError("Both companies must opt in before sharing or opening a deal room")

    def withdraw(self, left, right, company, actor):
        self.owner(company, actor)
        with self.connect() as db:
            db.execute("DELETE FROM interests WHERE pair=? AND company=?", (self.pair(left, right), company))
            db.execute("DELETE FROM shared WHERE pair=?", (self.pair(left, right),))
            db.execute("DELETE FROM range_consents WHERE pair=?", (self.pair(left, right),))

    def range_consent(self, left, right, company, actor, message_id):
        self.owner(company, actor)
        self.require_mutual(left, right)
        if company not in self.participants(left, right):
            raise ValueError("Company is not a participant")
        text(message_id, "Switch message ID", 300)
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO range_consents VALUES (?, ?, ?)",
                       (self.pair(left, right), company, message_id))

    def require_range_consent(self, left, right):
        self.require_mutual(left, right)
        with self.connect() as db:
            rows = db.execute("SELECT company FROM range_consents WHERE pair=?", (self.pair(left, right),)).fetchall()
        if {r["company"] for r in rows} != self.participants(left, right):
            raise ValueError("Both humans must separately consent to the broker's private-range check")

    def bind_room(self, left, right, room_id):
        self.require_mutual(left, right)
        text(room_id, "Switch room ID", 300)
        with self.connect() as db:
            existing = db.execute("SELECT room_id FROM rooms WHERE pair=?", (self.pair(left, right),)).fetchone()
            if existing and existing["room_id"] != room_id:
                raise ValueError("Pair already has a Switch room")
            db.execute("INSERT OR IGNORE INTO rooms VALUES (?, ?)", (self.pair(left, right), room_id))

    def stage_shared(self, left, right, company, actor, payload):
        self.owner(company, actor)
        if company not in self.participants(left, right):
            raise ValueError("Company is not a participant in this match")
        self.require_mutual(left, right)
        if not isinstance(payload, dict) or set(payload) != {"position", "questions"}:
            raise ValueError("Shared draft accepts only position and questions")
        text(payload["position"], "position")
        from .models import string_list
        string_list(payload["questions"], "questions")
        fingerprint = digest(payload)
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO shared VALUES (?, ?, ?, ?, NULL, NULL)",
                       (self.pair(left, right), company, canonical(payload), fingerprint))
        return fingerprint

    def approve_shared(self, left, right, company, actor, fingerprint, message_id):
        self.owner(company, actor)
        self.require_mutual(left, right)
        text(message_id, "Switch message ID", 300)
        with self.connect() as db:
            cursor = db.execute("UPDATE shared SET approved_by=?, message_id=? WHERE pair=? AND company=? AND digest=?",
                                (actor, message_id, self.pair(left, right), company, fingerprint))
            if cursor.rowcount != 1:
                raise ValueError("Shared draft does not exist or has changed")

    def shared_context(self, left, right):
        self.require_mutual(left, right)
        pair = self.pair(left, right)
        with self.connect() as db:
            room = db.execute("SELECT room_id FROM rooms WHERE pair=?", (pair,)).fetchone()
            rows = db.execute("SELECT company, payload FROM shared WHERE pair=? AND approved_by IS NOT NULL", (pair,)).fetchall()
        if not room or len(rows) != 2:
            raise ValueError("Bind a Switch room and approve both positions first")
        return {"room_id": room["room_id"], "positions": {r["company"]: json.loads(r["payload"]) for r in rows}}
