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

# Assumptions for a hypothetical university endowment.
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
        monthly = returns.loc[row["period_start"]:row["period_end"], row["ticker"]]
        if row["metric"] == "cagr":
            vendor_return = compound_return(monthly)
        else:
            vendor_return = (1 + monthly).prod() - 1
        observed.append(vendor_return)
    checks["vendor_return"] = observed
    checks["difference_bps"] = 10_000 * (checks["vendor_return"] - checks["sponsor_return"])
    checks["review_needed"] = checks["difference_bps"].abs() > 5
    return checks


def liquidity_stress(call_fraction=.80, initial_nav=INITIAL_NAV,
                     annual_spending=ANNUAL_SPENDING, initial_commitments=UNFUNDED_COMMITMENTS,
                     reserve=MINIMUM_CASH):
    """Apply one market shock, then follow cash and investments for 12 months."""
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
        uncalled_commitments = remaining_commitments - unpaid_calls
        new_calls = min(scheduled_monthly_call, uncalled_commitments)
        spending_due = unpaid_spending + monthly_spending
        calls_due = unpaid_calls + new_calls
        cash_needed = max(0, spending_due + calls_due + reserve - cash)

        # 2. Sell bonds first. There is no bond-sale cost in this case.
        bond_sales = min(bonds, cash_needed)
        bonds -= bond_sales
        cash += bond_sales
        # 3. Sell equity for any remaining cash need. A $100 sale brings in $95.
        remaining_cash_needed = max(0, cash_needed - bond_sales)
        equity_to_sell = remaining_cash_needed / (1 - EQUITY_SALE_HAIRCUT)
        equity_sales = min(equity, equity_to_sell)
        sale_costs = equity_sales * EQUITY_SALE_HAIRCUT
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
        rows.append({"month": month, "beginning_nav": previous_nav, "valuation_loss": valuation_loss,
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
    for fraction, scenario in monthly.groupby("call_fraction"):
        last = scenario.iloc[-1]
        rows.append({"call_fraction": fraction, "total_calls_paid": scenario.calls_paid.sum(),
                     "total_spending_paid": scenario.spending_paid.sum(),
                     "total_bond_sales": scenario.bond_sales.sum(), "total_equity_sales": scenario.equity_sales.sum(),
                     "total_sale_costs": scenario.sale_costs.sum(), "ending_cash": last.cash,
                     "ending_private_nav": last.private_nav, "ending_nav": last.total_nav,
                     "private_weight": last.private_nav / last.total_nav,
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
           xlabel="Monthly total returns; starting value at December 2014")
    ax.yaxis.set_major_formatter(StrMethodFormatter("${x:,.0f}"))
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=.2)
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
           xlabel="Month-end observations")
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.legend(frameon=False, loc="lower left")
    ax.grid(axis="y", alpha=.2)
    fig.savefig(folder / "drawdowns.png", dpi=170)
    plt.close(fig)

    # Chart 3: compare the two capital-call assumptions side by side.
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.2), layout="constrained", sharey=True)
    for position, fraction in enumerate(CALL_FRACTIONS):
        ax = axes[position]
        scenario = monthly[monthly["call_fraction"] == fraction]
        bond_sales_millions = scenario["bond_sales"] / 1_000_000
        equity_sales_millions = scenario["equity_sales"] / 1_000_000
        ax.bar(scenario["month"], bond_sales_millions, color=COLORS["SPY"], label="Bonds")
        ax.bar(scenario["month"], equity_sales_millions, bottom=bond_sales_millions,
               color=COLORS["SEQUX"], label="Public equity")
        ax.set(title=f"{fraction:.0%} of commitments called", xlabel="Month", xticks=range(1, 13))
        ax.grid(axis="y", alpha=.2)
    axes[0].set_ylabel("Gross assets sold ($ millions)")
    axes[0].legend(frameon=False)
    fig.suptitle("Monthly asset sales under stress")
    fig.supxlabel("Hypothetical case; equity sales have a 5% cost", fontsize=9)
    fig.savefig(folder / "monthly_asset_sales.png", dpi=170)
    plt.close(fig)


def millions(amount):
    return f"${amount / 1_000_000:,.1f} million"


