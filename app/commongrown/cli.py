import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
import sqlite3
import sys
from pathlib import Path

from .ai import AgentModel, Matcher, headline, prepare_meeting
from .briefs import BriefFactory, CreditGate
from .config import DATA, ROOT, private_path, read_json
from .exchange import Exchange, publish
from .models import Opportunity, digest
from .state import State


def parser_for(command):
    parser = argparse.ArgumentParser(description=f"CommonGrown {command} — local Switch broker tool")
    if command == "seed":
        parser.add_argument("--include-a", action="store_true", help="Publish fictional A1 too; omit for live consent demo")
    elif command == "draft":
        parser.add_argument("file")
        parser.add_argument("--actor", required=True)
    elif command == "publish":
        parser.add_argument("file")
        parser.add_argument("--approval", required=True, help="Exact draft SHA-256 shown to its owner")
        parser.add_argument("--actor", required=True)
        parser.add_argument("--response", required=True)
        parser.add_argument("--message-id", required=True, help="Observed Switch human approval message")
    elif command == "search":
        parser.add_argument("source")
        parser.add_argument("--counterpart", help="Explain a specific candidate, including a hard no")
        parser.add_argument("--near-misses", action="store_true", help="Include relaxed candidates as diagnostics")
    elif command in ("brief", "overlap"):
        parser.add_argument("source")
        parser.add_argument("counterpart")
        if command == "brief":
            parser.add_argument("--kind", choices=("full", "verified", "range"), default="full")
        parser.add_argument("--actor", required=True)
        parser.add_argument("--request-id", required=True, help="Stable ID; retry with the same ID to retrieve without recharging")
    elif command == "credits":
        parser.add_argument("company")
        parser.add_argument("--topup", type=int, help="Operator-only demo top-up")
    elif command == "deal":
        parser.add_argument("action", choices=("interest", "withdraw", "status", "bind-room", "share", "approve-share", "range-consent", "prepare"))
        parser.add_argument("source")
        parser.add_argument("counterpart")
        parser.add_argument("--company")
        parser.add_argument("--actor")
        parser.add_argument("--message-id")
        parser.add_argument("--room-id")
        parser.add_argument("--file")
        parser.add_argument("--approval")
    else:
        raise ValueError("Unknown command")
    return parser


def seed(state, exchange, include_a):
    state.seed_accounts()
    published = []
    for item in read_json(ROOT / "seeds" / "opportunities.json"):
        opportunity = Opportunity.from_dict(item)
        if opportunity.opp_id == "A1" and not include_a:
            continue
        try:
            opportunity = exchange.get(opportunity.opp_id)
        except ValueError:
            exchange.upsert(opportunity, state.account(opportunity.company)["verified_level"])
        state.register_opportunity(opportunity)
        published.append(opportunity.opp_id)
    # Fictional demo notes only; never overwrite an operator's private edits.
    demo_notes = {
        "NusaConf": {"ranges": {"A1": {"min": 40000, "max": 100000}},
                     "notes": "Floor USD 40,000; may discount about 15% for a two-year deal."},
        "CloudKita": {"ranges": {"B1": {"min": 60000, "max": 90000}},
                      "notes": "Budget ceiling USD 90,000; wants exclusive cloud-category sponsorship."},
    }
    for company, notes in demo_notes.items():
        path = private_path(company)
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            with open(path, "x", opener=lambda name, flags: os.open(name, flags, 0o600)) as stream:
                json.dump(notes, stream, indent=2)
        except FileExistsError:
            pass
    return {"seeded": published, "live_intake": "A1 awaits Rina's approval" if not include_a else "A1 seeded as fictional approved data"}


def get_pair(exchange, state, source_id, counterpart_id):
    source, counterpart = exchange.get(source_id), exchange.get(counterpart_id)
    if source.company == counterpart.company or source.status != "open" or counterpart.status != "open":
        raise ValueError("Choose open opportunities from different companies")
    state.participants(source_id, counterpart_id)
    return source, counterpart


def search(exchange, args, llm=None):
    source = exchange.get(args.source)
    matcher = Matcher(llm or AgentModel())
    if args.counterpart:
        return {"headlines": [headline(matcher.rank(source, exchange.get(args.counterpart)))]}
    strict = exchange.candidates(source, limit=4)
    strict_ids = {r["opportunity"]["opp_id"] for r in strict}
    rows = strict
    if args.near_misses and not strict:
        rows = exchange.candidates(source, strict=False, limit=3)
    def rank_row(row):
        for _ in (1, 2):  # a malformed or mislabeled model answer gets one retry, then the candidate is skipped
            try:
                return assess(row)
            except (RuntimeError, ValueError):
                pass
        return None

    def assess(row):
        result = headline(matcher.rank(source, Opportunity.from_dict(row["opportunity"])))
        result["retrieval"] = "qualified" if result["opp_id"] in strict_ids else "near_miss"
        if result["retrieval"] == "near_miss" and result["verdict"] in ("strong", "good"):
            result["verdict"] = "weak"
            result["headline"] = "Outside the current region or budget filters; confirm constraints before proceeding."
        return result

    with ThreadPoolExecutor(max_workers=5) as pool:  # one model call per candidate: run them side by side
        ranked = list(pool.map(rank_row, rows))
    results = [r for r in ranked if r]
    skipped = len(ranked) - len(results)
    results.sort(key=lambda r: ("strong", "good", "weak", "none").index(r["verdict"]))
    note = f" {skipped} candidate(s) could not be assessed; try again." if skipped else ""
    return {"headlines": results, "message": ("No candidates found" if not rows else
            "Headlines are free. Request a brief for details.") + note}


