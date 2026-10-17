# Endowment Allocation Study

Should a hypothetical $5 billion university endowment replace part of its passive US equity allocation with Sequoia or Dodge & Cox?

This Python study compares SEQUX, DODGX and SPY over 2015–2024, measures the effect of different manager allocations, and follows spending and capital calls through a year of market stress. The calculations are in one script: [analyze.py](analyze.py).

The case recommendation is to **keep the passive allocation and continue diligence**. Both funds trailed SPY over the sample with higher volatility and deeper month-end drawdowns. Benchmark fit matters: Dodge & Cox lost less than SPY in 2022. The [investment memo](IC_MEMO.md) explains the tradeoffs and missing evidence.

![Growth of $100, 2015–2024](results/growth_of_100.png)

## Run the analysis

Download the repository using **Code → Download ZIP** and extract it, or clone it with Git. Open a terminal in the project folder. Python 3.14 was used for verification.

**Windows (PowerShell)**

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe analyze.py
.\.venv\Scripts\python.exe verify.py
```

**macOS / Linux**

```bash
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python analyze.py
.venv/bin/python verify.py
```

If Python is missing, install it from [python.org](https://www.python.org/downloads/) and reopen the terminal. On Windows, `python -m venv .venv` also works if `python --version` reports 3.14. No environment activation is required.

Dependency installation needs internet access. After setup, both scripts run offline. `analyze.py` saves six CSV tables, three charts and the investment memo. `verify.py` checks input hashes, return calculations, allocation contributions and monthly cash accounts against the saved tables.

## What the analysis measures

The sample contains 120 monthly returns per investment, January 2015–December 2024. The four measures are compound annual return, annualized volatility, maximum drawdown and correlation with SPY. February–March 2020 and calendar 2022 are also examined separately.

Manager positions are 0%, 2.5% and 5% of endowment NAV, funded from passive US equity. A 5% position is $250 million, or 25% of the US-equity sleeve. Both 0% alternatives share the same starting point.

```text
monthly contribution = allocation weight * (manager return - SPY return)
annualized contribution = 12 * average monthly contribution
```

This is an arithmetic contribution in percentage points of NAV. It assumes constant weights and omits rebalancing costs. It is not the compounded return of the whole endowment. SPY represents the investment given up; evaluating a manager's style may require a different benchmark.

![Drawdowns, 2015–2024](results/drawdowns.png)

## Cash needs under stress

| Item | Assumption |
|---|---|
| Starting assets | $5bn: 20% US equity, 10% international equity, 15% bonds, 15% hedge funds, 35% private markets, 5% cash |
| Obligations | $250m annual spending; $1bn unfunded commitments |
| Cash target | $125m |
| Immediate losses | Public equity 50%; bonds 10%; hedge funds 25%; private markets 40% |
| Capital calls | 80% of initial commitments; 100% in the sensitivity |
| Timing | Spending and calls spread evenly across 12 months |
| Other cash flows | No private distributions or further investment returns |
| Sales | Bonds first, then public equity; equity proceeds are 95% of gross value sold |
| Restrictions | No hedge-fund redemptions, private-asset sales or borrowing |

The 80% call case requires **$938.2 million in gross asset sales**. Calling 100% requires **$210.5 million more**. Both scenarios pay all obligations and finish with $125 million in cash, but private assets make up a larger share of the remaining portfolio.

Paid calls move cash into private NAV and reduce commitments. Spending and sale costs reduce total NAV. Obligations take priority over the cash target. Unpaid obligations are tracked if liquid assets run out; unpaid spending is a liability when due. The model treats all public equity alike and does not predict manager-specific losses.

![Monthly asset sales under stress](results/monthly_asset_sales.png)

## Files

| File | Purpose |
|---|---|
| [analyze.py](analyze.py) | Assumptions, calculations, charts and memo |
| [verify.py](verify.py) | Checks of the data, arithmetic and saved results |
| [IC_MEMO.md](IC_MEMO.md) | Recommendation and supporting evidence |
| [LEARNING_GUIDE.md](LEARNING_GUIDE.md) | Worked examples and explanations |
| [data/](data/) | Two input tables and source provenance |
| [results/](results/) | Performance, regimes, allocations, monthly liquidity, liquidity summary and sponsor comparisons; three charts |

CSV rates are decimals (`0.05` means 5%); dollar amounts are dollars. Assumptions are near the top of `analyze.py`. The saved results and checks describe the documented case; changing assumptions requires reviewing them together.

## Sources and limits

Returns use distribution-adjusted prices; fund expenses are already reflected in the underlying NAV. Dividends and expenses are not counted again. Drawdowns use month-end values and include the initial investment as a possible peak.

The public copy includes the two input tables. [data/README.md](data/README.md) describes their construction; [data/sources.json](data/sources.json) preserves source URLs, retrieval dates and hashes. Original downloads are not bundled. The loader checks the two required tables and any original source files supplied locally. It rejects missing, duplicate or unsorted months and invalid returns. Hashes detect changed files, not economic accuracy.

Two vendor-versus-sponsor differences remain unresolved: Sequoia's ten-year CAGR differs by about −6.55 basis points annually, and Dodge & Cox's 2024 return differs by about −15.94 basis points. Returns are retained as observed. No archived SPY sponsor checkpoint is verified.

This is a historical case study with hypothetical allocations. The selection of surviving funds, hindsight, monthly sampling, benchmark fit and changes in teams or share classes limit its conclusions. Current vehicles, eligibility, fees, capacity, operations and full holdings need further research.
