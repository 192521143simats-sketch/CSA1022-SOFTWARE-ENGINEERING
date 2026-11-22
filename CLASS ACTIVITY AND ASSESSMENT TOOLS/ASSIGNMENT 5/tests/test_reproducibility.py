import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TestReproducibility(unittest.TestCase):
    def test_results_json_is_reproduced_exactly(self):
        with tempfile.TemporaryDirectory() as tmp:
            dst = Path(tmp) / "repo"
            shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns(".git", "figures", "screenshots", "__pycache__"))
            subprocess.run([sys.executable, "run_demonstrator.py"], cwd=dst, check=True,
                           capture_output=True)
            self.assertEqual((dst / "results" / "results.json").read_bytes(),
                             (ROOT / "results" / "results.json").read_bytes())
