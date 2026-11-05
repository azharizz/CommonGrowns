import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass, fields


def text(value, name, limit=6000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"{name} must be nonempty text (max {limit} characters)")
    return value


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value):
        raise ValueError("Invalid identifier")
    return value


def bounds(low, high):
    if any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in (low, high)):
        raise ValueError("Bounds must be finite nonnegative numbers")
    if low > high:
        raise ValueError("Minimum exceeds maximum")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


@dataclass(frozen=True)
class Opportunity:
    opp_id: str
    company: str
    seeks: str
    offers: str
    budget_min: float | None
    budget_max: float | None
    region: str
    categories: list[str]
    audience: str
    status: str = "open"

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict) or set(data) - {f.name for f in fields(cls)}:
            raise ValueError("Only the documented matchable fields are accepted")
        try:
            result = cls(**data)
        except TypeError as exc:
            raise ValueError("Missing matchable fields") from exc
        identifier(result.opp_id)
        for name in ("company", "seeks", "offers", "region", "audience"):
            text(getattr(result, name), name)
        if result.budget_min is not None or result.budget_max is not None:
            bounds(result.budget_min, result.budget_max)
        if not isinstance(result.categories, list) or not 1 <= len(result.categories) <= 20:
            raise ValueError("Provide 1–20 categories")
        for category in result.categories:
            text(category, "category", 100)
        if result.status not in ("open", "closed"):
            raise ValueError("Status must be open or closed")
        return result

    def to_dict(self):
        return asdict(self)


def private_overlap(left, right):
    for item in (left, right):
        if not isinstance(item, dict) or set(item) != {"min", "max"}:
            raise ValueError("Private range requires only min and max")
        bounds(item["min"], item["max"])
    width = min(left["max"], right["max"]) - max(left["min"], right["min"])
    span = max(left["max"], right["max"]) - min(left["min"], right["min"])
    return {"compatible": width >= 0,
            "overlap": "none" if width < 0 else "narrow" if width <= span * .25 else "broad"}


FIT_KEYS = ("business", "commercial", "capability", "strategic")
MATCH_KEYS = {"opp_id", "company", "verdict", "headline", "fits", "gains", "risks",
              "missing_info", "pitch_angle", "next_step"}


def validate_match(data, opp_id, company):
    if not isinstance(data, dict) or set(data) != MATCH_KEYS:
        raise ValueError("Invalid match fields")
    if data["opp_id"] != opp_id or data["company"] != company:
        raise ValueError("Match identifies the wrong counterpart")
    if data["verdict"] not in ("strong", "good", "weak", "none"):
        raise ValueError("Invalid match verdict")
    for name in ("headline", "pitch_angle", "next_step"):
        text(data[name], name)
    if not isinstance(data["fits"], dict) or set(data["fits"]) != set(FIT_KEYS):
        raise ValueError("Every match needs all four fits")
    for fit in data["fits"].values():
        if not isinstance(fit, dict) or set(fit) != {"verdict", "evidence"}:
            raise ValueError("Invalid fit fields")
        if fit["verdict"] not in ("yes", "partial", "no", "n/a"):
            raise ValueError("Invalid fit verdict")
        string_list(fit["evidence"], "evidence", required=True)
    if not isinstance(data["gains"], dict) or set(data["gains"]) != {"source", "counterpart"}:
        raise ValueError("Describe both sides' gains")
    for gain in data["gains"].values():
        text(gain, "gain")
    for name in ("risks", "missing_info"):
        string_list(data[name], name)
    return data


def string_list(value, name, required=False):
    if not isinstance(value, list) or len(value) > 30 or (required and not value):
        raise ValueError(f"{name} must be a list of up to 30 strings")
    for item in value:
        text(item, name)
