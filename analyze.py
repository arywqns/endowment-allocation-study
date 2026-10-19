r"""Compare two equity funds and work through an endowment cash budget.

Run: python analyze.py
All returns are monthly decimals; all money amounts are US dollars.
"""
from pathlib import Path
import hashlib
import json
import math
import os

import pandas as pd

ROOT = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))
import matplotlib
matplotlib.use("Agg")  # Save charts without needing a GUI or internet connection.
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter, StrMethodFormatter

# Deliberately severe hypothetical case; rationale is in README.md.
# Spending is fixed at 5% of beginning NAV, not a changing payout formula.
INITIAL_NAV = 5_000_000_000
ANNUAL_SPENDING = 250_000_000
UNFUNDED_COMMITMENTS = 1_000_000_000
MINIMUM_CASH = 125_000_000
POLICY = {"us_equity": .20, "international_equity": .10, "bonds": .15,
          "hedge_funds": .15, "private_markets": .35, "cash": .05}
LOSSES = {"equity": .50, "bonds": .10, "hedge_funds": .25, "private_markets": .40}
EQUITY_SALE_HAIRCUT = .05
SIZES = [0, .025, .05]
CALL_FRACTIONS = [.80, 1.00]
TICKERS = ["SEQUX", "DODGX", "SPY"]
COLORS = {"SEQUX": "#B45535", "DODGX": "#187668", "SPY": "#1D4168"}


def verify_sources(root=ROOT):
    """Check the two input tables and any locally cached source documents."""
    sources = json.loads((root / "data/sources.json").read_text(encoding="utf-8"))
    checked = 0
    for source in sources:
        path = root / source["path"]
        # Original downloads are kept locally; the public copy uses the tables.
        if not path.exists() and not source.get("required_for_analysis", True):
            continue
        if "sha256" not in source:
            continue  # Citation only; no assertion of archived byte provenance.
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != source["sha256"]:
            raise ValueError(f"Cached source changed: {source['path']}")
        checked += 1
    return checked


def validate_returns(returns):
    """Check the dates, missing values and return units before calculating."""
    expected = pd.date_range("2015-01-31", "2024-12-31", freq="ME")
    if list(returns.columns) != TICKERS or not returns.index.equals(expected):
        raise ValueError("Expected SEQUX, DODGX, SPY and all 120 months, in order.")
    for ticker in TICKERS:
        for monthly_return in returns[ticker]:
            if not math.isfinite(monthly_return):
                raise ValueError(f"Missing or invalid return for {ticker}.")
            # This bound checks units in this dataset; it is not a market rule.
            if monthly_return <= -1 or monthly_return >= 1:
                raise ValueError("Use decimals: a 5% return should be 0.05.")


def load_returns(root=ROOT):
    verify_sources(root)
    returns = pd.read_csv(root / "data/monthly_returns.csv", parse_dates=["date"], index_col="date")
    validate_returns(returns)
    return returns


def validate_assumptions():
    if set(POLICY) != {"us_equity", "international_equity", "bonds", "hedge_funds", "private_markets", "cash"}:
        raise ValueError("Unexpected policy asset buckets.")
    if any(not math.isfinite(x) or x < 0 for x in POLICY.values()) or not math.isclose(sum(POLICY.values()), 1):
        raise ValueError("Policy weights must be finite, nonnegative and sum to one.")
    if set(LOSSES) != {"equity", "bonds", "hedge_funds", "private_markets"} or any(not math.isfinite(x) or not 0 <= x <= 1 for x in LOSSES.values()):
        raise ValueError("Losses must be fractions between zero and one.")
    if not CALL_FRACTIONS or len(set(CALL_FRACTIONS)) != len(CALL_FRACTIONS) or any(not math.isfinite(x) or not 0 <= x <= 1 for x in CALL_FRACTIONS):
        raise ValueError("Call scenarios must be distinct fractions between zero and one.")
    if not SIZES or any(not math.isfinite(x) or not 0 <= x <= POLICY["us_equity"] for x in SIZES):
        raise ValueError("Manager allocations must fit within the funding sleeve.")
    if not math.isfinite(EQUITY_SALE_HAIRCUT) or not 0 <= EQUITY_SALE_HAIRCUT < 1:
        raise ValueError("Equity sale deduction must be below 100%.")


def compound_return(monthly_returns):
    """Find the constant annual rate that gives the same total growth."""
    total_growth = (1 + monthly_returns).prod()
    years = len(monthly_returns) / 12
    return total_growth ** (1 / years) - 1


