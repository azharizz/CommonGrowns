# CommonGrown

**AI finds the right counterpart. AI prepares both sides. Humans close the deal.**

An AI-powered B2B opportunity network. Companies publish what they need and what they offer. Agents find compatible counterparts, explain the fit, and prepare both sides for the real business conversation inside a shared Switch room.

> Built for the **Flip the Switch** hackathon (WeMakeDevs x DevTools Academy), target track: **Best Business Workflow**. Deadline: Nov 7, 2026, 11:59 PM IST.

---

## 1. Problem

B2B deals (sponsorships, client acquisition, channel and strategic partnerships) are found through referrals, events and cold outreach, then bargained over in meetings. Two things hurt:

1. **Discovery is luck.** Companies don't know who else has a matching need or capability, so good counterparts never meet.
2. **Meetings start cold.** Neither side knows the other's real constraints, so the first meetings go to basic qualification and positioning, not the deal.

## 2. Product thesis

We do **not** try to replace the meeting. The evidence points to a split: buyers like to research and shortlist online, but still want a human for judgment-heavy steps (see section 8).

| Stage | Who does it |
|---|---|
| Publish a need or offer | Company (agent-assisted, human-approved) |
| Discover and rank counterparts | Agents |
| Explain fit, risks, missing info | Agents |
| Prepare both sides for the meeting | Agents + humans in a Switch deal room |
| Bargain and close | **Humans** |

**Network of opportunities, not companies.** A profile says who a company is; an opportunity says what it wants to accomplish ("need a sponsor for a 5,000-person tech conference, $50k-$100k, Indonesia"). One company can hold several opportunities in different roles.

## 3. Differentiation

| Existing | Purpose | CommonGrown difference |
|---|---|---|
| LinkedIn | Identity and networking | Matches concrete commercial needs, not people |
| Marketplaces (e.g. Alibaba) | Products and suppliers | Covers sponsorships, services, clients, partnerships |
| CRM / PRM | Manage existing leads and partners | Discovers new counterparts, then coordinates both sides |
| Sponsorship / partner platforms | Discovery, contracts, tracking | Agents prepare the negotiation in a shared room |

We don't claim nobody has done business matching. Our edge is the **journey from stated need to a meeting-ready proposal**, with consent controls built in.

## 4. User flow

1. **Intake.** A company chats privately with its agent. The agent extracts a structured opportunity (need, budget range, audience, location, categories).
2. **Consent.** The agent shows exactly what it will publish and what stays private. The human approves.
3. **Match.** The matching agent ranks counterparts in the Opportunity Exchange and explains each match.
4. **Mutual interest.** Both sides opt in; only then is more information exchanged.
5. **Deal room.** A shared Switch room opens with both humans, each company's agent, and a facilitator agent.
6. **Prep output.** The room produces a draft proposal, each side's likely sticking points, open questions, and a suggested meeting agenda.
7. **Humans take it from there** into the actual negotiation and agreement.

### 4.1 Flow by person

Two live humans and four agents in the demo. Companies C, D and E (section 4.2) are seeded data with no live human.

| Who | Role |
|---|---|
| **Rina** | Organizer at NusaConf (Company A). Needs sponsors. Live human. |
| **Budi** | Partnerships lead at CloudKita (Company B). Live human. |
| **A-agent** | Rina's agent: intake, consent, represents A in the deal room. |
| **B-agent** | Budi's agent: represents B in the deal room. |
| **Matcher** | Reads the exchange data, ranks matches, explains fit. |
| **Facilitator** | Runs the deal room and writes the meeting-prep output. |

