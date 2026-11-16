"""Explicit synthetic Web fixture generation using actual public Research + HTTP DTOs.

Run from repository root with .venv/bin/python. Does not touch real caches or Demo.
"""
import sys
from pathlib import Path
from datetime import timedelta
from dataclasses import replace

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'market_research/tests'))
from calendar_spread_fixtures import Services, DAY, AFTER  # noqa: E402
from market_research.descriptive.cases import futures_calendar_spread as case  # noqa: E402
from ui_http.products.futures_calendar_spread.schemas import DailyResponse  # noqa: E402
from ui_http.products.calendar_spread_relative_value.projection import historical_response  # noqa: E402


def save(feature, name, result):
    target = ROOT / 'ui_web/src/features' / feature / 'testing' / f'{name}.json'
    target.write_text(result.model_dump_json() + '\n')


def generate():
    for name, delta in [('daily', 0), ('closed', 1), ('empty', 0), ('excluded', 0)]:
        day = DAY + timedelta(days=delta)
        s = Services(day, day)
        if name == 'empty':
            s.set_rows([])
        if name == 'excluded':
            s.set_rows([replace(row, close=0.0) if row.contract_code == 'IM2410.CFX' else row for row in s.futures.records])
        r = case.query_daily_spreads(s.product, day, calendar_service=s, futures_service=s)
        save('futures_calendar_spread', name, DailyResponse.model_validate({
            'case': r.case, 'definition_version': r.definition_version, 'request': r.request,
            'day': r.day, 'accounting': r.accounting, 'source_context': r.source_context,
        }))
    for n in [0, 1, 29, 30]:
        if n == 0:
            start, end = DAY + timedelta(days=1), AFTER
        else:
            end = DAY
            start = end
            count = 0
            while count < n:
                start -= timedelta(days=1)
                if start.weekday() < 5:
                    count += 1
        s = Services(start, end)
        r = case.query_historical_relative_value('IM', start, end, histogram_edges=(-.1, 0, .1), calendar_service=s, futures_service=s)
        save('calendar_spread_relative_value', f'history{n}', historical_response(r))
    for name in ['nohist', 'currentclosed', 'currentexcluded', 'matchingempty']:
        end = DAY + timedelta(days=1) if name == 'currentclosed' else DAY
        start = DAY - timedelta(days=40 if name == 'matchingempty' else 1)
        s = Services(start, end)
        if name == 'currentexcluded':
            s.set_rows([replace(row, close=0.0) if row.trade_date == end and row.contract_code == 'IM2410.CFX' else row for row in s.futures.records])
        if name == 'matchingempty':
            s.set_rows([row for row in s.futures.records if row.trade_date < DAY - timedelta(days=28) or row.trade_date == end])
        r = case.query_historical_relative_value('IM', start, end, calendar_service=s, futures_service=s)
        save('calendar_spread_relative_value', name, historical_response(r))

    for metric in ['signed_spread', 'annualized_point_spread']:
        start, end = DAY - timedelta(days=2), DAY
        services = Services(start, end)
        r = case.query_historical_relative_value('IM', start, end, metric=metric, calendar_service=services, futures_service=services)
        save('calendar_spread_relative_value', metric, historical_response(r))


if __name__ == '__main__':
    generate()
