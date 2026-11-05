# CommonGrown

An AI opportunity network for B2B companies, built on [Switch](https://github.com/sandboxaq/switch). Employees just talk in their company's Telegram group. The CommonGrown agent listens, keeps a short structured summary of the company's needs, offers, constraints and facts (not the chat), asks the owner before publishing anything, then finds partners, sponsors or clients on a shared exchange.

## Try it in 30 seconds (no install, no password)

Join a company group, then just talk like your team would. The bot listens and speaks up when it notices a need.

| Company | Join |
|---|---|
| Acme Events (event organiser seeking sponsors) | https://t.me/+64cIxX2hXdBlZWU1 |
| CloudKita (cloud provider) | https://t.me/+-jpNEHao4sA3YmU9 |
| PromptWorks (AI consultancy) | https://t.me/+EdESi2Lq_7YyOGZl |
| SecureNusa (security vendor) | https://t.me/+i9EBMsZ648E4MjRl |
| BatikMesin Supply (manufacturer) | https://t.me/+hxQ54Wtfl25lMGQ9 |

Things to try (mention the bot with `@commongrown2`):
- Chat about a need, e.g. "we need a sponsor for our June summit, budget around 60-100k". The bot offers to publish; reply **yes** twice (it never publishes on one yes).
- `@commongrown2 /facts` shows what it knows. Confidential numbers (floors, ceilings) are kept private.
- `@commongrown2 /matches` finds partners. Headlines are free; `@commongrown2 /brief <my ID> <their ID> full` costs a credit.
- `@commongrown2 /status` shows credits.

Limits: in these demo groups any member can approve and run commands. Each group is capped at 25 model-heavy requests a day, and matching takes 40-70 seconds. Replies say "working on it" first. Data is demo data and may be reset.

To use it for your own company: add `@CommonGrown_Bot` to your group, run `!invite-agent @commongrown2`, then `@commongrown2 /setup <Company>`. You become the owner.

## How it works

See [product.md](product.md) for the flow and [app/README.md](app/README.md) for the code. Python worker on Switch's WebSocket agent protocol, OpenAI-compatible model, SQLite for accounts and facts, Chroma for matching, deployed on a GCP VM. Demo video: `assets/video/` (not in git, see submission).
