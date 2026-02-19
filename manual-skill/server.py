"""MCP server exposing the HP Prime user guide PDF as searchable tools,
and scaffolding tools for creating new HP Prime Python apps."""

import os
import shutil
import sys
from pathlib import Path

import fitz  # pymupdf
from mcp.server.fastmcp import FastMCP

DOCS_DIR = Path(__file__).parent.parent / "docs"

# ---------------------------------------------------------------------------
# Load all PDFs from docs/ at startup
# ---------------------------------------------------------------------------

class PdfDoc:
    def __init__(self, path: Path):
        self.name = path.stem          # filename without extension
        self.path = path
        doc = fitz.open(str(path))
        self.page_texts: list[str] = [page.get_text() for page in doc]
        self.toc: list[tuple] = doc.get_toc()
        self.total_pages: int = len(self.page_texts)
        doc.close()

    def __repr__(self):
        return f"<PdfDoc {self.name!r} {self.total_pages}pp>"


if not DOCS_DIR.exists():
    print(f"ERROR: docs/ folder not found at {DOCS_DIR}", file=sys.stderr)
    sys.exit(1)

pdf_files = sorted(DOCS_DIR.glob("*.pdf"))
if not pdf_files:
    print(f"ERROR: no PDF files found in {DOCS_DIR}", file=sys.stderr)
    sys.exit(1)

DOCS: dict[str, PdfDoc] = {p.stem: PdfDoc(p) for p in pdf_files}
print(f"Loaded {len(DOCS)} PDF(s): {', '.join(DOCS)}", file=sys.stderr)

# Default doc (first alphabetically, or the user guide if present)
_default_key = "hpprime-ug-en" if "hpprime-ug-en" in DOCS else next(iter(DOCS))

# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "HP Prime Docs",
    instructions=(
        "Tools for reading HP Prime graphing calculator documentation PDFs. "
        "Use list_docs to see available documents. Use search_manual, get_section, "
        "get_page, and list_sections with an optional 'doc' argument to target a "
        "specific document (defaults to the user guide)."
    ),
)

MAX_RESULTS = 10
SNIPPET_CHARS = 400  # characters of context around each match


def _resolve_doc(doc: str | None) -> tuple[PdfDoc | None, str]:
    """Return (PdfDoc, error_message). error_message is '' on success."""
    key = doc or _default_key
    if key not in DOCS:
        available = ", ".join(DOCS)
        return None, f"Unknown document '{key}'. Available: {available}"
    return DOCS[key], ""


@mcp.tool()
def list_docs() -> str:
    """List all available PDF documents loaded by this server."""
    lines = []
    for name, d in DOCS.items():
        lines.append(f"  {name}  ({d.total_pages} pages)  — {d.path.name}")
    return "Available documents:\n" + "\n".join(lines)


@mcp.tool()
def search_manual(query: str, doc: str | None = None) -> str:
    """Search an HP Prime documentation PDF for pages containing the given keywords.

    Returns up to 10 matching pages with a short excerpt around each match.

    Returns up to 10 matching pages with a short excerpt around each match.

    Args:
        query: Keyword or phrase to search for.
        doc:   Document name to search (see list_docs). Defaults to the user guide.
    """
    d, err = _resolve_doc(doc)
    if err:
        return err

    query_lower = query.lower()
    results = []

    for page_num, text in enumerate(d.page_texts, start=1):
        idx = text.lower().find(query_lower)
        if idx == -1:
            continue
        start = max(0, idx - 100)
        end = min(len(text), idx + SNIPPET_CHARS)
        snippet = text[start:end].strip().replace("\n", " ")
        results.append(f"[Page {page_num}] ...{snippet}...")
        if len(results) >= MAX_RESULTS:
            break

    if not results:
        return f"No results found for '{query}' in '{d.name}'."

    header = f"Found {len(results)} result(s) for '{query}' in '{d.name}' (showing up to {MAX_RESULTS}):\n\n"
    return header + "\n\n".join(results)


@mcp.tool()
def get_section(section_name: str, doc: str | None = None) -> str:
    """Look up a chapter or section by name in a documentation PDF table of contents.

    Returns the full text of the matched section (from its start page to the
    next same-or-higher-level section). Pass a partial name to fuzzy-match.

    Args:
        section_name: Partial or full section/chapter title to look up.
        doc:          Document name (see list_docs). Defaults to the user guide.
    """
    d, err = _resolve_doc(doc)
    if err:
        return err

    if not d.toc:
        return f"Table of contents not available in '{d.name}'."

    name_lower = section_name.lower()
    match = None
    for entry in d.toc:
        if name_lower in entry[1].lower():
            match = entry
            break

    if match is None:
        available = "\n".join(f"  (level {e[0]}) {e[1]} — p.{e[2]}" for e in d.toc[:40])
        return (
            f"No section matching '{section_name}' found in '{d.name}'.\n\n"
            f"First 40 TOC entries:\n{available}"
        )

    match_level, match_title, start_page = match

    end_page = d.total_pages
    found = False
    for entry in d.toc:
        if found and entry[0] <= match_level:
            end_page = entry[2] - 1
            break
        if entry is match:
            found = True

    pages_to_read = min(end_page, start_page + 19)
    parts = []
    for p in range(start_page - 1, pages_to_read):
        if 0 <= p < d.total_pages:
            parts.append(f"--- Page {p + 1} ---\n{d.page_texts[p].strip()}")

    header = f"[{d.name}] Section: {match_title} (pages {start_page}–{pages_to_read})\n\n"
    return header + "\n\n".join(parts)


