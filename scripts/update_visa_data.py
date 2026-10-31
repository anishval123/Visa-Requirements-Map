"""Update visa requirement data from English Wikipedia tables.

Wikipedia is not an official government source, so the generated dataset keeps
page titles, URLs, and retrieval dates for auditability.
"""

from __future__ import annotations

import json
import re
import time
from argparse import ArgumentParser
from datetime import date
from pathlib import Path
from urllib.parse import quote

import pycountry
import requests
from bs4 import BeautifulSoup

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "visa_data.json"
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
WIKIPEDIA_PAGE = "https://en.wikipedia.org/wiki/{title}"
USER_AGENT = "SriAI Visa Map educational importer/1.0"

EXTRA_COUNTRIES = {
    "XKX": {
        "name": "Kosovo",
        "numeric": "XK",
        "official_name": "Republic of Kosovo",
    }
}

COUNTRY_ALIASES = {
    "bahamas": "BHS",
    "bolivia": "BOL",
    "brunei": "BRN",
    "cape verde": "CPV",
    "czech republic": "CZE",
    "democratic republic of the congo": "COD",
    "dr congo": "COD",
    "east timor": "TLS",
    "eswatini": "SWZ",
    "hong kong": "HKG",
    "iran": "IRN",
    "ivory coast": "CIV",
    "laos": "LAO",
    "macau": "MAC",
    "micronesia": "FSM",
    "moldova": "MDA",
    "myanmar": "MMR",
    "north korea": "PRK",
    "palestine": "PSE",
    "republic of the congo": "COG",
    "russia": "RUS",
    "south korea": "KOR",
    "syria": "SYR",
    "sao tome and principe": "STP",
    "são tomé and príncipe": "STP",
    "taiwan": "TWN",
    "tanzania": "TZA",
    "the bahamas": "BHS",
    "the gambia": "GMB",
    "turkey": "TUR",
    "united kingdom": "GBR",
    "united states": "USA",
    "vatican city": "VAT",
    "venezuela": "VEN",
    "vietnam": "VNM",
}

TITLE_SUBJECT_ALIASES = {
    "bangladesh": "BGD",
    "bangladeshi": "BGD",
    "belarus": "BLR",
    "belarusian": "BLR",
    "belarussian": "BLR",
    "belgian": "BEL",
    "belorussian": "BLR",
    "cambodian": "KHM",
    "canadian": "CAN",
    "chinese citizens of macau": "MAC",
    "chinese citizens of hong kong": "HKG",
    "danish": "DNK",
    "dominica": "DMA",
    "egyptian": "EGY",
    "faroese": "FRO",
    "filipino": "PHL",
    "gambian": "GMB",
    "greenlandic": "GRL",
    "hungarian": "HUN",
    "icelandic": "ISL",
    "indonesian": "IDN",
    "irish": "IRL",
    "kosovan": "XKX",
    "kosovar": "XKX",
    "kosovo": "XKX",
    "kyrgyz": "KGZ",
    "kyrgyzstani": "KGZ",
    "lithuanian": "LTU",
    "macanese": "MAC",
    "moldovan": "MDA",
    "moroccan": "MAR",
    "north korean": "PRK",
    "pakistani": "PAK",
    "palestinian": "PSE",
    "philippine": "PHL",
    "saint kitts and nevis": "KNA",
    "saint lucia": "LCA",
    "saint lucian": "LCA",
    "santomean": "STP",
    "senegalese": "SEN",
    "slovenian": "SVN",
    "somali": "SOM",
    "somalian": "SOM",
    "thai": "THA",
    "turkish": "TUR",
    "ugandan": "UGA",
    "vietnamese": "VNM",
}

