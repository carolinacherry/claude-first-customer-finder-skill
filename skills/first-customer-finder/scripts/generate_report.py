#!/usr/bin/env python3
"""Render a First Customer Finder analysis JSON as a standalone HTML report."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SCORE_DIMENSIONS = {
    "pain": "Pain strength",
    "fit": "Product fit",
    "timing": "Timing",
    "reachability": "Reachability",
    "evidence": "Evidence quality",
}

STAGE_CLASSES = {
    "high": "stage-high",
    "problem": "stage-warm",
    "trigger": "stage-warm",
}


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def clamp(value: Any, maximum: int = 100) -> int:
    try:
        number = round(float(value))
    except (TypeError, ValueError):
        number = 0
    return max(0, min(maximum, number))


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def safe_url(value: Any) -> str:
    raw = str(value or "").strip()
    parsed = urlparse(raw)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return esc(raw)
    return "#"


def stage_class(stage: Any) -> str:
    value = str(stage or "").lower()
    for needle, cls in STAGE_CLASSES.items():
        if needle in value:
            return cls
    return "stage-cool"


def score_band(score: int) -> str:
    if score >= 80:
        return "Strong candidate"
    if score >= 65:
        return "Promising"
    return "Needs validation"


def render_scores(scores: dict[str, Any]) -> str:
    rows = []
    for key, label in SCORE_DIMENSIONS.items():
        value = clamp(scores.get(key, 0), 5)
        rows.append(
            f'<div class="dim"><span>{esc(label)}</span>'
            f'<div class="bar"><i style="width:{value * 20}%"></i></div>'
            f"<b>{value}/5</b></div>"
        )
    return "".join(rows)


def render_prospect(prospect: dict[str, Any], index: int) -> str:
    score = clamp(prospect.get("score"))
    source = as_dict(prospect.get("source"))
    url = safe_url(source.get("url"))
    return f"""
      <article class="prospect">
        <header>
          <span class="index">{index:02d}</span>
          <div class="who">
            <small>{esc(prospect.get('type', 'Public prospect'))}</small>
            <h3>{esc(prospect.get('name', f'Prospect {index}'))}</h3>
            <span class="stage {stage_class(prospect.get('stage'))}">{esc(prospect.get('stage', 'Potential fit'))}</span>
          </div>
          <div class="fit">
            <strong>{score}</strong>
            <div class="fit-bar"><i style="width:{score}%"></i></div>
            <small>{esc(score_band(score))}</small>
          </div>
        </header>
        <p class="signal">{esc(prospect.get('signal', ''))}</p>
        <dl class="facts">
          <div><dt>Why it fits</dt><dd>{esc(prospect.get('why_fit', ''))}</dd></div>
          <div><dt>Why now</dt><dd>{esc(prospect.get('why_now', ''))}</dd></div>
          <div><dt>Channel</dt><dd>{esc(prospect.get('channel', ''))}</dd></div>
          <div><dt>Caution</dt><dd>{esc(prospect.get('caution', 'Confirm the signal is still current before outreach.'))}</dd></div>
        </dl>
        <div class="opener"><dt>Suggested opener (draft — never auto-sent)</dt><p>{esc(prospect.get('opener', ''))}</p></div>
        <details>
          <summary>Evidence &amp; score breakdown</summary>
          <p>{esc(prospect.get('evidence', ''))}</p>
          <p class="source">
            {esc(source.get('type', 'Public source'))} · {esc(source.get('date', 'date unavailable'))} ·
            <a href="{url}" target="_blank" rel="noreferrer">{esc(source.get('title', 'Open original source'))} ↗</a>
          </p>
          <div class="dims">{render_scores(as_dict(prospect.get('scores')))}</div>
        </details>
      </article>"""


def render_pattern(pattern: dict[str, Any]) -> str:
    return (
        f'<article class="pattern"><strong>{clamp(pattern.get("count"), 999)}×</strong>'
        f'<div><h3>{esc(pattern.get("title", "Repeated signal"))}</h3>'
        f'<p>{esc(pattern.get("insight", ""))}</p></div></article>'
    )


def build_html(data: dict[str, Any]) -> str:
    prospects = [p for p in as_list(data.get("prospects")) if isinstance(p, dict)]
    patterns = [p for p in as_list(data.get("patterns")) if isinstance(p, dict)]
    plan = as_dict(data.get("outreach_plan"))
    scores = [clamp(p.get("score")) for p in prospects]
    average = round(sum(scores) / len(scores)) if scores else 0
    high_intent = sum(1 for p in prospects if "high" in str(p.get("stage", "")).lower())
    top = max(prospects, key=lambda p: clamp(p.get("score")), default={})
    top_source = as_dict(top.get("source"))

    prospect_html = "".join(render_prospect(p, i) for i, p in enumerate(prospects, 1))
    pattern_html = "".join(render_pattern(p) for p in patterns)
    limits_html = "".join(f"<li>{esc(x)}</li>" for x in as_list(data.get("limits")))
    plan_html = "".join(
        f'<div><dt>{esc(label)}</dt><dd>{esc(plan.get(key, ""))}</dd></div>'
        for key, label in (
            ("first_step", "First step"),
            ("follow_up", "Follow-up"),
            ("success", "Success signal"),
        )
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{esc(data.get('title', 'First Customer Finder'))}</title>
<style>
  :root{{--paper:#faf7f2;--card:#ffffff;--ink:#1c1917;--muted:#6f675e;--line:#e4ddd2;--accent:#c2410c;--accent-soft:#fff1e7;--good:#166534;--radius:14px}}
  @media(prefers-color-scheme:dark){{:root{{--paper:#151312;--card:#1e1b19;--ink:#efeae3;--muted:#a39a8f;--line:#332e29;--accent:#fb923c;--accent-soft:#2b2019;--good:#4ade80}}}}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 ui-sans-serif,-apple-system,"Segoe UI",sans-serif}}
  .wrap{{max-width:960px;margin:0 auto;padding:0 24px 64px}}
  a{{color:var(--accent)}}
  header.masthead{{padding:56px 0 32px;border-bottom:2px solid var(--ink)}}
  .kicker{{font:700 12px/1 ui-monospace,monospace;letter-spacing:.12em;text-transform:uppercase;color:var(--accent)}}
  h1{{font-size:clamp(34px,6vw,58px);line-height:1.04;letter-spacing:-.03em;margin:14px 0 18px}}
  .verdict{{font-size:clamp(17px,2.2vw,21px);max-width:52em;margin:0}}
  .facts-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;margin:28px 0 48px}}
  .facts-row>div{{background:var(--card);padding:14px 16px}}
  .facts-row dt,dt{{font:700 10px/1.4 ui-monospace,monospace;letter-spacing:.09em;text-transform:uppercase;color:var(--muted)}}
  .facts-row dd,dd{{margin:4px 0 0;font-weight:600;font-size:15px}}
  .top-pick{{display:flex;gap:20px;align-items:baseline;justify-content:space-between;flex-wrap:wrap;background:var(--accent-soft);border:1px solid var(--accent);border-radius:var(--radius);padding:20px 24px;margin-bottom:48px}}
  .top-pick h2{{margin:6px 0 4px;font-size:26px;letter-spacing:-.02em}}
  .top-pick p{{margin:0;color:var(--muted)}}
  .top-pick strong.big{{font-size:44px;letter-spacing:-.04em;color:var(--accent)}}
  h2.section{{font-size:clamp(24px,3.4vw,34px);letter-spacing:-.025em;border-bottom:1px solid var(--line);padding-bottom:10px;margin:56px 0 8px}}
  .section-note{{color:var(--muted);margin:0 0 24px}}
  .prospect{{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:22px 24px;margin-bottom:16px;break-inside:avoid}}
  .prospect header{{display:grid;grid-template-columns:44px 1fr 150px;gap:14px;align-items:start}}
  .index{{font:800 20px ui-monospace,monospace;color:var(--accent);padding-top:4px}}
  .who small{{font:700 10px/1 ui-monospace,monospace;letter-spacing:.09em;text-transform:uppercase;color:var(--muted)}}
  .who h3{{margin:4px 0 8px;font-size:22px;letter-spacing:-.02em}}
  .stage{{display:inline-block;font:700 11px/1 ui-monospace,monospace;letter-spacing:.05em;text-transform:uppercase;border:1px solid var(--line);border-radius:999px;padding:6px 10px;color:var(--muted)}}
  .stage-high{{color:var(--accent);border-color:var(--accent)}}
  .stage-warm{{color:var(--good);border-color:var(--good)}}
  .fit{{text-align:right}}
  .fit strong{{font-size:30px;letter-spacing:-.03em}}
  .fit small{{display:block;color:var(--muted);margin-top:4px}}
  .fit-bar{{height:6px;background:var(--line);border-radius:6px;overflow:hidden;margin-top:6px}}
  .fit-bar i,.bar i{{display:block;height:100%;background:var(--accent)}}
  .signal{{font-size:17px;border-left:3px solid var(--accent);padding:10px 16px;background:var(--accent-soft);margin:18px 0 14px}}
  dl.facts{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:0}}
  dl.facts>div{{border:1px solid var(--line);border-radius:10px;padding:12px 14px}}
  .opener{{border:1px dashed var(--accent);border-radius:10px;padding:12px 16px;margin-top:12px}}
  .opener p{{margin:6px 0 0;font-style:italic}}
  details{{margin-top:12px}}
  summary{{cursor:pointer;font-weight:700;color:var(--accent)}}
  .source{{color:var(--muted);font-size:14px}}
  .dims{{display:grid;gap:6px;margin-top:10px}}
  .dim{{display:grid;grid-template-columns:130px 1fr 40px;gap:12px;align-items:center;font-size:13px}}
  .dim .bar{{height:6px;background:var(--line);border-radius:6px;overflow:hidden}}
  .patterns{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
  .pattern{{display:flex;gap:16px;background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:18px 20px}}
  .pattern strong{{font-size:26px;color:var(--accent);letter-spacing:-.03em}}
  .pattern h3{{margin:0 0 4px;font-size:17px}}
  .pattern p{{margin:0;color:var(--muted);font-size:14px}}
  .plan{{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:24px}}
  .plan .angle{{font-size:21px;font-weight:700;letter-spacing:-.015em;margin:4px 0 18px}}
  .plan-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}
  .plan-grid>div{{border:1px solid var(--line);border-radius:10px;padding:12px 14px}}
  .limits{{border:1px solid var(--line);border-radius:var(--radius);padding:8px 24px;color:var(--muted)}}
  footer{{margin-top:48px;padding-top:18px;border-top:1px solid var(--line);display:flex;justify-content:space-between;gap:16px;color:var(--muted);font-size:13px}}
  @media(max-width:720px){{.facts-row{{grid-template-columns:1fr 1fr}}.prospect header{{grid-template-columns:32px 1fr}}.fit{{grid-column:1/-1;text-align:left}}dl.facts,.patterns,.plan-grid{{grid-template-columns:1fr}}}}
  @media print{{body{{background:#fff}}.prospect,.pattern,.plan{{border-color:#ccc}}details{{open:true}}}}
</style>
</head>
<body>
<div class="wrap">
  <header class="masthead">
    <span class="kicker">First customer finder · {esc(data.get('generated_at', ''))} · {esc(data.get('mode', 'standard'))} mode</span>
    <h1>{esc(data.get('title', 'First Customer Finder'))}</h1>
    <p class="verdict">{esc(data.get('verdict', 'No verdict supplied.'))}</p>
  </header>

  <dl class="facts-row">
    <div><dt>Product</dt><dd><a href="{safe_url(data.get('product_url'))}" target="_blank" rel="noreferrer">{esc(data.get('product', 'Not specified'))}</a></dd></div>
    <div><dt>Target customer</dt><dd>{esc(data.get('target_customer', 'Not specified'))}</dd></div>
    <div><dt>Qualified prospects</dt><dd>{len(prospects)} ({high_intent} high intent)</dd></div>
    <div><dt>Average fit score</dt><dd>{average}/100</dd></div>
  </dl>

  <section class="top-pick">
    <div>
      <span class="kicker">Highest-confidence prospect</span>
      <h2>{esc(top.get('name', 'No qualified prospect'))}</h2>
      <p>{esc(top.get('why_now', top.get('signal', '')))}</p>
    </div>
    <strong class="big">{clamp(top.get('score'))}</strong>
  </section>

  <h2 class="section">Prospects with a reason to care now</h2>
  <p class="section-note">Every entry is tied to a verified public signal — open the evidence before considering outreach. Scope: {esc(data.get('search_scope', 'not specified'))}.</p>
  {prospect_html or '<p>No qualified prospects supplied.</p>'}

  <h2 class="section">Signals that repeat</h2>
  <p class="section-note">Recurring pains and triggers across prospects — your strongest positioning and outreach angles.</p>
  <div class="patterns">{pattern_html or '<p>No repeated patterns supplied.</p>'}</div>

  <h2 class="section">Seven-day manual validation plan</h2>
  <div class="plan">
    <span class="kicker">Angle</span>
    <p class="angle">{esc(plan.get('angle', 'Validate the pain before pitching the product.'))}</p>
    <div class="plan-grid">{plan_html}</div>
  </div>

  <h2 class="section">Read this before acting</h2>
  <ul class="limits">{limits_html or '<li>Potential customers inferred from public signals, not confirmed buyers.</li>'}</ul>

  <footer>
    <span>Generated by the first-customer-finder skill</span>
    <span>Public signals only · outreach is never sent automatically</span>
  </footer>
</div>
</body>
</html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Path to analysis JSON")
    parser.add_argument("output", type=Path, help="Path to output HTML")
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("Input JSON must be an object at the top level.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_html(data), encoding="utf-8")
    print(f"Created report: {args.output.resolve()}")


if __name__ == "__main__":
    main()
