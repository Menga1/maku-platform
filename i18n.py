"""
MAKU i18n
=========
Minimal translation layer for the Streamlit UI. Per project guidelines,
the UI defaults to French, with English, Arabic, and Spanish offered as
alternates. This file holds ONLY display strings - all code, variables,
and internal logic stay in English, and no risk math lives here (see
risk_engine.py).

Arabic (ar) note: Streamlit has no built-in right-to-left layout support,
so apply_rtl_style() injects a small best-effort CSS block that right-
aligns text and reverses flex-based layouts (columns, sidebar) when
Arabic is selected. This is a practical approximation, not a certified
RTL implementation - complex nested layouts (e.g. metric cards inside
columns inside expanders) may still read subtly better in en/fr/es than
ar in a few spots. Numbers, units, and technical acronyms (GHI, WBGT,
ACGIH, PM2.5, CO, kW, cal/cm²...) are intentionally kept in Latin script
within the Arabic strings below, matching standard practice in Arabic
technical/engineering documentation. The same acronym-preservation
convention is used in the Spanish strings.

Usage:
    from i18n import t, LANGUAGES, apply_rtl_style
    lang = st.session_state.get("lang", "fr")
    st.header(t("solar_header", lang))
"""

LANGUAGES = {"Français": "fr", "English": "en", "العربية": "ar", "Español": "es"}
DEFAULT_LANG = "fr"
RTL_LANGS = {"ar"}