STATUS_PATTERNS = [
    ("freedom_of_movement", ["freedom of movement", "right to abode"]),
    ("entry_restricted", ["admission refused", "entry refused", "entry banned", "entry prohibited"]),
    ("visa_on_arrival", ["visa on arrival", "visitor's permit on arrival"]),
    ("e_visa", ["evisa", "e-visa", "electronic visa", "online visa"]),
    ("eta", ["electronic travel authorization", "electronic travel authorisation", "eta"]),
    ("esta", ["esta"]),
    ("visa_free", ["visa not required", "visa-free", "visa free", "visa exemption"]),
    ("visa_required", ["visa required", "entry permit required"]),
]


def clean_text(value: str) -> str:
    value = re.sub(r"\[[^\]]+\]", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_country_name(value: str) -> str:
    value = clean_text(value)
    value = re.sub(r"\(.*?\)", "", value)
    value = value.replace("*", "")
    return value.strip(" .")


def country_to_iso3(value: str) -> str | None:
    normalized = normalize_country_name(value).casefold()
    if normalized in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[normalized]
    for iso3, country in EXTRA_COUNTRIES.items():
        names = {country["name"].casefold(), country["official_name"].casefold()}
        if normalized in names:
            return iso3

    try:
        return pycountry.countries.lookup(normalized).alpha_3
    except LookupError:
        return None


def classify_requirement(value: str) -> str | None:
    normalized = clean_text(value).casefold()
    normalized = normalized.replace("e visa", "e-visa")

    leading_statuses = [
        ("entry_restricted", ["admission refused", "entry refused", "entry banned", "entry prohibited"]),
        ("visa_required", ["visa required", "entry permit required"]),
        ("visa_on_arrival", ["visa on arrival", "visitor's permit on arrival"]),
        ("e_visa", ["evisa", "e-visa", "electronic visa", "online visa"]),
        ("eta", ["electronic travel authorization", "electronic travel authorisation", "eta"]),
        ("esta", ["esta"]),
        ("visa_free", ["visa not required", "visa-free", "visa free", "visa exemption"]),
        ("freedom_of_movement", ["freedom of movement", "right to abode"]),
    ]
    for status, patterns in leading_statuses:
        if any(normalized.startswith(pattern) for pattern in patterns):
            return status

    for status, patterns in STATUS_PATTERNS:
        if any(pattern in normalized for pattern in patterns):
            return status
    return None


def wikipedia_get(params: dict) -> dict:
    for attempt in range(5):
        response = requests.get(
            WIKIPEDIA_API,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )
        if response.status_code != 429:
            response.raise_for_status()
            return response.json()

        retry_after = int(response.headers.get("Retry-After", "5"))
        time.sleep(retry_after + attempt)

    response.raise_for_status()
    return response.json()


def wikipedia_page_exists(title: str) -> bool:
    response = wikipedia_get(
        {
            "action": "query",
            "format": "json",
            "titles": title,
        }
    )
    pages = response.get("query", {}).get("pages", {})
    return not any("missing" in page for page in pages.values())


def find_passport_page_title(country_name: str) -> str | None:
    search = wikipedia_get(
        {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": f'"{country_name}" passport',
            "srlimit": 8,
        }
    )
    for result in search.get("query", {}).get("search", []):
        title = result["title"]
        if title.casefold().endswith(" passport"):
            return title
    return None


def find_visa_page_title(country_name: str) -> str | None:
    candidates = [
        f"Visa requirements for {country_name} citizens",
    ]
    passport_title = find_passport_page_title(country_name)
    if passport_title:
        passport_subject = passport_title.removesuffix(" passport")
        candidates.append(f"Visa requirements for {passport_subject} citizens")

    for title in candidates:
        if "non-citizens" not in title.casefold() and wikipedia_page_exists(title):
            return title

    queries = [
        f'intitle:"Visa requirements for" "{country_name}" citizens',
        f'"Visa requirements for" "{country_name}" citizens',
        f'"Visa requirements for" "{country_name}" passport',
        f"Visa requirements citizens {country_name}",
    ]
    for query in queries:
        search = wikipedia_get(
            {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": query,
                "srlimit": 10,
            }
        )
        for result in search.get("query", {}).get("search", []):
            title = result["title"]
            title_lc = title.casefold()
            if (
                title_lc.startswith("visa requirements for")
                and "citizens" in title_lc
                and "non-citizens" not in title_lc
            ):
                return title
    return None


def list_visa_page_titles() -> list[str]:
    titles: list[str] = []
    params = {
        "action": "query",
        "format": "json",
        "list": "allpages",
        "apprefix": "Visa requirements for ",
        "aplimit": "max",
    }
    while True:
        data = wikipedia_get(params)
        for page in data.get("query", {}).get("allpages", []):
            title = page["title"]
            title_lc = title.casefold()
            if (
                title_lc.startswith("visa requirements for")
                and "citizens" in title_lc
                and "non-citizens" not in title_lc
                and "european union citizens" not in title_lc
            ):
                titles.append(title)

        if "continue" not in data:
            return sorted(set(titles))
        params.update(data["continue"])


def fetch_page_html(title: str) -> str:
    url = WIKIPEDIA_PAGE.format(title=quote(title.replace(" ", "_")))
    for attempt in range(5):
        try:
            response = requests.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=30,
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException:
            if attempt == 4:
                raise
            time.sleep(2 + attempt)
    raise RuntimeError(f"Could not fetch {title}")


def extract_passport_iso3(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    text = clean_text(soup.get_text(" "))
    patterns = [
        r"citizens of the ([A-Z][A-Za-z '-]+?)\s*(?:entering|travelling|traveling|holding|who|[.,;]| are| were)",
        r"citizens of ([A-Z][A-Za-z '-]+?)\s*(?:entering|travelling|traveling|holding|who|[.,;]| are| were)",
        r"holders of ([A-Z][A-Za-z '-]+?) passports",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            iso3 = country_to_iso3(match.group(1))
            if iso3:
                return iso3
    return None


def title_subject_to_iso3(title: str) -> str | None:
    match = re.match(r"Visa requirements for (.+?) citizens$", title, flags=re.IGNORECASE)
    if not match:
        match = re.match(r"Visa requirements for (.+)$", title, flags=re.IGNORECASE)
    if not match:
        return None
    subject = match.group(1).strip().casefold()
    return TITLE_SUBJECT_ALIASES.get(subject)


def table_header_indexes(table) -> tuple[int, int] | None:
    headers = [clean_text(header.get_text(" ")) for header in table.select("tr th")]
    lowered = [header.casefold() for header in headers]
    country_index = next(
        (index for index, header in enumerate(lowered) if "country" in header or "destination" in header),
        None,
    )
    requirement_index = next(
        (
            index
            for index, header in enumerate(lowered)
            if "visa requirement" in header or header in {"requirement", "entry requirement"}
        ),
        None,
    )
    if country_index is None or requirement_index is None:
        return None
    return country_index, requirement_index


def parse_requirements_from_html(html: str) -> tuple[dict[str, str], list[str]]:
    soup = BeautifulSoup(html, "html.parser")
    requirements: dict[str, str] = {}
    unmapped: list[str] = []

    for table in soup.select("table.wikitable"):
        indexes = table_header_indexes(table)
        if indexes is None:
            continue

        country_index, requirement_index = indexes
        for row in table.select("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) <= max(country_index, requirement_index):
                continue

            destination = normalize_country_name(cells[country_index].get_text(" "))
            if destination.casefold() in {"country", "country / region", "countries", "visitor to"}:
                continue
            requirement_text = cells[requirement_index].get_text(" ")
            iso3 = country_to_iso3(destination)
            status = classify_requirement(requirement_text)

            if iso3 and status:
                requirements[iso3] = status
            elif destination and not iso3:
                unmapped.append(destination)

        if requirements:
            break

    return requirements, sorted(set(unmapped))


def fetch_country_record(country, delay_seconds: float) -> dict | None:
    title = find_visa_page_title(country.name)
    if title is None:
        return None

    html = fetch_page_html(title)
    requirements, unmapped = parse_requirements_from_html(html)
    requirements[country.alpha_3] = "freedom_of_movement"

    time.sleep(delay_seconds)
    return {
        "country": country.name,
        "iso3": country.alpha_3,
        "aliases": [getattr(country, "official_name", country.name)],
        "source": {
            "title": title,
            "url": WIKIPEDIA_PAGE.format(title=quote(title.replace(" ", "_"))),
            "retrieved_at": date.today().isoformat(),
            "unmapped_destinations": unmapped,
        },
        "requirements": dict(sorted(requirements.items())),
    }


def fetch_records_from_page_list(limit: int | None, delay_seconds: float) -> tuple[list[dict], list[dict]]:
    titles = list_visa_page_titles()
    if limit is not None:
        titles = titles[:limit]

    passports = []
    failures = []
    for index, title in enumerate(titles, start=1):
        print(f"[{index}/{len(titles)}] Fetching {title}...")
        try:
            html = fetch_page_html(title)
            passport_iso3 = extract_passport_iso3(html) or title_subject_to_iso3(title)
            if passport_iso3 is None:
                failures.append({"title": title, "reason": "Could not identify passport country"})
                continue

            country = pycountry.countries.get(alpha_3=passport_iso3)
            if country is None and passport_iso3 in EXTRA_COUNTRIES:
                extra_country = EXTRA_COUNTRIES[passport_iso3]
                country_name = extra_country["name"]
                aliases = [extra_country["official_name"]]
            else:
                country_name = country.name
                aliases = [getattr(country, "official_name", country.name)]
            requirements, unmapped = parse_requirements_from_html(html)
            requirements[passport_iso3] = "freedom_of_movement"
            record = {
                "country": country_name,
                "iso3": passport_iso3,
                "aliases": aliases,
                "source": {
                    "title": title,
                    "url": WIKIPEDIA_PAGE.format(title=quote(title.replace(" ", "_"))),
                    "retrieved_at": date.today().isoformat(),
                    "unmapped_destinations": unmapped,
                },
                "requirements": dict(sorted(requirements.items())),
            }
            time.sleep(delay_seconds)
        except requests.RequestException as exc:
            record = None
            failures.append({"title": title, "reason": str(exc)})

        if record and len(record["requirements"]) > 1:
            passports.append(record)
        else:
            failures.append({"title": title, "reason": "No usable Wikipedia visa table found"})

    return passports, failures


def deduplicate_passports(passports: list[dict]) -> list[dict]:
    best_by_iso3: dict[str, dict] = {}
    for passport in passports:
        iso3 = passport["iso3"]
        current = best_by_iso3.get(iso3)
        if current is None or len(passport["requirements"]) > len(current["requirements"]):
            best_by_iso3[iso3] = passport
    return sorted(best_by_iso3.values(), key=lambda item: item["country"])


def fetch_latest_visa_data(limit: int | None = None, delay_seconds: float = 0.3) -> dict:
    passports, failures = fetch_records_from_page_list(limit, delay_seconds)
    passports = deduplicate_passports(passports)

    data = {
        "last_updated": date.today().isoformat(),
        "source_note": (
            "Visa data imported from English Wikipedia visa requirement tables. "
            "Wikipedia is not an official government source; verify before travel."
        ),
        "source": "English Wikipedia",
        "failed_imports": failures,
        "passports": passports,
    }
    return data


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Import only the first N countries.")
    parser.add_argument("--delay", type=float, default=0.3, help="Delay between country imports.")
    args = parser.parse_args()

    updated_data = fetch_latest_visa_data(limit=args.limit, delay_seconds=args.delay)
    with DATA_FILE.open("w", encoding="utf-8") as data_file:
        json.dump(updated_data, data_file, indent=2, sort_keys=False)
        data_file.write("\n")


if __name__ == "__main__":
    main()
