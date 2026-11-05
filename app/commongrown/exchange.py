import json

from .models import Opportunity


class Exchange:
    def __init__(self, collection):
        self.collection = collection

    @classmethod
    def open(cls, path):
        import chromadb
        client = chromadb.PersistentClient(path=str(path))
        return cls(client.get_or_create_collection("opportunities"))

    def upsert(self, opportunity, verified_level):
        if verified_level not in ("L0", "L1", "L2"):
            raise ValueError("Invalid verification level")
        data = opportunity.to_dict()
        metadata = {key: value for key, value in data.items()
                    if key not in ("seeks", "offers", "categories") and value is not None}
        metadata.update(categories=json.dumps(opportunity.categories),
                        verified_level=verified_level,
                        budget_known=opportunity.budget_min is not None)
        # Store only the allowlisted public model; never an intake transcript.
        metadata["public_json"] = json.dumps(data)
        self.collection.upsert(
            ids=[f"{opportunity.opp_id}:seeks", f"{opportunity.opp_id}:offers"],
            documents=[opportunity.seeks, opportunity.offers],
            metadatas=[metadata | {"kind": kind} for kind in ("seeks", "offers")])

    def get(self, opp_id):
        result = self.collection.get(ids=[f"{opp_id}:seeks"], include=["metadatas"])
        if not result["metadatas"]:
            raise ValueError("Opportunity not published")
        return Opportunity.from_dict(json.loads(result["metadatas"][0]["public_json"]))

    def candidates(self, source, *, strict=True, limit=10):
        if source.status != "open":
            raise ValueError("Source opportunity is closed")
        count = self.collection.count()
        if not count:
            return []
        constraints = [{"status": "open"}, {"company": {"$ne": source.company}}]
        if strict:
            constraints.append({"region": source.region})
            if source.budget_min is not None:
                constraints.append({"$or": [
                    {"budget_known": False},
                    {"$and": [{"budget_min": {"$lte": source.budget_max}},
                              {"budget_max": {"$gte": source.budget_min}}]}]})
        found = {}
        for kind, query in (("offers", source.seeks), ("seeks", source.offers)):
            result = self.collection.query(query_texts=[query], n_results=min(limit, count),
                                           where={"$and": constraints + [{"kind": kind}]},
                                           include=["metadatas", "distances"])
            for metadata, distance in zip(result["metadatas"][0], result["distances"][0]):
                opp_id = metadata["opp_id"]
                entry = found.setdefault(opp_id, {"opportunity": json.loads(metadata["public_json"]),
                                                  "forward_distance": None, "reverse_distance": None})
                entry["forward_distance" if kind == "offers" else "reverse_distance"] = distance
        return sorted(found.values(), key=lambda row: sum(
            row[key] if row[key] is not None else 2.0
            for key in ("forward_distance", "reverse_distance")))[:limit]


def publish(state, exchange, opportunity, fingerprint):
    with state.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        state.require_approved(opportunity, fingerprint)
        # Lock approval changes while embedding and writing the exact reviewed draft.
        state.register_opportunity(opportunity, db=db)
        exchange.upsert(opportunity, state.account(opportunity.company)["verified_level"])
    return {"published": opportunity.opp_id, "approval": fingerprint}
