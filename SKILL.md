---
name: interactive-paper-explainers
description: Turn an academic paper PDF into a single self-contained interactive HTML explainer. Produces a two-mode page (braindead first, braingood second) with embedded interactive widgets, animated visualizations, and quiz checks. Trigger phrases — "do this paper", "explain this paper", "make an explainer for this paper", "interactive version of this paper", followed by a PDF path or arxiv link.
---

# Interactive Paper Explainers

Generates a single-file HTML explainer of an academic paper. Two modes, in this order. **Tab labels are always lowercase, no emoji, no "Mode" suffix:**

1. **braindead** — the entire paper's story in 5 minutes, no jargon, heavy use of analogies and emoji, ends in a TL;DR card.
2. **braingood** — the rigorous version: key concepts, study design, interactive visualizations of the data, results, limits, quiz.

An optional third tab, **brainstorm**, can be added for research-direction riffs that go beyond the paper itself.

The three canonical tab labels — **`braingood`**, **`braindead`**, **`brainstorm`** — are the ONLY allowed display strings for the tab bar across every paper in this repo.

The output is one `index.html` file that lives next to the paper PDF (e.g. `papers/paperN/index.html`). Self-contained — no build step, no dependencies, just open it in a browser.

> **Forked from / inspired by** Paras Chopra's [`make-pages-interactive`](https://github.com/paraschopra/make-pages-interactive) — that skill turns any folder of HTML into a commenting surface. This skill produces the HTML to *feed* it. The two compose: build an explainer with this skill, then run `make-pages-interactive` on the folder to leave inline comments and iterate.

---

## When to invoke

User points at a paper (PDF on disk, arxiv link, or a paper-shaped DOI) and says:
- "do this paper"
- "make an explainer for this paper"
- "explain this paper interactively"
- "interactive version of <paper>"
- "let's do this paper now"

---

## The workflow — **always ask approval before each mode**

This is the rule: **never build a mode without first confirming with the user that they want it built right now.** The modes are independent and the user may want to ship one before starting the next, or skip one entirely.

### Step 1 — Read the paper end to end

Use the Read tool with `pages: "1-N"` ranges to walk through the whole PDF. Don't skim. Capture:
- The headline finding (one sentence)
- The method (one paragraph)
- Key numbers (sample size, effect sizes, p-values, CIs)
- Figures and tables — what each one shows
- Limits the authors acknowledge

Take internal notes; do not produce the HTML yet.

### Step 2 — Ask the user which mode to start with

Default sequence is **braindead first, then braingood**. Confirm before starting:

> "I've read the paper. Default plan is braindead first (the 5-minute jargon-free story), then braingood (the rigorous version with interactive widgets). Do you want me to start with braindead, or change the plan?"

If they say "go" or "yes" — proceed to braindead.
If they want to skip / reorder / only do one — adapt.

### Step 3 — Build braindead

Produce just the braindead section of the HTML (with the shell of the page — `<html>`, `<head>`, hero, tab bar with both tabs visible but only braindead populated, footer). This way the file is openable and reviewable on its own.

The tab bar must render exactly:

```html
<button class="tab-btn active" onclick="switchTab('normal', this)">braingood</button>
<button class="tab-btn" onclick="switchTab('ez', this)">braindead</button>
<button class="tab-btn" onclick="switchTab('brainstorm', this)">brainstorm</button>
```

(Internal tab IDs `normal` / `ez` / `brainstorm` are kept for historical reasons — only the visible label text uses the new names.)

braindead structure:
- A pink/purple gradient hero (`linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%)`) with title and "The whole paper in 5 minutes 🧠💥" subtitle
- 3–5 sections of `<p class="ez-big">` with bold key terms
- One `.ez-emoji-block` per section listing 2–4 concrete takeaways with emoji bullets
- At least one `.ez-analogy` (yellow box) per major idea
- A single `.ez-tldr` card at the end with the paper's headline finding in plain English

Style rules for braindead:
- No abbreviations on first use (spell out "EEG" → "electrodes on the scalp")
- No statistics — replace "r = 0.24, 95% CI [0.08, 0.40]" with "real but small correlation"
- One idea per paragraph
- Conversational tone — "here's what they found", "the story stuck", "actually meh"
- End every block with a concrete takeaway, never an open question

When done, show the user the page (or tell them to refresh) and **ask before proceeding**:

> "braindead is in. Refresh the page to see it. Move on to braingood?"

### Step 4 — Build braingood

Only after explicit approval. braingood goes in the `#tab-normal` panel and uses the rest of the design vocabulary:

