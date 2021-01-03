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
from datetime import date, timedelta
from excel import get_excel_data_for_date_range, safe_lookup


def create_date_list(today):
    # All charts start on February 26
    start = date(2020, 2, 26)
    dates = [start]
    d = start
    while d != today:
        d = d + timedelta(days=1)
        dates.append(d)
    return dates


def safe_sum(v1, v2):
    """Sum two integers (string type) accounting for the possibility that one or both
    is missing; returns an integer."""
    if v1:
        if v2:
            return int(v1) + int(v2)
        else:
            return int(v1)
    if v2:
        return int(v2)
    return 0


def create_cases_charts(date_list):
    date_str_list = [d.strftime(DAY_FMT) for d in date_list[:-1]]
    data = {d: {} for d in date_str_list}

    case_data = get_excel_data_for_date_range("CasesByDate.xlsx", date_list)
    for d in date_list:
        data[d.strftime(DAY_FMT)] = {
            "total": safe_lookup(case_data[d], "Positive Total", -1),
            "new": safe_lookup(case_data[d], "Positive New", -1),
        }

    out_str = "CASES DATES:\n"
    out_str += ", ".join([d.strftime(STATISTICS_DAY_FMT) for d in date_list])
    out_str += "\n\nTOTAL CASES:\n"
    out_str += ", ".join([str(data[date_str]["total"]) for date_str in date_str_list])
    out_str += "\n\nNEW CASES:\n"
    out_str += ", ".join([str(data[date_str]["new"]) for date_str in date_str_list])
    with open(os.path.join(OUT_DIR, "statistics.txt"), "w+") as outfile:
        outfile.write(out_str)


def create_deaths_charts(date_list):
    # There is a two day lag in death data
    deaths_date_list = date_list[:-2]
    date_str_list = [d.strftime(DAY_FMT) for d in deaths_date_list]
    data = {d: {} for d in date_str_list}

    death_data = get_excel_data_for_date_range("DateofDeath.xlsx", date_list)
    for d in date_list:
        if d in death_data:
            data[d.strftime(DAY_FMT)] = {
                "total": safe_lookup(death_data[d], "Confirmed Total", 0),
                "new": safe_lookup(death_data[d], "Confirmed Deaths", 0),
            }

    # Zero out the days going back to February 26
    for d in date_str_list:
        if "total" not in data[d]:
            data[d] = {"total": 0, "new": 0}

    out_str = "\n\n\n\n\nDEATH DATES:\n"
    out_str += ", ".join([d.strftime(STATISTICS_DAY_FMT) for d in deaths_date_list])
    out_str += "\n\nTOTAL DEATHS:\n"
    out_str += ", ".join([str(data[date_str]["total"]) for date_str in date_str_list])
    out_str += "\n\nNEW DEATHS:\n"
    out_str += ", ".join([str(data[date_str]["new"]) for date_str in date_str_list])
    with open(os.path.join(OUT_DIR, "statistics.txt"), "a") as outfile:
        outfile.write(out_str)


def create_statistics_graphs(args):
    date_list = create_date_list(args["today"])
    create_cases_charts(date_list)
    create_deaths_charts(date_list)
