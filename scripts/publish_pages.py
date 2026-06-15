#!/usr/bin/env python3
"""Publish an explainer HTML into this repo's GitHub Pages tree.

This script is intentionally dependency-free. It copies a finished local
explainer into papers/<slug>/index.html, strips the local feedback runtime from
that public copy, and rebuilds the repository homepage so multiple generated
papers are easy to browse.

Usage:
    python scripts/publish_pages.py /path/to/paper-dir --slug 2602.10552
    python scripts/publish_pages.py /path/to/index.html --slug my-paper
    python scripts/publish_pages.py --homepage-only
"""
from __future__ import annotations

import argparse
import html
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PAPERS_DIR = REPO_ROOT / "papers"
INDEX_PATH = REPO_ROOT / "index.html"
NOJEKYLL_PATH = REPO_ROOT / ".nojekyll"

CSS_REMOVE_RE = re.compile(
    r'[ \t]*<link[^>]*href=["\']/lib/feedback\.css["\'][^>]*>\s*\n?',
    re.IGNORECASE,
)
JS_REMOVE_RE = re.compile(
    r'[ \t]*<script[^>]*src=["\']/lib/feedback\.js["\'][^>]*></script>\s*\n?',
    re.IGNORECASE,
)
OPEN_FEEDBACK_BUTTON_RE = re.compile(
    r'<button([^>]*?)\s+onclick=["\']openFeedbackPanel\(\)["\']([^>]*)>.*?</button>',
    re.IGNORECASE | re.DOTALL,
)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
SUBTITLE_RE = re.compile(
    r'<p[^>]*class=["\'][^"\']*(?:hero-subtitle|subtitle)[^"\']*["\'][^>]*>(.*?)</p>',
    re.IGNORECASE | re.DOTALL,
)
ARXIV_RE = re.compile(r"arxiv[:\s-]*([0-9]{4}\.[0-9]{4,5})", re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")
SLUG_RE = re.compile(r"[^a-zA-Z0-9._-]+")


@dataclass
class PaperEntry:
    slug: str
    title: str
    subtitle: str
    href: str
    arxiv: str | None
    has_feedback_tab: bool
    has_braingood: bool


def strip_tags(value: str) -> str:
    value = TAG_RE.sub("", value)
    value = html.unescape(value)
    return " ".join(value.split())


def extract_match(regex: re.Pattern[str], text: str) -> str:
    match = regex.search(text)
    return strip_tags(match.group(1)) if match else ""


def normalize_slug(raw: str) -> str:
    slug = SLUG_RE.sub("-", raw.strip()).strip("-").lower()
    if not slug:
        raise ValueError("slug is empty after normalization")
    return slug


def resolve_source(source: str | None) -> Path | None:
    if source is None:
        return None
    path = Path(source).expanduser().resolve()
    if path.is_dir():
        path = path / "index.html"
    if not path.is_file():
        raise FileNotFoundError(f"could not find explainer HTML: {path}")
    return path


def publicize_html(text: str) -> str:
    """Make a local review page safe for static GitHub Pages hosting."""
    text = CSS_REMOVE_RE.sub("", text)
    text = JS_REMOVE_RE.sub("", text)
    text = OPEN_FEEDBACK_BUTTON_RE.sub(
        '<button\\1\\2 disabled>feedback panel is local-only</button>',
        text,
    )
    text = text.replace(
        "<h3>Open the panel</h3>\n            <p>Use the feedback launcher or the button below to open the floating review panel.</p>",
        "<h3>Open locally</h3>\n            <p>Run the local feedback server to load the floating review panel and collect comments.</p>",
    )
    text = text.replace(
        "<h3>Attach a note</h3>\n            <p>Highlight wording, select a section, or leave a general comment about the explainer.</p>",
        "<h3>Attach a note</h3>\n            <p>In the local version, highlight wording, select a section, or leave a general comment.</p>",
    )
    text = text.replace(
        "<h3>Submit batch</h3>\n            <p>The server appends your review to the local inbox for processing.</p>",
        "<h3>Publish changes</h3>\n            <p>After Codex applies feedback locally, push the updated static HTML to refresh this hosted page.</p>",
    )
    text = text.replace(
        "If the feedback launcher is not visible yet, the page still has this tab ready. "
        "The runtime is enabled after `scripts/inject.py` wires `/lib/feedback.css` and `/lib/feedback.js`, "
        "then the local server serves this folder.",
        "GitHub Pages hosts the changed explainer as static HTML. It does not run the Python feedback server or accept feedback POST requests.",
    )
    text = text.replace(
        "This tab is the review surface for the explainer. Highlight text, select an element, or add a general note; "
        "submitted batches are saved locally so Codex can process the comments and update this page.",
        "This public GitHub Pages copy is read-only. The live feedback workflow runs in the local server version, "
        "where submitted batches are saved locally so Codex can process comments and update this page before the next publish.",
    )
    disabled_css = """
    .feedback-button:disabled {
      cursor: not-allowed;
      opacity: 0.62;
      box-shadow: none;
    }
"""
    if ".feedback-button:disabled" not in text:
        if "\n    code {\n" in text:
            text = text.replace("\n    code {\n", disabled_css + "\n    code {\n", 1)
        else:
            text = text.replace("</style>", disabled_css + "</style>", 1)
    if "GitHub Pages copy: local feedback runtime stripped" not in text:
        text = text.replace(
            "</head>",
            "  <!-- GitHub Pages copy: local feedback runtime stripped by scripts/publish_pages.py. -->\n</head>",
            1,
        )
    return text


def publish_copy(source_html: Path, slug: str) -> Path:
    target_dir = PAPERS_DIR / normalize_slug(slug)
    target_dir.mkdir(parents=True, exist_ok=True)
    text = source_html.read_text(encoding="utf-8")
    public_text = publicize_html(text)
    target = target_dir / "index.html"
    target.write_text(public_text, encoding="utf-8")
    return target


def discover_papers() -> list[PaperEntry]:
    entries: list[PaperEntry] = []
    if not PAPERS_DIR.exists():
        return entries
    for index in sorted(PAPERS_DIR.glob("*/index.html")):
        slug = index.parent.name
        text = index.read_text(encoding="utf-8", errors="replace")
        title = extract_match(H1_RE, text) or extract_match(TITLE_RE, text) or slug
        subtitle = extract_match(SUBTITLE_RE, text)
        if not subtitle:
            subtitle = "Interactive paper explainer"
        arxiv_match = ARXIV_RE.search(text) or ARXIV_RE.search(slug)
        entries.append(
            PaperEntry(
                slug=slug,
                title=title,
                subtitle=subtitle,
                href=f"papers/{slug}/",
                arxiv=arxiv_match.group(1) if arxiv_match else None,
                has_feedback_tab="comment/feedback" in text,
                has_braingood="braingood" in text,
            )
        )
    return entries


def card_visual(slug: str, i: int) -> str:
    themes = [
        ("#2563eb", "#0d9488", "#f97316"),
        ("#db2777", "#7c3aed", "#2563eb"),
        ("#059669", "#1e40af", "#d97706"),
        ("#1f2937", "#2563eb", "#0d9488"),
    ]
    a, b, c = themes[i % len(themes)]
    return f"""
          <div class="paper-visual" style="--a:{a}; --b:{b}; --c:{c};" aria-hidden="true">
            <span class="node n1"></span>
            <span class="node n2"></span>
            <span class="node n3"></span>
            <span class="line l1"></span>
            <span class="line l2"></span>
            <span class="bars"><i></i><i></i><i></i><i></i></span>
          </div>"""


def render_homepage(entries: list[PaperEntry]) -> str:
    cards = []
    for i, entry in enumerate(entries):
        badges = []
        if entry.arxiv:
            badges.append(f"arXiv:{html.escape(entry.arxiv)}")
        if entry.has_braingood:
            badges.append("braingood")
        if entry.has_feedback_tab:
            badges.append("comment/feedback")
        badge_html = "".join(f"<span>{html.escape(badge)}</span>" for badge in badges)
        cards.append(
            f"""
        <article class="paper-card">
          <a class="paper-link" href="{html.escape(entry.href)}" aria-label="Open {html.escape(entry.title)}"></a>
{card_visual(entry.slug, i)}
          <div class="paper-copy">
            <div class="paper-slug">{html.escape(entry.slug)}</div>
            <h2>{html.escape(entry.title)}</h2>
            <p>{html.escape(entry.subtitle)}</p>
            <div class="badges">{badge_html}</div>
          </div>
        </article>"""
        )

    empty_state = """
        <div class="empty-state">
          <h2>No explainers yet</h2>
          <p>Run <code>python scripts/publish_pages.py /path/to/paper-folder --slug paper-slug</code> after generating one.</p>
        </div>"""
    card_html = "\n".join(cards) if cards else empty_state
    count = len(entries)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Interactive Paper Explainers</title>
  <style>
    :root {{
      --blue: #2563eb;
      --blue-dark: #1e40af;
      --teal: #0d9488;
      --pink: #db2777;
      --gray: #6b7280;
      --gray-dark: #1f2937;
      --line: #e5e7eb;
      --paper: #ffffff;
      --body: #fafafa;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--body);
      color: var(--gray-dark);
      font-family: Georgia, "Times New Roman", serif;
      line-height: 1.62;
      letter-spacing: 0;
    }}
    a {{ color: inherit; }}
    .shell {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 36px 24px 72px;
    }}
    header {{
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 24px;
      align-items: end;
      padding: 26px 0 28px;
      border-bottom: 1px solid var(--line);
    }}
    .eyebrow {{
      margin: 0 0 10px;
      color: var(--blue);
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 0.78rem;
      font-weight: 850;
      text-transform: uppercase;
    }}
    h1 {{
      margin: 0;
      max-width: 760px;
      color: #111827;
      font-size: 2.35rem;
      line-height: 1.12;
      font-weight: 540;
    }}
    .subhead {{
      margin: 14px 0 0;
      max-width: 760px;
      color: #4b5563;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 1rem;
      line-height: 1.55;
    }}
    .count-box {{
      min-width: 150px;
      padding: 16px 18px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: white;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      text-align: right;
    }}
    .count-box strong {{
      display: block;
      color: #111827;
      font-size: 2rem;
      line-height: 1;
    }}
    .count-box span {{
      color: var(--gray);
      font-size: 0.82rem;
      font-weight: 700;
    }}
    .notice {{
      margin: 22px 0 26px;
      padding: 14px 16px;
      border: 1px solid #fed7aa;
      border-left: 5px solid #d97706;
      border-radius: 0 8px 8px 0;
      background: #fff7ed;
      color: #7c2d12;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 0.92rem;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 18px;
    }}
    .paper-card {{
      position: relative;
      display: grid;
      grid-template-columns: 142px 1fr;
      min-height: 212px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--paper);
      overflow: hidden;
      transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
    }}
    .paper-card:hover {{
      transform: translateY(-2px);
      border-color: var(--blue);
      box-shadow: 0 14px 28px rgba(15, 23, 42, 0.08);
    }}
    .paper-link {{
      position: absolute;
      inset: 0;
      z-index: 3;
    }}
    .paper-visual {{
      position: relative;
      min-height: 212px;
      background:
        radial-gradient(circle at 54% 48%, rgba(255,255,255,0.95) 0 19%, transparent 20%),
        linear-gradient(135deg, var(--a), var(--b));
    }}
    .paper-visual .node {{
      position: absolute;
      width: 42px;
      height: 32px;
      border-radius: 7px;
      background: rgba(255,255,255,0.94);
      box-shadow: 0 8px 18px rgba(15, 23, 42, 0.16);
    }}
    .paper-visual .n1 {{ left: 18px; top: 24px; }}
    .paper-visual .n2 {{ right: 18px; top: 72px; }}
    .paper-visual .n3 {{ left: 26px; bottom: 28px; }}
    .paper-visual .line {{
      position: absolute;
      height: 2px;
      border-top: 2px dashed rgba(255,255,255,0.72);
      transform-origin: left center;
    }}
    .paper-visual .l1 {{ left: 56px; top: 48px; width: 70px; transform: rotate(26deg); }}
    .paper-visual .l2 {{ left: 48px; bottom: 62px; width: 82px; transform: rotate(-30deg); }}
    .paper-visual .bars {{
      position: absolute;
      left: 50%;
      top: 50%;
      transform: translate(-50%, -50%);
      display: flex;
      align-items: end;
      gap: 4px;
      height: 52px;
    }}
    .paper-visual .bars i {{
      width: 8px;
      border-radius: 4px 4px 1px 1px;
      background: var(--c);
    }}
    .paper-visual .bars i:nth-child(1) {{ height: 34%; }}
    .paper-visual .bars i:nth-child(2) {{ height: 78%; }}
    .paper-visual .bars i:nth-child(3) {{ height: 56%; }}
    .paper-visual .bars i:nth-child(4) {{ height: 92%; }}
    .paper-copy {{
      padding: 18px;
      display: grid;
      align-content: start;
      gap: 8px;
    }}
    .paper-slug {{
      color: var(--blue);
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 0.78rem;
      font-weight: 850;
    }}
    .paper-card h2 {{
      margin: 0;
      color: #111827;
      font-size: 1.14rem;
      line-height: 1.25;
      font-weight: 760;
    }}
    .paper-card p {{
      margin: 0;
      color: #4b5563;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 0.9rem;
      line-height: 1.48;
    }}
    .badges {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 8px;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    .badges span {{
      border-radius: 999px;
      background: #f1f5f9;
      color: #334155;
      padding: 4px 8px;
      font-size: 0.72rem;
      font-weight: 800;
    }}
    code {{
      padding: 2px 5px;
      border-radius: 5px;
      background: #f1f5f9;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 0.9em;
    }}
    .empty-state {{
      padding: 26px;
      border: 1px dashed #cbd5e1;
      border-radius: 8px;
      background: white;
    }}
    @media (max-width: 720px) {{
      .shell {{ padding: 24px 16px 54px; }}
      header {{ grid-template-columns: 1fr; }}
      h1 {{ font-size: 1.85rem; }}
      .count-box {{ text-align: left; }}
      .paper-card {{ grid-template-columns: 1fr; }}
      .paper-visual {{ min-height: 152px; }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <header>
      <div>
        <p class="eyebrow">Interactive Paper Explainers</p>
        <h1>Generated explainers</h1>
        <p class="subhead">A browsable shelf of paper explainers generated by the skill. Each page is static on GitHub Pages; local feedback stays in the local review server.</p>
      </div>
      <div class="count-box">
        <strong>{count}</strong>
        <span>{'explainer' if count == 1 else 'explainers'}</span>
      </div>
    </header>

    <div class="notice">
      Public pages are read-only mirrors. Run the local feedback server while reviewing, then republish the accepted HTML with <code>scripts/publish_pages.py</code>.
    </div>

    <section class="grid" aria-label="Generated paper explainers">
{card_html}
    </section>
  </main>
</body>
</html>
"""


def rebuild_homepage() -> int:
    PAPERS_DIR.mkdir(exist_ok=True)
    entries = discover_papers()
    INDEX_PATH.write_text(render_homepage(entries), encoding="utf-8")
    NOJEKYLL_PATH.touch()
    print(f"Homepage rebuilt with {len(entries)} explainer(s): {INDEX_PATH}")
    return len(entries)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", nargs="?", help="explainer directory or index.html to publish")
    ap.add_argument("--slug", help="destination slug under papers/")
    ap.add_argument("--homepage-only", action="store_true", help="only rebuild the repo homepage")
    ap.add_argument("--no-homepage", action="store_true", help="publish copy without rebuilding homepage")
    args = ap.parse_args()

    if args.homepage_only:
        rebuild_homepage()
        return 0

    source_html = resolve_source(args.source)
    if source_html is None:
        ap.error("source is required unless --homepage-only is set")

    slug = args.slug or source_html.parent.name
    target = publish_copy(source_html, slug)
    print(f"Published static copy: {target}")

    if not args.no_homepage:
        rebuild_homepage()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