def write_findings(performance, allocations, regimes, summary, checks):
    """Write the investment memo using the calculated results."""
    base = summary.iloc[0]
    sensitivity = summary.iloc[1]
    sales = base.total_bond_sales + base.total_equity_sales
    extra_sales = sensitivity.total_bond_sales + sensitivity.total_equity_sales - sales
    table = "| Investment | CAGR | Volatility | Max drawdown | Correlation with SPY |\n|---|---:|---:|---:|---:|\n"
    for ticker, row in performance.iterrows():
        table += f"| {ticker} | {row.cagr:.2%} | {row.volatility:.2%} | {row.max_drawdown:.2%} | {row.correlation_with_spy:.2f} |\n"
    impacts = allocations[allocations.weight == .05].set_index("manager")
    returns_2022 = regimes[regimes.regime == "2022"].set_index("ticker")
    flagged_checks = checks[checks["review_needed"]]
    discrepancies = []
    for row in flagged_checks.itertuples():
        description = f"{row.ticker}, {row.period_start} to {row.period_end}: {row.difference_bps:+.2f} bp"
        discrepancies.append(description)
    discrepancy_text = "; ".join(discrepancies)
    memo = f"""# Should the endowment hire an active equity manager?

**Research window:** January 2015–December 2024. **Source retrieval:** October 16, 2026.
**Case:** A hypothetical university endowment with {millions(INITIAL_NAV)} in assets.

## Recommendation

Keep the passive allocation for now. Neither manager's results in this period provide a strong enough reason to replace SPY. A hire would need more evidence about the investment process, portfolio fit and terms. This study compares 0%, 2.5% and 5% allocations to Sequoia or Dodge & Cox, funded by reducing SPY.

## What the returns show

{table}
Both funds earned less than SPY, with more volatility and deeper month-end losses. The main counterargument is benchmark fit: a value-oriented manager can behave differently from the US large-cap market. In 2022 DODGX returned {returns_2022.loc['DODGX','cumulative_return']:.2%}, compared with {returns_2022.loc['SPY','cumulative_return']:.2%} for SPY. That warrants a closer style comparison; one favorable year does not settle the decision. February–March 2020 results are also in `results/regimes.csv`.

## What changes at 5%?

The case starts with 20% US equity, 10% international equity, 15% bonds, 15% hedge funds, 35% private markets and 5% cash. A 2.5% manager position is {millions(INITIAL_NAV*.025)}, replacing 12.5% of US equity. At 5%, those figures are {millions(INITIAL_NAV*.05)} and 25%.

At 5%, the arithmetic annualized contribution from replacing SPY is {100*impacts.loc['SEQUX','arithmetic_annual_contribution']:.2f} percentage points for SEQUX and {100*impacts.loc['DODGX','arithmetic_annual_contribution']:.2f} for DODGX. The calculation is 12 × average monthly weight × (manager return − SPY return). This is not a compound return for the whole endowment. SPY measures what the endowment gives up, and may not be the best benchmark for evaluating a manager's style. No private-market or hedge-fund return history is modeled.

## Cash requirements under stress

Assume immediate losses of 50% in public equity, 10% in bonds, 25% in hedge funds and 40% in private markets. Annual spending is {millions(ANNUAL_SPENDING)}; 80% of commitments are called evenly over 12 months. There are no distributions or later returns. Bonds are sold first, then equities with a 5% haircut, targeting {millions(MINIMUM_CASH)} of cash. Hedge funds and private assets cannot be sold, and there is no borrowing. All public equity has the same assumed loss, so this is a funding test rather than a manager forecast.

The 80% call case needs {millions(sales)} of gross sales: {millions(base.total_bond_sales)} in bonds and {millions(base.total_equity_sales)} in equities. Costs total {millions(base.total_sale_costs)}. Ending cash is {millions(base.ending_cash)}, unpaid obligations are {millions(base.unpaid_obligations)}, and the largest reserve shortfall is {millions(base.max_reserve_shortfall)}. Ending NAV is {millions(base.ending_nav)}, with {base.private_weight:.2%} in private assets.

Calling 100% requires another {millions(extra_sales)} of sales. Costs rise to {millions(sensitivity.total_sale_costs)}; ending cash is {millions(sensitivity.ending_cash)}. Unpaid obligations are {millions(sensitivity.unpaid_obligations)} and the largest reserve shortfall is {millions(sensitivity.max_reserve_shortfall)}. Calls move money from cash into private investments; spending and sale costs reduce NAV. Paying the bills and keeping enough liquid assets afterward are separate concerns.

## What is still missing?

The unresolved vendor-minus-sponsor differences are {discrepancy_text}. There is no verified SPY sponsor checkpoint. This selected sample of surviving funds uses data retrieved in 2026, with hindsight, share-class and team changes to consider. Month-end observations miss intramonth losses.

Before reconsidering a hire, compare suitable low-cost style alternatives and investigate the current team, process, eligible vehicle, fees, capacity, operations and full holdings. Evidence of a repeatable process and a useful portfolio role could change the recommendation. Those checks are outside this project.
"""
    (ROOT / "IC_MEMO.md").write_text(memo, encoding="utf-8")


def main():
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

    # Run the same cash model twice, changing only the fraction of calls.
    scenarios = []
    for fraction in CALL_FRACTIONS:
        scenario = liquidity_stress(fraction)
        scenario["call_fraction"] = fraction
        scenarios.append(scenario)
    monthly = pd.concat(scenarios, ignore_index=True)
    summary = stress_summary(monthly)
    checks = sponsor_comparison(returns)

    performance.to_csv(results / "performance.csv", float_format="%.12f")
    for name, table in [("allocations", allocations), ("regimes", regimes),
                        ("liquidity_monthly", monthly), ("liquidity_summary", summary),
                        ("sponsor_comparison", checks)]:
        table.to_csv(results / f"{name}.csv", index=False, float_format="%.12f")
    save_charts(returns, monthly, results)
    write_findings(performance, allocations, regimes, summary, checks)
    print("Finished: 120 months, 3 investments, 6 allocation rows and 2 cash scenarios.")
    print(performance.round(4).to_string())
    print("Charts and tables are in results/. Findings are in IC_MEMO.md.")


if __name__ == "__main__":
    main()