def drawdown(monthly_returns):
    """Measure the fall from the previous high, starting with an investment of 1."""
    wealth = (1 + monthly_returns).cumprod()
    previous_peak = wealth.cummax().clip(lower=1)
    return wealth / previous_peak - 1


def performance_table(returns):
    rows = []
    for ticker in TICKERS:
        monthly = returns[ticker]
        annual_return = compound_return(monthly)
        annual_volatility = monthly.std(ddof=1) * math.sqrt(12)
        worst_drawdown = drawdown(monthly).min()
        correlation = monthly.corr(returns["SPY"])
        rows.append({
            "ticker": ticker,
            "cagr": annual_return,
            "volatility": annual_volatility,
            "max_drawdown": worst_drawdown,
            "correlation_with_spy": correlation,
        })
    return pd.DataFrame(rows).set_index("ticker")


def allocation_table(returns):
    rows = []
    for manager in ["SEQUX", "DODGX"]:
        for weight in SIZES:
            return_difference = returns[manager] - returns["SPY"]
            monthly_contribution = weight * return_difference
            annual_contribution = 12 * monthly_contribution.mean()
            rows.append({
                "manager": manager,
                "weight": weight,
                "dollar_allocation": INITIAL_NAV * weight,
                "us_equity_replaced": weight / POLICY["us_equity"],
                "arithmetic_annual_contribution": annual_contribution,
            })
    return pd.DataFrame(rows)


def sponsor_comparison(returns):
    checks = pd.read_csv(ROOT / "data/sponsor_returns.csv")
    observed = []
    for row in checks.to_dict("records"):
        if row["ticker"] not in TICKERS or row["metric"] not in {"cagr", "cumulative_return"}:
            raise ValueError("Invalid sponsor ticker or return metric.")
        start, end = pd.Timestamp(row["period_start"]), pd.Timestamp(row["period_end"])
        monthly = returns.loc[start:end, row["ticker"]]
        expected = pd.period_range(start, end, freq="M")
        if monthly.empty or not monthly.index.to_period("M").equals(expected):
            raise ValueError("Sponsor checkpoint must cover a complete period within the sample.")
        if not math.isfinite(row["sponsor_return"]) or row["sponsor_return"] <= -1:
            raise ValueError("Invalid sponsor return.")
        if row["metric"] == "cagr":
            vendor_return = compound_return(monthly)
        else:
            vendor_return = (1 + monthly).prod() - 1
        observed.append(vendor_return)
    checks["vendor_return"] = observed
    checks["difference_bps"] = 10_000 * (checks["vendor_return"] - checks["sponsor_return"])
    checks["review_needed"] = checks["difference_bps"].abs() > 5
    return checks


