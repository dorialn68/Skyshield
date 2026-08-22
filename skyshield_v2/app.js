document.documentElement.classList.add("js");

const ACCESS_SESSION_KEY = "airshield-preview-access";
const ACCESS_SESSION_VALUE = "granted-v1";
const ACCESS_CODE_DIGEST = "d7c7673ba8ca7b0f04b1af4df026cbea7fed5b8acf59b27d33ef988c60eff054";

async function digestAccessCode(value) {
  const bytes = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function grantPresentationAccess(remember = true) {
  const gate = document.getElementById("accessGate");
  if (remember) {
    try {
      sessionStorage.setItem(ACCESS_SESSION_KEY, ACCESS_SESSION_VALUE);
    } catch (_) {
      // Access still applies to the current document.
    }
  }

  document.documentElement.classList.add("access-granted");
  document.documentElement.classList.remove("access-pending");
  if (gate) gate.hidden = true;
}

function initializeAccessGate() {
  let hasSessionAccess = false;
  try {
    hasSessionAccess = sessionStorage.getItem(ACCESS_SESSION_KEY) === ACCESS_SESSION_VALUE;
  } catch (_) {
    hasSessionAccess = false;
  }

  if (hasSessionAccess) {
    grantPresentationAccess(false);
    return;
  }

  const form = document.getElementById("accessForm");
  const input = document.getElementById("accessCode");
  const status = document.getElementById("accessStatus");
  if (!form || !input || !status) return;

  input.addEventListener("input", () => {
    input.value = input.value.replace(/\D/g, "").slice(0, 4);
    input.removeAttribute("aria-invalid");
    status.textContent = "";
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (input.value.length !== 4) {
      input.setAttribute("aria-invalid", "true");
      status.textContent = "יש להזין קוד בן ארבע ספרות.";
      input.focus();
      return;
    }

    const submittedDigest = await digestAccessCode(input.value);
    if (submittedDigest !== ACCESS_CODE_DIGEST) {
      input.setAttribute("aria-invalid", "true");
      status.textContent = "הקוד אינו מזוהה. נסו שוב.";
      input.select();
      return;
    }

    status.textContent = "הגישה אושרה.";
    document.getElementById("accessGate")?.classList.add("is-unlocking");
    window.setTimeout(() => grantPresentationAccess(true), 220);
  });

  window.requestAnimationFrame(() => input.focus());
}

initializeAccessGate();

const header = document.querySelector(".site-header");
const menuToggle = document.getElementById("menuToggle");
const mobileNav = document.getElementById("mobileNav");

function updateHeader() {
  if (!header) return;
  const scrollable = Math.max(document.documentElement.scrollHeight - window.innerHeight, 1);
  const progress = `${Math.min(window.scrollY / scrollable, 1) * 100}%`;
  header.classList.toggle("is-scrolled", window.scrollY > 18);
  header.style.setProperty("--scroll-progress", progress);
}

window.addEventListener("scroll", updateHeader, { passive: true });
updateHeader();

menuToggle?.addEventListener("click", () => {
  if (!mobileNav) return;
  const open = menuToggle.getAttribute("aria-expanded") === "true";
  menuToggle.setAttribute("aria-expanded", String(!open));
  mobileNav.hidden = open;
});

mobileNav?.querySelectorAll("a").forEach((link) => {
  link.addEventListener("click", () => {
    if (!menuToggle || !mobileNav) return;
    menuToggle.setAttribute("aria-expanded", "false");
    mobileNav.hidden = true;
  });
});

const megaMenu = document.getElementById("megaMenu");
const megaKicker = document.getElementById("megaKicker");
const megaTitle = document.getElementById("megaTitle");
const megaDescription = document.getElementById("megaDescription");
const megaLinks = document.getElementById("megaLinks");
const navScrim = document.getElementById("navScrim");
const desktopMenuLinks = Array.from(document.querySelectorAll("[data-menu-key]"));

const megaMenuContent = {
  investment: {
    kicker: "מערכת מגן תוקף",
    title: "הגנת גבולות",
    description: "נוכחות רציפה, זיהוי מוקדם ונטרול מבוקר לפני קו המגע — מתוך תמונת משימה אחת.",
    links: [["#investment", "תפיסת הפתיחה"], ["#platform", "הפלטפורמה"]]
  },
  platform: {
    kicker: "נכס אווירי מתמיד",
    title: "הפלטפורמה",
    description: "מודל תלת־ממד אינטראקטיבי המציג את כלי הטיס, תחנות המערכת וסביבות התאורה ב־360°.",
    links: [["#modelFrame", "מודל 360°"], ["#investmentDetails", "עיקרי ההשקעה"]]
  },
  system: {
    kicker: "מערכת משולבת",
    title: "המערכת",
    description: "פלטפורמה, קישוריות, תחנת שליטה וממשק מפעיל המחוברים לתמונת מצב אחת.",
    links: [["#system", "עקרונות מפתח"], ["#system", "בקרה וקישוריות"]]
  },
  architecture: {
    kicker: "חמש שכבות הנדסיות",
    title: "ארכיטקטורת מערכת",
    description: "הפרדה ברורה בין כלי הטיס, בקרת הטיסה, מחשוב המשימה, קווי הנתונים והבקרה הקרקעית.",
    links: [["#architecture", "שכבות המערכת"], ["#architecture", "מצב התכן"]]
  },
  planning: {
    kicker: "Baseline to objective",
    title: "בסיס תכנון",
    description: "השוואה שקופה בין מטוס הייחוס המוסב של Block 0 לבין יעדי הביצועים והתכן של Block 1.",
    links: [["#planning", "Block 0"], ["#planning", "Block 1"]]
  },
  roadmap: {
    kicker: "מהשקעה לטיסה",
    title: "תוכנית 18 חודשים",
    description: "רצף עבודה מדורג מהסכמות מסחריות, דרך הדגמה קרקעית, ועד סדרת טיסות ניסוי.",
    links: [["#roadmap", "אבני הדרך"], ["#roadmap", "שימושי הכספים"]]
  },
  leadership: {
    kicker: "יכולת ביצוע",
    title: "המייסדים וההנהלה",
    description: "ניסיון מבצעי, הנדסי וטכנולוגי עמוק המחבר פלטפורמה, AI ולקוח ביטחוני.",
    links: [["#leadership", "הנהלת החברה"], ["#leadership", "הניסיון המצטבר"]]
  }
};

function openMegaMenu(key) {
  const content = megaMenuContent[key];
  if (!header || !megaMenu || !content) return;
  if (megaKicker) megaKicker.textContent = content.kicker;
  if (megaTitle) megaTitle.textContent = content.title;
  if (megaDescription) megaDescription.textContent = content.description;
  if (megaLinks) {
    megaLinks.replaceChildren(...content.links.map(([href, label]) => {
      const link = document.createElement("a");
      link.href = href;
      link.textContent = label;
      link.addEventListener("click", closeMegaMenu);
      return link;
    }));
  }
  header.classList.add("menu-open");
  megaMenu.setAttribute("aria-hidden", "false");
  navScrim?.classList.add("is-visible");
  desktopMenuLinks.forEach((link) => link.classList.toggle("is-active", link.dataset.menuKey === key));
}

function closeMegaMenu() {
  if (!header || !megaMenu) return;
  header.classList.remove("menu-open");
  megaMenu.setAttribute("aria-hidden", "true");
  navScrim?.classList.remove("is-visible");
  desktopMenuLinks.forEach((link) => link.classList.remove("is-active"));
}

desktopMenuLinks.forEach((link) => {
  link.addEventListener("pointerenter", () => openMegaMenu(link.dataset.menuKey));
  link.addEventListener("focus", () => openMegaMenu(link.dataset.menuKey));
  link.addEventListener("click", closeMegaMenu);
});

header?.addEventListener("pointerleave", closeMegaMenu);
navScrim?.addEventListener("click", closeMegaMenu);
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeMegaMenu();
});

