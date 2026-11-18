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


def score_band(score: int) -> str:
    if score >= 80:
        return "Strong candidate"
    if score >= 65:
        return "Promising"
    return "Needs validation"


def render_scores(scores: dict[str, Any]) -> str:
    return "".join(
        f'<div><dt>{esc(label)}</dt><dd>{clamp(scores.get(key, 0), 5)} of 5</dd></div>'
        for key, label in SCORE_DIMENSIONS.items()
    )


def render_prospect(prospect: dict[str, Any], index: int) -> str:
    score = clamp(prospect.get("score"))
    source = as_dict(prospect.get("source"))
    url = safe_url(source.get("url"))
    rows = "".join(
        f"<dt>{esc(label)}</dt><dd>{esc(value)}</dd>"
        for label, value in (
            ("Why it fits", prospect.get("why_fit")),
            ("Why now", prospect.get("why_now")),
            ("Channel", prospect.get("channel")),
            ("Caution", prospect.get("caution") or "Confirm the signal is still current before outreach."),
        )
        if value
    )
    opener = prospect.get("opener")
    opener_html = (
        '      <div class="opener">\n'
        '        <p class="label">Suggested opener, draft only and never sent automatically</p>\n'
        f"        <p>{esc(opener)}</p>\n"
        "      </div>"
        if opener
        else ""
    )
    evidence_html = f"""        <p>{esc(prospect.get('evidence', ''))}</p>
        <p class="source">
          {esc(source.get('type', 'Public source'))}, {esc(source.get('date', 'date unavailable'))}
          <span aria-hidden="true">&middot;</span>
          <a href="{url}" target="_blank" rel="noreferrer">{esc(source.get('title', 'Open original source'))}</a>
        </p>
        <dl class="dims">{render_scores(as_dict(prospect.get('scores')))}</dl>"""
    return f"""
    <article class="prospect">
      <header class="p-head">
        <div>
          <h3>{esc(prospect.get('name') or f'Prospect {index}')}</h3>
          <p class="sub">{esc(prospect.get('type', 'Public prospect'))} <span aria-hidden="true">&middot;</span> {esc(prospect.get('stage', 'Potential fit'))}</p>
        </div>
        <div class="score"><b class="num">{score}</b><span>{esc(score_band(score))}</span></div>
      </header>
      {f'<p class="signal">{esc(prospect.get("signal"))}</p>' if prospect.get("signal") else ''}
      <dl class="kv">{rows}</dl>
{opener_html}
      <details class="screen-only">
        <summary>Evidence and score breakdown</summary>
{evidence_html}
      </details>
      <div class="print-only">
        <p class="label">Evidence and score breakdown</p>
{evidence_html}
      </div>
    </article>"""


def render_pattern(pattern: dict[str, Any]) -> str:
    return (
        f'<div class="pattern"><b class="num">{clamp(pattern.get("count"), 999)}</b>'
        f'<div><h4>{esc(pattern.get("title", "Repeated signal"))}</h4>'
        f'<p>{esc(pattern.get("insight", ""))}</p></div></div>'
    )


