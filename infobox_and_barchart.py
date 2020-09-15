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
from datetime import date, timedelta
from constants import *


def get_data(date_range, today):
    prev_day = date_range[0] - timedelta(days=1)
    today_str = today.strftime(DAY_FMT)
    data = {
        d.strftime(DAY_FMT): {
            "confirmed_cases": None,
            "probable_cases": None,
            "total_cases": None,
            "deaths": None,
        }
        for d in [prev_day] + date_range
    }

    with open(os.path.join(TMP_DIR, "Cases.csv"), "r") as cases_csv:
        reader = csv.DictReader(cases_csv)
        for row in reader:
            if row["Date"] in data:
                confirmed = int(row["Positive Total"])
                probable = int(row["Probable Total"])
                data[row["Date"]]["confirmed_cases"] = confirmed
                data[row["Date"]]["probable_cases"] = probable
                data[row["Date"]]["total_cases"] = confirmed + probable
    with open(os.path.join(TMP_DIR, "DeathsReported.csv"), "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["Date"] in data:
                data[row["Date"]]["deaths"] = int(row["DeathsConfTotal"]) + int(
                    row["DeathsProbTotal"]
                )
    return data


def create_infobox(data, today, last_wednesday):
    lines = []
    today_str = today.strftime(DAY_FMT)
    today_citation = today.strftime(CITATION_DATE_FORMAT)
    asof = "{{{{as of|{}|alt=as of {}}}}}".format(
        today.strftime("%Y|%m|%d"), today.strftime(AS_OF_ALT_FMT)
    )
    asof_last_wednesday = "{{{{as of|{}|alt=as of {}}}}}".format(
        last_wednesday.strftime("%Y|%m|%d"), last_wednesday.strftime(AS_OF_ALT_FMT)
    )

    lines.append(
        '| confirmed_cases = {:,} ({:,} total cases) {}<ref name="MDPH-Cases">{{{{cite web |'
        " title = COVID-19 Response Reporting | url = https://www.mass.gov/info-details"
        "/covid-19-response-reporting | website = Massachusetts Department of Public "
        "Health | access-date = {}}}}}</ref>".format(
            data[today_str]["confirmed_cases"],
            data[today_str]["total_cases"],
            asof,
            today_citation,
        )
    )
    lines.append(
        "| hospitalized_cases = CURRENT_HOSP (current)<br>CUMULATIVE_HOSP (cumulative) <br>{}"
        '<ref name="MDPH-Cases"/>'.format(asof)
    )
    lines.append("| critical_cases  = CURRENT_ICU (current) {}".format(asof))
    lines.append("| ventilator_cases = CURRENT_VENT (current) {}".format(asof))
    lines.append(
        '| recovery_cases = RECOVERED {}<ref group="note" name="MDPH-Weekly-{}"/>'.format(
            asof_last_wednesday, last_wednesday.strftime("%m-%d")
        )
    )
    lines.append(
        '| deaths          = {:,} {}<ref name="MDPH-Cases"/>'.format(
            data[today_str]["deaths"], asof
        )
    )
    return "\n".join(lines)


def create_bar_chart(data, date_range):
    rows = []
    for date in date_range:
        prev_day = (date - timedelta(days=1)).strftime(DAY_FMT)

        date_str = date.strftime(DAY_FMT)
        perc_case_change = (
            (data[date_str]["total_cases"] - data[prev_day]["total_cases"])
            / data[prev_day]["total_cases"]
        ) * 100
        sign = "" if perc_case_change < 0 else "+"
        row = (
            "{date};{deaths};RECOVERIES;{conf};{prob};;{total:,};{sign}"
            "{change:.2f}%".format(
                date=date.strftime(BAR_CHART_FMT),
                deaths=data[date_str]["deaths"],
                conf=data[date_str]["confirmed_cases"],
                prob=data[date_str]["probable_cases"],
                total=data[date_str]["total_cases"],
                sign=sign,
                change=perc_case_change,
            )
        )
        rows.append(row)
    return "\n".join(rows)


def write_file(infobox, bar_chart):
    with open(os.path.join(OUT_DIR, "infobox_and_barchart.txt"), "w+") as f:
        f.write(infobox + "\n\n\n" + bar_chart)


def create_infobox_and_barchart(date_range, args, last_wednesday):
    data = get_data(date_range, args["today"])
    infobox = create_infobox(data, args["today"], last_wednesday)
    bar_chart = create_bar_chart(data, date_range)
    write_file(infobox, bar_chart)
