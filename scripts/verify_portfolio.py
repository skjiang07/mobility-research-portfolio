"""Check source syntax, notebook output removal, local links and publication boundaries."""
import ast
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = [
    re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})"),
    re.compile(r"sk-(?:proj-)?[A-Za-z0-9_-]{30,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"/(?:Users|home)/[A-Za-z0-9_.-]+/"),
]


def verify():
    files = [p for p in ROOT.rglob("*") if p.is_file()
             and not any(x in p.relative_to(ROOT).parts for x in [".git", ".venv", "__pycache__"])]
    sources = notebooks = 0
    for file in files:
        relative = file.relative_to(ROOT)
        if file.suffix.lower() in {".csv", ".parquet", ".xlsx", ".pdf", ".pkl"}:
            raise AssertionError(f"Unexpected data or publication artifact: {relative}")
        text = file.read_text(encoding="utf-8")
        for pattern in PATTERNS:
            if pattern.search(text):
                raise AssertionError(f"Potential credential or private path: {relative}")
        if file.suffix == ".py":
            ast.parse(text, filename=str(relative))
            sources += 1
        if file.suffix == ".ipynb":
            notebook = json.loads(text)
            for index, cell in enumerate(notebook["cells"]):
                if cell["cell_type"] == "code":
                    assert not cell.get("outputs"), f"Saved notebook output: {relative} cell {index}"
                    assert cell.get("execution_count") is None, f"Execution state: {relative} cell {index}"
                    ast.parse("".join(cell["source"]), filename=f"{relative}:cell{index}")
            notebooks += 1
        if file.suffix == ".md":
            for target in re.findall(r"\[[^\]]*\]\(([^\s)]+)\)", text):
                if ":" not in target and not target.startswith("#"):
                    assert (file.parent / target.split("#")[0]).exists(), f"Broken local link: {relative}"
    print(f"Validated {sources} Python sources, {notebooks} clean notebooks and local Markdown links.")


if __name__ == "__main__":
    verify()