def liquidity_stress(call_fraction=None, initial_nav=None,
                     annual_spending=None, initial_commitments=None,
                     reserve=None, equity_haircut=None, call_timing="even"):
    # Resolve defaults at call time, so changing case assumptions changes all outputs.
    validate_assumptions()
    call_fraction = CALL_FRACTIONS[0] if call_fraction is None else call_fraction
    initial_nav = INITIAL_NAV if initial_nav is None else initial_nav
    annual_spending = ANNUAL_SPENDING if annual_spending is None else annual_spending
    initial_commitments = UNFUNDED_COMMITMENTS if initial_commitments is None else initial_commitments
    reserve = MINIMUM_CASH if reserve is None else reserve
    equity_haircut = EQUITY_SALE_HAIRCUT if equity_haircut is None else equity_haircut
    if not math.isfinite(equity_haircut) or not 0 <= equity_haircut < 1:
        raise ValueError("Equity sale deduction must be finite and below 100%.")
    if call_timing not in {"even", "front_loaded"}:
        raise ValueError("Call timing must be even or front_loaded.")
    if not 0 <= call_fraction <= 1:
        raise ValueError("The fraction of commitments called must be between 0 and 1.")
    for amount in [initial_nav, annual_spending, initial_commitments, reserve]:
        if not math.isfinite(amount) or amount < 0:
            raise ValueError("Dollar assumptions must be finite and nonnegative.")

    # First mark down the investments. Cash is unchanged by the market shock.
    cash = initial_nav * POLICY["cash"]
    bonds = initial_nav * POLICY["bonds"] * (1 - LOSSES["bonds"])
    equity = initial_nav * (POLICY["us_equity"] + POLICY["international_equity"]) * (1 - LOSSES["equity"])
    hedge_funds = initial_nav * POLICY["hedge_funds"] * (1 - LOSSES["hedge_funds"])
    private_nav = initial_nav * POLICY["private_markets"] * (1 - LOSSES["private_markets"])
    initial_loss = initial_nav - (cash + bonds + equity + hedge_funds + private_nav)
    remaining_commitments = initial_commitments
    unpaid_spending = 0.0
    unpaid_calls = 0.0
    previous_nav = initial_nav
    monthly_spending = annual_spending / 12
    scheduled_monthly_call = initial_commitments * call_fraction / 12
    rows = []
    for month in range(1, 13):
        # 1. Add this month's bills to anything still unpaid from last month.
        uncalled_commitments = max(0, remaining_commitments - unpaid_calls)
        scheduled = scheduled_monthly_call if call_timing == "even" else (initial_commitments * call_fraction if month == 1 else 0)
        new_calls = min(scheduled, uncalled_commitments)
        spending_due = unpaid_spending + monthly_spending
        calls_due = unpaid_calls + new_calls
        cash_needed = max(0, spending_due + calls_due + reserve - cash)

        # 2. Sell bonds first. There is no bond-sale cost in this case.
        bond_sales = min(bonds, cash_needed)
        bonds -= bond_sales
        cash += bond_sales
        # 3. Sell equity for any remaining cash need. A $100 sale brings in $95.
        remaining_cash_needed = max(0, cash_needed - bond_sales)
        equity_to_sell = remaining_cash_needed / (1 - equity_haircut)
        equity_sales = min(equity, equity_to_sell)
        sale_costs = equity_sales * equity_haircut
        equity -= equity_sales
        cash += equity_sales - sale_costs

        # 4. Pay spending, then calls. The reserve is a target, not a borrowing line.
        spending_paid = min(cash, spending_due)
        cash -= spending_paid
        calls_paid = min(cash, calls_due)
        cash -= calls_paid
        private_nav += calls_paid  # Calls are transfers into private investments.
        remaining_commitments -= calls_paid
        unpaid_spending = max(0, spending_due - spending_paid)
        unpaid_calls = max(0, calls_due - calls_paid)

        # 5. Check the accounts. Calls are transfers; spending and costs reduce NAV.
        # Unpaid spending is deducted as a liability when it becomes due.
        total_nav = cash + bonds + equity + hedge_funds + private_nav - unpaid_spending
        valuation_loss = initial_loss if month == 1 else 0
        expected_nav = previous_nav - valuation_loss - monthly_spending - sale_costs
        rows.append({"equity_sale_haircut": equity_haircut, "call_timing": call_timing, "cash_target": reserve,
                     "month": month, "beginning_nav": previous_nav, "valuation_loss": valuation_loss,
                     "spending_due": spending_due, "new_calls": new_calls,
                     "spending_paid": spending_paid, "calls_paid": calls_paid,
                     "bond_sales": bond_sales, "equity_sales": equity_sales, "sale_costs": sale_costs,
                     "cash": cash, "bonds": bonds, "equity": equity, "hedge_funds": hedge_funds,
                     "private_nav": private_nav, "remaining_commitments": remaining_commitments,
                     "unpaid_spending": unpaid_spending, "unpaid_calls": unpaid_calls,
                     "unpaid_obligations": unpaid_spending + unpaid_calls, "total_nav": total_nav,
                     "reserve_shortfall": max(0, reserve - cash), "nav_error": total_nav - expected_nav})
        previous_nav = total_nav
    result = pd.DataFrame(rows)
    if result.nav_error.abs().max() > .01 or result.cash.min() < -.01:
        raise ArithmeticError("Cash or NAV accounting does not reconcile.")
    return result


