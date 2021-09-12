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

import re
import os
from datetime import date, timedelta
from constants import *
from excel import get_excel_data_for_date_range


def get_data(xlsx_path, date_range, today):
    prev_day = date_range[0] - timedelta(days=1)
    today_str = today.strftime(DAY_FMT)
    full_date_range = [prev_day] + date_range
    data = {
        d.strftime(DAY_FMT): {
            "confirmed_cases": None,
            "probable_cases": None,
            "total_cases": None,
            "deaths": None,
        }
        for d in full_date_range
    }

    case_data = get_excel_data_for_date_range(
        xlsx_path, full_date_range, "Cases (Report Date)"
    )
    for date, row in case_data.items():
        date_str = date.strftime(DAY_FMT)
        data[date_str] = {
            "confirmed_cases": None,
            "probable_cases": None,
            "total_cases": None,
        }
        if row:
            confirmed = int(row["Positive Total"])
            probable = int(row["Probable Total"])
            data[date_str] = {
                "confirmed_cases": confirmed,
                "probable_cases": probable,
                "total_cases": confirmed + probable,
            }

    deaths_data = get_excel_data_for_date_range(
        xlsx_path, full_date_range, "DeathsReported (Report Date)"
    )
    for date, row in deaths_data.items():
        date_str = date.strftime(DAY_FMT)
        if row:
            data[date_str]["deaths"] = int(row["DeathsConfTotal"]) + int(
                row["DeathsProbTotal"]
            )
        else:
            data[date_str]["deaths"] = None

    # Additional data for today only, for use in the article body
    testing_data = get_excel_data_for_date_range(
        xlsx_path, [today], "Testing2 (Report Date)"
    )
    data[today_str]["total_molecular_tests"] = int(
        testing_data[today]["Molecular All Tests Total"]
    )
    data[today_str]["individual_molecular_tests"] = int(
        testing_data[today]["Molecular Total"]
    )
    data[today_str]["antigen_tests"] = int(testing_data[today]["Antigen Total"])

    # For hospitalizations and rolling averages, the data from previous days is the most
    # recent
    yesterday = today - timedelta(days=1)
    day_before_yesterday = today - timedelta(days=2)

    case_data = get_excel_data_for_date_range(
        xlsx_path, [yesterday], "CasesByDate (Test Date)"
    )
    data[today_str]["rolling_avg_cases"] = int(
        round(case_data[yesterday]["7-day confirmed case average"])
    )

    death_data = get_excel_data_for_date_range(
        xlsx_path, [day_before_yesterday], "DateofDeath"
    )
    data[today_str]["rolling_avg_deaths"] = int(
        round(death_data[day_before_yesterday]["7-day confirmed death average"])
    )

    hosp_data = get_excel_data_for_date_range(
        xlsx_path, [yesterday], "Hospitalization from Hospitals"
    )
    data[today_str]["hosp_current"] = hosp_data[yesterday][
        "Total number of COVID patients in hospital today"
    ]
    data[today_str]["icu_current"] = hosp_data[yesterday]["ICU"]
    data[today_str]["vent_current"] = hosp_data[yesterday]["Intubated"]

    return data


def create_infobox(data, today, manual_data):
    lines = []
    today_str = today.strftime(DAY_FMT)
    today_citation = today.strftime(CITATION_DATE_FORMAT)
    asof = "{{{{as of|{}|alt=as of {}}}}}".format(
        today.strftime("%Y|%m|%d"), today.strftime(AS_OF_ALT_FMT)
    )
    asof_vaccine = "{{{{as of|{}|alt=as of {}}}}}".format(
        manual_data["as_of"].strftime("%Y|%m|%d"),
        manual_data["as_of"].strftime(AS_OF_ALT_FMT),
    )
    vaccine_citation = (
        '<ref name="CDC-vaccines">{{{{cite web | title = COVID-19 State Profile Report '
        "- Massachusetts | url = https://healthdata.gov/Community/COVID-19-State-Profile-"
        "Report-Massachusetts/j75q-tgps | website = Healthdata.gov | publisher = [[U.S. Department"
        " of Health & Human Services]] | date = {} | access-date = {} }}}}</ref>".format(
            manual_data["as_of"].strftime(CITATION_DATE_FORMAT), today_citation
        )
    )

    lines.append(
        '| confirmed_cases   = {:,} (cumulative) {}<ref name="MDPH-Cases">{{{{cite web |'
        " title = COVID-19 Response Reporting | url = https://www.mass.gov/info-details"
        "/covid-19-response-reporting | website = Massachusetts Department of Public "
        "Health | access-date = {}}}}}</ref>".format(
            data[today_str]["confirmed_cases"],
            asof,
            today_citation,
        )
    )
    lines.append(
        '| hospitalized_cases = {:,} (current) {}<ref name="MDPH-Cases"/>'.format(
            data[today_str]["hosp_current"],
            asof,
        )
    )
    lines.append(
        '| critical_cases    = {:,} (current) {}<ref name="MDPH-Cases"/>'.format(
            data[today_str]["icu_current"],
            asof,
        )
    )
    lines.append(
        '| ventilator_cases  = {:,} (current) {}<ref name="MDPH-Cases"/>'.format(
            data[today_str]["vent_current"],
            asof,
        )
    )
    lines.append(
        '| deaths            = {:,} (cumulative) {}<ref name="MDPH-Cases"/>'.format(
            data[today_str]["deaths"], asof
        )
    )
    lines.append(
        (
            "| vaccinations      = {{{{Unbulleted list\n| {:,} ({}) (people with at "
            "least one dose) {}{}\n| {:,} ({}) (fully vaccinated people) {}{}\n}}}}"
        ).format(
            manual_data["one_dose_num"],
            manual_data["one_dose_perc"],
            asof_vaccine,
            vaccine_citation,
            manual_data["fully_vaccinated_num"],
            manual_data["fully_vaccinated_perc"],
            asof_vaccine,
            '<ref name="CDC-vaccines" />',
        )
    )
    return "\n".join(lines)


