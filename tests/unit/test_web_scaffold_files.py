import unittest
from pathlib import Path


class TestWebScaffoldFiles(unittest.TestCase):
    def test_web_scaffold_key_files_exist(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        web_root = project_root / "futures_monitor" / "web"

        expected_files = [
            web_root / "package.json",
            web_root / "src" / "main.ts",
            web_root / "src" / "App.vue",
        ]

        for file_path in expected_files:
            self.assertTrue(file_path.exists(), f"Missing web scaffold file: {file_path}")


if __name__ == "__main__":
    unittest.main()