CSS = """
:root{--bg:#f6f5f2;--sheet:#fff;--ink:#18181a;--ink2:#54545b;--ink3:#86868d;--line:#ecebe7;--tint:#f4f3ef;--accent:#2f5d50;--link-line:#cfcfca;
  --shadow:0 1px 2px rgba(20,20,20,.04),0 12px 40px -12px rgba(20,20,20,.08);
  --sans:ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,"Helvetica Neue",Arial,sans-serif}
@media(prefers-color-scheme:dark){:root{--bg:#121211;--sheet:#1a1a19;--ink:#ecebe7;--ink2:#a8a7a1;--ink3:#8a8983;--line:rgba(255,255,255,.07);--tint:#222220;--accent:#93b5a6;--link-line:#4a4a46;--shadow:0 1px 2px rgba(0,0,0,.3)}}
*{box-sizing:border-box}
html{-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 var(--sans)}
a{color:var(--ink);text-decoration:underline;text-decoration-color:var(--link-line);text-underline-offset:3px}
a:hover{text-decoration-color:currentColor}
.num{font-variant-numeric:tabular-nums}
.sheet{max-width:880px;margin:40px auto 64px;background:var(--sheet);border-radius:28px;box-shadow:var(--shadow);padding:72px 80px 56px}
.meta{color:var(--ink3);font-size:13px;margin:0}
h1{font-weight:300;font-size:clamp(32px,5vw,46px);line-height:1.08;letter-spacing:-.035em;margin:18px 0 22px;max-width:15em}
.verdict{font-size:18px;line-height:1.6;color:var(--ink2);max-width:36em;margin:0}
.facts{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:48px 0 0;padding:22px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.facts dt,.kv dt,.steps dt,.dims dt,.label,.eyebrow{color:var(--ink3);font-size:13px;font-weight:400}
.facts dd{margin:4px 0 0;font-weight:500}
.top{display:flex;justify-content:space-between;align-items:flex-end;gap:32px;margin:56px 0 0}
.top h2{font-weight:400;font-size:28px;line-height:1.2;letter-spacing:-.025em;margin:6px 0 8px}
.top p{margin:0;color:var(--ink2);max-width:32em}
.top .big{font-weight:300;font-size:64px;line-height:1;letter-spacing:-.05em;color:var(--accent)}
section.block{margin-top:80px}
.eyebrow{margin:0}
h2.section{font-weight:400;font-size:26px;line-height:1.2;letter-spacing:-.025em;margin:8px 0 6px}
.note{color:var(--ink3);font-size:14px;margin:0 0 12px;max-width:40em}
.prospect{padding:36px 0;border-bottom:1px solid var(--line);break-inside:avoid;page-break-inside:avoid}
.prospect:last-child{border-bottom:0}
.p-head{display:flex;justify-content:space-between;gap:24px;align-items:baseline}
.p-head h3{font-weight:500;font-size:20px;line-height:1.3;letter-spacing:-.02em;margin:0}
.sub{color:var(--ink3);font-size:13px;margin:4px 0 0}
.score{text-align:right;white-space:nowrap}
.score b{font-weight:400;font-size:30px;line-height:1;letter-spacing:-.03em}
.score span{display:block;color:var(--ink3);font-size:12px;margin-top:6px}
.signal{font-size:17px;line-height:1.55;margin:18px 0 22px;max-width:38em}
.kv:empty{display:none}.p-head+.kv{margin-top:18px}.kv{display:grid;grid-template-columns:120px 1fr;gap:10px 24px;margin:0}
.kv dd{margin:0;color:var(--ink2);font-size:14px}
.kv dt{font-size:14px}
.opener{background:var(--tint);border-radius:16px;padding:18px 22px;margin:22px 0 0}
.opener p{margin:6px 0 0}.opener .label{margin:0}
details{margin-top:16px}
summary{cursor:pointer;color:var(--ink2);font-size:14px;list-style:none;display:inline-block}
summary::-webkit-details-marker{display:none}
summary::after{content:" +";color:var(--ink3)}
details[open] summary::after{content:" \\2212"}
details p,.print-only p{color:var(--ink2);font-size:14px;margin:10px 0 0;max-width:42em}
.source{color:var(--ink3)}
.dims{display:flex;flex-wrap:wrap;gap:6px 28px;margin:12px 0 0}
.dims div{display:flex;gap:8px}.dims dd{margin:0;font-size:13px;color:var(--ink)}.dims dt{font-size:13px}
.patterns{margin-top:12px}
.pattern{display:grid;grid-template-columns:56px 1fr;gap:16px;padding:18px 0;border-top:1px solid var(--line);break-inside:avoid}
.pattern b{font-weight:300;font-size:28px;line-height:1}
.pattern h4{margin:0;font-size:15px;font-weight:500}
.pattern p{margin:2px 0 0;color:var(--ink2);font-size:14px}
.angle{font-weight:400;font-size:22px;line-height:1.4;letter-spacing:-.02em;margin:10px 0 22px;max-width:30em}
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:32px;border-top:1px solid var(--line);padding-top:20px;margin:0}
.steps dd{margin:4px 0 0;font-size:14px;color:var(--ink2)}
.limits{margin:10px 0 0;padding:0;list-style:none}
.limits li{padding:10px 0;border-top:1px solid var(--line);color:var(--ink2);font-size:14px}
.print-only{display:none}
.empty{color:var(--ink3);font-size:14px;padding:18px 0;margin:0}
footer{margin-top:56px;display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;color:var(--ink3);font-size:12px}
@media screen and (max-width:760px){.sheet{margin:0;border-radius:0;box-shadow:none;padding:40px 22px}.facts,.steps{grid-template-columns:1fr 1fr;gap:16px}.kv{grid-template-columns:1fr;gap:2px}.kv dd{margin-bottom:10px}.top .big{font-size:48px}}
@page{margin:14mm}
@media print{
  :root{--bg:#fff;--sheet:#fff;--ink:#111;--ink2:#444;--ink3:#777;--line:#e2e2de;--tint:#f4f3ef;--accent:#2f5d50;--link-line:#bbb;--shadow:none}
  body{background:#fff;font-size:12.5px}
  .sheet{margin:0;max-width:none;padding:0;border-radius:0;box-shadow:none;zoom:.92}
  section.block{margin-top:40px}
  .top,.opener,.pattern,.steps{break-inside:avoid}
  .eyebrow,h2.section,.note{break-after:avoid}
  .screen-only{display:none}.print-only{display:block;margin-top:10px}
  .prospect{padding:20px 0}
  .signal{font-size:14px;margin:10px 0 12px}
  .kv{gap:4px 20px}.kv dt,.kv dd{font-size:12px}
  .opener{padding:10px 14px;margin-top:12px;border-radius:10px}
  details{margin-top:10px}details p,.print-only p{font-size:12px;margin-top:6px}
  .score b{font-size:24px}
  .opener{-webkit-print-color-adjust:exact;print-color-adjust:exact}
}
"""



