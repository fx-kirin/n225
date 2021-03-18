"""n225 - Get compositions and josuu."""
import csv
import datetime
import functools
import io
import os
import re
import time
import warnings
from pathlib import Path

import jpholiday
import kanilog
import mojimoji
import numpy as np
import pandas as pd
import pdftotext
import tabula
from kanirequests import KaniRequests, open_html_in_browser
from nth_weekday import get_nth_weekday
from urlpath import URL

from .jpx import get_last_business_date, get_next_business_date

__version__ = "0.1.22"
__author__ = "fx-kirin <fx.kirin@gmail.com>"
__all__ = [
    "get_compositions",
    "get_all_stock_codes",
    "calculate_n225_price",
    "get_daily_n225_data_from_nikkei",
    "get_futures_sq_dates",
]


logger = kanilog.get_module_logger(__file__, 1)


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
    if date < datetime.date(2019, 7, 1):
        raise NotImplementedError(f"Date must be after 2019-07-01")

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


def download_kouseimeigara_pdfs(download_path=None):
    if download_path is None:
        pdf_path = Path(__file__).parent / "pdf/kousei"
        pdf_path.mkdir(exist_ok=True, parents=True)
    idx = 1
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0",
        "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
        "Connection": "keep-alive",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "max-age=0",
    }

    session = KaniRequests(headers=headers)
    while True:
        is_found = False
        url = f"https://indexes.nikkei.co.jp/nkave/newsroom?evt=10016&idxtag=00001&page={idx}"
        logger.info("Opening %s", url)
        result = session.get(url)
        root_path = URL(result.url)
        links = []
        rows = result.html.find("div.row")
        for row in rows:
            for a in row.find("a"):
                if "銘柄" in a.text and "pdf" in a.attrs["href"]:
                    date_text = row.find("div.list-text")[0].text.replace(".", "-")
                    file_name = "%s_%s.pdf" % (date_text, a.text)
                    pdf_file_path = pdf_path / file_name
                    if not pdf_file_path.exists():
                        logger.info("Downloading %s", file_name)
                        url = root_path.joinpath(a.attrs["href"])
                        result = session.get(url)
                        time.sleep(1)
                        pdf_file_path.write_bytes(result.content)
                        is_found = True
        if not is_found:
            break
        logger.info("Go next page.")
        idx += 1


def download_josuu_pdfs(download_path=None):
    if download_path is None:
        pdf_path = Path(__file__).parent / "pdf/josuu"
        pdf_path.mkdir(exist_ok=True, parents=True)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0",
        "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
        "Connection": "keep-alive",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "max-age=0",
    }

    session = KaniRequests(headers=headers)
    idx = 1
    while True:
        is_found = False
        url = f"https://indexes.nikkei.co.jp/nkave/newsroom?evt=10022&idxtag=00001&page={idx}"
        logger.info("Opening %s", url)
        result = session.get(url)
        root_path = URL(result.url)
        links = []
        rows = result.html.find("div.row")
        for row in rows:
            for a in row.find("a"):
                if "除数" in a.text and "pdf" in a.attrs["href"]:
                    date_text = row.find("div.list-text")[0].text.replace(".", "-")
                    file_name = "%s_%s.pdf" % (date_text, a.text)
                    pdf_file_path = pdf_path / file_name
                    if not pdf_file_path.exists():
                        logger.info("Downloading %s", file_name)
                        url = root_path.joinpath(a.attrs["href"])
                        result = session.get(url)
                        time.sleep(1)
                        pdf_file_path.write_bytes(result.content)
                        is_found = True
        if not is_found:
            break
        logger.info("Go next page.")
        idx += 1

    idx = 1
    while True:
        is_found = False
        url = (
            f"https://indexes.nikkei.co.jp/nkave/newsroom?evt=&idxtag=00001&page={idx}"
        )
        logger.info("Opening %s", url)
        result = session.get(url)
        root_path = URL(result.url)
        links = []
        rows = result.html.find("div.row")
        for row in rows:
            for a in row.find("a"):
                if "除数" in a.text and "pdf" in a.attrs["href"]:
                    date_text = row.find("div.list-text")[0].text.replace(".", "-")
                    file_name = "%s_%s.pdf" % (date_text, a.text)
                    pdf_file_path = pdf_path / file_name
                    if not pdf_file_path.exists():
                        logger.info("Downloading %s", file_name)
                        url = root_path.joinpath(a.attrs["href"])
                        result = session.get(url)
                        time.sleep(1)
                        pdf_file_path.write_bytes(result.content)
                        is_found = True
        if not is_found:
            break
        logger.info("Go next page.")
        idx += 1


