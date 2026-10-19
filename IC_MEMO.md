# Endowment Allocation & Manager Evaluation: Historical Case

**Return window:** January 2015-December 2024. **Original input retrieval:** October 16, 2026. **Case review:** October 18, 2026.
**Illustrative starting NAV:** $5,000.0m. All allocations and funding obligations are hypothetical.

## Case decision

Retain the passive allocation pending further research. The evidence assembled here does not establish a sufficiently supported reason to replace it. This is a preliminary public-data evaluation; it does not establish that either manager lacks skill. Before considering a hire, distinguish the desired style allocation from the merits and implementation of a specific manager.

The historical fund screen and the funding stress are separate exercises. The latter applies one assumed loss to all public equity and therefore cannot rank manager downside protection or identify a preferred manager allocation.

## Historical evidence

| Investment | CAGR | Annualized volatility | Month-end maximum drawdown | Correlation with SPY |
|---|---:|---:|---:|---:|
| SEQUX | 7.95% | 17.33% | -36.22% | 0.86 |
| DODGX | 10.84% | 17.75% | -29.07% | 0.91 |
| SPY | 13.00% | 15.33% | -23.93% | 1.00 |

SEQUX: -5.04 percentage points of annualized compound return versus SPY; DODGX: -2.16 percentage points of annualized compound return versus SPY. These are standalone fund comparisons; they do not isolate skill from style.

SPY is the passive investment being reduced. A style benchmark answers a separate question. The following figures are sponsor-reported context, kept separate from the Yahoo-derived monthly return series:

| Period ending December 2024 | DODGX Class I | Russell 1000 Value Index |
|---|---:|---:|
| 2024 | 14.52% | 14.37% |
| 5-year annualized | 11.99% | 8.68% |
| 10-year annualized | 10.85% | 8.49% |

