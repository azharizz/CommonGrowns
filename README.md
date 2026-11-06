<p align="center">
  <img src="submission/assets/commongrown-banner.png" alt="CommonGrown: AI finds the right counterpart. AI prepares both sides. Humans close the deal. Two company stems meet above the soil, joined below it by a switch." width="100%">
</p>

<div align="center">
  <h1>CommonGrown</h1>
  <p><strong>An AI opportunity network that lives in your team chat. Your team just talks. The agent finds the deal.</strong></p>
  <p><em>AI finds the right counterpart. AI prepares both sides. Humans close the deal.</em></p>
  <p>
    <a href="submission/submission-description.md"><img src="https://img.shields.io/badge/SUBMISSION%20DESCRIPTION-1F7AE0?style=for-the-badge&logoColor=white" alt="Read the submission description"></a>
    <a href="submission/film/commongrown-showreel.mp4"><img src="https://img.shields.io/badge/WATCH%20THE%20FILM%20%C2%B7%202%3A58-E85A30?style=for-the-badge&logoColor=white" alt="Watch the 2:58 film"></a>
    <a href="#-try-it-in-30-seconds"><img src="https://img.shields.io/badge/TRY%20IT%20LIVE%20IN%20TELEGRAM-26A5E4?style=for-the-badge&logo=telegram&logoColor=white" alt="Try it live in Telegram"></a>
  </p>
  <p>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-8EBF6E.svg" alt="MIT license"></a>
    <img src="https://img.shields.io/badge/built%20on-Switch-1F7AE0.svg" alt="Built on Switch">
    <img src="https://img.shields.io/badge/Python-3.11--3.13-3776AB.svg" alt="Python 3.11 to 3.13">
    <img src="https://img.shields.io/badge/transport-WebSocket-17110C.svg" alt="WebSocket">
    <img src="https://img.shields.io/badge/matching-Chroma-7A6BD6.svg" alt="Chroma">
    <img src="https://img.shields.io/badge/state-SQLite-003B57.svg" alt="SQLite">
  </p>
  <p>
    <img src="https://img.shields.io/badge/agent-OpenAI%20Agents%20SDK-412991.svg" alt="OpenAI Agents SDK">
    <img src="https://img.shields.io/badge/hosted-GCP%20VM-4285F4.svg" alt="GCP VM">
    <img src="https://img.shields.io/badge/Telegram-live-8EBF6E.svg" alt="Telegram live">
    <img src="https://img.shields.io/badge/Slack%20%C2%B7%20Discord%20%C2%B7%20Teams%20%C2%B7%20Mattermost-experimental-F2B33D.svg" alt="Slack, Discord, Teams and Mattermost experimental">
    <img src="https://img.shields.io/badge/tests-69-F2B33D.svg" alt="69 tests">
  </p>
  <p>
    <a href="submission/submission-description.md">Submission</a> ·
    <a href="#-try-it-in-30-seconds">Try it</a> ·
    <a href="#how-switch-makes-this-possible">Switch</a> ·
    <a href="#how-the-system-is-built">Architecture</a> ·
    <a href="#-run-locally">Run locally</a> ·
    <a href="#truth-boundaries">Truth boundaries</a>
  </p>
  <p><sub>Your team talks → the agent keeps needs, not chat → the owner says yes twice → it finds the match → humans close the deal</sub></p>
</div>

