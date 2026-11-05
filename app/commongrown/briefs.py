import json

from .models import canonical, digest, identifier, private_overlap


class FullBrief:
    kind = "full"
    cost = 1

    def __init__(self, ranker):
        self.ranker = ranker

    def generate(self):
        return self.ranker()


class VerifiedBrief:
    """Decorator: enrich the same full brief with broker-held verification."""
    kind = "verified"
    cost = 3

    def __init__(self, wrapped, verification):
        self.wrapped = wrapped
        self.verification = verification

    def generate(self):
        return self.wrapped.generate() | {"verification": self.verification}


class RangeBrief:
    kind = "range"
    cost = 2

    def __init__(self, ranges):
        self.ranges = ranges

    def generate(self):
        return private_overlap(*self.ranges())


class BriefFactory:
    """Factory: select the requested product without branching in its caller."""
    @staticmethod
    def create(kind, *, ranker=None, verification=None, ranges=None):
        if kind == "full" and ranker is not None:
            return FullBrief(ranker)
        if kind == "verified" and ranker is not None and verification is not None:
            return VerifiedBrief(FullBrief(ranker), verification)
        if kind == "range" and ranges is not None:
            return RangeBrief(ranges)
        raise ValueError("Choose full, verified, or range with its required input")


class CreditGate:
    """Decorator: atomic, idempotent charging for any brief product."""
    def __init__(self, wrapped, state):
        self.wrapped = wrapped
        self.state = state

    def deliver(self, company, request_id, context):
        identifier(request_id)
        fingerprint = digest({"kind": self.wrapped.kind, "context": context})
        with self.state.connect() as db:
            # shortcut: serialize brief generation on SQLite, use reservations if throughput grows.
            db.execute("BEGIN IMMEDIATE")
            previous = db.execute("SELECT * FROM orders WHERE company=? AND request_id=?",
                                  (company, request_id)).fetchone()
            if previous:
                if previous["fingerprint"] != fingerprint:
                    raise ValueError("Request ID was already used for a different brief")
                return json.loads(previous["result"])
            account = db.execute("SELECT credits FROM accounts WHERE company=?", (company,)).fetchone()
            if account is None:
                raise ValueError("Unknown company")
            if account["credits"] < self.wrapped.cost:
                return {"locked": True, "credits": account["credits"], "cost": self.wrapped.cost,
                        "message": "Brief locked. Top up; match headlines remain free."}
            result = self.wrapped.generate()
            encoded = canonical(result)
            # Delivery means a durable, retrievable artifact; chat forwarding is retriable.
            db.execute("INSERT INTO orders VALUES (?, ?, ?, ?, ?)",
                       (company, request_id, fingerprint, self.wrapped.cost, encoded))
            db.execute("UPDATE accounts SET credits=credits-? WHERE company=?",
                       (self.wrapped.cost, company))
        return result