STRINGS = {
    # --- Global / sidebar ---
    "app_title": {"fr": "🏗️ MAKU", "en": "🏗️ MAKU", "ar": "🏗️ MAKU", "es": "🏗️ MAKU"},
    "app_tagline": {
        "fr": "IA Multi-Environnement pour l'Évaluation des Risques Cinétiques - "
              "Mega-Souterrain, Offshore, Solaire, Tours & Data Centers",
        "en": "Multi-Environment AI for Kinetic Risk Assessment - Mega-Underground, "
              "Offshore, Solar, High-Rise & Data Center construction",
        "ar": "منصة ذكاء اصطناعي متعددة البيئات لتقييم المخاطر الحركية - الأنفاق "
              "الكبرى، المنشآت البحرية، الطاقة الشمسية، الأبراج ومراكز البيانات",
        "es": "IA Multi-Entorno para la Evaluación de Riesgos Cinéticos - "
              "Mega-Subterráneo, Offshore, Solar, Torres y Centros de Datos",
    },
    "lang_label": {"fr": "Langue", "en": "Language", "ar": "اللغة", "es": "Idioma"},
    "ai_layer_header": {
        "fr": "Couche narrative IA (optionnelle)",
        "en": "AI Narrative Layer (optional)",
        "ar": "طبقة السرد بالذكاء الاصطناعي (اختيارية)",
        "es": "Capa narrativa de IA (opcional)",
    },
    "api_key_label": {
        "fr": "Clé API Anthropic",
        "en": "Anthropic API key",
        "ar": "مفتاح API الخاص بـ Anthropic",
        "es": "Clave API de Anthropic",
    },
    "api_key_help": {
        "fr": "Optionnel. Sans clé, MAKU fonctionne toujours grâce à ses formules de "
              "risque et ses recommandations de contrôle - la clé API ajoute uniquement "
              "une synthèse en langage naturel.",
        "en": "Optional. Without a key, MAKU still runs on its rule-based risk formulas "
              "and control recommendations - the API key only adds a plain-language "
              "narrative summary on top.",
        "ar": "اختياري. بدون مفتاح، يستمر تطبيق MAKU في العمل بالكامل عبر معادلات "
              "المخاطر القائمة على القواعد وتوصيات إجراءات التحكم - مفتاح API يضيف "
              "فقط ملخصاً سردياً بلغة طبيعية.",
        "es": "Opcional. Sin clave, MAKU sigue funcionando gracias a sus fórmulas de "
              "riesgo basadas en reglas y sus recomendaciones de control - la clave "
              "API solo añade un resumen narrativo en lenguaje natural.",
    },
    "work_rate_label": {"fr": "Cadence de travail", "en": "Work rate", "ar": "معدل العمل", "es": "Ritmo de trabajo"},
    "wr_light": {"fr": "légère", "en": "light", "ar": "خفيف", "es": "ligero"},
    "wr_moderate": {"fr": "modérée", "en": "moderate", "ar": "متوسط", "es": "moderado"},
    "wr_heavy": {"fr": "intense", "en": "heavy", "ar": "شاق", "es": "intenso"},
    "work_rest_label": {
        "fr": "Cycle travail/repos",
        "en": "Work/rest cycle",
        "ar": "دورة العمل/الراحة",
        "es": "Ciclo de trabajo/descanso",
    },
    "work_rest_help": {
        "fr": "Catégories ACGIH TLV travail/repos utilisées pour les limites d'action "
              "liées au stress thermique",
        "en": "ACGIH TLV work/rest categories used for heat-stress action limits",
        "ar": "فئات العمل/الراحة وفق معايير ACGIH TLV المستخدمة في تحديد حدود "
              "الإجراء الخاصة بالإجهاد الحراري",
        "es": "Categorías de trabajo/descanso ACGIH TLV utilizadas para los límites "
              "de acción por estrés térmico",
    },

    # --- Common result sections ---
    "risk_band_label": {"fr": "Niveau de risque", "en": "Risk Band", "ar": "مستوى الخطورة", "es": "Nivel de riesgo"},
    "primary_hazard_label": {
        "fr": "Danger principal",
        "en": "Primary hazard",
        "ar": "الخطر الرئيسي",
        "es": "Peligro principal",
    },
    "drivers_label": {
        "fr": "Facteurs environnementaux",
        "en": "Environmental drivers",
        "ar": "العوامل البيئية المؤثرة",
        "es": "Factores ambientales",
    },
    "controls_label": {
        "fr": "Mesures de contrôle recommandées",
        "en": "Recommended Controls",
        "ar": "إجراءات التحكم الموصى بها",
        "es": "Medidas de control recomendadas",
    },
    "briefing_label": {
        "fr": "Synthèse IA",
        "en": "AI Briefing",
        "ar": "الموجز الصادر عن الذكاء الاصطناعي",
        "es": "Resumen de IA",
    },
    "yes": {"fr": "Oui", "en": "Yes", "ar": "نعم", "es": "Sí"},
    "no": {"fr": "Non", "en": "No", "ar": "لا", "es": "No"},
    "acgih_exceeded_label": {
        "fr": "Limite ACGIH dépassée",
        "en": "ACGIH limit exceeded",
        "ar": "تجاوز حد ACGIH",
        "es": "Límite ACGIH superado",
    },
    "vs_limit": {"fr": "vs limite", "en": "vs limit", "ar": "مقابل الحد", "es": "vs límite"},
    "safety_override": {
        "fr": "⚠️ DÉPASSEMENT DE SÉCURITÉ DÉCLENCHÉ",
        "en": "⚠️ SAFETY OVERRIDE TRIGGERED",
        "ar": "⚠️ تم تفعيل تجاوز السلامة الحرج",
        "es": "⚠️ ANULACIÓN DE SEGURIDAD ACTIVADA",
    },
    "run_button": {
        "fr": "Lancer l'évaluation",
        "en": "Run Risk Assessment",
        "ar": "تشغيل تقييم المخاطر",
        "es": "Ejecutar evaluación de riesgo",
    },

    # --- Data Feed Mode (Manuel/Simulation <-> Automatique/Temps Reel) ---
    "data_mode_header": {
        "fr": "Mode d'Alimentation des Données",
        "en": "Data Feed Mode",
        "ar": "وضع تغذية البيانات",
        "es": "Modo de Alimentación de Datos",
    },
    "data_mode_prompt": {
        "fr": "Source des données environnementales",
        "en": "Environmental data source",
        "ar": "مصدر البيانات البيئية",
        "es": "Fuente de datos ambientales",
    },
    "data_mode_manual": {
        "fr": "Manuel / Simulation",
        "en": "Manual / Simulation",
        "ar": "يدوي / محاكاة",
        "es": "Manual / Simulación",
    },
    "data_mode_auto": {
        "fr": "Automatique / Temps Réel",
        "en": "Automatic / Real-Time",
        "ar": "تلقائي / آني",
        "es": "Automático / Tiempo Real",
    },
    "feed_live_badge": {"fr": "Données en direct", "en": "Live data", "ar": "بيانات مباشرة", "es": "Datos en vivo"},
    "feed_last_update": {
        "fr": "Dernière mise à jour",
        "en": "Last update",
        "ar": "آخر تحديث",
        "es": "Última actualización",
    },
    "feed_error_banner": {
        "fr": "Flux de données indisponible - retour automatique en mode manuel/simulation.",
        "en": "Data feed unavailable - safely reverted to manual/simulation mode.",
        "ar": "تعذر الوصول إلى مصدر البيانات - تم الرجوع تلقائياً وبأمان إلى الوضع اليدوي/المحاكاة.",
        "es": "Fuente de datos no disponible - se revirtió de forma segura al modo "
              "manual/simulación.",
    },
    "feed_not_armed_note": {
        "fr": "Mode automatique sélectionné. Activez le capteur ci-dessus pour démarrer le flux "
              "en direct, ou continuez avec les curseurs manuels ci-dessous.",
        "en": "Automatic mode selected. Enable the sensor toggle above to start the live "
              "stream, or continue with the manual sliders below.",
        "ar": "تم اختيار الوضع التلقائي. فعّل مفتاح الاستشعار أعلاه لبدء البث المباشر، "
              "أو تابع باستخدام أشرطة التمرير اليدوية أدناه.",
        "es": "Modo automático seleccionado. Active el interruptor del sensor arriba "
              "para iniciar la transmisión en vivo, o continúe con los controles "
              "manuales de abajo.",
    },
    "telemetry_readout_label": {
        "fr": "Lecture télémétrie en direct",
        "en": "Live telemetry readout",
        "ar": "قراءة القياس عن بُعد المباشرة",
        "es": "Lectura de telemetría en vivo",
    },
    "context_only_note": {
        "fr": "Indicateur contextuel (non utilisé par le moteur de risque actuel).",
        "en": "Contextual indicator (not consumed by the current risk engine).",
        "ar": "مؤشر سياقي فقط (لا يُستخدم حالياً في محرك حساب المخاطر).",
        "es": "Indicador contextual (no utilizado por el motor de riesgo actual).",
    },
    "wave_height_label": {
        "fr": "Hauteur des vagues",
        "en": "Wave height",
        "ar": "ارتفاع الأمواج",
        "es": "Altura de las olas",
    },
    "ocean_current_label": {
        "fr": "Vitesse du courant marin",
        "en": "Ocean current velocity",
        "ar": "سرعة التيار البحري",
        "es": "Velocidad de la corriente marina",
    },
    "iot_tunnel_toggle_label": {
        "fr": "Activer le flux de la centrale de capteurs IoT (LoRaWAN Tunnel)",
        "en": "Enable IoT sensor-hub stream (LoRaWAN Tunnel)",
        "ar": "تفعيل بث مركز مستشعرات إنترنت الأشياء (نفق LoRaWAN)",
        "es": "Activar la transmisión del centro de sensores IoT (Túnel LoRaWAN)",
    },
    "crane_telemetry_toggle_label": {
        "fr": "Activer la télémétrie de l'Anémomètre Grue & Capteurs d'Oscillation",
        "en": "Enable Crane Anemometer & Oscillation Sensor telemetry",
        "ar": "تفعيل قياس بُعد جهاز قياس الرياح للرافعة ومستشعرات التذبذب",
        "es": "Activar la telemetría del anemómetro de grúa y sensores de oscilación",
    },
    "dc_telemetry_toggle_label": {
        "fr": "Activer le flux des Transformateurs de Courant & Sondes Thermiques",
        "en": "Enable Current Transformer & Thermal Probe stream",
        "ar": "تفعيل بث محولات التيار ومجسات الحرارة",
        "es": "Activar la transmisión de transformadores de corriente y sondas térmicas",
    },

    # --- Explicit cross-page navigation (page_link), independent of the ---
    # --- native/auto sidebar multipage nav, for reliability on mobile/embedded browsers
    "nav_header": {
        "fr": "Navigation des modules",
        "en": "Module navigation",
        "ar": "التنقل بين الوحدات",
        "es": "Navegación de módulos",
    },
    "nav_dashboard": {"fr": "🛡️ Tableau de bord", "en": "🛡️ Dashboard", "ar": "🛡️ لوحة التحكم", "es": "🛡️ Panel principal"},
    "nav_solar": {
        "fr": "☀️ Fermes solaires",
        "en": "☀️ Solar Farms",
        "ar": "☀️ مزارع الطاقة الشمسية",
        "es": "☀️ Granjas Solares",
    },
    "nav_offshore": {
        "fr": "🌊 Offshore Pétrole & Gaz",
        "en": "🌊 Offshore Oil & Gas",
        "ar": "🌊 النفط والغاز البحري",
        "es": "🌊 Petróleo y Gas Offshore",
    },
    "nav_metros": {
        "fr": "🚇 Métros & Tunnels",
        "en": "🚇 Metros & Tunnels",
        "ar": "🚇 المترو والأنفاق",
        "es": "🚇 Metros y Túneles",
    },
    "nav_highrise": {
        "fr": "🏙️ Tours (Gratte-ciel)",
        "en": "🏙️ High-Rise",
        "ar": "🏙️ الأبراج الشاهقة",
        "es": "🏙️ Torres (Rascacielos)",
    },
    "nav_datacenter": {
        "fr": "🖥️ Data Centers",
        "en": "🖥️ Data Centers",
        "ar": "🖥️ مراكز البيانات",
        "es": "🖥️ Centros de Datos",
    },

    # --- Dashboard (app.py) ---
    "dashboard_intro_header": {"fr": "Tableau de bord", "en": "Dashboard", "ar": "لوحة التحكم", "es": "Panel principal"},
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
        "ar": "يقيّم تطبيق MAKU مخاطر الموقع لحظياً عبر خمس بيئات متخصصة، تعتمد كل "
              "منها على محرك حساب شفاف خاص بها (WBGT، Humidex، معايير ACGIH TLV، حدود "
              "التعرض المهني OEL، نموذج قانون القدرة للرياح، وطريقة Lee لحساب طاقة "
              "القوس الكهربائي). اختر وحدة من القائمة الجانبية لبدء تقييم.",
        "es": "MAKU evalúa el riesgo del sitio en tiempo real en cinco entornos "
              "especializados, cada uno con su propio motor de cálculo transparente "
              "(WBGT, Humidex, ACGIH TLV, OEL, perfil de viento de ley de potencia, "
              "método Lee para el arco eléctrico). Elija un módulo en el menú "
              "izquierdo para iniciar una evaluación.",
    },
    "dashboard_module_col_header": {
        "fr": "Modules disponibles",
        "en": "Available modules",
        "ar": "الوحدات المتاحة",
        "es": "Módulos disponibles",
    },
    "dashboard_footer": {
        "fr": "MAKU - moteur de risque basé sur des règles (5 environnements) avec "
              "couche narrative IA optionnelle.",
        "en": "MAKU - rule-based risk engine (5 environments) with optional AI "
              "narrative layer.",
        "ar": "MAKU - محرك مخاطر قائم على قواعد محددة (5 بيئات) مع طبقة سرد اختيارية "
              "بالذكاء الاصطناعي.",
        "es": "MAKU - motor de riesgo basado en reglas (5 entornos) con capa "
              "narrativa de IA opcional.",
    },

    # --- Field Inspection / Geolocation section (dashboard) ---
    "field_inspection_header": {
        "fr": "📍 Inspection de terrain - Géolocalisation",
        "en": "📍 Field Inspection - Geolocation",
        "ar": "📍 التفتيش الميداني - تحديد الموقع الجغرافي",
        "es": "📍 Inspección de Campo - Geolocalización",
    },
    "field_inspection_caption": {
        "fr": "Utilisez le GPS de votre appareil sur le terrain pour localiser "
              "automatiquement le site simulé MAKU le plus proche de votre position.",
        "en": "Use your device's GPS on-site to automatically find the nearest "
              "simulated MAKU site to your current position.",
        "ar": "استخدم نظام تحديد المواقع GPS في جهازك أثناء التواجد في الموقع "
              "للعثور تلقائياً على أقرب موقع محاكاة في MAKU لموقعك الحالي.",
        "es": "Use el GPS de su dispositivo en el sitio para localizar "
              "automáticamente el sitio simulado de MAKU más cercano a su posición.",
    },
    "field_inspection_button": {
        "fr": "🛰️ Détecter ma position GPS",
        "en": "🛰️ Detect my GPS location",
        "ar": "🛰️ تحديد موقعي عبر GPS",
        "es": "🛰️ Detectar mi ubicación GPS",
    },
    "field_inspection_refresh_button": {
        "fr": "🔄 Actualiser ma position",
        "en": "🔄 Refresh my location",
        "ar": "🔄 تحديث موقعي",
        "es": "🔄 Actualizar mi ubicación",
    },
    "field_inspection_loading": {
        "fr": "En attente de la position GPS... autorisez l'accès à la localisation "
              "si votre navigateur le demande.",
        "en": "Waiting for a GPS fix... allow location access if your browser prompts you.",
        "ar": "في انتظار تحديد الموقع عبر GPS... يرجى السماح بالوصول إلى الموقع إذا "
              "طلب المتصفح ذلك.",
        "es": "Esperando la señal GPS... permita el acceso a la ubicación si su "
              "navegador se lo solicita.",
    },
    "field_inspection_denied": {
        "fr": "Accès à la localisation refusé. Autorisez la géolocalisation dans les "
              "paramètres de votre navigateur pour utiliser cette fonctionnalité.",
        "en": "Location access denied. Enable geolocation permission in your browser "
              "settings to use this feature.",
        "ar": "تم رفض الوصول إلى الموقع. يرجى تفعيل إذن تحديد الموقع الجغرافي في "
              "إعدادات المتصفح لاستخدام هذه الميزة.",
        "es": "Acceso a la ubicación denegado. Habilite el permiso de geolocalización "
              "en la configuración de su navegador para usar esta función.",
    },
    "field_inspection_unavailable": {
        "fr": "Position indisponible. Vérifiez que le GPS de votre appareil est "
              "activé et réessayez.",
        "en": "Position unavailable. Check that your device's GPS is enabled and "
              "try again.",
        "ar": "الموقع غير متاح. تأكد من تفعيل نظام GPS في جهازك وأعد المحاولة.",
        "es": "Posición no disponible. Compruebe que el GPS de su dispositivo esté "
              "activado e inténtelo de nuevo.",
    },
    "field_inspection_timeout": {
        "fr": "Délai d'attente dépassé lors de la localisation. Réessayez, "
              "idéalement à l'extérieur avec un bon signal GPS.",
        "en": "Location request timed out. Try again, ideally outdoors with a "
              "clear GPS signal.",
        "ar": "انتهت مهلة طلب تحديد الموقع. أعد المحاولة، ويفضل في الهواء الطلق "
              "بإشارة GPS جيدة.",
        "es": "Se agotó el tiempo de espera de la solicitud de ubicación. "
              "Inténtelo de nuevo, preferiblemente al aire libre con buena señal GPS.",
    },
    "field_inspection_error_generic": {
        "fr": "Erreur de géolocalisation",
        "en": "Geolocation error",
        "ar": "خطأ في تحديد الموقع الجغرافي",
        "es": "Error de geolocalización",
    },
    "field_inspection_your_position": {
        "fr": "Votre position",
        "en": "Your position",
        "ar": "موقعك",
        "es": "Su posición",
    },
    "field_inspection_accuracy_label": {
        "fr": "Précision",
        "en": "Accuracy",
        "ar": "الدقة",
        "es": "Precisión",
    },
    "field_inspection_closest_site_label": {
        "fr": "Site simulé le plus proche",
        "en": "Closest simulated site",
        "ar": "أقرب موقع محاكاة",
        "es": "Sitio simulado más cercano",
    },
    "field_inspection_distance_label": {
        "fr": "Distance",
        "en": "Distance",
        "ar": "المسافة",
        "es": "Distancia",
    },
    "field_inspection_go_to_module_button": {
        "fr": "➡️ Ouvrir le module correspondant",
        "en": "➡️ Open the matching module",
        "ar": "➡️ فتح الوحدة المطابقة",
        "es": "➡️ Abrir el módulo correspondiente",
    },
    "field_inspection_sites_note": {
        "fr": "Les cinq sites affichés sont des coordonnées de référence illustratives "
              "utilisées pour cette démonstration MVP - elles ne représentent pas des "
              "installations réelles.",
        "en": "The five sites shown are illustrative reference coordinates used for "
              "this MVP demonstration - they do not represent real facilities.",
        "ar": "المواقع الخمسة المعروضة هي إحداثيات مرجعية توضيحية تُستخدم في هذا "
              "العرض التجريبي (MVP) - ولا تمثل منشآت حقيقية.",
        "es": "Los cinco sitios mostrados son coordenadas de referencia ilustrativas "
              "utilizadas para esta demostración MVP - no representan instalaciones "
              "reales.",
    },

    # --- Solar page ---
    "solar_header": {
        "fr": "☀️ Fermes solaires à grande échelle - Environnement désertique",
        "en": "☀️ Utility-Scale Solar Farms - Desert Environment",
        "ar": "☀️ مزارع الطاقة الشمسية واسعة النطاق - البيئة الصحراوية",
        "es": "☀️ Granjas Solares a Gran Escala - Entorno Desértico",
    },
    "solar_caption": {
        "fr": "Albédo de surface + charge thermique radiative liée au GHI pour les "
              "équipes MEP d'installation de trackers/modules",
        "en": "Land surface albedo + GHI-driven radiant heat load forecasting for "
              "MEP tracker/module crews",
        "ar": "انعكاسية سطح الأرض (Albedo) + التنبؤ بالحمل الحراري الإشعاعي الناتج "
              "عن GHI لطواقم تركيب متتبعات/وحدات الألواح",
        "es": "Albedo de la superficie terrestre + previsión de carga térmica "
              "radiante impulsada por GHI para cuadrillas MEP de instalación de "
              "seguidores/módulos",
    },
    "solar_env_data_header": {
        "fr": "Données environnementales",
        "en": "Environmental data",
        "ar": "البيانات البيئية",
        "es": "Datos ambientales",
    },
    "solar_realtime_header": {
        "fr": "Évaluation en temps réel de l'équipe MEP",
        "en": "Real-Time MEP Crew Assessment",
        "ar": "التقييم الآني لطاقم الأعمال الكهروميكانيكية",
        "es": "Evaluación en Tiempo Real de la Cuadrilla MEP",
    },
    "solar_temp_label": {
        "fr": "Température ambiante (°C)",
        "en": "Ambient temperature (°C)",
        "ar": "درجة الحرارة المحيطة (°C)",
        "es": "Temperatura ambiente (°C)",
    },
    "solar_ghi_label": {
        "fr": "Irradiation Globale Horizontale (GHI, W/m²)",
        "en": "Global Horizontal Irradiation (GHI, W/m²)",
        "ar": "الإشعاع الأفقي الكلي (GHI, W/m²)",
        "es": "Irradiación Global Horizontal (GHI, W/m²)",
    },
    "solar_uv_label": {
        "fr": "Indice UV",
        "en": "UV Index",
        "ar": "مؤشر الأشعة فوق البنفسجية (UV)",
        "es": "Índice UV",
    },
    "solar_surface_label": {
        "fr": "Type de surface (simulation capteurs SIG)",
        "en": "Surface type (simulated GIS sensor feed)",
        "ar": "نوع السطح (محاكاة بيانات مستشعرات نظم المعلومات الجغرافية)",
        "es": "Tipo de superficie (simulación de sensores SIG)",
    },
    "surf_pure_desert_sand": {
        "fr": "Sable désertique pur",
        "en": "Pure desert sand",
        "ar": "رمال صحراوية نقية",
        "es": "Arena desértica pura",
    },
    "surf_silicon_pv_panels": {
        "fr": "Panneaux PV en silicium",
        "en": "Silicon PV panels",
        "ar": "ألواح كهروضوئية من السيليكون",
        "es": "Paneles fotovoltaicos de silicio",
    },
    "surf_hybrid_assembly_zone": {
        "fr": "Zone d'assemblage hybride",
        "en": "Hybrid assembly zone",
        "ar": "منطقة تجميع هجينة",
        "es": "Zona de ensamblaje híbrida",
    },
    "perceived_temp_label": {
        "fr": "Température perçue (corrigée)",
        "en": "Perceived Temperature (Corrected)",
        "ar": "درجة الحرارة المحسوسة (المصححة)",
        "es": "Temperatura percibida (corregida)",
    },
    "albedo_delta_label": {
        "fr": "Albédo",
        "en": "Albedo",
        "ar": "معامل الانعكاسية (Albedo)",
        "es": "Albedo",
    },
    "risk_level_label": {
        "fr": "Niveau de Risque",
        "en": "Risk Level",
        "ar": "مستوى الخطورة",
        "es": "Nivel de Riesgo",
    },
    "shift_rotation_label": {
        "fr": "Rotation des Équipes",
        "en": "Team Rotation",
        "ar": "تناوب الطواقم",
        "es": "Rotación de Equipos",
    },
    "solar_critical_alert": {
        "fr": "🚨 **ALERTE CRITIQUE :** Risque d'insolation aiguë immédiat pour l'assemblage "
              "mécanique des trackers.",
        "en": "🚨 **CRITICAL ALERT:** Immediate acute heat-stroke risk for tracker "
              "mechanical assembly.",
        "ar": "🚨 **تنبيه حرج:** خطر ضربة شمس حادة وفورية لطاقم التجميع الميكانيكي "
              "للمتتبعات الشمسية.",
        "es": "🚨 **ALERTA CRÍTICA:** Riesgo inmediato de golpe de calor agudo para "
              "el ensamblaje mecánico de seguidores.",
    },
    "solar_high_alert": {
        "fr": "⚠️ **ATTENTION :** Risque élevé de stress thermique. Rotation obligatoire.",
        "en": "⚠️ **WARNING:** High heat-stress risk. Mandatory rotation required.",
        "ar": "⚠️ **تحذير:** خطر مرتفع للإجهاد الحراري. التناوب إلزامي.",
        "es": "⚠️ **ADVERTENCIA:** Alto riesgo de estrés térmico. Rotación obligatoria.",
    },
    "solar_standard_ok": {
        "fr": "✅ Conditions opérationnelles standards. Assurez l'hydratation continue "
              "des techniciens.",
        "en": "✅ Standard operating conditions. Ensure continuous technician hydration.",
        "ar": "✅ ظروف تشغيل اعتيادية. تأكد من استمرار ترطيب الفنيين.",
        "es": "✅ Condiciones operativas estándar. Asegure la hidratación continua "
              "de los técnicos.",
    },

    # --- Offshore page ---
    "offshore_header": {
        "fr": "🌊 Pétrole & gaz offshore - Environnement marin",
        "en": "🌊 Offshore Oil & Gas - Marine Environment",
        "ar": "🌊 النفط والغاز البحري - البيئة البحرية",
        "es": "🌊 Petróleo y Gas Offshore - Entorno Marino",
    },
    "offshore_caption": {
        "fr": "Matrice de risque Humidex marine + seuils opérationnels vent/houle pour "
              "les équipes de soudure, tuyauterie et échafaudage",
        "en": "Marine Humidex Risk Matrix + wind/wave operational gating for welding, "
              "pipe-fitting, scaffolding crews",
        "ar": "مصفوفة مخاطر الرطوبة الحرارية البحرية (Humidex) + عتبات تشغيلية للرياح "
              "والأمواج لطواقم اللحام وتركيب الأنابيب والسقالات",
        "es": "Matriz de riesgo Humidex marina + límites operativos de viento/oleaje "
              "para cuadrillas de soldadura, tuberías y andamios",
    },
    "wind_gate_label": {"fr": "Seuil vent", "en": "Wind gate", "ar": "عتبة الرياح", "es": "Umbral de viento"},
    "wave_gate_label": {"fr": "Seuil houle", "en": "Wave gate", "ar": "عتبة الأمواج", "es": "Umbral de oleaje"},
    "offshore_env_data_header": {
        "fr": "Télémétrie Bouée GIS (Simulation)",
        "en": "GIS Buoy Telemetry (Simulated)",
        "ar": "قياس بُعد العوامة الجغرافية (محاكاة)",
        "es": "Telemetría de Boya SIG (Simulación)",
    },
    "offshore_realtime_header": {
        "fr": "Évaluation en Temps Réel des Opérations Marines",
        "en": "Real-Time Marine Operations Assessment",
        "ar": "التقييم الآني للعمليات البحرية",
        "es": "Evaluación en Tiempo Real de Operaciones Marinas",
    },
    "offshore_temp_label": {
        "fr": "Température ambiante (°C)",
        "en": "Ambient temperature (°C)",
        "ar": "درجة الحرارة المحيطة (°C)",
        "es": "Temperatura ambiente (°C)",
    },
    "offshore_rh_label": {
        "fr": "Humidité relative (%)",
        "en": "Relative humidity (%)",
        "ar": "الرطوبة النسبية (%)",
        "es": "Humedad relativa (%)",
    },
    "offshore_wind_label": {
        "fr": "Vitesse du vent (nœuds)",
        "en": "Wind speed (knots)",
        "ar": "سرعة الرياح (عقدة)",
        "es": "Velocidad del viento (nudos)",
    },
    "humidex_label": {
        "fr": "Humidex",
        "en": "Humidex",
        "ar": "مؤشر الرطوبة الحرارية (Humidex)",
        "es": "Humidex",
    },
    "wind_status_label": {"fr": "Statut du vent", "en": "Wind Status", "ar": "حالة الرياح", "es": "Estado del viento"},
    "wind_status_normal": {
        "fr": "Opérations normales",
        "en": "Normal Operations",
        "ar": "عمليات اعتيادية",
        "es": "Operaciones normales",
    },
    "wind_status_restricted": {
        "fr": "Restreint - Surveillance rapprochée",
        "en": "Restricted - Monitor Closely",
        "ar": "مقيّد - مراقبة لصيقة",
        "es": "Restringido - Vigilancia estrecha",
    },
    "wind_status_suspended": {
        "fr": "Suspendu - Danger grue/levage",
        "en": "Suspended - Crane/Lifting Danger",
        "ar": "موقوف - خطر على الرافعات وعمليات الرفع",
        "es": "Suspendido - Peligro de grúa/izado",
    },
    "offshore_elevated_alert": {
        "fr": "⚠️ **ATTENTION :** Stress thermique marin élevé. Resserrez la rotation "
              "des équipes de soudure/tuyauterie et surveillez la tendance Humidex.",
        "en": "⚠️ **WARNING:** Elevated marine heat stress. Tighten welding/pipe-fitting "
              "crew rotation and monitor the Humidex trend.",
        "ar": "⚠️ **تحذير:** إجهاد حراري بحري مرتفع. شدّد تناوب طواقم اللحام وتركيب "
              "الأنابيب وراقب اتجاه مؤشر Humidex.",
        "es": "⚠️ **ADVERTENCIA:** Estrés térmico marino elevado. Refuerce la "
              "rotación de las cuadrillas de soldadura/tuberías y vigile la "
              "tendencia del Humidex.",
    },
    "offshore_standard_ok": {
        "fr": "✅ Conditions opérationnelles marines normales. Maintenir le protocole "
              "HSE standard.",
        "en": "✅ Standard marine operating conditions. Maintain standard HSE protocol.",
        "ar": "✅ ظروف تشغيل بحرية اعتيادية. حافظ على بروتوكول السلامة والصحة "
              "المهنية القياسي.",
        "es": "✅ Condiciones operativas marinas normales. Mantenga el protocolo "
              "HSE estándar.",
    },

    # --- Underground page ---
    "underground_header": {
        "fr": "🚇 Métros & tunnels - Infrastructure souterraine",
        "en": "🚇 Metros & Tunnels - Underground Substructure Infrastructure",
        "ar": "🚇 المترو والأنفاق - البنية التحتية الجوفية",
        "es": "🚇 Metros y Túneles - Infraestructura Subterránea",
    },
    "underground_caption": {
        "fr": "Charge thermique du tunnelier + corrélation OEL en temps réel générant "
              "des dépassements de sécurité prédictifs pour les équipes électriques MEP",
        "en": "TBM heat load + real-time OEL correlation generating predictive safety "
              "overrides for MEP electrical crews",
        "ar": "الحمل الحراري لآلة حفر الأنفاق + ربط آني بحدود التعرض المهني (OEL) "
              "لتوليد تجاوزات سلامة تنبؤية لطواقم الأعمال الكهربائية",
        "es": "Carga térmica de la tuneladora + correlación OEL en tiempo real que "
              "genera anulaciones de seguridad predictivas para cuadrillas "
              "eléctricas MEP",
    },
    "gas_exceeds_label": {
        "fr": "Limite gaz OEL dépassée",
        "en": "Gas OEL exceeded",
        "ar": "تجاوز حد OEL للغاز",
        "es": "Límite OEL de gas superado",
    },
    "dust_exceeds_label": {
        "fr": "Limite poussière OEL dépassée",
        "en": "Dust OEL exceeded",
        "ar": "تجاوز حد OEL للغبار",
        "es": "Límite OEL de polvo superado",
    },
    "underground_env_data_header": {
        "fr": "Télémétrie 3D SIG Souterraine (Simulation)",
        "en": "3D Subsurface GIS Telemetry (Simulated)",
        "ar": "قياس بُعد جغرافي ثلاثي الأبعاد للباطن الأرضي (محاكاة)",
        "es": "Telemetría SIG Subterránea 3D (Simulación)",
    },
    "underground_realtime_header": {
        "fr": "Évaluation en Temps Réel des Équipes MEP Électriques",
        "en": "Real-Time MEP Electrical Crew Assessment",
        "ar": "التقييم الآني لطواقم الأعمال الكهربائية",
        "es": "Evaluación en Tiempo Real de Cuadrillas Eléctricas MEP",
    },
    "underground_ambient_temp_label": {
        "fr": "Température ambiante (°C)",
        "en": "Ambient temperature (°C)",
        "ar": "درجة الحرارة المحيطة (°C)",
        "es": "Temperatura ambiente (°C)",
    },
    "underground_geo_humidity_label": {
        "fr": "Humidité géothermique piégée (%)",
        "en": "Trapped geothermal humidity (%)",
        "ar": "الرطوبة الأرضية المحبوسة (%)",
        "es": "Humedad geotérmica atrapada (%)",
    },
    "underground_pm25_label": {
        "fr": "Particules en suspension PM2.5 (µg/m³)",
        "en": "Airborne particulate matter PM2.5 (µg/m³)",
        "ar": "الجسيمات العالقة PM2.5 (µg/m³)",
        "es": "Partículas en suspensión PM2.5 (µg/m³)",
    },
    "underground_co_label": {
        "fr": "Monoxyde de carbone CO (ppm)",
        "en": "Carbon monoxide CO (ppm)",
        "ar": "أول أكسيد الكربون CO (ppm)",
        "es": "Monóxido de carbono CO (ppm)",
    },
    "underground_perceived_temp_label": {
        "fr": "Température perçue (chaleur piégée)",
        "en": "Perceived Temperature (Trapped Heat)",
        "ar": "درجة الحرارة المحسوسة (الحرارة المحبوسة)",
        "es": "Temperatura percibida (calor atrapado)",
    },
    "underground_critical_alert": {
        "fr": "🚨 **DÉPASSEMENT DE SÉCURITÉ CRITIQUE :** Halte immédiate des travaux de "
              "câblage haute tension MEP. Évacuer le front de taille et revérifier "
              "la ventilation avant tout nouveau test.",
        "en": "🚨 **CRITICAL SAFETY OVERRIDE:** Immediate halt to MEP high-voltage cabling "
              "work. Evacuate the excavation face and re-verify ventilation before re-testing.",
        "ar": "🚨 **تجاوز سلامة حرج:** إيقاف فوري لأعمال مد الكابلات عالية الجهد. "
              "إخلاء واجهة الحفر وإعادة التحقق من التهوية قبل أي اختبار جديد.",
        "es": "🚨 **ANULACIÓN DE SEGURIDAD CRÍTICA:** Detención inmediata del cableado "
              "de alta tensión MEP. Evacúe el frente de excavación y reverifique la "
              "ventilación antes de volver a probar.",
    },
    "underground_high_alert": {
        "fr": "⚠️ **ATTENTION :** Stress thermique et/ou qualité de l'air en approche des "
              "limites OEL. Resserrez la rotation des équipes et surveillez les capteurs.",
        "en": "⚠️ **WARNING:** Heat stress and/or air quality approaching OEL limits. "
              "Tighten crew rotation and watch the sensor trend closely.",
        "ar": "⚠️ **تحذير:** إجهاد حراري و/أو جودة هواء تقترب من حدود OEL. شدّد "
              "تناوب الطواقم وراقب اتجاه المستشعرات عن كثب.",
        "es": "⚠️ **ADVERTENCIA:** El estrés térmico y/o la calidad del aire se "
              "acercan a los límites OEL. Refuerce la rotación de cuadrillas y "
              "vigile de cerca la tendencia de los sensores.",
    },
    "underground_standard_ok": {
        "fr": "✅ Conditions souterraines standards. Maintenir la cadence de surveillance "
              "OEL et thermique.",
        "en": "✅ Standard underground conditions. Maintain the OEL and heat monitoring cadence.",
        "ar": "✅ ظروف جوفية اعتيادية. حافظ على وتيرة مراقبة حدود OEL والحرارة.",
        "es": "✅ Condiciones subterráneas estándar. Mantenga la cadencia de "
              "monitoreo de OEL y calor.",
    },

    # --- High-Rise page ---
    "highrise_header": {
        "fr": "🏙️ Construction de tours - Environnement urbain vertical",
        "en": "🏙️ High-Rise Building Construction - Vertical Urban Environment",
        "ar": "🏙️ إنشاء الأبراج الشاهقة - البيئة الحضرية الرأسية",
        "es": "🏙️ Construcción de Torres - Entorno Urbano Vertical",
    },
    "highrise_caption": {
        "fr": "Jumeau numérique BIM 3D + télémétrie d'anémomètres multi-niveaux pour "
              "une matrice de risque de cisaillement du vent étage par étage",
        "en": "3D BIM digital twin + multi-level anemometer telemetry driving a "
              "floor-by-floor wind-shear risk matrix",
        "ar": "توأم رقمي ثلاثي الأبعاد (BIM) + قياس بُعد لأجهزة قياس الرياح متعددة "
              "المستويات، لبناء مصفوفة مخاطر قص الرياح طابقاً بطابق",
        "es": "Gemelo digital BIM 3D + telemetría de anemómetros multinivel que "
              "alimenta una matriz de riesgo de cizallamiento de viento piso a piso",
    },
    "crane_gate_label": {"fr": "Seuil grue", "en": "Crane gate", "ar": "عتبة الرافعة", "es": "Umbral de grúa"},
    "facade_gate_label": {
        "fr": "Seuil façade/accès suspendu",
        "en": "Facade/access gate",
        "ar": "عتبة الواجهة/الوصول المعلّق",
        "es": "Umbral de fachada/acceso suspendido",
    },
    "fall_arrest_alert": {
        "fr": "⚠️ ALERTE ANTICHUTE / ACCÈS SUSPENDU",
        "en": "⚠️ FALL-ARREST / SUSPENDED-ACCESS ALERT",
        "ar": "⚠️ تنبيه نظام إيقاف السقوط / الوصول المعلّق",
        "es": "⚠️ ALERTA DE ANTICAÍDAS / ACCESO SUSPENDIDO",
    },
    "highrise_env_data_header": {
        "fr": "Télémétrie BIM 3D / Anémomètre (Simulation)",
        "en": "3D BIM / Anemometer Telemetry (Simulated)",
        "ar": "قياس بُعد BIM ثلاثي الأبعاد / جهاز قياس الرياح (محاكاة)",
        "es": "Telemetría BIM 3D / Anemómetro (Simulación)",
    },
    "highrise_realtime_header": {
        "fr": "Évaluation en Temps Réel Grue & Accès Suspendu",
        "en": "Real-Time Crane & Suspended-Access Assessment",
        "ar": "التقييم الآني للرافعة والوصول المعلّق",
        "es": "Evaluación en Tiempo Real de Grúa y Acceso Suspendido",
    },
    "highrise_ground_wind_label": {
        "fr": "Vitesse du vent au sol (nœuds)",
        "en": "Ground wind speed (knots)",
        "ar": "سرعة الرياح عند مستوى الأرض (عقدة)",
        "es": "Velocidad del viento en superficie (nudos)",
    },
    "highrise_floor_level_label": {
        "fr": "Étage de travail actuel",
        "en": "Current working floor level",
        "ar": "الطابق الحالي لموقع العمل",
        "es": "Nivel de piso de trabajo actual",
    },
    "highrise_crane_load_label": {
        "fr": "Masse de charge du levage (tonnes)",
        "en": "Crane lift load mass (tons)",
        "ar": "كتلة حمولة الرفع (طن)",
        "es": "Masa de carga de izado (toneladas)",
    },
    "scaled_wind_label": {
        "fr": "Vent amplifié en hauteur (nœuds)",
        "en": "Scaled Wind at Height (knots)",
        "ar": "الرياح المعدّلة حسب الارتفاع (عقدة)",
        "es": "Viento ajustado por altura (nudos)",
    },
    "oscillation_index_label": {
        "fr": "Indice d'oscillation de charge",
        "en": "Load Oscillation Index",
        "ar": "مؤشر تذبذب الحمولة",
        "es": "Índice de oscilación de carga",
    },
    "highrise_critical_alert": {
        "fr": "🚨 **DÉPASSEMENT DE SÉCURITÉ CRITIQUE :** Suspension immédiate de tous les "
              "levages par grue et des travaux de façade/mur-rideau en hauteur. Vérifiez "
              "les points d'ancrage antichute avant toute reprise.",
        "en": "🚨 **CRITICAL SAFETY OVERRIDE:** Immediate suspension of all crane lifts "
              "and facade/curtain-wall work at height. Recheck fall-arrest tie-off points "
              "before resuming.",
        "ar": "🚨 **تجاوز سلامة حرج:** إيقاف فوري لجميع عمليات الرفع بالرافعة وأعمال "
              "الواجهات/الجدران الساترة على الارتفاع. أعد التحقق من نقاط تثبيت نظام "
              "إيقاف السقوط قبل استئناف العمل.",
        "es": "🚨 **ANULACIÓN DE SEGURIDAD CRÍTICA:** Suspensión inmediata de todos "
              "los izados con grúa y del trabajo en fachada/muro cortina en altura. "
              "Reverifique los puntos de anclaje anticaídas antes de reanudar.",
    },
    "highrise_high_alert": {
        "fr": "⚠️ **ATTENTION :** Cisaillement du vent élevé en hauteur. Informez "
              "l'opérateur de grue et retardez les levages non critiques.",
        "en": "⚠️ **WARNING:** High wind shear at this floor level. Notify the crane "
              "operator and delay non-critical lifts.",
        "ar": "⚠️ **تحذير:** قص رياح مرتفع عند هذا الطابق. أبلغ مشغّل الرافعة وأجّل "
              "عمليات الرفع غير الحرجة.",
        "es": "⚠️ **ADVERTENCIA:** Alto cizallamiento de viento en este piso. "
              "Notifique al operador de la grúa y retrase los izados no críticos.",
    },
    "highrise_standard_ok": {
        "fr": "✅ Conditions de vent standards en hauteur. Maintenir la surveillance "
              "anémométrique à chaque poste.",
        "en": "✅ Standard wind conditions at height. Maintain anemometer monitoring each shift.",
        "ar": "✅ ظروف رياح اعتيادية على الارتفاع. حافظ على مراقبة جهاز قياس الرياح "
              "في كل نوبة عمل.",
        "es": "✅ Condiciones de viento estándar en altura. Mantenga el monitoreo "
              "del anemómetro en cada turno.",
    },

    # --- Data Center page ---
    "datacenter_header": {
        "fr": "🖥️ Construction & mise en service de data centers - Environnement "
              "critique contrôlé",
        "en": "🖥️ Data Center Construction & Commissioning - Controlled Critical "
              "Environment",
        "ar": "🖥️ إنشاء وتشغيل مراكز البيانات - البيئة الحرجة المتحكم بها",
        "es": "🖥️ Construcción y Puesta en Marcha de Centros de Datos - Entorno "
              "Crítico Controlado",
    },
    "datacenter_caption": {
        "fr": "Cartographie thermique IoT allée chaude/froide + méthode Lee pour "
              "l'arc électrique, croisée avec les conditions d'espace confiné et "
              "d'agent propre",
        "en": "Rack-level IoT hot-aisle/cold-aisle thermal mapping + Lee-method "
              "arc-flash screening, cross-referenced against confined-space and "
              "clean-agent commissioning conditions",
        "ar": "رسم خرائط حرارية عبر إنترنت الأشياء للممرات الساخنة/الباردة على "
              "مستوى الرفوف + فحص طاقة القوس الكهربائي بطريقة Lee، مع الربط بظروف "
              "الأماكن المحصورة وأنظمة الإطفاء بالغاز النظيف",
        "es": "Mapeo térmico IoT de pasillo caliente/frío a nivel de rack + "
              "detección de arco eléctrico por método Lee, contrastado con las "
              "condiciones de espacio confinado y agente limpio",
    },
    "esd_risk_label": {
        "fr": "Risque ESD",
        "en": "ESD risk",
        "ar": "خطر التفريغ الكهروستاتيكي (ESD)",
        "es": "Riesgo ESD",
    },
    "confined_clean_agent_label": {
        "fr": "Espace confiné + agent propre présent",
        "en": "Confined space + clean-agent present",
        "ar": "مكان محصور + وجود نظام إطفاء بغاز نظيف",
        "es": "Espacio confinado + agente limpio presente",
    },
    "datacenter_env_data_header": {
        "fr": "Télémétrie IoT Micro-SIG au Niveau des Baies (Simulation)",
        "en": "Rack-Level Micro-GIS IoT Telemetry (Simulated)",
        "ar": "قياس بُعد عبر إنترنت الأشياء على مستوى الرفوف (محاكاة)",
        "es": "Telemetría IoT Micro-SIG a Nivel de Rack (Simulación)",
    },
    "datacenter_realtime_header": {
        "fr": "Évaluation en Temps Réel - Électrique, Thermique & Suppression Incendie",
        "en": "Real-Time Electrical, Thermal & Fire-Suppression Assessment",
        "ar": "التقييم الآني - الكهرباء، الحرارة، وإطفاء الحرائق",
        "es": "Evaluación en Tiempo Real - Eléctrica, Térmica y Supresión de Incendios",
    },
    "datacenter_load_label": {
        "fr": "Charge électrique en direct (kW)",
        "en": "Live electrical load (kW)",
        "ar": "الحمل الكهربائي المباشر (kW)",
        "es": "Carga eléctrica en vivo (kW)",
    },
    "datacenter_hot_aisle_label": {
        "fr": "Température allée chaude (°C)",
        "en": "Hot-aisle temperature (°C)",
        "ar": "درجة حرارة الممر الساخن (°C)",
        "es": "Temperatura del pasillo caliente (°C)",
    },
    "datacenter_confined_label": {
        "fr": "Espace de travail confiné (plénum/faux-plafond)",
        "en": "Confined ceiling-void workspace",
        "ar": "مساحة عمل محصورة (فراغ السقف المستعار)",
        "es": "Espacio de trabajo confinado (plenum/falso techo)",
    },
    "datacenter_gas_armed_label": {
        "fr": "Système de suppression incendie gazeux armé",
        "en": "Gaseous fire-suppression system armed",
        "ar": "نظام إطفاء الحرائق الغازي مفعّل",
        "es": "Sistema de supresión de incendios por gas armado",
    },
    "arc_flash_energy_label": {
        "fr": "Énergie incidente arc électrique (cal/cm²)",
        "en": "Arc-Flash Incident Energy (cal/cm²)",
        "ar": "طاقة القوس الكهربائي الساقطة (cal/cm²)",
        "es": "Energía incidente de arco eléctrico (cal/cm²)",
    },
    "thermal_differential_label": {
        "fr": "Différentiel thermique allée chaude/froide (°C)",
        "en": "Hot/Cold-Aisle Thermal Differential (°C)",
        "ar": "الفارق الحراري بين الممرين الساخن والبارد (°C)",
        "es": "Diferencial térmico pasillo caliente/frío (°C)",
    },
    "datacenter_critical_alert": {
        "fr": "🚨 **DÉPASSEMENT DE SÉCURITÉ CRITIQUE :** Halte immédiate des travaux de "
              "mise en service électrique/mécanique/suppression incendie dans cette zone. "
              "Désénergisez avant toute intervention et revérifiez les conditions.",
        "en": "🚨 **CRITICAL SAFETY OVERRIDE:** Immediate halt to electrical/mechanical/"
              "fire-suppression commissioning work in this zone. De-energize before any "
              "work and recheck conditions before resuming.",
        "ar": "🚨 **تجاوز سلامة حرج:** إيقاف فوري لأعمال التشغيل الكهربائية/الميكانيكية/"
              "إطفاء الحرائق في هذه المنطقة. افصل الطاقة قبل أي تدخل وأعد التحقق من "
              "الظروف قبل الاستئناف.",
        "es": "🚨 **ANULACIÓN DE SEGURIDAD CRÍTICA:** Detención inmediata del trabajo "
              "de puesta en marcha eléctrica/mecánica/supresión de incendios en esta "
              "zona. Desenergice antes de cualquier intervención y reverifique las "
              "condiciones antes de reanudar.",
    },
    "datacenter_high_alert": {
        "fr": "⚠️ **ATTENTION :** Risque élevé d'arc électrique ou de stress thermique "
              "allée chaude/froide. Confirmez le classement EPI et resserrez la rotation "
              "des équipes.",
        "en": "⚠️ **WARNING:** Elevated arc-flash or hot/cold-aisle thermal risk. Confirm "
              "PPE rating and tighten commissioning crew rotation.",
        "ar": "⚠️ **تحذير:** خطر مرتفع لقوس كهربائي أو إجهاد حراري بين الممرين. "
              "تأكد من تصنيف معدات الوقاية الشخصية وشدّد تناوب طواقم التشغيل.",
        "es": "⚠️ **ADVERTENCIA:** Riesgo elevado de arco eléctrico o estrés térmico "
              "entre pasillos. Confirme la clasificación de EPP y refuerce la "
              "rotación de la cuadrilla de puesta en marcha.",
    },
    "datacenter_standard_ok": {
        "fr": "✅ Conditions standards de mise en service. Maintenir la surveillance "
              "thermique, arc électrique et espace confiné.",
        "en": "✅ Standard commissioning conditions. Maintain thermal, arc-flash, and "
              "confined-space monitoring.",
        "ar": "✅ ظروف تشغيل اعتيادية. حافظ على مراقبة الحرارة، القوس الكهربائي، "
              "والأماكن المحصورة.",
        "es": "✅ Condiciones de puesta en marcha estándar. Mantenga el monitoreo "
              "térmico, de arco eléctrico y de espacio confinado.",
    },
}


