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

import csv
import os
from constants import *

COUNTIES = [
    "Barnstable",
    "Berkshire",
    "Bristol",
    "Dukes and Nantucket",
    "Essex",
    "Franklin",
    "Hampden",
    "Hampshire",
    "Middlesex",
    "Norfolk",
    "Plymouth",
    "Suffolk",
    "Worcester",
    "Unknown",
]


def get_data(date_range):
    data = {date.strftime(DAY_FMT): {} for date in date_range}
    with open(
        os.path.join(TMP_DIR, "County.csv"), "r", encoding="utf-8-sig"
    ) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["Date"] in data:
                if row["County"] in ["Dukes", "Nantucket", "Dukes and Nantucket"]:
                    # Roll up Dukes & Nantucket data
                    county = "Dukes and Nantucket"
                else:
                    county = row["County"]

                if county not in data[row["Date"]]:
                    data[row["Date"]][county] = {"count": 0, "deaths": 0}

                if row["Total Confirmed Cases"]:
                    data[row["Date"]][county]["count"] += int(
                        row["Total Confirmed Cases"]
                    )
                if row["Total Probable and Confirmed Deaths"]:
                    data[row["Date"]][county]["deaths"] += int(
                        row["Total Probable and Confirmed Deaths"]
                    )
    return data


def create_row(d, data):
    row = '|-\n| style="text-align:left;" | {}\n'.format(d.strftime("%B&nbsp;%-d"))
    row += '| style="border-left: 2px solid #888;" '
    for county in COUNTIES:
        row += "| {}\n".format(data[county]["count"])
    row += '| style="border-left: 2px solid #888;" '
    for county in COUNTIES:
        row += "| {}\n".format(data[county]["deaths"])
    return row


def create_table(date_range, data):
    rows = []
    for d in date_range:
        date_str = d.strftime(DAY_FMT)
        rows.append(create_row(d, data[date_str]))
    with open(os.path.join(OUT_DIR, "cases_by_county.txt"), "w+") as f:
        f.write("".join(rows))


def create_cases_by_county_table(date_range):
    data = get_data(date_range)
    create_table(date_range, data)
