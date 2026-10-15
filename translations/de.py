"""German translations for MAKU - see translations/__init__.py.

Generated from the English source strings; edit the values, never the keys.
"""

UI = {
    "acclimatized_label": "Hitzeakklimatisierte Arbeitskraft",
    "advanced_heat_panel_title": "Erweiterte Hitzestressbewertung (ACGIH/ISO 7243)",
    "air_quality_no2_label": "NO₂ (µg/m³)",
    "air_quality_o3_label": "O₃ (µg/m³)",
    "air_quality_pm10_label": "PM10 (µg/m³)",
    "albedo_delta_label": "Albedo",
    "arc_flash_energy_label": "Störlichtbogen-Einwirkenergie (cal/cm²)",
    "clothing_type_label": "Kleidung / PSA-Typ",
    "confined_clean_agent_label": "Enger Raum + Löschmittel vorhanden",
    "context_only_note": "Kontextindikator (wird von der aktuellen Risiko-Engine nicht verwendet).",
    "crane_gate_label": "Kran-Freigabe",
    "crane_telemetry_toggle_label": "Kran-Anemometer- und Pendelsensor-Telemetrie aktivieren",
    "ctv_status_label": "CTV-Transferstatus",
    "data_mode_auto": "Automatisch / Echtzeit",
    "data_mode_header": "Datenquellen-Modus",
    "data_mode_manual": "Manuell / Simulation",
    "data_mode_prompt": "Quelle der Umweltdaten",
    "datacenter_caption": "Störlichtbogen-Einwirkenergie nach Lee-Methode und Temperaturdifferenz Warm-/Kaltgang, abgeglichen mit Bedingungen für enge Räume und Inertgas-Löschanlagen bei der Inbetriebnahme",
    "datacenter_confined_label": "Enger Zwischendeckenbereich",
    "datacenter_env_data_header": "IoT-Telemetrie auf Rack-Ebene mit Mikro-GIS (simuliert)",
    "datacenter_gas_armed_label": "Gaslöschanlage scharf geschaltet",
    "datacenter_header": "🖥️ Rechenzentrumsbau & Inbetriebnahme - Kontrollierte kritische Umgebung",
    "datacenter_hot_aisle_label": "Warmgang-Temperatur (°C)",
    "datacenter_load_label": "Aktuelle elektrische Last (kW)",
    "datacenter_realtime_header": "Echtzeitbewertung Elektrik, Wärme & Löschanlage",
    "dc_telemetry_toggle_label": "Stromwandler- und Temperaturfühler-Datenstrom aktivieren",
    "dust_exceeds_label": "Staub-Grenzwert überschritten",
    "esd_risk_label": "ESD-Risiko",
    "facade_gate_label": "Fassaden-/Zugangsfreigabe",
    "fall_arrest_alert": "⚠️ ABSTURZSICHERUNG / HÄNGEZUGANG - WARNUNG",
    "feed_error_banner": "Datenquelle nicht verfügbar - sicher auf manuellen/Simulationsmodus zurückgesetzt.",
    "feed_last_update": "Letzte Aktualisierung",
    "feed_live_badge": "Live-Daten",
    "feed_not_armed_note": "Automatikmodus gewählt. Aktivieren Sie oben den Sensorschalter, um den Live-Datenstrom zu starten, oder arbeiten Sie unten mit den manuellen Schiebereglern weiter.",
    "ffp3_required_warning": "⚠️ Erhöhte Luftverschmutzung - FFP3-Atemschutzmaske vor Arbeitsbeginn empfohlen.",
    "field_inspection_accuracy_label": "Genauigkeit",
    "field_inspection_button": "🛰️ Meinen GPS-Standort ermitteln",
    "field_inspection_caption": "Nutzen Sie das GPS Ihres Geräts vor Ort, um automatisch den nächstgelegenen simulierten MAKU-Standort zu finden.",
    "field_inspection_closest_site_label": "Nächster simulierter Standort",
    "field_inspection_denied": "Standortzugriff verweigert. Aktivieren Sie die Standortberechtigung in den Browsereinstellungen, um diese Funktion zu nutzen.",
    "field_inspection_distance_label": "Entfernung",
    "field_inspection_error_generic": "Standortfehler",
    "field_inspection_go_to_module_button": "➡️ Passendes Modul öffnen",
    "field_inspection_header": "📍 Feldinspektion - Standortbestimmung",
    "field_inspection_loading": "Warte auf GPS-Position... erlauben Sie den Standortzugriff, falls Ihr Browser danach fragt.",
    "field_inspection_refresh_button": "🔄 Meinen Standort aktualisieren",
    "field_inspection_sites_note": "Die fünf angezeigten Standorte sind beispielhafte Referenzkoordinaten für diese MVP-Demonstration - sie stellen keine realen Anlagen dar.",
    "field_inspection_timeout": "Zeitüberschreitung bei der Standortabfrage. Versuchen Sie es erneut, am besten im Freien mit gutem GPS-Empfang.",
    "field_inspection_unavailable": "Position nicht verfügbar. Prüfen Sie, ob das GPS Ihres Geräts aktiviert ist, und versuchen Sie es erneut.",
    "field_inspection_your_position": "Ihre Position",
    "gas_exceeds_label": "Gas-Grenzwert überschritten",
    "generating_live_note": "Wird live erzeugt...",
    "hardware_capacity_label": "Verbleibende Tragfähigkeit der Ausrüstung (%)",
    "high_contrast_help": "Reinweißer Hintergrund, sehr große schwarze Schrift, fluoreszierende Warnungen - für optimale Lesbarkeit bei starker Blendung im Feld.",
    "high_contrast_toggle_label": "☀️ Hochkontrast- / Volle-Sonne-Modus",
    "highrise_caption": "Wind in Arbeitshöhe (Potenzgesetz-Profil oder gemessener Anemometerwert), geprüft gegen Kran- und Fassadengrenzen, Stockwerk für Stockwerk",
    "highrise_crane_load_label": "Masse der Kranlast (Tonnen)",
    "highrise_env_data_header": "3D-BIM- / Anemometer-Telemetrie (simuliert)",
    "highrise_floor_level_label": "Aktuelles Arbeitsstockwerk",
    "highrise_ground_wind_label": "Bodenwindgeschwindigkeit (Knoten)",
    "highrise_header": "🏙️ Hochhausbau - Vertikale urbane Umgebung",
    "highrise_realtime_header": "Echtzeitbewertung Kran & Hängezugang",
    "humidex_label": "Humidex",
    "iot_tunnel_toggle_label": "IoT-Sensor-Hub-Datenstrom aktivieren (LoRaWAN-Tunnel)",
    "ip_geo_fallback_button": "Netzwerkstandort verwenden (ungefähr)",
    "ip_geo_fallback_note": "GPS nicht verfügbar oder verweigert - ungefährer Standort über die IP-Adresse des Netzwerks ermittelt. Weniger genau als GPS, nur als Ausweichlösung verwendet.",
    "lightning_status_label": "Blitzstatus",
    "marineport_caption": "Gezeiten-Freiraum, Sichtbarkeitsfaktor bei Nacht und Korrosionsabbau der Ausrüstung in der Spritzwasserzone durch Salzsprühnebel",
    "marineport_clearance_label": "Erforderlicher Mindestfreiraum (m)",
    "marineport_env_data_header": "Umweltdaten",
    "marineport_exposure_class_label": "Korrosionsbelastungsklasse",
    "marineport_hardware_years_label": "Betriebsjahre der Ausrüstung",
    "marineport_header": "⚓ Hafen- & Wasserbau",
    "marineport_illuminance_label": "Gemessene Beleuchtungsstärke (lux)",
    "marineport_night_toggle": "Nachtbetrieb",
    "marineport_tide_label": "Aktueller Wasserstand (m)",
    "mining_caption": "Alveolengängiges kristallines Siliziumdioxid, Lärmdosis und Ganzkörpervibration für Abbaufront- und Fahrzeugpersonal",
    "mining_env_data_header": "Umweltdaten",
    "mining_header": "⛏️ Bergbau & Steinbrüche",
    "mining_noise_hours_label": "Dauer der Lärmexposition (Stunden)",
    "mining_noise_label": "Gemessener Lärmpegel (dBA)",
    "mining_silica_label": "Alveolengängiges kristallines Siliziumdioxid (µg/m³)",
    "mining_vibration_hours_label": "Dauer der Vibrationsexposition (Stunden)",
    "mining_vibration_label": "Gemessene Vibration a_w (m/s²)",
    "narrative_cached_note": "⚡ Zwischengespeichertes Ergebnis (< 30 min)",
    "noise_calc_caption": "Schätzt den Schallpegel in Ihrem Arbeitsabstand aus dem Referenzpegel der Maschine (Abstandsgesetz, -6 dB je Abstandsverdopplung) und berechnet dann die gesetzliche Tagesdosis nach den Regeln des gewählten Landes.",
    "noise_calc_header": "Akustischer Lärmrechner (Abstand → dB)",
    "noise_distance_label": "Arbeitsabstand (m)",
    "noise_dose_label": "Lärmdosis (%)",
    "noise_estimated_dba_label": "Geschätzter Pegel in diesem Abstand (dBA)",
    "noise_source_dba_label": "Quellpegel in 1 m (dBA)",
    "ocean_current_label": "Meeresströmungsgeschwindigkeit",
    "offshore_caption": "Maritime Humidex-Risikomatrix + Wind-/Wellen-Betriebsgrenzen für Schweiß-, Rohrleitungs- und Gerüstbauteams",
    "offshore_env_data_header": "GIS-Bojen-Telemetrie (simuliert)",
    "offshore_header": "🌊 Offshore Öl & Gas - Meeresumgebung",
    "offshore_realtime_header": "Echtzeitbewertung des Seebetriebs",
    "offshore_rh_label": "Relative Luftfeuchtigkeit (%)",
    "offshore_temp_label": "Umgebungstemperatur (°C)",
    "offshore_wind_label": "Windgeschwindigkeit (Knoten)",
    "org_context_label": "Organisation / Projekt / Standort",
    "org_context_org_label": "Organisation",
    "org_context_project_label": "Projekt",
    "org_context_site_label": "Standort",
    "oscillation_index_label": "Lastpendel-Index",
    "perceived_temp_label": "Gefühlte Temperatur (korrigiert)",
    "physio_add_worker_button": "+ Arbeitskraft hinzufügen (Check-in)",
    "physio_caption": "Nur anonyme Profilkennungen (z. B. Worker_A3) - DSGVO-konform. Es werden keine namentlichen personenbezogenen Daten erhoben oder gespeichert.",
    "physio_core_temp_label": "Geschätzte Körperkerntemperatur (Tci, °C)",
    "physio_dashboard_header": "Physiologische Belastung der Arbeitskräfte (anonym)",
    "physio_dehydration_label": "Dehydrierungs-Risikofaktor",
    "physio_hr_label": "Herzfrequenz (Schläge/min)",
    "physio_manual_checkin_header": "Manueller Sicherheits-Check-in",
    "physio_medical_disclaimer_caption": "Dies ist ein Screening-Werkzeug für die Arbeitssicherheit, kein Medizinprodukt und keine Diagnose - eine Arbeitskraft in echter Notlage muss unabhängig von diesem Wert sofort Erste Hilfe / notfallmedizinische Versorgung erhalten.",
    "physio_no_workers_note": "Noch keine Arbeitskräfte überwacht - fügen Sie oben einen Check-in hinzu, um die Erfassung zu starten (simulierter Wearable-Datenstrom oder manuelle Eingabe).",
    "physio_pct_hrmax_label": "% max. HF (Tanaka)",
    "physio_remove_worker_button": "Entfernen",
    "physio_status_critical": "KRITISCH",
    "physio_status_safe": "SICHER",
    "physio_status_warning": "WARNUNG",
    "physio_wearable_manual": "Manueller Check-in",
    "physio_wearable_mode_label": "Datenquelle",
    "physio_wearable_simulated": "Wearable-Datenstrom (simuliert)",
    "physio_worker_age_label": "Alter der Arbeitskraft",
    "risk_level_label": "Risikostufe",
    "scaled_wind_label": "Skalierter Wind in Höhe (Knoten)",
    "shift_rotation_label": "Team-Rotation",
    "silica_exceeds_label": "Siliziumdioxid-Grenzwert überschritten",
    "solar_caption": "Abschätzung der Strahlungswärmelast aus Bodenalbedo, GHI und UV für Montageteams von Trackern/Modulen",
    "solar_env_data_header": "Umweltdaten",
    "solar_ghi_label": "Globalstrahlung (GHI, W/m²)",
    "solar_header": "☀️ Solarparks im Großmaßstab - Wüstenumgebung",
    "solar_realtime_header": "Echtzeitbewertung der MEP-Teams",
    "solar_surface_label": "Oberflächentyp",
    "solar_temp_label": "Umgebungstemperatur (°C)",
    "solar_uv_label": "UV-Index",
    "surf_hybrid_assembly_zone": "Hybride Montagezone",
    "surf_pure_desert_sand": "Reiner Wüstensand",
    "surf_silicon_pv_panels": "Silizium-PV-Module",
    "telemetry_readout_label": "Live-Telemetrieanzeige",
    "thermal_differential_label": "Temperaturdifferenz Warm-/Kaltgang (°C)",
    "tide_margin_label": "Gezeiten-Freiraumreserve (m)",
    "tomorrow_briefing_button": "Vorab-Briefing für morgen erstellen",
    "tomorrow_briefing_caption": "Analysiert die Vorhersage für morgen und schlägt Anpassungen des Schichtplans vor (z. B. Aussetzen morgendlicher Kranhübe vor einer vorhergesagten Windspitze).",
    "tomorrow_briefing_header": "Vorab-Briefing für morgen (J+1)",
    "underground_ambient_temp_label": "Umgebungstemperatur (°C)",
    "underground_caption": "Tunnelwärme, CO und PM2.5, geprüft gegen Arbeitsplatzgrenzwerte, um Arbeitsstopps auszulösen",
    "underground_co_label": "Kohlenmonoxid CO (ppm)",
    "underground_env_data_header": "3D-Untergrund-GIS-Telemetrie (simuliert)",
    "underground_geo_humidity_label": "Eingeschlossene geothermische Feuchte (%)",
    "underground_header": "🚇 Metros & Tunnel - Unterirdische Infrastruktur",
    "underground_perceived_temp_label": "Gefühlte Temperatur (eingeschlossene Wärme)",
    "underground_pm25_label": "Feinstaub PM2.5 in der Luft (µg/m³)",
    "underground_realtime_header": "Echtzeitbewertung der MEP-Elektroteams",
    "vibration_a8_label": "Vibration A(8) (m/s²)",
    "wave_gate_label": "Wellen-Freigabe",
    "wave_height_label": "Wellenhöhe",
    "wind_gate_label": "Wind-Freigabe",
    "wind_status_label": "Windstatus",
    "wind_status_normal": "Normalbetrieb",
    "wind_status_restricted": "Eingeschränkt - genau beobachten",
    "wind_status_suspended": "Ausgesetzt - Kran-/Hebegefahr",
    "windenergy_caption": "Windgrenzwerte für Arbeiten in der Höhe, die 30-30-Blitzregel und Seegangsgrenzen für den Personentransfer per Crew-Transfer-Schiff (offshore)",
    "windenergy_env_data_header": "Umweltdaten",
    "windenergy_header": "💨 Windenergie - Onshore/Offshore",
    "windenergy_lightning_label": "Zeit zwischen Blitz und Donner (Sekunden)",
    "windenergy_lightning_toggle": "Gewittertätigkeit beobachtet",
    "windenergy_offshore_toggle": "Offshore-Standort (aktiviert Grenzwerte für Crew-Transfer-Schiffe)",
    "windenergy_wave_label": "Signifikante Wellenhöhe (m)",
    "windenergy_wind_label": "Windgeschwindigkeit in Nabenhöhe (m/s)",
    "page_dashboard": "Übersicht",
    "page_solar": "Solarparks",
    "page_offshore": "Offshore Öl & Gas",
    "page_underground": "Metros & Tunnel",
    "page_highrise": "Hochhäuser",
    "page_datacenter": "Rechenzentren",
    "page_windenergy": "Windenergie",
    "page_mining": "Bergbau & Steinbrüche",
    "page_marineport": "Hafen- & Wasserbau",
    "page_account": "Mein Konto",
    "page_admin_users": "Benutzer (Admin)",
}