DODGX exceeded this value benchmark while lagging broad US equities over the reported ten-year period. That is material contrary evidence to a simple rejection based on SPY. It does not establish factor-adjusted alpha. [Source: sponsor presentation, page 6](https://www.dodgeandcox.com/content/dam/dc/us/en/pdf/podcast/2024_Annual_U.S._Equity_Review_Presentation.pdf).

A matched monthly style series and an assessment of the actual portfolio role are still needed. There is no factor regression in this study. The selected February-March 2020 and calendar-2022 returns are in results/regimes.csv; they are neither daily peak-to-trough losses nor a comprehensive regime model.

## Illustrative allocation effects

The funding budget is 20.0% of NAV. Allocations below replace SPY within that budget; foreign holdings can change look-through geographic exposure. These sizes are scenarios, not optimized recommendations.

| Fund | Endowment weight | Initial position | Share of funding sleeve replaced | Annualized arithmetic contribution |
|---|---:|---:|---:|---:|
| SEQUX | 0.0% | $0.0m | 0.0% | +0.000 pp |
| SEQUX | 2.5% | $125.0m | 12.5% | -0.107 pp |
| SEQUX | 5.0% | $250.0m | 25.0% | -0.213 pp |
| DODGX | 0.0% | $0.0m | 0.0% | +0.000 pp |
| DODGX | 2.5% | $125.0m | 12.5% | -0.039 pp |
| DODGX | 5.0% | $250.0m | 25.0% | -0.077 pp |

Contribution equals 12 times the average monthly weight multiplied by the fund-minus-SPY return. Constant weights and no trading costs are assumed. It is an incremental arithmetic contribution, not the compounded return or risk of the entire endowment.

## Funding assumptions

- Starting mix: 20.0% US equity, 10.0% international equity, 15.0% bonds, 15.0% hedge funds, 35.0% private markets, 5.0% cash.
- Fixed annual spending: $250.0m, equal to 5.00% of beginning NAV, paid monthly and unchanged after the shock. No smoothed or changing payout formula is implemented.
- Opening unfunded commitments: $1,000.0m; cases call 80%, 100% of this stock, evenly over twelve months.
- Soft cash target: $125.0m. Obligations take priority over this target.
- Immediate joint losses: 50.0% equity, 10.0% bonds, 25.0% hedge funds, 40.0% private markets; no later investment returns or private distributions.
- Sell bonds first with no additional deduction, then public equity with a 5.0% additional realization deduction after the market shock.
- No hedge-fund redemptions, private-asset sales, borrowing, or settlement delays. Spending is paid before calls as an explicit modeling convention.

These are deliberately severe illustrative funding assumptions, not estimated probabilities or actual institutional policies. The call rates test a rapid draw of opening commitments without distributions. The additional equity deduction tests adverse realization beyond marked prices; it is not asserted to be a normal public-fund trading fee. Cost-free bond sales are an asymmetric simplification. The source of stress is the combined assumption set, not an empirically calibrated historical replay.

Paid calls are credited fully to private NAV and reduce commitments. Call-related fees, later impairment, private valuation lags, fund vintages and default penalties are not modeled. Unpaid obligations indicate a funding failure; the arrears balance is not a model of actual default outcomes.

## Funding results

| Calls / opening commitments | Calls paid | Bonds sold | Gross equity sold | Gross total sales | Realization loss | Ending cash | Ending NAV | Private weight |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 80% | $800.0m | $675.0m | $263.2m | $938.2m | $13.2m | $125.0m | $3,024.3m | 61.17% |
| 100% | $1,000.0m | $675.0m | $473.7m | $1,148.7m | $23.7m | $125.0m | $3,013.8m | 68.02% |

| Calls | Unpaid obligations at year-end | Any monthly funding failure | Remaining commitments | Ending bonds | Realizable liquid assets | Locked assets / NAV |
|---|---:|---|---:|---:|---:|---:|
| 80% | $0.0m | no | $200.0m | $0.0m | $587.5m | 79.77% |
| 100% | $0.0m | no | $0.0m | $0.0m | $387.5m | 86.68% |

Realizable liquidity includes cash, remaining bonds, and public equity net of the same realization deduction. Locked assets combine private markets and hedge funds. A maintained cash target does not by itself establish portfolio flexibility.

For the first case, gross sales are $938.2m (18.76% of initial NAV), including $263.2m of public equity. These are conditional asset sales, not investment losses or a forecast.

Next decisions concern reserve sizing, commitment pacing, and contingent liquidity. Bond exhaustion, where shown above, and rising locked-asset weights are policy consequences even when every obligation is paid.

## Assumption sensitivities

Each row changes the named assumption around the first case, holding other assumptions fixed. Month 0 means no equity sale occurs. Front-loading changes when assets must be sold; with no subsequent returns, distributions or timing-dependent costs, it need not change annual totals.

| Scenario | Calls | Cash target | Equity deduction | Call timing | Gross total sales | Gross equity sales | First equity-sale month |
|---|---:|---:|---:|---|---:|---:|---:|
| calls_0% | 0% | $125.0m | 5% | even | $125.0m | $0.0m | 0 |
| calls_40% | 40% | $125.0m | 5% | even | $525.0m | $0.0m | 0 |
| calls_80% | 80% | $125.0m | 5% | even | $938.2m | $263.2m | 10 |
| calls_100% | 100% | $125.0m | 5% | even | $1,148.7m | $473.7m | 8 |
| zero_reserve | 80% | $0.0m | 5% | even | $806.6m | $131.6m | 11 |
| deduction_0% | 80% | $125.0m | 0% | even | $925.0m | $250.0m | 10 |
| deduction_1% | 80% | $125.0m | 1% | even | $927.5m | $252.5m | 10 |
| deduction_5% | 80% | $125.0m | 5% | even | $938.2m | $263.2m | 10 |
| front_loaded_calls | 80% | $125.0m | 5% | front_loaded | $938.2m | $263.2m | 1 |

## Data and decision limits

The supplied monthly series are adjusted-price total-return proxies. Fund operating expenses are embedded; dividends and contemporary fees are not added or subtracted again. Month-end sampling excludes intramonth losses. Selected surviving funds, the ten-year endpoint and the 2026 retrieval vintage limit inference.

Unresolved vendor-minus-sponsor differences above the 5 bp screening threshold:
- SEQUX, 2015-01-01 to 2024-12-31: -6.55 bp (cagr).
- DODGX, 2024-01-01 to 2024-12-31: -15.94 bp (cumulative_return).

These differences have not been explained or forced to zero. There is no matched archived SPY sponsor checkpoint. The sponsor context table is not spliced into the vendor series. Reproducing supplied-input outputs is possible offline; original-vintage reconstruction remains unverified because the original raw downloads are not bundled. See data/README.md.

SEQUX is the historical Sequoia mutual-fund series. Its sponsor reports an ETF successor beginning October 16, 2026; current vehicle terms require separate review. [Successor disclosure](https://www.sequoiaetf.com/sequoia-etf-performance/).

Before a real hire: add a matched monthly style comparison; assess team continuity, process and holdings; verify eligible vehicle, fees, capacity and operations; and test the proposed role against the whole portfolio. The choice to retain passive exposure is a stated case judgment that must be reconsidered if evidence changes.
