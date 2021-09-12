# Copyright (c) 2020-2021 Molly White
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import os
import requests
from datetime import date, timedelta

from constants import *

from infobox_and_barchart import create_infobox_and_barchart
from cases_by_county_daily_table import create_daily_county_table
from statistics import create_statistics_graphs


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--no-manual",
        help="skip manually inputting extra data (will result in placeholders in output"
        + "files that will need to be replaced)",
        action="store_true",
    )
    parser.add_argument(
        "--dev",
        help="developer mode, avoids making HTTP requests when possible",
        action="store_true",
    )
    parser.add_argument(
        "-fromdate",
        nargs="?",
        default=None,
        type=str,
        help="For tables where historical data is preserved, output previous days' "
        "data starting from this date. Format YYYY-MM-DD.",
    )
    parser.add_argument(
        "-date",
        nargs="?",
        default=date.today(),
        type=str,
        help="The date on which to gather data. Defaults to today's date, but if "
        "today's data has not been published you probably want to use yesterday's "
        "date. Format YYYY-MM-DD.",
    )
    parser.add_argument(
        "-url",
        nargs="?",
        default=None,
        type=str,
        help="A custom URL from which to download data for this date. Useful if the "
        "state makes a typo in the URL and it can't be automatically generated as "
        "normal.",
    )
    args = parser.parse_args()
    dev = args.dev
    nomanual = args.no_manual
    today = args.date if isinstance(args.date, date) else date.fromisoformat(args.date)
    fromdate = date.fromisoformat(args.fromdate) if args.fromdate else None
    url = args.url
    return {
        "nomanual": nomanual,
        "dev": dev,
        "today": today,
        "fromdate": fromdate,
        "url": url,
    }


def fetch_data(url, xlsx_path, is_dev):
    """Fetch the data for today and extract the necessary files."""
    if is_dev and len(os.listdir(TMP_DIR)) > 0:
        # If we're in dev mode and the files exist, we don't have to fetch them again.
        return

    r = requests.get(url, headers=REQUEST_HEADER)
    if r.status_code == 200:
        with open(xlsx_path, "wb+") as f:
            f.write(r.content)
        print("Downloaded today's data to {}".format(xlsx_path))
    elif r.status_code == 404:
        raise Exception(
            "Data for this date was not found. This is probably because today's data "
            "hasn't been published yet.",
            url,
        )
    else:
        raise Exception(
            "Something went wrong when trying to download today's data",
            r.status_code,
            r.reason,
        )


def set_up_folders(is_dev):
    """Ensure the tmp and output directories are in place and cleared as needed."""
    if not os.path.exists(TMP_DIR):
        # Create the tmp directory if it doesn't exist
        os.mkdir(TMP_DIR)
    elif not is_dev:
        # Clear out the tmp directory if it does exist and we're not in dev mode
        files = os.listdir(TMP_DIR)
        if len(files) != 0:
            [os.remove(os.path.join(TMP_DIR, f)) for f in files]

    if not os.path.exists(OUT_DIR):
        # Create the output directory if it doesn't exist
        os.mkdir(OUT_DIR)
    else:
        # Clear out the output directory if it does exist
        files = os.listdir(OUT_DIR)
        if len(files) != 0:
            [os.remove(os.path.join(OUT_DIR, f)) for f in files]


def get_date_range(today, fromdate):
    """Gets an array of dates for which we wish to collect data."""
    dates = []
    if fromdate:
        d = fromdate
        while d != today:
            dates.append(d)
            d = d + timedelta(days=1)
    dates.append(today)
    return dates


def run():
    args = parse_args()
    today = args["today"]
    weekday = today.weekday()
    if weekday > 4:
        # Today is a weekend day, and no data is published on weekends. Set today to previous Friday.
        today = args["today"] - timedelta(days=abs(4 - weekday))
        print(
            "Today is a weekend. Because data isn't published on weekends, getting data for "
            + today.strftime(DAY_FMT)
        )

    date_range = get_date_range(today, args["fromdate"])
    url_date = today.strftime(URL_DATE_FMT).lower()
    xlsx_path = os.path.join(TMP_DIR, url_date + ".xlsx")

    if args["url"]:
        url = args["url"]
    else:
        url = URL.format(url_date)

    set_up_folders(args["dev"])
    fetch_data(url, xlsx_path, args["dev"])

    create_infobox_and_barchart(xlsx_path, url, today, date_range, args)
    create_daily_county_table(xlsx_path, today)
    create_statistics_graphs(xlsx_path, today)


if __name__ == "__main__":
    run()
