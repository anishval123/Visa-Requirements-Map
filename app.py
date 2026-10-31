
from __future__ import annotations

import json
import os
from pathlib import Path

import pycountry
from flask import Flask, abort, jsonify, render_template


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "visa_data.json"

app = Flask(__name__)

COMMON_ALIASES = {
    "america": "USA",
    "brasil": "BRA",
    "britain": "GBR",
    "czech republic": "CZE",
    "england": "GBR",
    "iran": "IRN",
    "kosovo": "XKX",
    "laos": "LAO",
    "moldova": "MDA",
    "north korea": "PRK",
    "palestine": "PSE",
    "russia": "RUS",
    "south korea": "KOR",
    "syria": "SYR",
    "taiwan": "TWN",
    "tanzania": "TZA",
    "turkey": "TUR",
    "uk": "GBR",
    "united kingdom": "GBR",
    "united states": "USA",
    "united states of america": "USA",
    "usa": "USA",
    "venezuela": "VEN",
    "vietnam": "VNM",
}

EXTRA_COUNTRIES = {
    "XKX": {
        "country": "Kosovo",
        "iso3": "XKX",
        "iso_numeric": "XK",
        "aliases": ["Republic of Kosovo"],
    }
}


def load_visa_data() -> dict:
    with DATA_FILE.open("r", encoding="utf-8") as data_file:
        return json.load(data_file)


def find_passport_record(country_name: str) -> dict | None:
    normalized = country_name.strip().casefold()
    data = load_visa_data()

    for record in data["passports"]:
        names = [record["country"], *record.get("aliases", [])]
        if normalized in {name.casefold() for name in names}:
            return record

    country = find_country(country_name)

    if country is not None:
        for record in data["passports"]:
            if record["iso3"] == country.alpha_3:
                return record

    return None


def country_to_payload(country) -> dict:
    return {
        "country": country.name,
        "iso3": country.alpha_3,
        "iso_numeric": country.numeric,
        "aliases": [
            getattr(country, "official_name", country.name)
        ],
    }


def country_payloads() -> list[dict]:
    payloads = [
        country_to_payload(country)
        for country in sorted(
            pycountry.countries,
            key=lambda item: item.name
        )
    ]

    payloads.extend(EXTRA_COUNTRIES.values())

    return sorted(payloads, key=lambda item: item["country"])


def find_country(country_name: str):
    normalized = country_name.strip().casefold()
    alias_iso3 = COMMON_ALIASES.get(normalized)

    if alias_iso3 in EXTRA_COUNTRIES:
        return type(
            "Country",
            (),
            {
                "name": EXTRA_COUNTRIES[alias_iso3]["country"],
                "alpha_3": alias_iso3,
                "numeric": EXTRA_COUNTRIES[alias_iso3]["iso_numeric"],
            },
        )()

    if alias_iso3:
        return pycountry.countries.get(alpha_3=alias_iso3)

    try:
        return pycountry.countries.lookup(country_name)
    except LookupError:
        return None


def _all_country_iso3s() -> set[str]:
    """Return all known ISO 3166-1 alpha-3 codes."""
    codes = {country.alpha_3 for country in pycountry.countries}
    codes.update(EXTRA_COUNTRIES.keys())
    return codes


def iso3_requirements_to_numeric(
    requirements: dict[str, str]
) -> dict[str, str]:

    numeric_requirements = {}

    for iso3, status in requirements.items():

        if iso3 in EXTRA_COUNTRIES:
            numeric_requirements[
                EXTRA_COUNTRIES[iso3]["iso_numeric"]
            ] = status
            continue

        country = pycountry.countries.get(alpha_3=iso3)

        if country is not None:
            numeric_requirements[country.numeric] = status

    return numeric_requirements


def fill_missing_requirements(
    requirements: dict[str, str],
    own_iso3: str
) -> dict[str, str]:

    """Ensure all known countries have a visa status."""

    result = dict(requirements)
    all_codes = _all_country_iso3s()

    for iso3 in all_codes:
        if iso3 not in result:
            result[iso3] = "unknown"

    if result.get(own_iso3) == "unknown":
        result[own_iso3] = "freedom_of_movement"

    return result


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/countries")
def countries():
    return jsonify(country_payloads())


@app.get("/api/visa/<country_name>")
def visa_requirements(country_name: str):

    data = load_visa_data()
    record = find_passport_record(country_name)
    country = find_country(country_name)

    if record is None and country is None:
        abort(
            404,
            description=f"No visa data found for '{country_name}'."
        )

    if record is not None:

        passport_country = record["country"]
        passport_iso3 = record["iso3"]
        source = record.get("source")

        requirements = {
            **record["requirements"],
            passport_iso3: "freedom_of_movement",
        }

        data_quality = "wikipedia"

    else:

        passport_country = country.name
        passport_iso3 = country.alpha_3
        source = None

        requirements = {
            passport_iso3: "freedom_of_movement"
        }

        data_quality = "no_verified_data"

    complete_requirements = fill_missing_requirements(
        requirements,
        passport_iso3
    )

    return jsonify(
        {
            "passport_country": passport_country,
            "passport_iso3": passport_iso3,
            "last_updated": data["last_updated"],
            "source_note": data["source_note"],
            "source": source,
            "data_quality": data_quality,
            "requirements": requirements,
            "requirements_numeric": iso3_requirements_to_numeric(
                complete_requirements
            ),
        }
    )


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": error.description}), 404


# Render startup configuration
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