const systemSection = document.getElementById("system");
const systemModules = Array.from(document.querySelectorAll("[data-system-module]"));
const systemPrinciples = Array.from(document.querySelectorAll("[data-system-related]"));
const systemDetailIndex = document.getElementById("systemDetailIndex");
const systemDetailKicker = document.getElementById("systemDetailKicker");
const systemDetailTitle = document.getElementById("systemDetailTitle");
const systemDetailText = document.getElementById("systemDetailText");
const systemDetailTags = document.getElementById("systemDetailTags");

const systemDetailContent = {
  airframe: {
    index: "01",
    kicker: "שכבת הפלטפורמה",
    title: "חישה, נשיאה ואוטונומיה בקצה",
    text: "הפלטפורמה מאחדת EO/IR, מטענים ייעודיים, AI Edge וטייס אוטומטי לכדי נכס אווירי רב־משימתי ומתמיד.",
    tags: ["EO/IR", "AI Edge", "Autopilot"]
  },
  communications: {
    index: "02",
    kicker: "שכבת הקישוריות",
    title: "רציפות תקשורתית גם מעבר לקו הראייה",
    text: "קישורי LOS ו־SATCOM / Starlink, הצפנה ויתירות שומרים על שליטה מאובטחת ועל רציפות המשימה בתנאים משתנים.",
    tags: ["LOS", "SATCOM", "Encrypted"]
  },
  mission: {
    index: "03",
    kicker: "שכבת השליטה",
    title: "תמונת מצב אחת לכל שרשרת ההפעלה",
    text: "תחנת השליטה מרכזת חיישנים, משימה ומעקב בזמן אמת כדי לקצר את המעבר מגילוי להבנה ולהחלטה.",
    tags: ["GCS", "Mission", "Common picture"]
  },
  vr: {
    index: "04",
    kicker: "שכבת המפעיל",
    title: "שליטה טבעית בסביבת מציאות רבודה",
    text: "ממשק VR מציג למפעיל את המידע הרלוונטי בהקשר המבצעי ומאפשר תפעול אינטואיטיבי באמצעות צוות קטן.",
    tags: ["VR", "Human in loop", "Small crew"]
  }
};

