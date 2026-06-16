# interactive-paper-explainers

A Claude Code skill that turns an academic paper PDF into a single self-contained interactive HTML explainer.

Published explainers homepage: <https://sukanthoriginal.github.io/interactive-paper-explainers/>

Default tabs, in order:

1. **braindead** — the entire paper in 5 minutes, no jargon, heavy analogies.
2. **braingood** — the rigorous version with interactive widgets, click-to-expand concept cards, animated visualizations, and a quiz.
3. **comment/feedback** — the built-in review surface for highlighting text, selecting elements, and submitting feedback batches.

Every generated explainer should include all three tabs by default, open on `braindead`, and wire `comment/feedback` after `braingood` is built.

The skill always **asks for approval before starting each explanation mode** — so you can review `braindead`, course-correct, then green-light `braingood` separately. The `comment/feedback` tab is part of the default shell and is wired after the page is complete.

---

## Forked from

This skill is a derivative of Paras Chopra's [`make-pages-interactive`](https://github.com/paraschopra/make-pages-interactive). That skill turns any folder of HTML pages into a live commenting surface — you highlight text, leave a note, and Claude edits the page in response.

This repo bundles the original commenting runtime (`lib/` and `scripts/`) **vendored verbatim under MIT** from upstream, plus a new `SKILL.md` that adds the paper-explainer workflow on top. So a single install gives you both halves:

1. The new `SKILL.md` workflow generates the paper explainer HTML.
2. The vendored `lib/` and `scripts/` make that HTML commentable through the default `comment/feedback` tab and floating feedback panel.

The original repository is not modified — Paras's upstream is unchanged and remains the canonical source for the commenting layer.

Credit and link: <https://github.com/paraschopra/make-pages-interactive>

---

## Install

```bash
git clone https://github.com/sukanthoriginal/interactive-paper-explainers \
  ~/.claude/skills/interactive-paper-explainers
```

Claude Code auto-discovers any folder under `~/.claude/skills/` that contains a `SKILL.md`.

---

## Usage

Inside a Claude Code session, point at a paper:

> "Do this paper: /path/to/paper.pdf"

Claude will:

1. Read the PDF end to end.
2. Ask you to confirm the plan — `braindead` first, then `braingood`, with `comment/feedback` as the third tab.
3. Build **braindead** and stop. Show you the page.
4. Ask before continuing.
5. Build **braingood** with paper-specific interactive widgets.
6. Wire **comment/feedback** by injecting the bundled feedback runtime and starting the local feedback server with event-triggered Codex processing.
7. Optionally publish a static GitHub Pages copy and rebuild the homepage.
8. Stop again, ask if anything else.

The output is a single `index.html` next to the PDF. The explainer content opens standalone in a browser; the default `comment/feedback` flow uses the bundled local server so comments can be saved to disk, plus an event-triggered `codex exec` processor so submitted comments can be applied back into the page during review without idle polling.

---

## GitHub Pages publishing

Local feedback and public hosting are intentionally split:

- The **local review copy** keeps the feedback runtime and talks to `lib/server.py`.
- The **GitHub Pages copy** is static/read-only, keeps the `comment/feedback` tab as workflow context, and strips `/lib/feedback.css` plus `/lib/feedback.js`.
- The root homepage, `index.html`, is regenerated so visitors can browse every published paper.
- Every published paper page gets a persistent `all explainers` home link back to the homepage.

Publish a generated explainer into this repo:

```bash
python scripts/publish_pages.py /path/to/paper-folder --slug paper-slug
```

For example:

```bash
python scripts/publish_pages.py ../papers/2602.10552 --slug 2602.10552
```

Rebuild only the homepage:

```bash
python scripts/publish_pages.py --homepage-only
```

Then commit and push. With GitHub Pages enabled from `main` at `/`, public pages resolve as:

```text
https://sukanthoriginal.github.io/interactive-paper-explainers/
https://sukanthoriginal.github.io/interactive-paper-explainers/papers/<paper-slug>/
```

Do not publish the source PDF by default; publish only the static HTML unless you explicitly want the PDF in the repo.

---

## Visualization standard

The skill should not turn explicit visualization requests into plain tables with emoji. Process loops, model pipelines, experimental protocols, scoring functions, and data transformations should become actual figures: flow diagrams, state machines, timelines, architecture sketches, mini charts, or interactive steppers.

For accumulated review-session lessons, see [`LESSONS.md`](LESSONS.md). Future explainer work should treat it as the durable QA memory for local feedback flow, visual teaching boards, evidence image sizing, responsive verification, and publish behavior.

For visual first drafts, use the bundled helper:

```bash
python scripts/visualizer.py closed-loop spec.json > loop-fragment.html
python scripts/visualizer.py process-flow spec.json > flow-fragment.html
```

Use `closed-loop` for feedback systems, optimization loops, agent-environment loops, and adaptive experiments. Use `process-flow` for one-way methods. Then customize the generated HTML/CSS for the paper. The final explainer remains self-contained; online tools like Mermaid Live, diagrams.net, Observable, or Excalidraw can be used while drafting, but final visuals should be exported or rewritten as inline SVG/HTML/CSS rather than loaded from an external CDN.

Hard visual QA rules:

- Paper figures, crops, and dataset examples are evidence. They must be large enough to inspect and should use contained rendering unless a deliberate crop is explained.
- Do not ship tiny letterbox thumbnails, cropped-away objects, overflowing labels, or equal-height card rows that create giant blank columns.
- Verify the changed region in the actual local browser viewport before calling an interactive “done.”

---

## Why two explanation modes?

Academic papers carry two audiences inside one PDF:

- The **curious outsider** who wants to know what the paper says without learning the field. `braindead` is for them.
- The **engaged reader** who wants to evaluate the claim, see the data, and decide whether to act on it. `braingood` is for them.

Most explainers pick one audience and lose the other. A multi-tab page can hold both — and the approval gate between them is what keeps the writer (the human, not the agent) in the loop. The third default tab, `comment/feedback`, keeps the iteration loop visible.

---

## What the skill does NOT do

- Generate the explainer without reading the full paper first
- Build both explanation modes in one shot without asking
- Invent statistics — every number on the page comes from the source PDF
- Touch Paras's original repo or vendor any of its files

---

## License

MIT. See [LICENSE](LICENSE).
