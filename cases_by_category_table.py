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
from datetime import date, timedelta
from constants import *
from excel import get_excel_data_for_date_range, safe_lookup


def get_data(xlsx_path, date_range):
    # Also grab data for the day before, so we can calculate % change
    prev_day = date_range[0] - timedelta(days=1)
    date_range_with_prev_day = [prev_day] + date_range
    data = {d.strftime(DAY_FMT): {} for d in date_range_with_prev_day}

    case_data = get_excel_data_for_date_range(
        xlsx_path, date_range_with_prev_day, "Cases (Report Date)"
    )
    for row in case_data.values():
        date_str = row["Date"].strftime(DAY_FMT)
        pos_total = int(row["Positive Total"])
        pos_new = int(row["Positive New"])
        prob_total = int(row["Probable Total"])
        prob_new = int(row["Probable New"])
        data[date_str] = {
            "total_cases": pos_total,
            "total_cases_new": pos_new,
            "probable_cases": prob_total,
            "probable_cases_new": prob_new,
        }

    testing_data = get_excel_data_for_date_range(
        xlsx_path, date_range_with_prev_day, "Testing2 (Report Date)"
    )
    for row in testing_data.values():
        date_str = row["Date"].strftime(DAY_FMT)
        data[date_str]["testing_total"] = int(row["Molecular Total"])
        data[date_str]["testing_new"] = int(row["Molecular New"])

    hosp_data = get_excel_data_for_date_range(
        xlsx_path, date_range_with_prev_day, "Hospitalization from Hospitals"
    )
    for d in date_range_with_prev_day:
        if d in hosp_data:
            data[d.strftime(DAY_FMT)]["hospitalized"] = safe_lookup(
                hosp_data[d], "Total number of COVID patients in hospital today", -1,
            )

    deaths_reported_data = get_excel_data_for_date_range(
        xlsx_path, date_range_with_prev_day, "DeathsReported (Report Date)"
    )
    for row in deaths_reported_data.values():
        date_str = row["Date"].strftime(DAY_FMT)
        data[date_str]["deaths_total"] = int(row["DeathsConfTotal"]) + int(
            row["DeathsProbTotal"]
        )
        data[date_str]["deaths_new"] = int(row["DeathsConfNew"]) + int(
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


def create_row(d, data, last_thursday, manual_data, recoveries):
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
        recoveries if recoveries else ""
    )
    row += '| style="border-left: 2px solid #888;" |{}\n'.format(
        manual_data["quar_total"]
        if manual_data and d >= last_thursday
        else "TOTAL QUARANTINED"
    )
    row += "|{}\n".format(
        manual_data["quar_released"]
        if manual_data and d >= last_thursday
        else "RELEASED FROM QUARANTINE"
    )
    return row


def create_table(date_range, data, last_thursday, manual_data, recoveries):
    rows = []
    prev_day_str = (date_range[0] - timedelta(days=1)).strftime(DAY_FMT)
    rows.append(
        "{} hospitalized: {}\n\n".format(
            prev_day_str, data[prev_day_str]["hospitalized"]
        ),
    )
    for d in date_range:
        date_str = d.strftime(DAY_FMT)
        row = create_row(
            d, data[date_str], last_thursday, manual_data, recoveries[date_str]
        )
        rows.append(row)
    with open(os.path.join(OUT_DIR, "cases_by_category.txt"), "w+") as f:
        f.write("".join(rows))


def create_cases_by_category_table(
    xlsx_path, date_range, last_thursday, manual_data, recoveries
):
    data = get_data(xlsx_path, date_range)
    calculate_columns(date_range, data)
    create_table(date_range, data, last_thursday, manual_data, recoveries)
