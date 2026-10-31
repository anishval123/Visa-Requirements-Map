"""
Comprehensive verification of ALL passport records in visa_data.json.
Checks every country and territory for data correctness.
"""
import json, sys
sys.path.insert(0, ".")
import pycountry

data = json.load(open("data/visa_data.json", "r"))
passports = data["passports"]
all_iso3s = {p["iso3"] for p in passports}

issues = []

print("=" * 80)
print("COMPREHENSIVE VERIFICATION OF ALL PASSPORT RECORDS")
print("=" * 80)

# ============================================================================
# 1. Verify every passport record has the required structure
# ============================================================================
print("\n--- 1. STRUCTURAL VALIDITY ---")
required_keys = {"country", "iso3", "aliases", "requirements"}
for p in passports:
    missing_keys = required_keys - set(p.keys())
    if missing_keys:
        issues.append(f"{p.get('iso3','???')}: Missing keys: {missing_keys}")
        print(f"  ✗ {p['iso3']}: Missing keys: {missing_keys}")
    if not isinstance(p.get("requirements"), dict):
        issues.append(f"{p.get('iso3','???')}: requirements is not a dict")
        print(f"  ✗ {p['iso3']}: requirements is not a dict")
    if p.get("iso3") not in p.get("requirements", {}):
        issues.append(f"{p['iso3']}: Missing freedom_of_movement for own passport")
        print(f"  ✗ {p['iso3']}: Missing freedom_of_movement for own passport")
    elif p["requirements"][p["iso3"]] != "freedom_of_movement":
        issues.append(f"{p['iso3']}: Own passport status is {p['requirements'][p['iso3']]}, expected freedom_of_movement")
        print(f"  ✗ {p['iso3']}: Own passport status is {p['requirements'][p['iso3']]}")

if not issues:
    print("  ✓ All records have valid structure")

# ============================================================================
# 2. Verify every passport has entries for ALL other passports
# ============================================================================
print(f"\n--- 2. DESTINATION COMPLETENESS ({len(passports)} passports, {len(all_iso3s)} destinations) ---")
incomplete_count = 0
for p in passports:
    reqs = p["requirements"]
    missing_dests = all_iso3s - set(reqs.keys())
    if missing_dests:
        incomplete_count += 1
        if incomplete_count <= 5:  # Show first 5
            print(f"  ✗ {p['country']} ({p['iso3']}): Missing {len(missing_dests)} destinations: {sorted(missing_dests)[:10]}...")

if incomplete_count == 0:
    print(f"  ✓ All {len(passports)} passport records have complete destination coverage")
else:
    issues.append(f"{incomplete_count} passports have incomplete destination coverage")

# ============================================================================
# 3. Verify pycountry matching for each ISO3
# ============================================================================
print(f"\n--- 3. PYCOUNTRY MATCHING ---")
unmatched = []
for p in passports:
    iso3 = p["iso3"]
    country = pycountry.countries.get(alpha_3=iso3)
    if country is None and iso3 != "XKX":  # XKX is Kosovo (user-defined)
        unmatched.append((iso3, p["country"]))
        print(f"  ✗ {iso3} ({p['country']}): Not found in pycountry")

if not unmatched:
    print(f"  ✓ All {len(passports)} ISO3 codes match pycountry (or are user-defined)")
else:
    issues.append(f"{len(unmatched)} ISO3 codes not in pycountry")

# ============================================================================
# 4. Specific check: Caribbean and territory countries
# ============================================================================
print(f"\n--- 4. CARIBBEAN & TERRITORY DATA CONSISTENCY ---")

# Verify specific territories have reasonable data
territory_checks = {
    "ABW": "Aruba",
    "AIA": "Anguilla", 
    "ATG": "Antigua and Barbuda",
    "BES": "Bonaire, Sint Eustatius and Saba",
    "BLM": "Saint Barthélemy",
    "BMU": "Bermuda",
    "BRB": "Barbados",
    "CUW": "Curaçao",
    "CYM": "Cayman Islands",
    "DMA": "Dominica",
    "GLP": "Guadeloupe",
    "GRD": "Grenada",
    "GUF": "French Guiana",
    "KNA": "Saint Kitts and Nevis",
    "LCA": "Saint Lucia",
    "MAF": "Saint Martin",
    "MSR": "Montserrat",
    "MTQ": "Martinique",
    "SXM": "Sint Maarten",
    "TCA": "Turks and Caicos Islands",
    "VCT": "Saint Vincent and the Grenadines",
    "VGB": "Virgin Islands, British",
    "PRI": "Puerto Rico",
    "VIR": "Virgin Islands, U.S.",
    "GUM": "Guam",
    "ASM": "American Samoa",
    "MNP": "Northern Mariana Islands",
}

for iso3, expected_name in sorted(territory_checks.items()):
    match = [p for p in passports if p["iso3"] == iso3]
    if not match:
        issues.append(f"{iso3} ({expected_name}): MISSING from passport list")
        print(f"  ✗ {iso3} ({expected_name}): MISSING")
        continue
    
    p = match[0]
    num_reqs = len(p["requirements"])
    
    # Check the country name is reasonable
    if p["country"].lower() != expected_name.lower() and p["country"].lower() != expected_name.lower():
        # Some have minor differences (e.g. "St." vs "Saint")
        print(f"  ? {iso3}: Passport says '{p['country']}' (expected '{expected_name}')")
    
    # Check it has a reasonable number of requirements
    if num_reqs < 100:
        issues.append(f"{iso3} ({p['country']}): Only {num_reqs} requirements")
        print(f"  ✗ {iso3} ({p['country']}): Only {num_reqs} requirements (expected ~{len(all_iso3s)})")
    else:
        print(f"  ✓ {iso3:5s} {p['country']:35s} {num_reqs} reqs")

