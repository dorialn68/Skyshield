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
    kicker: "תקציר מנהלים",
    title: "ההשקעה",
    description: "כניסה מוקדמת למיזם המשלב פלטפורמה אווירית, מערכות משימה, AI וחימושים מתקדמים.",
    links: [["#investmentDetails", "עיקרי ההשקעה"], ["#modelFrame", "מודל 360°"]]
  },
  system: {
    kicker: "מערכת משולבת",
    title: "המערכת",
    description: "פלטפורמה, קישוריות, תחנת שליטה וממשק מפעיל המחוברים לתמונת מצב אחת.",
    links: [["#system", "עקרונות מפתח"], ["#system", "בקרה וקישוריות"]]
  },
  experience: {
    kicker: "תקדימים תעשייתיים",
    title: "ניסיון בהסבות",
    description: "דוגמאות בינלאומיות הממחישות מסלולי הסבה ואינטגרציה ממטוסים מאוישים למערכות בלתי מאוישות.",
    links: [["#experience", "Diamond DA 42"], ["#experience", "Long‑EZ"], ["#experience", "Avanti 180"]]
  },
  arit: {
    kicker: "שותפות אסטרטגית",
    title: "החיבור לארית",
    description: "חימוש, אלקטרוניקה ויכולת ייצור כחלק ממערכת אווירית מלאה עם נתיב ניסויים וצמיחה.",
    links: [["#arit", "מנועי הצמיחה"], ["#arit", "ערך ללקוח"]]
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

const model = document.getElementById("aircraftModel");
const modelStage = model?.closest(".hero-model");
const exposureControl = document.getElementById("modelExposure");
const lightingButtons = Array.from(document.querySelectorAll("[data-lighting-preset]"));
const modelHotspots = Array.from(model?.querySelectorAll(".model-hotspot") ?? []);
const modelFocusCard = document.getElementById("modelFocusCard");
const modelFocusStation = document.getElementById("modelFocusStation");
const modelFocusTitle = document.getElementById("modelFocusTitle");
const modelFocusText = document.getElementById("modelFocusText");
const modelOverviewControl = document.getElementById("modelOverviewControl");
const modelFocusOverview = document.getElementById("modelFocusOverview");
let activeModelComponent = null;

const modelFocusContent = {
  propeller: { station: "STA 01", title: "מערכת הנעה", text: "מדחף לבן בעל גאומטריה אווירודינמית, המשולב בחזית חיפוי המנוע." },
  engine: { station: "STA 02", title: "יחידת הנעה", text: "מעטפת מנוע קונפורמית המשמרת את קווי הגוף ואת הזרימה לאורך הפלטפורמה." },
  flightComputer: { station: "STA 03", title: "מחשב טיסה FCC", text: "ליבת בקרת הטיסה, הניווט והאוטונומיה של הפלטפורמה." },
  datalink: { station: "STA 04", title: "קישור נתונים", text: "אנטנה קונפורמית לתקשורת מאובטחת ולרציפות משימה מעבר לקו הראייה." },
  landingGear: { station: "STA 05", title: "כן נסע ראשי", text: "גלגל ראשי עם חיפוי אווירודינמי ותצורה התואמת לפלטפורמת Ximango." },
  wing: { station: "STA 06", title: "כנף למינרית", text: "כנף נמוכה וארוכת־מוטה, המיועדת ליעילות אווירודינמית ולשהייה ממושכת." },
  tail: { station: "STA 07", title: "מכלול זנב", text: "מכלול זנב עם כנפוני קצה וכּן זנב קצר, לשמירת קווי המתאר המקוריים." },
  remoteWeapon: { station: "STA 08", title: "צריח קינטי EO/IR", text: "צריח מיוצב המשלב חיישני EO/IR ומטען קינטי במעטפת קומפקטית ואווירודינמית." },
  forwardCamera: { station: "STA 09", title: "מצלמת VR קדמית", text: "מערך חישה קדמי קטן לתמונת מצב, הטסה מרחוק ותמיכה בתפיסת ההפעלה." },
  fuselageBay: { station: "STA 10", title: "תא משימה", text: "נפח משימה מאחורי הכנף עבור רחפנים, חימושים משוטטים ומטענים ייעודיים." },
  externalInterface: { station: "AUX 01", title: "בידוני דלק", text: "בידונים המחוברים ישירות לכנף ומרחיבים את מעטפת השהייה והטווח." }
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
    exposure: 1.12,
    shadowIntensity: 1.04,
    shadowSoftness: 0.7
  }
};

function applyLightingPreset(presetName) {
  if (!model || !lightingPresets[presetName]) return;
  const preset = lightingPresets[presetName];
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
}

lightingButtons.forEach((button) => {
  button.addEventListener("click", () => applyLightingPreset(button.dataset.lightingPreset));
});

exposureControl?.addEventListener("input", () => {
  model?.setAttribute("exposure", exposureControl.value);
});

function updateModelFocusCard() {
  if (!activeModelComponent || !modelFocusCard || !modelFocusTitle || !modelFocusText) return;
  const content = modelFocusContent[activeModelComponent];
  if (!content) return;
  if (modelFocusStation) modelFocusStation.textContent = content.station;
  modelFocusTitle.textContent = content.title;
  modelFocusText.textContent = content.text;
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
  modelHotspots.forEach((hotspot) => {
    const isActive = hotspot.dataset.component === activeModelComponent;
    const shouldShow = isActive || Number(hotspot.dataset.detailLevel ?? 1) <= maximumLevel;
    hotspot.hidden = !shouldShow;
    hotspot.setAttribute("aria-hidden", String(!shouldShow));
  });
}

function scheduleHotspotDensityUpdate() {
  if (hotspotDensityFrame) return;
  hotspotDensityFrame = window.requestAnimationFrame(updateHotspotDensity);
}

function focusModelComponent(hotspot) {
  if (!model) return;
  activeModelComponent = hotspot.dataset.component;
  hotspot.hidden = false;
  hotspot.setAttribute("aria-hidden", "false");
  model.removeAttribute("auto-rotate");
  model.cameraTarget = hotspot.dataset.target;
  model.cameraOrbit = hotspot.dataset.orbit;
  model.fieldOfView = "18deg";
  modelHotspots.forEach((button) => {
    const selected = button === hotspot;
    button.classList.toggle("active", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
  updateModelFocusCard();
  if (modelFocusCard) modelFocusCard.hidden = false;
  scheduleHotspotDensityUpdate();
}

function resetModelOverview() {
  if (!model) return;
  activeModelComponent = null;
  model.removeAttribute("auto-rotate");
  model.cameraTarget = "auto auto auto";
  model.cameraOrbit = "-34deg 83deg 118%";
  model.fieldOfView = "33deg";
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

if (model) {
  model.addEventListener("camera-change", scheduleHotspotDensityUpdate);
  model.addEventListener("load", () => {
    const progress = model.querySelector(".model-progress");
    if (progress) progress.hidden = true;
    resetModelOverview();
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
