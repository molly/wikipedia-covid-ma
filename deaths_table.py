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

import csv
import os
from constants import *

HEADERS = [
    {"key": "80+", "header": "Above 80"},
    {"key": "70-79", "header": "70–79"},
    {"key": "60-69", "header": "60–69"},
    {"key": "50-59", "header": "50–59"},
    {"key": "40-49", "header": "40–49"},
    {"key": "30-39", "header": "30-39"},
    {"key": "20-29", "header": "20-29"},
    {"key": "0-19", "header": "0-19"},
    {"key": "Unknown", "header": "n/d"},
]


def parse_data(today):
    """Gather the needed data from the CSV"""
    with open(os.path.join(TMP_DIR, "Age.csv")) as csvfile:
        reader = csv.DictReader(csvfile)
        today_str = today.strftime("%-m/%-d/%Y")
        data = {}
        for row in reader:
            if row["Date"] == today_str:
                data[row["Age"]] = {
                    "cases": int(row["Cases"]),
                    "deaths": int(row["Deaths"]),
                }
        return data


def create_row(header, row_data, total_cases, total_deaths):
    perc_cases = round(row_data["cases"] / total_cases * 100, 1)
    perc_deaths = round(row_data["deaths"] / total_deaths * 100, 1)
    lethality = round(row_data["deaths"] / row_data["cases"] * 100, 1)
    row = "! {}\n".format(header["header"])
    row += "|{:,}\n".format(row_data["cases"])
    row += "|({})\n".format(perc_cases)
    row += "|{:,}\n".format(row_data["deaths"])
    row += "|({})\n".format(perc_deaths)
    row += "|({})\n|-\n".format(lethality)
    return row


def create_wikitable(data, total_cases, total_deaths, args):
    """Create the wikitable in the expected format."""
    today = args["today"]
    rows = []
    for header in HEADERS:
        rows.append(create_row(header, data[header["key"]], total_cases, total_deaths))
    footer = '! colspan="2" | All\n'
    footer += "|''''{:,}'''\n".format(total_cases)
    footer += "|'''(100.0)'''\n"
    footer += "|''''{:,}'''\n".format(total_deaths)
    footer += "|'''(100.0)'''\n"
    footer += "|'''({})'''\n".format(round(total_deaths / total_cases * 100, 1))
    footer += '|-\n| style="text-align:left;" colspan="7" | '
    footer += "{{{{center|{{{{As of|{}|{:02d}|{:02d}|df=US}}}}".format(
        today.year, today.month, today.day
    )
    footer += '<ref group="note" name="{}"/>}}}}\n|}}'.format(args["refname"])
    rows.append(footer)

    with open(os.path.join(OUT_DIR, "deaths.txt"), "w+") as f:
        f.write("".join(rows))


def create_deaths_table(args):
    data = parse_data(args["today"])
    total_cases = 0
    total_deaths = 0
    for row in data.values():
        total_cases += row["cases"]
        total_deaths += row["deaths"]
    create_wikitable(data, total_cases, total_deaths, args)
