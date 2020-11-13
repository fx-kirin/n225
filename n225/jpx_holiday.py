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


def is_market_open(date):
    if date.month == 1 and date.day <= 3:
        pass
    elif (not jpholiday.is_holiday(date)) and (date.weekday() < 5):
        return date
