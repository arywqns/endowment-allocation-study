"""A few checks of the financial logic. Run after: python analyze.py."""

from math import isclose
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory

import pandas as pd

from analyze import (
    allocation_table, compound_return, drawdown, liquidity_stress,
    load_returns, performance_table, validate_returns, verify_sources,
)

ROOT = Path(__file__).resolve().parent


def close(actual, expected):
    """Allow only rounding error, including for dollar amounts in billions."""
    assert isclose(float(actual), float(expected), rel_tol=1e-11, abs_tol=1e-5), (
        actual, expected
    )


def check_packaged_sources():
    """The public copy needs two input tables; archived originals are optional."""
    with TemporaryDirectory() as folder:
        package = Path(folder)
        data = package / "data"
        data.mkdir()
        for filename in ["sources.json", "monthly_returns.csv", "sponsor_returns.csv"]:
            copyfile(ROOT / "data" / filename, data / filename)
        assert verify_sources(package) == 2
        assert len(load_returns(package)) == 120

        for filename in ["monthly_returns.csv", "sponsor_returns.csv"]:
            path = data / filename
            original = path.read_bytes()
            path.write_bytes(original + b"\n")
            try:
                verify_sources(package)
            except ValueError:
                pass
            else:
                raise AssertionError(f"Changed input was accepted: {filename}")
            path.write_bytes(original)
            path.unlink()
            try:
                verify_sources(package)
            except (FileNotFoundError, ValueError):
                pass
            else:
                raise AssertionError(f"Missing input was accepted: {filename}")
            path.write_bytes(original)


def check_sponsor_comparison(returns):
    checkpoints = pd.read_csv(ROOT / "data/sponsor_returns.csv")
    saved = pd.read_csv(ROOT / "results/sponsor_comparison.csv")
    pd.testing.assert_frame_equal(saved[checkpoints.columns], checkpoints, check_dtype=False)
    for checkpoint, result in zip(checkpoints.itertuples(), saved.itertuples()):
        monthly = returns.loc[checkpoint.period_start:checkpoint.period_end, checkpoint.ticker]
        assert len(monthly) > 0
        growth = 1.0
        for monthly_return in monthly:
            growth *= 1 + monthly_return
        if checkpoint.metric == "cagr":
            expected = growth ** (12 / len(monthly)) - 1
        else:
            assert checkpoint.metric == "cumulative_return"
            expected = growth - 1
        difference = (expected - checkpoint.sponsor_return) * 10_000
        close(result.vendor_return, expected)
        close(result.difference_bps, difference)
        assert result.review_needed == (abs(difference) > 5)