function activateSystemModule(moduleKey) {
  const content = systemDetailContent[moduleKey];
  if (!systemSection || !content) return;

  systemSection.dataset.systemActive = moduleKey;
  systemModules.forEach((moduleButton) => {
    const selected = moduleButton.dataset.systemModule === moduleKey;
    moduleButton.classList.toggle("is-active", selected);
    moduleButton.setAttribute("aria-pressed", String(selected));
  });
  systemPrinciples.forEach((principle) => {
    const relatedModules = (principle.dataset.systemRelated ?? "").split(",");
    principle.classList.toggle("is-related", relatedModules.includes(moduleKey));
  });

  if (systemDetailIndex) systemDetailIndex.textContent = content.index;
  if (systemDetailKicker) systemDetailKicker.textContent = content.kicker;
  if (systemDetailTitle) systemDetailTitle.textContent = content.title;
  if (systemDetailText) systemDetailText.textContent = content.text;
  if (systemDetailTags) {
    systemDetailTags.replaceChildren(...content.tags.map((label) => {
      const tag = document.createElement("span");
      tag.textContent = label;
      return tag;
    }));
  }
}

systemModules.forEach((moduleButton) => {
  moduleButton.addEventListener("click", () => activateSystemModule(moduleButton.dataset.systemModule));
  moduleButton.addEventListener("focus", () => activateSystemModule(moduleButton.dataset.systemModule));
  moduleButton.addEventListener("pointerenter", (event) => {
    if (event.pointerType === "mouse") activateSystemModule(moduleButton.dataset.systemModule);
  });
});

activateSystemModule("airframe");

const architectureSection = document.getElementById("architecture");
const architectureTabs = Array.from(document.querySelectorAll("[data-architecture-layer]"));
const architecturePanel = document.querySelector(".architecture-panel");
const architectureNumber = document.getElementById("architectureNumber");
const architectureKicker = document.getElementById("architectureKicker");
const architecturePanelTitle = document.getElementById("architecturePanelTitle");
const architectureDescription = document.getElementById("architectureDescription");
const architectureStatus = document.getElementById("architectureStatus");
const architecturePoints = document.getElementById("architecturePoints");