- **Hero update**: switch the hero gradient to a serious blue/navy palette
- **Section: The Question** — frame what the paper is asking and why it matters
- **Section: Key Concepts** — a `.cards` grid of 3–5 click-to-expand concept cards
- **Section: At least one interactive widget** specific to the paper's data. Examples:
  - Animated SVG wave for a frequency-domain paper
  - Clickable head/brain/body map for neuroscience papers
  - Animated PRISMA/CONSORT funnel for systematic reviews
  - Forest plot with toggleable subgroup views for meta-analyses
  - Slider-driven simulation for parameter-space papers
  - Step-through timeline for longitudinal studies
- **Section: Method** — a PRISMA-style or pipeline visualization plus a `.stats` grid of headline numbers
- **Section: Results** — the headline finding with confidence intervals visualized, not just stated
- **Section: Implications** — `.cards` for "if you build X / if you run Y / if you read Z" framings
- **Section: Limits** — the authors' own caveats, one per row, in plain language
- **Section: Quiz** — 3 multiple-choice questions with click-to-reveal feedback. Each question should reward careful reading; the explanations should teach something the question alone doesn't.

**Reach for the dual-mode glossary table when the paper has a term-dense reference surface** — a taxonomy of mechanisms, a list of named entities, or a multi-row comparison where each row carries jargon a curious reader would otherwise have to Google. See the "Dual-mode reference tables" section below for the pattern. Do *not* apply this to narrative sections (Question / Method / Results / Implications) — braindead already serves the no-jargon audience there, and dual-versioning narrative prose just produces two worse copies of the same paragraph.

When done, **ask before proceeding** to any optional extras:

> "braingood is in. Page is complete. Anything else — a brainstorm tab, additional widgets, or are we done?"

### Step 5 — Wrap up: turn the page into a commenting surface

The commenting runtime ships with this skill (vendored from `make-pages-interactive` under MIT). When the explainer is in good shape, offer to wire it up:

> "Want me to enable inline commenting on this page? You'll be able to highlight text, leave notes, and I'll edit the HTML in response."

If yes, run the bundled tooling from the skill directory:

```bash
# 1. Inject the feedback <link>/<script> tags into every *.html in the paper folder
#    and create feedback/inbox.jsonl + feedback/history.json
python <skill-dir>/scripts/inject.py <papers-dir>/<paper-slug>/

# 2. Start the local feedback server (serves the folder + accepts comments)
python <skill-dir>/lib/server.py --root <papers-dir>/<paper-slug>/ --port 8765
```

Then open `http://localhost:8765/` in a browser. The server writes new comments to `<paper-slug>/feedback/inbox.jsonl` — tail it with the Monitor tool to react to user comments in real time and edit the HTML in response.

To take the page back to a clean state later: `python <skill-dir>/scripts/inject.py <papers-dir>/<paper-slug>/ --remove`.

---

## File output convention

- One paper → one HTML file
- Path: `<papers-dir>/<paper-slug>/index.html`
- Single file: all CSS inline in `<style>`, all JS inline in `<script>`, no external assets except the two `<link>`/`<script>` tags the `make-pages-interactive` skill injects (and those only after the user explicitly opts in to commenting)
- Mobile-responsive (test under 600px width)
- No emojis in the page unless they're functional UI. The tab labels (`braingood` / `braindead` / `brainstorm`) are emoji-free; emoji is fine inside `.ez-emoji-block` bullets and inline within braindead prose.

---

## Design language (CSS variables to define at the top of every page)

```css
:root {
  --blue: #2563eb;       --blue-light: #dbeafe;     --blue-dark: #1e40af;
  --gray: #6b7280;       --gray-light: #f3f4f6;     --gray-dark: #1f2937;
  --green: #059669;      --green-light: #d1fae5;
  --red: #dc2626;        --red-light: #fee2e2;
  --orange: #d97706;     --orange-light: #fef3c7;
  --purple: #7c3aed;     --purple-light: #ede9fe;
  --teal: #0d9488;       --teal-light: #ccfbf1;
  --pink: #db2777;       --pink-light: #fce7f3;
}
```

Body is Georgia serif for prose, sans-serif (system default) for chrome (tabs, buttons, captions, stats). Heavy use of subtle borders (`#e5e7eb`), light backgrounds (`#fafafa` body, `white` cards), and one-color accents per section.

---

## Component vocabulary (use these consistently)

