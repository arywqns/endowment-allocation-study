# Working through the project

This optional appendix works through the historical case: whether a hypothetical $5 billion endowment had sufficient evidence to replace passive US equity with Sequoia Fund or Dodge & Cox Stock Fund. The return comparison and funding stress are separate exercises. Numbers in the examples describe the shipped assumptions; the generated memo displays current scenario facts.

In `analyze.py`, start with `compound_return`, `drawdown`, `performance_table`, `allocation_table`, and `liquidity_stress`. Other functions handle data and output.

## Read the returns

There are 120 monthly observations per investment, January 2015-December 2024. A return of `0.02` means 2%: `100 * 1.02 = $102`.

Cached adjusted-close returns include distributions and embedded fund expenses. Adding dividends or subtracting expenses again counts them twice. Investigate missing months rather than filling them. See [data/README.md](data/README.md) for sources and unresolved sponsor checks.

## Four measures

### Compound annual return

Multiply the monthly growth factors, then express that growth as an annual rate:

```text
growth = product of (1 + monthly return)
annual return = growth ** (12 / number of months) - 1
```

If $100 becomes $121 in 24 months, the annual return is `1.21 ** (12/24) - 1 = 10%`. A 10% gain followed by a 10% loss leaves $99, which shows why averaging returns is different from compounding them.

### Annualized volatility

Volatility measures how much returns vary around their average:

```text
annualized volatility = sample standard deviation of monthly returns * sqrt(12)
```

For returns of 1%, 2%, and 3%, the average is 2%. Squared deviations sum to `0.0002`. Divide by `3 - 1` and take the square root: monthly volatility is 1%. Multiplying by `sqrt(12)` gives about 3.46% annually. In pandas, `ddof=1` selects the sample calculation.

Annualization assumes variation scales with time. Volatility counts gains and losses, not just the worst loss.

### Maximum drawdown

Drawdown measures the fall from the highest investment value reached so far:

```text
drawdown = current value / previous peak - 1
maximum drawdown = most negative drawdown
```

Include the initial $100 as a possible peak. If it falls to $90 immediately, drawdown is -10%. If it later reaches $120 and falls to $96, drawdown is -20%: the deeper loss.

Month-end data miss losses that occur and recover within a month.

### Correlation with SPY

Correlation measures how closely two return series move together around their averages. It ranges from -1 to +1.

If SPY returns are 1%, 2%, and 3%, while a manager returns 2%, 4%, and 6%, their correlation is +1. The pattern matches exactly, but the manager's variation is twice as large. High correlation does not mean identical returns or risk, and it does not establish skill.

For February-March 2020 and calendar 2022, the script compounds only the selected months. For example, -10% followed by +5% gives `0.90 * 1.05 - 1 = -5.5%`.

## Replacing passive equity

The US-equity allocation is 20% of $5 billion, or $1 billion. Manager investments come out of that amount:

| Share of endowment | Manager investment | US-equity sleeve replaced |
|---|---:|---:|
| 0% | $0 | 0% |
| 2.5% | $125 million | 12.5% |
| 5% | $250 million | 25% |

The policy funding budget stays at 20%; its composition changes. A fund's foreign holdings can change underlying geographic exposure, even when its budget is classified as US equity.

```text
monthly contribution = allocation weight * (manager return - SPY return)
annualized contribution = 12 * average monthly contribution
```

Suppose a 5% manager allocation earns 2% while SPY earns 1%. The contribution is `0.05 * (0.02 - 0.01) = 0.0005`, or **0.05 percentage points** of endowment return: 5 basis points.

An average monthly contribution of 0.05 percentage points annualizes to 0.60 percentage points. This is an arithmetic contribution, not a compounded endowment return. It assumes constant weights and omits the other assets' histories, actual rebalancing, and trading costs.

SPY measures the investment given up. Dodge & Cox's sponsor also reports returns against Russell 1000 Value; the memo includes that material context. No factor regression or matched monthly style analysis is present, so these calculations cannot establish manager skill.

## Cash and investment value

NAV means net asset value: assets minus liabilities. Cash is one asset within NAV.

| Transaction | Effect |
|---|---|
| New spending of $10m, paid immediately | Cash and NAV fall $10m |
| Pay a $10m capital call | Cash falls $10m, private NAV rises $10m, commitments fall $10m; total NAV stays the same |
| Sell $10m of bonds | Bonds fall $10m, cash rises $10m; NAV stays the same |
| Sell $10m of equity at a 5% haircut | Equity falls $10m, cash rises $9.5m, NAV falls $0.5m |

To receive $10m in cash from equity, sell `10 / 0.95 = $10.526m`.

The stress first reduces public equity by 50%, bonds by 10%, hedge funds by 25%, and private markets by 40%. Cash is unchanged. There are no further returns or private distributions over the following year.

Spending is `$250m / 12 = $20.83m` monthly. Calls are `$800m / 12 = $66.67m` monthly in the 80% case, or `$1bn / 12 = $83.33m` in the 100% sensitivity.

Bonds are sold first, then equity, to pay obligations and target $125m cash. Obligations take priority over the reserve. Hedge funds and private assets cannot be sold; borrowing is unavailable. Unpaid amounts become arrears instead of negative cash and trigger a funding-failure flag; penalties and actual fund-default outcomes are not modeled. The additional 5% equity realization deduction is a stress assumption after the market loss, not an estimate of ordinary trading costs.

```text
ending NAV = previous NAV - valuation losses - new spending obligations - equity sale costs
```

Valuation losses occur only in month one. Unpaid spending creates a liability when due. Paying it later does not count the expense twice. Calls transfer value; they are not spending.

Private weight is `private NAV / total NAV`. If private assets stay at $100 while other assets fall from $100 to $50, private weight rises from 50% to 66.7%. In this project's initial shock, private weight instead falls from 35% to about 31.9%: private NAV becomes $1,050m and total NAV $3,287.5m. Later calls increase private assets while spending and sale costs reduce total NAV.

## Read the output

The charts show historical compounding, month-end drawdowns, and hypothetical asset sales. They do not forecast performance. The stress cannot rank manager downside protection.

Trace one month in `results/liquidity_monthly.csv`, then use `results/liquidity_sensitivities.csv` to isolate call size, reserve, realization deduction and call timing. Gross total sales include bonds and equity: the shipped 80% case's $263.2m is equity-only, within $938.2m total. Half those equity sales arise from preserving the cash target.

For experiments, change assumptions atop `analyze.py` in a disposable copy, predict the result and rerun. The memo's numerical descriptions use current assumptions, while this appendix and README describe the shipped case. Review the investment judgment and fixed-case regression expectations after a deliberate case change. Retrospective selection, benchmark fit, sponsor discrepancies, and missing current terms limit the recommendation.

## Questions to work through

1. **What decision does the project study?** Explain the hypothetical endowment, managers, SPY funding source, and allocation sizes.
2. **Why not choose the highest historical return?** Discuss losses, benchmark fit, uncertainty, and missing evidence about teams, fees, capacity, and operations.
3. **What does incremental contribution mean?** Calculate the 5% example and explain why it is not the whole endowment's compound return.
4. **Why are capital calls different from spending?** Follow cash, private NAV, and commitments, then explain how valuable assets can coexist with a cash shortage.
5. **What did you contribute, and what would you check next?** Describe the calculations and evidence you have reviewed, and identify information that could change the recommendation.