const architectureContent = {
  airframe: {
    number: "01",
    kicker: "כלי טיס",
    title: "כלי טיס יעיל, מבוסס מסלול",
    description: "פלטפורמה בעלת מוטת כנף גדולה, המבוססת על פרופורציות Ximango, תומכת ביעד השהייה; הפעלה ממסלול מפשטת התאוששות, תחזוקה וניסויי טיסה חוזרים.",
    status: "בסיס התכן הוגדר · כפוף לתכן מפורט",
    points: ["חלוקה ניתנת להתאמה בין דלק למטען", "המראה ונחיתה ממסלול", "מסלול פיתוח מ־Block 0 ל־Block 1"]
  },
  flight: {
    number: "02",
    kicker: "מערכת טיסה",
    title: "בקרה קריטית לטיסה, המופרדת מיישומי המשימה",
    description: "בקרת הטיסה, ההנעה, ניהול החשמל וניטור בריאות כלי הטיס מטופלים כתחום בטיחות מוגן, שאינו תלוי ביישומי המשימה.",
    status: "הארכיטקטורה הוגדרה · בחירת החומרה בתהליך",
    points: ["חישה והפעלה יתירות", "מצבי פעולה מוגדרים בתנאי כשל", "ראיות לכשירות אווירית כחלק מהתכן"]
  },
  compute: {
    number: "03",
    kicker: "מחשוב משימה",
    title: "עיבוד על גבי כלי הטיס לחישה ולסיוע בקבלת החלטות",
    description: "שכבת מחשוב המשימה מיועדת לאחד נתוני מטענים, לתעדף מידע ולתמוך בניווט — ללא סמכות בלתי מוגבלת על פעולות קריטיות.",
    status: "קונספט תכן · אימות מעבדתי טרם בוצע",
    points: ["יישומי מטען מודולריים", "עיבוד קצה ואיחוי חיישנים", "סמכות אנושית בפעולות קריטיות"]
  },
  links: {
    number: "04",
    kicker: "קווי נתונים",
    title: "ערוצי תקשורת מרובים והתנהגות מוגדרת בעת אובדן קשר",
    description: "ארכיטקטורת התקשורת כוללת חלופות בקו ראייה ומעבר לקו ראייה, הצפנה, יתירות ותגובה צפויה כאשר הקישור נפגע.",
    status: "מערך החלופות הוגדר · נדרשת השלמת עבודה מול ספקים ורגולטורים",
    points: ["חלופות LOS ו־BLOS", "פיקוד וטלמטריה מוצפנים", "לוגיקה ניתנת לבדיקה בעת אובדן קשר"]
  },
  gcs: {
    number: "05",
    kicker: "בקרה קרקעית",
    title: "תמונה מבצעית אחודה לצוות מצומצם",
    description: "המקטע הקרקעי מתוכנן סביב תפקידי מפעיל ברורים, תמונת משימה אחת ונקודות אישור מפורשות לפעילות קריטית לבטיחות ולמשימה.",
    status: "קונספט ממשק אדם–מכונה · התכן המפורט טרם הושלם",
    points: ["תצוגת משימה אחודה", "סמכות מפעיל מבוססת תפקיד", "ממשקי אינטגרציה פתוחים"]
  }
};

function activateArchitectureLayer(layerKey) {
  const content = architectureContent[layerKey];
  if (!architectureSection || !content) return;

  architectureSection.dataset.architectureActive = layerKey;
  architectureTabs.forEach((tab) => {
    const selected = tab.dataset.architectureLayer === layerKey;
    tab.classList.toggle("is-active", selected);
    tab.setAttribute("aria-selected", String(selected));
  });

  if (architectureNumber) architectureNumber.textContent = content.number;
  if (architectureKicker) architectureKicker.textContent = content.kicker;
  if (architecturePanelTitle) architecturePanelTitle.textContent = content.title;
  if (architectureDescription) architectureDescription.textContent = content.description;
  if (architectureStatus) architectureStatus.textContent = content.status;
  if (architecturePoints) {
    architecturePoints.replaceChildren(...content.points.map((point) => {
      const item = document.createElement("li");
      item.textContent = point;
      return item;
    }));
  }

  architecturePanel?.classList.remove("is-changing");
  window.requestAnimationFrame(() => architecturePanel?.classList.add("is-changing"));
}

architectureTabs.forEach((tab) => {
  tab.addEventListener("click", () => activateArchitectureLayer(tab.dataset.architectureLayer));
  tab.addEventListener("focus", () => activateArchitectureLayer(tab.dataset.architectureLayer));
});

activateArchitectureLayer("airframe");

