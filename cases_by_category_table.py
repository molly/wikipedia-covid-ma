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
import re
from datetime import date, timedelta
from constants import *
from utils import comma_separate


def get_data(date_range):
    # Also grab data for the day before, so we can calculate % change
    prev_day = date_range[0] - timedelta(days=1)
    data = {d.strftime(DAY_FMT): {} for d in [prev_day] + date_range}
    with open(os.path.join(TMP_DIR, "Cases.csv"), "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["Date"] in data:
                pos_total = int(row["Positive Total"])
                pos_new = int(row["Positive New"])
                prob_total = int(row["Probable Total"])
                prob_new = int(row["Probable New"])
                data[row["Date"]] = {
                    "total_cases": pos_total,
                    "total_cases_new": pos_new,
                    "probable_cases": prob_total,
                    "probable_cases_new": prob_new,
                }
    with open(os.path.join(TMP_DIR, "Testing2.csv"), "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["Date"] in data:
                data[row["Date"]]["testing_total"] = int(row["Molecular Total"])
                data[row["Date"]]["testing_new"] = int(row["Molecular New"])
    with open(
        os.path.join(TMP_DIR, "Hospitalization from Hospitals.csv"), "r"
    ) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["Date"] in data:
                data[row["Date"]]["hospitalized"] = int(
                    row["Total number of COVID patients in hospital today"]
                )
    with open(os.path.join(TMP_DIR, "DeathsReported.csv"), "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["Date"] in data:
                data[row["Date"]]["deaths_total"] = int(row["DeathsConfTotal"]) + int(
                    row["DeathsProbTotal"]
                )
                data[row["Date"]]["deaths_new"] = int(row["DeathsConfNew"]) + int(
                    row["DeathsProbNew"]
                )
    return data


def calculate_columns(date_range, data):
    # Calculate any of the calculated columns (% change, etc.)
    for day in date_range:
        prev_day = day - timedelta(days=1)
        day_str = day.strftime(DAY_FMT)
        prev_day_str = prev_day.strftime(DAY_FMT)
        data[day_str]["perc_change_cases"] = round(
            (data[day_str]["total_cases_new"] + data[day_str]["probable_cases_new"])
            / (data[prev_day_str]["total_cases"] + data[prev_day_str]["probable_cases"])
            * 100,
            1,
        )
        data[day_str]["perc_new_tests"] = round(
            data[day_str]["testing_new"] / data[prev_day_str]["testing_total"] * 100, 1
        )
        data[day_str]["perc_new_deaths"] = round(
            data[day_str]["deaths_new"] / data[prev_day_str]["deaths_total"] * 100, 1
        )


def prefix_number(val):
    return "+" + str(val) if val > 0 else val


def create_row(d, data, refname, last_wednesday, manual_data):
    pretty_date = d.strftime(CITATION_DATE_FORMAT)
    url = CITATION_URL.format(d.strftime(URL_DATE_FMT).lower())
    title = CITATION_TITLE.format(pretty_date)
    pretty_today = date.today().strftime(CITATION_DATE_FORMAT)

    row = '|-\n| style="text-align:left;" | {}\n'.format(d.strftime("%B&nbsp;%-d"))
    row += '| style="border-left: 2px solid #888;" |{}\n'.format(
        data["total_cases"] + data["probable_cases"]
    )
    row += "| {}\n".format(
        prefix_number(data["total_cases_new"] + data["probable_cases_new"])
    )
    row += "| {}%\n".format(prefix_number(data["perc_change_cases"]))
    row += "| {}\n".format(data["probable_cases"])
    row += "| {}\n".format(data["total_cases"])
    row += '| style="border-left: 2px solid #888;" |\n|\n|\n|\n'
    row += '| style="border-left: 2px solid #888;" |{}\n'.format(data["testing_total"])
    row += "| {}\n".format(prefix_number(data["testing_new"]))
    row += "| {}%\n".format(prefix_number(data["perc_new_tests"]))
    row += '| style="border-left: 2px solid #888;" |{}\n'.format(
        data["hospitalized"] if "hospitalized" in data else ""
    )
    row += "|\n|\n"
    row += '| style="border-left: 2px solid #888;" |{}\n'.format(data["deaths_total"])
    row += "| {}\n".format(prefix_number(data["deaths_new"]))
    row += "| {}%\n".format(prefix_number(data["perc_new_deaths"]))
    row += '| style="border-left: 2px solid #888;" |{}\n'.format(
        manual_data["recoveries"]
        if manual_data and d >= last_wednesday
        else "RECOVERIES"
    )
    row += '| style="border-left: 2px solid #888;" |{}\n'.format(
        manual_data["quar_total"]
        if manual_data and d >= last_wednesday
        else "TOTAL QUARANTINED"
    )
    row += '|{}\n| style="border-left: 2px solid #888;" |'.format(
        manual_data["quar_released"]
        if manual_data and d >= last_wednesday
        else "RELEASED FROM QUARANTINE"
    )
    row += '<ref group="note" name="{}">'.format(refname)
    row += "{{{{Cite web|url={}|title={}|last=|first=|".format(url, title)
    row += "date={}|website=Massachusetts Department of Public ".format(pretty_date)
    row += "Health|url-status=live|archive-url=|archive-date=|"
    row += "access-date={}}}}}</ref>".format(pretty_today)
    row += '<ref group="note" name="MDPH-Weekly-{:02d}-{:02d}"/>\n'.format(
        last_wednesday.month, last_wednesday.day
    )
    return row


def get_next_refname(refname):
    if not refname:
        return ""
    match = re.match(r":(\d+)", refname)
    if match:
        return ":{}".format(int(match.group(1)) - 1)
    return ""


def create_table(date_range, data, base_refname, last_wednesday, manual_data):
    rows = []
    refname = base_refname
    prev_day_str = (date_range[0] - timedelta(days=1)).strftime(DAY_FMT)
    rows.append(
        "\n\n\n{} hospitalized: {}".format(
            prev_day_str, data[prev_day_str]["hospitalized"]
        ),
    )
    for d in reversed(date_range):
        date_str = d.strftime(DAY_FMT)
        row = create_row(d, data[date_str], refname, last_wednesday, manual_data)
        rows.insert(0, row)
        refname = get_next_refname(refname)
    with open(os.path.join(OUT_DIR, "cases_by_category.txt"), "w+") as f:
        f.write("".join(rows))


def create_cases_by_category_table(date_range, args, last_wednesday, manual_data):
    data = get_data(date_range)
    calculate_columns(date_range, data)
    create_table(date_range, data, args["refname"], last_wednesday, manual_data)
