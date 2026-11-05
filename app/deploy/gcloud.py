"""Explicit Google Cloud operations. Default action prints a plan without changing anything."""
import argparse
from pathlib import Path
import re
import shlex
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
NAME = "commongrown-demo"


def create_commands(project, zone):
    if not re.fullmatch(r"[a-z][a-z0-9-]{4,61}[a-z0-9]", project) or not re.fullmatch(r"[a-z]+-[a-z]+[0-9]-[a-z]", zone):
        raise ValueError("Provide a valid Google project ID and zone")
    region = zone.rsplit("-", 1)[0]
    commands = [
        ["services", "enable", "compute.googleapis.com", "iap.googleapis.com"],
        ["compute", "networks", "create", NAME, "--subnet-mode=custom"],
        ["compute", "networks", "subnets", "create", NAME, f"--network={NAME}", f"--region={region}", "--range=10.77.0.0/24"],
        ["compute", "firewall-rules", "create", f"{NAME}-iap", f"--network={NAME}", "--allow=tcp:22",
         "--source-ranges=35.235.240.0/20", f"--target-tags={NAME}"],
        ["compute", "instances", "create", NAME, f"--zone={zone}", "--machine-type=e2-small",
         "--image-family=debian-12", "--image-project=debian-cloud", "--boot-disk-size=20GB",
         "--boot-disk-type=pd-standard", "--no-boot-disk-auto-delete", f"--subnet={NAME}", f"--tags={NAME}",
         "--no-service-account", "--no-scopes", "--metadata=enable-oslogin=TRUE",
         "--no-restart-on-failure",
         "--labels=app=commongrown,purpose=on-demand-demo"],
    ]
    return [["gcloud", *command, f"--project={project}", "--quiet"] for command in commands]


def package(target):
    # Whitelist source files; never upload local credentials, runtime state or private notes.
    files = list(ROOT.glob("*.py")) + [ROOT / name for name in ("pyproject.toml", "uv.lock", "switch.example.json")]
    files += list((ROOT / "commongrown").glob("*.py"))
    files += list((ROOT / "seeds").glob("*.json"))
    files += [ROOT / "deploy" / "install.sh", ROOT / "deploy" / "commongrown.service"]
    with tarfile.open(target, "w:gz") as archive:
        for path in sorted(files):
            archive.add(path, arcname=str(path.relative_to(ROOT)), recursive=False)


def run(command):
    subprocess.run(command, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "create", "upload", "start", "stop", "status", "ssh", "tunnel"), default="plan", nargs="?")
    parser.add_argument("--project", required=True)
    parser.add_argument("--zone", default="us-central1-a")
    args = parser.parse_args()
    commands = create_commands(args.project, args.zone)
    common = [f"--project={args.project}", f"--zone={args.zone}", "--quiet"]
    if args.action == "plan":
        for command in commands:
            print(shlex.join(command))
        print("No resources changed. create provisions; upload installs source; start/stop control running cost.")
    elif args.action == "create":
        for command in commands:
            run(command)
    elif args.action == "upload":
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "commongrown-app.tar.gz"
            package(archive)
            run(["gcloud", "compute", "scp", str(archive), f"{NAME}:/tmp/commongrown-app.tar.gz", "--tunnel-through-iap", *common])
            remote = ("sudo install -d -m 755 /opt/commongrown && "
                      "sudo tar -xzf /tmp/commongrown-app.tar.gz -C /opt/commongrown && "
                      f"sudo bash /opt/commongrown/deploy/install.sh {shlex.quote(args.project)}")
            run(["gcloud", "compute", "ssh", NAME, "--tunnel-through-iap", f"--command={remote}", *common])
    elif args.action in ("start", "stop", "status"):
        operation = "describe" if args.action == "status" else args.action
        run(["gcloud", "compute", "instances", operation, NAME, *common])
    else:
        command = ["gcloud", "compute", "ssh", NAME, "--tunnel-through-iap", *common]
        if args.action == "tunnel":
            command += ["--", "-N", "-L", "8080:127.0.0.1:8000"]
        run(command)


if __name__ == "__main__":
    main()
