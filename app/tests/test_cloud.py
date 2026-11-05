import importlib.util
from pathlib import Path
import tempfile
import tarfile
import unittest

path = Path(__file__).resolve().parents[1] / "deploy" / "gcloud.py"
spec = importlib.util.spec_from_file_location("cloud_deploy", path)
cloud = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cloud)


class CloudTests(unittest.TestCase):
    def test_plan_has_small_instance_auto_stop_and_no_public_app_port(self):
        commands = cloud.create_commands("demo-project", "us-central1-a")
        vm = next(c for c in commands if c[1:4] == ["compute", "instances", "create"])
        self.assertIn("--machine-type=e2-small", vm)
        self.assertIn("--boot-disk-type=pd-standard", vm)
        self.assertIn("--no-service-account", vm)
        self.assertIn("--no-scopes", vm)
        self.assertNotIn("aiplatform", str(commands))
        firewall = next(c for c in commands if "firewall-rules" in c)
        self.assertIn("--source-ranges=35.235.240.0/20", firewall)
        self.assertIn("--allow=tcp:22", firewall)
        self.assertTrue(all("--project=demo-project" in c for c in commands))

    def test_archive_has_only_reviewed_source_not_private_data(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "app.tar.gz"
            cloud.package(target)
            with tarfile.open(target) as archive:
                names = archive.getnames()
            self.assertIn("switch_worker.py", names)
            self.assertIn("commongrown/worker.py", names)
            self.assertFalse(any(".data" in n or "private.json" in n or ".venv" in n or n.endswith(".env") for n in names))

    def test_invalid_project_and_zone_are_rejected(self):
        for project, zone in (("x;shutdown", "us-central1-a"), ("demo-project", "../secret")):
            with self.assertRaises(ValueError):
                cloud.create_commands(project, zone)