def find_previous_total_cases(data, date):
    offset = 1
    prev_day = (date - timedelta(days=offset)).strftime(DAY_FMT)
    while prev_day in data:
        if data[prev_day]["total_cases"] is not None:
            return data[prev_day]["total_cases"]
        else:
            offset += 1
            prev_day = (date - timedelta(days=offset)).strftime(DAY_FMT)
    return None


def create_bar_chart(data, date_range):
    rows = []
    for date in date_range:
        date_str = date.strftime(DAY_FMT)

        previous_total_cases = find_previous_total_cases(data, date)
        if (
            data[date_str]["total_cases"] is not None
            and previous_total_cases is not None
        ):
            perc_case_change = (
                (data[date_str]["total_cases"] - previous_total_cases)
                / previous_total_cases
            ) * 100
            perc_case_change_str = "{:.2f}%".format(perc_case_change)
        else:
            perc_case_change_str = "n/a"

        if data[date_str]["confirmed_cases"] is None:
            row = ";;;;;;;"
        else:
            sign = "" if perc_case_change_str == "n/a" or perc_case_change < 0 else "+"
            row = "{date};{deaths};;{conf};{prob};;{total:,};{sign}{change}".format(
                date=date.strftime(BAR_CHART_FMT),
                deaths=data[date_str]["deaths"],
                conf=data[date_str]["confirmed_cases"],
                prob=data[date_str]["probable_cases"],
                total=data[date_str]["total_cases"],
                sign=sign,
                change=perc_case_change_str,
            )
        rows.append(row)
    return "\n".join(rows)


def get_addl_info(data, url, today, manual_data):
    today_str = today.strftime(DAY_FMT)
    today_citation_fmt = today.strftime(CITATION_DATE_FORMAT)
    addl = "Total cases: {:,}".format(data[today_str]["total_cases"])
    addl += "\nLatest rolling averages (prev day for cases, 2 days ago for deaths):"
    addl += "\n\tConfirmed cases: {:,}".format(data[today_str]["rolling_avg_cases"])
    addl += "\n\tConfirmed deaths: {:,}".format(data[today_str]["rolling_avg_deaths"])
    addl += "\n\nTests:\n\tMolecular: {:,} tests on {:,} individuals".format(
        data[today_str]["total_molecular_tests"],
        data[today_str]["individual_molecular_tests"],
    )
    addl += "\n\tAntigen: {:,}".format(data[today_str]["antigen_tests"])
    addl += (
        '\n\n<ref name="MDPH-current-day">{{{{Cite web|url={url}|title=COVID-19 Raw '
        "Data - {cite_date}|date={cite_date}|website=Massachusetts Department of "
        "Public Health|url-status=live|access-date={cite_date}|format=XLSX}}}}"
        "</ref>".format(url=url, cite_date=today_citation_fmt)
    )
    addl += "\n\nVaccines ({}):".format(manual_data["as_of"].strftime(DAY_FMT))
    addl += "\n\t>1 dose: {:,}, {}".format(
        manual_data["one_dose_num"], manual_data["one_dose_perc"]
    )
    addl += "\n\t>Fully vaccinated: {:,}, {}".format(
        manual_data["fully_vaccinated_num"], manual_data["fully_vaccinated_perc"]
    )

    return addl


def write_file(infobox, bar_chart, addl_info_for_article_body):
    with open(os.path.join(OUT_DIR, "infobox_and_barchart.txt"), "w+") as f:
        f.write(infobox + "\n\n\n" + bar_chart + "\n\n\n" + addl_info_for_article_body)


def parse_vax_row(prompt):
    inp = input(prompt)
    result = re.search(r"([\d,]+).*?([\d\.%]+)", inp)
    if result:
        num = result.group(1)
        perc = result.group(2)
        if num:
            num = int(re.sub(",", "", num))
        return num, perc
    return None


def get_manual_data():
    """Some data isn't included in the spreadsheets but can be pulled from other reports."""
    print(
        "From CDC: https://healthdata.gov/Community/COVID-19-State-Profile-Report-Massachusetts/j75q-tgps"
    )
    one_dose_num, one_dose_perc = parse_vax_row("Received >1 dose: ")
    fully_vaccinated_num, fully_vaccinated_perc = parse_vax_row("Fully vaccinated: ")
    as_of = input("As of (YYYY-MM-DD): ")
    return {
        "one_dose_num": one_dose_num,
        "one_dose_perc": one_dose_perc,
        "fully_vaccinated_num": fully_vaccinated_num,
        "fully_vaccinated_perc": fully_vaccinated_perc,
        "as_of": date.fromisoformat(as_of),
    }


def create_infobox_and_barchart(xlsx_path, url, today, date_range, args):
    data = get_data(xlsx_path, date_range, today)
    manual_data = get_manual_data()
    infobox = create_infobox(data, today, manual_data)
    bar_chart = create_bar_chart(data, date_range)
    addl_info_for_article_body = get_addl_info(data, url, today, manual_data)
    write_file(infobox, bar_chart, addl_info_for_article_body)
