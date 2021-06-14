import datetime
from datetime import timedelta

import dateutil.parser
import jpholiday


class ExchangeClosed(jpholiday.registry.OriginalHoliday):
    def _is_holiday(self, date):
        if date.year == 2020 and date.month == 10 and date.day == 1:
            return True
        return False

    def _is_holiday_name(self, date):
        return "障害発生"


class Sanganichi(jpholiday.registry.OriginalHoliday):
    def _is_holiday(self, date):
        if date.month == 1 and date.day <= 3:
            return True
        return False

    def _is_holiday_name(self, date):
        return "正月三が日"


class Omisoka(jpholiday.registry.OriginalHoliday):
    def _is_holiday(self, date):
        if date.month == 12 and date.day == 31:
            return True
        return False

    def _is_holiday_name(self, date):
        return "大晦日"


def is_market_open(date):
    if jpholiday.is_holiday(date):
        return False
    if date.weekday() >= 5:
        return False
    return True


def get_next_business_date(date, days=1):
    next_bdate = date + timedelta(days=1)
    count = 0
    while True:
        if is_market_open(next_bdate):
            count += 1
            if days <= count:
                return next_bdate
        next_bdate = next_bdate + timedelta(days=1)


def get_last_business_date(date, days=1):
    next_bdate = date - timedelta(days=1)
    count = 0
    while True:
        if is_market_open(next_bdate):
            count += 1
            if days <= count:
                return next_bdate
        next_bdate = next_bdate - timedelta(days=1)


def get_shinagashi_nissu(date):
    borrow_date = get_next_business_date(date, 2)

    shinagashi_nissu = 1
    return_date = borrow_date + timedelta(days=1)
    for _ in range(30):
        if is_market_open(return_date):
            break
        shinagashi_nissu += 1
        return_date = return_date + timedelta(days=1)
    else:
        raise RuntimeError("Something Wrong.")
    return shinagashi_nissu


def get_stock_zaraba_filter(from_date, to_date, pandas_series):
    from_date, to_date = _parse_date_inputs(from_date, to_date)
    business_days = get_business_days(from_date, to_date)
    zaraba_filter = None
    for business_day in business_days:
        business_dt = datetime.datetime.fromordinal(business_day.toordinal())
        additional_filter = ((business_dt + timedelta(hours=9)) <= pandas_series.index) & (
            pandas_series.index < (business_dt + timedelta(hours=11, minutes=30))
        )
        additional_filter |= (
            (business_dt + timedelta(hours=12, minutes=30)) <= pandas_series.index
        ) & (pandas_series.index < (business_dt + timedelta(hours=15)))
        if zaraba_filter is None:
            zaraba_filter = additional_filter
        else:
            zaraba_filter = zaraba_filter | additional_filter
    return zaraba_filter


def get_business_days(from_date, to_date):
    from_date, to_date = _parse_date_inputs(from_date, to_date)
    current_date = from_date
    business_days = []
    if is_market_open(current_date):
        business_days.append(current_date)

    while True:
        current_date = get_next_business_date(current_date)
        if current_date <= to_date:
            business_days.append(current_date)
        else:
            return business_days


def _parse_date_inputs(from_date, to_date):
    if isinstance(from_date, str):
        from_date = dateutil.parser.parse(from_date)
    if isinstance(to_date, str):
        to_date = dateutil.parser.parse(to_date)
    if isinstance(from_date, datetime.datetime):
        from_date = from_date.date()
    if isinstance(to_date, datetime.datetime):
        to_date = to_date.date()
    return from_date, to_date