def parse_pdfs(download_path=None):
    if download_path is None:
        pdf_path = Path(__file__).parent / "pdf/kousei"

    pdf_files = reversed(sorted(list(pdf_path.glob("*.pdf"))))
    output_df = pd.DataFrame(columns=["Remove", "Add", "Minashi"])

    for pdf_file in pdf_files:
        logger.info("parsing %s", pdf_file.name)
        try:
            doc_date = datetime.datetime.strptime(
                pdf_file.name[0:10], "%Y-%m-%d"
            ).date()
            if doc_date < datetime.date(2019, 7, 1):
                logger.warning("Not implemented yet before 2019-7-1.")
                break
            if "日経平均株価等の構成銘柄の取り扱いについて" in pdf_file.name:
                with pdf_file.open("rb") as f:
                    pdf = pdftotext.PDF(f)
                text = "\n".join(list(pdf))
                text = text.replace("\n", "")
                remove = re.search(r"「.+?(\d+)）」", text).group(1)

                span1 = re.search(r"１．日経平均株価", text).span()
                span2 = re.search(r"２．", text).span()
                content = text[span1[1]: span2[0]].replace(" ", "")
                minashi = mojimoji.zen_to_han(
                    re.search(r"みなし額面は([0-9０-９/／]+)", content).group(1)
                )
                add = re.search(r"「.+?（(\d+)）」を採用", content).group(1).strip()
                date = re.search("([０-９0-9]+)月([０-９0-9]+)日", content)
                month = int(mojimoji.zen_to_han(date.group(1)))
                day = int(mojimoji.zen_to_han(date.group(2)))
                target_date = datetime.date(doc_date.year, month, day)
                if target_date < doc_date:
                    target_date = datetime.date(doc_date.year + 1, month, day)
                if jpholiday.is_holiday(target_date):
                    target_date = get_next_business_date(target_date)
                output_df = output_df.append(
                    pd.DataFrame(
                        [[remove, add, minashi]],
                        index=[target_date],
                        columns=["Remove", "Add", "Minashi"],
                    )
                )
            elif "日経平均株価の銘柄定期入れ替え等について" in pdf_file.name:
                dfs = tabula.read_pdf(pdf_file)
                if len(dfs) == 2:
                    df = dfs[0]
                    for idx, row in df.iterrows():
                        add = row["コード"]
                        remove = row["コード.1"]
                        minashi = re.search(r"\(([0-9/]+)\)", row["採用銘柄"]).group(1)
                        date = re.search("([０-９0-9]+)月([０-９0-9]+)日", row["実施日"])
                        month = int(mojimoji.zen_to_han(date.group(1)))
                        day = int(mojimoji.zen_to_han(date.group(2)))
                        target_date = datetime.date(doc_date.year, month, day)
                        if target_date < doc_date:
                            target_date = datetime.date(doc_date.year + 1, month, day)
                        if jpholiday.is_holiday(target_date):
                            target_date = get_next_business_date(target_date)
                        output_df = output_df.append(
                            pd.DataFrame(
                                [[remove, add, minashi]],
                                index=[target_date],
                                columns=["Remove", "Add", "Minashi"],
                            )
                        )

                    with pdf_file.open("rb") as f:
                        pdf = pdftotext.PDF(f)
                    text = "\n".join(list(pdf))
                    span = re.search(r"．.*株式", text).span()
                    content = text[span[1]:]
                    date = re.search("([０-９0-9]+)月([０-９0-9]+)日", content)
                    month = int(mojimoji.zen_to_han(date.group(1)))
                    day = int(mojimoji.zen_to_han(date.group(2)))
                    target_date = datetime.date(doc_date.year, month, day)
                    if target_date < doc_date:
                        target_date = datetime.date(doc_date.year + 1, month, day)
                    if jpholiday.is_holiday(target_date):
                        target_date = get_next_business_date(target_date)

                    split_df = dfs[1]
                    for idx, row in split_df.iterrows():
                        add = row["コード"]
                        remove = row["コード"]
                        minashi = re.search(r"([0-9/]+)円", row["新みなし額面"]).group(1)
                        output_df = output_df.append(
                            pd.DataFrame(
                                [[remove, add, minashi]],
                                index=[target_date],
                                columns=["Remove", "Add", "Minashi"],
                            )
                        )
                else:
                    logger.warning("Not parsed")
            elif "日経平均株価の銘柄定期入れ替えについて" in pdf_file.name:
                dfs = tabula.read_pdf(pdf_file)
                if len(dfs) == 1:
                    df = dfs[0]
                    df = df.dropna(axis=1)
                    for column in df.columns:
                        if " " in column:
                            name1, name2 = column.split(" ", 1)
                            splited = df[column].str.split(" ", 1, expand=True)
                            if name1 in df:
                                name1 += ".1"
                            if name2 in df:
                                name2 += ".1"
                            df[[name1, name2]] = splited
                    for idx, row in df.iterrows():
                        add = row["コード"].strip()
                        remove = row["コード.1"].strip()
                        minashi = re.search(r"\(([0-9/]+)\)", row["採用銘柄"]).group(1)
                        date = re.search("([０-９0-9]+)月([０-９0-9]+)日", row["実施日"])
                        month = int(mojimoji.zen_to_han(date.group(1)))
                        day = int(mojimoji.zen_to_han(date.group(2)))
                        target_date = datetime.date(doc_date.year, month, day)
                        if target_date < doc_date:
                            target_date = datetime.date(doc_date.year + 1, month, day)
                        if jpholiday.is_holiday(target_date):
                            target_date = get_next_business_date(target_date)
                        output_df = output_df.append(
                            pd.DataFrame(
                                [[remove, add, minashi]],
                                index=[target_date],
                                columns=["Remove", "Add", "Minashi"],
                            )
                        )
                else:
                    logger.warning("Not parsed")
            else:
                logger.warning("Not parsed")
        except:
            logger.warning("Not parsed")

    output_df["Josuu"] = np.nan
    if download_path is None:
        pdf_path = Path(__file__).parent / "pdf/josuu"
    pdf_files = reversed(sorted(list(pdf_path.glob("*.pdf"))))

    for pdf_file in pdf_files:
        doc_date = datetime.datetime.strptime(pdf_file.name[0:10], "%Y-%m-%d").date()
        target_date = get_next_business_date(doc_date)
        josuu = re.search(r"([0-9\.]+)", pdf_file.name[12:]).group(1)
        if target_date in output_df.index:
            output_df.loc[target_date, "Josuu"] = josuu
    output_df.bfill(inplace=True)
    output_df.index.name = "Date"
    output_df.sort_index(inplace=True)
    output_df.to_csv(Path(__file__).parent / "data/n225.csv")


def get_futures_sq_dates(today):
    sq_dates = []
    for year in range(2020, today.year + 2):
        for month in range(3, 13, 3):
            sq_date = get_nth_weekday(4, year, month, 1)
            while True:
                if not jpholiday.is_holiday(sq_date):
                    break
                sq_date = get_last_business_date(sq_date)
            while True:
                if not jpholiday.is_holiday(sq_date):
                    break
                sq_date = get_last_business_date(sq_date)
            sq_dates.append(sq_date)
    return sq_dates
