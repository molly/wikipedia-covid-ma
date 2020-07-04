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
from datetime import timedelta
from constants import DAY_FMT, TMP_DIR


def get_data(date_range):
    # Also grab data for the day before, so we can calculate % change
    prev_day = date_range[0] - timedelta(days=1)
    data = {date.strftime(DAY_FMT): {} for date in [prev_day] + date_range}
    with open(os.path.join(TMP_DIR, "Cases.csv"), "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["Date"] in data:
                pos_total = int(row["Positive Total"])
                pos_new = int(row["Positive New"])
                prob_total = int(row["Probable Total"])
                prob_new = int(row["Probable New"])
                data[row["Date"]] = {
                    "total_cases": pos_total + prob_total,
                    "total_cases_new": pos_new + prob_new,
                    "presumptive_cases": prob_total,
                    "confirmed_cases": pos_total,
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
            data[day_str]["total_cases_new"] / data[prev_day_str]["total_cases"] * 100,
            1,
        )
        data[day_str]["perc_new_tests"] = round(
            data[day_str]["testing_new"] / data[prev_day_str]["testing_total"] * 100, 1
        )
        data[day_str]["perc_new_deaths"] = round(
            data[day_str]["deaths_new"] / data[prev_day_str]["deaths_total"] * 100, 1
        )


def create_cases_by_category_table(date_range, args):
    data = get_data(date_range)
    calculate_columns(date_range, data)
    print("hi")
