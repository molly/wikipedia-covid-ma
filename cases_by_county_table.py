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

import os
from constants import *
from openpyxl import load_workbook

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


def get_data(xlsx_path, date_range):
    data = {date.strftime(DAY_FMT): {} for date in date_range}
    wb = load_workbook(filename=xlsx_path, data_only=True)
    sheet = wb["County_Daily"]
    for ind, row in enumerate(sheet.rows):
        if ind == 0:
            continue
        dt = row[0].value
        try:
            date_str = dt.strftime(DAY_FMT)
        except AttributeError:
            continue
        if dt and dt.date() in date_range:
            county = row[1].value
            if county in ["Dukes", "Nantucket", "Dukes and Nantucket"]:
                county = "Dukes and Nantucket"
            if county not in data[date_str]:
                data[date_str][county] = {"count": 0, "deaths": 0}
            if row[3].value:
                data[date_str][county]["count"] += int(row[3].value)
            if row[5].value:
                data[date_str][county]["deaths"] += int(row[5].value)
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


def create_cases_by_county_table(xlsx_path, date_range):
    data = get_data(xlsx_path, date_range)
    create_table(date_range, data)