def t(key: str, lang: str = DEFAULT_LANG) -> str:
    """Look up a UI string by key for the given language code (defaults to French)."""
    entry = STRINGS.get(key)
    if entry is None:
        return key
    return entry.get(lang, entry.get(DEFAULT_LANG, key))


def is_rtl(lang: str) -> bool:
    """Whether the given language code reads right-to-left."""
    return lang in RTL_LANGS


def apply_rtl_style(st_module, lang: str) -> None:
    """Best-effort right-to-left layout for Arabic. Streamlit has no native
    RTL mode, so this injects a small CSS block that right-aligns text and
    flips flex-based layout direction (columns, sidebar) when Arabic is
    selected. No-op for fr/en/es. Call once near the top of every page,
    right after language_selector()."""
    if not is_rtl(lang):
        return
    st_module.markdown(
        """
        <style>
        .stApp, [data-testid="stSidebar"] {
            direction: rtl;
        }
        .stApp p, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
        .stApp label, .stApp caption, .stMarkdown, .stCaption,
        [data-testid="stSidebar"] * {
            text-align: right;
        }
        .stApp [data-testid="stMetricLabel"],
        .stApp [data-testid="stMetricValue"] {
            text-align: right;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def language_selector(st_module, sidebar=True, key: str = "lang") -> str:
    """
    Renders the shared language selector and returns the resolved language
    code ("fr"/"en"/"ar"/"es"). Backed by st.session_state so the choice
    persists as the user navigates between pages in the multipage app.
    Also applies RTL styling automatically when Arabic is selected, so
    callers don't need a separate apply_rtl_style() call.
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
    apply_rtl_style(st_module, st_module.session_state[key])
    return st_module.session_state[key]
