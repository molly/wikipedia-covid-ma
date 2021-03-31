TMP_DIR = "tmp"
DATA_DIR = "data"
OUT_DIR = "out"

URL = "https://www.mass.gov/doc/covid-19-raw-data-{}/download"
EXCEL_URL = "https://www.mass.gov/doc/chapter-93-state-numbers-daily-report-{}/download"
CITATION_URL = "https://www.mass.gov/doc/covid-19-dashboard-{}/download"

URL_DATE_FMT = "%B-%-d-%Y"
DAY_FMT = "%-m/%-d/%Y"
CITATION_DATE_FORMAT = "%B %-d, %Y"
STATISTICS_DAY_FMT = "%b %-d %Y"
AS_OF_ALT_FMT = "%B{{nbsp}}%-d"
BAR_CHART_FMT = "%Y-%m-%d"

CITATION_TITLE = "COVID-19 Dashboard – {}"

REQUEST_HEADER = {
    "user-agent": "COVID in Massachusetts data parser: https://github.com/molly/wikipedia-covid-ma"
}

EMPTY_COUNTY_TABLE_ROW = (
    '|-\n| style="text-align:left;" | ⋮\n| style="border-left: 2px solid #888;" |\n|\n'
    '|\n|\n|\n|\n|\n|\n|\n|\n|\n|\n|\n|\n| style="border-left: 2px solid #888;" |\n|\n'
    '|\n|\n|\n|\n|\n|\n|\n|\n|\n|\n|\n|\n| style="border-left: 2px solid #888;" |\n'
)
