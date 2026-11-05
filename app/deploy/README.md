# Deploying on Google Cloud

The running demo is one `e2-small` VM (`commongrown-demo`, `us-central1-a`) with two things on it:

- the **Switch server** (upstream Docker Compose: switch-core, gateway, Postgres at `/opt/commongrown-switch`, API on `127.0.0.1:8000`, with the Telegram bridge enabled), and
- the **CommonGrown worker** (`commongrown.service`, installed in `/opt/commongrown`, data in `/var/lib/commongrown`).

The worker reaches Switch over loopback. Nothing is exposed publicly: SSH is IAP-only, there is no app port, no reserved IP and no VM service account. Telegram traffic goes out from the Switch bridge. The Switch Console and Gateway admin UI are reached through an IAP tunnel. The VM has **no auto-stop**, so it bills continuously; stop it when you are done.

## Commands (run from `app/`)

```sh
PROJECT_ID="$(gcloud config get-value project)"
python3 deploy/gcloud.py plan   --project "$PROJECT_ID"   # print the commands, change nothing
python3 deploy/gcloud.py create --project "$PROJECT_ID"   # network, firewall, VM
python3 deploy/gcloud.py upload --project "$PROJECT_ID"   # ship source, install, repeatable
python3 deploy/gcloud.py start|stop|status --project "$PROJECT_ID"
python3 deploy/gcloud.py ssh    --project "$PROJECT_ID"
python3 deploy/gcloud.py tunnel --project "$PROJECT_ID"   # localhost:8080 -> VM Switch API (port 8000)
```

`upload` is repeatable and preserves `/var/lib/commongrown` and configuration. The archive contains only whitelisted source (no `.env`, databases, notes or virtualenvs). `create` stops on errors and never overwrites same-name resources.

## One-time setup on the VM

1. Install Switch from its [self-host guide](https://docs.switchagents.ai/switch-rooms/deploy/self-host); connect the Telegram bot (BotFather token, **Group Privacy off before adding the bot to any group**).
2. Put the model settings in `/etc/commongrown/worker.env` (`AGENT_BASE_URL`, `AGENT_MODEL`, `AGENT_API_KEY`; root:commongrown, mode 640). Never put secrets in arguments or the archive.
3. Create `/etc/commongrown/switch.json` from `switch.example.json`:

```json
{
  "url": "http://127.0.0.1:8000",
  "name": "commongrown2",
  "allow_claim_seeded": true,
  "open_companies": ["Acme Events", "CloudKita", "PromptWorks", "SecureNusa", "BatikMesin Supply"],
  "daily_limit": 25
}
```

`name` must match the agent name registered in Switch. `allow_claim_seeded` lets a group `/setup` a seeded company. `open_companies` lets any member of those groups act (public demo); leave it out for normal owner-only groups.

4. Register the agent once with a registration key from the Switch API Keys page, then start the service. The identity is stored at `/var/lib/commongrown/switch-identity.json` (mode 600); do not register again on restart.

```sh
read -r -s -p 'Switch registration key: ' SWITCH_REGISTRATION_KEY; export SWITCH_REGISTRATION_KEY
sudo --preserve-env=SWITCH_REGISTRATION_KEY -u commongrown env COMMONGROWN_DATA=/var/lib/commongrown \
  /opt/commongrown/.venv/bin/python /opt/commongrown/switch_worker.py register --config /etc/commongrown/switch.json
unset SWITCH_REGISTRATION_KEY
sudo systemctl enable --now commongrown
```

5. In Switch, set the agent's addressing policy to Open so Telegram users can mention it (an agent cannot change its own policy), and give it a friendly display name in the Gateway.

## Add a company group

Add the bot to a Telegram group, run `!invite-agent @commongrown2` once, then `@commongrown2 /setup <Company>`. History from before the bot joined is not visible to it.

## Reset the demo

With the worker stopped (`sudo systemctl stop commongrown`):

```sh
sudo -u commongrown env COMMONGROWN_DATA=/var/lib/commongrown PYTHONPATH=/opt/commongrown \
  /opt/commongrown/.venv/bin/python /opt/commongrown/reset_demo.py
sudo systemctl start commongrown
```

This wipes accounts, facts, Chroma and histories, then loads the seeded accounts and background opportunities. It keeps the Switch identity. Groups must run `/setup` again.

## Operations notes

- **Logs:** `journalctl -u commongrown -f` shows one line per Switch event and any connection loss.
- **Delivery:** one serial worker, a separate socket reader that keeps Switch pings alive during model calls, a process lock against duplicate workers, and per-message result caching so a replay does not charge a brief twice. Delivery is at-least-once.
- **Cost:** the model is called only for fact extraction, drafting, ranking, briefs and meeting prep. Credits are product billing, not a Google spend cap. `daily_limit` bounds heavy requests per group.
- **Isolation:** application-level on a trusted broker; the operator can read stored data. Per-company data is separated under `/var/lib/commongrown/companies/<hash>/` and shared rooms under `shared/<hash>/`; the hash is a storage key, not encryption.
- **Backups:** copy `/var/lib/commongrown` with the worker stopped, and back up Switch's Postgres separately.
