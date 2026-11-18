"""
Central America as islands -> what happens to US LNG to Asia and the JKM-TTF spread?

A deliberately simple, first-principles model. Run:  python3 analysis/lng_model.py
Every input is listed once in section 0 with its source; every result is printed
line by line so it can be checked by hand.

Framework (5 steps)
  1. Freight: cost of each route = round-trip days x daily cost + fixed fees.
  2. Arbitrage threshold: a US cargo goes to Asia only if JKM - TTF > F_Asia - F_Europe.
  3. Does the lower threshold bind? Replay 2019-2025 spreads against old/new thresholds.
  4. Price split: who absorbs the spread compression (JKM down vs TTF up)?
  5. Volumes & mix: total US exports, share to Asia, ships freed.
"""

from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent.parent / "memo"

# ---------------------------------------------------------------------------
# 0. INPUTS (one place; source in comment)
# ---------------------------------------------------------------------------
# Ship & cargo
SPEED_KN = 17.0            # Platts route-cost basis; matches Kpler 38 d (Cape) / 22 d (Panama) voyages
CAPACITY_M3 = 174_000      # standard modern two-stroke LNG carrier
FILL = 0.985               # Platts fillable volume
T_PER_M3 = 0.45            # GIIGNL / IGU conversion
MMBTU_PER_T = 52.0         # Platts conversion factor
DELIVERED_MMBTU = 3.9e6    # loaded ~4.0m less boil-off/heel (rounded)
PORT_DAYS = 2.0            # 1 day load + 1 day discharge per round trip
PORT_COST = 200_000        # $ per round trip (WoodMac: US Gulf <$70k/call; others $70-190k)

# Daily cost
CHARTER = {"low (2025 spot)": 25_000,       # Q1-25 two-stroke spot ~$17k; 1-yr TC ~$30-50k
           "base (mid-cycle)": 75_000,      # Flex LNG TCE 2024-25 ~$72-75k; 5-10yr TC high-70s/low-80s
           "high (tight market)": 150_000}  # 2022 spot avg ~$131k; Mar-2026 spike >$250k
FUEL_SHARE_PER_DAY = 0.0008  # 0.08% of cargo burned per day (Platts 0.085% laden, Argus 0.08%)
GAS_VALUE = 10.0             # $/MMBtu value of gas burned (between US FOB ~$7 and delivered ~$12)

# One-way sea distances, nautical miles (Sabine Pass basis)
DIST_NM = {
    "Asia via Cape":   15_689,  # S&P Global (Sabine Pass -> Tokyo Bay)
    "Asia via Panama":  9_214,  # S&P Global (Sabine Pass -> Tokyo Bay)
    "Asia via strait":  9_214,  # HYPOTHETICAL: open sea gap where the canal was ~ same path, no locks
    "NW Europe":        4_900,  # approx. sea-distance tables (US Gulf -> Rotterdam/Gate); ~12 days
}

# Panama Canal (status-quo comparison only)
PANAMA_LADEN_TOLL = 300_000 + 2.05 * CAPACITY_M3   # 2023 tariff reform: $300k fixed + $2.05/m3 (2025 step)
PANAMA_BALLAST_TOLL = 0.85 * PANAMA_LADEN_TOLL     # ballast at 85% of laden (approved 2023 structure)
PANAMA_TRANSIT_DAYS = 2.0   # ~1 day each way
PANAMA_WAIT_DAYS = 2.0      # typical early-2026 unbooked wait (~2 d); rose to 11-18 d by Apr-Sep 2026

# Prices, annual averages $/MMBtu (JKM: S&P Global Platts / GIIGNL; TTF: Eni WER, IEA)
JKM = {2019: 5.49, 2020: 4.39, 2021: 18.60, 2022: 33.98, 2023: 13.78, 2024: 11.91, 2025: 12.26}
TTF = {2019: 4.50, 2020: 3.15, 2021: 15.80, 2022: 37.10, 2023: 12.80, 2024: 10.90, 2025: 11.90}