> [!IMPORTANT]
> Built for the **Flip the Switch** hackathon, track **Best Business Workflow**. **Telegram is the only chat app run live.** Slack, Discord, Teams and Mattermost are **experimental and not tested**. The companies and deals are fictional demo data. Privacy is a trusted-broker design, not cryptography. See [Truth boundaries](#truth-boundaries).

<details>
<summary><kbd>Contents</kbd></summary>

- [At a glance](#-at-a-glance)
- [Try it in 30 seconds](#-try-it-in-30-seconds)
- [The problem](#the-problem)
- [The CommonGrown loop](#the-commongrown-loop)
- [How Switch makes this possible](#how-switch-makes-this-possible)
- [See the product](#see-the-product)
- [The flow, step by step](#the-flow-step-by-step)
- [What stays private](#what-stays-private)
- [How we make money](#how-we-make-money)
- [Five live groups, five different deals](#five-live-groups-five-different-deals)
- [How the system is built](#how-the-system-is-built)
- [Other chat apps (experimental)](#other-chat-apps-experimental)
- [Run locally](#-run-locally)
- [Verify](#verify)
- [Truth boundaries](#truth-boundaries)
- [Repository map](#repository-map)
- [License](#license)

</details>

## 🌱 At a glance

<table>
  <tr>
    <td width="20%" align="center"><strong>01 / CONNECT</strong><br><br>Switch links your group to a room. Two commands and the agent works for your company.</td>
    <td width="20%" align="center"><strong>02 / LISTEN</strong><br><br>Your team talks as usual. The agent keeps needs, offers and facts. Not the chat.</td>
    <td width="20%" align="center"><strong>03 / ASK</strong><br><br>It spots a need and asks. One yes drafts. A second yes publishes. Never on one.</td>
    <td width="20%" align="center"><strong>04 / MATCH</strong><br><br>It searches by meaning, ranks the top 4, and says a clear “no match” when that is the truth.</td>
    <td width="20%" align="center"><strong>05 / BRIEF</strong><br><br>Headlines are free. A paid brief prepares you, then humans close the deal.</td>
  </tr>
</table>

<p align="center">
  <img src="submission/assets/film-hero.gif" alt="A switch flips on, colour bursts across the screen, a sprout grows and the CommonGrown logo lands: AI finds the right counterpart, humans close the deal" width="100%">
</p>

## 🚀 Try it in 30 seconds

No install, no password. Join a company group and talk like your team would. The bot listens and speaks up when it notices a need.

| Company | What they do | Join |
| --- | --- | --- |
| **Acme Events** | Event organiser seeking sponsors | https://t.me/+64cIxX2hXdBlZWU1 |
| **CloudKita** | Cloud provider | https://t.me/+-jpNEHao4sA3YmU9 |
| **PromptWorks** | AI consultancy | https://t.me/+EdESi2Lq_7YyOGZl |
| **SecureNusa** | Security vendor | https://t.me/+i9EBMsZ648E4MjRl |
| **BatikMesin Supply** | Manufacturer | https://t.me/+hxQ54Wtfl25lMGQ9 |

Things to try (mention the bot with `@commongrown2`):

- Chat about a need, for example “we need a sponsor for our June summit, budget around 60-100k”. The bot offers to publish. Reply **yes** twice; it never publishes on one yes.
- `@commongrown2 /facts` shows what it knows. Confidential numbers (floors, ceilings) are kept private.
- `@commongrown2 /matches` finds partners. Headlines are free; `@commongrown2 /brief <my ID> <their ID> full` costs a credit.
- `@commongrown2 /status` shows credits.

In these demo groups any member can approve and run commands. Each group is capped at 25 model-heavy requests a day, and matching takes 40 to 70 seconds, so replies say “working on it” first. Data is demo data and may be reset.

For your own company: add `@CommonGrown_Bot` to your group, run `!invite-agent @commongrown2`, then `@commongrown2 /setup <Company>`. You become the owner.

## The problem

A tech summit in Jakarta expects five thousand people and has zero sponsors. A cloud company in Singapore is about to launch in Indonesia and nobody there knows its name. They need each other, and they may never meet.

B2B deals are found through referrals, events and cold outreach. Two things hurt:

1. **Discovery is luck.** Companies don't know who has a matching need, so good counterparts never meet.
2. **Meetings start cold.** Neither side knows the other's real constraints, so the first meetings go to basic qualification.

Meanwhile the need is already written down: in the company's team chat, where nobody outside can see it, and nobody inside will copy it into a form.

CommonGrown asks a narrower question:

> Can an agent read along in the chat a team already uses, understand what the company needs, and bring back the right counterpart without leaking what must stay private?

We don't replace the meeting. Agents discover and prepare. Humans bargain and close.

## The CommonGrown loop

<p align="center">
  <img src="submission/assets/commongrown-loop.gif" alt="Animated timeline: the team talks and the agent learns and asks below the soil line, private. The owner's two yeses cross the line, then the agent matches and both sides close." width="100%">
</p>

| Stage | What happens | What cannot happen silently |
| --- | --- | --- |
| **Talk** | The team plans in their group, lunch jokes included. Switch delivers every message to the agent. | The setup message says the team should know it is listening. `/mode mention` stops it, `/forget` wipes what it knows. |
| **Learn** | Every few messages the model folds the buffer into **facts**: need, offer, constraint or fact, each public or private. Raw messages are then deleted. | Contradictions are never resolved by guessing. They go to the owner under “Please settle”. |
| **Ask** | When the facts show an unpublished need, the agent asks. The first yes builds a draft with “where this came from” on every line. | The draft uses public facts only. Private facts never reach the drafting prompt. |
| **Publish** | A second yes publishes fixed public fields to the exchange and starts a search. | Never on one yes. The model cannot approve its own draft. |
| **Match** | Chroma recalls in both directions by meaning. The model ranks the top 4 and explains four fits. | A clear “no match” is a valid answer. It saves a meeting too. |
| **Brief** | Headlines are free. A full brief costs a credit and gives risks, unknowns and a pitch angle. | Credits are debited atomically. A failed generation refunds. |

## How Switch makes this possible

**Switch is the whole connection between the team and the agent.** The agent has no chat code. It holds one WebSocket to Switch, and every message, in every company's group, arrives through it.

<table>
  <tr>
    <td width="50%"><img src="submission/assets/film-path.gif" alt="A chat bubble travels from the team chat through Switch to the agent and the reply travels back, with three numbered jobs: carries it in, says who and which room, carries the reply back"><br><sub><strong>What Switch does.</strong> It carries the message in, says who wrote it and in which room, and carries the reply back.</sub></td>
    <td width="50%"><img src="submission/assets/film-build.gif" alt="A grid of five chat apps by five jobs fills with red BUILD cards, then collapses into one card: Switch does all of it"><br><sub><strong>Without Switch, we build all of this.</strong> Five chat apps times five jobs. With Switch, we wrote one agent.</sub></td>
  </tr>
  <tr>
    <td width="50%"><img src="submission/assets/film-apps.gif" alt="Telegram marked live and Slack, Discord, Teams and Mattermost marked experimental, all feeding one Switch bar and one agent"><br><sub><strong>One agent, any chat app Switch bridges.</strong> Telegram is live. The others are experimental: not tested yet.</sub></td>
    <td width="50%"><img src="submission/assets/film-off.gif" alt="The switch flips off and the screen goes dark: Nothing gets through. No Switch, no CommonGrown."><br><sub><strong>The Off test.</strong> Turn Switch off and nothing gets through. An illustration of the architecture, not a recording.</sub></td>
  </tr>
</table>

| Switch provides | We would otherwise build | CommonGrown adds |
| --- | --- | --- |
| **Chat bridge:** one bot, a room per group | A bot and connection per chat app | Listening and folding chat into facts |
| **Rooms:** one agent serves every company, each isolated | Tenant routing | One company per group, with an owner |
| **Identity:** `sender`, `sender_name` on every event | Per-app user lookup | Owner-only approval and credit spend |
| **Addressing:** `addressed` on every event | Per-app mention parsing | Commands when asked, silence otherwise |
| **Message log:** a cursor to resume from | A store and replay logic | Replay-safe work after a reconnect |

This is everything the worker reads from a chat message, and it looks the same whatever app it came from:

```text
room_id · sender · sender_name · body · addressed · message_id
```

It connects with `filter=all`, which is what makes listen mode possible: the agent sees ordinary team talk, not only mentions, and decides for itself when to speak.

## See the product

Every screenshot is a frame from a screen recording of the real run in the live Telegram groups.

### Connect and listen

| Two commands to connect | The team just talks | It asks first |
| --- | --- | --- |
| ![Switch explains how to add an agent, then !invite-agent and /setup link the group to CloudKita](submission/screenshots/onboarding.jpg) | ![Rina, Doni and Mira plan the Jakarta Tech Summit, including a lunch joke, and the bot asks if it should find matching companies](submission/screenshots/team-chat.jpg) | ![The bot asks, the team says yes, and it shows what it would publish](submission/screenshots/ask-first.jpg) |
| Switch links the group to a room. `!invite-agent`, then `/setup`. | Rina, Mira and Doni plan a summit. The agent reads along. | One yes gets a draft. Nothing is public yet. |

### Publish and match

| Every line traced | Published, with matches | What it knows |
| --- | --- | --- |
| ![Draft with a where this came from section naming owner statements](submission/screenshots/draft.jpg) | ![Published, 4 possible matches: NimbusID good match, CloudKita weak fit, Samudra Systems and SiamPack no match](submission/screenshots/published-matches.jpg) | ![The /facts reply: needs, offers, facts, 1 confidential fact kept private, and a please settle item about 5000 vs 6000](submission/screenshots/facts.jpg) |
| “Where this came from” shows who said each line. | Top 4, ranked. Two honest “no match” results. | One fact kept private, one disagreement for the owner to settle. |

### Credits and briefs

| 0 credits: locked | Credits on `/status` | The paid brief |
| --- | --- | --- |
| ![This brief is locked: it costs 1 credit and you have 0](submission/screenshots/locked-brief.jpg) | ![Status: free plan, credits 3, verification L0, listening, facts known 10 with 1 kept private](submission/screenshots/status.jpg) | ![A delivered brief with risks, still unknown, pitch angle and next step](submission/screenshots/paid-brief.jpg) |
| Headlines stay free. The brief is locked. | 3 credits, plan and verification level. | Risks, what is still unknown, a pitch angle, a next step. |

## The flow, step by step

<table>
  <tr>
    <td width="50%"><img src="submission/assets/film-connect.gif" alt="The real Telegram onboarding next to a diagram: Telegram group, Switch room, agent"><br><sub><strong>1 · Connect.</strong> Switch links the group to a room. One command invites the agent, one more binds it to your company.</sub></td>
    <td width="50%"><img src="submission/assets/film-listen.gif" alt="Chat bubbles feed fact chips above the soil line, a $40k floor sinks below it"><br><sub><strong>2 · Listen.</strong> Chat becomes fact chips. The $40k floor goes below the line and never comes back up.</sub></td>
  </tr>
  <tr>
    <td width="50%"><img src="submission/assets/film-two-yes.gif" alt="YES, 1 of 2: a draft with sources. YES, 2 of 2: published, a sprout breaks through the soil"><br><sub><strong>3 · Two yeses.</strong> One yes drafts, with every line traced. The second publishes. Never on one.</sub></td>
    <td width="50%"><img src="submission/assets/film-match.gif" alt="Dots drift on a map of meaning, needs a sponsor finds wants exposure, then NimbusID good match, CloudKita weak, Samudra and SiamPack no match"><br><sub><strong>4 · Match.</strong> “Needs a sponsor” finds “wants exposure”. Same deal, different words.</sub></td>
  </tr>
  <tr>
    <td width="50%"><img src="submission/assets/film-settle.gif" alt="/facts on the left, a balance scale weighing 5,000 against 6,000 on the right: please settle, it won't guess, $40k floor still private"><br><sub><strong>5 · It won't guess.</strong> The team said 5,000 and 6,000. The owner decides. The floor stays private.</sub></td>
    <td width="50%"><img src="submission/assets/film-groups.gif" alt="Five phones wired to one agent through the soil, with CloudKita to Acme Events good match highlighted"><br><sub><strong>6 · Five groups, one agent.</strong> Same flow, different deals, one shared worker on Switch.</sub></td>
  </tr>
  <tr>
    <td width="50%"><img src="submission/assets/film-brief.gif" alt="Headlines free, 0 credits locked, then a brief delivered with risks, still unknown and a pitch angle, credits going from 3 to 2"><br><sub><strong>7 · The brief.</strong> 0 credits: locked. With a credit: risks, unknowns and a pitch angle, 3 credits to 2.</sub></td>
    <td width="50%"><img src="submission/assets/film-finale.gif" alt="Two company stems grow and meet: AI finds the right counterpart, AI prepares both sides, humans close the deal, then the CommonGrown logo"><br><sub><strong>8 · Humans close the deal.</strong> The first meeting starts from the deal, not the basics.</sub></td>
  </tr>
</table>

## What stays private

<p align="center">
  <img src="submission/assets/commongrown-privacy.gif" alt="Real demo chat lines are sorted: the package and public range rise into a public record with fixed fields, the $40k floor falls below the line, the lunch joke dissolves. The public record has no private notes field." width="100%">
</p>

| Rule | How it is enforced |
| --- | --- |
| **A floor can't be published by mistake** | The public record has fixed fields and no field for private notes. This is a code-level gate, not a prompt rule (`models.py`). |
| **Private facts stay out of drafts** | They are excluded from drafting prompts, matches and other companies' views. `/facts` shows only a count. |
| **The chat isn't kept** | Raw messages are buffered for at most 24 hours and 40 per room, then deleted once summarized. |
| **The model never sees chat IDs** | Sources are shown as `owner`, `member N` or `team`. |
| **The model can't approve itself** | Only the owner can say yes or spend credits (any member in the public demo groups). |

## How we make money

<p align="center">
  <img src="submission/assets/film-money.gif" alt="A price staircase rises out of the soil: free headlines, 1 credit full brief, 2 credits private budget check, 3 credits verified brief, then NO CUT OF THE DEAL" width="80%">
</p>

We charge for what only a neutral broker can do. Companies can take a meeting to Zoom or WhatsApp without us, so we don't charge per introduction or per closed deal.

| Output | Cost | What you get | Why it can't be copied outside |
| --- | --- | --- | --- |
| **Match headline** | Free | Company, verdict, one line why | It's the hook |
| **Full brief** | 1 credit | Four fits, risks, unknowns, pitch angle | Built from both sides' approved data |
| **Private budget check** | 2 credits | Overlap or not. **Never the numbers** | Needs both sides' hidden numbers |
| **Verified brief** | 3 credits | The full brief plus the counterpart's verification level | Verification evidence lives with us |

New companies start with 3 credits. **Credit costs are built; money prices are not set yet.** No real payments are connected, and willingness to pay has not been validated. The private check and verified brief are implemented and unit-tested, but were not shown live.

## Five live groups, five different deals

| Group | Says in chat | Result |
| --- | --- | --- |
| **Acme Events** (Jakarta tech summit) | Needs sponsors, a private $40k floor, a 5,000 vs 6,000 attendee disagreement | **NimbusID, good match.** The floor stays private; the disagreement is flagged. |
| **CloudKita** (cloud provider) | Wants brand exposure, keeps a ceiling private | **Acme Events, good match.** NimbusID is correctly “no match”. Brief locked at 0 credits. |
| **PromptWorks** (AI consultancy) | Wants enterprise clients | **CloudKita, good match** in its implementation-partner role: the company that fails as a sponsor fits as a partner. |
| **SecureNusa** (security vendor) | Wants CISO leads through events | **Acme Events, weak fit.** Honest about it. |
| **BatikMesin Supply** (packaging machines) | Wants distributors in Vietnam and Thailand | **SiamPack Distribution, good match.** |

| PromptWorks | SecureNusa | BatikMesin Supply |
| --- | --- | --- |
| ![PromptWorks published with CloudKita as a good match](submission/screenshots/group-promptworks.jpg) | ![SecureNusa published with Acme Events as a weak fit](submission/screenshots/group-securenusa.jpg) | ![BatikMesin published with SiamPack Distribution as a good match](submission/screenshots/group-batikmesin.jpg) |

## How the system is built

<p align="center">
  <img src="submission/assets/commongrown-architecture.gif" alt="Animated architecture: a message travels from Telegram through Switch over a WebSocket to the CommonGrown worker, which uses SQLite, Chroma and the OpenAI Agents SDK, and the reply travels back. Slack, Discord, Teams and Mattermost are marked experimental." width="100%">
</p>

The two-yes flow, as it runs over Switch:

```mermaid
sequenceDiagram
    actor Team as Team in Telegram
    participant S as Switch
    participant W as CommonGrown worker
    participant M as Model
    participant X as Chroma exchange
    Team->>S: Chat in the group
    S->>W: room_id, sender, body, addressed
    W->>M: Fold buffer into facts
    M-->>W: Needs, offers, public and private
    Note over W: Raw messages deleted
    W->>S: "Want me to find matches?"
    S->>Team: Posted in the same chat
    Team->>S: yes
    S->>W: yes (1 of 2)
    W->>S: Draft from public facts, with sources
    S->>Team: Nothing is published yet
    Team->>S: yes
    S->>W: yes (2 of 2)
    W->>X: Publish fixed public fields
    X-->>W: Recall by meaning, both directions
    W->>M: Rank top 4, explain four fits
    M-->>W: Verdicts
    W->>S: Published, with matches
    S->>Team: Good match, weak fit, no match
```

| Technology | Role in CommonGrown |
| --- | --- |
| **Switch** | Self-hosted on Docker (core, gateway, Postgres): chat bridge, rooms, identity, addressing and message log. |
| **Python 3.11–3.13 · websockets** | One worker with one serial queue, reconnect and checkpoint, “working on it” notices. Serves every company group. |
| **OpenAI Agents SDK** | Scoped tools and validated output, against any OpenAI-compatible endpoint. No model is hardcoded. |
| **Chroma · all-MiniLM-L6-v2** | Two documents per opportunity. Forward and reverse recall, with hard filters on status and budget overlap. |
| **SQLite** | Accounts, atomic credits, groups, facts, conflicts, consent, the short evidence buffer. |
| **GCP** | One `e2-small` VM. No public app port, no reserved IP, IAP-only SSH. |

## Other chat apps (experimental)

Telegram is the only chat app we have run live. Switch also bridges Slack, Microsoft Teams, Discord and Mattermost, and the worker has no Telegram-specific logic: it only sees Switch rooms. The same agent should work there, but **none of these has been tested yet**.

Two small settings exist for them: mentions in the platform's own form are stripped (`<@id>`, `<at>name</at>`), and `max_message_chars` sets the reply size (Discord needs 1900). Setup is in [app/deploy/README.md](app/deploy/README.md#other-chat-apps-experimental).

## 🛠️ Run locally

Python 3.11–3.13 and [uv](https://docs.astral.sh/uv/). You need a Switch server and an OpenAI-compatible model that supports function calling.

```sh
git clone https://github.com/azharizz/CommonGrowns
cd CommonGrowns/app
uv sync --locked
cp switch.example.json switch.json     # URL, agent name, optional open_companies
uv run python seed.py                  # fictional companies and opportunities
```

Model settings go in the repo-root `.env` or the environment:

```dotenv
AGENT_BASE_URL=https://your-provider.example/v1
AGENT_MODEL=your-model-id
AGENT_API_KEY=your-key
```

Register the agent once (`SWITCH_REGISTRATION_KEY` in the environment), then run it:

```sh
uv run python switch_worker.py register --config switch.json
uv run python switch_worker.py run --config switch.json
```

<details>
<summary><strong>All chat commands</strong></summary>

Mention the bot (`@commongrown2 ...`): `/setup <Company>`, `/status`, `/facts`, `/fromchat`, `/matches`, `/brief <my ID> <their ID> full|verified|range`, `/mode listen|mention`, `/forget`, `/draft`, `/approve`, `/balance`.

Deal-room commands (`/interest`, `/share`, `/approve-share`, `/range-consent`, `/prepare`, `/withdraw`) are implemented and unit-tested but have not been run live.

</details>

<details>
<summary><strong>Deploying on Google Cloud</strong></summary>

[app/deploy/README.md](app/deploy/README.md) covers the VM, the Switch self-host, the worker service and per-app setup for the experimental bridges.

</details>

## Verify

```sh
cd app
uv run python -m unittest discover -s tests
```

69 tests cover consent, ownership, the facts store and its privacy rules, the proactive flow, open demo groups and the rate cap, credits (retries, concurrency, refunds), Switch message parsing and the render layer. Chroma, the model and Switch are mocked; live behavior was verified by running real group conversations on the deployed worker.

## Truth boundaries

- **Telegram only, live.** Slack, Discord, Teams and Mattermost are experimental and have not been tested.
- **Trusted broker, not cryptography.** The platform can read stored facts, so companies must trust it with private numbers. The bot itself tells teams not to post confidential numbers. Privacy-preserving matching is later work.
- **Fictional demo.** The companies and deals are demo data. There are no real customers and no measured savings.
- **No real payments or verification.** Credits are a working gate with no money behind them. Verification levels (L0, L1, L2) are demo flags, and money prices are not set.
- **Not shown live.** The private budget check, verified brief and deal-room commands are implemented and unit-tested only.
- **The Off test is an illustration.** The film shows what the architecture implies; the outage was not recorded.
- **Known limits.** One opportunity per company. Anyone can `/setup` an unclaimed company name. Matching takes 40 to 70 seconds. The budget filter compares stated budgets, so it can exclude a good match. English and USD demo data.
- **Unvalidated.** Willingness to pay has not been tested with real buyers. See [product.md](product.md#8-evidence-and-open-risks).

## Repository map

```text
app/commongrown/     Worker: switch.py, worker.py, state.py, exchange.py, cli.py, ai.py, briefs.py, models.py, render.py
app/tests/           69 unit tests
app/deploy/          GCP scripts, service file, Switch setup, experimental bridges
app/seeds/           Fictional companies and opportunities
assets/logos/        Demo company logos
submission/          Submission description, screenshots, animations, film
tools/video/         Scripts for the earlier demo capture
product.md           Product thesis, flow, business model, evidence and open risks
product_research.md  Market research
```

The code walkthrough is in [app/README.md](app/README.md). Product decisions are in [product.md](product.md).

## License

[MIT](LICENSE). Switch is a separate project: [github.com/sandboxaq/switch](https://github.com/sandboxaq/switch). CommonGrown is not endorsed by its authors.