const model = document.getElementById("aircraftModel");
const modelStage = model?.closest(".hero-model");
const exposureControl = document.getElementById("modelExposure");
const lightingButtons = Array.from(document.querySelectorAll("[data-lighting-preset]"));
const modelHotspots = Array.from(model?.querySelectorAll(".model-hotspot") ?? []);
const modelFocusCard = document.getElementById("modelFocusCard");
const modelFocusStation = document.getElementById("modelFocusStation");
const modelFocusTitle = document.getElementById("modelFocusTitle");
const modelFocusText = document.getElementById("modelFocusText");
const modelFocusSpecs = document.getElementById("modelFocusSpecs");
const modelFocusNote = document.getElementById("modelFocusNote");
const modelOverviewControl = document.getElementById("modelOverviewControl");
const modelFocusOverview = document.getElementById("modelFocusOverview");
const modelStationsToggle = document.getElementById("modelStationsToggle");
const modelStationsToggleState = document.getElementById("modelStationsToggleState");
let activeModelComponent = null;
let modelFocusClickStage = 0;
let modelStationsVisible = true;
let activeLightingPreset = "studio";
let navigationBlinkTimer = null;
let navigationBlinkOn = false;

const modelFocusContent = {
  propeller: { station: "STA 01", title: "מערכת הנעה", text: "מדחף דו־להבי לבן בעל פיתול ופסיעה נראים; מישור הלהבים הוזז לאחור אל בסיס הכיפה הצמוד לבית המנוע." },
  datalink: { station: "STA 04", title: "קישור נתונים", text: "אנטנה קונפורמית לתקשורת מאובטחת ולרציפות משימה מעבר לקו הראייה." },
  landingGear: { station: "STA 05", title: "כן נסע ראשי", text: "כן נסע המחובר ברציפות לכנף עם חיפוי מוארך בצורת מגף, המסתיר את רוב הגלגל ומשאיר סהר קטן מהצמיג גלוי בתחתית." },
  wing: { station: "STA 06", title: "כנף למינרית", text: "כנף נמוכה וארוכת־מוטה. פרופיל רציף אחד ממשיך מקצה הכנף למעבר טרפזי העולה בכ־25 מעלות ומתעגל אל ה־winglet הטרפזי, ללא חפיפה, מכסה פנימי או שבירה במשטח. קווי המדפים והמאזנות מוטמעים במעטפת ואינם אלמנטים מוגבהים. עדשות הניווט ממוקמות בפינות החיצוניות ומהבהבות במצבי לילה והחשכה." },
  tail: { station: "STA 07", title: "מכלול זנב", text: "מכלול זנב T עם קווי ציר ברורים להגה הגובה ולהגה הכיוון וכן כן זנב קצר המחובר לגוף." },
  remoteWeapon: { station: "STA 08", title: "צריח קינטי EO/IR", text: "צריח מיוצב בקנה־מידה 0.75, הממוקם בשליש הקדמי של שורש הכנף. החיבור סגור, הברגים מוסתרים והקנה חלול ושקוע." },
  forwardCamera: { station: "STA 09", title: "מצלמת VR קדמית", text: "מערך חישה קדמי קטן וקונפורמי, הממוקם בגחון הקדמי לתמונת מצב ולהטסה מרחוק." },
  externalInterface: { station: "AUX 01", title: "בידוני דלק", text: "שני בידוני הדלק בקנה־מידה 0.8 מחוברים מתחת לכנפיים באמצעות פיילונים סגורים וצרים בעלי חתך אווירודינמי, שפת תקיפה מעוגלת ושורשים מתרחבים. הפיילונים חופפים מעט למעטפת הכנף והבידון כאובייקטים נפרדים ואינם משנים את ה־mesh של הכנף." },
  navigationLights: { station: "NAV 01", title: "תאורת ניווט", text: "עדשה אדומה בקצה כנף שמאל, עדשה ירוקה בקצה כנף ימין ועדשה לבנה הפונה לאחור. התאורה מופעלת במצבי לילה והחשכה." },
  ewResilience: { station: "EW 01", title: "שרידות בתנאי חסימה", text: "מצבי תגובה מוגדרים לאובדן קישור או חסימה: המשך מוגבל, חזרה בטוחה או המתנה, לצד הקלטה מקומית וניסיונות חידוש קשר." }
};

