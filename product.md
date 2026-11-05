# CommonGrown

**AI finds the right counterpart. AI prepares both sides. Humans close the deal.**

An AI-powered B2B opportunity network that lives in a company's Telegram group. Employees just talk; an agent on Switch keeps a summary of what the company needs and offers, publishes only with the owner's approval, finds compatible counterparts and explains the fit, so the first real meeting starts from the deal.

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
| Prepare both sides for the meeting | Agents (briefs; deal-room prep is implemented but not shown live) |
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

The product lives where teams already talk: a **company Telegram group**. Nobody fills in a form or chats privately with a bot; employees discuss work normally and the bot (an agent on Switch) listens.

1. **Link.** Someone adds the bot to the group and runs `!invite-agent @commongrown2`, then `@commongrown2 /setup <Company>`. They become the **owner**. The bot explains in plain language what it does and does not keep.
2. **Listen.** As people talk, the bot folds the discussion into a structured summary of **needs, offers, constraints and facts**, each marked shareable or private. The raw messages are deleted after summarizing; only the summary is stored. Newer statements replace older ones, and contradictions are flagged to the owner.
3. **Suggest.** When it sees an unpublished need, the bot asks the owner. A first "yes" produces a draft built only from shareable facts, showing where each line came from. A second "yes" publishes it and searches. Never on a single yes.
4. **Match.** Chroma recall plus the model ranks the top candidates, explaining the four fits, risks and missing information. A clear "no match" is a valid answer.
5. **Brief.** Headlines are free; a full brief costs a credit. A company with no credits sees the headlines and a locked brief.
6. **Humans take it from there** into the real conversation. (The mutual-interest and deal-room commands exist and are unit-tested, but were not run live for the hackathon.)

### 4.1 Demo companies and expected results

Five live Telegram groups (Acme Events, CloudKita, PromptWorks, SecureNusa, BatikMesin Supply) run the real flow. Background companies are loaded by `reset_demo.py` so each need has real alternatives: TechSprint Expo (sponsor-seeking dev conference), NimbusID (cloud provider with sponsorship budget), Samudra Systems (AI implementation partner for banks and telcos), SiamPack Distribution (packaging distributor in Thailand and Vietnam), and CloudKita's second opportunity (implementation partner).

| Group | Says in chat | Result |
|---|---|---|
| **Acme Events** (Jakarta, tech summit) | Needs sponsors; a $40k floor and a 5,000-vs-6,000 attendee disagreement | NimbusID, good match. The floor stays private; the disagreement is flagged. |
| **CloudKita** (cloud provider) | Wants exposure, shares a $60k–$120k range, keeps a $90k ceiling private | Acme Events, good match. NimbusID is correctly "no match". Brief is locked at 0 credits. |
| **PromptWorks** (AI agency) | Wants enterprise clients, small event budget | CloudKita's implementation-partner role: the same company that fails as a sponsor succeeds in another role. |
| **SecureNusa** (security vendor) | Wants CISO leads via events | Honest weak fit with Acme. |
| **BatikMesin Supply** (machines) | Wants distributors in Vietnam and Thailand | SiamPack Distribution, good match. |

A paid brief is then delivered to Acme (3 credits to 2).

## 5. Core modules

**Opportunity Exchange.** Needs and offers live in a **Chroma** collection (two documents per opportunity: what it seeks, what it offers) with fixed public metadata (budget range, region, status, verification level). Matching is about meaning ("needs a sponsor" vs "wants brand exposure"), so vector recall runs in both directions with hard filters on status and budget overlap, then the model ranks and explains. There is no marketplace UI.

**Match Intelligence.** Each match shows four fits, with evidence, not one opaque score:

| Dimension | Question |
|---|---|
| Business fit | Do objectives and industries align? |
| Commercial fit | Are budget, pricing and expected value compatible? |
| Capability fit | Can the other side actually deliver? |
| Strategic fit | Is there long-term value? |

Each match also lists what each side gains, risks, missing information, a pitch angle and the next step.

**Verified Match Briefs (the paid product).** Headlines stay free; a brief is what only a neutral third party can produce.

