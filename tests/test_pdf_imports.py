import ast
import unittest
from pathlib import Path


class PyMuPdfImportTests(unittest.TestCase):
    def test_python_files_do_not_import_deprecated_fitz_namespace(self) -> None:
        project_root = Path(__file__).parents[1]
        deprecated_imports: list[str] = []

        for source_root in (project_root / "src", project_root / "tests"):
            for source_path in source_root.rglob("*.py"):
                tree = ast.parse(source_path.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import) and any(alias.name == "fitz" for alias in node.names):
                        deprecated_imports.append(f"{source_path.relative_to(project_root)}:{node.lineno}")
                    if isinstance(node, ast.ImportFrom) and node.module == "fitz":
                        deprecated_imports.append(f"{source_path.relative_to(project_root)}:{node.lineno}")

        self.assertEqual(deprecated_imports, [])


if __name__ == "__main__":
    unittest.main()
