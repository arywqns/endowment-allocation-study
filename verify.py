"""A few checks of the financial logic. Run after: python analyze.py."""

from math import isclose
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory

import pandas as pd

from analyze import (
    liquidity_sensitivities, stress_summary, validate_assumptions,
    allocation_table, compound_return, drawdown, liquidity_stress,
    load_returns, performance_table, validate_returns, verify_sources,
)

if not __debug__:
    raise RuntimeError("Run verification without Python's -O flag; assertions are required.")

ROOT = Path(__file__).resolve().parent


def temporary_case():
    """Keep disposable tests inside the project, including restricted environments."""
    scratch = ROOT / 'work'
    scratch.mkdir(exist_ok=True)
    return TemporaryDirectory(dir=scratch)


def close(actual, expected):
    """Allow only rounding error, including for dollar amounts in billions."""
    assert isclose(float(actual), float(expected), rel_tol=1e-11, abs_tol=1e-5), (
        actual, expected
    )


def check_packaged_sources():
    """The public copy needs two input tables; archived originals are optional."""
    with temporary_case() as folder:
        package = Path(folder)
        data = package / "data"
        data.mkdir()
        for filename in ["sources.json", "monthly_returns.csv", "sponsor_returns.csv", "benchmark_context.csv"]:
            copyfile(ROOT / "data" / filename, data / filename)
        assert verify_sources(package) == 3
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


