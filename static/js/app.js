const WORLD_TOPOJSON_URL = "/static/data/countries-50m.json";

const STATUS_META = {
  freedom_of_movement: { label: "Freedom of movement", color: "#1a9850" },
  entry_restricted: { label: "Entry restricted", color: "#5c1a1a" },
  visa_free: { label: "Visa free", color: "#66bd63" },
  visa_on_arrival: { label: "Visa on arrival", color: "#fdae61" },
  e_visa: { label: "E-visa", color: "#3288bd" },
  eta: { label: "Electronic travel authorization", color: "#5e4fa2" },
  esta: { label: "ESTA / travel authorization", color: "#7b3294" },
  visa_required: { label: "Visa required", color: "#d73027" },
  disputed: { label: "Disputed territory", color: "#cccccc" },
  unknown: { label: "No Wikipedia data", color: "#b9c2cb" }
};

let worldFeatures = [];
let activeRequirements = {};

const svg = d3.select("#world-map");
const mapNode = document.querySelector("#map");
const tooltip = document.querySelector("#map-tooltip");
const statusMessage = document.querySelector("#status-message");
const countryInput = document.querySelector("#country-input");
const countryForm = document.querySelector("#country-form");
const countryOptions = document.querySelector("#country-options");

// Map of disputed/no-ID territory names to known numeric codes
const TERRITORY_IDS = {
  "Kosovo": "XK",
  "Somaliland": null,
  "N. Cyprus": "196",
  "Siachen Glacier": "586",  // Pakistan/India disputed - use Pakistan's code
  "Indian Ocean Ter.": null
};

function numericCountryId(feature) {
  if (feature.id == null) {
    const name = getCountryName(feature);
    const mapped = TERRITORY_IDS[name];
    return mapped || null;
  }
  return String(feature.id).padStart(3, "0");
}

function getRequirement(feature) {
  const fid = numericCountryId(feature);
  if (fid === null) return "disputed";
  return activeRequirements[fid] || "unknown";
}

function getCountryName(feature) {
  return feature.properties.name || "Unknown country";
}

function colorFor(feature) {
  const status = getRequirement(feature);
  return (STATUS_META[status] || STATUS_META.unknown).color;
}

function renderMap() {
  if (!worldFeatures.length) return;

  const width = Math.max(320, mapNode.clientWidth);
  const height = Math.max(360, mapNode.clientHeight);
  const projection = d3.geoNaturalEarth1().fitExtent(
    [
      [24, 24],
      [width - 24, height - 24]
    ],
    { type: "Sphere" }
  );
  const path = d3.geoPath(projection);
  const graticule = d3.geoGraticule10();

  svg.attr("viewBox", `0 0 ${width} ${height}`);
  svg.selectAll("*").remove();

  svg.append("path").attr("class", "sphere").attr("d", path({ type: "Sphere" }));
  svg.append("path").attr("class", "graticule").attr("d", path(graticule));

  svg
    .append("g")
    .selectAll("path")
    .data(worldFeatures)
    .join("path")
    .attr("class", "country")
    .attr("d", path)
    .attr("fill", colorFor)
    .attr("opacity", (feature) => (getRequirement(feature) === "unknown" ? 0.6 : 0.92))
    .on("pointermove", (event, feature) => {
      const status = getRequirement(feature);
      const meta = STATUS_META[status] || STATUS_META.unknown;
      tooltip.hidden = false;
      tooltip.innerHTML = `<strong>${getCountryName(feature)}</strong><br>${meta.label}`;
      tooltip.style.left = `${event.offsetX}px`;
      tooltip.style.top = `${event.offsetY}px`;
    })
    .on("pointerleave", () => {
      tooltip.hidden = true;
    });
}

function refreshCountryStyles() {
  svg
    .selectAll(".country")
    .attr("fill", colorFor)
    .attr("opacity", (feature) => (getRequirement(feature) === "unknown" ? 0.6 : 0.92));
}

function renderLegend() {
  const legendItems = document.querySelector("#legend-items");
  legendItems.className = "legend-grid";
  legendItems.innerHTML = Object.values(STATUS_META)
    .map(
      (item) => `
        <div class="legend-item">
          <span class="swatch" style="background:${item.color}"></span>
          <span>${item.label}</span>
        </div>
      `
    )
    .join("");
}

async function loadWorldMap() {
  const topology = await d3.json(WORLD_TOPOJSON_URL);
  if (!topology?.objects?.countries) {
    throw new Error("Could not load world map data.");
  }

  worldFeatures = topojson
    .feature(topology, topology.objects.countries)
    .features.filter((feature) => numericCountryId(feature) !== "010");
  renderMap();
}

async function loadCountryOptions() {
  const response = await fetch("/api/countries");
  if (!response.ok) return;

  const countries = await response.json();
  countryOptions.innerHTML = countries
    .map((country) => `<option value="${country.country}"></option>`)
    .join("");
}

async function loadVisaData(countryName) {
  statusMessage.textContent = `Loading visa requirements for ${countryName}...`;

  const response = await fetch(`/api/visa/${encodeURIComponent(countryName)}`);
  const data = await response.json();

  if (!response.ok) {
    activeRequirements = {};
    refreshCountryStyles();
    statusMessage.textContent = data.error || "No visa data found.";
    return;
  }

  activeRequirements = data.requirements_numeric || {};
  refreshCountryStyles();
  const quality =
    data.data_quality === "wikipedia"
      ? "Wikipedia-sourced data loaded"
      : "No Wikipedia destination data is available yet";
  statusMessage.textContent = `${data.passport_country} passport loaded. ${quality}. Updated ${data.last_updated}.`;
}

countryForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const countryName = countryInput.value.trim();
  if (countryName) {
    loadVisaData(countryName);
  }
});

window.addEventListener("resize", () => {
  window.requestAnimationFrame(renderMap);
});

async function boot() {
  renderLegend();
  await Promise.all([loadWorldMap(), loadCountryOptions()]);
  countryInput.value = "United States";
  await loadVisaData(countryInput.value);
}

boot().catch((error) => {
  statusMessage.textContent = error.message;
});
