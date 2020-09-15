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

TOTAL_POPULATION = 6892503
CASES_PER_POP_FORMULA = (
    "{{{{ formatnum: {{{{ #expr: ( {{{{ formatnum: {:,}|R }}}} / {} round 1 ) }}}} }}}}"
)
DEATHS_PER_POP_FORMULA = (
    "{{{{ formatnum: {{{{ #expr: ( {{{{ formatnum: {:,}|R }}}} / {} round 1 ) }}}} }}}}"
    ""
)
DEATHS_CASES_FORMULA = (
    "{{{{ formatnum: {{{{ #expr: ( {{{{ formatnum: {:,}|R }}}} / {} round 2 ) }}}} }}}}"
)
HEADER_STYLE = (
    '! style="text-align:right; padding-right:17px; padding-left:3px;" scope="row" '
)
ROW_STYLE = 'style="padding:0px 2px;" '
COUNTIES = [
    {
        "county": "Barnstable",
        "population": 212990,
        "wikilink": "[[Barnstable County, Massachusetts|Barnstable]]",
    },
    {
        "county": "Berkshire",
        "population": 124944,
        "wikilink": "[[Berkshire County, Massachusetts|Berkshire]]",
    },
    {
        "county": "Bristol",
        "population": 565217,
        "wikilink": "[[Bristol County, Massachusetts|Bristol]]",
    },
    {
        "county": "Dukes and Nantucket",
        "population": 28731,
        "wikilink": "[[Dukes County, Massachusetts|Dukes]] and [[Nantucket County, "
        "Massachusetts|Nantucket]]",
    },
    {
        "county": "Essex",
        "population": 789034,
        "wikilink": "[[Essex County, Massachusetts|Essex]]",
    },
    {
        "county": "Franklin",
        "population": 70180,
        "wikilink": "[[Franklin County, Massachusetts|Franklin]]",
    },
    {
        "county": "Hampden",
        "population": 466372,
        "wikilink": "[[Hampden County, Massachusetts|Hampden]]",
    },
    {
        "county": "Hampshire",
        "population": 160830,
        "wikilink": "[[Hampshire County, Massachusetts|Hampshire]]",
    },
    {
        "county": "Middlesex",
        "population": 1611699,
        "wikilink": "[[Middlesex County, Massachusetts|Middlesex]]",
    },
    {
        "county": "Norfolk",
        "population": 706775,
        "wikilink": "[[Norfolk County, Massachusetts|Norfolk]]",
    },
    {
        "county": "Plymouth",
        "population": 521202,
        "wikilink": "[[Plymouth County, Massachusetts|Plymouth]]",
    },
    {
        "county": "Suffolk",
        "population": 803907,
        "wikilink": "[[Suffolk County, Massachusetts|Suffolk]]",
    },
    {
        "county": "Worcester",
        "population": 830622,
        "wikilink": "[[Worcester County, Massachusetts|Worcester]]",
    },
    {"county": "Unknown", "population": None, "wikilink": "Unknown"},
]


def get_data(today):
    today_str = today.strftime(DAY_FMT)
    data = {
        c["county"]: {"population": c["population"], "cases": 0, "deaths": 0}
        for c in COUNTIES
    }
    with open(
        os.path.join(TMP_DIR, "County.csv"), "r", encoding="utf-8-sig"
    ) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["Date"] == today_str:
                if row["County"] in ["Dukes", "Nantucket", "Dukes and Nantucket"]:
                    county = "Dukes and Nantucket"
                else:
                    county = row["County"]
                if row["Total Confirmed Cases"]:
                    data[county]["cases"] += int(row["Total Confirmed Cases"])
                if row["Total Probable and Confirmed Deaths"]:
                    data[county]["deaths"] += int(
                        row["Total Probable and Confirmed Deaths"]
                    )
        return data


def create_header_row(data, recov):
    total_cases = 0
    total_deaths = 0
    for c in COUNTIES:
        total_cases += data[c["county"]]["cases"]
        total_deaths += data[c["county"]]["deaths"]
    divided_pop = TOTAL_POPULATION / 100000

    row = "|-\n"
    row += HEADER_STYLE + "| '''14 / 14'''\n"
    row += HEADER_STYLE + "| '''{:,}'''\n".format(total_cases)
    row += HEADER_STYLE + "| '''{:,}'''\n".format(total_deaths)
    row += HEADER_STYLE + "| '''{}'''\n".format(
        "{:,}".format(recov) if recov else "RECOVERIES"
    )
    row += HEADER_STYLE + "| '''{:,}'''\n".format(TOTAL_POPULATION)
    row += HEADER_STYLE + "| '''{}'''\n".format(
        CASES_PER_POP_FORMULA.format(total_cases, divided_pop)
    )
    row += HEADER_STYLE + "| '''{}'''\n".format(
        DEATHS_PER_POP_FORMULA.format(total_deaths, divided_pop)
    )
    row += HEADER_STYLE + "| '''{}'''\n".format(
        DEATHS_CASES_FORMULA.format(total_deaths, total_cases / 100)
    )
    return row


def create_county_row(county, data):
    divided_pop = county["population"] / 100000 if county["population"] else None
    row = "|-\n"
    row += "! " + ROW_STYLE + "|{}\n".format(county["wikilink"])
    row += "| " + ROW_STYLE + "|{:,}\n".format(data["cases"])
    row += "| " + ROW_STYLE + "|{:,}\n".format(data["deaths"])
    if county["population"]:
        row += "| " + ROW_STYLE + "|{{–}}\n"
        row += "| " + ROW_STYLE + "|{:,}\n".format(county["population"])
        row += "| " + CASES_PER_POP_FORMULA.format(data["cases"], divided_pop) + "\n"
        row += "| " + DEATHS_PER_POP_FORMULA.format(data["deaths"], divided_pop) + "\n"
    else:
        for i in range(4):
            row += "| " + ROW_STYLE + "| n/a\n"
    row += "| " + DEATHS_CASES_FORMULA.format(data["deaths"], data["cases"] / 100)
    row += "\n"
    return row


def create_footer(today):
    pretty_today = today.strftime(CITATION_DATE_FORMAT)
    row = '|- style="text-align:center;" class="sortbottom"\n'
    row += '| colspan="9" | {{{{resize|Updated {}}}}}<br/>'.format(pretty_today)
    row += "{{resize|Data is publicly reported by Massachusetts Department of Public "
    row += "Health}}<ref>{{cite web |title=COVID-19 Updates and Information |"
    row += "url=https://www.mass.gov/info-details/covid-19-updates-and-information "
    row += "|website=Massachusetts Department of Public Health "
    row += "|accessdate={}}}}}</ref>".format(pretty_today)
    row += "<ref>{{cite web |title=COVID-19 Response Reporting |"
    row += "url=https://www.mass.gov/info-details/covid-19-response-reporting "
    row += "|website=Massachusetts Department of Public Health "
    row += "|accessdate={}}}}}</ref>\n".format(pretty_today)
    return row


def create_table(data, today, recov):
    rows = [create_header_row(data, recov)]
    for c in COUNTIES:
        rows.append(create_county_row(c, data[c["county"]]))
    rows.append(create_footer(today))
    with open(os.path.join(OUT_DIR, "daily_county.txt"), "w+") as f:
        f.write("".join(rows))


def create_daily_county_table(today, recov):
    data = get_data(today)
    create_table(data, today, recov)
