# CommonGrown: the code

Employees talk in their company's Telegram group. One shared Python worker, connected to a [Switch](https://github.com/sandboxaq/switch) server as an agent, listens, keeps a structured summary of what the company needs, offers and cannot disclose, and (only after the owner says yes twice) publishes an opportunity and finds matches. See `../product.md` for the product, `deploy/README.md` for hosting.

## How a message travels

```
Telegram group ── Switch Telegram bridge ── Switch room ──(WebSocket agent protocol)── worker
                                                                      │
        accounts.db (SQLite): credits, groups, facts, consent ◄───────┤
        Chroma (all-MiniLM-L6-v2): public opportunities ◄─────────────┤
        OpenAI Agents SDK → your OpenAI-compatible model ◄────────────┘
```

- **Listen mode.** In a linked group the worker receives every message (`filter=all`), buffers raw text briefly (24 h, 40 per room), and every few messages has the model fold it into **facts** (need / offer / constraint / fact, each public or private, with the source as `owner | member N | team`). The raw messages are then deleted; only the summary stays. A newer statement replaces an older fact with the same key; contradictions are flagged for the owner.
- **Proactive suggestion.** When the facts show an unpublished need, the bot asks the owner. A first "yes" builds a draft from the public facts; a second "yes" publishes it and runs a search. Never on one yes.
- **Matching.** Chroma recall (needs vs. others' offers, and the reverse) with hard filters on status and budget overlap, then the model ranks the top 4 and explains fit (business, commercial, capability, strategic). Region is judged by the model, not filtered.
- **Credits.** Headlines are free. A full brief costs 1 credit, verified 3, private range check 2. New companies start with 3. Debits are atomic and replay-safe; a failed generation refunds.
- **Privacy.** Private facts (floors, ceilings, rate cards, margins) never reach a drafting prompt or another company. This is a trusted-broker design, not cryptography; verification levels are demo flags.

## Modules (`commongrown/`)

| Module | Responsibility |
| --- | --- |
| `switch.py` | WebSocket connection, serial work queue, reconnect/checkpoint, "working on it" notices, reply posting |
| `worker.py` | Group onboarding (`/setup`), authorization, listen/learn/suggest loop, yes-flow, all commands |
| `state.py` | SQLite: accounts, groups, facts, conflicts, evidence buffer, watch state, consent, shared positions |
| `exchange.py` | Chroma store: two documents per opportunity, forward/reverse recall, hard filters |
| `cli.py` | `search`: top-4 ranking with per-candidate retry; brief and meeting-prep commands |
| `ai.py` | OpenAI Agents SDK wrapper (scoped tools, validated submission, one retry) |
| `briefs.py` | Brief factory, verification decorator, credit gate |
| `models.py` | Fixed public fields and validation (there is no field for private notes) |
| `render.py` | Plain-language chat text (bullets, no JSON, no tables) |

## Chat commands

Mention the bot (`@commongrown2 ...`): `/setup <Company>`, `/status`, `/facts`, `/fromchat`, `/matches`, `/brief <my ID> <their ID> full|verified|range`, `/mode listen|mention`, `/forget`, `/draft`, `/approve`, `/balance`. Deal-room commands (`/interest`, `/share`, `/approve-share`, `/range-consent`, `/prepare`, `/withdraw`) are implemented and unit-tested but have not been run live.

Who may act: the person who ran `/setup` owns the group. Companies listed in `open_companies` in the worker config (the public demo groups) let any member act. `daily_limit` (default 25) caps model-heavy requests per group per day.

## Run locally

Python 3.11–3.13 and [uv](https://docs.astral.sh/uv/).

```sh
uv sync --locked
cp switch.example.json switch.json     # URL, agent name, optional open_companies
uv run python seed.py                  # fictional companies and opportunities
uv run python reset_demo.py            # or: wipe state and load the demo background companies
```

Model settings (values are never printed), in the repo-root `.env` or the environment:

```dotenv
AGENT_BASE_URL=https://your-provider.example/v1
AGENT_MODEL=your-model-id
AGENT_API_KEY=your-key
```

The endpoint must support Chat Completions function calling. Register the agent once (`SWITCH_REGISTRATION_KEY` in the environment), then run it:

```sh
uv run python switch_worker.py register --config switch.json
uv run python switch_worker.py run --config switch.json
```

Data lives in `.data` (override with `COMMONGROWN_DATA`).

## Tests

```sh
uv run python -m unittest discover -s tests
```

69 tests cover consent, ownership, the facts store and its privacy rules, the proactive flow, open demo groups and the rate cap, credits (retries, concurrency, refunds), Switch message parsing and the render layer. Chroma, the model and Switch are mocked; live behavior was verified by running real group conversations on the deployed worker.

## Other chat apps (experimental, not tested)

Telegram is the only app run live. The worker talks only to Switch rooms, so Slack, Teams, Discord and Mattermost need no new connector, just a Switch bridge. Two settings exist for them: mentions in the platform's own form are stripped (`<@id>`, `<at>name</at>`), and `max_message_chars` in the worker config sets the reply size (Discord needs 1900). See `deploy/README.md`.

## Known limits

- One opportunity per company; opportunity IDs derive from the company.
- Anyone can `/setup` an unclaimed company name (no verification).
- Matching takes 40–70 s. The budget filter compares stated budgets, so it can exclude a good match whose project budget differs from the other side's event budget.
- English and USD demo data; no real payments or verification.
