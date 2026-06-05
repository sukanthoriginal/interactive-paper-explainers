# interactive-paper-explainers

A Claude Code skill that turns an academic paper PDF into a single self-contained interactive HTML explainer.

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
6. Wire **comment/feedback** by injecting the bundled feedback runtime, starting the local feedback server, and creating a 30-second Codex heartbeat checker for the active review session.
7. Stop again, ask if anything else.

The output is a single `index.html` next to the PDF. The explainer content opens standalone in a browser; the default `comment/feedback` flow uses the bundled local server so comments can be saved to disk, plus a Codex-native heartbeat checker so submitted comments can be applied back into the page during review. The checker should be removed when the review session is done or repeatedly idle.

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
