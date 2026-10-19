"""Build candidates from original-vintage Yahoo JSON, without changing inputs.

Run: python prepare_data.py --output-dir work/prepared
Original files must match data/sources.json; a new download is a new vintage.
"""
import argparse
import calendar
import csv
from datetime import date, datetime
import hashlib
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
TICKERS = ['SEQUX', 'DODGX', 'SPY']
MONTHS = [(2014, 12)] + [(year, month) for year in range(2015, 2025) for month in range(1, 13)]


def monthly_from_chart(payload, ticker):
    chart = payload['chart']
    if chart.get('error') or not chart.get('result') or len(chart['result']) != 1:
        raise ValueError('Expected one successful Yahoo chart result.')
    series = chart['result'][0]
    if series['meta'].get('symbol') != ticker:
        raise ValueError(f'Unexpected symbol for {ticker}.')
    timezone = series['meta'].get('exchangeTimezoneName')
    if timezone != 'America/New_York':
        raise ValueError(f'Unexpected exchange timezone: {timezone}.')
    timestamps = series['timestamp']
    prices = series['indicators']['adjclose'][0]['adjclose']
    if len(prices) != len(timestamps) or timestamps != sorted(set(timestamps)):
        raise ValueError('Timestamps must be unique, ordered and aligned with adjusted closes.')
    selected = {}
    for stamp, price in zip(timestamps, prices):
        observed = datetime.fromtimestamp(stamp, ZoneInfo(timezone)).date()
        key = (observed.year, observed.month)
        if key in MONTHS:
            if key in selected and observed <= selected[key][0]:
                raise ValueError('Duplicate or unordered daily observations.')
            selected[key] = (observed, price)
    audit = []
    for year, month in MONTHS:
        key = (year, month)
        if key not in selected:
            raise ValueError(f'Missing price month: {year}-{month:02}.')
        observed, price = selected[key]
        month_end = date(year, month, calendar.monthrange(year, month)[1])
        if (month_end - observed).days > 4:
            raise ValueError(f'Stale last observation: {observed} for {month_end}.')
        if price is None or not isinstance(price, (int, float)) or not math.isfinite(price) or price <= 0:
            raise ValueError(f'Invalid selected adjusted close for {ticker}, {month_end}.')
        audit.append({'ticker': ticker, 'month_end': month_end.isoformat(),
                      'observed_date': observed.isoformat(), 'adjusted_close': price})
    returns = [audit[i]['adjusted_close'] / audit[i-1]['adjusted_close'] - 1 for i in range(1, len(audit))]
    if any(not math.isfinite(r) or not -1 < r < 1 for r in returns):
        raise ValueError('Candidate returns do not satisfy the fixed-sample unit checks.')
    return returns, audit


def prepare(root, output_dir):
    sources = {row['id']: row for row in json.loads((root / 'data/sources.json').read_text(encoding='utf-8'))}
    returns, dates = {}, []
    for ticker in TICKERS:
        source = sources[f'yahoo_{ticker}']
        path = root / source['path']
        if not path.exists():
            raise FileNotFoundError(f'Original-vintage source missing: {path}. No published inputs were changed.')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != source['sha256']:
            raise ValueError(f'Source vintage/hash mismatch: {path}. Review a new vintage separately.')
        returns[ticker], audit = monthly_from_chart(json.loads(raw), ticker)
        dates.extend(audit)
    with (root / 'data/monthly_returns.csv').open(newline='', encoding='utf-8') as f:
        published = list(csv.DictReader(f))
    expected_dates = [date(y, m, calendar.monthrange(y, m)[1]).isoformat() for y, m in MONTHS[1:]]
    if [row['date'] for row in published] != expected_dates:
        raise ValueError('Published input dates do not match the fixed sample.')
    differences = [abs(returns[t][i] - float(row[t])) for i, row in enumerate(published) for t in TICKERS]
    report = {'maximum_absolute_return_difference': max(differences),
              'matches_published_within_1e_10': max(differences) <= 1e-10,
              'stale_guard': 'Last observation within four calendar days of month-end; not a full exchange calendar.'}
    targets = [output_dir / name for name in ['monthly_returns_candidate.csv', 'selected_prices.csv', 'comparison.json']]
    if any(path.exists() for path in targets):
        raise FileExistsError('Choose an output directory without existing candidate files.')
    if output_dir.resolve() == (root / 'data').resolve():
        raise ValueError('Candidate outputs must be separate from published data inputs.')
    output_dir.mkdir(parents=True, exist_ok=True)
    with targets[0].open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(['date', *TICKERS])
        for i, observed in enumerate(expected_dates):
            writer.writerow([observed, *[f'{returns[t][i]:.12f}' for t in TICKERS]])
    with targets[1].open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['ticker','month_end','observed_date','adjusted_close'], lineterminator='\n')
        writer.writeheader()
        writer.writerows(dates)
    targets[2].write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    try:
        prepare(ROOT, args.output_dir)
    except (ValueError, FileNotFoundError, FileExistsError) as error:
        parser.exit(1, f'{error}\n')