| Component | Purpose |
|-----------|---------|
| `.hero` | Title + one-sentence subtitle + citation footer |
| `.tab-bar` (sticky) | Mode switcher — `braingood` / `braindead` / optional `brainstorm` (lowercase labels, no emoji) |
| `.callout` (blue/green/orange/purple) | A boxed quote-style aside |
| `.cards` + `.card` | Click-to-expand concept cards |
| `.stats` + `.stat-box` | Headline-number grid |
| `.quiz-box` | One multiple-choice question with feedback |
| `.ez-hero`, `.ez-big`, `.ez-emoji-block`, `.ez-analogy`, `.ez-tldr` | braindead primitives |
| `.bands-mode-toggle` + `.bands-table` + `.term[data-def]` + `.term-tip` | Dual-mode reference table with hover/tap glossary (see below) |

---

## Dual-mode reference tables (Plain ↔ Scientific + hover-glossary)

**When to use:** the paper has a term-dense reference surface — a taxonomy of mechanisms (e.g. EEG bands), a comparison of named entities (e.g. five competing algorithms), or any table where each row carries technical vocabulary that's load-bearing but unfamiliar. The pattern gives the reader a plain-language version they can absorb fast *and* a scientific version where every jargon term has a hover/tap tooltip — so they can learn the real terminology against scaffolding they already understand.

**When NOT to use:** narrative sections (Question / Method / Results / Implications) and any prose-heavy block. braindead already serves the no-jargon audience for narrative content. Forcing dual-versioning on prose just produces two worse copies of the same paragraph.

**Structure:**
1. A pill-style toggle (`.bands-mode-toggle`) above the table with two buttons: "Plain language" (default, active) and "Scientific (with jargon)"
2. Two parallel tables — same rows, same columns, same source attribution — one with all jargon translated, one with jargon preserved
3. In the scientific table, every technical term is wrapped in `<span class="term" title="one-line definition">term</span>`. JS upgrades `title` → `data-def` on load so the slow native browser tooltip never fires
4. A single floating `.term-tip` element fires on hover (desktop, instant) and tap (mobile, toggle)
5. A closing `.callout` ties the table back to the paper's central finding — *why* this taxonomy matters for what the paper is claiming

**Authoring rules:**
- Both tables must have the same number of rows in the same order, so flipping the toggle doesn't reflow the page
- The Plain column should use everyday metaphors that stay accurate ("go cells / stop cells" for pyramidal cells / interneurons; "memory hub" for hippocampus). Don't invent metaphors that mislead
- Every jargon term in the Scientific table needs a `title` — if you can't write a one-line definition, the term is either not load-bearing (drop it) or needs its own row (promote it)
- Source attribution lives in a final `.source-row` spanning all columns, with primary references for both columns

**Recipe (CSS):**

```css
.bands-mode-toggle {
  display: inline-flex; background: var(--gray-light);
  border: 1px solid #e5e7eb; border-radius: 999px;
  padding: 4px; margin: 16px 0 0; font-family: sans-serif;
}
.bands-mode-toggle button {
  border: none; background: transparent; padding: 8px 18px;
  font-size: 0.88rem; font-weight: 600; color: var(--gray);
  cursor: pointer; border-radius: 999px;
  transition: background 0.15s, color 0.15s;
}
.bands-mode-toggle button.active {
  background: white; color: var(--blue-dark);
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
.bands-table-wrap {
  margin: 12px 0 28px; overflow-x: auto;
  border: 1px solid #e5e7eb; border-radius: 12px; background: white;
}
.bands-table-wrap.hidden { display: none; }
.bands-table { width: 100%; border-collapse: collapse;
  font-family: sans-serif; font-size: 0.92rem; min-width: 720px; }
.bands-table thead th { background: var(--gray-light); color: var(--gray-dark);
  font-weight: 600; text-align: left; padding: 12px 14px;
  border-bottom: 2px solid #e5e7eb; font-size: 0.78rem;
  letter-spacing: 0.05em; text-transform: uppercase; }
.bands-table tbody td { padding: 14px; border-bottom: 1px solid #f3f4f6;
  vertical-align: top; line-height: 1.5; }
.bands-table .source-row td { background: #fafafa; font-size: 0.82rem;
  color: var(--gray); font-style: italic; }
.bands-table .term { font-weight: 600; color: var(--gray-dark);
  border-bottom: 1px dotted var(--gray); cursor: help; }
.bands-table .term:hover, .bands-table .term.active { background: var(--orange-light); }

.term-tip {
  position: absolute; background: #1f2937; color: white;
  padding: 10px 14px; border-radius: 8px; font-family: sans-serif;
  font-size: 0.88rem; line-height: 1.45; max-width: 320px;
  z-index: 9999; pointer-events: none; opacity: 0;
  transform: translateY(-4px);
  transition: opacity 0.12s ease, transform 0.12s ease;
  box-shadow: 0 6px 20px rgba(0,0,0,0.25);
}
.term-tip.visible { opacity: 1; transform: translateY(0); }
.term-tip::before {
  content: ''; position: absolute; top: -6px; left: 16px;
  width: 0; height: 0;
  border-left: 6px solid transparent; border-right: 6px solid transparent;
  border-bottom: 6px solid #1f2937;
}
```