| # | Room | Rina | Budi | Agents |
|---|---|---|---|---|
| 1 | `a-private` | Tells A-agent: "Need sponsors for NusaTech Summit, $50k-$100k." Mentions her floor of $40k. | | **A-agent** extracts a structured opportunity and splits it into *private* (floor, discount room) and *matchable* (range, audience, categories). |
| 2 | `a-private` | Reviews the draft, edits it, replies **approve**. | | **A-agent** waits. It posts nothing to the exchange until she approves. |
| 3 | `exchange` | | | **A-agent** posts the matchable version. **Matcher** replies with ranked matches, each with the four fits, evidence, risks and missing info. |
| 4 | `exchange` | Picks CloudKita; says "open it." | Gets notified; says "interested." | **Matcher** records both opt-ins. **Facilitator** creates the deal room only after both. |
| 5 | `deal-a-b` | Joins. | Joins. | **A-agent** and **B-agent** state each side's approved positions. **Facilitator** summarizes the gap and open questions. |
| 6 | `deal-a-b` | Answers questions, e.g. speaking slot, 2-year option. | Answers questions, e.g. exclusivity, budget timing. | Agents argue their own side using private notes *without revealing them*. **Facilitator** keeps it to the agenda. |
| 7 | `deal-a-b` | Reviews the output. | Reviews the output. | **Facilitator** posts: draft proposal, each side's likely sticking points, open questions, meeting agenda. |
| 8 | offline | Takes the meeting with Budi. | Takes the meeting with Rina. | Agents stop. Humans negotiate and close. |

Alternate branch (shows "no" is a valid answer): Rina also asks about BatikMesin, and the Matcher returns "no fit" with reasons, not a padded recommendation.

### 4.2 Seed data: 5 example companies

All fictional. Together they cover a strong match, a good match with caveats, a near-miss with a better role elsewhere, and a hard no.

| Code | Company | What they are | Opportunity (matchable) | Private (never published) |
|---|---|---|---|---|
| **A** | **NusaConf** (Jakarta) | Tech conference organizer | **Seeks sponsors** for NusaTech Summit: 5,000 attendees, Jakarta, tracks in Cloud / AI / Cybersecurity. Range **$50k-$100k**. | Floor **$40k**; will discount ~15% for a 2-year deal. |
| **B** | **CloudKita** (Singapore) | Cloud provider entering Indonesia | (1) **Wants brand exposure** among Indonesian tech decision-makers, budget **$60k-$120k**. (2) **Seeks an implementation partner** for Indonesian enterprise customers. | Budget ceiling **$90k**; wants exclusive "cloud" category sponsor. |
| **C** | **SecureNusa** (Jakarta) | Cybersecurity vendor | **Wants CISO leads** via events, budget **$40k-$70k**. | Would accept a smaller tier if CISO attendance is proven. |
| **D** | **PromptWorks** (Singapore) | AI software agency | **Seeks enterprise clients** for AI implementation. Small event budget **$5k-$10k**. | Cash is tight until Q2. |
| **E** | **BatikMesin Supply** (Surabaya) | Industrial packaging machine distributor | **Seeks distributors** for machines in Vietnam and Thailand. | Margin floor 18%. |

**Expected results** (what the Matcher should output):

*From A's opportunity (sponsors for NusaTech Summit):*

