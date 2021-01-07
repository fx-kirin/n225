import datetime

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
    next_bdate = date + datetime.timedelta(days=days)
    count = 0
    while True:
        if is_market_open(next_bdate):
            count += 1
            if days <= count:
                return next_bdate
        next_bdate = next_bdate + datetime.timedelta(days=1)


def get_last_business_date(date, days=1):
    next_bdate = date - datetime.timedelta(days=days)
    count = 0
    while True:
        if is_market_open(next_bdate):
            count += 1
            if days <= count:
                return next_bdate
        next_bdate = next_bdate - datetime.timedelta(days=1)


def get_shinagashi_nissu(date):
    borrow_date = get_next_business_date(date, 2)

    shinagashi_nissu = 1
    return_date = borrow_date + datetime.timedelta(days=1)
    for _ in range(30):
        if is_market_open(return_date):
            break
        shinagashi_nissu += 1
        return_date = return_date + datetime.timedelta(days=1)
    else:
        raise RuntimeError("Something Wrong.")
    return shinagashi_nissu
