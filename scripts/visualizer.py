#!/usr/bin/env python3
"""Generate starter HTML/CSS fragments for paper explainer visualizations.

The output is intentionally dependency-free so it can be pasted into the
single-file explainer HTML and customized by the agent.
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path


MINIS = {
    "image": """
      <div class="viz-mini viz-mini-image" aria-hidden="true">
        <span></span><span></span><span></span>
      </div>""",
    "wave": """
      <div class="viz-mini viz-mini-wave" aria-hidden="true">
        <svg viewBox="0 0 120 48" role="img">
          <path d="M4 24 C14 5, 25 43, 36 24 S58 5, 70 24 S92 43, 116 18"></path>
          <path d="M4 34 C20 26, 30 38, 44 30 S72 20, 84 30 S102 38, 116 28"></path>
        </svg>
      </div>""",
    "vector": """
      <div class="viz-mini viz-mini-vector" aria-hidden="true">
        <span style="height: 32%"></span><span style="height: 72%"></span><span style="height: 46%"></span><span style="height: 88%"></span><span style="height: 55%"></span>
      </div>""",
    "score": """
      <div class="viz-mini viz-mini-score" aria-hidden="true">
        <div class="viz-score-track"><span></span></div>
        <div class="viz-score-dots"><i></i><i></i></div>
      </div>""",
    "batch": """
      <div class="viz-mini viz-mini-batch" aria-hidden="true">
        <span></span><span></span><span></span><span></span>
      </div>""",
}


CSS = """
<style>
.viz-flow {
  margin: 24px 0 28px;
  padding: 22px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #fff;
}
.viz-flow h3 {
  margin: 0 0 6px;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 1.15rem;
}
.viz-flow-caption {
  margin: 0 0 18px;
  color: #4b5563;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 0.94rem;
}
.viz-flow-track {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 14px;
  align-items: stretch;
}
.viz-stage {
  position: relative;
  display: grid;
  gap: 10px;
  min-height: 220px;
  padding: 16px;
  border: 1px solid #dbeafe;
  border-radius: 10px;
  background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
}
.viz-stage:not(:last-child)::after {
  content: "->";
  position: absolute;
  right: -13px;
  top: 48%;
  color: #2563eb;
  font-weight: 800;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.viz-stage-label {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #1f2937;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-weight: 800;
}
.viz-stage-label span {
  display: inline-grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 999px;
  background: #2563eb;
  color: white;
  font-size: 0.78rem;
}
.viz-stage p {
  margin: 0;
  color: #374151;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 0.88rem;
  line-height: 1.45;
}
.viz-stage p strong { color: #111827; }
.viz-mini {
  min-height: 66px;
  border-radius: 8px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  overflow: hidden;
}
.viz-mini-image {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 3px;
  padding: 5px;
}
.viz-mini-image span:first-child {
  grid-row: span 2;
  background: linear-gradient(135deg, #f97316, #2563eb);
}
.viz-mini-image span:nth-child(2) { background: linear-gradient(135deg, #22c55e, #a855f7); }
.viz-mini-image span:nth-child(3) { background: linear-gradient(135deg, #facc15, #ef4444); }
.viz-mini-image span { border-radius: 5px; }
.viz-mini-wave svg { width: 100%; height: 66px; }
.viz-mini-wave path {
  fill: none;
  stroke: #2563eb;
  stroke-width: 4;
  stroke-linecap: round;
}
.viz-mini-wave path + path { stroke: #14b8a6; stroke-width: 3; opacity: 0.75; }
.viz-mini-vector {
  display: flex;
  align-items: end;
  gap: 6px;
  padding: 10px;
}
.viz-mini-vector span {
  flex: 1;
  border-radius: 5px 5px 0 0;
  background: linear-gradient(180deg, #7c3aed, #c4b5fd);
}
.viz-mini-score {
  display: grid;
  align-content: center;
  gap: 10px;
  padding: 14px;
}
.viz-score-track {
  height: 12px;
  border-radius: 999px;
  background: #dbeafe;
}
.viz-score-track span {
  display: block;
  width: 72%;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #f97316, #22c55e);
}
.viz-score-dots {
  position: relative;
  height: 24px;
}
.viz-score-dots::before {
  content: "";
  position: absolute;
  left: 12%;
  right: 12%;
  top: 11px;
  border-top: 2px dashed #93c5fd;
}
.viz-score-dots i {
  position: absolute;
  top: 5px;
  width: 14px;
  height: 14px;
  border-radius: 999px;
  background: #ef4444;
}
.viz-score-dots i:first-child { left: 22%; }
.viz-score-dots i:last-child { right: 16%; background: #22c55e; }
.viz-mini-batch {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 5px;
  padding: 7px;
}
.viz-mini-batch span {
  border-radius: 6px;
  background: linear-gradient(135deg, #e0f2fe, #2563eb);
}
.viz-mini-batch span:nth-child(2) { background: linear-gradient(135deg, #dcfce7, #16a34a); }
.viz-mini-batch span:nth-child(3) { background: linear-gradient(135deg, #fef3c7, #f59e0b); }
.viz-mini-batch span:nth-child(4) { background: linear-gradient(135deg, #fce7f3, #db2777); }
.viz-flow-note {
  margin: 16px 0 0;
  padding: 12px 14px;
  border-left: 4px solid #2563eb;
  background: #eff6ff;
  color: #1f2937;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 0.92rem;
  line-height: 1.5;
}
@media (max-width: 720px) {
  .viz-flow { padding: 16px; }
  .viz-flow-track { grid-template-columns: 1fr; }
  .viz-stage:not(:last-child)::after {
    content: "down";
    right: 18px;
    top: auto;
    bottom: -12px;
    background: white;
    padding: 0 6px;
  }
}
</style>
"""


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def load_spec(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise SystemExit("spec must be a JSON object")
    steps = data.get("steps")
    if not isinstance(steps, list) or not steps:
        raise SystemExit("spec.steps must be a non-empty array")
    return data


def render_process_flow(spec: dict) -> str:
    title = esc(spec.get("title", "Process flow"))
    caption = esc(spec.get("caption", "Follow how the signal changes from step to step."))
    closing = spec.get("closing")

    parts = [CSS, '<figure class="viz-flow">', f"  <h3>{title}</h3>", f'  <p class="viz-flow-caption">{caption}</p>', '  <div class="viz-flow-track">']
    for index, step in enumerate(spec["steps"], 1):
        mini_key = str(step.get("mini", "vector"))
        mini = MINIS.get(mini_key, MINIS["vector"])
        label = esc(step.get("label", f"Step {index}"))
        data = esc(step.get("data", "data representation"))
        meaning = esc(step.get("meaning", "what this step does"))
        parts.extend(
            [
                '    <article class="viz-stage">',
                f'      <div class="viz-stage-label"><span>{index}</span>{label}</div>',
                mini.rstrip(),
                f"      <p><strong>Data:</strong> {data}</p>",
                f"      <p><strong>Meaning:</strong> {meaning}</p>",
                "    </article>",
            ]
        )
    parts.append("  </div>")
    if closing:
        parts.append(f'  <p class="viz-flow-note">{esc(closing)}</p>')
    parts.append("</figure>")
    return "\n".join(parts) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate explainer visualization fragments.")
    sub = parser.add_subparsers(dest="command", required=True)
    flow = sub.add_parser("process-flow", help="generate a process/loop flow figure")
    flow.add_argument("spec", help="JSON spec file")
    args = parser.parse_args()

    if args.command == "process-flow":
        sys.stdout.write(render_process_flow(load_spec(args.spec)))
        return 0
    raise SystemExit(f"unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