# Market sizes & demand response
ASIA_LNG_MT = 271          # 2025 Asia LNG imports (GIIGNL-based; regional definitions vary)
EUROPE_LNG_MT = 126        # 2025 Europe LNG imports
K_TOTAL = 7.0              # Mt of global LNG demand per $1/MMBtu price change:
                           #   OIES: $6/MMBtu gas -> +60 bcm (~44 Mt) LNG demand => ~7 Mt per $
                           #   2026 Hormuz shock: ~85 Mt/yr supply loss <-> ~$8-17 price rise => 5-11 Mt per $
US_EXPORTS_2025_MT = 111   # LSEG / EIA (15.1 Bcf/d)
US_CAPACITY_BCFD = 15.4    # ~2025 nameplate
US_EXPORTS_2025_BCFD = 15.1
US_TO_ASIA_2024_MT = 31.6  # Kpler (EIA: 4.0 Bcf/d, 33% of exports)
SHARE_VIA_CAPE_2024 = 0.94 # SynMax
GLOBAL_FLEET = 804         # IGU World LNG Report 2026 (end-2025 active fleet)

# US delivered-cost check (contract formula 115% x HH + fee)
HH_2025 = 3.52             # EIA
LIQ_FEE = 2.80             # new-SPA fees ~$2.65-2.95 (Poten, 2025)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
NM_PER_DAY = SPEED_KN * 24
LOADED_MMBTU = CAPACITY_M3 * FILL * T_PER_M3 * MMBTU_PER_T
CARGO_MT = CAPACITY_M3 * FILL * T_PER_M3 / 1e6
FUEL_PER_DAY = FUEL_SHARE_PER_DAY * LOADED_MMBTU * GAS_VALUE


def round_trip_days(route):
    days = 2 * DIST_NM[route] / NM_PER_DAY + PORT_DAYS
    if route == "Asia via Panama":
        days += PANAMA_TRANSIT_DAYS + PANAMA_WAIT_DAYS
    return days


def freight(route, charter):
    """$/MMBtu delivered = (days x daily cost + port costs + tolls) / delivered MMBtu"""
    cost = round_trip_days(route) * (charter + FUEL_PER_DAY) + PORT_COST
    if route == "Asia via Panama":
        cost += PANAMA_LADEN_TOLL + PANAMA_BALLAST_TOLL
    return cost / DELIVERED_MMBTU


def clip(x, lo, hi):
    return max(lo, min(hi, x))


def model(charter):
    f = {r: freight(r, charter) for r in DIST_NM}
    d_old = f["Asia via Cape"] - f["NW Europe"]      # today's threshold (Cape is the route in use)
    d_pan = f["Asia via Panama"] - f["NW Europe"]    # threshold if Panama were usable
    d_new = f["Asia via strait"] - f["NW Europe"]    # hypothetical threshold
    dF = d_old - d_new
    comp = {y: clip(JKM[y] - TTF[y] - d_new, 0, dF) for y in JKM}
    return f, d_old, d_pan, d_new, dF, comp


def line(label, value, unit=""):
    print(f"  {label:<62} {value:>10} {unit}")