def check_data_and_returns():
    count = verify_sources(ROOT)
    returns = load_returns(ROOT)
    assert len(returns) == 120
    assert list(returns.columns) == ["SEQUX", "DODGX", "SPY"]
    assert returns.index.to_period("M").equals(pd.period_range("2015-01", "2024-12", freq="M"))
    assert not returns.isna().any().any()
    assert (returns.abs() < 1).all().all(), "Expect decimal returns, not percentages."
    for invalid in [returns.drop(returns.index[12]), returns * 100]:
        try:
            validate_returns(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("Missing months or percentage-unit returns must be rejected.")

    close(compound_return(pd.Series([0.01] * 12)), 1.01 ** 12 - 1)
    close(compound_return(pd.Series([0.10, -0.10] * 6)), 0.99 ** 6 - 1)
    # Losing 20%, then gaining 25%, recovers exactly; the initial loss still counts.
    for actual, expected in zip(drawdown(pd.Series([-0.20, 0.25, -0.10])), [-0.20, 0, -0.10]):
        close(actual, expected)

    performance = performance_table(returns)
    close(performance.loc["SPY", "correlation_with_spy"], 1)
    assert (performance["max_drawdown"] < 0).all()
    assert (performance["volatility"] > 0).all()
    saved = pd.read_csv(ROOT / "results/performance.csv", index_col="ticker")
    pd.testing.assert_frame_equal(saved, performance, check_dtype=False, rtol=1e-10)

    allocations = allocation_table(returns)
    assert len(allocations) == 6
    assert set(allocations["weight"]) == {0, 0.025, 0.05}
    for row in allocations.itertuples():
        close(row.dollar_allocation, 5_000_000_000 * row.weight)
        close(row.us_equity_replaced, row.weight / 0.20)
        # Total monthly active differences divided by 10 years: arithmetic annual contribution.
        expected = row.weight * (returns[row.manager] - returns["SPY"]).sum() / 10
        close(row.arithmetic_annual_contribution, expected)
    saved = pd.read_csv(ROOT / "results/allocations.csv")
    pd.testing.assert_frame_equal(saved, allocations, check_dtype=False, rtol=1e-10)
    regimes = pd.read_csv(ROOT / "results/regimes.csv")
    assert len(regimes) == 6
    for row in regimes.itertuples():
        start, end = ("2020-02", "2020-03") if row.regime == "COVID selloff" else ("2022-01", "2022-12")
        close(row.cumulative_return, (1 + returns.loc[start:end, row.ticker]).prod() - 1)
    check_sponsor_comparison(returns)
    return count


def check_liquidity(rows, initial_nav=5e9, annual_spending=250e6, commitments=1e9, reserve=125e6):
    """Rebuild the cash, investment, commitment and NAV bridges independently."""
    assert len(rows) == 12
    cash, bonds, equity = initial_nav * .05, initial_nav * .15, initial_nav * .30
    private, hedge_funds = initial_nav * .35, initial_nav * .15
    previous_nav, unpaid_spending, unpaid_calls = initial_nav, 0.0, 0.0
    for number, row in enumerate(rows.itertuples(), start=1):
        close(row.month, number)
        loss = 0.0
        if number == 1:
            loss = equity * .50 + bonds * .10 + hedge_funds * .25 + private * .40
            bonds, equity, hedge_funds, private = bonds * .90, equity * .50, hedge_funds * .75, private * .60
        close(row.valuation_loss, loss)
        close(row.beginning_nav, previous_nav)
        close(row.spending_due, unpaid_spending + annual_spending / 12)
        close(row.sale_costs, row.equity_sales * .05)
        assert row.bond_sales <= bonds + 1e-5
        assert row.equity_sales <= equity + 1e-5
        if row.equity_sales > 1e-5:
            close(bonds - row.bond_sales, 0)  # Bonds must be exhausted first.
        cash += row.bond_sales + row.equity_sales - row.sale_costs - row.spending_paid - row.calls_paid
        bonds -= row.bond_sales
        equity -= row.equity_sales
        private += row.calls_paid
        commitments -= row.calls_paid
        unpaid_spending += annual_spending / 12 - row.spending_paid
        unpaid_calls += row.new_calls - row.calls_paid
        close(row.cash, cash)
        close(row.bonds, bonds)
        close(row.equity, equity)
        close(row.hedge_funds, hedge_funds)
        close(row.private_nav, private)
        close(row.remaining_commitments, commitments)
        close(row.unpaid_spending, unpaid_spending)
        close(row.unpaid_calls, unpaid_calls)
        close(row.unpaid_obligations, unpaid_spending + unpaid_calls)
        close(row.total_nav, cash + bonds + equity + hedge_funds + private - unpaid_spending)
        close(row.total_nav, previous_nav - loss - annual_spending / 12 - row.sale_costs)
        close(row.reserve_shortfall, max(0, reserve - cash))
        assert min(cash, bonds, equity, private, commitments, unpaid_spending, unpaid_calls) >= -1e-5
        assert unpaid_calls <= commitments + 1e-5
        close(row.nav_error, 0)
        previous_nav = row.total_nav


def main():
    count = check_data_and_returns()
    check_packaged_sources()
    baseline, sensitivity = liquidity_stress(), liquidity_stress(call_fraction=1.0)
    for rows in [baseline, sensitivity]:
        check_liquidity(rows)
        close(rows["unpaid_obligations"].max(), 0)
    close(baseline["new_calls"].sum(), .8e9)
    close(sensitivity["new_calls"].sum(), 1e9)
    # Extra calls require extra equity proceeds once the bonds have been sold.
    close(sensitivity["equity_sales"].sum() - baseline["equity_sales"].sum(), .2e9 / .95)
    transfers = liquidity_stress(initial_commitments=100e6, annual_spending=0, reserve=0)
    check_liquidity(transfers, annual_spending=0, commitments=100e6, reserve=0)
    close(transfers.iloc[-1].total_nav, transfers.iloc[0].total_nav)
    exhausted = liquidity_stress(call_fraction=1, initial_commitments=10e9)
    check_liquidity(exhausted, commitments=10e9)
    assert exhausted.iloc[-1].unpaid_obligations > 0
    saved = pd.read_csv(ROOT / "results/liquidity_monthly.csv")
    summaries = pd.read_csv(ROOT / "results/liquidity_summary.csv").set_index("call_fraction")
    assert len(saved) == 24 and len(summaries) == 2
    for fraction, rows in [(.8, baseline), (1.0, sensitivity)]:
        matching = saved.loc[saved["call_fraction"] == fraction].reset_index(drop=True)
        pd.testing.assert_frame_equal(matching[rows.columns], rows, check_dtype=False, rtol=1e-10, atol=1e-5)
        summary, last = summaries.loc[fraction], rows.iloc[-1]
        for field in ["calls_paid", "spending_paid", "bond_sales", "equity_sales", "sale_costs"]:
            close(summary[f"total_{field}"], rows[field].sum())
        for output, field in [("ending_cash", "cash"), ("ending_private_nav", "private_nav"), ("ending_nav", "total_nav"),
                              ("remaining_commitments", "remaining_commitments"), ("unpaid_obligations", "unpaid_obligations")]:
            close(summary[output], last[field])
        close(summary.private_weight, last.private_nav / last.total_nav)
        close(summary.max_reserve_shortfall, rows.reserve_shortfall.max())
    for filename in ["growth_of_100.png", "drawdowns.png", "monthly_asset_sales.png"]:
        assert (ROOT / "results" / filename).read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    print(f"Passed: {count} source hashes; public data package; 120 months; returns, sponsor checks, allocations, liquidity bridges and saved outputs.")


if __name__ == "__main__":
    main()