# ============================================================================
# 5. Check status consistency for US destination data
# ============================================================================
print(f"\n--- 5. US PASSPORT DESTINATION DATA CHECK ---")
us_passport = next((p for p in passports if p["iso3"] == "USA"), None)
if us_passport:
    us_reqs = us_passport["requirements"]
    
    # Check specific known values
    known_statuses = {
        "ABW": "visa_free",    # Aruba
        "AIA": "visa_free",    # Anguilla
        "ATG": "visa_free",    # Antigua
        "BES": "visa_free",    # Bonaire
        "BLM": "visa_free",    # St Barths
        "BMU": "visa_free",    # Bermuda
        "BRB": "visa_free",    # Barbados
        "CUW": "visa_free",    # Curacao
        "CYM": "visa_free",    # Cayman
        "DMA": "visa_free",    # Dominica
        "GLP": "visa_free",    # Guadeloupe
        "GRD": "visa_free",    # Grenada
        "GUF": "visa_free",    # French Guiana
        "KNA": "eta",          # St Kitts (uses ESTA/ETA)
        "LCA": "visa_free",    # Saint Lucia
        "MAF": "visa_free",    # St Martin
        "MSR": "visa_free",    # Montserrat
        "MTQ": "visa_free",    # Martinique
        "SXM": "visa_free",    # Sint Maarten
        "TCA": "visa_free",    # Turks and Caicos
        "VCT": "visa_free",    # St Vincent
        "VGB": "visa_free",    # BVI
        "PRI": "freedom_of_movement",  # Puerto Rico (US territory)
        "VIR": "freedom_of_movement",  # US Virgin Islands
        "GUM": "freedom_of_movement",  # Guam
        "ASM": "freedom_of_movement",  # American Samoa
        "MNP": "freedom_of_movement",  # N. Mariana Islands
    }
    
    us_issues = 0
    for iso3, expected in known_statuses.items():
        actual = us_reqs.get(iso3, "MISSING")
        if actual != expected:
            issues.append(f"US->{iso3}: Expected '{expected}', got '{actual}'")
            print(f"  ✗ US -> {iso3:5s}: expected '{expected:25s}' got '{actual}'")
            us_issues += 1
    
    if us_issues == 0:
        print(f"  ✓ All {len(known_statuses)} Caribbean/territory statuses verified for US passport")

# ============================================================================
# 6. Spot-check a few territory passports against their parent
# ============================================================================
print(f"\n--- 6. PARENT-COUNTRY CONSISTENCY CHECK ---")
parent_checks = [
    ("ABW", "NLD", "Aruba", "Netherlands"),
    ("PRI", "USA", "Puerto Rico", "United States"),
    ("GUF", "FRA", "French Guiana", "France"),
    ("AIA", "GBR", "Anguilla", "United Kingdom"),
    ("CUW", "NLD", "Curaçao", "Netherlands"),
    ("GUM", "USA", "Guam", "United States"),
]
parent_issues = 0
for child_iso3, parent_iso3, child_name, parent_name in parent_checks:
    child = next((p for p in passports if p["iso3"] == child_iso3), None)
    parent = next((p for p in passports if p["iso3"] == parent_iso3), None)
    if not child or not parent:
        print(f"  ✗ Cannot find {child_iso3}/{parent_iso3} to compare")
        continue
    
    child_reqs = child["requirements"]
    parent_reqs = parent["requirements"]
    
    # Check a few key destinations match
    sample_dests = ["CAN", "MEX", "JPN", "GBR", "FRA", "DEU", "AUS", "BRA", "ZAF", "CHN", "IND", "RUS"]
    mismatches = 0
    for dest in sample_dests:
        if dest in child_reqs and dest in parent_reqs:
            if child_reqs[dest] != parent_reqs[dest]:
                mismatches += 1
    
    if mismatches == 0:
        print(f"  ✓ {child_name:35s} matches {parent_name} visa policy across all sampled destinations")
    else:
        print(f"  ? {child_name:35s} has {mismatches} differences from {parent_name} (may be intentional)")
        if mismatches > 3:
            issues.append(f"{child_iso3}: Too many differences from parent {parent_iso3}")
            parent_issues += 1

# ============================================================================
# 7. Check for missing failed_imports that should now be resolved
# ============================================================================
print(f"\n--- 7. FAILED IMPORTS REVIEW ---")
resolved_failed = []
still_failed = []
for f in data.get("failed_imports", []):
    found = False
    for p in passports:
        if p["country"].lower() in f["title"].lower() or p["iso3"].lower() in f["title"].lower():
            found = True
            break
    if found:
        resolved_failed.append(f)
    else:
        still_failed.append(f)

if resolved_failed:
    print(f"  ✓ {len(resolved_failed)} previously failed imports now resolved")
    for f in resolved_failed[:5]:
        print(f"    · {f['title']}")
if still_failed:
    print(f"  ? {len(still_failed)} failed imports remain")
    for f in still_failed[:5]:
        print(f"    · {f['title']}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)
if not issues:
    print(f"  ✓ ALL PASSED — {len(passports)} passport records, no issues found")
else:
    print(f"  ✗ {len(issues)} ISSUES FOUND:")
    for issue in issues:
        print(f"    · {issue}")

print(f"\n  Total passport records: {len(passports)}")
print(f"  Total destination ISO3s: {len(all_iso3s)}")