"""
Add missing Caribbean countries and territories (Saint Lucia, Aruba, Dominica, etc.)
as passport records in visa_data.json so they appear in the searchable country list
and display visa requirement data when selected.
"""
import json

VISA_DATA_PATH = "data/visa_data.json"

with open(VISA_DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# Get all existing ISO3 codes to build a comprehensive destination list
existing_iso3s = sorted({p["iso3"] for p in data["passports"]})

# Build a template requirements dict with all countries as "visa_required" (conservative default)
template_reqs = {iso3: "visa_required" for iso3 in existing_iso3s}

# Define territories that need passport records
# Each entry: iso3 -> (country_name, aliases, parent_country_iso3, known_visa_free, known_e_visa, known_eta)
# For territories, we use the parent country's visa policy as a baseline since they typically share it.

territories_to_add = {
    # Caribbean independent nations
    "ATG": {
        "country": "Antigua and Barbuda",
        "aliases": [],
        "parent": None,  # Independent nation, use conservative defaults + known agreements
        "visa_free": ["DMA", "GRD", "KNA", "LCA", "VCT", "BRB", "BHS", "BLZ", "GUY", "HTI", "JAM", "SUR", "TTO"],
        "e_visa": [],
        "eta": [],
    },
    "BRB": {
        "country": "Barbados",
        "aliases": [],
        "parent": None,
        "visa_free": ["DMA", "GRD", "KNA", "LCA", "VCT", "ATG", "BHS", "BLZ", "GUY", "HTI", "JAM", "SUR", "TTO"],
        "e_visa": [],
        "eta": [],
    },
    "DMA": {
        "country": "Dominica",
        "aliases": ["Commonwealth of Dominica"],
        "parent": None,
        "visa_free": ["ATG", "BRB", "GRD", "KNA", "LCA", "VCT", "BHS", "BLZ", "GUY", "HTI", "JAM", "SUR", "TTO"],
        "e_visa": [],
        "eta": [],
    },
    "GRD": {
        "country": "Grenada",
        "aliases": [],
        "parent": None,
        "visa_free": ["ATG", "BRB", "DMA", "KNA", "LCA", "VCT", "BHS", "BLZ", "GUY", "HTI", "JAM", "SUR", "TTO"],
        "e_visa": [],
        "eta": [],
    },
    "KNA": {
        "country": "Saint Kitts and Nevis",
        "aliases": ["St. Kitts and Nevis", "Federation of Saint Kitts and Nevis"],
        "parent": None,
        "visa_free": ["ATG", "BRB", "DMA", "GRD", "LCA", "VCT", "BHS", "BLZ", "GUY", "HTI", "JAM", "SUR", "TTO"],
        "e_visa": [],
        "eta": [],
    },
    "LCA": {
        "country": "Saint Lucia",
        "aliases": [],
        "parent": None,
        "visa_free": ["ATG", "BRB", "DMA", "GRD", "KNA", "VCT", "BHS", "BLZ", "GUY", "HTI", "JAM", "SUR", "TTO"],
        "e_visa": [],
        "eta": [],
    },
    "VCT": {
        "country": "Saint Vincent and the Grenadines",
        "aliases": ["St. Vincent and Grenadines"],
        "parent": None,
        "visa_free": ["ATG", "BRB", "DMA", "GRD", "KNA", "LCA", "BHS", "BLZ", "GUY", "HTI", "JAM", "SUR", "TTO"],
        "e_visa": [],
        "eta": [],
    },
    # Dutch Caribbean territories (follow Netherlands visa policy)
    "ABW": {
        "country": "Aruba",
        "aliases": [],
        "parent": "NLD",
        "visa_free": [],
        "e_visa": [],
        "eta": [],
    },
    "CUW": {
        "country": "Curaçao",
        "aliases": [],
        "parent": "NLD",
        "visa_free": [],
        "e_visa": [],
        "eta": [],
    },
    "SXM": {
        "country": "Sint Maarten",
        "aliases": ["Sint Maarten (Dutch part)"],
        "parent": "NLD",
        "visa_free": [],
        "e_visa": [],
        "eta": [],
    },
    "BES": {
        "country": "Bonaire, Sint Eustatius and Saba",
        "aliases": ["Caribbean Netherlands"],
        "parent": "NLD",
        "visa_free": [],
        "e_visa": [],
        "eta": [],
    },
    # French overseas departments/territories (follow France/Schengen policy)
    "GUF": {
        "country": "French Guiana",
        "aliases": [],
        "parent": "FRA",
        "visa_free": [],
        "e_visa": [],
        "eta": [],
    },
    "GLP": {
        "country": "Guadeloupe",
        "aliases": [],
        "parent": "FRA",
        "visa_free": [],
        "e_visa": [],
        "eta": [],
    },
    "MTQ": {
        "country": "Martinique",
        "aliases": [],
        "parent": "FRA",
        "visa_free": [],
        "e_visa": [],
        "eta": [],
    },
    "MAF": {
        "country": "Saint Martin",
        "aliases": ["Saint Martin (French part)"],
        "parent": "FRA",
        "visa_free": [],
        "e_visa": [],
        "eta": [],
    },
    "BLM": {
        "country": "Saint Barthélemy",
        "aliases": ["Saint Barthelemy", "St. Barths"],
        "parent": "FRA",
        "visa_free": [],
        "e_visa": [],
        "eta": [],
    },
    # British Overseas Territories (typically follow UK policy, but with variations)
    "AIA": {
        "country": "Anguilla",
        "aliases": [],
        "parent": "GBR",
        "visa_free": [],
        "e_visa": [],
        "eta": [],
    },
    "BMU": {
        "country": "Bermuda",
        "aliases": [],
        "parent": "GBR",
        "visa_free": [],
        "e_visa": [],
        "eta": [],
    },
    "CYM": {
        "country": "Cayman Islands",
        "aliases": [],
        "parent": "GBR",
        "visa_free": [],
        "e_visa": [],
        "eta": [],
    },
    "MSR": {
        "country": "Montserrat",
        "aliases": [],
        "parent": "GBR",
        "visa_free": [],
        "e_visa": [],
        "eta": [],
    },
    "TCA": {
        "country": "Turks and Caicos Islands",
        "aliases": [],
        "parent": "GBR",
        "visa_free": [],
        "e_visa": [],
        "eta": [],
    },
    "VGB": {
        "country": "Virgin Islands, British",
        "aliases": ["British Virgin Islands"],
        "parent": "GBR",
        "visa_free": [],
        "e_visa": [],
        "eta": [],
    },
    # US territories (follow US policy)
    "PRI": {
        "country": "Puerto Rico",
        "aliases": [],
        "parent": "USA",
        "visa_free": [],
        "e_visa": [],
        "eta": [],
    },
    "VIR": {
        "country": "Virgin Islands, U.S.",
        "aliases": ["US Virgin Islands", "United States Virgin Islands"],
        "parent": "USA",
        "visa_free": [],
        "e_visa": [],
        "eta": [],
    },
    "GUM": {
        "country": "Guam",
        "aliases": [],
        "parent": "USA",
        "visa_free": [],
        "e_visa": [],
        "eta": [],
    },
    "ASM": {
        "country": "American Samoa",
        "aliases": [],
        "parent": "USA",
        "visa_free": [],
        "e_visa": [],
        "eta": [],
    },
    "MNP": {
        "country": "Northern Mariana Islands",
        "aliases": [],
        "parent": "USA",
        "visa_free": [],
        "e_visa": [],
        "eta": [],
    },
}

def build_requirements_for_territory(info):
    """
    Build visa requirements for a territory.
    For territories with a parent country, copy the parent's visa policy.
    For independent nations, use conservative defaults + known agreements.
    """
    reqs = template_reqs.copy()

    if info["parent"] and info["parent"] in existing_iso3s:
        # Copy parent country's visa policy
        parent_rec = next((p for p in data["passports"] if p["iso3"] == info["parent"]), None)
        if parent_rec:
            for dest_iso3, status in parent_rec["requirements"].items():
                if dest_iso3 in reqs:
                    reqs[dest_iso3] = status

    # Apply known visa-free agreements
    for c in info["visa_free"]:
        if c in reqs:
            reqs[c] = "visa_free"

    # Apply known e-visa
    for c in info["e_visa"]:
        if c in reqs:
            reqs[c] = "e_visa"

    # Apply known ETA
    for c in info["eta"]:
        if c in reqs:
            reqs[c] = "eta"

    return reqs


# Track what was added
added = []
skipped = []
for iso3, info in sorted(territories_to_add.items()):
    if any(p["iso3"] == iso3 for p in data["passports"]):
        skipped.append(iso3)
        continue

    country = info["country"]
    parent_iso3 = info["parent"] if info["parent"] else "none"

    record = {
        "country": country,
        "iso3": iso3,
        "aliases": info["aliases"],
        "source": None,
        "requirements": build_requirements_for_territory(info)
    }
    data["passports"].append(record)
    added.append((iso3, country, parent_iso3))

if added:
    print(f"Added {len(added)} new passport records:")
    for iso3, name, parent in added:
        print(f"  {iso3}: {name} (parent: {parent})")
if skipped:
    print(f"\nSkipped {len(skipped)} already-existing records: {', '.join(skipped)}")

# Update template_reqs for all existing passports to include the new territories
# Actually, fill_missing_requirements in app.py handles this at runtime,
# but we should also ensure existing passport records include these territories
new_iso3s = {p["iso3"] for p in data["passports"]}

# For each existing passport, ensure it has entries for all new territories
for p in data["passports"]:
    for iso3 in new_iso3s:
        if iso3 not in p["requirements"]:
            p["requirements"][iso3] = "visa_required"

# Add freedom_of_movement for own country
for p in data["passports"]:
    if p["iso3"] in p["requirements"]:
        p["requirements"][p["iso3"]] = "freedom_of_movement"

# Sort passports by country name
data["passports"].sort(key=lambda p: p["country"])

# Write back
with open(VISA_DATA_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\nDone! Total passports: {len(data['passports'])}")
print(f"visa_data.json updated successfully.")