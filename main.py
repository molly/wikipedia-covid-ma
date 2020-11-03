# Copyright (c) 2020 Molly White
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
import zipfile
from datetime import date, timedelta

from constants import *
from infobox_and_barchart import create_infobox_and_barchart
from cases_by_category_table import create_cases_by_category_table
from cases_by_county_table import create_cases_by_county_table
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
    args = parser.parse_args()
    dev = args.dev
    nomanual = args.no_manual
    today = args.date if isinstance(args.date, date) else date.fromisoformat(args.date)
    fromdate = date.fromisoformat(args.fromdate) if args.fromdate else None
    return {
        "nomanual": nomanual,
        "dev": dev,
        "today": today,
        "fromdate": fromdate,
    }


def fetch_data(args):
    """Fetch the data for today and extract the necessary files."""
    if args["dev"] and len(os.listdir(TMP_DIR)) > 0:
        # If we're in dev mode and the files exist, we don't have to fetch them again.
        return

    url_date = args["today"].strftime(URL_DATE_FMT).lower()
    url = URL.format(url_date)
    r = requests.get(url, headers=REQUEST_HEADER)
    if r.status_code == 200:
        zipfile_path = os.path.join(TMP_DIR, url_date + ".zip")
        with open(zipfile_path, "wb+") as f:
            f.write(r.content)
        print("Downloaded today's data to {}.zip".format(url_date))
        with zipfile.ZipFile(zipfile_path, "r") as zipObj:
            zipObj.extractall(TMP_DIR)
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


def get_manual_data(today, last_thursday):
    """Some data isn't included in the CSVs but can be pulled from other reports."""
    print(
        "From the weekly report: https://www.mass.gov/doc/weekly-covid-19-public-health"
        "-report-{}/download".format(last_thursday.strftime(URL_DATE_FMT).lower())
    )
    quar_released = input(
        "Total individuals who have completed monitoring (no longer in quarantine): "
    )
    quar_total = input("Total individuals subject to quarantine: ")
    recoveries = input("Total cases released from isolation: ")
    return {
        "quar_total": int(quar_total),
        "quar_released": int(quar_released),
        "recoveries": int(recoveries),
    }


def set_up_folders(args):
    """Ensure the tmp and output directories are in place and cleared as needed."""
    if not os.path.exists(TMP_DIR):
        # Create the tmp directory if it doesn't exist
        os.mkdir(TMP_DIR)
    elif not args["dev"]:
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


def get_last_thursday(today):
    """Get the date of the most recent Thursday (including today's date, if today is
    a Thursday. This is used to refer to the weekly data, which is published every
    Thursday."""
    todays_day_of_week = today.weekday()
    if todays_day_of_week == 3:
        return today
    else:
        offset = (todays_day_of_week - 3) % 7
        return today - timedelta(days=offset)


def run():
    args = parse_args()
    date_range = get_date_range(args["today"], args["fromdate"])
    last_thursday = get_last_thursday(args["today"])
    set_up_folders(args)
    fetch_data(args)
    manual_data = (
        None if args["nomanual"] else get_manual_data(args["today"], last_thursday)
    )
    create_infobox_and_barchart(date_range, args, last_thursday, manual_data)
    create_cases_by_category_table(date_range, last_thursday, manual_data)
    create_cases_by_county_table(date_range)
    create_daily_county_table(
        args["today"], manual_data["recoveries"] if manual_data else None
    )
    create_statistics_graphs(args)


if __name__ == "__main__":
    run()