def stress_summary(monthly):
    rows = []
    for fraction, scenario in monthly.groupby("call_fraction", sort=False):
        last = scenario.iloc[-1]
        rows.append({"call_fraction": fraction, "total_calls_paid": scenario.calls_paid.sum(),
                     "total_spending_paid": scenario.spending_paid.sum(),
                     "total_bond_sales": scenario.bond_sales.sum(), "total_equity_sales": scenario.equity_sales.sum(),
                     "total_sale_costs": scenario.sale_costs.sum(), "ending_cash": last.cash,
                     "ending_private_nav": last.private_nav, "ending_nav": last.total_nav,
                     "private_weight": last.private_nav / last.total_nav if last.total_nav > 0 else float("nan"),
                     "ending_bonds": last.bonds, "ending_equity": last.equity,
                     "locked_weight": (last.private_nav + last.hedge_funds) / last.total_nav if last.total_nav > 0 else float("nan"),
                     "ending_realizable_liquidity": last.cash + last.bonds + last.equity * (1 - last.equity_sale_haircut),
                     "funding_failure": bool((scenario.unpaid_obligations > .01).any()),
                     "remaining_commitments": last.remaining_commitments,
                     "unpaid_obligations": last.unpaid_obligations,
                     "max_reserve_shortfall": scenario.reserve_shortfall.max()})
    return pd.DataFrame(rows)


def save_charts(returns, monthly, folder):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False})
    baseline = pd.Timestamp("2014-12-31")

    # Chart 1: start each investment at $100 before the first monthly return.
    growth = 100 * (1 + returns).cumprod()
    growth.loc[baseline] = 100
    growth = growth.sort_index()
    fig, ax = plt.subplots(figsize=(10, 5), layout="constrained")
    for ticker in TICKERS:
        ax.plot(growth.index, growth[ticker], label=ticker, color=COLORS[ticker])
    ax.set(title="Growth of $100, 2015–2024", ylabel="Investment value",
           xlabel="Month-end adjusted-price return proxy; starting value at December 2014")
    ax.yaxis.set_major_formatter(StrMethodFormatter("${x:,.0f}"))
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=.2)
    fig.supxlabel("Source: supplied Yahoo-derived monthly returns, January 2015-December 2024; sponsor discrepancies disclosed in data/README.md", fontsize=8)
    fig.savefig(folder / "growth_of_100.png", dpi=170)
    plt.close(fig)

    # Chart 2: show each fund's distance below its previous high.
    drawdowns = pd.DataFrame(index=returns.index)
    for ticker in TICKERS:
        drawdowns[ticker] = drawdown(returns[ticker])
    drawdowns.loc[baseline] = 0
    drawdowns = drawdowns.sort_index()
    fig, ax = plt.subplots(figsize=(10, 5), layout="constrained")
    for ticker in TICKERS:
        ax.plot(drawdowns.index, drawdowns[ticker], label=ticker, color=COLORS[ticker])
    ax.set(title="Drawdowns, 2015–2024", ylabel="Loss from previous high",
           xlabel="Month-end adjusted-price return proxy; intramonth losses excluded")
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.legend(frameon=False, loc="lower left")
    ax.grid(axis="y", alpha=.2)
    fig.supxlabel("Source: supplied Yahoo-derived monthly returns, January 2015-December 2024; sponsor discrepancies disclosed in data/README.md", fontsize=8)
    fig.savefig(folder / "drawdowns.png", dpi=170)
    plt.close(fig)

    # Use actual scenario values for labels and support one or several scenarios.
    fractions = list(monthly["call_fraction"].unique())
    fig, axes_grid = plt.subplots(1, len(fractions), figsize=(5.5 * len(fractions), 5.2), layout="constrained", sharey=True, squeeze=False)
    axes = axes_grid[0]
    for position, fraction in enumerate(fractions):
        ax = axes[position]
        scenario = monthly[monthly["call_fraction"] == fraction]
        bond_sales_millions = scenario["bond_sales"] / 1_000_000
        equity_sales_millions = scenario["equity_sales"] / 1_000_000
        ax.bar(scenario["month"], bond_sales_millions, color=COLORS["SPY"], label="Bonds")
        ax.bar(scenario["month"], equity_sales_millions, bottom=bond_sales_millions,
               color=COLORS["SEQUX"], label="Public equity")
        ax.set(title=f"{fraction:.0%} of commitments called", xlabel="Month", xticks=range(1, 13))
        total_sales = (scenario.bond_sales + scenario.equity_sales).sum() / 1e6
        ax.text(.03, .97, f"Total gross sales: ${total_sales:,.1f}m", transform=ax.transAxes, va="top", fontsize=9)
        ax.grid(axis="y", alpha=.2)
    axes[0].set_ylabel("Gross assets sold ($ millions)")
    axes[0].legend(frameon=False)
    fig.suptitle("Monthly asset sales under stress")
    fig.supxlabel(f"Hypothetical joint shock; even monthly calls; no distributions; {EQUITY_SALE_HAIRCUT:.0%} additional equity realization deduction", fontsize=8)
    fig.savefig(folder / "monthly_asset_sales.png", dpi=170)
    plt.close(fig)


