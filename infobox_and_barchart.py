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
from constants import *
from excel import get_excel_data_for_date_range
from utils import comma_separate


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
    with open(os.path.join(TMP_DIR, "DeathsReported.csv"), "r") as deaths_csv:
        reader = csv.DictReader(deaths_csv)
        for row in reader:
            if row["Date"] in data:
                data[row["Date"]]["deaths"] = int(row["DeathsConfTotal"]) + int(
                    row["DeathsProbTotal"]
                )

    # Additional data for today only, for use in the article body
    with open(os.path.join(TMP_DIR, "Testing2.csv"), "r") as tests_csv:
        reader = csv.DictReader(tests_csv)
        for row in reader:
            if row["Date"] == today_str:
                data[today_str]["total_molecular_tests"] = int(
                    row["Molecular All Tests Total"]
                )
                data[today_str]["individual_molecular_tests"] = int(
                    row["Molecular Total"]
                )
                data[today_str]["antigen_tests"] = int(row["Antigen Total"])
    with open(os.path.join(TMP_DIR, "LTC Facilities.csv"), "r") as ltc_csv:
        reader = csv.DictReader(ltc_csv)
        for row in reader:
            if row["date"] == today_str:
                data[today_str]["ltc_deaths"] = int(row["Deaths Reported in LTCFs"])
                data[today_str]["ltc_cases"] = int(
                    row["Cases in Residents/Healthcare Workers of LTCFs"]
                )
                data[today_str]["ltc_facilities"] = int(row["facilities"])

    # For hospitalizations, the data from the previous day in the spreadsheet is
    # displayed for that day
    yesterday = today - timedelta(days=1)
    hosp_data = get_excel_data_for_date_range(
        "Hospitalization from Hospitals.xlsx", [yesterday]
    )
    data[today_str]["hosp_current"] = hosp_data[yesterday][
        "Total number of confirmed COVID patients in hospital today"
    ]
    data[today_str]["icu_current"] = hosp_data[yesterday]["Confirmed ICU"]
    data[today_str]["vent_current"] = hosp_data[yesterday]["Confirmed intubated"]

    return data


def create_infobox(data, today, recoveries):
    lines = []
    today_str = today.strftime(DAY_FMT)
    today_citation = today.strftime(CITATION_DATE_FORMAT)
    asof = "{{{{as of|{}|alt=as of {}}}}}".format(
        today.strftime("%Y|%m|%d"), today.strftime(AS_OF_ALT_FMT)
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
        '| hospitalized_cases = {} (current) {}<ref name="MDPH-Cases"/>'.format(
            data[today_str]["hosp_current"],
            asof,
        )
    )
    lines.append(
        "| critical_cases  = {} (current) {}".format(
            data[today_str]["icu_current"],
            asof,
        )
    )
    lines.append(
        "| ventilator_cases = {} (current) {}".format(
            data[today_str]["vent_current"],
            asof,
        )
    )
    lines.append(
        '| recovery_cases  = {} {}<ref name="MDPH-Cases"/>'.format(
            comma_separate(recoveries[today_str])
            if recoveries[today_str]
            else "RECOVERIES",
            asof,
        )
    )
    lines.append(
        '| deaths          = {:,} {}<ref name="MDPH-Cases"/>'.format(
            data[today_str]["deaths"], asof
        )
    )
    return "\n".join(lines)


def create_bar_chart(data, date_range, recoveries):
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
            "{date};{deaths};{recov};{conf};{prob};;{total:,};{sign}"
            "{change:.2f}%".format(
                date=date.strftime(BAR_CHART_FMT),
                deaths=data[date_str]["deaths"],
                recov=recoveries[date_str] if recoveries[date_str] else "RECOVERIES",
                conf=data[date_str]["confirmed_cases"],
                prob=data[date_str]["probable_cases"],
                total=data[date_str]["total_cases"],
                sign=sign,
                change=perc_case_change,
            )
        )
        rows.append(row)
    return "\n".join(rows)


def get_addl_info(data, today):
    today_str = today.strftime(DAY_FMT)
    today_url_fmt = today.strftime(URL_DATE_FMT).lower()
    today_citation_fmt = today.strftime(CITATION_DATE_FORMAT)
    addl = "Tests:\n\tMolecular: {:,} tests on {:,} individuals".format(
        data[today_str]["total_molecular_tests"],
        data[today_str]["individual_molecular_tests"],
    )
    addl += "\n\tAntigen: {:,}".format(data[today_str]["antigen_tests"])
    addl += (
        '\n\n<ref name="MDPH-current-day">{{{{Cite web|url=https://www.mass.gov/doc/'
        "covid-19-dashboard-{url_date}/download|title=COVID-19 Dashboard – {cite_date}"
        "|date={cite_date}|website=Massachusetts Department of Public Health|"
        "url-status=live|access-date={cite_date}}}}}</ref>".format(
            url_date=today_url_fmt, cite_date=today_citation_fmt
        )
    )
    addl += "\n\nLong-term care:\n\tDeaths: {:,}".format(data[today_str]["ltc_deaths"])
    addl += "\n\tCases among residents & workers: {:,}".format(
        data[today_str]["ltc_cases"]
    )
    addl += "\n\tFacilities with >=1 case: {:,}".format(
        data[today_str]["ltc_facilities"]
    )
    addl += "\n\t% of deaths that are LTC residents: {:.0f}%".format(
        data[today_str]["ltc_deaths"] / data[today_str]["deaths"] * 100
    )
    return addl


def write_file(infobox, bar_chart, addl_info_for_article_body):
    with open(os.path.join(OUT_DIR, "infobox_and_barchart.txt"), "w+") as f:
        f.write(infobox + "\n\n\n" + bar_chart + "\n\n\n" + addl_info_for_article_body)


def create_infobox_and_barchart(date_range, args, recoveries):
    data = get_data(date_range, args["today"])
    infobox = create_infobox(data, args["today"], recoveries)
    bar_chart = create_bar_chart(data, date_range, recoveries)
    addl_info_for_article_body = get_addl_info(data, args["today"])
    write_file(infobox, bar_chart, addl_info_for_article_body)