def build_html(data: dict[str, Any]) -> str:
    prospects = [p for p in as_list(data.get("prospects")) if isinstance(p, dict)]
    patterns = [p for p in as_list(data.get("patterns")) if isinstance(p, dict)]
    plan = as_dict(data.get("outreach_plan"))
    scores = [clamp(p.get("score")) for p in prospects]
    average = round(sum(scores) / len(scores)) if scores else 0
    high_intent = sum(1 for p in prospects if "high" in str(p.get("stage", "")).lower())
    top = max(prospects, key=lambda p: clamp(p.get("score")), default={})
    top_name = top.get("name") or f"Prospect {prospects.index(top) + 1}" if top else ""
    meta = ' <span aria-hidden="true">&middot;</span> '.join(
        esc(part)
        for part in (
            "First Customer Finder",
            data.get("generated_at"),
            f"{str(data.get('mode') or 'standard').capitalize()} mode",
        )
        if part
    )

    prospect_html = "".join(render_prospect(p, i) for i, p in enumerate(prospects, 1))
    pattern_html = "".join(render_pattern(p) for p in patterns)
    limits_html = "".join(f"<li>{esc(x)}</li>" for x in as_list(data.get("limits")))
    plan_html = "".join(
        f'<div><dt>{esc(label)}</dt><dd>{esc(plan.get(key, ""))}</dd></div>'
        for key, label in (
            ("first_step", "First step"),
            ("follow_up", "Follow up"),
            ("success", "Success signal"),
        )
    )
    top_html = (
        f"""
  <section class="top">
    <div>
      <p class="eyebrow">Highest confidence prospect</p>
      <h2>{esc(top_name)}</h2>
      <p>{esc(top.get('why_now', top.get('signal', '')))}</p>
    </div>
    <div class="big num">{clamp(top.get('score'))}</div>
  </section>"""
        if top
        else ""
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{esc(data.get('title', 'First Customer Finder'))}</title>
<style>{CSS}</style>
</head>
<body>
<main class="sheet">
  <header>
    <p class="meta">{meta}</p>
    <h1>{esc(data.get('title', 'First Customer Finder'))}</h1>
    <p class="verdict">{esc(data.get('verdict', 'No verdict supplied.'))}</p>
  </header>

  <dl class="facts">
    <div><dt>Product</dt><dd><a href="{safe_url(data.get('product_url'))}" target="_blank" rel="noreferrer">{esc(data.get('product', 'Not specified'))}</a></dd></div>
    <div><dt>Target customer</dt><dd>{esc(data.get('target_customer', 'Not specified'))}</dd></div>
    <div><dt>Qualified prospects</dt><dd class="num">{len(prospects)} <span class="sub">({high_intent} high intent)</span></dd></div>
    <div><dt>Average fit score</dt><dd class="num">{average} of 100</dd></div>
  </dl>
{top_html}
  <section class="block">
    <p class="eyebrow">Shortlist</p>
    <h2 class="section">Prospects with a reason to care now</h2>
    <p class="note">Every entry is tied to a verified public signal. Open the evidence before considering outreach. Scope: {esc(data.get('search_scope', 'not specified'))}.</p>
    {prospect_html or '<p class="empty">No qualified prospects supplied.</p>'}
  </section>

  <section class="block">
    <p class="eyebrow">Patterns</p>
    <h2 class="section">Signals that repeat</h2>
    <p class="note">Recurring pains and triggers across prospects. These are your strongest positioning and outreach angles.</p>
    <div class="patterns">{pattern_html or '<p class="empty">No repeated patterns supplied.</p>'}</div>
  </section>

  <section class="block">
    <p class="eyebrow">Next seven days</p>
    <h2 class="section">Manual validation plan</h2>
    <p class="angle">{esc(plan.get('angle', 'Validate the pain before pitching the product.'))}</p>
    <dl class="steps">{plan_html}</dl>
  </section>

  <section class="block">
    <p class="eyebrow">Limits</p>
    <h2 class="section">Read this before acting</h2>
    <ul class="limits">{limits_html or '<li>Potential customers inferred from public signals, not confirmed buyers.</li>'}</ul>
  </section>

  <footer>
    <span>Generated by the first-customer-finder skill</span>
    <span>Public signals only. Outreach is never sent automatically.</span>
  </footer>
</main>
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
