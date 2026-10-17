# Should the endowment hire an active equity manager?

**Research window:** January 2015–December 2024. **Source retrieval:** October 16, 2026.
**Case:** A hypothetical university endowment with $5,000.0 million in assets.

## Recommendation

Keep the passive allocation for now. Neither manager's results in this period provide a strong enough reason to replace SPY. A hire would need more evidence about the investment process, portfolio fit and terms. This study compares 0%, 2.5% and 5% allocations to Sequoia or Dodge & Cox, funded by reducing SPY.

## What the returns show

| Investment | CAGR | Volatility | Max drawdown | Correlation with SPY |
|---|---:|---:|---:|---:|
| SEQUX | 7.95% | 17.33% | -36.22% | 0.86 |
| DODGX | 10.84% | 17.75% | -29.07% | 0.91 |
| SPY | 13.00% | 15.33% | -23.93% | 1.00 |

Both funds earned less than SPY, with more volatility and deeper month-end losses. The main counterargument is benchmark fit: a value-oriented manager can behave differently from the US large-cap market. In 2022 DODGX returned -7.25%, compared with -18.18% for SPY. That warrants a closer style comparison; one favorable year does not settle the decision. February–March 2020 results are also in `results/regimes.csv`.

## What changes at 5%?

The case starts with 20% US equity, 10% international equity, 15% bonds, 15% hedge funds, 35% private markets and 5% cash. A 2.5% manager position is $125.0 million, replacing 12.5% of US equity. At 5%, those figures are $250.0 million and 25%.

At 5%, the arithmetic annualized contribution from replacing SPY is -0.21 percentage points for SEQUX and -0.08 for DODGX. The calculation is 12 × average monthly weight × (manager return − SPY return). This is not a compound return for the whole endowment. SPY measures what the endowment gives up, and may not be the best benchmark for evaluating a manager's style. No private-market or hedge-fund return history is modeled.

## Cash requirements under stress

Assume immediate losses of 50% in public equity, 10% in bonds, 25% in hedge funds and 40% in private markets. Annual spending is $250.0 million; 80% of commitments are called evenly over 12 months. There are no distributions or later returns. Bonds are sold first, then equities with a 5% haircut, targeting $125.0 million of cash. Hedge funds and private assets cannot be sold, and there is no borrowing. All public equity has the same assumed loss, so this is a funding test rather than a manager forecast.

The 80% call case needs $938.2 million of gross sales: $675.0 million in bonds and $263.2 million in equities. Costs total $13.2 million. Ending cash is $125.0 million, unpaid obligations are $0.0 million, and the largest reserve shortfall is $0.0 million. Ending NAV is $3,024.3 million, with 61.17% in private assets.

Calling 100% requires another $210.5 million of sales. Costs rise to $23.7 million; ending cash is $125.0 million. Unpaid obligations are $0.0 million and the largest reserve shortfall is $0.0 million. Calls move money from cash into private investments; spending and sale costs reduce NAV. Paying the bills and keeping enough liquid assets afterward are separate concerns.

## What is still missing?

The unresolved vendor-minus-sponsor differences are SEQUX, 2015-01-01 to 2024-12-31: -6.55 bp; DODGX, 2024-01-01 to 2024-12-31: -15.94 bp. There is no verified SPY sponsor checkpoint. This selected sample of surviving funds uses data retrieved in 2026, with hindsight, share-class and team changes to consider. Month-end observations miss intramonth losses.

Before reconsidering a hire, compare suitable low-cost style alternatives and investigate the current team, process, eligible vehicle, fees, capacity, operations and full holdings. Evidence of a repeatable process and a useful portfolio role could change the recommendation. Those checks are outside this project.