def millions(amount):
    return f"${amount / 1_000_000:,.1f} million"


def liquidity_sensitivities():
    """Change one funding assumption at a time around the first documented case."""
    records = []
    base = CALL_FRACTIONS[0]
    cases = [(f"calls_{fraction:.0%}", fraction, MINIMUM_CASH, EQUITY_SALE_HAIRCUT, "even")
             for fraction in sorted({0, .4, *CALL_FRACTIONS})]
    cases += [("zero_reserve", base, 0, EQUITY_SALE_HAIRCUT, "even")]
    cases += [(f"deduction_{haircut:.0%}", base, MINIMUM_CASH, haircut, "even") for haircut in sorted({0, .01, EQUITY_SALE_HAIRCUT})]
    cases += [("front_loaded_calls", base, MINIMUM_CASH, EQUITY_SALE_HAIRCUT, "front_loaded")]
    for name, fraction, reserve, haircut, timing in cases:
        monthly = liquidity_stress(fraction, reserve=reserve, equity_haircut=haircut, call_timing=timing)
        monthly["call_fraction"] = fraction
        row = stress_summary(monthly).iloc[0].to_dict()
        equity_months = monthly.loc[monthly.equity_sales > .01, "month"]
        row.update({"scenario": name, "cash_target": reserve, "equity_sale_haircut": haircut,
                    "call_timing": timing, "total_gross_sales": row["total_bond_sales"] + row["total_equity_sales"],
                    "first_equity_sale_month": int(equity_months.iloc[0]) if not equity_months.empty else 0})
        records.append(row)
    return pd.DataFrame(records)


def write_findings(performance, allocations, regimes, summary, checks, sensitivities):
    from reporting import write_memo
    settings = {"initial_nav": INITIAL_NAV, "spending": ANNUAL_SPENDING,
                "commitments": UNFUNDED_COMMITMENTS, "reserve": MINIMUM_CASH,
                "policy": POLICY.copy(), "losses": LOSSES.copy(),
                "equity_haircut": EQUITY_SALE_HAIRCUT}
    benchmarks = pd.read_csv(ROOT / "data/benchmark_context.csv")
    write_memo(ROOT / "IC_MEMO.md", performance, allocations, regimes, summary,
               checks, sensitivities, settings, benchmarks)


def main():
    validate_assumptions()
    results = ROOT / "results"
    results.mkdir(exist_ok=True)

    returns = load_returns()
    performance = performance_table(returns)
    allocations = allocation_table(returns)

    # Compound the returns only within each selected period.
    periods = {"COVID selloff": ("2020-02", "2020-03"), "2022": ("2022-01", "2022-12")}
    period_results = []
    for name, dates in periods.items():
        start, end = dates
        for ticker in TICKERS:
            period_returns = returns.loc[start:end, ticker]
            cumulative_return = (1 + period_returns).prod() - 1
            period_results.append({"ticker": ticker, "regime": name,
                                   "cumulative_return": cumulative_return})
    regimes = pd.DataFrame(period_results)

    # Run each documented case, then isolate reserve, deduction and timing effects.
    scenarios = []
    for fraction in CALL_FRACTIONS:
        scenario = liquidity_stress(fraction)
        scenario["call_fraction"] = fraction
        scenarios.append(scenario)
    monthly = pd.concat(scenarios, ignore_index=True)
    summary = stress_summary(monthly)
    checks = sponsor_comparison(returns)
    sensitivities = liquidity_sensitivities()

    performance.to_csv(results / "performance.csv", float_format="%.12f")
    for name, table in [("allocations", allocations), ("regimes", regimes),
                        ("liquidity_monthly", monthly), ("liquidity_summary", summary),
                        ("sponsor_comparison", checks), ("liquidity_sensitivities", sensitivities)]:
        table.to_csv(results / f"{name}.csv", index=False, float_format="%.12f")
    save_charts(returns, monthly, results)
    write_findings(performance, allocations, regimes, summary, checks, sensitivities)
    print(f"Finished: {len(returns)} months, {len(TICKERS)} investments, {len(allocations)} allocation rows, {len(summary)} main cash scenarios and {len(sensitivities)} sensitivities.")
    print(performance.round(4).to_string())
    print("Charts and tables are in results/. Findings are in IC_MEMO.md.")


if __name__ == "__main__":
    main()