# ---------------------------------------------------------------------------
# RUN
# ---------------------------------------------------------------------------
def main():
    base = CHARTER["base (mid-cycle)"]
    f, d_old, d_pan, d_new, dF, comp = model(base)

    print("=" * 84)
    print("STEP 1  FREIGHT (base case: modern 174k m3 two-stroke, 17 kn, mid-cycle charter)")
    print("=" * 84)
    line("Speed: 17 kn x 24 h", f"{NM_PER_DAY:,.0f}", "nm/day")
    line("Cargo loaded: 174,000 m3 x 98.5% x 0.45 t/m3 x 52 MMBtu/t", f"{LOADED_MMBTU/1e6:.2f}", "m MMBtu")
    line("Cargo delivered (after boil-off/heel)", f"{DELIVERED_MMBTU/1e6:.2f}", "m MMBtu")
    line("Fuel: 0.08%/day x 4.01m MMBtu x $10", f"${FUEL_PER_DAY:,.0f}", "/day")
    line("Charter (mid-cycle)", f"${base:,.0f}", "/day")
    daily = base + FUEL_PER_DAY
    line("All-in daily cost", f"${daily:,.0f}", "/day")
    line("Cost of one extra voyage day per MMBtu = daily / 3.9m", f"${daily/DELIVERED_MMBTU:.4f}", "/MMBtu/day")
    print()
    print(f"  {'Route (round trip)':<22}{'one-way nm':>11}{'days':>8}{'time+fuel $m':>14}{'port+toll $m':>14}{'$/MMBtu':>10}")
    for r in DIST_NM:
        days = round_trip_days(r)
        fixed = PORT_COST + (PANAMA_LADEN_TOLL + PANAMA_BALLAST_TOLL if r == "Asia via Panama" else 0)
        print(f"  {r:<22}{DIST_NM[r]:>11,}{days:>8.1f}{days*daily/1e6:>14.2f}{fixed/1e6:>14.2f}{f[r]:>10.2f}")
    print()
    line("Panama tolls: laden $300k + $2.05 x 174k m3", f"${PANAMA_LADEN_TOLL:,.0f}")
    line("            + ballast at 85% of laden", f"${PANAMA_BALLAST_TOLL:,.0f}")
    line("            = round-trip toll / 3.9m MMBtu", f"${(PANAMA_LADEN_TOLL+PANAMA_BALLAST_TOLL)/DELIVERED_MMBTU:.2f}", "/MMBtu")
    one_way_saving = (DIST_NM["Asia via Cape"] - DIST_NM["Asia via strait"]) / NM_PER_DAY
    line("Voyage time saved one-way, Cape -> strait", f"{one_way_saving:.1f}", "days")
    line("  one-way voyage: Cape -> strait", f"{DIST_NM['Asia via Cape']/NM_PER_DAY:.1f} -> {DIST_NM['Asia via strait']/NM_PER_DAY:.1f}", "days")
    line("Freight saving vs Cape (today's route)", f"${f['Asia via Cape']-f['Asia via strait']:.2f}", "/MMBtu")
    line("Freight saving vs a working Panama (tolls + 4 days)", f"${f['Asia via Panama']-f['Asia via strait']:.2f}", "/MMBtu")
    wait_eq = (f["Asia via Cape"] - f["Asia via Panama"]) / (daily / DELIVERED_MMBTU) + PANAMA_WAIT_DAYS
    line("Panama queue (days) at which Panama costs as much as the Cape", f"{wait_eq:.0f}", "days")

    print()
    print("=" * 84)
    print("STEP 2  ARBITRAGE THRESHOLD  (US cargo -> Asia only if JKM - TTF > F_Asia - F_Europe)")
    print("=" * 84)
    line("Old threshold (via Cape):   F_Cape - F_Europe", f"${d_old:.2f}", "/MMBtu")
    line("Panama threshold (if usable): F_Panama - F_Europe", f"${d_pan:.2f}", "/MMBtu")
    line("New threshold (via strait): F_strait - F_Europe", f"${d_new:.2f}", "/MMBtu")
    line("Threshold falls by (= freight saving, dF)", f"${dF:.2f}", "/MMBtu")

    print()
    print("=" * 84)
    print("STEP 3  DOES THE LOWER THRESHOLD BIND?  compression = clip(spread - new threshold, 0, dF)")
    print("=" * 84)
    print(f"  {'Year':<6}{'JKM':>8}{'TTF':>8}{'JKM-TTF':>10}{'> new thr?':>12}{'compression':>13}")
    for y in JKM:
        s = JKM[y] - TTF[y]
        print(f"  {y:<6}{JKM[y]:>8.2f}{TTF[y]:>8.2f}{s:>+10.2f}{'yes' if s > d_new else 'no':>12}{comp[y]:>13.2f}")
    avg_s = sum(JKM[y] - TTF[y] for y in JKM) / len(JKM)
    avg_c = sum(comp.values()) / len(comp)
    n_bind = sum(1 for v in comp.values() if v > 0)
    line("Average JKM-TTF 2019-25", f"${avg_s:+.2f}", "/MMBtu")
    line(f"Years the new threshold binds", f"{n_bind} of {len(comp)}")
    line("Average spread compression 2019-25", f"${avg_c:.2f}", "/MMBtu")
    line("Max compression in a tight-Asia year (= dF)", f"${dF:.2f}", "/MMBtu")

    print()
    print("  Sensitivity to charter rate (freight level):")
    print(f"  {'case':<22}{'charter':>10}{'old thr':>9}{'new thr':>9}{'dF':>7}{'avg comp':>10}{'binds':>7}")
    sens = {}
    for name, ch in CHARTER.items():
        _, o, _, n, d, c = model(ch)
        a = sum(c.values()) / len(c)
        sens[name] = (o, n, d, a)
        print(f"  {name:<22}{ch:>10,}{o:>9.2f}{n:>9.2f}{d:>7.2f}{a:>10.2f}{sum(1 for v in c.values() if v>0):>5}/7")

    print()
    print("=" * 84)
    print("STEP 4  PRICE SPLIT  (supply fixed -> volume-weighted LNG price unchanged)")
    print("=" * 84)
    w_a = ASIA_LNG_MT / (ASIA_LNG_MT + EUROPE_LNG_MT)
    w_e = 1 - w_a
    line("Asia share of Asia+Europe LNG imports: 271 / 397", f"{w_a:.0%}")
    line("TTF change  = +C x Asia share", f"+${w_a*avg_c:.2f}", "/MMBtu (avg)")
    line("JKM change  = -C x Europe share", f"-${w_e*avg_c:.2f}", "/MMBtu (avg)")
    line("  tight-Asia year (C = dF): TTF", f"+${w_a*dF:.2f}", "/MMBtu")
    line("  tight-Asia year (C = dF): JKM", f"-${w_e*dF:.2f}", "/MMBtu")
    line("As % of 2023-25 avg price (~$12.1): TTF / JKM", f"+{w_a*avg_c/12.1:.1%} / -{w_e*avg_c/12.1:.1%}")
    line("US FOB netback change (= TTF change, Europe is US's marginal outlet)", f"+${w_a*avg_c:.2f}", "/MMBtu")

    print()
    print("=" * 84)
    print("STEP 5  VOLUMES & MIX")
    print("=" * 84)
    line("US utilisation 2025: 15.1 / 15.4 Bcf/d", f"{US_EXPORTS_2025_BCFD/US_CAPACITY_BCFD:.0%}")
    line("=> short-run change in total US export volume", "~0", "(capacity-bound)")
    k_a, k_e = K_TOTAL * w_a, K_TOTAL * w_e
    line("Demand response: Asia k_A = 7 x 68%", f"{k_a:.1f}", "Mt per $1")
    line("Demand response: Europe k_E = 7 x 32%", f"{k_e:.1f}", "Mt per $1")
    per_dollar = k_a * k_e / (k_a + k_e)
    line("Mt moved Europe->Asia per $1 of compression = kA*kE/(kA+kE)", f"{per_dollar:.2f}", "Mt")
    dq_avg, dq_max = per_dollar * avg_c, per_dollar * dF
    line("Volume shifted to Asia, average year (C avg)", f"{dq_avg:.1f}", f"Mt (~{dq_avg/CARGO_MT:.0f} cargoes)")
    line("Volume shifted to Asia, tight-Asia year (C = dF)", f"{dq_max:.1f}", f"Mt (~{dq_max/CARGO_MT:.0f} cargoes)")
    line("  as share of 2025 US exports (111 Mt)", f"{dq_avg/US_EXPORTS_2025_MT:.1%} - {dq_max/US_EXPORTS_2025_MT:.1%}")
    line("  if long-run demand response were 3x larger", f"{3*dq_avg:.1f} - {3*dq_max:.1f}", "Mt")
    print()
    cape_cargoes = US_TO_ASIA_2024_MT * SHARE_VIA_CAPE_2024 / CARGO_MT
    rt_saved = round_trip_days("Asia via Cape") - round_trip_days("Asia via strait")
    ships = cape_cargoes * rt_saved / 365
    line("Cargo size: 171,390 m3 x 0.45 t", f"{CARGO_MT*1e3:.1f}", "kt")
    line("US->Asia cargoes via Cape (2024): 31.6 Mt x 94% / 0.0771", f"{cape_cargoes:.0f}", "cargoes/yr")
    line("Round-trip days saved per cargo", f"{rt_saved:.1f}", "days")
    line("Ship-years freed = cargoes x days / 365", f"{ships:.0f}", f"ships ({ships/GLOBAL_FLEET:.1%} of {GLOBAL_FLEET}-ship fleet)")
    line("Annual freight bill saved = cargoes x days x daily cost", f"${cape_cargoes*rt_saved*daily/1e9:.2f}", "bn/yr")
    print()
    fob = 1.15 * HH_2025 + LIQ_FEE
    des_old, des_new = fob + f["Asia via Cape"], fob + f["Asia via strait"]
    line("US FOB cost: 1.15 x $3.52 HH + $2.80 fee", f"${fob:.2f}", "/MMBtu")
    line("US delivered cost to Japan: via Cape -> via strait", f"${des_old:.2f} -> ${des_new:.2f}", f"({des_new/des_old-1:+.0%})")

    make_chart(d_old, d_pan, d_new, dF, comp)
    return dict(f=f, d_old=d_old, d_new=d_new, dF=dF, comp=comp, avg_c=avg_c, sens=sens)