| Match | Verdict | Business | Commercial | Capability | Strategic | Key note |
|---|---|---|---|---|---|---|
| **B CloudKita** | **Strong** | Yes | Yes ($60k-$120k overlaps $50k-$100k) | Yes | Yes | Risk: exclusivity demand. Missing: attendee seniority split. |
| **C SecureNusa** | **Good, with caveats** | Yes | Partial (low end of A's range) | Yes | Yes | Missing: how many CISOs attend. Might take a smaller tier. |
| **D PromptWorks** | **Weak** | Partial | **No** ($5k-$10k is below sponsor tiers) | n/a | n/a | Suggest a community-partner or booth tier, not a sponsorship. |
| **E BatikMesin** | **No match** | **No** (industry, audience, geography) | No | No | No | Matcher says so plainly and does not pad the list. |

*From B's second opportunity (implementation partner for Indonesian enterprises):*

| Match | Verdict | Why |
|---|---|---|
| **D PromptWorks** | **Strong** | Has the capability and wants enterprise clients, so the *same company that failed as a sponsor succeeds in a different role*. This is the "network of opportunities, not companies" idea. |
| C SecureNusa | No | Not an implementation partner. |

**What this proves in the demo**
- A strong match with a real hidden gap: A's $40k floor vs B's $90k ceiling. Both are inside each other's range, so the deal is possible, and it never leaks.
- A match that needs verification (C), a weak one with an alternative (D), and a clean "no" (E).
- One company (B, D) taking part in different roles in different opportunities.

**Sticking points the Facilitator should surface for A-B:** price within the $50k-$90k overlap, whether "exclusive cloud sponsor" is allowed, deliverables (speaking slot, booth), contract length (1 vs 2 years).

## 5. Core modules

**Opportunity Exchange (the finder).** Where needs and offers live and where counterparts are discovered. Matching is about meaning, not field equality ("needs a sponsor" vs "wants brand exposure"), so it uses **vector search (Chroma)** for recall plus metadata filters for hard constraints, then an LLM to rank and explain. New opportunities can be published live. For the hackathon there is no marketplace UI; the exchange is a Chroma store plus a Switch room.

**Match Intelligence.** Every match shows four fits, with evidence, not one opaque score:

| Dimension | Question |
|---|---|
| Business fit | Do objectives and industries align? |
| Commercial fit | Are budget, pricing and expected value compatible? |
| Capability fit | Can the other side actually deliver? |
| Strategic fit | Is there long-term value? |

Each match also lists: why it fits, supporting evidence, what each side gains, missing information, risks or conflicts, and the next step.

**Verified Match Briefs (the paid product).** Companies spend credits on a brief that only a neutral third party can produce: how trustworthy the counterpart's claims are, and whether the two sides' *hidden* numbers are compatible. Match headlines stay free.

| Output | Cost (illustrative) | Contents |
|---|---|---|
| Match headline | Free | Company, verdict (strong / weak / none), one line why |
| Full brief | 1 credit | Four-fit explanation, risks, missing info, pitch angle |
| Verified brief | 3 credits | The above plus the counterpart's verification level and evidence |
| Private-range check | 2 credits | Yes / no and how wide the overlap is, **never the numbers** |

Verification levels: **L0** self-declared, **L1** domain or email verified, **L2** evidence uploaded (event audience report, company registration).

**Consent and privacy.** Four sharing levels:

| Level | Content |
|---|---|
| Private | Internal conversations, confidential budgets, strategy |
| Matchable | Approved needs, capabilities, matching criteria |
| Mutual interest | Extra info shared after both sides opt in |
| Shared deal | Documents and proposals approved for the room |

Example: a sponsor-seeker publishes "$50k-$100k"; its internal maximum stays private.

**AI Deal Room (on Switch).** The collaboration layer: shared room, persistent context, both companies' humans and agents in one log.

## 5.1 Technical architecture

**Decision: Chroma (embedded) for the exchange.** `pip install chromadb`, local folder as storage, no server and no API key, so anyone can clone the repo and run it. Vector search and metadata filtering happen in one call. Scale-up path: Postgres + pgvector (e.g. Supabase). Caveat: common local embedding models are English-first, so write the seed data in English. Verify Chroma's default embedding model and `where` filter syntax on install.

### System overview

```
 ┌────────────────────────── one laptop ──────────────────────────┐
 │                                                                │
 │  Switch Console runs 4 agents (Claude Code, own folder each):  │
 │                                                                │
 │   A-agent        B-agent        Matcher        Facilitator     │
 │   + private      + private      │                              │
 │     notes          notes        │                              │
 │     │                │          │                              │
 │     │ publish.py     │          │ search.py                    │
 │     └───────┐        │          │                              │
 │             ▼        │          ▼                              │
 │          ┌───────────────────────────┐                         │
 │          │   Chroma "opportunities"  │  (matchable data only)  │
 │          └───────────────────────────┘                         │
 │                                                                │
 │  Switch server: rooms, addressing, permissions, logs           │
 └───────────────────────────────┬────────────────────────────────┘
                                 │ Telegram bot (chat adapter)
          ┌──────────────────────┼──────────────────────┐
          ▼                      ▼                      ▼
    ┌───────────┐         ┌─────────────┐        ┌─────────────┐
    │ a-private │         │  exchange   │        │  deal-a-b   │
    │ Rina      │         │ Rina, Budi  │        │ Rina, Budi  │
    │ A-agent   │         │ A-agent     │        │ A-agent     │
    └───────────┘         │ B-agent     │        │ B-agent     │
                          │ Matcher     │        │ Facilitator │
                          └─────────────┘        └─────────────┘
```

### Matching pipeline

```
 Rina's approved opportunity  (A.seeks, A.offers, budget, region)
                │
                ▼  A-agent calls publish.py (matchable fields only)
        ┌───────────────┐
        │    Chroma     │  each opportunity stored as 2 documents:
        │  collection   │   kind="offers"  → text of what they offer
        │ "opportunities"│   kind="seeks"   → text of what they want
        └───────┬───────┘
                │  Matcher calls search.py
                ▼
 1. Vector query   A.seeks  ─►  others' kind="offers"      (meaning)
 2. Metadata filter  budget overlap · region · status=open  (hard limits)
 3. Reverse check  A.offers ─►  others' kind="seeks"       (is it mutual?)
                │
                ▼  ~10 candidate rows
 4. Matcher (LLM) reads the candidates, ranks them with the four fits,
    writes: why it fits · evidence · risks · missing info · next step
                │
                ▼
      Post ranked matches to the `exchange` room
```

### Data model (Chroma collection `opportunities`)

| Field | Where | Example |
|---|---|---|
| `document` | text, embedded | "Looking for sponsors for NusaTech Summit, 5,000 tech professionals, Cloud/AI/Cybersecurity tracks" |
| `kind` | metadata | `seeks` or `offers` |
| `company`, `opp_id` | metadata | `NusaConf`, `O1` |
| `budget_min`, `budget_max` | metadata (number) | 50000, 100000 |
| `region` | metadata | `Indonesia` |
| `status` | metadata | `open` |
| `verified_level` | metadata | `L0`, `L1`, `L2` |

Budget overlap filter: `budget_min <= A.max AND budget_max >= A.min`.

### Privacy by construction

- **`publish.py` takes a fixed list of fields** (the matchable level). There is no field for private notes, so a floor like "$40k" cannot be written to the exchange by mistake. This is a code-level consent gate, not only a prompt rule.
- **Private notes** live as files in each company agent's own folder, outside Chroma and outside any room.
- **A-agent only calls `publish.py` after Rina replies "approve"** in `a-private`.
- **Rooms:** `a-private` has only Rina and A-agent; the Matcher is never in it. Every agent receives all messages in its rooms, so nothing private is ever posted to `exchange` or `deal-a-b`.

### Credits and verified briefs

```
Rina: "@a-agent full brief on CloudKita"
        │
        ▼
   brief.py ──► accounts.db :  credits(NusaConf) ≥ cost ?
        │                           │
        │ yes                       │ no
        ▼                           ▼
 deduct credits                post headline only +
 run match (Chroma)            "Brief locked: 0 credits. Top up."
 read verified_level
 (optional) overlap.py reads both companies' private notes
            and returns only a verdict, never the numbers
        │
        ▼
 post brief to the room
```

`accounts.db` (SQLite, built into Python; balances need atomic updates, so they stay out of Chroma):

| company | plan | credits | verified_level |
|---|---|---|---|
| NusaConf | paid | 10 | L1 |
| CloudKita | paid | 0 | L2 |
| SecureNusa | free | 0 | L0 |
| PromptWorks | free | 0 | L0 |
| BatikMesin | free | 0 | L0 |

- `brief.py` checks the balance before doing any work and deducts after delivering.
- A company with 0 credits sees headlines and a locked brief. This is the visible paywall in the demo.
- No real payments: top-up is a script that adds credits.
- Our own LLM cost per brief must stay below its credit price. Switch Trust's cost tracking shows per-agent spend and monthly caps, but caps do not block spending and the docs do not say whether Switch Rooms agents report to it, so credits are enforced in our own script.

**Why this is hard to bypass:** the private-range check needs *both* sides' hidden bounds (for example A's $40k floor and B's $90k ceiling). Two companies on a video call cannot do this for each other without revealing the numbers, which is exactly what they want to avoid before negotiating.

**Limit (state it in the README):** this is a trusted-broker design, not cryptography. The platform sees both private notes. Real privacy-preserving matching (MPC, clean rooms) is later work. Verification is a flag in the demo, not a real document check.

### Components and who owns what

| Component | Built by us? | Notes |
|---|---|---|
| Rooms, agent identity, addressing, permissions, chat bridge | No (Switch) | Telegram adapter via Switch Console |
| Agent instructions (A, B, Matcher, Facilitator) | Yes | Prompts, one folder per agent |
| `publish.py`, `search.py` | Yes (~20-40 lines each) | Chroma read and write |
| Seed data (5 companies) | Yes | Loaded into Chroma at startup |
| Embeddings | No | Chroma default, local |
| `brief.py`, `overlap.py`, `accounts.db` | Yes | Credit gate, verified briefs, private-range check (SQLite) |

## 6. Hackathon scope (Nov 4-7)

Switch must be central: the project should break without it, and a person plus at least one agent must complete a real task together in the chat.

**Build for real**
- Intake agent with the consent step.
- Matching agent over seeded data, with the four-fit explanation.
- Deal room in Switch: Company A agent, Company B agent, facilitator agent, one human per side.
- Meeting-prep output (draft proposal, sticking points, agenda).
- Credit gate: a company with credits gets a full brief; one with 0 credits gets headlines and a locked brief.
- Private-range check: `overlap.py` returns "compatible, narrow overlap" without revealing either side's number.

**Seeded / faked**
- `accounts.db` with the credit balances and verification levels from section 5.1 (no real payments or document checks).
- The 5 fictional companies from section 4.2, loaded into the Chroma exchange at startup (stands in for Company Passport). New opportunities published during the demo are written to the same store live.

**Out of scope**
- Full marketplace UI, billing, verification, deal tracking, real cross-company Switch federation. Use one shared room for the demo.

**Demo script**
1. Company A states: "Looking for sponsors for our tech conference."
2. Agent extracts the opportunity; human approves what is shared.
3. Three matches appear, each with a fit breakdown and risks.
4. Company A and one match opt in.
5. Shared Switch room opens; agents and humans work through terms.
6. Output: draft proposal plus meeting agenda.

**Telegram setup (from the [Switch Telegram docs](https://docs.switchagents.ai/switch-rooms/deploy/messaging-apps/telegram.md))**
1. Create a bot with @BotFather (`/newbot`); save the token (shown once).
2. In BotFather, turn **Group Privacy off before** adding the bot to any group. Otherwise agents see only mentions, and fixing it means removing and re-adding the bot.
3. In Switch Console: Home > Messaging apps > Connect > Telegram; enter name, token and bot username.
4. Create the three groups by hand (Switch can't create Telegram channels): `a-private` (Rina + bot only), `exchange`, `deal-a-b` (Rina, Budi, bot). Add the bot as a member; Switch makes a room per group.
5. Each human posts once in their group, then uses **Link account** in Console. An unlinked account matches no one, so the agent will ignore them.
6. Add the agents to the right rooms and set "Who can talk to your agent" so Budi can address B-agent.
7. Use one bot token per environment, since two processes sharing a token split incoming messages.

Telegram gotchas: agent names don't autocomplete (type them in full; `!list-agents` shows them); messages over 4096 characters are split and tables arrive as plain text, so tell the agents to reply in short bullet lists.

**Submission checklist:** repo that others can clone and run, README showing how Switch is used, demo video.

## 7. Market and launch focus

Cold start is the main marketplace risk, so start narrow:

- **Region:** Southeast Asia (starting with Indonesia).
- **Segments:** tech companies, event and conference organizers, software agencies, SaaS, IT consultants/MSPs, distributors and channel partners, corporate partnership teams.
- **Opportunity types:** sponsorships, client/project acquisition, strategic and channel partnerships (all share one structure: one side has a need, the other has a resource that satisfies it).

**Business model: charge for what stays in our system.** Companies can take a meeting to Zoom or WhatsApp without us, so we do not charge per introduction or per closed deal (we cannot see or attribute either). We charge where value is delivered before the meeting and cannot be copied outside:

- **Credits for Verified Match Briefs** (section 5): headlines free; full briefs, verified briefs and private-range checks cost credits. Credit prices are placeholders and must stay above our LLM cost per brief.
- **Why it holds:** the private-range check needs both sides' hidden numbers, and verification evidence lives with us.
- **Later:** annual plans for heavy users, white-label private networks for communities and conference series, enterprise-grade privacy-preserving matching.
- **Avoid:** a take rate on closed deals (leaks offline and cannot be attributed).

## 8. Evidence and open risks

What the research supports:
- Gartner: [61% of B2B buyers prefer a rep-free experience](https://www.gartner.com/en/newsroom/press-releases/2025-06-25-gartner-sales-survey-finds-61-percent-of-b2b-buyers-prefer-a-rep-free-buying-experience) (2025 survey of 632 buyers); a [later survey reports 67%](https://gcomdr.pdo.aws.gartner.com/en/newsroom/press-releases/2026-03-09-gartner-sales-survey-finds-67-percent-of-b2b-buyers-prefer-a-rep-free-experience). The same release says buyers still want sellers for judgment-heavy tasks like assessing fit.
- McKinsey B2B Pulse reportedly shows buyers wanting in-person, remote and self-serve in roughly equal measure ([secondary coverage](https://europeanbusinessmagazine.com/business/mckinsey-companys-ninth-global-b2b-pulse-survey/); primary report not checked).

Open risks and unknowns:
- **Offline preference.** Those studies cover product buying. Sponsorship and partnership deals are likely more relationship-driven; this is unverified. No Indonesia/SEA data on meeting-vs-online preference was found.
- **Indonesian B2B marketplace history is mixed.** Ula raised an [$87M Series B](https://www.thejakartapost.com/paper/2021/10/05/e-marketplace-ula-raises-87m-from-tencent-jeff-bezos.html) and reportedly shut its core B2B operations in 2023 ([secondary source](https://ideaproof.io/failure/ula-indonesia)); Mitra Bukalapak did better by [digitizing existing offline relationships](https://kr-asia.com/bukalapak-adapts-beyond-metro-areas-to-face-off-with-tokopedia-and-shopee-ahead-of-idx-listing) (our reading, not a documented analysis).
- **Trade-show statistics** from vendor blogs are biased and unsourced; do not cite them.
- **Privacy trust.** Companies won't join if confidential discussions can leak to competitors. The consent model is a product requirement, not a nice-to-have.
- **Willingness to pay is unvalidated.** Interview question: would you pay for a brief that confirms the counterpart's claims and tells you whether your budgets are compatible, before the first meeting?
- **Trusted-broker limit.** The private-range check requires users to trust the platform with both sides' private numbers. This is not cryptographic privacy.

**Validation to do (post-hackathon):** interview 5-10 event organizers and B2B service sellers; ask where their last three deals came from and what slowed them down before the first meeting.

## 9. Positioning line

**CommonGrown: the AI-powered business opportunity network that finds the right counterpart and gets both sides meeting-ready.**

Three promises: **Discover** opportunities you wouldn't have found. **Match** with a clear explanation of fit. **Prepare** so the first meeting is about the deal, not the basics.