**Recipe (JS):**

```js
function setBandsMode(mode, btn) {
  const plain = document.getElementById('bandsTablePlain');
  const science = document.getElementById('bandsTableScience');
  if (!plain || !science) return;
  (mode === 'science' ? plain : science).classList.add('hidden');
  (mode === 'science' ? science : plain).classList.remove('hidden');
  document.querySelectorAll('.bands-mode-toggle button').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
}

(function() {
  const tip = document.createElement('div');
  tip.className = 'term-tip';
  document.body.appendChild(tip);
  let activeTerm = null;

  document.querySelectorAll('.term[title]').forEach(t => {
    t.setAttribute('data-def', t.getAttribute('title'));
    t.removeAttribute('title');
  });

  function showTip(term) {
    const text = term.getAttribute('data-def');
    if (!text) return;
    tip.textContent = text;
    const r = term.getBoundingClientRect();
    tip.style.left = (r.left + window.scrollX) + 'px';
    tip.style.top = (r.bottom + window.scrollY + 10) + 'px';
    tip.classList.add('visible');
    requestAnimationFrame(() => {
      const tr = tip.getBoundingClientRect();
      if (tr.right > window.innerWidth - 12) {
        tip.style.left = (window.innerWidth - tr.width - 12 + window.scrollX) + 'px';
      }
    });
    if (activeTerm && activeTerm !== term) activeTerm.classList.remove('active');
    term.classList.add('active');
    activeTerm = term;
  }
  function hideTip() {
    tip.classList.remove('visible');
    if (activeTerm) activeTerm.classList.remove('active');
    activeTerm = null;
  }

  document.addEventListener('mouseover', e => {
    const term = e.target.closest('.term');
    if (term) showTip(term);
  });
  document.addEventListener('mouseout', e => {
    const term = e.target.closest('.term');
    if (!term) return;
    const next = e.relatedTarget && e.relatedTarget.closest && e.relatedTarget.closest('.term');
    if (next === term) return;
    hideTip();
  });
  document.addEventListener('click', e => {
    const term = e.target.closest('.term');
    if (term) {
      e.preventDefault();
      if (activeTerm === term) hideTip(); else showTip(term);
    } else if (activeTerm) {
      hideTip();
    }
  });
  window.addEventListener('scroll', () => { if (activeTerm) hideTip(); }, { passive: true });
})();
```

**Recipe (HTML skeleton):**

```html
<div class="bands-mode-toggle">
  <button class="active" onclick="setBandsMode('plain', this)">Plain language</button>
  <button onclick="setBandsMode('science', this)">Scientific (with jargon)</button>
</div>
<div class="bands-table-wrap" id="bandsTablePlain">
  <table class="bands-table"> ... plain rows ... </table>
</div>
<div class="bands-table-wrap hidden" id="bandsTableScience">
  <table class="bands-table">
    <!-- Each jargon term: <span class="term" title="one-line definition">term</span> -->
    ... scientific rows ...
  </table>
</div>
```

The class names start with `bands-` for historical reasons (the pattern was first built for an EEG-band table). The names don't carry meaning — feel free to keep them as-is across papers for consistency, or rename per paper as long as the JS hook IDs (`bandsTablePlain` / `bandsTableScience`) match.

---

## Gotchas

- **Don't summarize before reading.** Always read the whole PDF before proposing the plan. Skipping pages produces explainers that miss the paper's actual contribution.
- **Don't build all modes in one shot.** The approval gate between modes is the point — the user often wants to course-correct after seeing braindead before you commit to a braingood structure.
- **Don't invent numbers.** Every statistic on the page should be quotable back to a specific page/figure/table in the source PDF. If you can't find it, leave it out.
- **Don't include the PDF in any downstream repo.** The HTML is the shippable artifact; the PDF stays alongside as a working file. (This applies if the user later asks you to publish — match what they ship.)