const lightingPresets = {
  studio: {
    environment: "../environments/studio-softbox-1k.hdr",
    skybox: null,
    exposure: 1.04,
    shadowIntensity: 1.08,
    shadowSoftness: 0.82
  },
  daylight: {
    environment: "../environments/daylight-noon-1k.hdr",
    skybox: "../environments/daylight-noon-1k.hdr",
    exposure: 0.96,
    shadowIntensity: 1.62,
    shadowSoftness: 0.34
  },
  sky: {
    environment: "../environments/sky-partly-cloudy-1k.hdr",
    skybox: "../environments/sky-partly-cloudy-1k.hdr",
    exposure: 1.02,
    shadowIntensity: 1.3,
    shadowSoftness: 0.6
  },
  golden: {
    environment: "../environments/golden-sunset-1k.hdr",
    skybox: "../environments/golden-sunset-1k.hdr",
    exposure: 1.02,
    shadowIntensity: 1.44,
    shadowSoftness: 0.5
  },
  night: {
    environment: "../environments/night-moonrise-1k.hdr",
    skybox: "../environments/night-moonrise-1k.hdr",
    exposure: 0.50,
    shadowIntensity: 0.48,
    shadowSoftness: 0.82
  },
  blackout: {
    environment: "../environments/night-moonrise-1k.hdr",
    skybox: "../environments/night-moonrise-1k.hdr",
    exposure: 0.26,
    shadowIntensity: 0.28,
    shadowSoftness: 0.90
  }
};

function setNavigationLights(on) {
  const materials = model?.model?.materials ?? [];
  materials.forEach((material) => {
    const isPort = material.name === "Port navigation lens";
    const isStarboard = material.name === "Starboard navigation lens";
    const isAft = material.name === "Aft navigation lens";
    if (!isPort && !isStarboard && !isAft) return;
    const color = isPort
      ? [1.0, 0.002, 0.001]
      : isStarboard
        ? [0.002, 1.0, 0.028]
        : [1.0, 1.0, 1.0];
    material.setEmissiveFactor(on ? color : [0, 0, 0]);
    if (typeof material.setEmissiveStrength === "function") {
      material.setEmissiveStrength(on ? 10.0 : 0.0);
    }
  });
}

function syncNavigationBlinking() {
  if (navigationBlinkTimer) {
    window.clearInterval(navigationBlinkTimer);
    navigationBlinkTimer = null;
  }
  const exposure = Number(model?.getAttribute("exposure") ?? 1);
  const sceneIsDark = activeLightingPreset === "night"
    || activeLightingPreset === "blackout"
    || exposure <= 0.56;
  if (!sceneIsDark || document.hidden) {
    navigationBlinkOn = false;
    setNavigationLights(false);
    return;
  }
  navigationBlinkOn = true;
  setNavigationLights(true);
  navigationBlinkTimer = window.setInterval(() => {
    navigationBlinkOn = !navigationBlinkOn;
    setNavigationLights(navigationBlinkOn);
  }, 680);
}

