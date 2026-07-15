import os
import tempfile
import unittest
from pathlib import Path

from rctl.config import load_config


class LoadConfigTests(unittest.TestCase):
    def test_reads_dotenv_from_repo_root(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text(
                "PUBLIC_URL=https://example.com\nAUTH_TOKEN=secret-token\nPROJECT_NAME=my-project\n",
                encoding="utf-8",
            )

            config = load_config(start_dir=tmpdir)

            self.assertEqual(config["SERVER_URL"], "https://example.com")
            self.assertEqual(config["AUTH_TOKEN"], "secret-token")
            self.assertEqual(config["PROJECT_NAME"], "my-project")

    def test_environment_variables_override_dotenv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text(
                "PUBLIC_URL=https://from-dotenv.com\nAUTH_TOKEN=dotenv-token\nPROJECT_NAME=dotenv-project\n",
                encoding="utf-8",
            )

            os.environ["PUBLIC_URL"] = "https://from-env.com"
            os.environ["AUTH_TOKEN"] = "env-token"
            os.environ["PROJECT_NAME"] = "env-project"
            try:
                config = load_config(start_dir=tmpdir)
            finally:
                os.environ.pop("PUBLIC_URL", None)
                os.environ.pop("AUTH_TOKEN", None)
                os.environ.pop("PROJECT_NAME", None)

            self.assertEqual(config["SERVER_URL"], "https://from-env.com")
            self.assertEqual(config["AUTH_TOKEN"], "env-token")
            self.assertEqual(config["PROJECT_NAME"], "env-project")


if __name__ == "__main__":
    unittest.main()
