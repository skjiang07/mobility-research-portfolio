"""Check source syntax, notebook output removal, local links and publication boundaries."""
import ast
import hashlib
import json
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = [
    re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})"),
    re.compile(r"sk-(?:proj-)?[A-Za-z0-9_-]{30,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"/(?:Users|home)/[A-Za-z0-9_.-]+/"),
]


def verify():
    inventory_file = ROOT / "docs/research_assets.json"
    assets = {}
    if inventory_file.exists():
        for item in json.loads(inventory_file.read_text(encoding="utf-8"))["assets"]:
            path = item["path"]
            assert path not in assets, f"Duplicate research asset: {path}"
            assert not Path(path).is_absolute() and ".." not in Path(path).parts, path
            file = ROOT / path
            assert file.is_file(), f"Missing research asset: {path}"
            content = file.read_bytes()
            assert hashlib.sha256(content).hexdigest() == item["sha256"], f"Changed research asset: {path}"
            if item["kind"] == "research_figure":
                assert file.suffix.lower() == ".png" and content[:8] == b"\x89PNG\r\n\x1a\n", path
                assert content[12:16] == b"IHDR" and all(struct.unpack(">II", content[16:24])), path
            elif item["kind"] == "author_manuscript":
                assert file.suffix.lower() == ".pdf" and content.startswith(b"%PDF-"), path
            else:
                raise AssertionError(f"Unknown research asset kind: {path}")
            assets[path] = item
    files = [p for p in ROOT.rglob("*") if p.is_file()
             and not any(x in p.relative_to(ROOT).parts for x in [".git", ".venv", "__pycache__"])]
    sources = notebooks = 0
    for file in files:
        relative = file.relative_to(ROOT)
        if relative.as_posix() in assets:
            continue
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
            targets = re.findall(r"\[[^\]]*\]\(([^\s)]+)\)", text)
            targets += re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', text)
            for target in targets:
                if ":" not in target and not target.startswith("#"):
                    assert (file.parent / target.split("#")[0]).exists(), f"Broken local link: {relative}"
    print(f"Validated {sources} Python sources, {notebooks} clean notebooks, "
          f"{len(assets)} registered research assets and local Markdown links.")


if __name__ == "__main__":
    verify()
