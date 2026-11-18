# Framework and stress test

## Plan

| Step | Question | Method (one line) | Key inputs |
|---|---|---|---|
| 1. Freight | How much cheaper and faster is US Gulf → Asia once the canal is open sea? | $/MMBtu = (round-trip days × [charter + fuel] + port + tolls) ÷ delivered MMBtu | Distances, speed, charter, boil-off, Panama tolls |
| 2. Threshold | When does a US cargo choose Asia over Europe? | Go to Asia if JKM − TTF > F_Asia − F_Europe; the threshold falls by the freight saving | Step 1 |
| 3. Binding test | Does the lower threshold change the observed JKM−TTF? | Replay 2019–25 spreads: compression = clip(spread − new threshold, 0, saving) | Annual JKM, TTF |
| 4. Price split | Does JKM fall or TTF rise? | Fixed supply: the volume-weighted price is unchanged, so the split follows import shares | Asia/Europe LNG imports |
| 5. Volumes | Do total US exports or the regional mix change? | Utilization check; Mt moved = compression × kA·kE/(kA+kE); ship-days saved | Capacity, demand response, fleet |

## Stress test: what changed in the plan and why

1. **Baseline route.** Panama is the intuitive baseline, but since 2024 about 94% of US→Asia cargoes have gone via the Cape. The hypothetical is therefore measured against the Cape, with Panama shown only as a comparison. This is the difference between a $0.87 and a $0.42 saving.
2. **Cost vs price.** The thesis says lower freight lowers the Asian price, but prices are set at the margin. So freight only matters when the spread would otherwise sit above the new threshold. That is why Step 3 (the binding test) is needed.
3. **The threshold is a ceiling, not a floor.** When Europe is short (2022, TTF > JKM), the strait has no effect. The replay captures this automatically.
4. **Volume is capacity-bound.** US plants run at ~98% of capacity, so total volume cannot respond in the short run, and only the mix can. Moving more cargo to Asia does not "drain" Europe one-for-one either. Prices adjust until netbacks equalize, so the quantity moved depends on how responsive demand is (Step 5).
5. **Cross-checks against independent data:**
   - Platts' published route costs and arbitrage prints (2024–26).
   - The 2026 Qatar/Hormuz outage as a live test: the arbitrage was open via Panama but closed via the Cape.
   - Two independent estimates of demand response (OIES, the 2026 shock), both around 7 Mt per $1.
6. **Kept simple on purpose.** The model uses one freight level (with a ±sensitivity), annual data and equal elasticities. Each simplification is listed in the memo, along with the direction it biases the result (mostly conservative).
