"""Render case facts from the same inputs as the calculations.

The recommendation is a stated research judgment. Tables and scenario descriptions
are generated; changing data still requires reviewing the investment judgment.
"""
import math


def money(value):
    return f"${value / 1e6:,.1f}m"


def pct(value):
    return f"{value:.2%}" if math.isfinite(value) else "undefined"


def write_memo(path, performance, allocations, regimes, summary, checks,
               sensitivities, settings, benchmarks):
    c = settings
    asset_names = {'us_equity': 'US equity', 'international_equity': 'international equity', 'bonds': 'bonds', 'hedge_funds': 'hedge funds', 'private_markets': 'private markets', 'cash': 'cash'}
    policy = ", ".join(f"{value:.1%} {asset_names[name]}" for name, value in c['policy'].items())
    losses = ", ".join(f"{value:.1%} {name.replace('_', ' ')}" for name, value in c['losses'].items())
    call_cases = ", ".join(f"{value:.0%}" for value in summary.call_fraction)
    spending_rate = c['spending'] / c['initial_nav'] if c['initial_nav'] else float('nan')
    lines = [
        '# Endowment Allocation & Manager Evaluation: Historical Case',
        '',
        '**Return window:** January 2015-December 2024. **Original input retrieval:** October 16, 2026. **Case review:** October 18, 2026.',
        f"**Illustrative starting NAV:** {money(c['initial_nav'])}. All allocations and funding obligations are hypothetical.",
        '',
        '## Case decision',
        '',
        'Retain the passive allocation pending further research. The evidence assembled here does not establish a sufficiently supported reason to replace it. This is a preliminary public-data evaluation; it does not establish that either manager lacks skill. Before considering a hire, distinguish the desired style allocation from the merits and implementation of a specific manager.',
        '',
        'The historical fund screen and the funding stress are separate exercises. The latter applies one assumed loss to all public equity and therefore cannot rank manager downside protection or identify a preferred manager allocation.',
        '',
        '## Historical evidence',
        '',
        '| Investment | CAGR | Annualized volatility | Month-end maximum drawdown | Correlation with SPY |',
        '|---|---:|---:|---:|---:|',
    ]
    for ticker, row in performance.iterrows():
        lines.append(f'| {ticker} | {row.cagr:.2%} | {row.volatility:.2%} | {row.max_drawdown:.2%} | {row.correlation_with_spy:.2f} |')
    comparisons = []
    for ticker in ['SEQUX', 'DODGX']:
        difference = performance.loc[ticker, 'cagr'] - performance.loc['SPY', 'cagr']
        comparisons.append(f"{ticker}: {difference * 100:+.2f} percentage points of annualized compound return versus SPY")
    lines += ['', '; '.join(comparisons) + '. These are standalone fund comparisons; they do not isolate skill from style.',
              '', 'SPY is the passive investment being reduced. A style benchmark answers a separate question. The following figures are sponsor-reported context, kept separate from the Yahoo-derived monthly return series:',
              '', '| Period ending December 2024 | DODGX Class I | Russell 1000 Value Index |', '|---|---:|---:|']
    for row in benchmarks.itertuples():
        label = '2024' if row.metric == 'cumulative_return' else f"{int(row.period_end[:4]) - int(row.period_start[:4]) + 1}-year annualized"
        lines.append(f'| {label} | {row.fund_return:.2%} | {row.benchmark_return:.2%} |')
    lines += ['', 'DODGX exceeded this value benchmark while lagging broad US equities over the reported ten-year period. That is material contrary evidence to a simple rejection based on SPY. It does not establish factor-adjusted alpha. [Source: sponsor presentation, page 6](https://www.dodgeandcox.com/content/dam/dc/us/en/pdf/podcast/2024_Annual_U.S._Equity_Review_Presentation.pdf).',
              '', 'A matched monthly style series and an assessment of the actual portfolio role are still needed. There is no factor regression in this study. The selected February-March 2020 and calendar-2022 returns are in results/regimes.csv; they are neither daily peak-to-trough losses nor a comprehensive regime model.',
              '', '## Illustrative allocation effects', '',
              f'The funding budget is {c["policy"]["us_equity"]:.1%} of NAV. Allocations below replace SPY within that budget; foreign holdings can change look-through geographic exposure. These sizes are scenarios, not optimized recommendations.', '',
              '| Fund | Endowment weight | Initial position | Share of funding sleeve replaced | Annualized arithmetic contribution |', '|---|---:|---:|---:|---:|']
    for row in allocations.itertuples():
        lines.append(f'| {row.manager} | {row.weight:.1%} | {money(row.dollar_allocation)} | {row.us_equity_replaced:.1%} | {100 * row.arithmetic_annual_contribution:+.3f} pp |')
    lines += ['', 'Contribution equals 12 times the average monthly weight multiplied by the fund-minus-SPY return. Constant weights and no trading costs are assumed. It is an incremental arithmetic contribution, not the compounded return or risk of the entire endowment.',
              '', '## Funding assumptions', '',
              f'- Starting mix: {policy}.',
              f'- Fixed annual spending: {money(c["spending"])}, equal to {pct(spending_rate)} of beginning NAV, paid monthly and unchanged after the shock. No smoothed or changing payout formula is implemented.',
              f'- Opening unfunded commitments: {money(c["commitments"])}; cases call {call_cases} of this stock, evenly over twelve months.',
              f'- Soft cash target: {money(c["reserve"])}. Obligations take priority over this target.',
              f'- Immediate joint losses: {losses}; no later investment returns or private distributions.',
              f'- Sell bonds first with no additional deduction, then public equity with a {c["equity_haircut"]:.1%} additional realization deduction after the market shock.',
              '- No hedge-fund redemptions, private-asset sales, borrowing, or settlement delays. Spending is paid before calls as an explicit modeling convention.',
              '', 'These are deliberately severe illustrative funding assumptions, not estimated probabilities or actual institutional policies. The call rates test a rapid draw of opening commitments without distributions. The additional equity deduction tests adverse realization beyond marked prices; it is not asserted to be a normal public-fund trading fee. Cost-free bond sales are an asymmetric simplification. The source of stress is the combined assumption set, not an empirically calibrated historical replay.',
              '', 'Paid calls are credited fully to private NAV and reduce commitments. Call-related fees, later impairment, private valuation lags, fund vintages and default penalties are not modeled. Unpaid obligations indicate a funding failure; the arrears balance is not a model of actual default outcomes.',
              '', '## Funding results', '',
              '| Calls / opening commitments | Calls paid | Bonds sold | Gross equity sold | Gross total sales | Realization loss | Ending cash | Ending NAV | Private weight |', '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for row in summary.itertuples():
        total = row.total_bond_sales + row.total_equity_sales
        lines.append(f'| {row.call_fraction:.0%} | {money(row.total_calls_paid)} | {money(row.total_bond_sales)} | {money(row.total_equity_sales)} | {money(total)} | {money(row.total_sale_costs)} | {money(row.ending_cash)} | {money(row.ending_nav)} | {pct(row.private_weight)} |')
    lines += ['', '| Calls | Unpaid obligations at year-end | Any monthly funding failure | Remaining commitments | Ending bonds | Realizable liquid assets | Locked assets / NAV |', '|---|---:|---|---:|---:|---:|---:|']
    for row in summary.itertuples():
        lines.append(f'| {row.call_fraction:.0%} | {money(row.unpaid_obligations)} | {"yes" if row.funding_failure else "no"} | {money(row.remaining_commitments)} | {money(row.ending_bonds)} | {money(row.ending_realizable_liquidity)} | {pct(row.locked_weight)} |')
    base = summary.iloc[0]
    lines += ['', 'Realizable liquidity includes cash, remaining bonds, and public equity net of the same realization deduction. Locked assets combine private markets and hedge funds. A maintained cash target does not by itself establish portfolio flexibility.',
              '', f'For the first case, gross sales are {money(base.total_bond_sales + base.total_equity_sales)} ({pct((base.total_bond_sales + base.total_equity_sales) / c["initial_nav"] if c["initial_nav"] else float("nan"))} of initial NAV), including {money(base.total_equity_sales)} of public equity. These are conditional asset sales, not investment losses or a forecast.',
              '', 'Next decisions concern reserve sizing, commitment pacing, and contingent liquidity. Bond exhaustion, where shown above, and rising locked-asset weights are policy consequences even when every obligation is paid.',
              '', '## Assumption sensitivities', '',
              'Each row changes the named assumption around the first case, holding other assumptions fixed. Month 0 means no equity sale occurs. Front-loading changes when assets must be sold; with no subsequent returns, distributions or timing-dependent costs, it need not change annual totals.', '',
              '| Scenario | Calls | Cash target | Equity deduction | Call timing | Gross total sales | Gross equity sales | First equity-sale month |', '|---|---:|---:|---:|---|---:|---:|---:|']
    for row in sensitivities.itertuples():
        lines.append(f'| {row.scenario} | {row.call_fraction:.0%} | {money(row.cash_target)} | {row.equity_sale_haircut:.0%} | {row.call_timing} | {money(row.total_gross_sales)} | {money(row.total_equity_sales)} | {row.first_equity_sale_month} |')
    lines += ['', '## Data and decision limits', '',
              'The supplied monthly series are adjusted-price total-return proxies. Fund operating expenses are embedded; dividends and contemporary fees are not added or subtracted again. Month-end sampling excludes intramonth losses. Selected surviving funds, the ten-year endpoint and the 2026 retrieval vintage limit inference.',
              '', 'Unresolved vendor-minus-sponsor differences above the 5 bp screening threshold:']
    flagged = checks.loc[checks.review_needed]
    if flagged.empty:
        lines.append('- None exceeds the screening threshold; this does not prove source accuracy.')
    for row in flagged.itertuples():
        lines.append(f'- {row.ticker}, {row.period_start} to {row.period_end}: {row.difference_bps:+.2f} bp ({row.metric}).')
    lines += ['', 'These differences have not been explained or forced to zero. There is no matched archived SPY sponsor checkpoint. The sponsor context table is not spliced into the vendor series. Reproducing supplied-input outputs is possible offline; original-vintage reconstruction remains unverified because the original raw downloads are not bundled. See data/README.md.',
              '', 'SEQUX is the historical Sequoia mutual-fund series. Its sponsor reports an ETF successor beginning October 16, 2026; current vehicle terms require separate review. [Successor disclosure](https://www.sequoiaetf.com/sequoia-etf-performance/).',
              '', 'Before a real hire: add a matched monthly style comparison; assess team continuity, process and holdings; verify eligible vehicle, fees, capacity and operations; and test the proposed role against the whole portfolio. The choice to retain passive exposure is a stated case judgment that must be reconsidered if evidence changes.']
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
