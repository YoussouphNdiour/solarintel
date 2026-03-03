"""
Constantes partagées pour le pipeline SolarIntel.
"""

# ---------------------------------------------------------------------------
# Ollama / LLM
# ---------------------------------------------------------------------------
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "mistral"  # modèle par défaut, surchargeable par env

# ---------------------------------------------------------------------------
# UI – Thème Engineering
# ---------------------------------------------------------------------------
UI_THEME = {
    "primary": "#0EA5E9",       # Solar Blue (sky-500)
    "primary_dark": "#0369A1",  # sky-700
    "accent": "#F59E0B",        # Amber-500 – énergie solaire
    "background": "#0F172A",    # Slate-900
    "surface": "#1E293B",       # Slate-800
    "text": "#F8FAFC",          # Slate-50
    "border": "#334155",        # Slate-700
    "success": "#22C55E",       # Green-500
    "error": "#EF4444",         # Red-500
    "font_mono": "JetBrains Mono, monospace",
    "font_sans": "Inter, system-ui, sans-serif",
    "framework": "Shadcn/UI + TailwindCSS",
}

# ---------------------------------------------------------------------------
# ArcGIS – Modules requis par le Frontend Agent
# ---------------------------------------------------------------------------
ARCGIS_MODULES = [
    "esri/Map",
    "esri/views/MapView",
    "esri/widgets/Sketch",
    "esri/widgets/Sketch/SketchViewModel",
    "esri/geometry/geometryEngine",
    "esri/geometry/Polygon",
    "esri/geometry/Point",
    "esri/layers/GraphicsLayer",
    "esri/layers/TileLayer",
    "esri/Graphic",
    "esri/symbols/SimpleFillSymbol",
    "esri/symbols/SimpleMarkerSymbol",
]

ARCGIS_BASEMAPS = {
    "orthophoto": "satellite",
    "topo": "topo-vector",
    "streets": "streets-navigation-v2",
}

# ---------------------------------------------------------------------------
# pvlib – Modules requis par le Backend Agent
# ---------------------------------------------------------------------------
PVLIB_MODULES = [
    "pvlib.location.Location",
    "pvlib.pvsystem.PVSystem",
    "pvlib.modelchain.ModelChain",
    "pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS",
    "pvlib.irradiance.get_total_irradiance",
    "pvlib.iotools.get_pvgis_tmy",
    "pvlib.solarposition.get_solarposition",
]

# ---------------------------------------------------------------------------
# Panneau – Spécifications par défaut (surchargeable par l'UI)
# ---------------------------------------------------------------------------
DEFAULT_PANEL = {
    "brand": "JA Solar",
    "model": "JAM72S30-545/MR",
    "power_wc": 545,
    "width_mm": 1134,
    "height_mm": 2278,
    "efficiency": 0.211,
    "temp_coeff_pmax": -0.350,  # %/°C
    "noct": 45,                 # °C
}

# ---------------------------------------------------------------------------
# Économique – Défauts Afrique de l'Ouest (XOF)
# ---------------------------------------------------------------------------
ECONOMIC_DEFAULTS = {
    "currency": "XOF",
    "electricity_price_kwh": 118,   # FCFA/kWh (tarif SENELEC tranche 2)
    "annual_increase_pct": 3.5,
    "system_lifetime_years": 25,
    "degradation_pct_year": 0.5,
    "cost_per_wc_xof": 650,
}

# ---------------------------------------------------------------------------
# Coordonnées par défaut – Dakar, Sénégal
# ---------------------------------------------------------------------------
DEFAULT_LOCATION = {
    "latitude": 14.6928,
    "longitude": -17.4467,
    "altitude": 22,
    "timezone": "Africa/Dakar",
    "name": "Dakar, Sénégal",
}