def make_chart(d_old, d_pan, d_new, dF, comp):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e2dc"
    KEEP, CUT = "#2a78d6", "#eb6834"   # reference palette slots 1-2

    years = list(JKM)
    spread = [JKM[y] - TTF[y] for y in years]
    cut = [comp[y] for y in years]
    keep = [s - c for s, c in zip(spread, cut)]

    fig, ax = plt.subplots(figsize=(6.4, 2.3), dpi=220)
    fig.patch.set_facecolor("#fcfcfb"); ax.set_facecolor("#fcfcfb")
    x = range(len(years))
    ax.bar(x, keep, width=0.55, color=KEEP, label="Spread that remains", zorder=2)
    ax.bar(x, cut, width=0.55, bottom=keep, color=CUT, label="Removed by toll-free strait",
           zorder=2, edgecolor="#fcfcfb", linewidth=1.5)
    x_end = len(years) - 0.55
    ax.hlines(d_old, -0.6, x_end, color=INK2, lw=1.3, ls=(0, (4, 3)), zorder=3)
    ax.hlines(d_new, -0.6, x_end, color=INK, lw=1.3, zorder=3)
    ax.axhline(0, color=INK2, lw=0.8, zorder=1)
    ax.text(x_end + 0.08, d_old, f"Cape ${d_old:.2f}", ha="left", va="center",
            fontsize=7.5, color=INK2)
    ax.text(x_end + 0.08, d_new, f"Strait ${d_new:.2f}", ha="left", va="center",
            fontsize=7.5, color=INK)
    i22 = years.index(2022)
    ax.text(i22 - 0.4, -2.5, "2022: TTF > JKM (Europe pulls)\n→ no effect",
            ha="right", va="center", fontsize=7.5, color=INK2)
    ax.set_xlim(-0.6, len(years) + 0.45)
    ax.set_xticks(list(x)); ax.set_xticklabels(years, fontsize=7.5, color=INK2)
    ax.tick_params(axis="y", labelsize=7.5, colors=INK2)
    ax.set_ylabel("JKM − TTF, $/MMBtu", fontsize=7.5, color=INK2)
    ax.set_ylim(-3.5, 3.2)
    ax.grid(axis="y", color=GRID, lw=0.6, zorder=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.legend(loc="lower right", fontsize=7.5, frameon=False)
    ax.set_title("Annual JKM−TTF spread vs US→Asia arbitrage threshold (base case)", fontsize=8.5,
                 color=INK, loc="left")
    fig.tight_layout()
    OUT_DIR.mkdir(exist_ok=True)
    fig.savefig(OUT_DIR / "spread_vs_thresholds.png", facecolor=fig.get_facecolor())


if __name__ == "__main__":
    main()
