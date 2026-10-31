"""Check every territory and small nation for data completeness."""
import json, sys, pycountry
sys.path.insert(0, ".")
from app import app

data = json.load(open("data/visa_data.json", "r"))
all_passports = {p["iso3"] for p in data["passports"]}

with app.test_client() as c:
    r = c.get("/api/visa/United%20States").get_json()
    req = r["requirements"]
    num = r["requirements_numeric"]

# All territories that should have destination data
all_territories = {
    "ATG": "Antigua and Barbuda",
    "ABW": "Aruba",
    "DMA": "Dominica",
    "LCA": "Saint Lucia",
    "VCT": "St. Vincent and Grenadines",
    "BRB": "Barbados",
    "GRD": "Grenada",
    "KNA": "St. Kitts and Nevis",
    "COK": "Cook Islands",
    "NIU": "Niue",
    "CYM": "Cayman Islands",
    "AIA": "Anguilla",
    "MSR": "Montserrat",
    "VGB": "British Virgin Islands",
    "TCA": "Turks and Caicos Islands",
    "BMU": "Bermuda",
    "CUW": "Curacao",
    "SXM": "Sint Maarten",
    "BES": "Bonaire, Sint Eustatius and Saba",
    "GUF": "French Guiana",
    "MTQ": "Martinique",
    "GLP": "Guadeloupe",
    "MYT": "Mayotte",
    "REU": "Reunion",
    "NCL": "New Caledonia",
    "PYF": "French Polynesia",
    "WLF": "Wallis and Futuna",
    "SPM": "St. Pierre and Miquelon",
    "BLM": "Saint Barthelemy",
    "MAF": "Saint Martin",
    "GIB": "Gibraltar",
    "GGY": "Guernsey",
    "JEY": "Jersey",
    "IMN": "Isle of Man",
    "FRO": "Faroe Islands",
    "ALA": "Aland Islands",
    "HKG": "Hong Kong",
    "MAC": "Macao",
    "SJM": "Svalbard and Jan Mayen",
    "PRI": "Puerto Rico",
    "VIR": "Virgin Islands, U.S.",
    "GUM": "Guam",
    "ASM": "American Samoa",
    "MNP": "Northern Mariana Islands",
    "NFK": "Norfolk Island",
    "PCN": "Pitcairn",
    "SHN": "Saint Helena",
    "FLK": "Falkland Islands",
    "IOT": "British Indian Ocean Territory",
    "ATF": "French Southern Territories",
    "BVT": "Bouvet Island",
    "HMD": "Heard Island",
    "SGS": "South Georgia",
    "ESH": "Western Sahara",
    "TKL": "Tokelau",
    "WLF": "Wallis and Futuna",
    "SYC": "Seychelles",
    "WSM": "Samoa",
    "TON": "Tonga",
    "PLW": "Palau",
    "FSM": "Micronesia",
    "MHL": "Marshall Islands",
    "KIR": "Kiribati",
    "TUV": "Tuvalu",
    "NRU": "Nauru",
    "SLB": "Solomon Islands",
    "VUT": "Vanuatu",
    "MDV": "Maldives",
    "MUS": "Mauritius",
    "SGP": "Singapore",
    "BHR": "Bahrain",
    "QAT": "Qatar",
    "OMN": "Oman",
    "KWT": "Kuwait",
    "UKR": "Ukraine",
    "SRB": "Serbia",
    "MNE": "Montenegro",
    "BIH": "Bosnia",
    "MKD": "North Macedonia",
    "ALB": "Albania",
    "MLT": "Malta",
    "CYP": "Cyprus",
    "ISL": "Iceland",
    "LIE": "Liechtenstein",
    "MCO": "Monaco",
    "SMR": "San Marino",
    "VAT": "Vatican City",
}

print(f"{'ISO3':6s} {'Name':30s} {'Dest':10s} {'Numeric':10s} {'Searchable':12s}")
print("="*70)

missing_dest = []
for iso3 in sorted(all_territories.keys()):
    name = all_territories[iso3]
    dest_status = req.get(iso3, "M")
    is_passport = "YES" if iso3 in all_passports else "NO"
    
    country = pycountry.countries.get(alpha_3=iso3)
    if country:
        numeric = str(country.numeric).zfill(3)
        num_status = num.get(numeric, "M")
    else:
        numeric = "N/A"
        num_status = "M"
    
    print(f"{iso3:6s} {name:30s} {dest_status:10s} {num_status:10s} {is_passport:12s}")
    
    if dest_status == "M" or num_status == "M":
        missing_dest.append((iso3, name))

if missing_dest:
    print(f"\n\n=== MISSING DESTINATION DATA ({len(missing_dest)}) ===")
    for iso3, name in missing_dest:
        print(f"  {iso3} ({name})")
else:
    print("\n\n✓ ALL territories have destination data for US passport!")