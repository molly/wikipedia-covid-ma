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
from datetime import date

from constants import *
from deaths_table import create_deaths_table


def parse_args():
    parser = argparse.ArgumentParser()
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
    today = args.date if isinstance(args.date, date) else date.fromisoformat(args.date)
    fromdate = date.fromisoformat(args.fromdate) if args.fromdate else None
    return dev, today, fromdate


def fetch_data(today, dev):
    """Fetch the data for today and extract the necessary files."""
    if dev and len(os.listdir(TMP_DIR)) > 0:
        # If we're in dev mode and the files exist, we don't have to fetch them again.
        return

    url_date = today.strftime("%B-%-d-%Y")
    r = requests.get(URL.format(url_date))
    if r.status_code == 200:
        zipfile_path = os.path.join(TMP_DIR, url_date + ".zip")
        with open(zipfile_path, "wb+") as f:
            f.write(r.content)
        print("Downloaded today's data to {}.zip".format(url_date))
        files_to_extract = [
            "Age.csv",
            "CasesByDate.csv",
            "County.csv",
            "DateofDeath.csv",
        ]
        with zipfile.ZipFile(zipfile_path, "r") as zipObj:
            for filename in files_to_extract:
                zipObj.extract(filename, TMP_DIR)
                print("Extracted {}".format(filename))

    elif r.status_code == 404:
        print(
            "Data for this date was not found. This is probably because today's data "
            "hasn't been published yet."
        )
        return None
    else:
        raise Exception(
            "Something went wrong when trying to download today's data",
            r.status_code,
            r.reason,
        )


def set_up_folders(dev):
    """Ensure the tmp and output directories are in place and cleared as needed."""
    if not os.path.exists(TMP_DIR):
        # Create the tmp directory if it doesn't exist
        os.mkdir(TMP_DIR)
    elif not dev:
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


def run():
    dev, today, start = parse_args()
    set_up_folders(dev)
    fetch_data(today, dev)
    create_deaths_table()


if __name__ == "__main__":
    run()