@mcp.tool()
def get_page(page_number: int, doc: str | None = None) -> str:
    """Retrieve the text content of a specific page from a documentation PDF.

    Page numbers are 1-based.

    Args:
        page_number: 1-based page number.
        doc:         Document name (see list_docs). Defaults to the user guide.
    """
    d, err = _resolve_doc(doc)
    if err:
        return err

    if page_number < 1 or page_number > d.total_pages:
        return f"Invalid page number {page_number}. '{d.name}' has {d.total_pages} pages."
    text = d.page_texts[page_number - 1].strip()
    return f"[{d.name} — Page {page_number} of {d.total_pages}]\n\n{text}"


@mcp.tool()
def list_sections(doc: str | None = None) -> str:
    """List all chapters and sections from a documentation PDF table of contents.

    Args:
        doc: Document name (see list_docs). Defaults to the user guide.
    """
    d, err = _resolve_doc(doc)
    if err:
        return err

    if not d.toc:
        return f"Table of contents not available in '{d.name}'."
    lines = [f"Table of contents — {d.name}:"]
    for level, title, page in d.toc:
        indent = "  " * (level - 1)
        lines.append(f"{indent}{title} — p.{page}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# App scaffolding
# ---------------------------------------------------------------------------

TEMPLATE_DIR = Path(__file__).parent.parent / "MarkdownViewer.hpappdir"
TEMPLATE_HPAPP = TEMPLATE_DIR / "MarkdownViewer.hpapp"
TEMPLATE_HPAPPPRGM = TEMPLATE_DIR / "MarkdownViewer.hpappprgm"

HELLO_WORLD_MAIN = '''\
"""Hello World — HP Prime Python app."""
import hpprime as h

def main():
    # Clear screen (white background)
    h.fillrect(0, 0, 0, 320, 220, 0xFFFFFF, 0xFFFFFF)

    # Title bar
    h.fillrect(0, 0, 0, 320, 20, 0x000080, 0x000080)
    h.eval('TEXTOUT_P("{name}", G0, 5, 2, 2, RGB(255,255,255), 310, RGB(0,0,128))')

    # Body text
    h.eval('TEXTOUT_P("Hello, World!", G0, 10, 60, 4, RGB(0,0,0), 300, RGB(255,255,255))')
    h.eval('TEXTOUT_P("Press ESC to exit.", G0, 10, 90, 2, RGB(80,80,80), 300, RGB(255,255,255))')

    # Soft menu
    h.eval('DRAWMENU("","","","","","Exit")')

    # Event loop
    while True:
        h.eval('wait(0.1)')
        key = h.eval('GETKEY()')
        if key == 4:   # ESC
            break
        f1, _ = h.eval('mouse')
        if len(f1) > 0 and f1[0] >= 0:
            x, y = f1[0], f1[1]
            if y >= 220 and x // 53 == 5:   # F6 = Exit
                break
'''


@mcp.tool()
def create_hp_prime_app(app_name: str, output_dir: str = ".") -> str:
    """Scaffold a new HP Prime Python app with the required binary files and a Hello World main.py.

    Creates <output_dir>/<app_name>.hpappdir/ containing:
      - <app_name>.hpapp        (binary app metadata — copied from template)
      - <app_name>.hpappprgm   (compiled PPL wrapper — copied from template)
      - main.py                 (Hello World entry point)

    The app is ready to deploy to the calculator via the HP Connectivity Kit.

    Args:
        app_name:   Name for the new app (e.g. "MyApp"). Use CamelCase, no spaces.
        output_dir: Directory to create the app folder in. Defaults to current directory.
    """
    if not app_name or not app_name.replace("_", "").isalnum():
        return "Error: app_name must be alphanumeric (underscores allowed), no spaces."

    if not TEMPLATE_HPAPP.exists() or not TEMPLATE_HPAPPPRGM.exists():
        return f"Error: template binaries not found at {TEMPLATE_DIR}"

    out = Path(output_dir).resolve()
    app_dir = out / f"{app_name}.hpappdir"

    if app_dir.exists():
        return f"Error: {app_dir} already exists."

    app_dir.mkdir(parents=True)

    # Copy binary templates (app name is NOT embedded — filenames are all that matter)
    shutil.copy2(TEMPLATE_HPAPP, app_dir / f"{app_name}.hpapp")
    shutil.copy2(TEMPLATE_HPAPPPRGM, app_dir / f"{app_name}.hpappprgm")

    # Write Hello World main.py
    main_py = HELLO_WORLD_MAIN.replace('"{name}"', f'"{app_name}"')
    (app_dir / "main.py").write_text(main_py, encoding="utf-8")

    files = [f.name for f in sorted(app_dir.iterdir())]
    return (
        f"Created {app_dir}\n\n"
        f"Files:\n" + "\n".join(f"  {f}" for f in files) + "\n\n"
        f"Next steps:\n"
        f"  1. Edit {app_name}.hpappdir/main.py to build your app.\n"
        f"  2. Copy the .hpappdir folder to the calculator using HP Connectivity Kit.\n"
        f"  3. On the calculator: Apps → {app_name} → Start.\n"
        f"  4. You may need to press 'Clear' once after first launch."
    )


if __name__ == "__main__":
    mcp.run()