ENGINE = {
    "Arc rating >= 25 cal/cm2 (PPE Category 3)":
        "Lichtbogenfestigkeit ≥ 25 cal/cm2 (PSA-Kategorie 3)",
    "Arc rating >= 4 cal/cm2 (PPE Category 1)":
        "Lichtbogenfestigkeit ≥ 4 cal/cm2 (PSA-Kategorie 1)",
    "Arc rating >= 40 cal/cm2 (PPE Category 4)":
        "Lichtbogenfestigkeit ≥ 40 cal/cm2 (PSA-Kategorie 4)",
    "Arc rating >= 8 cal/cm2 (PPE Category 2)":
        "Lichtbogenfestigkeit ≥ 8 cal/cm2 (PSA-Kategorie 2)",
    "Below 1.2 cal/cm2 - second-degree-burn threshold not reached":
        "Unter 1.2 cal/cm2 - Schwelle für Verbrennungen zweiten Grades nicht erreicht",
    "CRITICAL":
        "KRITISCH",
    "Dangerous - heat stroke possible":
        "Gefährlich - Hitzschlag möglich",
    "Extreme":
        "Extrem",
    "Extreme danger - exposed skin can freeze almost instantly":
        "Extreme Gefahr - ungeschützte Haut kann fast sofort erfrieren",
    "Great discomfort - avoid exertion":
        "Starkes Unbehagen - Anstrengung vermeiden",
    "HIGH":
        "HOCH",
    "Heat stroke imminent":
        "Hitzschlag unmittelbar bevorstehend",
    "High":
        "Hoch",
    "High risk - frostbite possible in 5-10 min":
        "Hohes Risiko - Erfrierungen in 5-10 min möglich",
    "LOW":
        "NIEDRIG",
    "Little to no discomfort":
        "Kaum oder kein Unbehagen",
    "Low":
        "Niedrig",
    "Low risk":
        "Geringes Risiko",
    "MODERATE":
        "MITTEL",
    "Moderate":
        "Mittel",
    "Moderate risk - frostbite possible in 10-30 min":
        "Mittleres Risiko - Erfrierungen in 10-30 min möglich",
    "SAFE":
        "SICHER",
    "Severe risk - frostbite possible in under 2 min":
        "Schweres Risiko - Erfrierungen in unter 2 min möglich",
    "Some discomfort":
        "Gewisses Unbehagen",
    "Very high risk - frostbite possible in 2-5 min":
        "Sehr hohes Risiko - Erfrierungen in 2-5 min möglich",
    "WARNING":
        "WARNUNG",
    "Acute heat stroke / UV-driven heat exhaustion - MEP tracker & module assembly crews":
        "Akuter Hitzschlag / UV-bedingte Hitzeerschöpfung - MEP-Montageteams für Tracker & Module",
    "Arc-flash incident energy + hot/cold-aisle thermal stress + confined-space clean-agent risk - MEP electrical/mechanical/fire-suppression commissioning crews":
        "Störlichtbogen-Einwirkenergie + Hitzestress Warm-/Kaltgang + Risiko enger Räume mit Inertgas-Löschmittel - Inbetriebnahmeteams Elektrik/Mechanik/Löschanlagen",
    "Excessive cardiovascular strain / heat-driven physiological overload":
        "Übermäßige Herz-Kreislauf-Belastung / hitzebedingte physiologische Überlastung",
    "Excessive occupational noise dose at estimated working distance":
        "Übermäßige berufliche Lärmdosis im geschätzten Arbeitsabstand",
    "Heat retention / thermal stress + wind-driven crane/lifting risk - welding, pipe-fitting, scaffolding crews":
        "Wärmestau / Hitzestress + windbedingtes Kran-/Hebe-Risiko - Schweiß-, Rohrleitungs- und Gerüstbauteams",
    "Heat strain from WBGT exposure, adjusted for clothing insulation, workload/metabolic rate, and acclimatization status, screened against ACGIH TLV action limits":
        "Hitzebelastung durch WBGT-Exposition, angepasst an Kleidungsisolation, Arbeitsschwere/Stoffwechselrate und Akklimatisierung, geprüft gegen ACGIH-TLV-Aktionsgrenzen",
    "Heat stress + air-quality (CO/PM2.5) exposure - MEP electrical crews pulling high-voltage cabling pre-ventilation commissioning":
        "Hitzestress + Luftqualitätsbelastung (CO/PM2.5) - MEP-Elektroteams beim Ziehen von Hochspannungskabeln vor Inbetriebnahme der Lüftung",
    "Respirable crystalline silica exposure, noise-induced hearing loss risk, and whole-body-vibration injury risk - quarry-face and mobile-plant crews":
        "Exposition gegenüber alveolengängigem kristallinem Siliziumdioxid, Risiko lärmbedingter Schwerhörigkeit und Verletzungsrisiko durch Ganzkörpervibration - Abbaufront- und Fahrzeugteams",
    "Tide-clearance access risk, reduced night-time visibility, and corrosion-degraded splash-zone lifting/scaffold hardware capacity":
        "Zugangsrisiko durch Gezeiten-Freiraum, eingeschränkte Sicht bei Nacht und korrosionsbedingt verminderte Tragfähigkeit von Hebe-/Gerüstausrüstung in der Spritzwasserzone",
    "Wind-driven fall-from-height risk during blade/nacelle access, lightning strike exposure, and (offshore) crew-transfer-vessel sea-state risk":
        "Windbedingtes Absturzrisiko beim Zugang zu Rotorblatt/Gondel, Blitzschlaggefahr und (offshore) Seegangsrisiko für Crew-Transfer-Schiffe",
    "Wind-shear-driven crane load-swing and fall-from-height risk - MEP riser & external-wall crews":
        "Durch Windscherung verursachtes Pendeln der Kranlast und Absturzrisiko - MEP-Teams für Steigleitungen & Außenwände",
    "30-30 rule triggered: evacuate exposed work-at-height positions immediately; do not resume outdoor work until 30 minutes after the last observed strike":
        "30-30-Regel ausgelöst: exponierte Höhenarbeitsplätze sofort räumen; Außenarbeiten erst 30 Minuten nach dem letzten beobachteten Blitz wieder aufnehmen",
    "Adjust welding/pipe-fitting shift rotations per Humidex band; shorten exposure intervals":
        "Schweiß-/Rohrleitungsschichten nach Humidex-Stufe anpassen; Expositionsintervalle verkürzen",
    "Arc-flash incident energy is UNKNOWN: no energized work until the equipment's arc-flash label or a current arc-flash study (IEEE 1584) confirms incident energy and the required arc rating; otherwise establish an electrically safe work condition (lock-out/tag-out, test before touch)":
        "Die Störlichtbogen-Einwirkenergie ist UNBEKANNT: keine Arbeiten unter Spannung, bis das Lichtbogen-Etikett der Anlage oder eine aktuelle Störlichtbogenstudie (IEEE 1584) die Einwirkenergie und die erforderliche Lichtbogenfestigkeit bestätigt; andernfalls einen spannungsfreien Zustand herstellen (Freischalten/Kennzeichnen, Spannungsfreiheit prüfen)",
    "Buddy system + heat-illness spotters; mandatory electrolyte replacement schedule":
        "Buddy-System + Beobachter für Hitzeerkrankungen; verpflichtender Plan zum Elektrolytausgleich",
    "CO OEL exceeded - evacuate face area, verify forced ventilation, re-test before re-entry":
        "CO-Grenzwert überschritten - Ortsbrust räumen, Zwangslüftung prüfen, vor dem Wiederbetreten neu messen",
    "Confined ceiling-void space + armed clean-agent suppression: disarm/isolate the system and atmosphere-test (O2/asphyxiant risk) before entry":
        "Enge Zwischendecke + scharf geschaltete Inertgas-Löschanlage: Anlage deaktivieren/trennen und Atmosphäre messen (O2-/Erstickungsgefahr) vor dem Betreten",
    "DANGER: arc-flash incident energy exceeds 40 cal/cm2 - de-energize equipment before any work; no PPE category permits live work":
        "GEFAHR: Störlichtbogen-Einwirkenergie über 40 cal/cm2 - Anlage vor jeder Arbeit spannungsfrei schalten; keine PSA-Kategorie erlaubt Arbeiten unter Spannung",
    "Delay non-critical curtain-wall/riser lifts to the next confirmed calm window":
        "Nicht kritische Hübe für Vorhangfassaden/Steigleitungen auf das nächste bestätigte ruhige Zeitfenster verschieben",
    "Enforce ACGIH work/rest cycle per calculated action level; increase rest ratio if margin exceeded":
        "ACGIH-Arbeits-/Pausenzyklus gemäß berechneter Aktionsstufe durchsetzen; Pausenanteil erhöhen, wenn die Reserve überschritten wird",
    "Escalate to HSE manager: consider suspending non-critical outdoor MEP tasks during peak GHI hours":
        "An den HSE-Manager eskalieren: Aussetzen nicht kritischer MEP-Außenarbeiten zu den Stunden mit maximaler GHI erwägen",
    "Hot/cold-aisle thermal differential elevated - rotate commissioning crews more frequently, hydrate, reduce continuous hot-aisle dwell time":
        "Erhöhte Temperaturdifferenz Warm-/Kaltgang - Inbetriebnahmeteams häufiger rotieren, trinken, Aufenthaltsdauer im Warmgang verkürzen",
    "Increase hydration monitoring; enclosed-space heat retention areas need forced ventilation checks":
        "Trinküberwachung verstärken; geschlossene Bereiche mit Wärmestau benötigen Kontrollen der Zwangslüftung",
    "Limit CTV transfers to essential personnel only; brief crew on sea-state trend":
        "CTV-Transfers auf unverzichtbares Personal beschränken; Besatzung über die Seegangsentwicklung informieren",
    "Maintain standard at-height wind-monitoring protocol; recheck anemometer feed each shift":
        "Standardprotokoll zur Windüberwachung in der Höhe beibehalten; Anemometerdaten jede Schicht prüfen",
    "Maintain standard data-center commissioning HSE protocol; continue thermal, arc-flash, and confined-space monitoring cadence":
        "Standard-HSE-Protokoll für die Inbetriebnahme von Rechenzentren beibehalten; Überwachung von Wärme, Störlichtbogen und engen Räumen fortsetzen",
    "Maintain standard heat-safety protocol; monitor GHI/temp trend for escalation":
        "Standardprotokoll für Hitzeschutz beibehalten; GHI-/Temperaturentwicklung auf Eskalation überwachen",
    "Maintain standard heat-stress protocol; recheck WBGT/clothing/workload if conditions change":
        "Standardprotokoll gegen Hitzestress beibehalten; WBGT/Kleidung/Arbeitsschwere bei geänderten Bedingungen erneut prüfen",
    "Maintain standard marine HSE protocol; monitor wind/humidex trend":
        "Standard-HSE-Protokoll auf See beibehalten; Wind-/Humidex-Entwicklung überwachen",
    "Maintain standard marine/port HSE protocol; continue tide, lighting, and hardware-condition monitoring":
        "Standard-HSE-Protokoll für Hafen-/Wasserbau beibehalten; Überwachung von Gezeiten, Beleuchtung und Ausrüstungszustand fortsetzen",
    "Maintain standard mining/quarrying HSE protocol; continue silica, noise, and vibration monitoring cadence":
        "Standard-HSE-Protokoll für Bergbau/Steinbrüche beibehalten; Überwachung von Siliziumdioxid, Lärm und Vibration fortsetzen",
    "Maintain standard underground HSE protocol; continue OEL and heat monitoring cadence":
        "Standard-HSE-Protokoll unter Tage beibehalten; Überwachung von Grenzwerten und Wärme fortsetzen",
    "Maintain standard wind-energy HSE protocol; continue hub-height wind, lightning, and sea-state monitoring":
        "Standard-HSE-Protokoll für Windenergie beibehalten; Überwachung von Wind in Nabenhöhe, Blitzen und Seegang fortsetzen",
    "Mandatory shaded rest areas / cooling stations within 100m of active work fronts":
        "Verpflichtende schattige Ruhebereiche / Kühlstationen innerhalb von 100m zu aktiven Arbeitsbereichen",
    "Notify tower crane operator and site HSE manager of current floor-level scaled wind readings":
        "Turmkranführer und HSE-Manager über die skalierten Windwerte auf der aktuellen Etage informieren",
    "PM2.5 OEL exceeded - mandatory respiratory PPE upgrade, water suppression, re-test":
        "PM2.5-Grenzwert überschritten - verpflichtende Aufrüstung des Atemschutzes, Wasserbedüsung, erneute Messung",
    "Prioritize temporary ventilation deployment ahead of permanent system commissioning":
        "Bereitstellung temporärer Lüftung vor der Inbetriebnahme der Dauerlüftung priorisieren",
    "Recheck tie-off points and suspended-access rigging before resuming work at height":
        "Anschlagpunkte und Takelage des Hängezugangs vor Wiederaufnahme der Höhenarbeit erneut prüfen",
    "Reduce work/rest ratio for MEP electrical crews; rotate more frequently as heat trend rises":
        "Arbeitsanteil der MEP-Elektroteams verringern; bei steigender Hitze häufiger rotieren",
    "Reflective/ventilated PPE for crews working adjacent to panel rows (elevated radiant load)":
        "Reflektierende/belüftete PSA für Teams neben den Modulreihen (erhöhte Strahlungslast)",
    "Respirable crystalline silica exceeds the OEL - mandatory water suppression/wet-cutting, upgrade respiratory PPE, rotate crews away from the quarry face":
        "Alveolengängiges kristallines Siliziumdioxid über dem Grenzwert - verpflichtende Wasserbedüsung/Nassschneiden, Atemschutz aufrüsten, Teams von der Abbaufront wegrotieren",
    "Restrict blade/nacelle access to essential tasks only; recheck anemometer trend before each climb":
        "Zugang zu Rotorblatt/Gondel auf unverzichtbare Aufgaben beschränken; Anemometertrend vor jedem Aufstieg prüfen",
    "SAFETY OVERRIDE: halt all blade/nacelle access and crane operations until wind, lightning, or sea-state conditions clear":
        "SICHERHEITSSTOPP: jeden Zugang zu Rotorblatt/Gondel und alle Kranarbeiten einstellen, bis Wind, Blitze oder Seegang wieder unbedenklich sind",
    "SAFETY OVERRIDE: halt exposure until silica, noise, or vibration levels are brought under control":
        "SICHERHEITSSTOPP: Exposition einstellen, bis Siliziumdioxid-, Lärm- oder Vibrationswerte unter Kontrolle sind",
    "SAFETY OVERRIDE: halt marine/port access work until tide clearance or hardware capacity conditions are rechecked":
        "SICHERHEITSSTOPP: Zugangsarbeiten im Hafen-/Wasserbau einstellen, bis Gezeiten-Freiraum oder Ausrüstungstragfähigkeit erneut geprüft sind",
    "SAFETY OVERRIDE: halt non-essential commissioning work in this zone until conditions are rechecked":
        "SICHERHEITSSTOPP: nicht unverzichtbare Inbetriebnahmearbeiten in dieser Zone einstellen, bis die Bedingungen erneut geprüft sind",
    "SAFETY OVERRIDE: halt non-essential high-voltage MEP cabling work until conditions recheck":
        "SICHERHEITSSTOPP: nicht unverzichtbare MEP-Hochspannungsverkabelung einstellen, bis die Bedingungen erneut geprüft sind",
    "SAFETY OVERRIDE: suspend all crane lifts and external-wall/curtain-wall installation until scaled wind drops below the 30-knot threshold":
        "SICHERHEITSSTOPP: alle Kranhübe und Fassaden-/Vorhangfassadenmontagen aussetzen, bis der skalierte Wind unter die 30-Knoten-Schwelle fällt",
    "SAFETY OVERRIDE: suspend crane/lifting and welding ops until conditions recheck":
        "SICHERHEITSSTOPP: Kran-/Hebe- und Schweißarbeiten aussetzen, bis die Bedingungen erneut geprüft sind",
    "SAFETY OVERRIDE: vapor-barrier/limited-use PPE requires direct physiological monitoring (e.g. core temperature, heart-rate recovery) - a WBGT table lookup alone is not sufficient authorization to continue work in this ensemble":
        "SICHERHEITSSTOPP: dampfdichte PSA / PSA mit begrenzter Nutzung erfordert direkte physiologische Überwachung (z. B. Körperkerntemperatur, Herzfrequenzerholung) - ein Blick in die WBGT-Tabelle allein genügt nicht, um die Arbeit in dieser Ausrüstung fortzusetzen",
    "STOP WORK: no ACGIH-compliant work/rest ratio exists at this workload/clothing/acclimatization combination, even at 25/75 - reduce workload category, change clothing, or wait for cooler conditions before resuming":
        "ARBEIT STOPPEN: für diese Kombination aus Arbeitsschwere/Kleidung/Akklimatisierung gibt es kein ACGIH-konformes Arbeits-/Pausenverhältnis, auch nicht bei 25/75 - Arbeitsschwere senken, Kleidung wechseln oder kühlere Bedingungen abwarten",
    "Shift high-exertion tracker/module installation to early morning or late afternoon windows":
        "Anstrengende Tracker-/Modulmontage in den frühen Morgen oder späten Nachmittag verlegen",
    "Suspend all crew-transfer-vessel personnel transfers until significant wave height drops below the transfer limit":
        "Alle Personentransfers per Crew-Transfer-Schiff aussetzen, bis die signifikante Wellenhöhe unter das Transferlimit fällt",
    "Task-area illuminance below the OSHA 1926.56 minimum for night operations - deploy additional lighting before resuming work":
        "Beleuchtungsstärke im Arbeitsbereich unter dem OSHA-1926.56-Minimum für Nachtarbeit - vor Wiederaufnahme zusätzliche Beleuchtung aufstellen",
    "Tide clearance margin critical - halt underside/pile-driving access work until tide recedes to a safe margin":
        "Gezeiten-Freiraumreserve kritisch - Zugangsarbeiten von unten/Pfahlrammen einstellen, bis die Flut auf eine sichere Reserve zurückgeht",
    "Tide clearance margin restricted - limit access to essential monitored tasks, recheck tide tables before each shift":
        "Gezeiten-Freiraumreserve eingeschränkt - Zugang auf überwachte unverzichtbare Aufgaben beschränken, Gezeitentabellen vor jeder Schicht prüfen",
    "Whole-body vibration A(8) exceeds the EU exposure limit value - remove operator from the machine immediately, inspect seat/suspension, reduce daily operating hours":
        "Ganzkörpervibration A(8) über dem EU-Expositionsgrenzwert - Bediener sofort von der Maschine abziehen, Sitz/Federung prüfen, tägliche Betriebsstunden verringern",
    "Whole-body vibration A(8) exceeds the action value - schedule maintenance on seat/suspension, monitor exposure hours":
        "Ganzkörpervibration A(8) über dem Auslösewert - Wartung von Sitz/Federung einplanen, Expositionsstunden überwachen",
    "Worker is not marked as heat-acclimatized - apply a graduated acclimatization schedule (ACGIH recommends progressive exposure over ~1-2 weeks) before assigning full workload":
        "Arbeitskraft ist nicht als hitzeakklimatisiert erfasst - einen stufenweisen Akklimatisierungsplan anwenden (ACGIH empfiehlt schrittweise Exposition über ~1-2 Wochen), bevor die volle Arbeitslast zugewiesen wird",
    "% of max HR":
        "% der max. HF",
    "Acclimatized":
        "Akklimatisiert",
    "Albedo factor applied":
        "Angewandter Albedo-Faktor",
    "Ambient temperature (C)":
        "Umgebungstemperatur (C)",
    "Ambient temperature (deg C)":
        "Umgebungstemperatur (°C)",
    "Arc-flash incident energy source":
        "Quelle der Störlichtbogen-Einwirkenergie",
    "Bolted fault current (kA)":
        "Satter Kurzschlussstrom (kA)",
    "CO (ppm)":
        "CO (ppm)",
    "Clothing Adjustment Factor (C)":
        "Kleidungs-Korrekturfaktor (C)",
    "Clothing type":
        "Kleidungstyp",
    "Cold-aisle setpoint (C)":
        "Sollwert Kaltgang (C)",
    "Confined ceiling-void space":
        "Enge Zwischendecke",
    "Crane load mass (tons)":
        "Masse der Kranlast (Tonnen)",
    "Current tide level (m)":
        "Aktueller Wasserstand (m)",
    "Dehydration risk multiplier":
        "Dehydrierungs-Risikofaktor",
    "Effective WBGT (C)":
        "Effektiver WBGT (C)",
    "Electrical load (kW) - context only, not used in arc-flash maths":
        "Elektrische Last (kW) - nur Kontext, nicht in der Lichtbogenberechnung verwendet",
    "Estimated core temp proxy (Tci, deg C)":
        "Geschätzte Körperkerntemperatur (Tci, °C)",
    "Estimated level at working distance (dBA)":
        "Geschätzter Pegel im Arbeitsabstand (dBA)",
    "Exchange rate (dB)":
        "Halbierungsparameter (dB)",
    "Exposure duration (hours)":
        "Expositionsdauer (Stunden)",
    "Floor level":
        "Stockwerk",
    "GHI (W/m2)":
        "GHI (W/m2)",
    "Gaseous suppression system armed":
        "Gaslöschanlage scharf geschaltet",
    "Geothermal humidity (%)":
        "Geothermische Feuchte (%)",
    "Ground wind speed (knots)":
        "Bodenwindgeschwindigkeit (Knoten)",
    "Hardware exposure class":
        "Belastungsklasse der Ausrüstung",
    "Hardware remaining capacity (%)":
        "Verbleibende Tragfähigkeit der Ausrüstung (%)",
    "Hardware years in service":
        "Betriebsjahre der Ausrüstung",
    "Heart rate (bpm)":
        "Herzfrequenz (Schläge/min)",
    "Hot-aisle temperature (C)":
        "Warmgang-Temperatur (C)",
    "Hub-height wind speed (m/s)":
        "Windgeschwindigkeit in Nabenhöhe (m/s)",
    "Label incident energy (cal/cm2)":
        "Einwirkenergie laut Etikett (cal/cm2)",
    "Legal daily noise dose (%)":
        "Gesetzliche tägliche Lärmdosis (%)",
    "Lightning flash-to-bang (s)":
        "Zeit zwischen Blitz und Donner (s)",
    "Measured illuminance (lux)":
        "Gemessene Beleuchtungsstärke (lux)",
    "Measured working-height wind (knots)":
        "Gemessener Wind in Arbeitshöhe (Knoten)",
    "Metabolic rate range (W/m2)":
        "Bereich der Stoffwechselrate (W/m2)",
    "Night operation":
        "Nachtbetrieb",
    "Noise criterion (dBA)":
        "Lärmkriterium (dBA)",
    "Noise dose (%)":
        "Lärmdosis (%)",
    "Noise exposure (hours)":
        "Lärmexposition (Stunden)",
    "Noise level (dBA)":
        "Lärmpegel (dBA)",
    "Offshore":
        "Offshore",
    "PM2.5 (ug/m3)":
        "PM2.5 (µg/m3)",
    "Protective-device clearing time (s)":
        "Abschaltzeit der Schutzeinrichtung (s)",
    "Raw WBGT (C)":
        "Roher WBGT (C)",
    "Recommended ratio ACGIH limit (C)":
        "ACGIH-Grenze des empfohlenen Verhältnisses (C)",
    "Recommended work/rest ratio":
        "Empfohlenes Arbeits-/Pausenverhältnis",
    "Reference distance (m)":
        "Referenzabstand (m)",
    "Relative humidity (%)":
        "Relative Luftfeuchtigkeit (%)",
    "Requested ratio ACGIH limit (C)":
        "ACGIH-Grenze des angefragten Verhältnisses (C)",
    "Requested ratio exceeded":
        "Angefragtes Verhältnis überschritten",
    "Requested work/rest ratio":
        "Angefragtes Arbeits-/Pausenverhältnis",
    "Required min. clearance (m)":
        "Erforderlicher Mindestfreiraum (m)",
    "Requires physiological monitoring (vapor-barrier PPE)":
        "Physiologische Überwachung erforderlich (dampfdichte PSA)",
    "Respirable silica (ug/m3)":
        "Alveolengängiges Siliziumdioxid (µg/m3)",
    "Significant wave height (m)":
        "Signifikante Wellenhöhe (m)",
    "Source level at reference distance (dBA)":
        "Quellpegel im Referenzabstand (dBA)",
    "Surface type":
        "Oberflächentyp",
    "System voltage (kV)":
        "Systemspannung (kV)",
    "Tanaka max HR (bpm)":
        "Max. HF nach Tanaka (Schläge/min)",
    "Terrain exponent (alpha)":
        "Geländeexponent (alpha)",
    "Tide clearance margin (m)":
        "Gezeiten-Freiraumreserve (m)",
    "UV index":
        "UV-Index",
    "Vibration A(8) (m/s2)":
        "Vibration A(8) (m/s2)",
    "Vibration a_w (m/s2)":
        "Vibration a_w (m/s2)",
    "Vibration exposure (hours)":
        "Vibrationsexposition (Stunden)",
    "WBGT data source":
        "WBGT-Datenquelle",
    "Wind speed (knots)":
        "Windgeschwindigkeit (Knoten)",
    "Working distance (m)":
        "Arbeitsabstand (m)",
    "Working distance (mm)":
        "Arbeitsabstand (mm)",
    "Working height (m)":
        "Arbeitshöhe (m)",
    "Workload intensity":
        "Arbeitsintensität",
    "Workload/metabolic category":
        "Kategorie Arbeitsschwere/Stoffwechsel",
    "Normal Operations":
        "Normalbetrieb",
    "Restricted - Monitor Closely":
        "Eingeschränkt - genau beobachten",
    "Suspended - Crane/Lifting Danger":
        "Ausgesetzt - Kran-/Hebegefahr",
    "NONE - STOP WORK (no compliant ratio)":
        "KEINES - ARBEIT STOPPEN (kein konformes Verhältnis)",
    "pure_desert_sand":
        "Reiner Wüstensand",
    "silicon_pv_panels":
        "Silizium-PV-Module",
    "hybrid_assembly_zone":
        "Hybride Montagezone",
}

ENGINE_TEMPLATES = {
    "wind_status": "Windrisikostatus: {0}",
    "noise_dose": "Lärmdosis bei {0}% des zulässigen 8-Stunden-Grenzwerts - Gehörschutz verpflichtend, Dauer der Dauerexposition verringern, Lärmquellen wo möglich abschirmen/kapseln",
    "splash_zone": "Ausrüstung in der Spritzwasserzone auf {0}% der Nenntragfähigkeit geschätzt - vor weiterer Nutzung eine zertifizierte Strukturprüfung einplanen; Herabsetzung der zulässigen Arbeitslast erwägen",
    "arc_flash_ppe": "Störlichtbogen-PSA für Arbeiten unter Spannung: {0} (Quelle: {1})",
    "work_rest": "Einen {0}-Arbeits-/Pausenzyklus einhalten, um innerhalb der ACGIH-TLV-Aktionsgrenze für diese Arbeitsschwere und Kleidung zu bleiben",
}
