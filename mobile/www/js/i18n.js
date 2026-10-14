/* Shell strings (the hosted app has its own 14-language i18n). */
(function () {
  const STRINGS = {
    en: {
      loading: "Connecting to MAKU…", reconnecting: "Reconnecting…",
      offlineTitle: "No connection",
      offlineBody: "Showing the last assessments saved on this phone. Live data is not available.",
      serverDown: "MAKU can't be reached right now. Showing the last assessments saved on this phone.",
      retry: "Try again",
      offlineWarning: "Cached results may be out of date. Re-measure on site before any go / no-go decision.",
      historyEmpty: "No assessment has been saved on this phone yet. Run one while online and it will be available here.",
      emergency: "In an emergency: stop work, make the area safe and follow your site emergency procedure.",
      stopWork: "SAFETY OVERRIDE - STOP WORK", simulated: "SIMULATED DATA - not valid for decisions",
      controls: "Priority controls", ago: "ago", justNow: "just now",
      backOnline: "Back online", savedOffline: "Assessment saved for offline use",
      fileShared: "Report ready to share"
    },
    fr: {
      loading: "Connexion à MAKU…", reconnecting: "Reconnexion…",
      offlineTitle: "Pas de connexion",
      offlineBody: "Affichage des dernières évaluations enregistrées sur ce téléphone. Les données en direct sont indisponibles.",
      serverDown: "MAKU est injoignable pour le moment. Affichage des dernières évaluations enregistrées sur ce téléphone.",
      retry: "Réessayer",
      offlineWarning: "Les résultats en cache peuvent être périmés. Mesurez à nouveau sur site avant toute décision go / no-go.",
      historyEmpty: "Aucune évaluation n'est encore enregistrée sur ce téléphone. Lancez-en une en ligne pour la retrouver ici.",
      emergency: "En cas d'urgence : arrêtez le travail, sécurisez la zone et suivez la procédure d'urgence du site.",
      stopWork: "DÉPASSEMENT DE SÉCURITÉ - ARRÊT DU TRAVAIL", simulated: "DONNÉES SIMULÉES - non valides pour décider",
      controls: "Mesures prioritaires", ago: "", justNow: "à l'instant",
      backOnline: "Connexion rétablie", savedOffline: "Évaluation enregistrée hors ligne",
      fileShared: "Rapport prêt à partager"
    },
    ar: {
      loading: "جارٍ الاتصال بـ MAKU…", reconnecting: "جارٍ إعادة الاتصال…",
      offlineTitle: "لا يوجد اتصال",
      offlineBody: "عرض آخر التقييمات المحفوظة على هذا الهاتف. البيانات المباشرة غير متاحة.",
      serverDown: "تعذّر الوصول إلى MAKU حالياً. عرض آخر التقييمات المحفوظة على هذا الهاتف.",
      retry: "أعد المحاولة",
      offlineWarning: "قد تكون النتائج المخزنة قديمة. أعد القياس في الموقع قبل أي قرار بالمتابعة أو الإيقاف.",
      historyEmpty: "لم يُحفظ أي تقييم على هذا الهاتف بعد. شغّل تقييماً أثناء الاتصال وسيظهر هنا.",
      emergency: "في حالات الطوارئ: أوقف العمل، أمّن المنطقة واتبع إجراءات الطوارئ في الموقع.",
      stopWork: "تجاوز السلامة - أوقف العمل", simulated: "بيانات محاكاة - غير صالحة لاتخاذ القرار",
      controls: "الإجراءات ذات الأولوية", ago: "", justNow: "الآن",
      backOnline: "عاد الاتصال", savedOffline: "تم حفظ التقييم للاستخدام دون اتصال",
      fileShared: "التقرير جاهز للمشاركة"
    }
  };
  const lang = (navigator.language || "en").slice(0, 2).toLowerCase();
  const active = STRINGS[lang] ? lang : "en";
  window.MAKU_LANG = active;
  window.t = (key) => (STRINGS[active] && STRINGS[active][key]) || STRINGS.en[key] || key;
  document.documentElement.lang = active;
  if (active === "ar") document.documentElement.dir = "rtl";
  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = window.t(el.dataset.i18n); });
  });
})();
