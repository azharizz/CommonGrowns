# Google Cloud: one shared worker, on-demand VM

This uses **one Python worker and request-scoped OpenAI Agents SDK runs**. The existing Factory and Decorator patterns remain. SQLite
and Chroma stay on persistent disk. No Kubernetes, Cloud SQL, load balancer,
NAT Gateway, managed vector service, or four always-running model clients.

**Nothing has been deployed.** The installed `gcloud` CLI was inspected and a
read-only plan was generated. Compute Engine is disabled in the currently
configured project; `create` below explicitly enables the required APIs.

## Cost controls

- One `e2-small` VM, 2 GB RAM, with a 20 GB standard persistent disk. This is a
  starting size for the worker, not a load-tested promise for an entire Switch
  server stack. Swap is not used as a substitute for measurement.
- Compute Engine stops the VM **two hours after every start** using
  `--max-run-duration=2h --instance-termination-action=STOP`. Disk survives.
  This is a maximum session duration, not an idle detector: a long active
  session also stops at two hours. Start it again when needed.
- Explicit `start` and `stop` commands. A Telegram message does **not** wake a
  stopped VM. This is on-demand demo hosting, not automatic request scale-to-zero.
- Ephemeral public IPv4 only for outbound provider/Telegram access. Inbound SSH
  is restricted to Google's IAP range. No public app port, reserved IP or NAT.
- The configured `.env` model is called only for intake, matching or preparation.
  Deterministic consent/credit commands do not call a model. History sent to
  intake is bounded to eight turns and 24,000 characters; output is capped at
  4,096 tokens per model call with at most five turns. Credits are product billing, not a Google spend cap.
- While stopped, disk/backups and any other retained billable resources can
  still cost money. Configured provider calls, IPv4 and network usage are additional. Credit
  eligibility must be checked in your Google Billing account; none is assumed.

