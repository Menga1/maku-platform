"""
MAKU i18n
=========
Minimal translation layer for the Streamlit UI. Per project guidelines,
the UI defaults to French, with English offered as an alternate. This file
holds ONLY display strings - all code, variables, and internal logic stay
in English, and no risk math lives here (see risk_engine.py).

Usage:
    from i18n import t, LANGUAGES
    lang = st.session_state.get("lang", "fr")
    st.header(t("solar_header", lang))
"""

LANGUAGES = {"Français": "fr", "English": "en"}
DEFAULT_LANG = "fr"

STRINGS = {
    # --- Global / sidebar ---
    "app_title": {"fr": "🏗️ MAKU", "en": "🏗️ MAKU"},
    "app_tagline": {
        "fr": "IA Multi-Environnement pour l'Évaluation des Risques Cinétiques - "
              "Mega-Souterrain, Offshore, Solaire, Tours & Data Centers",
        "en": "Multi-Environment AI for Kinetic Risk Assessment - Mega-Underground, "
              "Offshore, Solar, High-Rise & Data Center construction",
    },
    "lang_label": {"fr": "Langue", "en": "Language"},
    "ai_layer_header": {"fr": "Couche narrative IA (optionnelle)", "en": "AI Narrative Layer (optional)"},
    "api_key_label": {"fr": "Clé API Anthropic", "en": "Anthropic API key"},
    "api_key_help": {
        "fr": "Optionnel. Sans clé, MAKU fonctionne toujours grâce à ses formules de "
              "risque et ses recommandations de contrôle - la clé API ajoute uniquement "
              "une synthèse en langage naturel.",
        "en": "Optional. Without a key, MAKU still runs on its rule-based risk formulas "
              "and control recommendations - the API key only adds a plain-language "
              "narrative summary on top.",
    },
    "work_rate_label": {"fr": "Cadence de travail", "en": "Work rate"},
    "wr_light": {"fr": "légère", "en": "light"},
    "wr_moderate": {"fr": "modérée", "en": "moderate"},
    "wr_heavy": {"fr": "intense", "en": "heavy"},
    "work_rest_label": {"fr": "Cycle travail/repos", "en": "Work/rest cycle"},
    "work_rest_help": {
        "fr": "Catégories ACGIH TLV travail/repos utilisées pour les limites d'action "
              "liées au stress thermique",
        "en": "ACGIH TLV work/rest categories used for heat-stress action limits",
    },

    # --- Common result sections ---
    "risk_band_label": {"fr": "Niveau de risque", "en": "Risk Band"},
    "primary_hazard_label": {"fr": "Danger principal", "en": "Primary hazard"},
    "drivers_label": {"fr": "Facteurs environnementaux", "en": "Environmental drivers"},
    "controls_label": {"fr": "Mesures de contrôle recommandées", "en": "Recommended Controls"},
    "briefing_label": {"fr": "Synthèse IA", "en": "AI Briefing"},
    "yes": {"fr": "Oui", "en": "Yes"},
    "no": {"fr": "Non", "en": "No"},
    "acgih_exceeded_label": {"fr": "Limite ACGIH dépassée", "en": "ACGIH limit exceeded"},
    "vs_limit": {"fr": "vs limite", "en": "vs limit"},
    "safety_override": {"fr": "⚠️ DÉPASSEMENT DE SÉCURITÉ DÉCLENCHÉ", "en": "⚠️ SAFETY OVERRIDE TRIGGERED"},
    "run_button": {"fr": "Lancer l'évaluation", "en": "Run Risk Assessment"},

    # --- Data Feed Mode (Manuel/Simulation <-> Automatique/Temps Reel) ---
    "data_mode_header": {"fr": "Mode d'Alimentation des Données", "en": "Data Feed Mode"},
    "data_mode_prompt": {"fr": "Source des données environnementales", "en": "Environmental data source"},
    "data_mode_manual": {"fr": "Manuel / Simulation", "en": "Manual / Simulation"},
    "data_mode_auto": {"fr": "Automatique / Temps Réel", "en": "Automatic / Real-Time"},
    "feed_live_badge": {"fr": "Données en direct", "en": "Live data"},
    "feed_last_update": {"fr": "Dernière mise à jour", "en": "Last update"},
    "feed_error_banner": {
        "fr": "Flux de données indisponible - retour automatique en mode manuel/simulation.",
        "en": "Data feed unavailable - safely reverted to manual/simulation mode.",
    },
    "feed_not_armed_note": {
        "fr": "Mode automatique sélectionné. Activez le capteur ci-dessus pour démarrer le flux "
              "en direct, ou continuez avec les curseurs manuels ci-dessous.",
        "en": "Automatic mode selected. Enable the sensor toggle above to start the live "
              "stream, or continue with the manual sliders below.",
    },
    "telemetry_readout_label": {"fr": "Lecture télémétrie en direct", "en": "Live telemetry readout"},
    "context_only_note": {
        "fr": "Indicateur contextuel (non utilisé par le moteur de risque actuel).",
        "en": "Contextual indicator (not consumed by the current risk engine).",
    },
    "wave_height_label": {"fr": "Hauteur des vagues", "en": "Wave height"},
    "ocean_current_label": {"fr": "Vitesse du courant marin", "en": "Ocean current velocity"},
    "iot_tunnel_toggle_label": {
        "fr": "Activer le flux de la centrale de capteurs IoT (LoRaWAN Tunnel)",
        "en": "Enable IoT sensor-hub stream (LoRaWAN Tunnel)",
    },
    "crane_telemetry_toggle_label": {
        "fr": "Activer la télémétrie de l'Anémomètre Grue & Capteurs d'Oscillation",
        "en": "Enable Crane Anemometer & Oscillation Sensor telemetry",
    },
    "dc_telemetry_toggle_label": {
        "fr": "Activer le flux des Transformateurs de Courant & Sondes Thermiques",
        "en": "Enable Current Transformer & Thermal Probe stream",
    },

    # --- Dashboard (app.py) ---
    "dashboard_intro_header": {"fr": "Tableau de bord", "en": "Dashboard"},
    "dashboard_intro_body": {
        "fr": "MAKU évalue le risque de chantier en temps réel dans cinq environnements "
              "spécialisés, chacun avec son propre moteur de calcul transparent (WBGT, "
              "Humidex, ACGIH TLV, OEL, profil de vent en loi de puissance, méthode Lee "
              "pour l'arc électrique). Choisissez un module dans le menu de gauche pour "
              "lancer une évaluation.",
        "en": "MAKU assesses live site risk across five specialized environments, each "
              "driven by its own transparent calculation engine (WBGT, Humidex, ACGIH "
              "TLV, OEL, wind power-law profile, Lee arc-flash method). Pick a module "
              "from the left-hand menu to run an assessment.",
    },
    "dashboard_module_col_header": {"fr": "Modules disponibles", "en": "Available modules"},
    "dashboard_footer": {
        "fr": "MAKU - moteur de risque basé sur des règles (5 environnements) avec "
              "couche narrative IA optionnelle.",
        "en": "MAKU - rule-based risk engine (5 environments) with optional AI "
              "narrative layer.",
    },

    # --- Solar page ---
    "solar_header": {
        "fr": "☀️ Fermes solaires à grande échelle - Environnement désertique",
        "en": "☀️ Utility-Scale Solar Farms - Desert Environment",
    },
    "solar_caption": {
        "fr": "Albédo de surface + charge thermique radiative liée au GHI pour les "
              "équipes MEP d'installation de trackers/modules",
        "en": "Land surface albedo + GHI-driven radiant heat load forecasting for "
              "MEP tracker/module crews",
    },
    "solar_env_data_header": {"fr": "Données environnementales", "en": "Environmental data"},
    "solar_realtime_header": {
        "fr": "Évaluation en temps réel de l'équipe MEP",
        "en": "Real-Time MEP Crew Assessment",
    },
    "solar_temp_label": {"fr": "Température ambiante (°C)", "en": "Ambient temperature (°C)"},
    "solar_ghi_label": {
        "fr": "Irradiation Globale Horizontale (GHI, W/m²)",
        "en": "Global Horizontal Irradiation (GHI, W/m²)",
    },
    "solar_uv_label": {"fr": "Indice UV", "en": "UV Index"},
    "solar_surface_label": {
        "fr": "Type de surface (simulation capteurs SIG)",
        "en": "Surface type (simulated GIS sensor feed)",
    },
    "solar_telemetry_toggle_label": {
        "fr": "Activer le flux météo solaire Open-Meteo",
        "en": "Enable Open-Meteo solar weather feed",
    },
    "surf_pure_desert_sand": {"fr": "Sable désertique pur", "en": "Pure desert sand"},
    "surf_silicon_pv_panels": {"fr": "Panneaux PV en silicium", "en": "Silicon PV panels"},
    "surf_hybrid_assembly_zone": {"fr": "Zone d'assemblage hybride", "en": "Hybrid assembly zone"},
    "perceived_temp_label": {
        "fr": "Température perçue (corrigée)",
        "en": "Perceived Temperature (Corrected)",
    },
    "albedo_delta_label": {"fr": "Albédo", "en": "Albedo"},
    "risk_level_label": {"fr": "Niveau de Risque", "en": "Risk Level"},
    "shift_rotation_label": {"fr": "Rotation des Équipes", "en": "Team Rotation"},
    "solar_critical_alert": {
        "fr": "🚨 **ALERTE CRITIQUE :** Risque d'insolation aiguë immédiat pour l'assemblage "
              "mécanique des trackers.",
        "en": "🚨 **CRITICAL ALERT:** Immediate acute heat-stroke risk for tracker "
              "mechanical assembly.",
    },
    "solar_high_alert": {
        "fr": "⚠️ **ATTENTION :** Risque élevé de stress thermique. Rotation obligatoire.",
        "en": "⚠️ **WARNING:** High heat-stress risk. Mandatory rotation required.",
    },
    "solar_standard_ok": {
        "fr": "✅ Conditions opérationnelles standards. Assurez l'hydratation continue "
              "des techniciens.",
        "en": "✅ Standard operating conditions. Ensure continuous technician hydration.",
    },

    # --- Offshore page ---
    "offshore_header": {
        "fr": "🌊 Pétrole & gaz offshore - Environnement marin",
        "en": "🌊 Offshore Oil & Gas - Marine Environment",
    },
    "offshore_caption": {
        "fr": "Matrice de risque Humidex marine + seuils opérationnels vent/houle pour "
              "les équipes de soudure, tuyauterie et échafaudage",
        "en": "Marine Humidex Risk Matrix + wind/wave operational gating for welding, "
              "pipe-fitting, scaffolding crews",
    },
    "wind_gate_label": {"fr": "Seuil vent", "en": "Wind gate"},
    "wave_gate_label": {"fr": "Seuil houle", "en": "Wave gate"},
    "offshore_env_data_header": {
        "fr": "Télémétrie Bouée GIS (Simulation)",
        "en": "GIS Buoy Telemetry (Simulated)",
    },
    "offshore_realtime_header": {
        "fr": "Évaluation en Temps Réel des Opérations Marines",
        "en": "Real-Time Marine Operations Assessment",
    },
    "offshore_temp_label": {"fr": "Température ambiante (°C)", "en": "Ambient temperature (°C)"},
    "offshore_rh_label": {"fr": "Humidité relative (%)", "en": "Relative humidity (%)"},
    "offshore_wind_label": {"fr": "Vitesse du vent (nœuds)", "en": "Wind speed (knots)"},
    "humidex_label": {"fr": "Humidex", "en": "Humidex"},
    "wind_status_label": {"fr": "Statut du vent", "en": "Wind Status"},
    "wind_status_normal": {"fr": "Opérations normales", "en": "Normal Operations"},
    "wind_status_restricted": {
        "fr": "Restreint - Surveillance rapprochée",
        "en": "Restricted - Monitor Closely",
    },
    "wind_status_suspended": {
        "fr": "Suspendu - Danger grue/levage",
        "en": "Suspended - Crane/Lifting Danger",
    },
    "offshore_elevated_alert": {
        "fr": "⚠️ **ATTENTION :** Stress thermique marin élevé. Resserrez la rotation "
              "des équipes de soudure/tuyauterie et surveillez la tendance Humidex.",
        "en": "⚠️ **WARNING:** Elevated marine heat stress. Tighten welding/pipe-fitting "
              "crew rotation and monitor the Humidex trend.",
    },
    "offshore_standard_ok": {
        "fr": "✅ Conditions opérationnelles marines normales. Maintenir le protocole "
              "HSE standard.",
        "en": "✅ Standard marine operating conditions. Maintain standard HSE protocol.",
    },

    # --- Underground page ---
    "underground_header": {
        "fr": "🚇 Métros & tunnels - Infrastructure souterraine",
        "en": "🚇 Metros & Tunnels - Underground Substructure Infrastructure",
    },
    "underground_caption": {
        "fr": "Charge thermique du tunnelier + corrélation OEL en temps réel générant "
              "des dépassements de sécurité prédictifs pour les équipes électriques MEP",
        "en": "TBM heat load + real-time OEL correlation generating predictive safety "
              "overrides for MEP electrical crews",
    },
    "gas_exceeds_label": {"fr": "Limite gaz OEL dépassée", "en": "Gas OEL exceeded"},
    "dust_exceeds_label": {"fr": "Limite poussière OEL dépassée", "en": "Dust OEL exceeded"},
    "underground_env_data_header": {
        "fr": "Télémétrie 3D SIG Souterraine (Simulation)",
        "en": "3D Subsurface GIS Telemetry (Simulated)",
    },
    "underground_realtime_header": {
        "fr": "Évaluation en Temps Réel des Équipes MEP Électriques",
        "en": "Real-Time MEP Electrical Crew Assessment",
    },
    "underground_ambient_temp_label": {"fr": "Température ambiante (°C)", "en": "Ambient temperature (°C)"},
    "underground_geo_humidity_label": {
        "fr": "Humidité géothermique piégée (%)",
        "en": "Trapped geothermal humidity (%)",
    },
    "underground_pm25_label": {
        "fr": "Particules en suspension PM2.5 (µg/m³)",
        "en": "Airborne particulate matter PM2.5 (µg/m³)",
    },
    "underground_co_label": {"fr": "Monoxyde de carbone CO (ppm)", "en": "Carbon monoxide CO (ppm)"},
    "underground_perceived_temp_label": {
        "fr": "Température perçue (chaleur piégée)",
        "en": "Perceived Temperature (Trapped Heat)",
    },
    "underground_critical_alert": {
        "fr": "🚨 **DÉPASSEMENT DE SÉCURITÉ CRITIQUE :** Halte immédiate des travaux de "
              "câblage haute tension MEP. Évacuer le front de taille et revérifier "
              "la ventilation avant tout nouveau test.",
        "en": "🚨 **CRITICAL SAFETY OVERRIDE:** Immediate halt to MEP high-voltage cabling "
              "work. Evacuate the excavation face and re-verify ventilation before re-testing.",
    },
    "underground_high_alert": {
        "fr": "⚠️ **ATTENTION :** Stress thermique et/ou qualité de l'air en approche des "
              "limites OEL. Resserrez la rotation des équipes et surveillez les capteurs.",
        "en": "⚠️ **WARNING:** Heat stress and/or air quality approaching OEL limits. "
              "Tighten crew rotation and watch the sensor trend closely.",
    },
    "underground_standard_ok": {
        "fr": "✅ Conditions souterraines standards. Maintenir la cadence de surveillance "
              "OEL et thermique.",
        "en": "✅ Standard underground conditions. Maintain the OEL and heat monitoring cadence.",
    },

    # --- High-Rise page ---
    "highrise_header": {
        "fr": "🏙️ Construction de tours - Environnement urbain vertical",
        "en": "🏙️ High-Rise Building Construction - Vertical Urban Environment",
    },
    "highrise_caption": {
        "fr": "Jumeau numérique BIM 3D + télémétrie d'anémomètres multi-niveaux pour "
              "une matrice de risque de cisaillement du vent étage par étage",
        "en": "3D BIM digital twin + multi-level anemometer telemetry driving a "
              "floor-by-floor wind-shear risk matrix",
    },
    "crane_gate_label": {"fr": "Seuil grue", "en": "Crane gate"},
    "facade_gate_label": {"fr": "Seuil façade/accès suspendu", "en": "Facade/access gate"},
    "fall_arrest_alert": {
        "fr": "⚠️ ALERTE ANTICHUTE / ACCÈS SUSPENDU",
        "en": "⚠️ FALL-ARREST / SUSPENDED-ACCESS ALERT",
    },
    "highrise_env_data_header": {
        "fr": "Télémétrie BIM 3D / Anémomètre (Simulation)",
        "en": "3D BIM / Anemometer Telemetry (Simulated)",
    },
    "highrise_realtime_header": {
        "fr": "Évaluation en Temps Réel Grue & Accès Suspendu",
        "en": "Real-Time Crane & Suspended-Access Assessment",
    },
    "highrise_ground_wind_label": {
        "fr": "Vitesse du vent au sol (nœuds)",
        "en": "Ground wind speed (knots)",
    },
    "highrise_floor_level_label": {"fr": "Étage de travail actuel", "en": "Current working floor level"},
    "highrise_crane_load_label": {
        "fr": "Masse de charge du levage (tonnes)",
        "en": "Crane lift load mass (tons)",
    },
    "scaled_wind_label": {
        "fr": "Vent amplifié en hauteur (nœuds)",
        "en": "Scaled Wind at Height (knots)",
    },
    "oscillation_index_label": {
        "fr": "Indice d'oscillation de charge",
        "en": "Load Oscillation Index",
    },
    "highrise_critical_alert": {
        "fr": "🚨 **DÉPASSEMENT DE SÉCURITÉ CRITIQUE :** Suspension immédiate de tous les "
              "levages par grue et des travaux de façade/mur-rideau en hauteur. Vérifiez "
              "les points d'ancrage antichute avant toute reprise.",
        "en": "🚨 **CRITICAL SAFETY OVERRIDE:** Immediate suspension of all crane lifts "
              "and facade/curtain-wall work at height. Recheck fall-arrest tie-off points "
              "before resuming.",
    },
    "highrise_high_alert": {
        "fr": "⚠️ **ATTENTION :** Cisaillement du vent élevé en hauteur. Informez "
              "l'opérateur de grue et retardez les levages non critiques.",
        "en": "⚠️ **WARNING:** High wind shear at this floor level. Notify the crane "
              "operator and delay non-critical lifts.",
    },
    "highrise_standard_ok": {
        "fr": "✅ Conditions de vent standards en hauteur. Maintenir la surveillance "
              "anémométrique à chaque poste.",
        "en": "✅ Standard wind conditions at height. Maintain anemometer monitoring each shift.",
    },

    # --- Data Center page ---
    "datacenter_header": {
        "fr": "🖥️ Construction & mise en service de data centers - Environnement "
              "critique contrôlé",
        "en": "🖥️ Data Center Construction & Commissioning - Controlled Critical "
              "Environment",
    },
    "datacenter_caption": {
        "fr": "Cartographie thermique IoT allée chaude/froide + méthode Lee pour "
              "l'arc électrique, croisée avec les conditions d'espace confiné et "
              "d'agent propre",
        "en": "Rack-level IoT hot-aisle/cold-aisle thermal mapping + Lee-method "
              "arc-flash screening, cross-referenced against confined-space and "
              "clean-agent commissioning conditions",
    },
    "esd_risk_label": {"fr": "Risque ESD", "en": "ESD risk"},
    "confined_clean_agent_label": {
        "fr": "Espace confiné + agent propre présent",
        "en": "Confined space + clean-agent present",
    },
    "datacenter_env_data_header": {
        "fr": "Télémétrie IoT Micro-SIG au Niveau des Baies (Simulation)",
        "en": "Rack-Level Micro-GIS IoT Telemetry (Simulated)",
    },
    "datacenter_realtime_header": {
        "fr": "Évaluation en Temps Réel - Électrique, Thermique & Suppression Incendie",
        "en": "Real-Time Electrical, Thermal & Fire-Suppression Assessment",
    },
    "datacenter_load_label": {"fr": "Charge électrique en direct (kW)", "en": "Live electrical load (kW)"},
    "datacenter_hot_aisle_label": {
        "fr": "Température allée chaude (°C)",
        "en": "Hot-aisle temperature (°C)",
    },
    "datacenter_confined_label": {
        "fr": "Espace de travail confiné (plénum/faux-plafond)",
        "en": "Confined ceiling-void workspace",
    },
    "datacenter_gas_armed_label": {
        "fr": "Système de suppression incendie gazeux armé",
        "en": "Gaseous fire-suppression system armed",
    },
    "arc_flash_energy_label": {
        "fr": "Énergie incidente arc électrique (cal/cm²)",
        "en": "Arc-Flash Incident Energy (cal/cm²)",
    },
    "thermal_differential_label": {
        "fr": "Différentiel thermique allée chaude/froide (°C)",
        "en": "Hot/Cold-Aisle Thermal Differential (°C)",
    },
    "datacenter_critical_alert": {
        "fr": "🚨 **DÉPASSEMENT DE SÉCURITÉ CRITIQUE :** Halte immédiate des travaux de "
              "mise en service électrique/mécanique/suppression incendie dans cette zone. "
              "Désénergisez avant toute intervention et revérifiez les conditions.",
        "en": "🚨 **CRITICAL SAFETY OVERRIDE:** Immediate halt to electrical/mechanical/"
              "fire-suppression commissioning work in this zone. De-energize before any "
              "work and recheck conditions before resuming.",
    },
    "datacenter_high_alert": {
        "fr": "⚠️ **ATTENTION :** Risque élevé d'arc électrique ou de stress thermique "
              "allée chaude/froide. Confirmez le classement EPI et resserrez la rotation "
              "des équipes.",
        "en": "⚠️ **WARNING:** Elevated arc-flash or hot/cold-aisle thermal risk. Confirm "
              "PPE rating and tighten commissioning crew rotation.",
    },
    "datacenter_standard_ok": {
        "fr": "✅ Conditions standards de mise en service. Maintenir la surveillance "
              "thermique, arc électrique et espace confiné.",
        "en": "✅ Standard commissioning conditions. Maintain thermal, arc-flash, and "
              "confined-space monitoring.",
    },
}


def t(key: str, lang: str = DEFAULT_LANG) -> str:
    """Look up a UI string by key for the given language code (defaults to French)."""
    entry = STRINGS.get(key)
    if entry is None:
        return key
    return entry.get(lang, entry.get(DEFAULT_LANG, key))


def language_selector(st_module, sidebar=True, key: str = "lang") -> str:
    """
    Renders the shared language selector and returns the resolved language
    code ("fr"/"en"). Backed by st.session_state so the choice persists as
    the user navigates between pages in the multipage app.
    """
    target = st_module.sidebar if sidebar else st_module
    if key not in st_module.session_state:
        st_module.session_state[key] = DEFAULT_LANG
    current_label = [k for k, v in LANGUAGES.items() if v == st_module.session_state[key]][0]
    chosen_label = target.selectbox(
        t("lang_label", st_module.session_state[key]),
        list(LANGUAGES.keys()),
        index=list(LANGUAGES.keys()).index(current_label),
        key="lang_selector_widget",
    )
    st_module.session_state[key] = LANGUAGES[chosen_label]
    return st_module.session_state[key]