def check_reporting_and_sensitivities():
    """Exercise actual changes, including the formerly stale memo descriptions."""
    import copy
    import calendar
    from datetime import datetime
    from zoneinfo import ZoneInfo
    import analyze as model
    from prepare_data import monthly_from_chart, prepare, MONTHS

    calculated = liquidity_sensitivities()
    saved = pd.read_csv(ROOT / "results/liquidity_sensitivities.csv")
    pd.testing.assert_frame_equal(saved, calculated, check_dtype=False, rtol=1e-10, atol=1e-5)
    rows = calculated.set_index("scenario")
    close(rows.loc["calls_40%", "total_gross_sales"], 525e6)
    close(rows.loc["zero_reserve", "total_equity_sales"], 125e6 / .95)
    close(rows.loc["deduction_0%", "total_equity_sales"], 250e6)
    close(rows.loc["deduction_1%", "total_equity_sales"], 250e6 / .99)
    close(rows.loc["front_loaded_calls", "total_gross_sales"], rows.loc["calls_80%", "total_gross_sales"])
    close(rows.loc["front_loaded_calls", "first_equity_sale_month"], 1)
    assert not calculated.funding_failure.any()
    empty = liquidity_stress(initial_nav=0, annual_spending=0, initial_commitments=0, reserve=0)
    empty["call_fraction"] = .8
    assert pd.isna(stress_summary(empty).iloc[0].private_weight)
    for bad in [1, -.01, float('nan')]:
        try:
            liquidity_stress(equity_haircut=bad)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid realization deduction was accepted.')

    # Synthetic chart construction tests parser mechanics, not real-data provenance.
    timestamps = [int(datetime(y, m, calendar.monthrange(y, m)[1], 16, tzinfo=ZoneInfo('America/New_York')).timestamp()) for y, m in MONTHS]
    prices = [100 * 1.01 ** i for i in range(len(MONTHS))]
    chart = {'chart': {'error': None, 'result': [{'meta': {'symbol': 'SPY', 'exchangeTimezoneName': 'America/New_York'}, 'timestamp': timestamps, 'indicators': {'adjclose': [{'adjclose': prices}]}}]}}
    candidate, selected = monthly_from_chart(chart, 'SPY')
    assert len(candidate) == 120 and len(selected) == 121
    for value in candidate:
        close(value, .01)
    invalid = copy.deepcopy(chart)
    invalid['chart']['result'][0]['timestamp'][-1] -= 8 * 86400
    try:
        monthly_from_chart(invalid, 'SPY')
    except ValueError:
        pass
    else:
        raise AssertionError('Stale month-end observation was accepted.')

    # Test source hashes, candidate export and non-overwrite behavior end to end.
    import csv
    import hashlib
    import json
    with temporary_case() as folder:
        package = Path(folder)
        (package / 'data/raw').mkdir(parents=True)
        sources = []
        for ticker in ['SEQUX', 'DODGX', 'SPY']:
            payload = copy.deepcopy(chart)
            payload['chart']['result'][0]['meta']['symbol'] = ticker
            raw = json.dumps(payload).encode('utf-8')
            source_path = f'data/raw/{ticker}.json'
            (package / source_path).write_bytes(raw)
            sources.append({'id': f'yahoo_{ticker}', 'path': source_path, 'sha256': hashlib.sha256(raw).hexdigest()})
        (package / 'data/sources.json').write_text(json.dumps(sources), encoding='utf-8')
        with (package / 'data/monthly_returns.csv').open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['date', 'SEQUX', 'DODGX', 'SPY'])
            for row in selected[1:]:
                writer.writerow([row['month_end'], .01, .01, .01])
        before = (package / 'data/monthly_returns.csv').read_bytes()
        prepare(package, package / 'candidate')
        check = json.loads((package / 'candidate/comparison.json').read_text())
        assert check['matches_published_within_1e_10']
        assert (package / 'data/monthly_returns.csv').read_bytes() == before
        try:
            prepare(package, package / 'candidate')
        except FileExistsError:
            pass
        else:
            raise AssertionError('Existing candidate outputs were overwritten.')
        raw_file = package / 'data/raw/SPY.json'
        raw_file.write_bytes(raw_file.read_bytes() + b' ')
        try:
            prepare(package, package / 'other')
        except ValueError:
            pass
        else:
            raise AssertionError('Changed raw-source vintage was accepted.')

    previous = {key: getattr(model, key) for key in ['ROOT', 'CALL_FRACTIONS', 'LOSSES', 'EQUITY_SALE_HAIRCUT', 'ANNUAL_SPENDING', 'MINIMUM_CASH', 'INITIAL_NAV', 'POLICY']}
    try:
        with temporary_case() as folder:
            package = Path(folder)
            (package / 'data').mkdir()
            for source in (ROOT / 'data').glob('*'):
                if source.is_file():
                    copyfile(source, package / 'data' / source.name)
            model.ROOT = package
            model.CALL_FRACTIONS = [.4]
            model.LOSSES = {**model.LOSSES, 'equity': .3}
            model.EQUITY_SALE_HAIRCUT = .01
            model.INITIAL_NAV = 4e9
            model.ANNUAL_SPENDING = 200e6
            model.MINIMUM_CASH = 50e6
            model.main()
            memo = (package / 'IC_MEMO.md').read_text(encoding='utf-8')
            assert '30.0% equity' in memo
            assert 'cases call 40% of this stock' in memo
            assert '1.0% additional realization deduction' in memo
            assert 'Fixed annual spending: $200.0m' in memo
            assert 'Soft cash target: $50.0m' in memo
            assert '50.0% equity' not in memo and 'cases call 80%' not in memo
            result = pd.read_csv(package / 'results/liquidity_summary.csv')
            close(result.iloc[0].total_calls_paid, 400e6)
            assert len(result) == 1
            assert (package / 'results/monthly_asset_sales.png').is_file()
            model.POLICY = {**model.POLICY, 'cash': .06}
            try:
                model.validate_assumptions()
            except ValueError:
                pass
            else:
                raise AssertionError('Policy that does not sum to one was accepted.')
    finally:
        for key, value in previous.items():
            setattr(model, key, value)


def main():
    validate_assumptions()
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
    check_reporting_and_sensitivities()
    print(f"Passed: {count} source hashes; public data package; 120 months; returns, sponsor checks, allocations, liquidity bridges and saved outputs.")


if __name__ == "__main__":
    main()