See [VM stop/start](https://cloud.google.com/compute/docs/instances/stop-start-instance),
[VM runtime limits](https://cloud.google.com/sdk/gcloud/reference/compute/instances/create),
and your configured API provider pricing.

## Review and provision with gcloud

From `app/`, first inspect the plan (no cloud mutations):

```sh
PROJECT_ID="$(gcloud config get-value project)"
python3 deploy/gcloud.py plan --project "$PROJECT_ID"
```

The default zone is `us-central1-a`. Pass the same `--zone` to every operation
if changing it. This favors low demo cost; choose an appropriate region if
latency or data-residency requirements matter. The AI endpoint comes from your configuration; choose its region according to
your data-residency requirements.

**Only when ready to deploy**, run:

```sh
python3 deploy/gcloud.py create --project "$PROJECT_ID"
python3 deploy/gcloud.py upload --project "$PROJECT_ID"
```

`create` provisions the named VPC/subnet, an IAP-only SSH firewall rule,
and one VM without an attached service account or API scopes. The operator needs permission to create those
resources plus IAP tunneling/OS Login administration access. Model access uses
your configured API key, not Google credentials.

Creation is intentionally explicit and stops on errors; existing same-name
resources are not overwritten. If creation partially succeeds, inspect the
printed plan/status and finish the missing commands rather than deleting data.
`upload` can be repeated; it preserves `/var/lib/commongrown` and configuration.
Its source archive excludes local databases, private notes, credentials and
virtual environments. The installation seeds only fictional data and downloads
Chroma's local embedding model. No LLM request runs during installation.

## Connect Switch once

The worker connects to a **real Switch server**. This script deploys CommonGrown,
not Switch's upstream server/PostgreSQL stack. Use an existing reachable Switch
host, or install the upstream [version-pinned Compose deployment](https://docs.switchagents.ai/switch-rooms/deploy/self-host)
on the VM. Co-hosting may require a larger machine; measure that stack before
choosing. Run only the shared worker.

```sh
python3 deploy/gcloud.py ssh --project "$PROJECT_ID"
```

On the VM:

1. Copy `/etc/commongrown/switch.example.json` to
   `/etc/commongrown/switch.json`, owned by `root:commongrown`, mode `640`.
2. Set the real Switch server URL. Remote URLs require HTTPS. Loopback HTTP is
   allowed for a server on the same machine. No API key belongs in this file.
3. Replace every placeholder with actual **Switch user IDs and room IDs**.
   Display names and a `company_id` supplied in chat are not authentication.
   The server's `payload.sender` value is matched exactly to the configured ID.
4. Configure the room memberships: Rina + shared agent in `a-private`, Budi +
   shared agent in `b-private`; both humans + shared agent in `exchange`.
   Create/activate the shared deal room only after mutual interest.
5. Register one agent, using a registration key created in Switch's API Keys
   page. Run the following as a trusted operator; the key is not saved in source:

```sh
read -r -s -p 'Switch registration key: ' SWITCH_REGISTRATION_KEY
printf '\n'
export SWITCH_REGISTRATION_KEY
sudo --preserve-env=SWITCH_REGISTRATION_KEY -u commongrown \
  env COMMONGROWN_DATA=/var/lib/commongrown \
  /opt/commongrown/.venv/bin/python /opt/commongrown/switch_worker.py register \
  --config /etc/commongrown/switch.json
unset SWITCH_REGISTRATION_KEY
```

The agent API key and persistent connection ID are stored mode `600` in
`/var/lib/commongrown/switch-identity.json`. Do not register again on restart.
In Switch, allow the two linked humans to address this agent and invite it into
the correct rooms. Registration defaults do not automatically authorize Budi.
Then start the worker:

```sh
sudo systemctl start commongrown
sudo systemctl status commongrown
```

Before starting the service, securely set `AGENT_BASE_URL`, `AGENT_MODEL`, and
`AGENT_API_KEY` in `/etc/commongrown/worker.env` (root:commongrown, mode 640).
Use the same values as your local `.env`; never put secrets in command arguments
or source archives. The deployment intentionally does not upload your `.env`.
The only model runtime is the OpenAI Agents SDK. It uses Chat Completions tools
against that endpoint, with bounded turns and tracing disabled. The service has
no Google AI role, ADC requirement, or alternate model-provider fallback.

## Work in chat

Address `@commongrown` in the appropriate room. Plain text in a private room
starts intake. The worker shows a structured draft and hash; it cannot approve
its own output. Explicit human commands drive business mutations:

| Command | Where / effect |
| --- | --- |
| `/draft JSON` | Private; stage a public opportunity belonging to your company |
| `/approve HASH` | Private; publish that exact reviewed draft |
| `/private {"notes":"...","ranges":{"A1":{"min":40000,"max":100000}}}` | Private; replace only your company's confidential record |
| `/matches A1` or `/matches A1 E1` | Public facts only; free headlines |
| `/brief A1 B1 full` | Private; paid brief, source must belong to the sender |
| `/brief A1 B1 verified` | Private; demo verification decorator |
| `/interest A1 B1` | Record only the authenticated human's company opt-in |
| `/share A1 B1 {"position":"...","questions":["..."]}` | Private; stage extra shared information and return review hash |
| `/approve-share A1 B1 HASH` | Private; approve that company's exact shared position |
| `/range-consent A1 B1` | Private; explicitly authorize coarse private comparison |
| `/brief A1 B1 range` | Private; requires both consents and credits |
| `/prepare A1 B1` | Bound deal room; proposal, sticking points, questions, agenda |
| `/withdraw A1 B1` | Revoke local opt-in/sharing; operator also removes Switch access |
| `/balance` | Private; only the sender company's balance |

After mutual interest, the operator creates the room in Switch (Telegram groups
are created by humans), adds its real ID to the config and binds it locally:

```sh
sudo -u commongrown env COMMONGROWN_DATA=/var/lib/commongrown \
  /opt/commongrown/.venv/bin/python /opt/commongrown/deal.py bind-room A1 B1 \
  --room-id ACTUAL_SWITCH_ROOM_ID
sudo systemctl restart commongrown
```

Do not put command text from documents/model replies back into the worker as
human events. Only direct addressed `message` events from Switch are processed.

## Isolation and delivery

Private files are physically separated by company under
`/var/lib/commongrown/companies/<SHA-256(company)>/`: `private.json` and
`history.db`. Within each history file, room IDs isolate conversations. Shared
room histories live separately under `shared/<SHA-256(room)>/history.db`.
The hash is a safe storage key, not encryption. SQLite broker state still holds
company-keyed approvals, accounts and paid artifacts; the worker checks the
authenticated company before invoking those operations.

The model never picks the sender, company, room or recipient. A server-side
allowlist and current mutual-interest/room binding choose the scope. Private
intake sees its company's history and notes. Matcher sees public records only.
Facilitator sees approved shared positions only. No global LLM chat session,
file tools, shell tools or cross-company memory is exposed to the model.

One serial consumer does the work; a separate async socket reader keeps Switch
pings alive during inference. A process lock prevents duplicate worker
instances. Results are cached per room/message ID so a replay does not charge
or regenerate a successful response. Forwarding is retried separately.
Delivery is at-least-once: a lost acknowledgment after a successful post can
produce duplicate text, but not a second paid brief charge. Gaps/replaced
connections stop with exit 78 for operator reconciliation rather than skipping
unseen consent events. First startup begins at the current event head; address
the agent after it connects, not while the VM is off.

This is **application-level isolation on a trusted broker**, not separate OS
tenants or cryptographic privacy. The service account/operator can read the
stored data. Private room membership must also be correctly configured in Switch.
Back up all of `/var/lib/commongrown` with the worker stopped, and separately
back up Switch's PostgreSQL database if self-hosting it. Neither deletion nor
withdrawal can recall already posted room messages.

## Start and stop

```sh
python3 deploy/gcloud.py start --project "$PROJECT_ID"
python3 deploy/gcloud.py status --project "$PROJECT_ID"
python3 deploy/gcloud.py stop --project "$PROJECT_ID"
```

For a co-hosted Switch server listening on loopback port 8080,
`python3 deploy/gcloud.py tunnel --project "$PROJECT_ID"` opens a private IAP
SSH port forward to `localhost:8080`. This creates no public firewall rule.

A synthetic SDK/provider smoke test is available in `smoke_ai.py`. Unit tests use fake
collections/providers/events and temporary local databases. Google VM sizing,
Switch protocol compatibility with your installed release and actual provider
cost/availability still require the later integration pass.

Latest verification: 43 unit tests passed, plus a live synthetic SDK smoke run
using the configured `.env` endpoint/model/key. The smoke confirmed one scoped
context tool call and one accepted submission. No company-private data was sent.
