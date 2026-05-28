---
name: interactive-paper-explainers
description: Turn an academic paper PDF into a single self-contained interactive HTML explainer. Produces a two-mode page (Brain Dead Mode first, Normal Mode second) with embedded interactive widgets, animated visualizations, and quiz checks. Trigger phrases — "do this paper", "explain this paper", "make an explainer for this paper", "interactive version of this paper", followed by a PDF path or arxiv link.
---

# Interactive Paper Explainers

Generates a single-file HTML explainer of an academic paper. Two modes, in this order:

1. **Brain Dead Mode 🧠💥** — the entire paper's story in 5 minutes, no jargon, heavy use of analogies and emoji, ends in a TL;DR card.
2. **Normal Mode** — the rigorous version: key concepts, study design, interactive visualizations of the data, results, limits, quiz.

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

Default sequence is **Brain Dead Mode first, then Normal Mode**. Confirm before starting:

> "I've read the paper. Default plan is Brain Dead Mode first (the 5-minute jargon-free story), then Normal Mode (the rigorous version with interactive widgets). Do you want me to start with Brain Dead Mode, or change the plan?"

If they say "go" or "yes" — proceed to Brain Dead Mode.
If they want to skip / reorder / only do one — adapt.

### Step 3 — Build Brain Dead Mode

Produce just the Brain Dead Mode section of the HTML (with the shell of the page — `<html>`, `<head>`, hero, tab bar with both tabs visible but only Brain Dead populated, footer). This way the file is openable and reviewable on its own.

Brain Dead Mode structure:
- A pink/purple gradient hero (`linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%)`) with title and "The whole paper in 5 minutes 🧠💥" subtitle
- 3–5 sections of `<p class="ez-big">` with bold key terms
- One `.ez-emoji-block` per section listing 2–4 concrete takeaways with emoji bullets
- At least one `.ez-analogy` (yellow box) per major idea
- A single `.ez-tldr` card at the end with the paper's headline finding in plain English

Style rules for Brain Dead Mode:
- No abbreviations on first use (spell out "EEG" → "electrodes on the scalp")
- No statistics — replace "r = 0.24, 95% CI [0.08, 0.40]" with "real but small correlation"
- One idea per paragraph
- Conversational tone — "here's what they found", "the story stuck", "actually meh"
- End every block with a concrete takeaway, never an open question

When done, show the user the page (or tell them to refresh) and **ask before proceeding**:

> "Brain Dead Mode is in. Refresh the page to see it. Move on to Normal Mode?"

### Step 4 — Build Normal Mode

Only after explicit approval. Normal Mode goes in the `#tab-normal` panel and uses the rest of the design vocabulary:

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

When done, **ask before proceeding** to any optional extras:

> "Normal Mode is in. Page is complete. Anything else — a brainstorm tab, additional widgets, or are we done?"

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
- No emojis in the page unless they're functional UI (e.g. the 🧠💥 in the Brain Dead Mode tab label, or emoji bullets inside `.ez-emoji-block`)

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
| `.tab-bar` (sticky) | Mode switcher — Brain Dead 🧠💥 / Normal / optional Brainstorm |
| `.callout` (blue/green/orange/purple) | A boxed quote-style aside |
| `.cards` + `.card` | Click-to-expand concept cards |
| `.stats` + `.stat-box` | Headline-number grid |
| `.quiz-box` | One multiple-choice question with feedback |
| `.ez-hero`, `.ez-big`, `.ez-emoji-block`, `.ez-analogy`, `.ez-tldr` | Brain Dead Mode primitives |

---

## Gotchas

- **Don't summarize before reading.** Always read the whole PDF before proposing the plan. Skipping pages produces explainers that miss the paper's actual contribution.
- **Don't build all modes in one shot.** The approval gate between modes is the point — the user often wants to course-correct after seeing Brain Dead Mode before you commit to a Normal Mode structure.
- **Don't invent numbers.** Every statistic on the page should be quotable back to a specific page/figure/table in the source PDF. If you can't find it, leave it out.
- **Don't include the PDF in any downstream repo.** The HTML is the shippable artifact; the PDF stays alongside as a working file. (This applies if the user later asks you to publish — match what they ship.)
