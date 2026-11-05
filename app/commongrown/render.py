"""Turn broker results into short plain-language chat text (bullets, no tables: Telegram shows tables as text)."""

VERDICT = {"strong": "Strong match", "good": "Good match", "weak": "Weak fit", "none": "No match"}
FIT = {"yes": "✓", "partial": "~", "no": "✗", "n/a": "–"}
FIT_NAME = {"business": "Business", "commercial": "Commercial", "capability": "Capability", "strategic": "Strategic"}


def money(low, high):
    if low is None or high is None:
        return "not stated"
    return f"${low:,.0f}–${high:,.0f}"


def bullets(items):
    return "\n".join(f"• {item}" for item in items)


def draft(result):
    d = result["publish_exactly"]
    lines = [f"Here is what I would publish for {d['company']}:",
             f"• Looking for: {d['seeks']}", f"• Offering: {d['offers']}",
             f"• Budget: {money(d['budget_min'], d['budget_max'])}", f"• Region: {d['region']}",
             f"• Categories: {', '.join(d['categories'])}", f"• Audience: {d['audience']}"]
    if result.get("evidence"):
        lines += ["", "Based on what you said:"] + [f"“{q}”" for q in result["evidence"]]
    lines += ["", "Nothing is published yet. Reply “yes” to publish and find matches, “no” to cancel, "
              f"or edit with /draft. (Exact command: /approve {result['approval']})"]
    return "\n".join(lines)


def headlines(result):
    rows = result["headlines"]
    if not rows:
        return result.get("message", "No candidates found.")
    source = result.get("source")
    lines = [f"Found {len(rows)} possible match{'es' if len(rows) != 1 else ''}:"]
    for number, row in enumerate(rows, 1):
        lines.append(f"{number}. {row['company']} ({row['opp_id']}) — {VERDICT[row['verdict']]}: {row['headline']}")
    if source:
        lines += ["", f"Headlines are free. For details: /brief {source} <ID> full (1 credit)."]
    return "\n".join(lines)


def brief(result):
    if result.get("locked"):
        return (f"This brief is locked: it costs {result['cost']} credit(s) and you have {result['credits']}. "
                "Match headlines stay free.")
    if "compatible" in result:
        return ("Private range check: " + ("compatible" if result["compatible"] else "not compatible")
                + f", overlap {result['overlap']}. Neither side's numbers are shown.")
    lines = [f"Brief on {result['company']} ({result['opp_id']}): {VERDICT[result['verdict']]}", result["headline"], ""]
    for key, name in FIT_NAME.items():
        fit = result["fits"][key]
        note = fit["evidence"][0] if fit["evidence"] else ""
        lines.append(f"{FIT[fit['verdict']]} {name}: {note}")
    lines += ["", f"You gain: {result['gains']['source']}", f"They gain: {result['gains']['counterpart']}"]
    if result["risks"]:
        lines += ["", "Risks:", bullets(result["risks"])]
    if result["missing_info"]:
        lines += ["", "Still unknown:", bullets(result["missing_info"])]
    lines += ["", f"Pitch angle: {result['pitch_angle']}", f"Next step: {result['next_step']}"]
    if "verification" in result:
        v = result["verification"]
        lines += ["", f"Verification level: {v['level']} (demo flag, not independently checked)."]
    return "\n".join(lines)


def meeting(result):
    lines = ["Meeting prep (draft for humans to review, not an agreement):", "", result["draft_proposal"], ""]
    for company, points in result["sticking_points"].items():
        lines += [f"Likely sticking points for {company}:", bullets(points), ""]
    lines += ["Open questions:", bullets(result["open_questions"]), "", "Suggested agenda:"]
    lines += [f"{n}. {item}" for n, item in enumerate(result["agenda"], 1)]
    return "\n".join(lines)


def status(result):
    where = {"listen": "listening to the whole group", "mention": "only reading messages that mention me"}
    lines = [f"{result['company']} — {result['plan']} plan", f"• Credits: {result['credits']}",
             f"• Verification: {result['verified_level']} (demo)"]
    if result.get("mode"):
        lines.append(f"• Mode: {where[result['mode']]}")
        lines.append(f"• Messages kept as evidence: {result['evidence_messages']}")
    lines.append("• Published opportunities: " + (", ".join(result["opportunities"]) or "none yet"))
    return "\n".join(lines)


def generic(result):
    return "\n".join(f"{key}: {value}" for key, value in result.items())


def render(result):
    if not isinstance(result, dict):
        return str(result)
    parts = []
    if "published" in result and "approval" in result:
        parts.append(f"Published ✓ (ID {result['published']}). It is now visible to other companies on the exchange.")
        result = {key: value for key, value in result.items() if key not in ("published", "approval")}
    if "publish_exactly" in result:
        return draft(result)
    if "headlines" in result:
        parts.append(headlines(result))
    elif "verdict" in result and "fits" in result or "locked" in result or "compatible" in result:
        parts.append(brief(result))
    elif "draft_proposal" in result:
        parts.append(meeting(result))
    elif "credits" in result and "plan" in result:
        parts.append(status(result))
    elif "credits" in result and "company" in result:
        parts.append(f"{result['company']} has {result['credits']} credit(s).")
    elif "mutual" in result:
        parts.append("Interest recorded. " + ("Both companies are interested: a deal room can now be opened."
                                              if result["mutual"] else "Waiting for the other company."))
    elif "approved" in result:
        parts.append("Approved.")
    elif "reply" in result:
        parts.append(result["reply"])
    elif result:
        parts.append(generic(result))
    return "\n\n".join(p for p in parts if p)
