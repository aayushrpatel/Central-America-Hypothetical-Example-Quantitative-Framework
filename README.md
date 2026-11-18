# Central-America-Hypothetical

**Question:** if Central America drifted apart into islands, so the Panama Canal is no longer needed to cross between the Atlantic and Pacific, what happens to US LNG exports to Asia, the JKM–TTF spread, and US export volumes and destination mix?

## Contents

| Path | What it is |
|---|---|
| `memo/memo.pdf` | **The deliverable.** 2-page memo with a sources appendix |
| `memo/memo.md` | Same memo in Markdown |
| `memo/spread_vs_thresholds.png` | Chart: annual JKM–TTF spread vs the old and new US→Asia arbitrage thresholds |
| `analysis/framework.md` | The 5-step framework and the stress test of the plan |
| `analysis/lng_model.py` | All inputs (with sources) and calculations, printed line by line |
| `analysis/model_output.txt` | Output of the model run |
| `analysis/build_memo_pdf.py` | Renders `memo.md` → `memo.pdf` (Chromium via Playwright) |

## Reproduce

```bash
pip install matplotlib markdown
python3 analysis/lng_model.py
python3 analysis/build_memo_pdf.py
```

## Headline result (base case)

- **Freight:** an open-water strait saves ~$0.87/MMBtu and ~16 days one-way on US Gulf→Asia versus today's Cape of Good Hope route.
- **Spread:** the ceiling on the JKM–TTF spread falls from $1.45 to $0.58/MMBtu. Replaying 2019–25 gives an average compression of ~$0.40 (range $0.25–0.40 across freight cases): TTF +$0.27, JKM −$0.13.
- **Volume:** total US export volume is unchanged in the short run (plants at ~98% of capacity). Only ~0.6–1.3 Mt/yr shifts from Europe to Asia.
- **Shipping:** ~33 LNG carriers (4% of the fleet) are freed and ~$1.3bn/yr of freight is saved.
