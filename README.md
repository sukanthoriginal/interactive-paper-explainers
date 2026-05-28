# interactive-paper-explainers

A Claude Code skill that turns an academic paper PDF into a single self-contained interactive HTML explainer.

Two modes, in order:

1. **Brain Dead Mode 🧠💥** — the entire paper in 5 minutes, no jargon, heavy analogies.
2. **Normal Mode** — the rigorous version with interactive widgets, click-to-expand concept cards, animated visualizations, and a quiz.

The skill always **asks for approval before starting each mode** — so you can review Brain Dead Mode, course-correct, then green-light Normal Mode separately.

---

## Forked from

This skill is a derivative of Paras Chopra's [`make-pages-interactive`](https://github.com/paraschopra/make-pages-interactive). That skill turns any folder of HTML pages into a live commenting surface — you highlight text, leave a note, and Claude edits the page in response.

The two skills compose: use **this** one to generate the paper explainer HTML, then use **Paras's** one to leave inline comments and iterate on the page. None of Paras's repo is modified or vendored here; this is just the explainer-generation half, in my own version.

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
2. Ask you to confirm the plan — Brain Dead Mode first, then Normal Mode.
3. Build **Brain Dead Mode** and stop. Show you the page.
4. Ask before continuing.
5. Build **Normal Mode** with paper-specific interactive widgets.
6. Stop again, ask if anything else.

The output is a single self-contained `index.html` next to the PDF — open it in a browser, no build step.

---

## Why two modes?

Academic papers carry two audiences inside one PDF:

- The **curious outsider** who wants to know what the paper says without learning the field. Brain Dead Mode is for them.
- The **engaged reader** who wants to evaluate the claim, see the data, and decide whether to act on it. Normal Mode is for them.

Most explainers pick one audience and lose the other. A two-tab page can hold both — and the approval gate between them is what keeps the writer (the human, not the agent) in the loop.

---

## What the skill does NOT do

- Generate the explainer without reading the full paper first
- Build both modes in one shot without asking
- Invent statistics — every number on the page comes from the source PDF
- Touch Paras's original repo or vendor any of its files

---

## License

MIT. See [LICENSE](LICENSE).
