TMP_DIR = "tmp"
DATA_DIR = "data"
OUT_DIR = "out"

URL = "https://www.mass.gov/doc/covid-19-raw-data-{}/download"
EXCEL_URL = "https://www.mass.gov/doc/chapter-93-state-numbers-daily-report-{}/download"
CITATION_URL = "https://www.mass.gov/doc/covid-19-dashboard-{}/download"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search?city={}&state=massachusetts&format=json&addressdetails=1"

URL_DATE_FMT = "%B-%-d-%Y"
DAY_FMT = "%-m/%-d/%Y"
CITATION_DATE_FORMAT = "%B %-d, %Y"
STATISTICS_DAY_FMT = "%b %-d"
AS_OF_ALT_FMT = "%B %-d"
BAR_CHART_FMT = "%Y-%m-%d"

CITATION_TITLE = "COVID-19 Dashboard – {}"

REQUEST_HEADER = {
    "user-agent": "COVID in Massachusetts data parser: https://github.com/molly/wikipedia-covid-ma"
}
