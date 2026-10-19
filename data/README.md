# Data sources

`monthly_returns.csv` contains 120 monthly decimal returns for SEQUX, DODGX and SPY, January 2015–December 2024. `sponsor_returns.csv` contains five published fund-return checkpoints. `benchmark_context.csv` separately records three sponsor-reported DODGX/value-index comparisons; it is not a monthly benchmark series.

## Monthly returns

Each monthly return is the final available daily adjusted close divided by the previous month's final adjusted close, minus one. December 2014 supplies the starting price. Daily dates use the exchange timezone, America/New_York.

Adjusted close is Yahoo's total-return proxy for distributions and share changes. Fund operating expenses are already reflected in the underlying NAV. Dividends are not added again, and today's expense ratio is not subtracted from historical returns.

The construction convention above was documented with the original inputs, but its execution cannot be established from the public CSV alone. The analysis checks exactly 120 ordered calendar month-end dates, the expected columns, finite decimal returns and file hashes. It never fills or interpolates a return. As a unit check for this fixed sample, each return must lie between −100% and +100%; this is not a universal bound on investment returns.

## Source register

`sources.json` records the original source URLs, UTC retrieval times on October 16, 2026, SHA-256 hashes and the relationships between source files and input tables.

| Source | Use |
|---|---|
| [Yahoo SEQUX daily history](https://query1.finance.yahoo.com/v8/finance/chart/SEQUX?period1=1417392000&period2=1735776000&interval=1d&events=history&includeAdjustedClose=true) | Daily adjusted closes |
| [Yahoo DODGX daily history](https://query1.finance.yahoo.com/v8/finance/chart/DODGX?period1=1417392000&period2=1735776000&interval=1d&events=history&includeAdjustedClose=true) | Daily adjusted closes |
| [Yahoo SPY daily history](https://query1.finance.yahoo.com/v8/finance/chart/SPY?period1=1417392000&period2=1735776000&interval=1d&events=history&includeAdjustedClose=true) | Daily adjusted exchange-price closes |
| [Sequoia December 2024 shareholder report](https://www.sequoiafund.com/wp-content/uploads/2025/02/SEQUX10-Sequoia-Fund_TSR-12.31.2024-Final-for-ADA-request.pdf) | Sponsor 2024 return and ten-year CAGR |
| [Dodge & Cox 2024 US equity review](https://www.dodgeandcox.com/individual-investor/us/en/insights/2024-annual-investment-reviews/us-equity-strategy.html) | Class I one-, five- and ten-year returns |

The public repository includes three input CSVs, not the original downloads or full sponsor publications. Original-vintage URLs, retrieval dates and hashes remain in the register. The five original downloads are optional and hash-checked if present. All three input CSVs are required and hash-checked. A fresh copy verifies three file hashes. The newly cited benchmark presentation is a citation-only record, without a claim to an archived byte hash or original retrieval timestamp; its page-6 figures were checked during the October 18, 2026 revision.

A hash detects changed bytes. It does not establish economic accuracy or independently reconstruct official fund returns. Source endpoints may change, and a fresh download may differ from the recorded vintage. It should be reviewed rather than silently substituted. Third-party data and publications retain their original ownership.

## Sponsor comparisons

`sponsor_returns.csv` records the period, return definition and source for each checkpoint. `results/sponsor_comparison.csv` calculates the corresponding return from the monthly series and reports vendor minus sponsor in basis points. Absolute differences above 5 basis points are flagged for review; this is a screening threshold.

- Sequoia's ten-year vendor CAGR is approximately 7.9545%, compared with the sponsor's 8.02%: −6.55 basis points annually.
- Dodge & Cox's vendor 2024 return is approximately 14.3606%, compared with the sponsor's 14.52%: −15.94 basis points.
- Adjustment or reinvestment conventions may contribute, but no cause has been established. Rounding sponsor percentages to two decimals cannot by itself explain either flagged difference. The observations have not been altered to force agreement.
- There is no verified archived SPY sponsor checkpoint. S&P 500 index returns are not substituted for SPY returns.

The retained series have no missing months. The fund histories are share-class specific; SPY uses exchange prices while mutual-fund records are NAV based. The selection of surviving funds and the 2026 retrieval vintage introduce survivorship and hindsight limitations. Current vehicle availability, team changes and institutional terms are outside this study.

## Optional original-vintage reconstruction

Place the original Yahoo JSON files at the paths recorded in sources.json, then run from the project root:

```text
python prepare_data.py --output-dir work/prepared
```

The script requires exact source hashes and writes candidate returns, each selected actual observation date/adjusted close, and a comparison with the published CSV. It never replaces published inputs or updates their hashes. A changed endpoint response is a new vintage requiring review, not an automatic substitute.

Selected observations must be within four calendar days of month-end. This transparent stale-data guard is not a full exchange-holiday calendar. Timestamps must be ordered, unique and interpreted in America/New_York. Missing months and invalid selected adjusted closes are rejected. The parser is covered by synthetic-input tests; reconstruction of the published inputs remains unverified because their original raw files are absent.

## Style context and interpretation

The [Dodge & Cox presentation, page 6](https://www.dodgeandcox.com/content/dam/dc/us/en/pdf/podcast/2024_Annual_U.S._Equity_Review_Presentation.pdf) supplies fund and Russell 1000 Value figures in benchmark_context.csv. Index returns do not include ETF fees. These sponsor figures are kept separate from the vendor series. The DODGX 2024 discrepancy can change the sign of its very small one-year difference versus this index; do not mix the two sources to make a precise skill claim. A matched monthly style benchmark and a matched SPY sponsor checkpoint remain open research items.
