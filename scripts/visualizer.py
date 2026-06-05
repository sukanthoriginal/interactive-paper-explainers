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


CLOSED_LOOP_CSS = """
<style>
.viz-loop {
  margin: 24px 0 30px;
  padding: 22px;
  border: 1px solid #dbeafe;
  border-radius: 12px;
  background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%);
}
.viz-loop-header {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: start;
  margin-bottom: 18px;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.viz-loop-header h3 {
  margin: 0 0 6px;
  color: #1e40af;
  font-size: 1.18rem;
  line-height: 1.2;
}
.viz-loop-header p {
  margin: 0;
  max-width: 660px;
  color: #4b5563;
  font-size: 0.92rem;
  line-height: 1.45;
}
.viz-loop-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}
.viz-loop-legend span {
  padding: 5px 9px;
  border: 1px solid #bfdbfe;
  border-radius: 999px;
  background: white;
  color: #1e40af;
  font-size: 0.74rem;
  font-weight: 800;
}
.viz-loop-orbit {
  position: relative;
  min-height: 760px;
  border-radius: 14px;
  background:
    radial-gradient(circle at 50% 46%, #ffffff 0 24%, rgba(219,234,254,0.62) 25% 27%, transparent 28%),
    linear-gradient(135deg, rgba(13,148,136,0.08), rgba(124,58,237,0.07));
  overflow: hidden;
}
.viz-loop-arrows {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
.viz-loop-arrows path {
  fill: none;
  stroke: rgba(37,99,235,0.42);
  stroke-width: 4;
  stroke-linecap: round;
  stroke-dasharray: 10 12;
}
.viz-loop-arrows marker path { fill: rgba(37,99,235,0.65); }
.viz-loop-core,
.viz-loop-node {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.viz-loop-core {
  position: absolute;
  left: 50%;
  top: 46%;
  width: min(300px, 36%);
  transform: translate(-50%, -50%);
  padding: 18px;
  border: 1px solid #c4b5fd;
  border-radius: 14px;
  background: white;
  box-shadow: 0 20px 50px rgba(31,41,55,0.12);
  text-align: center;
}
.viz-loop-core-label {
  margin-bottom: 8px;
  color: #7c3aed;
  font-size: 0.72rem;
  font-weight: 900;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
.viz-loop-vector {
  display: flex;
  align-items: end;
  justify-content: center;
  gap: 7px;
  height: 72px;
  margin: 12px 0;
}
.viz-loop-vector span {
  width: 18px;
  border-radius: 6px 6px 2px 2px;
  background: linear-gradient(180deg, #7c3aed, #c4b5fd);
}
.viz-loop-core p,
.viz-loop-node p {
  margin: 0;
  color: #4b5563;
  font-size: 0.82rem;
  line-height: 1.38;
}
.viz-loop-core strong {
  color: #111827;
  line-height: 1.35;
}
.viz-loop-node {
  position: absolute;
  width: 230px;
  min-height: 208px;
  padding: 14px;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  background: rgba(255,255,255,0.96);
  box-shadow: 0 14px 32px rgba(15,23,42,0.08);
}
.viz-loop-node h4 {
  margin: 0 0 8px;
  color: #1f2937;
  font-size: 0.98rem;
  line-height: 1.2;
}
.viz-loop-node-1 { left: 36px; top: 34px; }
.viz-loop-node-2 { right: 36px; top: 34px; }
.viz-loop-node-3 { right: 36px; bottom: 34px; }
.viz-loop-node-4 { left: 50%; bottom: 30px; transform: translateX(-50%); }
.viz-loop-node-5 { left: 36px; bottom: 34px; }
.viz-loop-mini {
  height: 92px;
  margin-bottom: 10px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #f8fafc;
  overflow: hidden;
}
.viz-loop-mini.image,
.viz-loop-mini.batch {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
  padding: 8px;
}
.viz-loop-mini.image span,
.viz-loop-mini.batch span {
  border-radius: 7px;
  background: linear-gradient(135deg, #bfdbfe, #16a34a);
}
.viz-loop-mini.image span:first-child {
  grid-row: span 2;
  background:
    radial-gradient(circle at 35% 28%, #fef3c7 0 13%, transparent 14%),
    linear-gradient(135deg, #93c5fd 0 45%, #16a34a 46% 100%);
}
.viz-loop-mini.image span:nth-child(2),
.viz-loop-mini.batch span:nth-child(3) { background: linear-gradient(135deg, #fce7f3, #db2777); }
.viz-loop-mini.image span:nth-child(3),
.viz-loop-mini.batch span:nth-child(4) { background: linear-gradient(135deg, #ede9fe, #7c3aed); }
.viz-loop-mini.wave {
  display: grid;
  gap: 5px;
  align-content: center;
  padding: 14px;
}
.viz-loop-mini.wave span {
  height: 8px;
  border-radius: 999px;
  background: repeating-linear-gradient(90deg, #0d9488 0 10px, #bfdbfe 10px 18px);
}
.viz-loop-mini.wave span:nth-child(2) { transform: translateX(10px); opacity: 0.82; }
.viz-loop-mini.wave span:nth-child(3) { transform: translateX(20px); opacity: 0.68; }
.viz-loop-mini.vector {
  display: grid;
  grid-template-columns: repeat(9, 1fr);
  align-items: end;
  gap: 5px;
  padding: 10px;
}
.viz-loop-mini.vector span {
  border-radius: 4px 4px 2px 2px;
  background: linear-gradient(180deg, #2563eb, #bfdbfe);
}
.viz-loop-mini.score {
  display: grid;
  gap: 10px;
  align-content: center;
  padding: 12px;
}
.viz-loop-score-row {
  display: grid;
  grid-template-columns: 54px 1fr;
  gap: 8px;
  align-items: center;
  color: #6b7280;
  font-size: 0.7rem;
  font-weight: 800;
  text-transform: uppercase;
}
.viz-loop-score-track {
  height: 12px;
  border-radius: 999px;
  background: #e5e7eb;
  overflow: hidden;
}
.viz-loop-score-track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #f97316, #22c55e);
}
.viz-loop-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}
.viz-loop-chips span {
  padding: 4px 7px;
  border-radius: 999px;
  background: #f1f5f9;
  color: #334155;
  font-size: 0.68rem;
  font-weight: 800;
  line-height: 1;
}
.viz-loop-takeaway {
  margin-top: 16px;
  padding: 13px 14px;
  border: 1px solid #e5e7eb;
  border-left: 4px solid #2563eb;
  border-radius: 10px;
  background: white;
  color: #1f2937;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 0.9rem;
  line-height: 1.45;
}
@media (max-width: 840px) {
  .viz-loop-header { display: block; }
  .viz-loop-legend { justify-content: flex-start; margin-top: 12px; }
  .viz-loop-orbit {
    display: grid;
    gap: 12px;
    min-height: 0;
    padding: 14px;
    background: linear-gradient(180deg, rgba(239,246,255,0.9), white);
  }
  .viz-loop-arrows { display: none; }
  .viz-loop-core,
  .viz-loop-node {
    position: static !important;
    width: auto;
    min-height: 0;
    transform: none !important;
  }
  .viz-loop-node::after {
    content: "down";
    display: block;
    margin-top: 10px;
    color: #2563eb;
    font-weight: 900;
    text-align: center;
  }
  .viz-loop-node:last-child::after { content: "loops back"; font-size: 0.78rem; }
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


def mini_for_loop(kind: str) -> str:
    kind = kind if kind in {"image", "wave", "vector", "score", "batch"} else "vector"
    if kind == "image":
        return '<div class="viz-loop-mini image" aria-hidden="true"><span></span><span></span><span></span></div>'
    if kind == "wave":
        return '<div class="viz-loop-mini wave" aria-hidden="true"><span></span><span></span><span></span><span></span></div>'
    if kind == "score":
        return (
            '<div class="viz-loop-mini score" aria-hidden="true">'
            '<div class="viz-loop-score-row"><span>now</span><div class="viz-loop-score-track"><span style="width: 46%"></span></div></div>'
            '<div class="viz-loop-score-row"><span>target</span><div class="viz-loop-score-track"><span style="width: 78%"></span></div></div>'
            '<div class="viz-loop-score-row"><span>fit</span><div class="viz-loop-score-track"><span style="width: 64%"></span></div></div>'
            "</div>"
        )
    if kind == "batch":
        return '<div class="viz-loop-mini batch" aria-hidden="true"><span></span><span></span><span></span><span></span><span></span><span></span></div>'
    return (
        '<div class="viz-loop-mini vector" aria-hidden="true">'
        '<span style="height: 22%"></span><span style="height: 72%"></span><span style="height: 41%"></span>'
        '<span style="height: 88%"></span><span style="height: 58%"></span><span style="height: 36%"></span>'
        '<span style="height: 80%"></span><span style="height: 50%"></span><span style="height: 66%"></span>'
        "</div>"
    )


def render_closed_loop(spec: dict) -> str:
    steps = spec["steps"]
    if len(steps) != 5:
        raise SystemExit("closed-loop specs must have exactly five steps")

    title = esc(spec.get("title", "Closed-loop system"))
    caption = esc(spec.get("caption", "Follow the visible action, hidden data, score, and next action."))
    center = spec.get("center", {})
    center_label = esc(center.get("label", "target"))
    center_title = esc(center.get("title", "target feature"))
    center_text = esc(center.get("text", "The loop compares each round with this objective."))
    closing = spec.get("closing")
    legend = spec.get("legend", ["visible input", "hidden data", "selection pressure"])

    parts = [
        CLOSED_LOOP_CSS,
        '<figure class="viz-loop">',
        '  <div class="viz-loop-header">',
        "    <div>",
        f"      <h3>{title}</h3>",
        f'      <p>{caption}</p>',
        "    </div>",
        '    <div class="viz-loop-legend" aria-label="diagram legend">',
    ]
    for item in legend:
        parts.append(f"      <span>{esc(item)}</span>")
    parts.extend(
        [
            "    </div>",
            "  </div>",
            '  <div class="viz-loop-orbit">',
            '    <svg class="viz-loop-arrows" viewBox="0 0 960 690" preserveAspectRatio="none" aria-hidden="true">',
            "      <defs>",
            '        <marker id="vizLoopArrow" markerWidth="10" markerHeight="10" refX="7" refY="3" orient="auto">',
            '          <path d="M0,0 L0,6 L8,3 z"></path>',
            "        </marker>",
            "      </defs>",
            '      <path marker-end="url(#vizLoopArrow)" d="M270 132 C380 70, 575 70, 692 132"></path>',
            '      <path marker-end="url(#vizLoopArrow)" d="M806 242 C842 350, 824 492, 706 558"></path>',
            '      <path marker-end="url(#vizLoopArrow)" d="M646 620 C548 666, 406 666, 314 620"></path>',
            '      <path marker-end="url(#vizLoopArrow)" d="M174 558 C62 486, 62 254, 174 132"></path>',
            '      <path marker-end="url(#vizLoopArrow)" d="M292 474 C404 420, 562 420, 672 474"></path>',
            "    </svg>",
            '    <div class="viz-loop-core">',
            f'      <div class="viz-loop-core-label">{center_label}</div>',
            f"      <strong>{center_title}</strong>",
            '      <div class="viz-loop-vector" aria-hidden="true">',
            '        <span style="height: 44%"></span><span style="height: 72%"></span><span style="height: 58%"></span><span style="height: 86%"></span><span style="height: 36%"></span><span style="height: 64%"></span>',
            "      </div>",
            f"      <p>{center_text}</p>",
            "    </div>",
        ]
    )

    for index, step in enumerate(steps, 1):
        label = esc(step.get("label", f"Step {index}"))
        meaning = esc(step.get("meaning", "what this step does"))
        mini = mini_for_loop(str(step.get("mini", "vector")))
        chips = step.get("chips", [])
        parts.extend(
            [
                f'    <article class="viz-loop-node viz-loop-node-{index}">',
                f"      <h4>{index}. {label}</h4>",
                f"      {mini}",
                f"      <p>{meaning}</p>",
                '      <div class="viz-loop-chips">',
            ]
        )
        for chip in chips[:5]:
            parts.append(f"        <span>{esc(chip)}</span>")
        parts.extend(["      </div>", "    </article>"])

    parts.append("  </div>")
    if closing:
        parts.append(f'  <div class="viz-loop-takeaway">{esc(closing)}</div>')
    parts.append("</figure>")
    return "\n".join(parts) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate explainer visualization fragments.")
    sub = parser.add_subparsers(dest="command", required=True)
    flow = sub.add_parser("process-flow", help="generate a process/loop flow figure")
    flow.add_argument("spec", help="JSON spec file")
    loop = sub.add_parser("closed-loop", help="generate a circular closed-loop figure")
    loop.add_argument("spec", help="JSON spec file with exactly five steps")
    args = parser.parse_args()

    if args.command == "process-flow":
        sys.stdout.write(render_process_flow(load_spec(args.spec)))
        return 0
    if args.command == "closed-loop":
        sys.stdout.write(render_closed_loop(load_spec(args.spec)))
        return 0
    raise SystemExit(f"unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
