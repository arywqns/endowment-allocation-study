# Data sources

`monthly_returns.csv` contains 120 monthly decimal returns for SEQUX, DODGX and SPY, January 2015–December 2024. `sponsor_returns.csv` contains five published fund-return checkpoints.

## Monthly returns

Each monthly return is the final available daily adjusted close divided by the previous month's final adjusted close, minus one. December 2014 supplies the starting price. Daily dates use the exchange timezone, America/New_York.

Adjusted close is Yahoo's total-return proxy for distributions and share changes. Fund operating expenses are already reflected in the underlying NAV. Dividends are not added again, and today's expense ratio is not subtracted from historical returns.

The original preparation rejected absent or stale month-end prices. The analysis checks exactly 120 ordered calendar month-end dates, the expected columns, finite decimal returns and file hashes. It never fills or interpolates a return. As a unit check for this fixed sample, each return must lie between −100% and +100%; this is not a universal bound on investment returns.

## Source register

`sources.json` records the original source URLs, UTC retrieval times on October 16, 2026, SHA-256 hashes and the relationships between source files and input tables.

| Source | Use |
|---|---|
| [Yahoo SEQUX daily history](https://query1.finance.yahoo.com/v8/finance/chart/SEQUX?period1=1417392000&period2=1735776000&interval=1d&events=history&includeAdjustedClose=true) | Daily adjusted closes |
| [Yahoo DODGX daily history](https://query1.finance.yahoo.com/v8/finance/chart/DODGX?period1=1417392000&period2=1735776000&interval=1d&events=history&includeAdjustedClose=true) | Daily adjusted closes |
| [Yahoo SPY daily history](https://query1.finance.yahoo.com/v8/finance/chart/SPY?period1=1417392000&period2=1735776000&interval=1d&events=history&includeAdjustedClose=true) | Daily adjusted exchange-price closes |
| [Sequoia December 2024 shareholder report](https://www.sequoiafund.com/wp-content/uploads/2025/02/SEQUX10-Sequoia-Fund_TSR-12.31.2024-Final-for-ADA-request.pdf) | Sponsor 2024 return and ten-year CAGR |
| [Dodge & Cox 2024 US equity review](https://www.dodgeandcox.com/individual-investor/us/en/insights/2024-annual-investment-reviews/us-equity-strategy.html) | Class I one-, five- and ten-year returns |

The public repository includes the two derived CSVs, not the original downloads or full sponsor publications. Their URLs, retrieval dates and hashes remain in the register for provenance. The original downloads have `required_for_analysis: false`: they are checked if present at their recorded paths, but are not needed to run the analysis. Both input CSVs are required and always checked. A fresh public copy therefore verifies two file hashes; a copy with all original downloads verifies seven.

A hash detects changed bytes. It does not establish economic accuracy or independently reconstruct official fund returns. Source endpoints may change, and a fresh download may differ from the recorded vintage. It should be reviewed rather than silently substituted. Third-party data and publications retain their original ownership.

## Sponsor comparisons

`sponsor_returns.csv` records the period, return definition and source for each checkpoint. `results/sponsor_comparison.csv` calculates the corresponding return from the monthly series and reports vendor minus sponsor in basis points. Absolute differences above 5 basis points are flagged for review; this is a screening threshold.

- Sequoia's ten-year vendor CAGR is approximately 7.9545%, compared with the sponsor's 8.02%: −6.55 basis points annually.
- Dodge & Cox's vendor 2024 return is approximately 14.3606%, compared with the sponsor's 14.52%: −15.94 basis points.
- Adjustment, reinvestment or rounding conventions may contribute, but no cause has been established. The observations have not been altered to force agreement.
- There is no verified archived SPY sponsor checkpoint. S&P 500 index returns are not substituted for SPY returns.

The retained series have no missing months. The fund histories are share-class specific; SPY uses exchange prices while mutual-fund records are NAV based. The selection of surviving funds and the 2026 retrieval vintage introduce survivorship and hindsight limitations. Current vehicle availability, team changes and institutional terms are outside this study.
