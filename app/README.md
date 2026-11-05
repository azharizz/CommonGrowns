# CommonGrown

**AI finds the right counterpart. AI prepares both sides. Humans close the deal.**

The app implements the consent-first opportunity workflow in `../product.md`.
The default cloud architecture is now **one shared Python worker**, with separate
company data and room histories. Four logical responsibilities (company intake,
matching, representation and facilitation) do not require four running agents.

## Google Cloud deployment

Read **[deploy/README.md](deploy/README.md)** for the complete setup, isolation
model and chat commands. Review a concrete plan without deploying:

```sh
cd app  # if you are at the repository root
uv sync --locked
PROJECT_ID="$(gcloud config get-value project)"
python3 deploy/gcloud.py plan --project "$PROJECT_ID"
```

The plan uses one `e2-small` VM, persistent SQLite/Chroma storage, no VM service account, IAP-only SSH and a **two-hour auto-stop after each
start**. No cloud changes occur until explicitly running `create`/`upload`.
A stopped VM must be started explicitly; chat messages do not wake it.
Persistent disk and other retained resources can still incur costs.

The shared worker connects to an existing Switch server, or an upstream Switch
server you self-host. The CommonGrown deployment script does not install that
separate server/PostgreSQL stack. See the deployment guide before choosing a
machine size for co-hosting. Switch remains responsible for chat, identity,
room membership and message transport.

## One worker, separated data

- Real Switch sender IDs map to company accounts in operator-owned configuration.
  A user cannot choose another company by writing a `company_id` in a message.
- Each company has its own `private.json` and `history.db` under
  `.data/companies/<company hash>/`. Histories are additionally separated by room.
- Shared room histories use `.data/shared/<room hash>/` and never load private
  company history. The model receives fresh, scoped context on every call.
- Only private intake sees its company's private notes. Matching sees public
  opportunities. Meeting preparation sees approved shared positions and public
  records. The model has no file/shell tools and cannot approve its own drafts.
- Exact-draft approval, mutual interest, separate range-check consent and credits
  remain enforced by the broker code. Replays return the saved response rather
  than charging or generating again.

This is application-level isolation in a **trusted broker**, not cryptographic
privacy or isolation from the VM operator. Correct private-room membership in
Switch is also required. Verification levels are explicitly fictional demo flags.

## Local setup

Python 3.11–3.13 and uv are required. Unit tests need only Python's standard library.

```sh
uv sync --locked
uv run python seed.py
cp switch.example.json switch.json
```

Seeding creates the five fictional counterpart opportunities; A1 is withheld for
Rina's live consent flow. There are six fixture opportunities across five
companies because CloudKita has both B1 and B2. `seed.py --include-a` explicitly
publishes all fictional fixtures for development only. Repeated seeding preserves
live edits, balances and private notes. 

Chroma 1.5.9 uses the local `all-MiniLM-L6-v2` model and downloads it on first use.
Persistent broker data defaults to `.data`; set `COMMONGROWN_DATA` to change it.

## OpenAI Agents SDK configuration

The only model implementation uses the OpenAI Agents SDK with your existing
OpenAI-compatible endpoint. The repository-root `.env` is loaded automatically;
`app/.env` is also supported. Existing process environment values take precedence.
Required names (values are never printed):

```dotenv
AGENT_BASE_URL=https://your-provider.example/v1
AGENT_MODEL=your-model-id
AGENT_API_KEY=your-key
```

Each run creates a fresh SDK Agent with two scoped tools: `read_scoped_context`
returns only the current authorized task/evidence; `submit_result` validates the
result against its schema. The agent can repair rejected submissions. Successful
validated submission ends the loop. No plain-text answer bypasses validation.
Runs are capped at five turns/180 seconds, 4,096 output tokens per call, and have
tracing disabled. No provider-hosted sessions or global company memory are used.
Business mutations still require direct authenticated human commands; the model
cannot approve, publish, debit credits or read arbitrary company data.

The endpoint must support Chat Completions function calling. The configured
model and URL are used verbatim; no automatic provider/model fallback exists.
Google Cloud hosts the worker only; AI billing belongs to your configured API
provider. Credentials are excluded from deployment archives and version control.

## Switch configuration

Replace the sample URL/user IDs/room IDs in `switch.json` with real Switch IDs.
Register one agent once, then invite it into the intended rooms and configure
who can address it in Switch. Do not copy private registration keys into source.

