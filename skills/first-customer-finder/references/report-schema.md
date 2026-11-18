# Report Schema

The report generator turns a JSON analysis into a standalone HTML report. Write the JSON to a work/temp directory, then:

```bash
python3 scripts/generate_report.py analysis.json outputs/first-customer-report.html
```

The script is stdlib-only Python 3.9+. Return the absolute output path as a clickable link. Keep the JSON out of the final answer unless the user asks for raw data.

## Schema

```json
{
  "title": "First customers for Example",
  "product": "Example",
  "product_url": "https://example.com",
  "target_customer": "Independent gym owners",
  "search_scope": "Public English-language sources, last 12 months",
  "generated_at": "2026-07-13",
  "mode": "standard",
  "verdict": "One short paragraph that says where the strongest early-customer signals are and who leads the list. Do not open with yes or no; the page never shows a question.",
  "prospects": [
    {
      "name": "Example Gym",
      "type": "Company",
      "stage": "Problem aware",
      "score": 82,
      "signal": "The owner publicly described manually chasing failed membership payments every week.",
      "evidence": "Recent public forum post describing the workflow and its time cost in first person.",
      "why_fit": "The product automates exactly the reminder and retry step described.",
      "why_now": "The post is three weeks old and asks how other owners handle it.",
      "source": {
        "title": "How do you handle failed payments?",
        "url": "https://example.com/public-post",
        "type": "Public forum",
        "date": "2026-06-20"
      },
      "channel": "Reply in the public thread",
      "opener": "Saw your question about failed-payment follow-up...",
      "caution": "Confirm the workflow is still manual before pitching.",
      "scores": {
        "pain": 5,
        "fit": 5,
        "timing": 4,
        "reachability": 4,
        "evidence": 4
      }
    }
  ],
  "patterns": [
    {
      "title": "Manual follow-up",
      "count": 4,
      "insight": "Owners fall back to spreadsheets and DMs once a payment fails."
    }
  ],
  "outreach_plan": {
    "angle": "Offer a manual concierge test before asking for software adoption.",
    "first_step": "Message the three highest-scoring prospects with one source-grounded question.",
    "follow_up": "Share a two-minute demo only after they confirm the pain is current.",
    "success": "Three conversations and one design-partner commitment within seven days."
  },
  "limits": [
    "Potential customers inferred from public signals, not confirmed buyers.",
    "Verify each signal is still current before outreach; keep all contact manual."
  ]
}
```

## Rules

- `standard` mode: up to 10 prospects. `quick`: up to 5. `deep`: up to 20.
- Every prospect requires a real, verified `source.url` (http/https) and a 0–100 `score` consistent with its `scores` breakdown.
- `scores` keys are `pain`, `fit`, `timing`, `reachability`, `evidence`, each 0–5.
- Missing optional fields render with safe defaults; do not invent filler to fill them.
