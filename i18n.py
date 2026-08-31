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

LANGUAGES = {
    "Français": "fr", "English": "en", "العربية": "ar", "Español": "es",
    "中文": "zh", "日本語": "ja", "हिन्दी": "hi", "اردو": "ur",
    "Dansk": "da", "Nederlands": "nl", "Norsk": "no", "Svenska": "sv",
    "Português": "pt", "Deutsch": "de",
}
DEFAULT_LANG = "fr"
RTL_LANGS = {"ar", "ur"}

STRINGS = {
    # --- Global / sidebar ---
    "app_title": {"fr": "🏗️ MAKU", "en": "🏗️ MAKU", "ar": "🏗️ MAKU", "es": "🏗️ MAKU", "zh": '🏗️ MAKU', "ja": '🏗️ MAKU', "hi": '🏗️ MAKU', "ur": '🏗️ MAKU', "da": '🏗️ MAKU', "nl": '🏗️ MAKU', "no": '🏗️ MAKU', "sv": '🏗️ MAKU', "pt": '🏗️ MAKU', "de": '🏗️ MAKU'},
    "app_tagline": {
        "fr": "IA Multi-Environnement pour l'Évaluation des Risques Cinétiques - "
              "Mega-Souterrain, Offshore, Solaire, Tours & Data Centers",
        "en": "Multi-Environment AI for Kinetic Risk Assessment - Mega-Underground, "
              "Offshore, Solar, High-Rise & Data Center construction",
        "ar": "منصة ذكاء اصطناعي متعددة البيئات لتقييم المخاطر الحركية - الأنفاق "
              "الكبرى، المنشآت البحرية، الطاقة الشمسية، الأبراج ومراكز البيانات",
        "es": "IA Multi-Entorno para la Evaluación de Riesgos Cinéticos - "
              "Mega-Subterráneo, Offshore, Solar, Torres y Centros de Datos",
              "zh": '多环境人工智能动能风险评估平台 —— 大型地下工程、海上、太阳能、高层建筑与数据中心施工',
              "ja": 'マルチ環境対応AIキネティックリスク評価 — 大規模地下、洋上、太陽光、高層ビル、データセンター建設',
              "hi": 'बहु-पर्यावरण एआई गतिज जोखिम मूल्यांकन - मेगा-भूमिगत, अपतटीय, सौर, ऊंची इमारतें और डेटा केंद्र निर्माण',
              "ur": 'ملٹی انوائرنمنٹ اے آئی کائنیٹک رسک اسیسمنٹ - میگا انڈرگراؤنڈ، آف شور، سولر، بلند عمارات اور ڈیٹا سینٹر تعمیرات',
              "da": 'Multi-miljø AI til kinetisk risikovurdering - Mega-undergrund, offshore, sol, højhuse og datacenterbyggeri',
              "nl": 'Multi-omgeving AI voor kinetische risicobeoordeling - Mega-ondergronds, offshore, zonne-energie, hoogbouw en datacenterbouw',
              "no": 'Multi-miljø AI for kinetisk risikovurdering - Mega-undergrunn, offshore, sol, høyhus og datasenterbygging',
              "sv": 'AI för kinetisk riskbedömning i flera miljöer - Mega-underjordiskt, offshore, sol, höghus och datacenterbyggande',
              "pt": 'IA Multi-Ambiente para Avaliação de Riscos Cinéticos - Construção de Mega-Subterrâneos, Offshore, Solar, Torres e Centros de Dados',
              "de": 'Multi-Umgebungs-KI für kinetische Risikobewertung - Mega-Untergrund-, Offshore-, Solar-, Hochhaus- und Rechenzentrumsbau',
    },
    "lang_label": {"fr": "Langue", "en": "Language", "ar": "اللغة", "es": "Idioma", "zh": '语言', "ja": '言語', "hi": 'भाषा', "ur": 'زبان', "da": 'Sprog', "nl": 'Taal', "no": 'Språk', "sv": 'Språk', "pt": 'Idioma', "de": 'Sprache'},
    "ai_layer_header": {
        "fr": "Couche narrative IA (optionnelle)",
        "en": "AI Narrative Layer (optional)",
        "ar": "طبقة السرد بالذكاء الاصطناعي (اختيارية)",
        "es": "Capa narrativa de IA (opcional)",
        "zh": 'AI叙述层（可选）',
        "ja": 'AIナラティブ層（任意）',
        "hi": 'एआई नैरेटिव लेयर (वैकल्पिक)',
        "ur": 'AI بیانیہ پرت (اختیاری)',
        "da": 'AI-fortællingslag (valgfrit)',
        "nl": 'AI-verhaallaag (optioneel)',
        "no": 'AI-fortellerlag (valgfritt)',
        "sv": 'AI-berättelselager (valfritt)',
        "pt": 'Camada narrativa de IA (opcional)',
        "de": 'KI-Erzählebene (optional)',
    },
    "api_key_label": {
        "fr": "Clé API Anthropic",
        "en": "Anthropic API key",
        "ar": "مفتاح API الخاص بـ Anthropic",
        "es": "Clave API de Anthropic",
        "zh": 'Anthropic API 密钥',
        "ja": 'Anthropic APIキー',
        "hi": 'Anthropic एपीआई कुंजी',
        "ur": 'Anthropic API کلید',
        "da": 'Anthropic API-nøgle',
        "nl": 'Anthropic API-sleutel',
        "no": 'Anthropic API-nøkkel',
        "sv": 'Anthropic API-nyckel',
        "pt": 'Chave de API da Anthropic',
        "de": 'Anthropic-API-Schlüssel',
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
              "zh": '可选。没有密钥，MAKU 仍可依靠其基于规则的风险公式和管控建议正常运行——API 密钥仅额外提供通俗语言的叙述性摘要。',
              "ja": '任意です。キーがなくても、MAKUはルールベースのリスク計算式と管理策の提案により引き続き機能します。APIキーは、その上に平易な言葉での要約ナラティブを追加するだけです。',
              "hi": 'वैकल्पिक। बिना कुंजी के भी MAKU अपने नियम-आधारित जोखिम सूत्रों और नियंत्रण सिफारिशों पर काम करता रहता है - एपीआई कुंजी केवल इसके ऊपर सरल भाषा में एक सारांश जोड़ती है।',
              "ur": 'اختیاری۔ کلید کے بغیر بھی MAKU اپنے قاعدہ پر مبنی رسک فارمولوں اور کنٹرول تجاویز پر کام کرتا رہتا ہے - API کلید صرف اس کے اوپر سادہ زبان میں ایک بیانیہ خلاصہ شامل کرتی ہے۔',
              "da": 'Valgfrit. Uden en nøgle kører MAKU stadig på sine regelbaserede risikoformler og kontrolanbefalinger - API-nøglen tilføjer blot et resumé i almindeligt sprog oven i.',
              "nl": 'Optioneel. Zonder sleutel blijft MAKU werken op basis van zijn regelgebaseerde risicoformules en beheersaanbevelingen - de API-sleutel voegt alleen een samenvatting in gewone taal toe.',
              "no": 'Valgfritt. Uten en nøkkel kjører MAKU fortsatt på sine regelbaserte risikoformler og tiltaksanbefalinger - API-nøkkelen legger bare til et sammendrag i vanlig språk på toppen.',
              "sv": 'Valfritt. Utan en nyckel körs MAKU fortfarande på sina regelbaserade riskformler och åtgärdsrekommendationer - API-nyckeln lägger bara till en sammanfattning i vanligt språk ovanpå.',
              "pt": 'Opcional. Sem uma chave, o MAKU continua funcionando com suas fórmulas de risco baseadas em regras e recomendações de controle - a chave de API apenas adiciona um resumo narrativo em linguagem simples.',
              "de": 'Optional. Ohne Schlüssel funktioniert MAKU weiterhin mit seinen regelbasierten Risikoformeln und Kontrollempfehlungen - der API-Schlüssel fügt lediglich eine Zusammenfassung in einfacher Sprache hinzu.',
    },
    "work_rate_label": {"fr": "Cadence de travail", "en": "Work rate", "ar": "معدل العمل", "es": "Ritmo de trabajo", "zh": '工作强度', "ja": '作業強度', "hi": 'कार्य दर', "ur": 'کام کی شرح', "da": 'Arbejdstempo', "nl": 'Werktempo', "no": 'Arbeidstempo', "sv": 'Arbetstakt', "pt": 'Ritmo de trabalho', "de": 'Arbeitstempo'},
    "wr_light": {"fr": "légère", "en": "light", "ar": "خفيف", "es": "ligero", "zh": '轻度', "ja": '軽作業', "hi": 'हल्का', "ur": 'ہلکا', "da": 'let', "nl": 'licht', "no": 'lett', "sv": 'lätt', "pt": 'leve', "de": 'leicht'},
    "wr_moderate": {"fr": "modérée", "en": "moderate", "ar": "متوسط", "es": "moderado", "zh": '中度', "ja": '中作業', "hi": 'मध्यम', "ur": 'درمیانہ', "da": 'moderat', "nl": 'matig', "no": 'moderat', "sv": 'måttlig', "pt": 'moderado', "de": 'mäßig'},
    "wr_heavy": {"fr": "intense", "en": "heavy", "ar": "شاق", "es": "intenso", "zh": '重度', "ja": '重作業', "hi": 'भारी', "ur": 'بھاری', "da": 'hårdt', "nl": 'zwaar', "no": 'tungt', "sv": 'tung', "pt": 'intenso', "de": 'schwer'},
    "wr_very_heavy": {"fr": "très intense", "en": "very heavy", "ar": "شاق جدا", "es": "muy intenso", "zh": '极重度', "ja": '超重作業', "hi": 'बहुत भारी', "ur": 'بہت بھاری', "da": 'meget hårdt', "nl": 'zeer zwaar', "no": 'svært tungt', "sv": 'mycket tung', "pt": 'muito intenso', "de": 'sehr schwer'},
    "advanced_heat_panel_title": {
        "fr": "Évaluation avancée du stress thermique (ACGIH/ISO 7243)",
        "en": "Advanced Heat-Stress Assessment (ACGIH/ISO 7243)",
    },
    "clothing_type_label": {"fr": "Type de vêtement / EPI", "en": "Clothing / PPE type"},
    "acclimatized_label": {"fr": "Travailleur acclimaté à la chaleur", "en": "Heat-acclimatized worker"},
    "work_rest_label": {
        "fr": "Cycle travail/repos",
        "en": "Work/rest cycle",
        "ar": "دورة العمل/الراحة",
        "es": "Ciclo de trabajo/descanso",
        "zh": '工作/休息周期',
        "ja": '作業/休息サイクル',
        "hi": 'कार्य/विश्राम चक्र',
        "ur": 'کام/آرام سائیکل',
        "da": 'Arbejds-/hvilecyklus',
        "nl": 'Werk-/rustcyclus',
        "no": 'Arbeids-/hvilesyklus',
        "sv": 'Arbets-/vilocykel',
        "pt": 'Ciclo de trabalho/descanso',
        "de": 'Arbeits-/Ruhezyklus',
    },
    "work_rest_help": {
        "fr": "Catégories ACGIH TLV travail/repos utilisées pour les limites d'action "
              "liées au stress thermique",
        "en": "ACGIH TLV work/rest categories used for heat-stress action limits",
        "ar": "فئات العمل/الراحة وفق معايير ACGIH TLV المستخدمة في تحديد حدود "
              "الإجراء الخاصة بالإجهاد الحراري",
        "es": "Categorías de trabajo/descanso ACGIH TLV utilizadas para los límites "
              "de acción por estrés térmico",
              "zh": 'ACGIH TLV 工作/休息类别，用于热应激行动限值',
              "ja": '熱ストレス対応限界に使用されるACGIH TLV作業/休息区分',
              "hi": 'ताप-तनाव कार्रवाई सीमाओं के लिए उपयोग की जाने वाली ACGIH TLV कार्य/विश्राम श्रेणियां',
              "ur": 'حرارتی تناؤ کی حد کے لیے استعمال ہونے والی ACGIH TLV کام/آرام کیٹیگریز',
              "da": 'ACGIH TLV arbejds-/hvilekategorier brugt til grænseværdier for varmestress',
              "nl": 'ACGIH TLV werk-/rustcategorieën gebruikt voor actielimieten bij hittestress',
              "no": 'ACGIH TLV arbeids-/hvilekategorier brukt for tiltaksgrenser ved varmestress',
              "sv": 'ACGIH TLV arbets-/vilokategorier som används för åtgärdsgränser vid värmestress',
              "pt": 'Categorias de trabalho/descanso ACGIH TLV usadas para limites de ação por estresse térmico',
              "de": 'ACGIH-TLV-Arbeits-/Ruhekategorien für Hitzestress-Aktionsgrenzwerte',
    },

    # --- Common result sections ---
    "risk_band_label": {"fr": "Niveau de risque", "en": "Risk Band", "ar": "مستوى الخطورة", "es": "Nivel de riesgo", "zh": '风险等级', "ja": 'リスクレベル', "hi": 'जोखिम स्तर', "ur": 'خطرے کی سطح', "da": 'Risikoniveau', "nl": 'Risiconiveau', "no": 'Risikonivå', "sv": 'Risknivå', "pt": 'Nível de risco', "de": 'Risikostufe'},
    "primary_hazard_label": {
        "fr": "Danger principal",
        "en": "Primary hazard",
        "ar": "الخطر الرئيسي",
        "es": "Peligro principal",
        "zh": '主要危害',
        "ja": '主な危険',
        "hi": 'प्रमुख खतरा',
        "ur": 'بنیادی خطرہ',
        "da": 'Primær fare',
        "nl": 'Primair gevaar',
        "no": 'Primær fare',
        "sv": 'Primär fara',
        "pt": 'Perigo principal',
        "de": 'Hauptgefahr',
    },
    "drivers_label": {
        "fr": "Facteurs environnementaux",
        "en": "Environmental drivers",
        "ar": "العوامل البيئية المؤثرة",
        "es": "Factores ambientales",
        "zh": '环境影响因素',
        "ja": '環境要因',
        "hi": 'पर्यावरणीय कारक',
        "ur": 'ماحولیاتی عوامل',
        "da": 'Miljøfaktorer',
        "nl": 'Omgevingsfactoren',
        "no": 'Miljøfaktorer',
        "sv": 'Miljöfaktorer',
        "pt": 'Fatores ambientais',
        "de": 'Umweltfaktoren',
    },
    "controls_label": {
        "fr": "Mesures de contrôle recommandées",
        "en": "Recommended Controls",
        "ar": "إجراءات التحكم الموصى بها",
        "es": "Medidas de control recomendadas",
        "zh": '建议的管控措施',
        "ja": '推奨される管理策',
        "hi": 'अनुशंसित नियंत्रण उपाय',
        "ur": 'تجویز کردہ حفاظتی اقدامات',
        "da": 'Anbefalede foranstaltninger',
        "nl": 'Aanbevolen beheersmaatregelen',
        "no": 'Anbefalte tiltak',
        "sv": 'Rekommenderade åtgärder',
        "pt": 'Medidas de controle recomendadas',
        "de": 'Empfohlene Kontrollmaßnahmen',
    },
    "briefing_label": {
        "fr": "Synthèse IA",
        "en": "AI Briefing",
        "ar": "الموجز الصادر عن الذكاء الاصطناعي",
        "es": "Resumen de IA",
        "zh": 'AI简报',
        "ja": 'AIブリーフィング',
        "hi": 'एआई ब्रीफिंग',
        "ur": 'AI بریفنگ',
        "da": 'AI-briefing',
        "nl": 'AI-briefing',
        "no": 'AI-briefing',
        "sv": 'AI-briefing',
        "pt": 'Resumo de IA',
        "de": 'KI-Briefing',
    },
    "yes": {"fr": "Oui", "en": "Yes", "ar": "نعم", "es": "Sí", "zh": '是', "ja": 'はい', "hi": 'हाँ', "ur": 'ہاں', "da": 'Ja', "nl": 'Ja', "no": 'Ja', "sv": 'Ja', "pt": 'Sim', "de": 'Ja'},
    "no": {"fr": "Non", "en": "No", "ar": "لا", "es": "No", "zh": '否', "ja": 'いいえ', "hi": 'नहीं', "ur": 'نہیں', "da": 'Nej', "nl": 'Nee', "no": 'Nei', "sv": 'Nej', "pt": 'Não', "de": 'Nein'},
    "acgih_exceeded_label": {
        "fr": "Limite ACGIH dépassée",
        "en": "ACGIH limit exceeded",
        "ar": "تجاوز حد ACGIH",
        "es": "Límite ACGIH superado",
        "zh": '超过ACGIH限值',
        "ja": 'ACGIH限界値超過',
        "hi": 'ACGIH सीमा पार',
        "ur": 'ACGIH حد سے تجاوز',
        "da": 'ACGIH-grænse overskredet',
        "nl": 'ACGIH-limiet overschreden',
        "no": 'ACGIH-grense overskredet',
        "sv": 'ACGIH-gräns överskriden',
        "pt": 'Limite ACGIH excedido',
        "de": 'ACGIH-Grenzwert überschritten',
    },
    "vs_limit": {"fr": "vs limite", "en": "vs limit", "ar": "مقابل الحد", "es": "vs límite", "zh": '相对于限值', "ja": '限界値との比較', "hi": 'सीमा बनाम', "ur": 'حد کے مقابلے میں', "da": 'vs. grænse', "nl": 'vs. limiet', "no": 'vs. grense', "sv": 'vs. gräns', "pt": 'vs. limite', "de": 'vs. Grenzwert'},
    "safety_override": {
        "fr": "⚠️ DÉPASSEMENT DE SÉCURITÉ DÉCLENCHÉ",
        "en": "⚠️ SAFETY OVERRIDE TRIGGERED",
        "ar": "⚠️ تم تفعيل تجاوز السلامة الحرج",
        "es": "⚠️ ANULACIÓN DE SEGURIDAD ACTIVADA",
        "zh": '⚠️ 已触发安全超限',
        "ja": '⚠️ 安全オーバーライド発動',
        "hi": '⚠️ सुरक्षा ओवरराइड सक्रिय',
        "ur": '⚠️ حفاظتی اوور رائیڈ فعال',
        "da": '⚠️ SIKKERHEDSOVERSTYRING UDLØST',
        "nl": '⚠️ VEILIGHEIDSOVERSCHRIJDING GEACTIVEERD',
        "no": '⚠️ SIKKERHETSOVERSTYRING UTLØST',
        "sv": '⚠️ SÄKERHETSÖVERSKRIDANDE UTLÖST',
        "pt": '⚠️ ANULAÇÃO DE SEGURANÇA ATIVADA',
        "de": '⚠️ SICHERHEITSÜBERSCHREITUNG AUSGELÖST',
    },
    "run_button": {
        "fr": "Lancer l'évaluation",
        "en": "Run Risk Assessment",
        "ar": "تشغيل تقييم المخاطر",
        "es": "Ejecutar evaluación de riesgo",
        "zh": '运行风险评估',
        "ja": 'リスク評価を実行',
        "hi": 'जोखिम आकलन चलाएं',
        "ur": 'رسک اسیسمنٹ چلائیں',
        "da": 'Kør risikovurdering',
        "nl": 'Risicobeoordeling uitvoeren',
        "no": 'Kjør risikovurdering',
        "sv": 'Kör riskbedömning',
        "pt": 'Executar avaliação de risco',
        "de": 'Risikobewertung ausführen',
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
        "zh": '模块导航',
        "ja": 'モジュールナビゲーション',
        "hi": 'मॉड्यूल नेविगेशन',
        "ur": 'ماڈیول نیویگیشن',
        "da": 'Modulnavigation',
        "nl": 'Modulenavigatie',
        "no": 'Modulnavigasjon',
        "sv": 'Modulnavigering',
        "pt": 'Navegação de módulos',
        "de": 'Modulnavigation',
    },
    "nav_dashboard": {"fr": "🛡️ Tableau de bord", "en": "🛡️ Dashboard", "ar": "🛡️ لوحة التحكم", "es": "🛡️ Panel principal", "zh": '🛡️ 仪表盘', "ja": '🛡️ ダッシュボード', "hi": '🛡️ डैशबोर्ड', "ur": '🛡️ ڈیش بورڈ', "da": '🛡️ Dashboard', "nl": '🛡️ Dashboard', "no": '🛡️ Dashbord', "sv": '🛡️ Dashboard', "pt": '🛡️ Painel principal', "de": '🛡️ Dashboard'},
    "nav_solar": {
        "fr": "☀️ Fermes solaires",
        "en": "☀️ Solar Farms",
        "ar": "☀️ مزارع الطاقة الشمسية",
        "es": "☀️ Granjas Solares",
        "zh": '☀️ 太阳能电站',
        "ja": '☀️ ソーラー発電所',
        "hi": '☀️ सौर फार्म',
        "ur": '☀️ سولر فارمز',
        "da": '☀️ Solcelleanlæg',
        "nl": '☀️ Zonneparken',
        "no": '☀️ Solkraftverk',
        "sv": '☀️ Solkraftparker',
        "pt": '☀️ Fazendas Solares',
        "de": '☀️ Solarparks',
    },
    "nav_offshore": {
        "fr": "🌊 Offshore Pétrole & Gaz",
        "en": "🌊 Offshore Oil & Gas",
        "ar": "🌊 النفط والغاز البحري",
        "es": "🌊 Petróleo y Gas Offshore",
        "zh": '🌊 海上油气',
        "ja": '🌊 洋上石油・ガス',
        "hi": '🌊 अपतटीय तेल और गैस',
        "ur": '🌊 آف شور آئل اینڈ گیس',
        "da": '🌊 Offshore olie og gas',
        "nl": '🌊 Offshore olie en gas',
        "no": '🌊 Offshore olje og gass',
        "sv": '🌊 Offshore olja och gas',
        "pt": '🌊 Petróleo e Gás Offshore',
        "de": '🌊 Offshore-Öl und -Gas',
    },
    "nav_metros": {
        "fr": "🚇 Métros & Tunnels",
        "en": "🚇 Metros & Tunnels",
        "ar": "🚇 المترو والأنفاق",
        "es": "🚇 Metros y Túneles",
        "zh": '🚇 地铁与隧道',
        "ja": '🚇 地下鉄・トンネル',
        "hi": '🚇 मेट्रो और सुरंगें',
        "ur": '🚇 میٹرو اور سرنگیں',
        "da": '🚇 Metro og tunneler',
        "nl": "🚇 Metro's en tunnels",
        "no": '🚇 T-bane og tunneler',
        "sv": '🚇 Tunnelbanor och tunnlar',
        "pt": '🚇 Metrôs e Túneis',
        "de": '🚇 U-Bahnen und Tunnel',
    },
    "nav_highrise": {
        "fr": "🏙️ Tours (Gratte-ciel)",
        "en": "🏙️ High-Rise",
        "ar": "🏙️ الأبراج الشاهقة",
        "es": "🏙️ Torres (Rascacielos)",
        "zh": '🏙️ 高层建筑',
        "ja": '🏙️ 高層ビル',
        "hi": '🏙️ ऊंची इमारतें',
        "ur": '🏙️ بلند و بالا عمارات',
        "da": '🏙️ Højhuse',
        "nl": '🏙️ Hoogbouw',
        "no": '🏙️ Høyhus',
        "sv": '🏙️ Höghus',
        "pt": '🏙️ Torres (Arranha-céus)',
        "de": '🏙️ Hochhäuser',
    },
    "nav_datacenter": {
        "fr": "🖥️ Data Centers",
        "en": "🖥️ Data Centers",
        "ar": "🖥️ مراكز البيانات",
        "es": "🖥️ Centros de Datos",
        "zh": '🖥️ 数据中心',
        "ja": '🖥️ データセンター',
        "hi": '🖥️ डेटा केंद्र',
        "ur": '🖥️ ڈیٹا سینٹرز',
        "da": '🖥️ Datacentre',
        "nl": '🖥️ Datacenters',
        "no": '🖥️ Datasentre',
        "sv": '🖥️ Datacenter',
        "pt": '🖥️ Centros de Dados',
        "de": '🖥️ Rechenzentren',
    },

    # --- Dashboard (app.py) ---
    "dashboard_intro_header": {"fr": "Tableau de bord", "en": "Dashboard", "ar": "لوحة التحكم", "es": "Panel principal", "zh": '仪表盘', "ja": 'ダッシュボード', "hi": 'डैशबोर्ड', "ur": 'ڈیش بورڈ', "da": 'Dashboard', "nl": 'Dashboard', "no": 'Dashbord', "sv": 'Dashboard', "pt": 'Painel principal', "de": 'Dashboard'},
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
              "zh": 'MAKU 可对五种专业环境的现场实时风险进行评估，每种环境均由其独立透明的计算引擎驱动（WBGT、Humidex、ACGIH TLV、OEL、风力幂律剖面、Lee电弧闪光法）。请从左侧菜单选择一个模块以开始评估。',
              "ja": 'MAKUは5つの専門環境にわたり、現場のリアルタイムリスクを評価します。各環境はそれぞれ独自の透明な計算エンジン（WBGT、Humidex、ACGIH TLV、OEL、風力べき乗則プロファイル、Lee法によるアークフラッシュ計算）によって駆動されます。左側メニューからモジュールを選択して評価を実行してください。',
              "hi": 'MAKU पांच विशिष्ट वातावरणों में लाइव साइट जोखिम का आकलन करता है, प्रत्येक अपने स्वयं के पारदर्शी गणना इंजन (WBGT, Humidex, ACGIH TLV, OEL, पवन पावर-लॉ प्रोफ़ाइल, Lee आर्क-फ्लैश विधि) द्वारा संचालित है। मूल्यांकन चलाने के लिए बाएं मेनू से एक मॉड्यूल चुनें।',
              "ur": 'MAKU پانچ خصوصی ماحول میں لائیو سائٹ رسک کا جائزہ لیتا ہے، ہر ایک اپنے شفاف حساب کے انجن (WBGT، Humidex، ACGIH TLV، OEL، ونڈ پاور-لاء پروفائل، Lee آرک فلیش طریقہ) سے چلتا ہے۔ تشخیص چلانے کے لیے بائیں مینو سے ایک ماڈیول منتخب کریں۔',
              "da": 'MAKU vurderer live-risiko på tværs af fem specialiserede miljøer, hver drevet af sin egen gennemsigtige beregningsmotor (WBGT, Humidex, ACGIH TLV, OEL, vindeffektlovsprofil, Lee-metoden for lysbue). Vælg et modul i venstremenuen for at køre en vurdering.',
              "nl": "MAKU beoordeelt live sitegerelateerde risico's binnen vijf gespecialiseerde omgevingen, elk aangedreven door zijn eigen transparante rekenmodule (WBGT, Humidex, ACGIH TLV, OEL, windmachtswetprofiel, Lee-methode voor vlambogen). Kies een module in het linkermenu om een beoordeling uit te voeren.",
              "no": 'MAKU vurderer sanntidsrisiko på tvers av fem spesialiserte miljøer, hver drevet av sin egen transparente beregningsmotor (WBGT, Humidex, ACGIH TLV, OEL, vindeffektlovprofil, Lee-metoden for lysbue). Velg en modul fra venstremenyen for å kjøre en vurdering.',
              "sv": 'MAKU bedömer risker på plats i realtid inom fem specialiserade miljöer, var och en driven av sin egen transparenta beräkningsmotor (WBGT, Humidex, ACGIH TLV, OEL, vindeffektlagsprofil, Lee-metoden för ljusbåge). Välj en modul i vänstermenyn för att köra en bedömning.',
              "pt": 'O MAKU avalia o risco do local em tempo real em cinco ambientes especializados, cada um baseado em seu próprio mecanismo de cálculo transparente (WBGT, Humidex, ACGIH TLV, OEL, perfil de lei de potência do vento, método Lee para arco elétrico). Escolha um módulo no menu à esquerda para iniciar uma avaliação.',
              "de": 'MAKU bewertet Live-Standortrisiken in fünf spezialisierten Umgebungen, die jeweils von einer eigenen transparenten Berechnungs-Engine angetrieben werden (WBGT, Humidex, ACGIH TLV, OEL, Windkraft-Potenzgesetzprofil, Lee-Methode für Lichtbögen). Wählen Sie im linken Menü ein Modul aus, um eine Bewertung durchzuführen.',
    },
    "dashboard_module_col_header": {
        "fr": "Modules disponibles",
        "en": "Available modules",
        "ar": "الوحدات المتاحة",
        "es": "Módulos disponibles",
        "zh": '可用模块',
        "ja": '利用可能なモジュール',
        "hi": 'उपलब्ध मॉड्यूल',
        "ur": 'دستیاب ماڈیولز',
        "da": 'Tilgængelige moduler',
        "nl": 'Beschikbare modules',
        "no": 'Tilgjengelige moduler',
        "sv": 'Tillgängliga moduler',
        "pt": 'Módulos disponíveis',
        "de": 'Verfügbare Module',
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
              "zh": 'MAKU——基于规则的风险引擎（5种环境），附带可选AI叙述层。',
              "ja": 'MAKU - ルールベースのリスクエンジン（5環境）、オプションのAIナラティブ層付き。',
              "hi": 'MAKU - नियम-आधारित जोखिम इंजन (5 वातावरण), वैकल्पिक एआई नैरेटिव लेयर के साथ।',
              "ur": 'MAKU - قاعدہ پر مبنی رسک انجن (5 ماحول)، اختیاری AI بیانیہ پرت کے ساتھ۔',
              "da": 'MAKU - regelbaseret risikomotor (5 miljøer) med valgfrit AI-fortællingslag.',
              "nl": 'MAKU - regelgebaseerde risico-engine (5 omgevingen) met optionele AI-verhaallaag.',
              "no": 'MAKU - regelbasert risikomotor (5 miljøer) med valgfritt AI-fortellerlag.',
              "sv": 'MAKU - regelbaserad riskmotor (5 miljöer) med valfritt AI-berättelselager.',
              "pt": 'MAKU - motor de risco baseado em regras (5 ambientes) com camada narrativa de IA opcional.',
              "de": 'MAKU - regelbasierte Risiko-Engine (5 Umgebungen) mit optionaler KI-Erzählebene.',
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
              "zh": '🚨 **紧急警报：** 支架机械组装存在即时急性中暑风险。',
              "ja": '🚨 **重大警報：** トラッカー機械組立作業に急性熱中症の即時リスクがあります。',
              "hi": '🚨 **गंभीर अलर्ट:** ट्रैकर मैकेनिकल असेंबली के लिए तत्काल तीव्र हीट-स्ट्रोक जोखिम।',
              "ur": '🚨 **شدید انتباہ:** ٹریکر مکینیکل اسمبلی کے لیے فوری شدید ہیٹ اسٹروک کا خطرہ۔',
              "da": '🚨 **KRITISK ALARM:** Umiddelbar akut risiko for hedeslag ved mekanisk montering af trackere.',
              "nl": '🚨 **KRITIEKE WAARSCHUWING:** Onmiddellijk acuut risico op hitteberoerte bij mechanische montage van trackers.',
              "no": '🚨 **KRITISK VARSEL:** Umiddelbar akutt risiko for hetslag ved mekanisk montering av trackere.',
              "sv": '🚨 **KRITISKT LARM:** Omedelbar akut risk för värmeslag vid mekanisk montering av trackers.',
              "pt": '🚨 **ALERTA CRÍTICO:** Risco imediato de golpe de calor agudo na montagem mecânica dos seguidores.',
              "de": '🚨 **KRITISCHER ALARM:** Unmittelbares akutes Hitzschlagrisiko bei der mechanischen Montage der Tracker.',
    },
    "solar_high_alert": {
        "fr": "⚠️ **ATTENTION :** Risque élevé de stress thermique. Rotation obligatoire.",
        "en": "⚠️ **WARNING:** High heat-stress risk. Mandatory rotation required.",
        "ar": "⚠️ **تحذير:** خطر مرتفع للإجهاد الحراري. التناوب إلزامي.",
        "es": "⚠️ **ADVERTENCIA:** Alto riesgo de estrés térmico. Rotación obligatoria.",
        "zh": '⚠️ **警告：** 高热应激风险。必须强制轮岗。',
        "ja": '⚠️ **警告：** 高い熱ストレスリスク。必須の交代が必要です。',
        "hi": '⚠️ **चेतावनी:** उच्च ताप-तनाव जोखिम। अनिवार्य रोटेशन आवश्यक।',
        "ur": '⚠️ **انتباہ:** زیادہ حرارتی تناؤ کا خطرہ۔ لازمی گردش درکار ہے۔',
        "da": '⚠️ **ADVARSEL:** Høj risiko for varmestress. Obligatorisk rotation påkrævet.',
        "nl": '⚠️ **WAARSCHUWING:** Hoog risico op hittestress. Verplichte rotatie vereist.',
        "no": '⚠️ **ADVARSEL:** Høy risiko for varmestress. Obligatorisk rotasjon kreves.',
        "sv": '⚠️ **VARNING:** Hög risk för värmestress. Obligatorisk rotation krävs.',
        "pt": '⚠️ **AVISO:** Alto risco de estresse térmico. Rotação obrigatória necessária.',
        "de": '⚠️ **WARNUNG:** Hohes Hitzestress-Risiko. Verpflichtende Rotation erforderlich.',
    },
    "solar_standard_ok": {
        "fr": "✅ Conditions opérationnelles standards. Assurez l'hydratation continue "
              "des techniciens.",
        "en": "✅ Standard operating conditions. Ensure continuous technician hydration.",
        "ar": "✅ ظروف تشغيل اعتيادية. تأكد من استمرار ترطيب الفنيين.",
        "es": "✅ Condiciones operativas estándar. Asegure la hidratación continua "
              "de los técnicos.",
              "zh": '✅ 标准运行条件。请确保技术人员持续补水。',
              "ja": '✅ 標準運転条件です。技術者の継続的な水分補給を徹底してください。',
              "hi": '✅ मानक संचालन स्थितियां। तकनीशियनों के निरंतर जलयोजन को सुनिश्चित करें。',
              "ur": '✅ معیاری آپریٹنگ حالات۔ ٹیکنیشنز کی مسلسل ہائیڈریشن کو یقینی بنائیں۔',
              "da": '✅ Standard driftsforhold. Sørg for løbende hydrering af teknikerne.',
              "nl": '✅ Standaard bedrijfsomstandigheden. Zorg voor continue hydratatie van technici.',
              "no": '✅ Standard driftsforhold. Sørg for kontinuerlig hydrering av teknikere.',
              "sv": '✅ Standarddriftförhållanden. Säkerställ kontinuerligt vätskeintag för tekniker.',
              "pt": '✅ Condições operacionais padrão. Garanta a hidratação contínua dos técnicos.',
              "de": '✅ Standardbetriebsbedingungen. Kontinuierliche Flüssigkeitszufuhr der Techniker sicherstellen.',
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
              "zh": '⚠️ **警告：** 海上热应激升高。加强焊接/管道安装班组轮换并监测Humidex趋势。',
              "ja": '⚠️ **警告：** 海上熱ストレスが上昇しています。溶接・配管班のローテーションを強化し、Humidexの傾向を監視してください。',
              "hi": '⚠️ **चेतावनी:** समुद्री ताप-तनाव बढ़ा हुआ है। वेल्डिंग/पाइप-फिटिंग दल के रोटेशन को सख्त करें और Humidex प्रवृत्ति की निगरानी करें।',
              "ur": '⚠️ **انتباہ:** سمندری حرارتی تناؤ بلند ہے۔ ویلڈنگ/پائپ فٹنگ عملے کی گردش سخت کریں اور Humidex رجحان کی نگرانی کریں۔',
              "da": '⚠️ **ADVARSEL:** Forhøjet marint varmestress. Stram rotationen for svejse-/rørmonteringshold, og overvåg Humidex-tendensen.',
              "nl": '⚠️ **WAARSCHUWING:** Verhoogde maritieme hittestress. Verscherp de rotatie van las-/leidingmontageploegen en monitor de Humidex-trend.',
              "no": '⚠️ **ADVARSEL:** Forhøyet marint varmestress. Stram rotasjonen for sveise-/rørleggerlag og overvåk Humidex-trenden.',
              "sv": '⚠️ **VARNING:** Förhöjd marin värmestress. Skärp rotationen för svets-/rörmontageteam och övervaka Humidex-trenden.',
              "pt": '⚠️ **AVISO:** Estresse térmico marinho elevado. Reforce o rodízio das equipes de solda/tubulação e monitore a tendência do Humidex.',
              "de": '⚠️ **WARNUNG:** Erhöhter mariner Hitzestress. Rotation der Schweiß-/Rohrmontageteams verschärfen und Humidex-Trend überwachen.',
    },
    "offshore_standard_ok": {
        "fr": "✅ Conditions opérationnelles marines normales. Maintenir le protocole "
              "HSE standard.",
        "en": "✅ Standard marine operating conditions. Maintain standard HSE protocol.",
        "ar": "✅ ظروف تشغيل بحرية اعتيادية. حافظ على بروتوكول السلامة والصحة "
              "المهنية القياسي.",
        "es": "✅ Condiciones operativas marinas normales. Mantenga el protocolo "
              "HSE estándar.",
              "zh": '✅ 标准海上运行条件。请维持标准HSE规程。',
              "ja": '✅ 標準的な海上運転条件です。標準のHSEプロトコルを維持してください。',
              "hi": '✅ मानक समुद्री संचालन स्थितियां। मानक HSE प्रोटोकॉल बनाए रखें।',
              "ur": '✅ معیاری میرین آپریٹنگ حالات۔ معیاری HSE پروٹوکول برقرار رکھیں۔',
              "da": '✅ Standard marine driftsforhold. Oprethold standard HSE-protokol.',
              "nl": '✅ Standaard maritieme bedrijfsomstandigheden. Handhaaf het standaard HSE-protocol.',
              "no": '✅ Standard marine driftsforhold. Oppretthold standard HMS-protokoll.',
              "sv": '✅ Standardmässiga marina driftförhållanden. Upprätthåll standard HSE-protokoll.',
              "pt": '✅ Condições operacionais marítimas padrão. Mantenha o protocolo HSE padrão.',
              "de": '✅ Marine Standardbetriebsbedingungen. Standard-HSE-Protokoll beibehalten.',
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
              "zh": '🚨 **严重安全超限：** 立即停止机电高压布线作业。撤离开挖面并在重新测试前重新核实通风情况。',
              "ja": '🚨 **重大な安全オーバーライド：** MEP高圧配線作業を直ちに中止してください。掘削面から退避し、再テスト前に換気を再確認してください。',
              "hi": '🚨 **गंभीर सुरक्षा ओवरराइड:** MEP उच्च-वोल्टेज केबलिंग कार्य तुरंत रोकें। उत्खनन मोर्चे को खाली करें और पुनः परीक्षण से पहले वेंटिलेशन की पुनः पुष्टि करें।',
              "ur": '🚨 **شدید حفاظتی اوور رائیڈ:** MEP ہائی وولٹیج کیبلنگ کا کام فوری طور پر روکیں۔ کھدائی کے محاذ کو خالی کریں اور دوبارہ ٹیسٹ سے پہلے وینٹیلیشن کی دوبارہ تصدیق کریں۔',
              "da": '🚨 **KRITISK SIKKERHEDSOVERSTYRING:** Øjeblikkeligt stop for MEP-højspændingskabelarbejde. Evakuer udgravningsfronten, og genbekræft ventilationen før ny test.',
              "nl": '🚨 **KRITIEKE VEILIGHEIDSOVERSCHRIJDING:** Onmiddellijke stopzetting van MEP-hoogspanningsbekabelingswerk. Evacueer het uitgravingsfront en controleer de ventilatie opnieuw vóór hertesten.',
              "no": '🚨 **KRITISK SIKKERHETSOVERSTYRING:** Umiddelbar stans av MEP høyspenningskabling. Evakuer utgravingsfronten og bekreft ventilasjonen på nytt før ny testing.',
              "sv": '🚨 **KRITISKT SÄKERHETSÖVERSKRIDANDE:** Omedelbart stopp av MEP-högspänningskablage. Utrym schaktfronten och verifiera ventilationen igen innan ny testning.',
              "pt": '🚨 **ANULAÇÃO DE SEGURANÇA CRÍTICA:** Parada imediata do cabeamento de alta tensão MEP. Evacue a frente de escavação e reverifique a ventilação antes de novo teste.',
              "de": '🚨 **KRITISCHE SICHERHEITSÜBERSCHREITUNG:** Sofortiger Stopp der MEP-Hochspannungsverkabelung. Evakuieren Sie die Ausgrabungsfront und überprüfen Sie die Belüftung erneut vor dem nächsten Test.',
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
              "zh": '⚠️ **警告：** 热应激和/或空气质量接近OEL限值。加强班组轮换并密切关注传感器趋势。',
              "ja": '⚠️ **警告：** 熱ストレスおよび/または空気質がOEL限界値に近づいています。班のローテーションを強化し、センサーの傾向を注視してください。',
              "hi": '⚠️ **चेतावनी:** ताप-तनाव और/या वायु गुणवत्ता OEL सीमाओं के करीब पहुंच रही है। दल रोटेशन को सख्त करें और सेंसर प्रवृत्ति पर बारीकी से नजर रखें।',
              "ur": '⚠️ **انتباہ:** حرارتی تناؤ اور/یا ہوا کا معیار OEL حدود کے قریب پہنچ رہا ہے۔ عملے کی گردش سخت کریں اور سینسر رجحان پر گہری نظر رکھیں۔',
              "da": '⚠️ **ADVARSEL:** Varmestress og/eller luftkvalitet nærmer sig OEL-grænser. Stram holdrotationen, og hold nøje øje med sensortendensen.',
              "nl": '⚠️ **WAARSCHUWING:** Hittestress en/of luchtkwaliteit nadert OEL-limieten. Verscherp de ploegenrotatie en houd de sensortrend nauwlettend in de gaten.',
              "no": '⚠️ **ADVARSEL:** Varmestress og/eller luftkvalitet nærmer seg OEL-grenser. Stram lagrotasjonen og følg nøye med på sensortrenden.',
              "sv": '⚠️ **VARNING:** Värmestress och/eller luftkvalitet närmar sig OEL-gränser. Skärp teamrotationen och bevaka sensortrenden noga.',
              "pt": '⚠️ **AVISO:** Estresse térmico e/ou qualidade do ar se aproximando dos limites OEL. Reforce o rodízio da equipe e monitore de perto a tendência dos sensores.',
              "de": '⚠️ **WARNUNG:** Hitzestress und/oder Luftqualität nähern sich den OEL-Grenzwerten. Teamrotation verschärfen und Sensortrend genau beobachten.',
    },
    "underground_standard_ok": {
        "fr": "✅ Conditions souterraines standards. Maintenir la cadence de surveillance "
              "OEL et thermique.",
        "en": "✅ Standard underground conditions. Maintain the OEL and heat monitoring cadence.",
        "ar": "✅ ظروف جوفية اعتيادية. حافظ على وتيرة مراقبة حدود OEL والحرارة.",
        "es": "✅ Condiciones subterráneas estándar. Mantenga la cadencia de "
              "monitoreo de OEL y calor.",
              "zh": '✅ 标准地下条件。请维持OEL与热监测节奏。',
              "ja": '✅ 標準的な地下条件です。OELおよび熱の監視頻度を維持してください。',
              "hi": '✅ मानक भूमिगत स्थितियां। OEL और ताप निगरानी की गति बनाए रखें।',
              "ur": '✅ معیاری زیرزمین حالات۔ OEL اور حرارت کی نگرانی کی رفتار برقرار رکھیں۔',
              "da": '✅ Standard underjordiske forhold. Oprethold OEL- og varmeovervågningstakten.',
              "nl": '✅ Standaard ondergrondse omstandigheden. Handhaaf het OEL- en warmtebewakingsritme.',
              "no": '✅ Standard undergrunnsforhold. Oppretthold OEL- og varmeovervåkingstakten.',
              "sv": '✅ Standardförhållanden under jord. Upprätthåll OEL- och värmeövervakningstakten.',
              "pt": '✅ Condições subterrâneas padrão. Mantenha a cadência de monitoramento de OEL e calor.',
              "de": '✅ Standardbedingungen im Untergrund. Überwachungstakt für OEL und Wärme beibehalten.',
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
              "zh": '🚨 **严重安全超限：** 立即暂停所有起重作业及高空幕墙/外墙作业。恢复前请重新检查防坠落系留点。',
              "ja": '🚨 **重大な安全オーバーライド：** すべてのクレーン作業および高所でのファサード/カーテンウォール作業を直ちに中断してください。再開前に墜落防止用の固定点を再確認してください。',
              "hi": '🚨 **गंभीर सुरक्षा ओवरराइड:** सभी क्रेन लिफ्ट और ऊंचाई पर फसाड/कर्टन-वॉल कार्य तुरंत निलंबित करें। फिर से शुरू करने से पहले फॉल-अरेस्ट टाई-ऑफ पॉइंट्स की पुनः जांच करें।',
              "ur": '🚨 **شدید حفاظتی اوور رائیڈ:** تمام کرین لفٹس اور بلندی پر فیساڈ/کرٹن وال کام فوری طور پر معطل کریں۔ دوبارہ شروع کرنے سے پہلے فال ارسٹ ٹائی آف پوائنٹس کی دوبارہ جانچ کریں۔',
              "da": '🚨 **KRITISK SIKKERHEDSOVERSTYRING:** Øjeblikkelig suspendering af alle kranløft og facade-/glasfacadearbejde i højden. Genkontroller faldsikringspunkter, før arbejdet genoptages.',
              "nl": '🚨 **KRITIEKE VEILIGHEIDSOVERSCHRIJDING:** Onmiddellijke opschorting van alle kraanhijsingen en gevel-/vliesgevelwerk op hoogte. Controleer valbeveiligingspunten opnieuw voordat het werk wordt hervat.',
              "no": '🚨 **KRITISK SIKKERHETSOVERSTYRING:** Umiddelbar stans av alle kranløft og fasade-/glassfasadearbeid i høyden. Sjekk festepunkter for fallsikring på nytt før gjenopptakelse.',
              "sv": '🚨 **KRITISKT SÄKERHETSÖVERSKRIDANDE:** Omedelbart stopp av alla kranlyft och fasad-/glasfasadarbete på höjd. Kontrollera fallskyddsförankringar på nytt innan arbetet återupptas.',
              "pt": '🚨 **ANULAÇÃO DE SEGURANÇA CRÍTICA:** Suspensão imediata de todos os içamentos com guindaste e trabalhos em fachada/parede cortina em altura. Reverifique os pontos de ancoragem anticaída antes de retomar.',
              "de": '🚨 **KRITISCHE SICHERHEITSÜBERSCHREITUNG:** Sofortige Aussetzung aller Kranhübe und Fassaden-/Vorhangfassadenarbeiten in der Höhe. Absturzsicherungs-Anschlagpunkte vor Wiederaufnahme erneut prüfen.',
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
              "zh": '⚠️ **警告：** 此楼层风切变较大。请通知起重机操作员并推迟非关键吊装作业。',
              "ja": '⚠️ **警告：** この階でウィンドシアが強くなっています。クレーンオペレーターに通知し、緊急性の低い吊り上げ作業は延期してください。',
              "hi": '⚠️ **चेतावनी:** इस मंजिल स्तर पर उच्च पवन कतरनी है। क्रेन ऑपरेटर को सूचित करें और गैर-महत्वपूर्ण लिफ्ट को स्थगित करें।',
              "ur": '⚠️ **انتباہ:** اس منزل کی سطح پر تیز ہوا کا شیئر ہے۔ کرین آپریٹر کو مطلع کریں اور غیر اہم لفٹس کو مؤخر کریں۔',
              "da": '⚠️ **ADVARSEL:** Høj vindforskydning på denne etage. Underret krananføreren, og udsæt ikke-kritiske løft.',
              "nl": '⚠️ **WAARSCHUWING:** Hoge windschering op dit verdiepingsniveau. Informeer de kraanmachinist en stel niet-kritieke hijsingen uit.',
              "no": '⚠️ **ADVARSEL:** Høy vindskjær på dette etasjenivået. Varsle kranføreren og utsett ikke-kritiske løft.',
              "sv": '⚠️ **VARNING:** Hög vindskjuvning på denna våningsnivå. Meddela kranföraren och skjut upp icke-kritiska lyft.',
              "pt": '⚠️ **AVISO:** Alto cisalhamento de vento neste nível do pavimento. Notifique o operador do guindaste e adie içamentos não críticos.',
              "de": '⚠️ **WARNUNG:** Hohe Windscherung auf dieser Etage. Kranführer benachrichtigen und unkritische Hübe verschieben.',
    },
    "highrise_standard_ok": {
        "fr": "✅ Conditions de vent standards en hauteur. Maintenir la surveillance "
              "anémométrique à chaque poste.",
        "en": "✅ Standard wind conditions at height. Maintain anemometer monitoring each shift.",
        "ar": "✅ ظروف رياح اعتيادية على الارتفاع. حافظ على مراقبة جهاز قياس الرياح "
              "في كل نوبة عمل.",
        "es": "✅ Condiciones de viento estándar en altura. Mantenga el monitoreo "
              "del anemómetro en cada turno.",
              "zh": '✅ 高空风况标准。请每班维持风速计监测。',
              "ja": '✅ 高所での風況は標準的です。各シフトで風速計の監視を継続してください。',
              "hi": '✅ ऊंचाई पर मानक पवन स्थितियां। प्रत्येक शिफ्ट में एनीमोमीटर निगरानी बनाए रखें।',
              "ur": '✅ بلندی پر معیاری ہوا کی صورتحال۔ ہر شفٹ میں اینیمومیٹر نگرانی برقرار رکھیں۔',
              "da": '✅ Standard vindforhold i højden. Oprethold anemometerovervågning i hver vagt.',
              "nl": '✅ Standaard windomstandigheden op hoogte. Handhaaf anemometerbewaking elke dienst.',
              "no": '✅ Standard vindforhold i høyden. Oppretthold anemometerovervåking hvert skift.',
              "sv": '✅ Standardvindförhållanden på höjd. Upprätthåll anemometerövervakning varje skift.',
              "pt": '✅ Condições de vento padrão em altura. Mantenha o monitoramento do anemômetro em cada turno.',
              "de": '✅ Standard-Windbedingungen in der Höhe. Anemometerüberwachung in jeder Schicht beibehalten.',
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
              "zh": '🚨 **严重安全超限：** 立即停止该区域的电气/机械/消防调试作业。作业前须断电，恢复前须重新检查条件。',
              "ja": '🚨 **重大な安全オーバーライド：** このゾーンでの電気/機械/消火設備のコミッショニング作業を直ちに中止してください。作業前に停電し、再開前に状況を再確認してください。',
              "hi": '🚨 **गंभीर सुरक्षा ओवरराइड:** इस क्षेत्र में विद्युत/यांत्रिक/अग्नि-दमन कमीशनिंग कार्य तुरंत रोकें। किसी भी कार्य से पहले डी-एनर्जाइज़ करें और फिर से शुरू करने से पहले स्थितियों की पुनः जांच करें।',
              "ur": '🚨 **شدید حفاظتی اوور رائیڈ:** اس زون میں الیکٹریکل/مکینیکل/فائر سپریشن کمیشننگ کام فوری روکیں۔ کسی بھی کام سے پہلے ڈی انرجائز کریں اور دوبارہ شروع کرنے سے پہلے حالات کی دوبارہ جانچ کریں۔',
              "da": '🚨 **KRITISK SIKKERHEDSOVERSTYRING:** Øjeblikkeligt stop af el-/mekanisk/brandslukningsidriftsættelsesarbejde i denne zone. Afbryd strømmen inden arbejde, og genkontroller forholdene før genoptagelse.',
              "nl": '🚨 **KRITIEKE VEILIGHEIDSOVERSCHRIJDING:** Onmiddellijke stopzetting van elektrisch/mechanisch/brandblussing-inbedrijfstellingswerk in deze zone. Schakel spanning uit vóór elk werk en controleer de omstandigheden opnieuw voordat het werk wordt hervat.',
              "no": '🚨 **KRITISK SIKKERHETSOVERSTYRING:** Umiddelbar stans av elektrisk/mekanisk/brannslukningsigangkjøringsarbeid i denne sonen. Koble fra strøm før arbeid og sjekk forholdene på nytt før gjenopptakelse.',
              "sv": '🚨 **KRITISKT SÄKERHETSÖVERSKRIDANDE:** Omedelbart stopp av elektriskt/mekaniskt/brandsläckningsidrifttagningsarbete i denna zon. Bryt strömmen före allt arbete och kontrollera förhållandena på nytt innan arbetet återupptas.',
              "pt": '🚨 **ANULAÇÃO DE SEGURANÇA CRÍTICA:** Parada imediata do trabalho de comissionamento elétrico/mecânico/supressão de incêndio nesta zona. Desenergize antes de qualquer trabalho e reverifique as condições antes de retomar.',
              "de": '🚨 **KRITISCHE SICHERHEITSÜBERSCHREITUNG:** Sofortiger Stopp der elektrischen/mechanischen/Brandbekämpfungs-Inbetriebnahmearbeiten in dieser Zone. Vor jeder Arbeit spannungsfrei schalten und Bedingungen vor Wiederaufnahme erneut prüfen.',
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
              "zh": '⚠️ **警告：** 电弧闪光风险或冷/热通道热风险升高。请确认PPE等级并加强调试班组轮换。',
              "ja": '⚠️ **警告：** アークフラッシュまたはホット/コールドアイルの熱リスクが上昇しています。PPE等級を確認し、コミッショニング班のローテーションを強化してください。',
              "hi": '⚠️ **चेतावनी:** आर्क-फ्लैश या हॉट/कोल्ड-आइल थर्मल जोखिम बढ़ा हुआ है। PPE रेटिंग की पुष्टि करें और कमीशनिंग दल रोटेशन को सख्त करें।',
              "ur": '⚠️ **انتباہ:** آرک فلیش یا ہاٹ/کولڈ ایزل حرارتی خطرہ بلند ہے۔ PPE ریٹنگ کی تصدیق کریں اور کمیشننگ عملے کی گردش سخت کریں۔',
              "da": '⚠️ **ADVARSEL:** Forhøjet lysbue- eller varm-/koldgangs termisk risiko. Bekræft PPE-klassificering, og stram idriftsættelsesholdrotationen.',
              "nl": '⚠️ **WAARSCHUWING:** Verhoogd vlambooggevaar of thermisch risico in warme/koude gang. Bevestig de PBM-classificatie en verscherp de rotatie van het inbedrijfstellingsteam.',
              "no": '⚠️ **ADVARSEL:** Forhøyet lysbue- eller varm-/kaldgang termisk risiko. Bekreft PVU-klassifisering og stram igangkjøringslagrotasjonen.',
              "sv": '⚠️ **VARNING:** Förhöjd ljusbåge- eller termisk risk i varm-/kallgång. Bekräfta PPE-klassificering och skärp idrifttagningsteamets rotation.',
              "pt": '⚠️ **AVISO:** Risco elevado de arco elétrico ou térmico no corredor quente/frio. Confirme a classificação de EPI e reforce o rodízio da equipe de comissionamento.',
              "de": '⚠️ **WARNUNG:** Erhöhtes Lichtbogen- oder thermisches Risiko im Warm-/Kaltgang. PSA-Einstufung bestätigen und Rotation des Inbetriebnahmeteams verschärfen.',
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
              "zh": '✅ 标准调试条件。请维持热、电弧闪光及受限空间监测。',
              "ja": '✅ 標準的なコミッショニング条件です。熱、アークフラッシュ、閉鎖空間の監視を維持してください。',
              "hi": '✅ मानक कमीशनिंग स्थितियां। थर्मल, आर्क-फ्लैश और सीमित-स्थान निगरानी बनाए रखें।',
              "ur": '✅ معیاری کمیشننگ حالات۔ حرارتی، آرک فلیش، اور محدود جگہ کی نگرانی برقرار رکھیں۔',
              "da": '✅ Standard idriftsættelsesforhold. Oprethold overvågning af varme, lysbue og lukkede rum.',
              "nl": '✅ Standaard inbedrijfstellingsomstandigheden. Handhaaf thermische, vlamboog- en besloten-ruimtebewaking.',
              "no": '✅ Standard igangkjøringsforhold. Oppretthold overvåking av varme, lysbue og trange rom.',
              "sv": '✅ Standardförhållanden vid idrifttagning. Upprätthåll övervakning av värme, ljusbåge och slutna utrymmen.',
              "pt": '✅ Condições de comissionamento padrão. Mantenha o monitoramento térmico, de arco elétrico e de espaço confinado.',
              "de": '✅ Standard-Inbetriebnahmebedingungen. Überwachung von Wärme, Lichtbogen und engen Räumen beibehalten.',
    },

    # --- Navigation: 3 new modules ---
    "nav_windenergy": {"fr": "💨 Énergie Éolienne", "en": "💨 Wind Energy", "ar": "💨 طاقة الرياح", "es": "💨 Energía Eólica", "zh": '💨 风能', "ja": '💨 風力エネルギー', "hi": '💨 पवन ऊर्जा', "ur": '💨 ونڈ انرجی', "da": '💨 Vindenergi', "nl": '💨 Windenergie', "no": '💨 Vindenergi', "sv": '💨 Vindkraft', "pt": '💨 Energia Eólica', "de": '💨 Windenergie'},
    "nav_mining": {"fr": "⛏️ Mines & Carrières", "en": "⛏️ Mining & Quarrying", "ar": "⛏️ التعدين والمحاجر", "es": "⛏️ Minería y Canteras", "zh": '⛏️ 采矿与采石', "ja": '⛏️ 採鉱・採石', "hi": '⛏️ खनन और खदान', "ur": '⛏️ کان کنی اور کوارٹزنگ', "da": '⛏️ Minedrift og stenbrud', "nl": '⛏️ Mijnbouw en steengroeven', "no": '⛏️ Gruvedrift og steinbrudd', "sv": '⛏️ Gruvdrift och stenbrott', "pt": '⛏️ Mineração e Pedreiras', "de": '⛏️ Bergbau und Steinbrüche'},
    "nav_marineport": {"fr": "⚓ Marine & Ports", "en": "⚓ Marine & Port", "ar": "⚓ الأعمال البحرية والموانئ", "es": "⚓ Marino y Portuario", "zh": '⚓ 海事与港口', "ja": '⚓ 海事・港湾', "hi": '⚓ समुद्री और बंदरगाह', "ur": '⚓ میرین اینڈ پورٹ', "da": '⚓ Marine og havn', "nl": '⚓ Maritiem en haven', "no": '⚓ Marine og havn', "sv": '⚓ Marin och hamn', "pt": '⚓ Marítimo e Portuário', "de": '⚓ Marine und Hafen'},

    # --- Module 6: Wind Energy ---
    "windenergy_header": {
        "fr": "💨 Énergie éolienne - Onshore/Offshore",
        "en": "💨 Wind Energy - Onshore/Offshore",
        "ar": "💨 طاقة الرياح - البرية والبحرية",
        "es": "💨 Energía Eólica - Terrestre/Marina",
    },
    "windenergy_caption": {
        "fr": "Seuils de vent pour le travail en hauteur, règle de la foudre 30-30, et "
              "seuils d'état de mer pour le transfert d'équipage par navire (offshore)",
        "en": "Working-at-height wind thresholds, the 30-30 lightning rule, and sea-state "
              "gating for crew-transfer-vessel personnel transfer (offshore)",
        "ar": "عتبات الرياح للعمل في المرتفعات، قاعدة البرق 30-30، وعتبات حالة البحر "
              "لنقل الطاقم عبر سفن النقل (البحرية)",
        "es": "Umbrales de viento para trabajo en altura, regla del rayo 30-30, y "
              "umbrales de estado del mar para el transbordo de tripulación (offshore)",
    },
    "windenergy_env_data_header": {
        "fr": "Données environnementales", "en": "Environmental data",
        "ar": "البيانات البيئية", "es": "Datos ambientales",
    },
    "windenergy_wind_label": {
        "fr": "Vitesse du vent au moyeu (m/s)", "en": "Hub-height wind speed (m/s)",
        "ar": "سرعة الرياح عند محور التوربين (م/ث)", "es": "Velocidad del viento en el buje (m/s)",
    },
    "windenergy_offshore_toggle": {
        "fr": "Site offshore (active le seuil de transfert par navire)",
        "en": "Offshore site (enables crew-transfer-vessel gating)",
        "ar": "موقع بحري (يفعّل عتبة نقل الطاقم عبر السفن)",
        "es": "Sitio offshore (activa el umbral de transbordo por embarcación)",
    },
    "windenergy_wave_label": {
        "fr": "Hauteur significative des vagues (m)", "en": "Significant wave height (m)",
        "ar": "الارتفاع المعنوي للأمواج (م)", "es": "Altura significativa de las olas (m)",
    },
    "windenergy_lightning_toggle": {
        "fr": "Activité orageuse observée", "en": "Thunderstorm activity observed",
        "ar": "تم رصد نشاط عاصف رعدي", "es": "Actividad de tormenta eléctrica observada",
    },
    "windenergy_lightning_label": {
        "fr": "Intervalle éclair-tonnerre (secondes)", "en": "Flash-to-bang interval (seconds)",
        "ar": "الفاصل الزمني بين البرق والرعد (ثوانٍ)", "es": "Intervalo relámpago-trueno (segundos)",
    },
    "ctv_status_label": {
        "fr": "Statut transfert par navire", "en": "CTV transfer status",
        "ar": "حالة نقل السفن", "es": "Estado de transbordo (CTV)",
    },
    "lightning_status_label": {
        "fr": "Statut foudre", "en": "Lightning status",
        "ar": "حالة البرق", "es": "Estado de rayos",
    },
    "windenergy_critical_alert": {
        "fr": "🚨 **DÉPASSEMENT DE SÉCURITÉ CRITIQUE :** Suspension immédiate de tout accès "
              "pale/nacelle et opérations de levage. Vérifiez la règle 30-30 et l'état de mer "
              "avant toute reprise.",
        "en": "🚨 **CRITICAL SAFETY OVERRIDE:** Immediate suspension of all blade/nacelle "
              "access and lifting operations. Recheck the 30-30 rule and sea state before resuming.",
        "ar": "🚨 **تجاوز سلامة حرج:** إيقاف فوري لجميع أعمال الوصول إلى الشفرات/العنبر "
              "وعمليات الرفع. أعد التحقق من قاعدة 30-30 وحالة البحر قبل الاستئناف.",
        "es": "🚨 **ANULACIÓN DE SEGURIDAD CRÍTICA:** Suspensión inmediata de todo acceso a "
              "pala/góndola y operaciones de izado. Reverifique la regla 30-30 y el estado "
              "del mar antes de reanudar.",
              "zh": '🚨 **严重安全超限：** 立即暂停所有叶片/机舱进入及吊装作业。恢复前请重新核查30-30规则及海况。',
              "ja": '🚨 **重大な安全オーバーライド：** ブレード/ナセルへのアクセスおよび吊り上げ作業をすべて直ちに中断してください。再開前に30-30ルールと海況を再確認してください。',
              "hi": '🚨 **गंभीर सुरक्षा ओवरराइड:** सभी ब्लेड/नैसेल एक्सेस और लिफ्टिंग संचालन तुरंत निलंबित करें। फिर से शुरू करने से पहले 30-30 नियम और समुद्र की स्थिति की पुनः जांच करें।',
              "ur": '🚨 **شدید حفاظتی اوور رائیڈ:** تمام بلیڈ/نیسیل رسائی اور لفٹنگ آپریشنز فوری معطل کریں۔ دوبارہ شروع کرنے سے پہلے 30-30 اصول اور سمندری حالت کی دوبارہ جانچ کریں۔',
              "da": '🚨 **KRITISK SIKKERHEDSOVERSTYRING:** Øjeblikkelig suspendering af al adgang til vinge/nacelle og løfteoperationer. Genkontroller 30-30-reglen og søtilstanden, før arbejdet genoptages.',
              "nl": '🚨 **KRITIEKE VEILIGHEIDSOVERSCHRIJDING:** Onmiddellijke opschorting van alle toegang tot blad/gondel en hijswerkzaamheden. Controleer de 30-30-regel en de zeestaat opnieuw voordat het werk wordt hervat.',
              "no": '🚨 **KRITISK SIKKERHETSOVERSTYRING:** Umiddelbar stans av all tilgang til blad/nacelle og løfteoperasjoner. Sjekk 30-30-regelen og sjøtilstanden på nytt før gjenopptakelse.',
              "sv": '🚨 **KRITISKT SÄKERHETSÖVERSKRIDANDE:** Omedelbart stopp av all tillgång till blad/nacell och lyftoperationer. Kontrollera 30-30-regeln och sjötillståndet på nytt innan arbetet återupptas.',
              "pt": '🚨 **ANULAÇÃO DE SEGURANÇA CRÍTICA:** Suspensão imediata de todo acesso a pá/nacele e operações de içamento. Reverifique a regra 30-30 e o estado do mar antes de retomar.',
              "de": '🚨 **KRITISCHE SICHERHEITSÜBERSCHREITUNG:** Sofortige Aussetzung des gesamten Zugangs zu Blatt/Gondel und aller Hebevorgänge. 30-30-Regel und Seegang vor Wiederaufnahme erneut prüfen.',
    },
    "windenergy_high_alert": {
        "fr": "⚠️ **ATTENTION :** Conditions de vent ou de mer élevées. Restreindre aux "
              "tâches essentielles uniquement.",
        "en": "⚠️ **WARNING:** Elevated wind or sea-state conditions. Restrict to essential "
              "tasks only.",
        "ar": "⚠️ **تحذير:** ظروف رياح أو حالة بحر مرتفعة. الاقتصار على المهام الأساسية فقط.",
        "es": "⚠️ **ADVERTENCIA:** Condiciones de viento o mar elevadas. Restrinja a tareas "
              "esenciales únicamente.",
              "zh": '⚠️ **警告：** 风力或海况条件升高。仅限执行必要任务。',
              "ja": '⚠️ **警告：** 風または海況の条件が悪化しています。必須作業のみに制限してください。',
              "hi": '⚠️ **चेतावनी:** पवन या समुद्री स्थिति बढ़ी हुई है। केवल आवश्यक कार्यों तक सीमित रखें।',
              "ur": '⚠️ **انتباہ:** ہوا یا سمندری حالت بلند ہے۔ صرف ضروری کاموں تک محدود رکھیں۔',
              "da": '⚠️ **ADVARSEL:** Forhøjede vind- eller søforhold. Begræns til kun væsentlige opgaver.',
              "nl": '⚠️ **WAARSCHUWING:** Verhoogde wind- of zeestaatomstandigheden. Beperk tot alleen essentiële taken.',
              "no": '⚠️ **ADVARSEL:** Forhøyede vind- eller sjøforhold. Begrens til kun essensielle oppgaver.',
              "sv": '⚠️ **VARNING:** Förhöjda vind- eller sjöförhållanden. Begränsa till endast nödvändiga uppgifter.',
              "pt": '⚠️ **AVISO:** Condições elevadas de vento ou estado do mar. Restrinja apenas a tarefas essenciais.',
              "de": '⚠️ **WARNUNG:** Erhöhte Wind- oder Seegangsbedingungen. Auf unbedingt notwendige Aufgaben beschränken.',
    },
    "windenergy_standard_ok": {
        "fr": "✅ Conditions standards. Poursuivre la surveillance du vent et de la foudre.",
        "en": "✅ Standard conditions. Continue wind and lightning monitoring.",
        "ar": "✅ ظروف اعتيادية. متابعة مراقبة الرياح والبرق.",
        "es": "✅ Condiciones estándar. Continúe el monitoreo de viento y rayos.",
        "zh": '✅ 标准条件。请继续进行风力和雷电监测。',
        "ja": '✅ 標準的な条件です。風と落雷の監視を継続してください。',
        "hi": '✅ मानक स्थितियां। पवन और बिजली निगरानी जारी रखें।',
        "ur": '✅ معیاری حالات۔ ہوا اور بجلی کی نگرانی جاری رکھیں۔',
        "da": '✅ Standardforhold. Fortsæt overvågning af vind og lyn.',
        "nl": '✅ Standaardomstandigheden. Blijf wind en blikseminslag bewaken.',
        "no": '✅ Standardforhold. Fortsett overvåking av vind og lyn.',
        "sv": '✅ Standardförhållanden. Fortsätt övervaka vind och blixtnedslag.',
        "pt": '✅ Condições padrão. Continue o monitoramento de vento e raios.',
        "de": '✅ Standardbedingungen. Wind- und Blitzüberwachung fortsetzen.',
    },

    # --- Module 7: Mining & Quarrying ---
    "mining_header": {
        "fr": "⛏️ Mines & carrières", "en": "⛏️ Mining & Quarrying",
        "ar": "⛏️ التعدين والمحاجر", "es": "⛏️ Minería y Canteras",
    },
    "mining_caption": {
        "fr": "Silice cristalline respirable, dose de bruit et vibrations corps entier "
              "pour les équipes de front de taille et d'engins mobiles",
        "en": "Respirable crystalline silica, noise dose, and whole-body vibration for "
              "quarry-face and mobile-plant crews",
        "ar": "السيليكا البلورية القابلة للاستنشاق، جرعة الضوضاء، واهتزاز الجسم الكامل "
              "لطواقم واجهة المحجر والمعدات المتنقلة",
        "es": "Sílice cristalina respirable, dosis de ruido y vibración de cuerpo entero "
              "para cuadrillas de frente de cantera y maquinaria móvil",
    },
    "mining_env_data_header": {
        "fr": "Données environnementales", "en": "Environmental data",
        "ar": "البيانات البيئية", "es": "Datos ambientales",
    },
    "mining_silica_label": {
        "fr": "Silice cristalline respirable (µg/m³)", "en": "Respirable crystalline silica (µg/m³)",
        "ar": "السيليكا البلورية القابلة للاستنشاق (µg/m³)", "es": "Sílice cristalina respirable (µg/m³)",
    },
    "mining_noise_label": {
        "fr": "Niveau de bruit mesuré (dBA)", "en": "Measured noise level (dBA)",
        "ar": "مستوى الضوضاء المقاس (dBA)", "es": "Nivel de ruido medido (dBA)",
    },
    "mining_noise_hours_label": {
        "fr": "Durée d'exposition au bruit (heures)", "en": "Noise exposure duration (hours)",
        "ar": "مدة التعرض للضوضاء (ساعات)", "es": "Duración de exposición al ruido (horas)",
    },
    "mining_vibration_label": {
        "fr": "Vibration mesurée a_w (m/s²)", "en": "Measured vibration a_w (m/s²)",
        "ar": "الاهتزاز المقاس a_w (م/ث²)", "es": "Vibración medida a_w (m/s²)",
    },
    "mining_vibration_hours_label": {
        "fr": "Durée d'exposition aux vibrations (heures)", "en": "Vibration exposure duration (hours)",
        "ar": "مدة التعرض للاهتزاز (ساعات)", "es": "Duración de exposición a la vibración (horas)",
    },
    "silica_exceeds_label": {
        "fr": "Limite OEL silice dépassée", "en": "Silica OEL exceeded",
        "ar": "تجاوز حد OEL للسيليكا", "es": "Límite OEL de sílice superado",
    },
    "noise_dose_label": {
        "fr": "Dose de bruit (%)", "en": "Noise dose (%)",
        "ar": "جرعة الضوضاء (%)", "es": "Dosis de ruido (%)",
    },
    "vibration_a8_label": {
        "fr": "Vibration A(8) (m/s²)", "en": "Vibration A(8) (m/s²)",
        "ar": "الاهتزاز A(8) (م/ث²)", "es": "Vibración A(8) (m/s²)",
    },
    "mining_critical_alert": {
        "fr": "🚨 **DÉPASSEMENT DE SÉCURITÉ CRITIQUE :** Silice, bruit ou vibration au-delà "
              "des limites critiques. Retirer immédiatement le personnel exposé.",
        "en": "🚨 **CRITICAL SAFETY OVERRIDE:** Silica, noise, or vibration beyond critical "
              "limits. Remove exposed personnel immediately.",
        "ar": "🚨 **تجاوز سلامة حرج:** السيليكا أو الضوضاء أو الاهتزاز تجاوزت الحدود "
              "الحرجة. إبعاد الأفراد المعرضين فوراً.",
        "es": "🚨 **ANULACIÓN DE SEGURIDAD CRÍTICA:** Sílice, ruido o vibración más allá de "
              "los límites críticos. Retire al personal expuesto de inmediato.",
              "zh": '🚨 **严重安全超限：** 二氧化硅、噪音或振动超出临界限值。请立即撤离暴露人员。',
              "ja": '🚨 **重大な安全オーバーライド：** シリカ、騒音、または振動が臨界限界値を超えています。曝露している作業員を直ちに退避させてください。',
              "hi": '🚨 **गंभीर सुरक्षा ओवरराइड:** सिलिका, शोर, या कंपन गंभीर सीमाओं से अधिक है। उजागर कर्मियों को तुरंत हटाएं।',
              "ur": '🚨 **شدید حفاظتی اوور رائیڈ:** سیلیکا، شور، یا وائبریشن نازک حدود سے تجاوز کر گئے ہیں۔ متاثرہ عملے کو فوری طور پر ہٹائیں۔',
              "da": '🚨 **KRITISK SIKKERHEDSOVERSTYRING:** Silica, støj eller vibration ud over kritiske grænser. Fjern eksponeret personale øjeblikkeligt.',
              "nl": '🚨 **KRITIEKE VEILIGHEIDSOVERSCHRIJDING:** Silica, geluid of trilling boven kritieke limieten. Verwijder blootgesteld personeel onmiddellijk.',
              "no": '🚨 **KRITISK SIKKERHETSOVERSTYRING:** Silika, støy eller vibrasjon over kritiske grenser. Fjern eksponert personell umiddelbart.',
              "sv": '🚨 **KRITISKT SÄKERHETSÖVERSKRIDANDE:** Kvartsdamm, buller eller vibration överskrider kritiska gränser. Avlägsna exponerad personal omedelbart.',
              "pt": '🚨 **ANULAÇÃO DE SEGURANÇA CRÍTICA:** Sílica, ruído ou vibração além dos limites críticos. Retire o pessoal exposto imediatamente.',
              "de": '🚨 **KRITISCHE SICHERHEITSÜBERSCHREITUNG:** Quarzstaub, Lärm oder Vibration jenseits kritischer Grenzwerte. Exponiertes Personal sofort entfernen.',
    },
    "mining_high_alert": {
        "fr": "⚠️ **ATTENTION :** Exposition approchant les limites réglementaires. "
              "Renforcer les EPI et la rotation.",
        "en": "⚠️ **WARNING:** Exposure approaching regulatory limits. Reinforce PPE and rotation.",
        "ar": "⚠️ **تحذير:** التعرض يقترب من الحدود التنظيمية. تعزيز معدات الوقاية والتناوب.",
        "es": "⚠️ **ADVERTENCIA:** Exposición acercándose a los límites regulatorios. "
              "Refuerce el EPP y la rotación.",
              "zh": '⚠️ **警告：** 暴露水平正接近法规限值。请加强PPE与轮岗。',
              "ja": '⚠️ **警告：** ばく露が規制限界値に近づいています。PPEとローテーションを強化してください。',
              "hi": '⚠️ **चेतावनी:** एक्सपोजर नियामक सीमाओं के करीब पहुंच रहा है। PPE और रोटेशन को मजबूत करें。',
              "ur": '⚠️ **انتباہ:** ایکسپوژر ریگولیٹری حدود کے قریب پہنچ رہا ہے۔ PPE اور گردش کو مضبوط کریں۔',
              "da": '⚠️ **ADVARSEL:** Eksponering nærmer sig lovgivningsmæssige grænser. Styrk PPE og rotation.',
              "nl": '⚠️ **WAARSCHUWING:** Blootstelling nadert wettelijke limieten. Versterk PBM en rotatie.',
              "no": '⚠️ **ADVARSEL:** Eksponering nærmer seg lovpålagte grenser. Styrk PVU og rotasjon.',
              "sv": '⚠️ **VARNING:** Exponeringen närmar sig lagstadgade gränser. Förstärk PPE och rotation.',
              "pt": '⚠️ **AVISO:** Exposição se aproximando dos limites regulatórios. Reforce o EPI e o rodízio.',
              "de": '⚠️ **WARNUNG:** Exposition nähert sich den gesetzlichen Grenzwerten. PSA und Rotation verstärken.',
    },
    "mining_standard_ok": {
        "fr": "✅ Expositions dans les limites standards. Poursuivre la surveillance.",
        "en": "✅ Exposures within standard limits. Continue monitoring.",
        "ar": "✅ مستويات التعرض ضمن الحدود الاعتيادية. متابعة المراقبة.",
        "es": "✅ Exposiciones dentro de los límites estándar. Continúe el monitoreo.",
        "zh": '✅ 暴露水平在标准限值内。请继续监测。',
        "ja": '✅ ばく露は標準限界値内です。監視を継続してください。',
        "hi": '✅ एक्सपोजर मानक सीमाओं के भीतर हैं। निगरानी जारी रखें।',
        "ur": '✅ ایکسپوژر معیاری حدود کے اندر ہیں۔ نگرانی جاری رکھیں۔',
        "da": '✅ Eksponeringer inden for standardgrænser. Fortsæt overvågningen.',
        "nl": '✅ Blootstellingen binnen standaardlimieten. Blijf monitoren.',
        "no": '✅ Eksponeringer innenfor standardgrenser. Fortsett overvåking.',
        "sv": '✅ Exponeringar inom standardgränser. Fortsätt övervakningen.',
        "pt": '✅ Exposições dentro dos limites padrão. Continue o monitoramento.',
        "de": '✅ Expositionen innerhalb der Standardgrenzwerte. Überwachung fortsetzen.',
    },

    # --- Module 8: Marine & Port Construction ---
    "marineport_header": {
        "fr": "⚓ Construction marine & portuaire", "en": "⚓ Marine & Port Construction",
        "ar": "⚓ الإنشاءات البحرية والموانئ", "es": "⚓ Construcción Marina y Portuaria",
    },
    "marineport_caption": {
        "fr": "Marge de dégagement de marée, modificateur de visibilité nocturne, et "
              "dégradation par corrosion saline du matériel en zone d'éclaboussure",
        "en": "Tide clearance margin, night-time visibility modifier, and salt-spray "
              "corrosion degradation of splash-zone hardware",
        "ar": "هامش تخليص المد، معدّل الرؤية الليلية، وتدهور المعدات بفعل التآكل "
              "الملحي في منطقة الرذاذ",
        "es": "Margen de holgura de marea, modificador de visibilidad nocturna, y "
              "degradación por corrosión salina del equipo en zona de salpicadura",
    },
    "marineport_env_data_header": {
        "fr": "Données environnementales", "en": "Environmental data",
        "ar": "البيانات البيئية", "es": "Datos ambientales",
    },
    "marineport_tide_label": {
        "fr": "Niveau de marée actuel (m)", "en": "Current tide level (m)",
        "ar": "مستوى المد الحالي (م)", "es": "Nivel de marea actual (m)",
    },
    "marineport_clearance_label": {
        "fr": "Dégagement minimum requis (m)", "en": "Required minimum clearance (m)",
        "ar": "الحد الأدنى المطلوب للتخليص (م)", "es": "Holgura mínima requerida (m)",
    },
    "marineport_night_toggle": {
        "fr": "Opération de nuit", "en": "Night-time operation",
        "ar": "عملية ليلية", "es": "Operación nocturna",
    },
    "marineport_illuminance_label": {
        "fr": "Éclairement mesuré (lux)", "en": "Measured illuminance (lux)",
        "ar": "الإضاءة المقاسة (لوكس)", "es": "Iluminancia medida (lux)",
    },
    "marineport_hardware_years_label": {
        "fr": "Âge du matériel en service (années)", "en": "Hardware years in service",
        "ar": "عمر المعدات قيد الخدمة (سنوات)", "es": "Años del equipo en servicio",
    },
    "marineport_exposure_class_label": {
        "fr": "Classe d'exposition à la corrosion", "en": "Corrosion exposure class",
        "ar": "فئة التعرض للتآكل", "es": "Clase de exposición a la corrosión",
    },
    "tide_margin_label": {
        "fr": "Marge de dégagement (m)", "en": "Clearance margin (m)",
        "ar": "هامش التخليص (م)", "es": "Margen de holgura (m)",
    },
    "hardware_capacity_label": {
        "fr": "Capacité résiduelle du matériel (%)", "en": "Hardware remaining capacity (%)",
        "ar": "السعة المتبقية للمعدات (%)", "es": "Capacidad restante del equipo (%)",
    },
    "marineport_critical_alert": {
        "fr": "🚨 **DÉPASSEMENT DE SÉCURITÉ CRITIQUE :** Marge de marée critique ou matériel "
              "gravement dégradé. Arrêter l'accès immédiatement.",
        "en": "🚨 **CRITICAL SAFETY OVERRIDE:** Critical tide margin or severely degraded "
              "hardware. Halt access immediately.",
        "ar": "🚨 **تجاوز سلامة حرج:** هامش مد حرج أو معدات متدهورة بشدة. إيقاف الوصول فوراً.",
        "es": "🚨 **ANULACIÓN DE SEGURIDAD CRÍTICA:** Margen de marea crítico o equipo "
              "gravemente degradado. Detenga el acceso de inmediato.",
              "zh": '🚨 **严重安全超限：** 潮位余量处于危急水平或设备严重退化。请立即停止进入。',
              "ja": '🚨 **重大な安全オーバーライド：** 潮位余裕が危機的、または機材の劣化が深刻です。直ちにアクセスを停止してください。',
              "hi": '🚨 **गंभीर सुरक्षा ओवरराइड:** महत्वपूर्ण ज्वार मार्जिन या गंभीर रूप से खराब हार्डवेयर। पहुंच तुरंत रोकें।',
              "ur": '🚨 **شدید حفاظتی اوور رائیڈ:** نازک جوار مارجن یا شدید خراب ہارڈویئر۔ رسائی فوری طور پر روکیں۔',
              "da": '🚨 **KRITISK SIKKERHEDSOVERSTYRING:** Kritisk tidevandsmargin eller alvorligt nedbrudt udstyr. Stop adgangen øjeblikkeligt.',
              "nl": '🚨 **KRITIEKE VEILIGHEIDSOVERSCHRIJDING:** Kritieke getijmarge of ernstig aangetast materieel. Stop de toegang onmiddellijk.',
              "no": '🚨 **KRITISK SIKKERHETSOVERSTYRING:** Kritisk tidevannsmargin eller alvorlig forringet utstyr. Stans tilgang umiddelbart.',
              "sv": '🚨 **KRITISKT SÄKERHETSÖVERSKRIDANDE:** Kritisk tidvattenmarginal eller allvarligt försämrad utrustning. Stoppa tillträdet omedelbart.',
              "pt": '🚨 **ANULAÇÃO DE SEGURANÇA CRÍTICA:** Margem de maré crítica ou equipamento severamente degradado. Interrompa o acesso imediatamente.',
              "de": '🚨 **KRITISCHE SICHERHEITSÜBERSCHREITUNG:** Kritische Gezeitenmarge oder stark beeinträchtigte Ausrüstung. Zugang sofort stoppen.',
    },
    "marineport_high_alert": {
        "fr": "⚠️ **ATTENTION :** Marge de marée restreinte ou visibilité nocturne "
              "insuffisante. Limiter aux tâches essentielles.",
        "en": "⚠️ **WARNING:** Restricted tide margin or insufficient night visibility. "
              "Limit to essential tasks.",
        "ar": "⚠️ **تحذير:** هامش مد مقيّد أو رؤية ليلية غير كافية. الاقتصار على المهام "
              "الأساسية.",
        "es": "⚠️ **ADVERTENCIA:** Margen de marea restringido o visibilidad nocturna "
              "insuficiente. Limite a tareas esenciales.",
              "zh": '⚠️ **警告：** 潮位余量受限或夜间能见度不足。请仅限执行必要任务。',
              "ja": '⚠️ **警告：** 潮位余裕が制限されている、または夜間視界が不十分です。必須作業のみに制限してください。',
              "hi": '⚠️ **चेतावनी:** प्रतिबंधित ज्वार मार्जिन या अपर्याप्त रात्रि दृश्यता। आवश्यक कार्यों तक सीमित करें।',
              "ur": '⚠️ **انتباہ:** محدود جوار مارجن یا رات کی ناکافی مرئیت۔ ضروری کاموں تک محدود رکھیں۔',
              "da": '⚠️ **ADVARSEL:** Begrænset tidevandsmargin eller utilstrækkelig natudsyn. Begræns til væsentlige opgaver.',
              "nl": '⚠️ **WAARSCHUWING:** Beperkte getijmarge of onvoldoende nachtzicht. Beperk tot essentiële taken.',
              "no": '⚠️ **ADVARSEL:** Begrenset tidevannsmargin eller utilstrekkelig nattsikt. Begrens til essensielle oppgaver.',
              "sv": '⚠️ **VARNING:** Begränsad tidvattenmarginal eller otillräcklig siktbarhet nattetid. Begränsa till nödvändiga uppgifter.',
              "pt": '⚠️ **AVISO:** Margem de maré restrita ou visibilidade noturna insuficiente. Limite a tarefas essenciais.',
              "de": '⚠️ **WARNUNG:** Eingeschränkte Gezeitenmarge oder unzureichende Nachtsicht. Auf notwendige Aufgaben beschränken.',
    },
    "marineport_standard_ok": {
        "fr": "✅ Conditions standards. Poursuivre la surveillance de marée et du matériel.",
        "en": "✅ Standard conditions. Continue tide and hardware-condition monitoring.",
        "ar": "✅ ظروف اعتيادية. متابعة مراقبة المد وحالة المعدات.",
        "es": "✅ Condiciones estándar. Continúe el monitoreo de marea y del equipo.",
        "zh": '✅ 标准条件。请继续监测潮位与设备状况。',
        "ja": '✅ 標準的な条件です。潮位と機材状態の監視を継続してください。',
        "hi": '✅ मानक स्थितियां। ज्वार और हार्डवेयर-स्थिति निगरानी जारी रखें।',
        "ur": '✅ معیاری حالات۔ جوار اور ہارڈویئر کی حالت کی نگرانی جاری رکھیں۔',
        "da": '✅ Standardforhold. Fortsæt overvågning af tidevand og udstyrstilstand.',
        "nl": '✅ Standaardomstandigheden. Blijf getijden en materieeltoestand bewaken.',
        "no": '✅ Standardforhold. Fortsett overvåking av tidevann og utstyrstilstand.',
        "sv": '✅ Standardförhållanden. Fortsätt övervaka tidvatten och utrustningens skick.',
        "pt": '✅ Condições padrão. Continue o monitoramento de maré e do estado do equipamento.',
        "de": '✅ Standardbedingungen. Überwachung von Gezeiten und Ausrüstungszustand fortsetzen.',
    },

    # --- Cross-cutting: TTS, translation, country selector, daily briefing, geofencing ---
    "tts_button_label": {
        "fr": "🔊 Écouter cette alerte", "en": "🔊 Listen to this alert",
        "ar": "🔊 استمع لهذا التنبيه", "es": "🔊 Escuchar esta alerta",
        "zh": '🔊 收听此警报',
        "ja": '🔊 このアラートを聞く',
        "hi": '🔊 इस अलर्ट को सुनें',
        "ur": '🔊 اس الرٹ کو سنیں',
        "da": '🔊 Lyt til denne alarm',
        "nl": '🔊 Luister naar deze melding',
        "no": '🔊 Lytt til dette varselet',
        "sv": '🔊 Lyssna på detta larm',
        "pt": '🔊 Ouvir este alerta',
        "de": '🔊 Diesen Alarm anhören',
    },
    "tts_generating": {
        "fr": "Génération audio en cours...", "en": "Generating audio...",
        "ar": "جارٍ إنشاء الصوت...", "es": "Generando audio...",
        "zh": '正在生成音频...',
        "ja": '音声を生成中...',
        "hi": 'ऑडियो जनरेट हो रहा है...',
        "ur": 'آڈیو تیار ہو رہی ہے...',
        "da": 'Genererer lyd...',
        "nl": 'Audio genereren...',
        "no": 'Genererer lyd...',
        "sv": 'Genererar ljud...',
        "pt": 'Gerando áudio...',
        "de": 'Audio wird erzeugt...',
    },
    "tts_unavailable": {
        "fr": "Audio indisponible (service de synthèse vocale injoignable). Le texte de "
              "l'alerte reste affiché ci-dessus.",
        "en": "Audio unavailable (text-to-speech service unreachable). The alert text "
              "above is still fully readable.",
        "ar": "الصوت غير متاح (تعذر الوصول إلى خدمة تحويل النص إلى كلام). يظل نص "
              "التنبيه أعلاه مقروءاً بالكامل.",
        "es": "Audio no disponible (servicio de texto a voz inaccesible). El texto de "
              "la alerta arriba sigue siendo completamente legible.",
              "zh": '音频不可用（无法连接语音合成服务）。上方警报文字仍可完整阅读。',
              "ja": '音声は利用できません（音声合成サービスに接続できません）。上記の警報テキストは引き続き完全にお読みいただけます。',
              "hi": 'ऑडियो अनुपलब्ध है (टेक्स्ट-टू-स्पीच सेवा तक नहीं पहुंचा जा सका)। ऊपर दिया गया अलर्ट टेक्स्ट पूरी तरह पठनीय है।',
              "ur": 'آڈیو دستیاب نہیں (ٹیکسٹ ٹو اسپیچ سروس تک رسائی ناممکن)۔ اوپر دیا گیا الرٹ متن مکمل طور پر پڑھا جا سکتا ہے۔',
              "da": 'Lyd utilgængelig (tekst-til-tale-tjeneste kan ikke nås). Alarmteksten ovenfor er stadig fuldt læsbar.',
              "nl": 'Audio niet beschikbaar (tekst-naar-spraakservice onbereikbaar). De waarschuwingstekst hierboven blijft volledig leesbaar.',
              "no": 'Lyd utilgjengelig (tekst-til-tale-tjenesten kan ikke nås). Varselteksten ovenfor er fortsatt fullt lesbar.',
              "sv": 'Ljud ej tillgängligt (text-till-tal-tjänsten kan inte nås). Larmtexten ovan är fortfarande fullt läsbar.',
              "pt": 'Áudio indisponível (serviço de texto para voz inacessível). O texto do alerta acima continua totalmente legível.',
              "de": 'Audio nicht verfügbar (Text-zu-Sprache-Dienst nicht erreichbar). Der obige Alarmtext bleibt vollständig lesbar.',
    },
    "translate_expander_label": {
        "fr": "🌍 Traduire cette synthèse", "en": "🌍 Translate this briefing",
        "ar": "🌍 ترجمة هذا الموجز", "es": "🌍 Traducir este resumen",
        "zh": '🌍 翻译此简报',
        "ja": '🌍 このブリーフィングを翻訳',
        "hi": '🌍 इस ब्रीफिंग का अनुवाद करें',
        "ur": '🌍 اس بریفنگ کا ترجمہ کریں',
        "da": '🌍 Oversæt denne briefing',
        "nl": '🌍 Vertaal deze briefing',
        "no": '🌍 Oversett denne briefingen',
        "sv": '🌍 Översätt denna briefing',
        "pt": '🌍 Traduzir este resumo',
        "de": '🌍 Dieses Briefing übersetzen',
    },
    "translate_target_label": {
        "fr": "Traduire vers", "en": "Translate to",
        "ar": "الترجمة إلى", "es": "Traducir a",
        "zh": '翻译为',
        "ja": '翻訳先',
        "hi": 'अनुवाद करें',
        "ur": 'ترجمہ کریں',
        "da": 'Oversæt til',
        "nl": 'Vertalen naar',
        "no": 'Oversett til',
        "sv": 'Översätt till',
        "pt": 'Traduzir para',
        "de": 'Übersetzen nach',
    },
    "translate_dialect_label": {
        "fr": "Variante dialectale (arabe)", "en": "Dialect variant (Arabic)",
        "ar": "النسخة اللهجية (العربية)", "es": "Variante dialectal (árabe)",
        "zh": '方言变体（阿拉伯语）',
        "ja": '方言バリエーション（アラビア語）',
        "hi": 'बोली प्रकार (अरबी)',
        "ur": 'لہجہ ورژن (عربی)',
        "da": 'Dialektvariant (arabisk)',
        "nl": 'Dialectvariant (Arabisch)',
        "no": 'Dialektvariant (arabisk)',
        "sv": 'Dialektvariant (arabiska)',
        "pt": 'Variante dialetal (árabe)',
        "de": 'Dialektvariante (Arabisch)',
    },
    "translate_button": {
        "fr": "Traduire", "en": "Translate", "ar": "ترجم", "es": "Traducir",
        "zh": '翻译',
        "ja": '翻訳',
        "hi": 'अनुवाद करें',
        "ur": 'ترجمہ کریں',
        "da": 'Oversæt',
        "nl": 'Vertalen',
        "no": 'Oversett',
        "sv": 'Översätt',
        "pt": 'Traduzir',
        "de": 'Übersetzen',
    },
    "translate_no_key": {
        "fr": "Traduction indisponible sans clé API - le texte original est affiché.",
        "en": "Translation unavailable without an API key - showing the original text.",
        "ar": "الترجمة غير متاحة بدون مفتاح API - يتم عرض النص الأصلي.",
        "es": "Traducción no disponible sin una clave API - se muestra el texto original.",
        "zh": '没有API密钥无法翻译——显示原文。',
        "ja": 'APIキーがないため翻訳できません - 元のテキストを表示しています。',
        "hi": 'एपीआई कुंजी के बिना अनुवाद उपलब्ध नहीं है - मूल पाठ दिखाया जा रहा है।',
        "ur": 'API کلید کے بغیر ترجمہ دستیاب نہیں - اصل متن دکھایا جا رہا ہے۔',
        "da": 'Oversættelse er ikke tilgængelig uden en API-nøgle - viser den oprindelige tekst.',
        "nl": 'Vertaling niet beschikbaar zonder API-sleutel - originele tekst wordt getoond.',
        "no": 'Oversettelse er ikke tilgjengelig uten en API-nøkkel - viser originalteksten.',
        "sv": 'Översättning ej tillgänglig utan API-nyckel - visar originaltexten.',
        "pt": 'Tradução indisponível sem uma chave de API - mostrando o texto original.',
        "de": 'Übersetzung ohne API-Schlüssel nicht verfügbar - Originaltext wird angezeigt.',
    },
    "translate_failed": {
        "fr": "Échec de la traduction - le texte original est affiché ci-dessous.",
        "en": "Translation failed - showing the original text below.",
        "ar": "فشلت الترجمة - يتم عرض النص الأصلي أدناه.",
        "es": "Falló la traducción - se muestra el texto original abajo.",
        "zh": '翻译失败——以下显示原文。',
        "ja": '翻訳に失敗しました - 以下に元のテキストを表示します。',
        "hi": 'अनुवाद विफल रहा - नीचे मूल पाठ दिखाया जा रहा है।',
        "ur": 'ترجمہ ناکام ہوا - نیچے اصل متن دکھایا جا رہا ہے۔',
        "da": 'Oversættelse mislykkedes - viser den oprindelige tekst nedenfor.',
        "nl": 'Vertaling mislukt - originele tekst hieronder weergegeven.',
        "no": 'Oversettelse mislyktes - viser originalteksten nedenfor.',
        "sv": 'Översättningen misslyckades - visar originaltexten nedan.',
        "pt": 'Falha na tradução - mostrando o texto original abaixo.',
        "de": 'Übersetzung fehlgeschlagen - Originaltext wird unten angezeigt.',
    },
    "country_selector_label": {
        "fr": "Cadre réglementaire (pays)", "en": "Regulatory framework (country)",
        "ar": "الإطار التنظيمي (البلد)", "es": "Marco regulatorio (país)",
        "zh": '法规框架（国家）',
        "ja": '規制フレームワーク（国）',
        "hi": 'नियामक ढांचा (देश)',
        "ur": 'ریگولیٹری فریم ورک (ملک)',
        "da": 'Lovgivningsmæssig ramme (land)',
        "nl": 'Regelgevend kader (land)',
        "no": 'Regelverksrammeverk (land)',
        "sv": 'Regelverk (land)',
        "pt": 'Marco regulatório (país)',
        "de": 'Regulatorischer Rahmen (Land)',
    },
    "org_context_label": {
        "fr": "Organisation / Projet / Site", "en": "Organization / Project / Site",
    },
    "org_context_org_label": {
        "fr": "Organisation", "en": "Organization",
    },
    "org_context_project_label": {
        "fr": "Projet", "en": "Project",
    },
    "org_context_site_label": {
        "fr": "Site", "en": "Site",
    },
    "midday_ban_active_warning": {
        "fr": "🌡️ Interdiction de travail extérieur de mi-journée actuellement en "
              "vigueur (UAE, mi-juin à mi-septembre, 12h30-15h00).",
        "en": "🌡️ UAE statutory midday outdoor-work ban is currently in effect "
              "(mid-June to mid-September, 12:30-15:00).",
        "ar": "🌡️ حظر العمل الخارجي وقت الظهيرة ساري المفعول حالياً (الإمارات، "
              "منتصف يونيو إلى منتصف سبتمبر، 12:30-15:00).",
        "es": "🌡️ La prohibición legal de trabajo exterior al mediodía en EAU está "
              "vigente actualmente (mediados de junio a mediados de septiembre, 12:30-15:00).",
              "zh": '🌡️ 阿联酋法定的午间户外禁工令目前正在生效（6月中旬至9月中旬，12:30-15:00）。',
              "ja": '🌡️ UAEの法定日中屋外作業禁止が現在適用中です（6月中旬〜9月中旬、12:30〜15:00）。',
              "hi": '🌡️ यूएई का वैधानिक दोपहर बाह्य-कार्य प्रतिबंध वर्तमान में लागू है (मध्य जून से मध्य सितंबर, 12:30-15:00)।',
              "ur": '🌡️ یو اے ای کا قانونی دوپہر آؤٹ ڈور ورک بین فی الحال نافذ ہے (وسط جون سے وسط ستمبر، 12:30-15:00)۔',
              "da": "🌡️ FAE's lovpligtige middagsforbud mod udendørsarbejde er i øjeblikket gældende (midt juni til midt september, 12:30-15:00).",
              "nl": '🌡️ Het wettelijke middagverbod op buitenwerk in de VAE is momenteel van kracht (half juni tot half september, 12:30-15:00).',
              "no": '🌡️ FAEs lovpålagte forbud mot utendørsarbeid midt på dagen gjelder for øyeblikket (midt i juni til midt i september, 12:30-15:00).',
              "sv": '🌡️ Förenade Arabemiratens lagstadgade förbud mot utomhusarbete mitt på dagen gäller för närvarande (mitten av juni till mitten av september, 12:30-15:00).',
              "pt": '🌡️ A proibição legal de trabalho externo ao meio-dia nos EAU está atualmente em vigor (meados de junho a meados de setembro, 12h30-15h00).',
              "de": '🌡️ Das gesetzliche Verbot für Außenarbeiten in den VAE zur Mittagszeit gilt derzeit (Mitte Juni bis Mitte September, 12:30-15:00 Uhr).',
    },
    "daily_briefing_header": {
        "fr": "📋 Briefing quotidien de sécurité (Toolbox Talk)",
        "en": "📋 Daily Safety Briefing (Toolbox Talk)",
        "ar": "📋 الموجز اليومي للسلامة (توك بوكس توك)",
        "es": "📋 Reunión Diaria de Seguridad (Toolbox Talk)",
        "zh": '📋 每日安全简报（班前讲话）',
        "ja": '📋 日次安全ブリーフィング（ツールボックストーク）',
        "hi": '📋 दैनिक सुरक्षा ब्रीफिंग (टूलबॉक्स टॉक)',
        "ur": '📋 روزانہ حفاظتی بریفنگ (ٹول باکس ٹاک)',
        "da": '📋 Daglig sikkerhedsbriefing (Toolbox Talk)',
        "nl": '📋 Dagelijkse veiligheidsbriefing (Toolbox Talk)',
        "no": '📋 Daglig sikkerhetsbriefing (Toolbox Talk)',
        "sv": '📋 Daglig säkerhetsgenomgång (Toolbox Talk)',
        "pt": '📋 Reunião Diária de Segurança (Toolbox Talk)',
        "de": '📋 Tägliches Sicherheits-Briefing (Toolbox Talk)',
    },
    "daily_briefing_caption": {
        "fr": "Génère un script de briefing à lire à l'équipe en début de poste, adapté "
              "aux tâches du jour et à la météo actuelle.",
        "en": "Generates a briefing script to read to the crew at shift start, tailored "
              "to today's tasks and current weather.",
        "ar": "يُنشئ نص موجز لقراءته على الطاقم عند بدء الوردية، مصمم وفق مهام اليوم "
              "والطقس الحالي.",
        "es": "Genera un guion de reunión para leer al equipo al inicio del turno, "
              "adaptado a las tareas de hoy y el clima actual.",
              "zh": '生成一份适用于班次开始时向班组宣读的简报脚本，结合当日任务与当前天气量身定制。',
              "ja": '本日のタスクと現在の天候に合わせて、シフト開始時にクルーへ読み上げるブリーフィング原稿を作成します。',
              "hi": 'आज के कार्यों और वर्तमान मौसम के अनुरूप, शिफ्ट शुरू होने पर दल को पढ़कर सुनाने के लिए एक ब्रीफिंग स्क्रिप्ट तैयार करता है।',
              "ur": 'آج کے کاموں اور موجودہ موسم کے مطابق، شفٹ کے آغاز پر عملے کو پڑھ کر سنانے کے لیے ایک بریفنگ اسکرپٹ تیار کرتا ہے۔',
              "da": 'Genererer et briefingmanuskript til at læse op for holdet ved skiftstart, tilpasset dagens opgaver og det aktuelle vejr.',
              "nl": 'Genereert een briefingscript om bij ploegstart aan de ploeg voor te lezen, afgestemd op de taken van vandaag en het huidige weer.',
              "no": 'Genererer et briefingmanus som skal leses opp for mannskapet ved skiftstart, tilpasset dagens oppgaver og gjeldende vær.',
              "sv": 'Genererar ett briefingmanus att läsa upp för teamet vid skiftstart, anpassat efter dagens uppgifter och aktuellt väder.',
              "pt": 'Gera um roteiro de reunião para ler à equipe no início do turno, adaptado às tarefas de hoje e ao clima atual.',
              "de": 'Erstellt ein Briefing-Skript, das dem Team zu Schichtbeginn vorgelesen wird, zugeschnitten auf die heutigen Aufgaben und das aktuelle Wetter.',
    },
    "daily_briefing_site_label": {
        "fr": "Nom du site", "en": "Site name", "ar": "اسم الموقع", "es": "Nombre del sitio",
        "zh": '场地名称',
        "ja": '現場名',
        "hi": 'साइट नाम',
        "ur": 'سائٹ کا نام',
        "da": 'Sitenavn',
        "nl": 'Locatienaam',
        "no": 'Stedsnavn',
        "sv": 'Platsnamn',
        "pt": 'Nome do local',
        "de": 'Standortname',
    },
    "daily_briefing_tasks_label": {
        "fr": "Tâches prévues aujourd'hui (une par ligne)",
        "en": "Today's scheduled tasks (one per line)",
        "ar": "مهام اليوم المجدولة (واحدة في كل سطر)",
        "es": "Tareas programadas para hoy (una por línea)",
        "zh": '今日计划任务（每行一项）',
        "ja": '本日の予定作業（1行に1つ）',
        "hi": 'आज के निर्धारित कार्य (प्रति पंक्ति एक)',
        "ur": 'آج کے شیڈول شدہ کام (فی لائن ایک)',
        "da": 'Dagens planlagte opgaver (én pr. linje)',
        "nl": 'Vandaag geplande taken (één per regel)',
        "no": 'Dagens planlagte oppgaver (én per linje)',
        "sv": 'Dagens schemalagda uppgifter (en per rad)',
        "pt": 'Tarefas programadas para hoje (uma por linha)',
        "de": 'Heutige geplante Aufgaben (eine pro Zeile)',
    },
    "daily_briefing_generate_button": {
        "fr": "Générer le briefing", "en": "Generate briefing",
        "ar": "إنشاء الموجز", "es": "Generar reunión",
        "zh": '生成简报',
        "ja": 'ブリーフィングを生成',
        "hi": 'ब्रीफिंग जनरेट करें',
        "ur": 'بریفنگ تیار کریں',
        "da": 'Generer briefing',
        "nl": 'Briefing genereren',
        "no": 'Generer briefing',
        "sv": 'Generera briefing',
        "pt": 'Gerar reunião',
        "de": 'Briefing erstellen',
    },
    "daily_briefing_script_label": {
        "fr": "Script du briefing", "en": "Briefing script",
        "ar": "نص الموجز", "es": "Guion de la reunión",
        "zh": '简报脚本',
        "ja": 'ブリーフィング原稿',
        "hi": 'ब्रीफिंग स्क्रिप्ट',
        "ur": 'بریفنگ اسکرپٹ',
        "da": 'Briefingmanuskript',
        "nl": 'Briefingscript',
        "no": 'Briefingmanus',
        "sv": 'Briefingmanus',
        "pt": 'Roteiro da reunião',
        "de": 'Briefing-Skript',
    },
    "geofence_inside_label": {
        "fr": "⚠️ Vous êtes dans une zone de chantier active",
        "en": "⚠️ You are inside an active site hazard zone",
        "ar": "⚠️ أنت داخل منطقة خطر نشطة بالموقع",
        "es": "⚠️ Se encuentra dentro de una zona de peligro activa del sitio",
        "zh": '⚠️ 您正处于活跃的现场危险区域内',
        "ja": '⚠️ アクティブなサイト危険区域内にいます',
        "hi": '⚠️ आप एक सक्रिय साइट खतरा क्षेत्र के भीतर हैं',
        "ur": '⚠️ آپ ایک فعال سائٹ خطرے کے علاقے کے اندر ہیں',
        "da": '⚠️ Du befinder dig i en aktiv farezone på arbejdspladsen',
        "nl": '⚠️ U bevindt zich in een actieve gevarenzone op de locatie',
        "no": '⚠️ Du befinner deg i en aktiv faresone på anlegget',
        "sv": '⚠️ Du befinner dig i en aktiv farozon på arbetsplatsen',
        "pt": '⚠️ Você está dentro de uma zona de perigo ativa do local',
        "de": '⚠️ Sie befinden sich innerhalb einer aktiven Gefahrenzone der Baustelle',
    },
    "geofence_outside_label": {
        "fr": "Aucune zone de chantier à proximité immédiate",
        "en": "No site hazard zone in immediate proximity",
        "ar": "لا توجد منطقة خطر بالموقع في الجوار المباشر",
        "es": "No hay zona de peligro del sitio en proximidad inmediata",
        "zh": '附近没有现场危险区域',
        "ja": '近隣にサイト危険区域はありません',
        "hi": 'तत्काल आसपास कोई साइट खतरा क्षेत्र नहीं',
        "ur": 'قریبی علاقے میں کوئی سائٹ خطرہ زون نہیں',
        "da": 'Ingen farezone på arbejdspladsen i umiddelbar nærhed',
        "nl": 'Geen gevarenzone op de locatie in de directe omgeving',
        "no": 'Ingen faresone på anlegget i umiddelbar nærhet',
        "sv": 'Ingen farozon på arbetsplatsen i omedelbar närhet',
        "pt": 'Nenhuma zona de perigo do local nas proximidades imediatas',
        "de": 'Keine Gefahrenzone der Baustelle in unmittelbarer Nähe',
    },
    "predictive_alert_header": {
        "fr": "🔮 Alerte prévisionnelle", "en": "🔮 Predictive Alert",
        "ar": "🔮 تنبيه استباقي", "es": "🔮 Alerta Predictiva",
        "zh": '🔮 预测性警报',
        "ja": '🔮 予測アラート',
        "hi": '🔮 पूर्वानुमानित अलर्ट',
        "ur": '🔮 پیش گوئی الرٹ',
        "da": '🔮 Prædiktiv alarm',
        "nl": '🔮 Voorspellende waarschuwing',
        "no": '🔮 Prediktivt varsel',
        "sv": '🔮 Prediktivt larm',
        "pt": '🔮 Alerta Preditivo',
        "de": '🔮 Prädiktiver Alarm',
    },
    "country_auto_detected_note": {
        "fr": "📍 Pays détecté automatiquement via GPS - modifiable ci-dessus.",
        "en": "📍 Auto-detected from GPS - override anytime above.",
        "ar": "📍 تم الكشف عنه تلقائياً عبر GPS - يمكن تغييره أعلاه في أي وقت.",
        "es": "📍 Detectado automáticamente por GPS - puede cambiarlo arriba en cualquier momento.",
        "zh": '📍 已通过GPS自动检测——可随时在上方更改。',
        "ja": '📍 GPSから自動検出されました - 上記でいつでも変更できます。',
        "hi": '📍 GPS से स्वतः पहचाना गया - ऊपर कभी भी बदलें।',
        "ur": '📍 GPS سے خودکار طور پر معلوم کیا گیا - اوپر کسی بھی وقت تبدیل کریں۔',
        "da": '📍 Automatisk registreret via GPS - kan til enhver tid ændres ovenfor.',
        "nl": '📍 Automatisch gedetecteerd via GPS - hierboven op elk moment aan te passen.',
        "no": '📍 Automatisk oppdaget via GPS - kan endres når som helst ovenfor.',
        "sv": '📍 Automatiskt identifierad via GPS - ändra när som helst ovan.',
        "pt": '📍 Detectado automaticamente por GPS - altere a qualquer momento acima.',
        "de": '📍 Automatisch per GPS erkannt - oben jederzeit änderbar.',
    },

    # --- New keys added for global expansion (UK/Canada/Australia,
    # regulatory fallback, cold stress, UV, bushfire smoke, remote comms) ---
    "regulatory_fallback_warning": {
        "fr": 'Profil législatif local introuvable. Retour aux directives de référence ACGIH/OSHA mondiales.',
        "en": 'Local legislation profile not found. Falling back to Global ACGIH/OSHA reference guidelines.',
        "ar": 'لم يتم العثور على ملف تشريعي محلي. سيتم الرجوع إلى إرشادات ACGIH/OSHA العالمية المرجعية.',
        "es": 'No se encontró un perfil legislativo local. Se recurrirá a las directrices de referencia globales ACGIH/OSHA.',
        "zh": '未找到本地法规配置文件。将回退至全球ACGIH/OSHA参考指南。',
        "ja": '現地の法規制プロファイルが見つかりません。グローバルなACGIH/OSHA参照ガイドラインにフォールバックします。',
        "hi": 'स्थानीय कानून प्रोफ़ाइल नहीं मिली। वैश्विक ACGIH/OSHA संदर्भ दिशानिर्देशों पर वापस जाया जा रहा है।',
        "ur": 'مقامی قانون سازی پروفائل نہیں ملی۔ عالمی ACGIH/OSHA حوالہ رہنما اصولوں کی طرف واپس جایا جا رہا ہے۔',
        "da": 'Lokal lovgivningsprofil ikke fundet. Falder tilbage til globale ACGIH/OSHA-referenceretningslinjer.',
        "nl": 'Lokaal wetgevingsprofiel niet gevonden. Terugvallen op wereldwijde ACGIH/OSHA-referentierichtlijnen.',
        "no": 'Lokal lovgivningsprofil ikke funnet. Faller tilbake til globale ACGIH/OSHA-referanseretningslinjer.',
        "sv": 'Lokal lagstiftningsprofil hittades inte. Återgår till globala ACGIH/OSHA-referensriktlinjer.',
        "pt": 'Perfil legislativo local não encontrado. Revertendo para as diretrizes de referência globais ACGIH/OSHA.',
        "de": 'Lokales Rechtsprofil nicht gefunden. Rückgriff auf globale ACGIH/OSHA-Referenzrichtlinien.',
    },
    "windchill_label": {
        "fr": 'Refroidissement éolien',
        "en": 'Wind Chill',
        "ar": 'برودة الرياح',
        "es": 'Sensación térmica por viento',
        "zh": '风寒指数',
        "ja": '体感温度（風冷）',
        "hi": 'पवन-शीत सूचकांक',
        "ur": 'ونڈ چل انڈیکس',
        "da": 'Vindafkøling',
        "nl": 'Windchill',
        "no": 'Vindkjøling',
        "sv": 'Vindkyla',
        "pt": 'Sensação de frio pelo vento',
        "de": 'Windchill (Gefühlte Kälte)',
    },
    "uv_category_label": {
        "fr": 'Catégorie UV',
        "en": 'UV Category',
        "ar": 'فئة الأشعة فوق البنفسجية',
        "es": 'Categoría UV',
        "zh": '紫外线等级',
        "ja": 'UVカテゴリー',
        "hi": 'यूवी श्रेणी',
        "ur": 'UV کیٹیگری',
        "da": 'UV-kategori',
        "nl": 'UV-categorie',
        "no": 'UV-kategori',
        "sv": 'UV-kategori',
        "pt": 'Categoria UV',
        "de": 'UV-Kategorie',
    },
    "bushfire_smoke_header": {
        "fr": "Fumée d'incendie de brousse / Qualité de l'air ambiant",
        "en": 'Bushfire Smoke / Ambient Air Quality',
        "ar": 'دخان حرائق الأدغال / جودة الهواء المحيط',
        "es": 'Humo de incendios forestales / Calidad del aire ambiente',
        "zh": '丛林大火烟雾／环境空气质量',
        "ja": '山火事の煙／大気環境質',
        "hi": 'झाड़ी अग्नि धुआं / परिवेशी वायु गुणवत्ता',
        "ur": 'جھاڑی کی آگ کا دھواں / ماحولیاتی ہوا کا معیار',
        "da": 'Naturbrandsrøg / Omgivende luftkvalitet',
        "nl": 'Bosbrandrook / Omgevingsluchtkwaliteit',
        "no": 'Lyngbrannrøyk / Omgivelsesluftkvalitet',
        "sv": 'Skogsbrandsrök / Omgivande luftkvalitet',
        "pt": 'Fumaça de incêndio florestal / Qualidade do ar ambiente',
        "de": 'Buschbrandrauch / Umgebungsluftqualität',
    },
    "remote_comms_banner": {
        "fr": '📡 Règle australienne (Safe Work Australia) sur les travailleurs isolés : maintenir un contact périodique (~toutes les 60 minutes) avec les équipes isolées/éloignées.',
        "en": '📡 Safe Work Australia isolated-worker rule: maintain a periodic communication check-in (~every 60 minutes) for remote/isolated crew.',
        "ar": '📡 قاعدة العامل المعزول لدى Safe Work Australia: حافظ على تواصل دوري (كل ~60 دقيقة تقريباً) مع الطاقم النائي/المعزول.',
        "es": '📡 Regla de trabajador aislado de Safe Work Australia: mantenga un contacto periódico (~cada 60 minutos) con el personal remoto/aislado.',
        "zh": '📡 澳大利亚安全工作局（Safe Work Australia）孤立工作者规则：请对偏远/孤立班组保持定期通讯确认（约每60分钟一次）。',
        "ja": '📡 Safe Work Australiaの孤立作業者規則：遠隔・孤立した班と定期的な通信確認（約60分ごと）を維持してください。',
        "hi": '📡 Safe Work Australia का पृथक-कर्मी नियम: दूरस्थ/पृथक दल के लिए आवधिक संचार जांच (~हर 60 मिनट) बनाए रखें।',
        "ur": '📡 Safe Work Australia کا تنہا کارکن قاعدہ: دور دراز/تنہا عملے کے لیے وقتاً فوقتاً رابطہ چیک ان (~ہر 60 منٹ) برقرار رکھیں۔',
        "da": '📡 Safe Work Australias regel for isolerede arbejdere: Oprethold periodisk kommunikationstjek (~hvert 60. minut) for fjerntliggende/isolerede hold.',
        "nl": '📡 Safe Work Australia-regel voor geïsoleerde werknemers: onderhoud periodieke communicatiecontroles (~elke 60 minuten) voor afgelegen/geïsoleerde ploegen.',
        "no": '📡 Safe Work Australias regel for isolerte arbeidere: Oppretthold periodisk kommunikasjonssjekk (~hvert 60. minutt) for fjerntliggende/isolerte lag.',
        "sv": '📡 Safe Work Australias regel för isolerade arbetare: Upprätthåll periodisk kommunikationsavstämning (~var 60:e minut) för avlägsna/isolerade team.',
        "pt": '📡 Regra de trabalhador isolado da Safe Work Australia: mantenha uma verificação de comunicação periódica (~a cada 60 minutos) para equipes remotas/isoladas.',
        "de": '📡 Safe-Work-Australia-Regel für isolierte Arbeiter: Regelmäßige Kommunikationsprüfung (~alle 60 Minuten) für abgelegene/isolierte Teams aufrechterhalten.',
    },
    "crane_wind_mph_caption": {
        "fr": 'Seuils de vent grue au Royaume-Uni indiqués en mph et en nœuds',
        "en": 'UK crane wind thresholds shown in mph as well as knots',
        "ar": 'عتبات رياح الرافعة في المملكة المتحدة معروضة بالميل/الساعة وكذلك العقدة',
        "es": 'Umbrales de viento de grúa del Reino Unido mostrados en mph y en nudos',
        "zh": '英国起重机风速阈值同时以mph和节显示',
        "ja": '英国のクレーン風速しきい値はmphとノットの両方で表示されます',
        "hi": 'यूके क्रेन पवन सीमाएं mph और नॉट्स दोनों में दिखाई गई हैं',
        "ur": 'یوکے کرین ونڈ حدود mph اور ناٹس دونوں میں دکھائی گئی ہیں',
        "da": 'UK-krananemometergrænser vises i mph såvel som knob',
        "nl": 'UK-kraanwindgrenzen weergegeven in mph en knopen',
        "no": 'UK-kranvindgrenser vises i mph i tillegg til knop',
        "sv": 'UK-kranvindgränser visas i mph såväl som knop',
        "pt": 'Limites de vento de guindaste do Reino Unido exibidos em mph e nós',
        "de": 'UK-Kranwindgrenzwerte werden sowohl in mph als auch in Knoten angezeigt',
    },

    # --- Enterprise upgrade: worker physiology, extended air quality, noise
    # calculator, J+1 forecasting, high-contrast mode, IP geolocation ---
    # Coverage note: fr/en are fully translated for this block (guaranteed
    # base languages); the other 12 languages gracefully fall back to fr
    # via t()'s existing design (never raises, never shows a raw key) until
    # a follow-up pass translates them, exactly like the previous "Tier-1
    # coverage" decision for the global-expansion keys above.
    "physio_dashboard_header": {"fr": "Suivi physiologique des travailleurs (anonyme)", "en": "Worker Physiological Strain (anonymous)"},
    "physio_caption": {
        "fr": "Marqueurs de profil anonymes uniquement (ex. Worker_A3) - conforme RGPD. "
              "Aucune donnée nominative n'est collectée ni stockée.",
        "en": "Anonymous profile markers only (e.g. Worker_A3) - GDPR-compliant. No named "
              "personal data is collected or stored.",
    },
    "physio_status_safe": {"fr": "SÛR", "en": "SAFE"},
    "physio_status_warning": {"fr": "ALERTE", "en": "WARNING"},
    "physio_status_critical": {"fr": "CRITIQUE", "en": "CRITICAL"},
    "physio_hr_label": {"fr": "Fréquence cardiaque (bpm)", "en": "Heart rate (bpm)"},
    "physio_pct_hrmax_label": {"fr": "% FC max (Tanaka)", "en": "% max HR (Tanaka)"},
    "physio_core_temp_label": {"fr": "Temp. corporelle estimée (Tci, °C)", "en": "Estimated core temp (Tci, °C)"},
    "physio_dehydration_label": {"fr": "Multiplicateur risque déshydratation", "en": "Dehydration risk multiplier"},
    "physio_add_worker_button": {"fr": "+ Ajouter un travailleur (check-in)", "en": "+ Add worker (check-in)"},
    "physio_worker_age_label": {"fr": "Âge du travailleur", "en": "Worker age"},
    "physio_manual_checkin_header": {"fr": "Check-in sécurité manuel", "en": "Manual safety check-in"},
    "physio_no_workers_note": {
        "fr": "Aucun travailleur suivi pour l'instant - ajoutez un check-in ci-dessus pour "
              "démarrer le suivi (montre connectée simulée ou saisie manuelle).",
        "en": "No workers monitored yet - add a check-in above to start tracking (simulated "
              "wearable stream or manual entry).",
    },
    "physio_remove_worker_button": {"fr": "Retirer", "en": "Remove"},
    "physio_wearable_mode_label": {"fr": "Source des données", "en": "Data source"},
    "physio_wearable_simulated": {"fr": "Montre connectée (simulée)", "en": "Wearable stream (simulated)"},
    "physio_wearable_manual": {"fr": "Check-in manuel", "en": "Manual check-in"},
    "physio_medical_disclaimer_caption": {
        "fr": "Ceci est un outil de dépistage de sécurité au travail, pas un dispositif "
              "médical ni un diagnostic - un travailleur en détresse réelle doit recevoir "
              "des premiers secours / soins d'urgence immédiats, indépendamment de cette lecture.",
        "en": "This is a workplace safety screening tool, not a medical device or "
              "diagnosis - a worker in genuine distress must receive immediate first aid / "
              "emergency medical attention regardless of this reading.",
    },
    "air_quality_pm10_label": {"fr": "PM10 (µg/m³)", "en": "PM10 (µg/m³)"},
    "air_quality_o3_label": {"fr": "O₃ (µg/m³)", "en": "O₃ (µg/m³)"},
    "air_quality_no2_label": {"fr": "NO₂ (µg/m³)", "en": "NO₂ (µg/m³)"},
    "ffp3_required_warning": {
        "fr": "⚠️ Pollution ambiante élevée - port du masque FFP3 recommandé avant le début des travaux.",
        "en": "⚠️ Elevated ambient pollution - FFP3 respiratory mask recommended before work starts.",
    },
    "noise_calc_header": {"fr": "Calculateur de bruit (distance → dB)", "en": "Acoustic Noise Calculator (distance → dB)"},
    "noise_calc_caption": {
        "fr": "Estime le niveau sonore à la distance de travail à partir du niveau de "
              "référence de l'équipement (loi de l'inverse du carré, -6 dB par doublement "
              "de distance), puis calcule la dose légale quotidienne selon le pays sélectionné.",
        "en": "Estimates the sound level at your working distance from the equipment's "
              "reference level (inverse-square law, -6 dB per doubling of distance), then "
              "calculates the legal daily dose under the selected country's rules.",
    },
    "noise_source_dba_label": {"fr": "Niveau de la source à 1 m (dBA)", "en": "Source level at 1 m (dBA)"},
    "noise_distance_label": {"fr": "Distance de travail (m)", "en": "Working distance (m)"},
    "noise_estimated_dba_label": {"fr": "Niveau estimé à cette distance (dBA)", "en": "Estimated level at this distance (dBA)"},
    "tomorrow_briefing_header": {"fr": "Pré-briefing de demain (J+1)", "en": "Tomorrow's Pre-Briefing (J+1)"},
    "tomorrow_briefing_caption": {
        "fr": "Analyse les prévisions de demain et propose des ajustements du plan de "
              "poste (ex. suspendre les levages de grue le matin avant un pic de vent prévu).",
        "en": "Analyzes tomorrow's forecast and suggests shift-plan adjustments (e.g. "
              "suspending morning crane lifts ahead of a forecast wind spike).",
    },
    "tomorrow_briefing_button": {"fr": "Générer le pré-briefing de demain", "en": "Generate tomorrow's pre-briefing"},
    "high_contrast_toggle_label": {"fr": "☀️ Mode Haute Visibilité / Plein Soleil", "en": "☀️ High-Contrast / Full Sun Mode"},
    "high_contrast_help": {
        "fr": "Fond blanc, texte noir massif, alertes fluorescentes - pour une lisibilité "
              "optimale en plein soleil sur le terrain.",
        "en": "Pure white background, massive black text, fluorescent alerts - for optimal "
              "readability in harsh field glare.",
    },
    "ip_geo_fallback_button": {"fr": "Utiliser la localisation réseau (approximative)", "en": "Use network location (approximate)"},
    "ip_geo_fallback_note": {
        "fr": "GPS indisponible ou refusé - localisation approximative résolue via l'adresse "
              "IP réseau. Moins précise que le GPS, utilisée uniquement en secours.",
        "en": "GPS unavailable or denied - approximate location resolved via network IP "
              "address. Less precise than GPS, used only as a fallback.",
    },
    "generating_live_note": {"fr": "Génération en direct...", "en": "Generating live..."},
    "narrative_cached_note": {"fr": "⚡ Résultat en cache (< 30 min)", "en": "⚡ Cached result (< 30 min)"},
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