```sh
# Set SWITCH_REGISTRATION_KEY securely in your environment first.
uv run python switch_worker.py register --config switch.json
uv run python switch_worker.py run --config switch.json
```

Use `a-private` for Rina, `b-private` for Budi, `exchange` for public discovery,
and the mutually approved deal room for shared preparation. Only the respective
human and the shared agent belong in each private room. The dedicated deployment
guide includes the full command table, room-binding step, registration procedure
and Linux service setup. Telegram groups are created by humans; each human must
link their account in Switch. Keep BotFather Group Privacy off before adding the
bot to groups, and use only one process per Telegram bot token.

## Product flow

1. Address `@commongrown` privately to draft an opportunity. Private numbers stay
   out of the draft; the human must review every public field.
2. `/approve HASH` publishes exactly the reviewed draft. Edits need new approval.
3. `/matches A1` returns free headlines; `/matches A1 E1` can explain a hard no.
   `/matches B2 D1` demonstrates the implementation-partner role.
4. `/brief A1 B1 full` or `verified` delivers the paid result privately. Source
   company must match the authenticated human. Zero balance blocks generation.
5. Both humans send `/interest A1 B1`. Only then may an operator create/activate
   and bind the actual Switch deal room.
6. Each privately stages `/share A1 B1 JSON` and approves the exact hash with
   `/approve-share A1 B1 HASH`.
7. `/prepare A1 B1` in the bound deal room produces a draft proposal, each side's
   sticking points, open questions and agenda. Humans negotiate and close.

Optional `/brief A1 B1 range` costs two credits and requires **both** humans to
separately send `/range-consent A1 B1`. It returns compatibility and a coarse
`none`/`narrow`/`broad` label, never numeric bounds. Narrow means the intersection
width is at most 25% of the union span. The fictional A–B range is broad.

## Code and patterns

| Module | Responsibility |
| --- | --- |
| `worker.py` | Authenticated company/room routing, isolated histories, explicit human commands |
| `switch.py` | One authenticated WebSocket connection, serial work queue, reconnect/checkpoint handling |
| `models.py` | Fixed public fields, validation, coarse private comparison |
| `state.py` | Broker SQLite accounts, approval revisions, opt-ins and shared consent |
| `exchange.py` | Two documents per opportunity, forward/reverse Chroma recall and hard filters |
| `ai.py` | Request-scoped SDK agent factory, tool loop, matching and meeting preparation |
| `briefs.py` | Product factory, verification decorator and atomic credit decorator |
| `cli.py` | Reusable low-level broker commands and demo seeding |

**Factory:** `BriefFactory` selects the requested product; `build_agent` builds a scoped SDK agent. **Decorator:** `VerifiedBrief` enriches a full brief;
`CreditGate` adds atomic balance checks, durable delivery and idempotency.
No agent framework or web framework is added.

Full brief costs 1 credit; verified costs 3; private range costs 2. “Delivery”
means the artifact is persisted with the debit. Forwarding retries reuse it.
Generation/validation failure rolls back the debit. SQLite serializes brief
production; this is sufficient for the demo's single worker.

## Verification and limits

```sh
python3 -m unittest discover -s tests -v
python3 -m compileall -q commongrown deploy tests *.py
bash -n deploy/install.sh
```

Tests were written before implementation and observed failing, then made to pass.
They cover consent, ownership, privacy, shared-room gating, factory/decorators,
credit retries/concurrency, scoped histories and notes, provider responses,
Switch message parsing and deployment cost/security flags. Chroma/provider/
Switch interactions are mocked; local SQLite tests use temporary directories.

The SDK live smoke command is `uv run python smoke_ai.py` (uses the configured
provider and can incur a small charge). It sends synthetic data only and asserts
actual context-tool execution and validated submission. Deployment, live Switch
transport, Chroma recall and full demo behavior need a later integration pass.

Other deliberate limits: English/USD demo data, five seeded accounts, no real
payments or verification, trusted operator CLI, and no cryptographic tenant
separation. Fixed keys cannot detect every secret in prose: human review remains
mandatory. Changing public terms invalidates old opt-ins. Withdrawal blocks
further local sharing but cannot recall messages already posted in Switch.
SQLite and Chroma are separate stores; retry an approved publication to reconcile
an interrupted write. Model output remains draft advice for human review.

Latest verification: 43 unit tests passed, plus a live synthetic SDK smoke run
using the configured `.env` endpoint/model/key. The smoke confirmed one scoped
context tool call and one accepted submission. No company-private data was sent.