def brief(state, exchange, args, kind, llm=None, notes_path=private_path):
    source, counterpart = get_pair(exchange, state, args.source, args.counterpart)
    state.owner(source.company, args.actor)
    verification = state.account(counterpart.company)
    context = {"source": source.to_dict(), "counterpart": counterpart.to_dict()}
    if kind == "verified":
        context["verification"] = verification["verified_level"]

    def ranges():
        state.require_range_consent(source.opp_id, counterpart.opp_id)
        try:
            return tuple(read_json(notes_path(opp.company))["ranges"][opp.opp_id] for opp in (source, counterpart))
        except (KeyError, OSError) as exc:
            raise ValueError("Private range unavailable; no credits charged") from exc

    if kind == "range":
        state.require_range_consent(source.opp_id, counterpart.opp_id)
    product = BriefFactory.create(
        kind, ranker=lambda: Matcher(llm or AgentModel()).rank(source, counterpart), ranges=ranges,
        verification={"level": verification["verified_level"],
                      "evidence": ["Fictional demo verification flag; no documents have been independently checked."],
                      "demo_only": True})
    return CreditGate(product, state).deliver(source.company, args.request_id, context)


def required(args, *names):
    for name in names:
        if not getattr(args, name):
            raise ValueError(f"--{name.replace('_', '-')} is required for {args.action}")


def deal(state, exchange, args):
    source, counterpart = get_pair(exchange, state, args.source, args.counterpart)
    left, right = source.opp_id, counterpart.opp_id
    if args.action in ("interest", "withdraw", "share", "approve-share", "range-consent"):
        required(args, "company", "actor")
        if args.company not in (source.company, counterpart.company):
            raise ValueError("Company is not a participant")
    if args.action == "interest":
        required(args, "message_id")
        ready = state.interest(left, right, args.company, args.actor, args.message_id)
        return {"mutual": ready, "next_step": "Facilitator may open the Switch room" if ready else "Wait for the other human"}
    if args.action == "withdraw":
        state.withdraw(left, right, args.company, args.actor)
        return {"mutual": False, "next_step": "Stop room work; remove access in Switch. Previously shared messages cannot be recalled."}
    if args.action == "status":
        return {"mutual": state.is_mutual(left, right)}
    if args.action == "bind-room":
        required(args, "room_id")
        state.bind_room(left, right, args.room_id)
        return {"room_id": args.room_id}
    if args.action == "share":
        required(args, "file")
        payload = read_json(args.file)
        return {"approval": state.stage_shared(left, right, args.company, args.actor, payload), "review": payload}
    if args.action == "approve-share":
        required(args, "approval", "message_id")
        state.approve_shared(left, right, args.company, args.actor, args.approval, args.message_id)
        return {"approved": True}
    if args.action == "range-consent":
        required(args, "message_id")
        state.range_consent(left, right, args.company, args.actor, args.message_id)
        return {"consent_recorded": True}
    context = state.shared_context(left, right)
    context["opportunities"] = [source.to_dict(), counterpart.to_dict()]
    return prepare_meeting(AgentModel(), context)


def main(command=None):
    command = command or Path(sys.argv[0]).stem
    parser = parser_for(command)
    args = parser.parse_args()
    try:
        state = State(DATA / "accounts.db")
        if command == "credits":
            result = state.topup(args.company, args.topup) if args.topup is not None else state.account(args.company)
        elif command == "draft":
            opportunity = Opportunity.from_dict(read_json(args.file))
            result = {"approval": state.draft(opportunity, args.actor), "publish_exactly": opportunity.to_dict(),
                      "private": "Private notes are excluded. Review all free text before approving."}
        else:
            exchange = Exchange.open(DATA / "chroma")
            if command == "seed":
                result = seed(state, exchange, args.include_a)
            elif command == "publish":
                opportunity = Opportunity.from_dict(read_json(args.file))
                if digest(opportunity.to_dict()) != args.approval:
                    raise ValueError("Draft changed; show the updated draft and request approval again")
                state.approve(args.approval, args.actor, args.response, args.message_id)
                result = publish(state, exchange, opportunity, args.approval)
            elif command == "search":
                result = search(exchange, args)
            elif command in ("brief", "overlap"):
                result = brief(state, exchange, args, "range" if command == "overlap" else args.kind)
            else:
                result = deal(state, exchange, args)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0
    except (ValueError, OSError, RuntimeError, sqlite3.Error) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1