function applyLightingPreset(presetName) {
  if (!model || !lightingPresets[presetName]) return;
  const preset = lightingPresets[presetName];
  activeLightingPreset = presetName;
  model.setAttribute("environment-image", preset.environment);
  if (preset.skybox) model.setAttribute("skybox-image", preset.skybox);
  else model.removeAttribute("skybox-image");
  model.setAttribute("exposure", String(preset.exposure));
  model.setAttribute("shadow-intensity", String(preset.shadowIntensity));
  model.setAttribute("shadow-softness", String(preset.shadowSoftness));
  if (modelStage) modelStage.dataset.lighting = presetName;
  if (exposureControl) exposureControl.value = String(preset.exposure);
  lightingButtons.forEach((button) => {
    const selected = button.dataset.lightingPreset === presetName;
    button.classList.toggle("active", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
  syncNavigationBlinking();
}

lightingButtons.forEach((button) => {
  button.addEventListener("click", () => applyLightingPreset(button.dataset.lightingPreset));
});

exposureControl?.addEventListener("input", () => {
  if (!model) return;
  model.setAttribute("exposure", exposureControl.value);
  syncNavigationBlinking();
});

document.addEventListener("visibilitychange", syncNavigationBlinking);

function updateModelFocusCard() {
  if (!activeModelComponent || !modelFocusCard || !modelFocusTitle || !modelFocusText) return;
  const content = modelFocusContent[activeModelComponent];
  if (!content) return;
  if (modelFocusStation) modelFocusStation.textContent = content.station;
  modelFocusTitle.textContent = content.title;
  modelFocusTitle.dir = content.titleDirection ?? (content.specs?.length ? "ltr" : "rtl");
  modelFocusText.replaceChildren();
  modelFocusText.classList.toggle("has-rich-copy", Boolean(content.lead || content.bullets?.length));
  if (content.lead || content.bullets?.length) {
    if (content.lead) {
      const lead = document.createElement("span");
      lead.className = "model-focus-lead";
      lead.textContent = content.lead;
      modelFocusText.append(lead);
    }
    (content.bullets ?? []).forEach(([title, text]) => {
      const bullet = document.createElement("span");
      bullet.className = "model-focus-bullet";
      const heading = document.createElement("strong");
      heading.textContent = title;
      const body = document.createElement("span");
      body.textContent = text;
      bullet.append(heading, body);
      modelFocusText.append(bullet);
    });
    if (content.closingText) {
      const closing = document.createElement("span");
      closing.className = "model-focus-closing";
      closing.textContent = content.closingText;
      modelFocusText.append(closing);
    }
  } else {
    modelFocusText.textContent = content.text ?? "";
    if (content.secondaryText) {
      modelFocusText.append(document.createElement("br"), document.createElement("br"), content.secondaryText);
    }
  }
  if (modelFocusSpecs) {
    modelFocusSpecs.replaceChildren();
    modelFocusSpecs.dir = content.specsDirection ?? "rtl";
    (content.specs ?? []).forEach(([label, value]) => {
      const term = document.createElement("dt");
      const definition = document.createElement("dd");
      term.textContent = label;
      term.dir = /^[A-Za-z]/.test(label) ? "ltr" : "rtl";
      definition.textContent = value;
      definition.dir = "ltr";
      modelFocusSpecs.append(term, definition);
    });
    modelFocusSpecs.hidden = !content.specs?.length;
  }
  if (modelFocusNote) {
    modelFocusNote.textContent = content.note ?? "";
    modelFocusNote.hidden = !content.note;
  }
}

let hotspotDensityFrame = 0;

function updateHotspotDensity() {
  hotspotDensityFrame = 0;
  if (!model || !modelStage || typeof model.getCameraOrbit !== "function") return;
  const orbit = model.getCameraOrbit();
  const fieldOfView = model.getFieldOfView();
  const visibleHalfHeight = orbit.radius * Math.tan(fieldOfView * Math.PI / 360);
  const maximumLevel = visibleHalfHeight > 3.2 ? 1 : visibleHalfHeight > 1.35 ? 2 : 3;
  modelStage.dataset.hotspotDensity = maximumLevel === 1 ? "overview" : maximumLevel === 2 ? "systems" : "detail";
  modelHotspots.forEach((hotspot, index) => {
    const detailLevel = Number(hotspot.dataset.detailLevel ?? 1);
    const shouldShow = modelStationsVisible;
    hotspot.dataset.lod = detailLevel > maximumLevel ? "compact" : "full";
    const isActive = hotspot.dataset.component === activeModelComponent;
    const offsetRadius = isActive || maximumLevel === 3
      ? 0
      : maximumLevel === 1
        ? detailLevel === 1
          ? 5
          : detailLevel === 2
            ? 10
            : 14
        : detailLevel === 3 ? 8 : 3;
    const offsetAngle = index * 2.3999632297;
    hotspot.style.setProperty("--station-offset-x", `${Math.cos(offsetAngle) * offsetRadius}px`);
    hotspot.style.setProperty("--station-offset-y", `${Math.sin(offsetAngle) * offsetRadius}px`);
    hotspot.hidden = !shouldShow;
    hotspot.setAttribute("aria-hidden", String(!shouldShow));
  });
}

function scheduleHotspotDensityUpdate() {
  if (hotspotDensityFrame) return;
  hotspotDensityFrame = window.requestAnimationFrame(updateHotspotDensity);
}

function focusModelComponent(hotspot) {
  if (!model || !modelStationsVisible) return;
  const nextComponent = hotspot.dataset.component;
  const isRepeatedSelection = activeModelComponent === nextComponent;
  if (isRepeatedSelection && modelFocusClickStage === 1) {
    modelFocusClickStage = 2;
    updateModelFocusCard();
    if (modelFocusCard) {
      modelFocusCard.hidden = false;
      modelFocusCard.classList.remove("is-entering");
      void modelFocusCard.offsetWidth;
      modelFocusCard.classList.add("is-entering");
    }
    return;
  }
  if (isRepeatedSelection && modelFocusClickStage === 2) {
    resetModelOverview();
    return;
  }
  activeModelComponent = nextComponent;
  modelFocusClickStage = 1;
  hotspot.hidden = false;
  hotspot.setAttribute("aria-hidden", "false");
  model.removeAttribute("auto-rotate");
  model.setAttribute("camera-target", hotspot.dataset.target);
  model.setAttribute("camera-orbit", hotspot.dataset.orbit);
  model.setAttribute("field-of-view", "18deg");
  modelHotspots.forEach((button) => {
    const selected = button === hotspot;
    button.classList.toggle("active", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
  updateModelFocusCard();
  if (modelFocusCard) {
    modelFocusCard.hidden = true;
    modelFocusCard.classList.remove("is-entering");
  }
  scheduleHotspotDensityUpdate();
}

function setModelStationsVisibility(visible) {
  modelStationsVisible = visible;
  if (modelStage) modelStage.dataset.stationsVisible = String(visible);
  if (modelStationsToggle) {
    modelStationsToggle.classList.toggle("is-active", visible);
    modelStationsToggle.setAttribute("aria-pressed", String(visible));
  }
  if (modelStationsToggleState) modelStationsToggleState.textContent = visible ? "מוצג" : "מוסתר";

  if (!visible) {
    activeModelComponent = null;
    modelFocusClickStage = 0;
    modelHotspots.forEach((hotspot) => {
      hotspot.hidden = true;
      hotspot.classList.remove("active");
      hotspot.setAttribute("aria-hidden", "true");
      hotspot.setAttribute("aria-pressed", "false");
    });
    if (modelFocusCard) modelFocusCard.hidden = true;
  }

  scheduleHotspotDensityUpdate();
}

function resetModelOverview() {
  if (!model) return;
  activeModelComponent = null;
  modelFocusClickStage = 0;
  model.removeAttribute("auto-rotate");
  model.setAttribute("camera-target", "auto auto auto");
  model.setAttribute("camera-orbit", "-34deg 83deg 118%");
  model.setAttribute("field-of-view", "33deg");
  modelHotspots.forEach((button) => {
    button.classList.remove("active");
    button.setAttribute("aria-pressed", "false");
  });
  if (modelFocusCard) modelFocusCard.hidden = true;
  window.requestAnimationFrame(() => {
    if (typeof model.jumpCameraToGoal === "function") model.jumpCameraToGoal();
  });
  scheduleHotspotDensityUpdate();
}

modelHotspots.forEach((hotspot) => {
  hotspot.setAttribute("aria-pressed", "false");
  hotspot.addEventListener("click", (event) => {
    event.stopPropagation();
    focusModelComponent(hotspot);
  });
});

modelOverviewControl?.addEventListener("click", resetModelOverview);
modelFocusOverview?.addEventListener("click", resetModelOverview);
modelStationsToggle?.addEventListener("click", () => setModelStationsVisibility(!modelStationsVisible));

if (model) {
  model.addEventListener("camera-change", scheduleHotspotDensityUpdate);
  model.addEventListener("load", () => {
    const progress = model.querySelector(".model-progress");
    if (progress) progress.hidden = true;
    resetModelOverview();
    syncNavigationBlinking();
  });
}

if ("IntersectionObserver" in window && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("revealed");
      revealObserver.unobserve(entry.target);
    });
  }, { threshold: 0.12, rootMargin: "0px 0px -40px" });

  document.querySelectorAll("[data-reveal]").forEach((element) => revealObserver.observe(element));
} else {
  document.querySelectorAll("[data-reveal]").forEach((element) => element.classList.add("revealed"));
}

const year = document.getElementById("year");
if (year) year.textContent = String(new Date().getFullYear());