| Output | Cost | Contents |
|---|---|---|
| Match headline | Free | Company, verdict (strong / good / weak / none), one line why |
| Full brief | 1 credit | Four-fit explanation, risks, missing info, pitch angle |
| Verified brief | 3 credits | The above plus the counterpart's verification level |
| Private-range check | 2 credits | Compatible or not, and how wide the overlap is; **never the numbers** |

New companies start with 3 credits. Verification levels (L0 self-declared, L1, L2) are demo flags, not real checks.

**Consent and privacy.** Four sharing levels: **private** (internal talk, floors and ceilings), **matchable** (approved needs and ranges), **mutual interest** (extra info after both opt in), **shared deal** (documents approved for the room). The owner approves what is published; confidential facts never appear in a draft, a match or another company's view.

## 5.1 Technical architecture

**Switch is the backbone.** The agent is registered on a self-hosted Switch server and talks over Switch's WebSocket agent protocol. Switch provides the Telegram bridge (one bot, a room per group), room membership and identity, the addressing policy, and the message log. The worker adds the broker logic. One agent serves every company group.

```
 Telegram groups (one per company)
        │  Switch Telegram bridge: one bot, a Switch room per group
        ▼
 ┌─────────────── GCP VM (e2-small) ────────────────┐
 │  Switch server (Docker: core, gateway, Postgres) │
 │        │ WebSocket agent protocol                │
 │        ▼                                         │
 │  CommonGrown worker (Python, one serial queue)   │
 │    ├─ accounts.db (SQLite): credits, groups,     │
 │    │    facts, consent, evidence buffer          │
 │    ├─ Chroma: public opportunities (embedded)    │
 │    └─ OpenAI Agents SDK ─► your model endpoint   │
 └──────────────────────────────────────────────────┘
```

| Layer | Choice | Why |
|---|---|---|
| Chat, rooms, identity, bridge | Switch + Telegram | Teams already use chat; the product breaks without it |
| Matching store | Chroma, local `all-MiniLM-L6-v2` | Vector search plus metadata filters in one call, no server or key |
| Accounts, facts, consent, credits | SQLite | Atomic balance updates, simple, in Python's stdlib |
| Model | OpenAI Agents SDK, any OpenAI-compatible endpoint | Scoped tools, validated output |
| Hosting | One GCP VM, IAP-only SSH | Low cost, nothing exposed publicly |

### Facts, not stored chat

Each group has a buffer of raw messages (24 hours, 40 per room). Every few messages, and when a need seems to appear, the model folds the buffer into facts (kind, key, value, public or private, a short snippet) and the raw messages are deleted. Sources are shown only as `owner`, `member N` or `team`; raw chat IDs never reach the model. A statement replaces an earlier fact with the same key; conflicts are kept for the owner to settle. `/facts` shows what is known, `/forget` wipes it.

### Privacy by construction

- The public record has fixed fields, with no field for private notes, so a floor cannot be written to the exchange by mistake. This is a code-level gate, not just a prompt rule.
- Private facts are excluded from drafting prompts.
- Only the group owner (or any member in the public demo groups) can say "yes" or spend credits; the model cannot approve its own drafts.
- Credits are checked and debited atomically; a failed generation refunds, and a replay returns the saved result.

**Limit (stated in the README):** a trusted-broker design, not cryptography. The platform can read stored facts. Privacy-preserving matching (MPC, clean rooms) is later work.

## 6. Hackathon scope (Nov 4-7)

Switch must be central: the project should break without it, and a person plus an agent must complete a real task together in chat.

**Built and run live**
- Self-serve group onboarding, listening, facts with a privacy split, proactive suggestion with two-yes publishing.
- Matching over seeded and live opportunities with four-fit explanations.
- Credit gate: a locked brief at 0 credits, a delivered brief with credits.
- Plain-language replies, "working on it" notices for slow requests, a per-group daily cap.
- Five real company groups with logos, and a reset tool for a clean demo.

**Implemented, tested, not shown live**
- Mutual interest, shared positions, private-range check and meeting-prep commands.

**Out of scope**
- Marketplace UI, real payments or verification, deal tracking, cross-company federation, company-name verification at `/setup`.

**Submission checklist:** repo others can clone and run, README showing how Switch is used, demo video.

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
