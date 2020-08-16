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

import os
import pickle
import requests
from datetime import datetime, timedelta
from openpyxl import load_workbook
from time import sleep

from constants import *

COUNTIES_DATA_PATH = os.path.join(DATA_DIR, "counties.pickle")


def get_sheets(yesterday):
    wb = load_workbook(filename=os.path.join(TMP_DIR, yesterday + ".xlsx"))
    cases_sheet = wb.get_sheet_by_name("Pos_Last24")
    deaths_sheet = wb.get_sheet_by_name("Died_last24")
    return cases_sheet, deaths_sheet


def get_case_data(sheet):
    col_a = sheet["A"]
    col_b = sheet["B"]
    city_data = {}
    write = False
    for ind, cell in enumerate(col_a):
        if cell.value and cell.value.startswith("Primary City"):
            write = True
            continue
        if write and cell.value and cell.value == "Unknown":
            break
        if write and cell.value:
            cases = col_b[ind].value
            city_data[cell.value] = {"cases": cases}
    return city_data


def get_deaths_data(sheet, city_data):
    col_a = sheet["A"]
    col_b = sheet["B"]
    write = False
    for ind, cell in enumerate(col_a):
        if cell.value and cell.value.startswith("Primary City"):
            write = True
            continue
        if write and cell.value and cell.value == "Unknown":
            break
        if write and cell.value:
            deaths = col_b[ind].value
            if cell.value in city_data:
                city_data[cell.value]["deaths"] = deaths
            else:
                city_data[cell.value] = {"deaths": deaths}
    return city_data


def get_city_locations(cities):
    if os.path.exists(COUNTIES_DATA_PATH):
        print("Found stored county data.")
        with open(COUNTIES_DATA_PATH, "rb") as pickle_file:
            county_map = pickle.load(pickle_file)
            return county_map

    print("Gathering county data...")
    county_map = {}
    last_req = datetime.now()
    for city in cities:
        if datetime.now() < last_req + timedelta(seconds=1):
            # Nominatim has a 1 request per second limit
            sleep(1)
        print(city)
        r = requests.get(NOMINATIM_URL.format(city), headers=REQUEST_HEADER)
        last_req = datetime.now()
        if r.status_code != 200:
            county = input("Couldn't get a county for this city: {}. Enter county: ")
        else:
            resp = r.json()
            try:
                county_full = resp[0]["address"]["county"]
                if county_full.endswith(" County"):
                    county = county_full[:-7]
            except KeyError:
                county = input(
                    "Couldn't get a county for this city: {}. Enter county: "
                )
            county_map[city] = county

    with open(COUNTIES_DATA_PATH, "wb+") as f:
        pickle.dump(county_map, f)


def rollup(city_data, cities, county_map):
    results = {}
    for city in cities:
        county = county_map[city]
        cases = city_data[city]["cases"]
        deaths = city_data[city]["deaths"]
        if not (county in results):
            results[county] = {
                "cases": 0,
                "deaths": 0,
                "cases_error": 0,
                "deaths_error": 0,
            }
        if cases == "<5":
            results[county]["cases"] += 2.5
            results[county]["cases_error"] += 1.5
        else:
            results[county]["cases"] += cases

        if deaths == "<5":
            results[county]["deaths"] += 2.5
            results[county]["deaths_error"] += 1.5
        else:
            results[county]["deaths"] += deaths
    return results


def create_county_tables(args):
    yesterday = (args["today"] - timedelta(days=1)).strftime(URL_DATE_FMT).lower()
    cases_sheet, deaths_sheet = get_sheets(yesterday)
    city_data = get_case_data(cases_sheet)
    city_data = get_deaths_data(deaths_sheet, city_data)
    cities = list(city_data.keys())
    county_map = get_city_locations(cities)
    results = rollup(city_data, cities, county_map)
