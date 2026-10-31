<<<<<<< HEAD
# Visa Requirements Map

A small Flask + D3 app that lets users enter a passport country and view a world map colored by destination visa requirement.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## What is included

- `GET /api/countries` returns recognized countries from `pycountry`.
- `GET /api/visa/<country>` returns visa requirements keyed by both ISO 3166-1 alpha-3 and ISO numeric destination country code.
- The frontend renders countries with locally vendored D3, `topojson-client`, and `world-atlas`, then colors them using `static/js/app.js`.
- Visa requirement data is imported from English Wikipedia pages named `Visa requirements for ... citizens`.
- Countries without an imported Wikipedia table can still be searched, but destinations remain gray until Wikipedia data is added.

## Visa status keys

The frontend currently supports:

- `freedom_of_movement`
- `entry_restricted`
- `visa_free`
- `visa_on_arrival`
- `e_visa`
- `eta`
- `esta`
- `visa_required`
- `unknown`

## Updating visa data regularly

The file `scripts/update_visa_data.py` is a placeholder importer. Replace `fetch_latest_visa_data()` with logic that fetches and normalizes data from a verified source.

Recommended update workflow:

1. Choose a data source, such as an official government source, licensed API, Wikidata/Wikipedia-derived table, or maintained internal dataset.
2. Normalize destination countries to ISO 3166-1 alpha-3 codes. The API converts these to ISO numeric codes for the D3 map.
3. Map source labels to the status keys listed above.
4. Validate the output JSON before writing `data/visa_data.json`.
5. Schedule the script with Windows Task Scheduler, cron, GitHub Actions, or your deployment platform.

Example scheduled command:

```powershell
python scripts/update_visa_data.py
```

Visa rules change often. Treat Wikipedia as a convenient public source, not an official authority. Verify production data against official government sources.
=======
# Visa-Requirements-Map
This is a website where you enter a country into the search bar and it shows what type of authoriation you need to enter that country.
>>>>>>> 75e8c51acc42c5a3e15c7381097a777649736935
