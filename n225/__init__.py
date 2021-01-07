"""n225 - Get compositions and josuu."""

__version__ = "0.1.17"
__author__ = "fx-kirin <fx.kirin@gmail.com>"
__all__ = [
    "get_compositions",
    "get_all_stock_codes",
    "calculate_n225_price",
    "get_daily_n225_data_from_nikkei",
]

import csv
import datetime
import functools
import os
import warnings
from pathlib import Path

import jpholiday


def get_compositions(date):
    return _get_compositions(date.year, date.month, date.day)


def _read_init_n225_csv(date=None):
    n225_dict = {"stocks": {}}
    init_csv_path = Path(__file__).parent / "data/initial_n225.csv"
    with init_csv_path.open() as f:
        csv_obj = csv.reader(f)
        from_date = next(csv_obj)[1].strip()
        from_date = datetime.datetime.strptime(from_date, "%Y-%m-%d").date()
        if date is not None and date < from_date:
            raise NotImplementedError(f"Not implemnted n225 list before {from_date}")
        n225_dict["josuu"] = float(next(csv_obj)[1].strip())
        next(csv_obj)
        for row in csv_obj:
            n225_dict["stocks"][row[0].strip()] = row[1].strip()
    return n225_dict


def _get_compositions(year, month, day):
    date = datetime.date(year, month, day)
    n225_dict = _read_init_n225_csv(date)

    csv_path = Path(__file__).parent / "data/n225.csv"
    with csv_path.open() as f:
        csv_obj = csv.reader(f)
        next(csv_obj)
        for row in csv_obj:
            mod_date = datetime.datetime.strptime(row[0].strip(), "%Y-%m-%d").date()
            if mod_date > date:
                break
            remove_stock = row[1].strip()
            add_stock = row[2].strip()
            minashi = row[3].strip()
            josuu = row[4].strip()
            del n225_dict["stocks"][remove_stock]
            n225_dict["stocks"][add_stock] = minashi
            n225_dict["josuu"] = float(josuu)

    assert len(n225_dict["stocks"]) == 225
    return n225_dict


def get_all_stock_codes():
    n225_dict = _read_init_n225_csv()
    stock_codes = set()
    stock_codes.update(n225_dict["stocks"].keys())

    csv_path = Path(__file__).parent / "data/n225.csv"
    with csv_path.open() as f:
        csv_obj = csv.reader(f)
        next(csv_obj)
        for row in csv_obj:
            add_stock = row[2].strip()
            stock_codes.add(add_stock)
    return stock_codes


def calculate_n225_price(date, stock_price_dict):
    n225_dict = get_compositions(date)
    sum_ = 0

    for stock_code, minashi in n225_dict["stocks"].items():
        minashi = eval(minashi)
        sum_ += stock_price_dict[stock_code] * 50 / minashi
    return sum_ / n225_dict["josuu"]


def get_daily_n225_data_from_nikkei():
    try:
        import pandas as pd
    except ImportError:
        warnings.warn("You need to install pandas before using this function.")
        raise
    nikkei_df = pd.read_csv(
        "https://indexes.nikkei.co.jp/nkave/historical/nikkei_stock_average_daily_jp.csv",
        encoding="ms932",
    )
    nikkei_df = nikkei_df[:-1]
    nikkei_df.index = pd.to_datetime(nikkei_df["データ日付"], format="%Y/%m/%d")
    del nikkei_df["データ日付"]
    return nikkei_df
