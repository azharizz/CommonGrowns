#!/usr/bin/env bash
set -euo pipefail
project_id="${1:?Google Cloud project ID is required}"
[[ "$project_id" =~ ^[a-z][a-z0-9-]+$ ]] || exit 1
apt-get update -qq
apt-get install -y -qq python3-venv ca-certificates
id commongrown >/dev/null 2>&1 || useradd --system --create-home --home-dir /var/lib/commongrown commongrown
install -d -m 700 -o commongrown -g commongrown /var/lib/commongrown
install -d -m 750 -o root -g commongrown /etc/commongrown
python3 -m venv /opt/commongrown-tools
/opt/commongrown-tools/bin/pip install --quiet uv
/opt/commongrown-tools/bin/uv sync --locked --project /opt/commongrown --python /usr/bin/python3
if [[ ! -f /etc/commongrown/worker.env ]]; then
  printf 'COMMONGROWN_DATA=/var/lib/commongrown\n' > /etc/commongrown/worker.env
  chmod 640 /etc/commongrown/worker.env
  chown root:commongrown /etc/commongrown/worker.env
fi
install -m 644 /opt/commongrown/switch.example.json /etc/commongrown/switch.example.json
install -m 644 /opt/commongrown/deploy/commongrown.service /etc/systemd/system/commongrown.service
systemctl daemon-reload
systemctl enable commongrown.service
sudo -u commongrown env HOME=/var/lib/commongrown COMMONGROWN_DATA=/var/lib/commongrown /opt/commongrown/.venv/bin/python /opt/commongrown/seed.py
printf '%s\n' 'Installed. Configure AGENT_BASE_URL, AGENT_MODEL, AGENT_API_KEY in /etc/commongrown/worker.env, Switch, /etc/commongrown/switch.json and register once before starting commongrown.service.'
