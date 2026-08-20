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
      // Access remains valid for the current page when storage is restricted.
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
      status.textContent = "Enter the four-digit access code.";
      input.focus();
      return;
    }

    const submittedDigest = await digestAccessCode(input.value);
    if (submittedDigest !== ACCESS_CODE_DIGEST) {
      input.setAttribute("aria-invalid", "true");
      status.textContent = "Access code not recognized. Please try again.";
      input.select();
      return;
    }

    status.textContent = "Access granted.";
    document.getElementById("accessGate")?.classList.add("is-unlocking");
    window.setTimeout(() => grantPresentationAccess(true), 220);
  });

  window.requestAnimationFrame(() => input.focus());
}

initializeAccessGate();

const translations = {
  en: {
    pageTitle: "AirShield.AI | AI.onSuper Development Program",
    pageDescription: "AI.onSuper is AirShield.AI's development program for a runway-based, long-endurance unmanned aircraft system.",
    skip: "Skip to content",
    navPlatform: "Platform",
    navArchitecture: "Architecture",
    navPerformance: "Performance",
    navProgram: "Program",
    navTeam: "Team",
    menu: "Menu",
    heroEyebrow: "AI.onSuper development program",
    heroStatus: "Concept & engineering phase",
    heroTitle: "Long-endurance autonomy, built around the mission.",
    heroIntro: "AI.onSuper is AirShield.AI’s development program for a runway-based unmanned aircraft system. The design combines an efficient airframe, open mission architecture and human-authorized command for persistent ISR and special-mission payloads.",
    heroPrimary: "Explore the platform",
    heroSecondary: "Program overview",
    heroAlt: "Interactive 3D concept model of the AI.onSuper Ximango-derived unmanned aircraft",
    modelStatus: "Interactive 3D model",
    modelInstruction: "Drag for 360° · Zoom to reveal system stations",
    modelLighting: "Lighting",
    lightingStudio: "Studio",
    lightingDaylight: "Daylight",
    lightingSky: "Sky",
    lightingGolden: "Golden hour",
    lightingNight: "Night",
    lightingExposure: "Exposure",
    modelOverview: "360° overview",
    modelFocusOverview: "Return to 360° overview",
    componentFocus: "Component focus",
    hotspotPropeller: "Propeller",
    hotspotEngine: "Engine",
    hotspotFlightComputer: "Flight computer",
    hotspotDatalink: "Conformal datalink",
    hotspotLandingGear: "Main landing gear",
    hotspotWing: "Laminar wing",
    hotspotTail: "Tail group",
    hotspotRemoteWeapon: "Gimballed weapon station",
    hotspotForwardCamera: "Forward VR camera",
    hotspotFuselageBay: "Fuselage bay",
    hotspotExternalInterface: "External fuel tanks",
    focusPropellerTitle: "Propeller and spinner",
    focusPropellerText: "White-coated two-blade variable-pitch propeller envelope and spinner transition at the forward end of the Ximango-derived cowling.",
    focusEngineTitle: "Powerplant installation",
    focusEngineText: "The station identifies the engine-cowling volume and its changing cross-section; internal powerplant geometry is not shown.",
    focusFlightComputerTitle: "Flight control computer (FCC)",
    focusFlightComputerText: "Reserved avionics volume inside the forward fuselage beneath the uninterrupted upper skin; no crew cockpit or separate cover is represented.",
    focusDatalinkTitle: "Conformal datalink antenna",
    focusDatalinkText: "Flush dorsal antenna panel for the command, telemetry and mission-data link architecture, without a raised mast or hump.",
    focusLandingGearTitle: "Retractable Ximango-style main gear",
    focusLandingGearText: "Two main legs deploy perpendicular to the low wing through wing-integrated trunnion housings. Each continuous assembly has an aerodynamic closure door, wheel-well throat, twin axle fork, machined rim, brake disc and tire; there is no nose wheel.",
    focusWingTitle: "Laminar-flow wing",
    focusWingText: "Low-mounted, high-aspect-ratio wing with a continuous non-swollen center transition, restrained dihedral and upturned tips.",
    focusTailTitle: "Tail group",
    focusTailText: "T-tail assembly, control-surface break lines and a compact tail wheel carried by a structural shoe blended continuously into the aft fuselage.",
    focusRemoteWeaponTitle: "Gimballed remote weapon station",
    focusRemoteWeaponText: "Presentation-only compact station with an aerodynamic receiver shell, small yaw bearing, two-sided elevation trunnion and reduced forward barrel envelope.",
    focusForwardCameraTitle: "Forward VR navigation camera",
    focusForwardCameraText: "Small conformal dual-aperture visual-navigation camera integrated into the forward belly fairing; the former aft sensor ball has been removed.",
    focusFuselageBayTitle: "Open aft mission bay",
    focusFuselageBayText: "Aft-fuselage volume shown with downward-opening doors and neutral interchangeable cartridges for drone, loitering-system or directed-energy payload concepts; no operational internals are represented.",
    focusExternalInterfaceTitle: "External fuel tanks",
    focusExternalInterfaceText: "Two teardrop external fuel-tank visualizations are mechanically joined to continuous underwing pylons; internal fuel-system detail is not shown.",
    heroCaption: "Parametric concept model · Texture-baked military PBR surfaces · Ximango-derived proportions",
    targetsHeading: "Program targets",
    metricEnduranceValue: "50+ hr",
    metricEndurance: "Endurance target",
    metricPayloadValue: "450 kg",
    metricPayload: "Maximum payload objective",
    metricAltitudeValue: "30,000+ ft",
    metricAltitude: "Growth objective",
    metricCruiseValue: "150–170 KTAS",
    metricCruise: "Planned cruise",
    statusNoteLabel: "A note on status",
    statusNoteText: "AI.onSuper is a development program. Throughout this site, reference-aircraft data, current design assumptions and future performance objectives are identified separately.",
    approachEyebrow: "Design approach",
    approachTitle: "One air vehicle. A deliberate system architecture.",
    approachIntro: "The platform is being developed as an integrated system: flight-critical functions remain separated from mission applications, payload interfaces stay modular and operator authority is defined from the outset.",
    cardAirTitle: "Air vehicle",
    cardAirText: "A long-span, runway-based aircraft with a configurable balance between fuel and mission payload.",
    cardMissionTitle: "Mission architecture",
    cardMissionText: "Open interfaces keep payload compute and mission applications separate from flight-critical control.",
    cardControlTitle: "Command & control",
    cardControlText: "Line-of-sight and beyond-line-of-sight communications are planned with redundant paths and defined lost-link behavior.",
    cardHumanTitle: "Human authority",
    cardHumanText: "Autonomous functions support navigation, sensing and decision support. Critical actions remain under designated operator authority.",
    architectureEyebrow: "System architecture",
    architectureTitle: "Explore the system, layer by layer.",
    architectureIntro: "Select a layer to review its role, current program status and design principles. The content distinguishes defined architecture from items that still require validation.",
    tabAirframe: "Air vehicle",
    tabFlight: "Flight system",
    tabCompute: "Mission compute",
    tabLinks: "Data links",
    tabGcs: "Ground control",
    performanceEyebrow: "Planning baseline",
    performanceTitle: "Reference aircraft and Block 1 objectives.",
    performanceIntro: "Block 0 establishes the flight-test baseline using a converted reference aircraft. Block 1 is the production-intent design objective built around the same general geometry.",
    tableCaption: "Comparison of Block 0 reference aircraft planning data and Block 1 design objectives",
    tableParameter: "Parameter",
    tableBlock0: "Reference aircraft",
    tableBlock1: "Design objective",
    rowEngine: "Engine",
    b0Engine: "Rotax 914 F3 · 115 hp take-off",
    b1Engine: "Rotax 916 iS/iSc · 160 hp target",
    rowMtow: "Maximum take-off mass",
    b0Mtow: "1,000 kg planning baseline",
    b1Mtow: "1,200 kg design target",
    rowMass: "Platform mass",
    b0Mass: "Approximately 540 kg · planning estimate",
    b1Mass: "500 kg target",
    rowCapacity: "Fuel and payload",
    b0Capacity: "250 kg fuel + approximately 210 kg payload",
    b1Capacity: "Configurable within 700 kg useful mass",
    rowCruise: "Cruise",
    b0Cruise: "105–120 KTAS estimate",
    b1Cruise: "150–170 KTAS objective",
    rowAltitude: "Operating altitude",
    b0Altitude: "20,000–26,000 ft class",
    b1Altitude: "23,000 ft baseline · above 30,000 ft growth objective",
    rowEndurance: "Endurance",
    b0Endurance: "28+ hr analytical estimate",
    b1Endurance: "Up to 50 hr engineering objective",
    rowStatus: "Configuration status",
    b0Status: "Converted reference aircraft",
    b1Status: "Production-intent design",
    performanceNote: "Values are management engineering estimates. They are not certified performance data and remain subject to detailed design, supplier confirmation, ground test, flight test, airworthiness and regulatory approval.",
    assuranceEyebrow: "Operational assurance",
    assuranceTitle: "Autonomy requires boundaries that can be explained and tested.",
    assuranceHumanTitle: "Defined authority",
    assuranceHumanText: "Critical operations remain subject to designated human authorization and mission rules.",
    assuranceLossTitle: "Predictable degradation",
    assuranceLossText: "Lost-link and degraded-navigation behavior must be designed, tested and documented before flight release.",
    assuranceSeparateTitle: "Separated responsibilities",
    assuranceSeparateText: "Flight-critical control is isolated from payload applications and mission-level decision support.",
    assuranceEvidenceTitle: "Evidence before claims",
    assuranceEvidenceText: "Assumptions, objectives and validated results are presented as different categories.",
    programEyebrow: "Development program",
    programTitle: "An 18-month path from baseline to flight demonstration.",
    programIntro: "The program sequence moves from requirements and interface control through ground integration to a controlled flight-test campaign.",
    phase1Title: "Baseline & requirements",
    phase1Text: "Reference-aircraft acquisition, requirements freeze, safety planning and interface control.",
    phase2Title: "Preliminary design",
    phase2Text: "Structural and electrical adaptations, communications architecture and ground-control definition.",
    phase3Title: "Critical design & ground test",
    phase3Text: "Critical design review, mission-compute bench testing and payload integration.",
    phase4Title: "System integration",
    phase4Text: "Full ground runs and integrated demonstrations of sensors, control and data links.",
    phase5Title: "Flight validation",
    phase5Text: "First flight, envelope expansion and an integrated system demonstration.",
    programNote: "Timing is a planning objective and depends on funding, supplier availability, permits, airworthiness activity and test approvals.",
    capitalLabel: "Program capital objective",
    capitalBasis: "Management planning basis",
    capitalEyebrow: "Capital plan",
    capitalTitle: "Funding converts the engineering baseline into hardware and flight evidence.",
    capitalText: "The current objective covers aircraft acquisition, engineering, integration, ground testing, first flight and the transition toward the Block 1 design. Financing and equity terms are not presented on this public overview.",
    capitalItem1: "Reference aircraft and propulsion",
    capitalItem2: "Engineering and system integration",
    capitalItem3: "Ground control and communications",
    capitalItem4: "Ground and flight-test activity",
    teamEyebrow: "Leadership",
    teamTitle: "Experience across aviation, engineering and applied AI.",
    teamCommand: "Program",
    teamEngineering: "Engineering",
    teamAutonomy: "AI & autonomy",
    avielRole: "Co-founder & CEO · Lt. Col. (Res.), IAF",
    avielBio: "Three decades across UAV and defense programs, including propulsion leadership at Aeronautics and work with Israel’s Ministry of Defense and DDR&D.",
    kobiRole: "Co-founder & CTO · Maj. (Res.), IAF",
    kobiBio: "Three decades in mechanical, software and UAV engineering across Elbit, Silver Arrow and BlueBird.",
    doronRole: "Co-founder & AI lead",
    doronBio: "Three decades in AI, data and software infrastructure across Texas Instruments, Samsung and Cybereason.",
    closingEyebrow: "Qualified discussions",
    closingTitle: "Detailed engineering and investment materials are available through the AirShield.AI team.",
    closingText: "This public overview is intentionally limited. Technical work breakdowns, cost assumptions and integration detail should be reviewed in a controlled discussion.",
    footerTagline: "Long-endurance unmanned systems · Development program",
    backTop: "Back to top ↑",
    footerLegal: "AI.onSuper is a development program. Configuration, schedule, pricing, performance and availability may change. Nothing on this site constitutes product certification, an operational claim, a securities offer or a binding commitment."
  },
  he: {
    pageTitle: "AirShield.AI | תוכנית הפיתוח AI.onSuper",
    pageDescription: "AI.onSuper היא תוכנית הפיתוח של AirShield.AI למערכת כלי טיס בלתי מאוישת, מבוססת מסלול, לשהייה ממושכת.",
    skip: "דלגו לתוכן",
    navPlatform: "פלטפורמה",
    navArchitecture: "ארכיטקטורה",
    navPerformance: "יעדי ביצועים",
    navProgram: "תוכנית",
    navTeam: "צוות",
    menu: "תפריט",
    heroEyebrow: "תוכנית הפיתוח AI.onSuper",
    heroStatus: "שלב קונספט ותכן הנדסי",
    heroTitle: "פלטפורמה בלתי מאוישת לשהייה ממושכת, המותאמת למשימה.",
    heroIntro: "AI.onSuper היא תוכנית הפיתוח של AirShield.AI למערכת כלי טיס בלתי מאוישת, מבוססת מסלול, לשהייה ממושכת. התכן משלב כלי טיס אווירודינמי יעיל, ארכיטקטורת משימה פתוחה ופיקוד בסמכות אנושית עבור משימות מודיעין, תצפית וסיור מתמשכות ומטענים ייעודיים.",
    heroPrimary: "להכרת הפלטפורמה",
    heroSecondary: "סקירת התוכנית",
    heroAlt: "מודל תלת־ממד אינטראקטיבי של קונספט AI.onSuper, המבוסס על פרופורציות Ximango",
    modelStatus: "מודל תלת־ממד אינטראקטיבי",
    modelInstruction: "גררו לצפייה ב־360° · קרבו כדי לחשוף תחנות מערכת",
    modelLighting: "תאורה",
    lightingStudio: "סטודיו",
    lightingDaylight: "אור יום",
    lightingSky: "שמים",
    lightingGolden: "שעת זהב",
    lightingNight: "לילה",
    lightingExposure: "חשיפה",
    modelOverview: "סקירת 360°",
    modelFocusOverview: "חזרה לתצוגת 360°",
    componentFocus: "מיקוד ברכיב",
    hotspotPropeller: "מדחף",
    hotspotEngine: "מנוע",
    hotspotFlightComputer: "מחשב טיסה",
    hotspotDatalink: "אנטנת קישור נתונים קונפורמית",
    hotspotLandingGear: "כני נסע ראשיים",
    hotspotWing: "כנף למינרית",
    hotspotTail: "מכלול זנב",
    hotspotRemoteWeapon: "עמדת נשק מגומבלת",
    hotspotForwardCamera: "מצלמת VR קדמית",
    hotspotFuselageBay: "תא משימה בגוף",
    hotspotExternalInterface: "בידוני דלק חיצוניים",
    focusPropellerTitle: "מדחף וכיפה קדמית",
    focusPropellerText: "מעטפת של מדחף דו־להבי לבן בעל פסיעה משתנה והמעבר אל בית המנוע המבוסס על פרופורציות Ximango.",
    focusEngineTitle: "התקנת מערכת ההנעה",
    focusEngineText: "התחנה מסמנת את נפח בית המנוע ואת החתך המשתנה שלו; גאומטריית המנוע הפנימית אינה מוצגת.",
    focusFlightComputerTitle: "מחשב בקרת טיסה (FCC)",
    focusFlightComputerText: "נפח אוויוניקה שמור בתוך הגוף הקדמי ומתחת למעטפת העליונה הרציפה; לא מוצגים תא טייס או חיפוי נפרד.",
    focusDatalinkTitle: "אנטנת קישור נתונים קונפורמית",
    focusDatalinkText: "לוח אנטנה גבי שטוח עבור ארכיטקטורת פיקוד, טלמטריה ונתוני משימה, ללא תורן או גיבנת בולטת.",
    focusLandingGearTitle: "כני נסע ראשיים נשלפים בתצורת Ximango",
    focusLandingGearText: "שני כני הנסע יורדים בניצב לכנף הנמוכה דרך בתי ציר המשולבים במבנה הכנף. כל מכלול רציף וכולל דלת חיפוי אווירודינמית, פתח כן נסע, מזלג כפול, חישוק, דיסק בלם וצמיג; אין כן נסע קדמי.",
    focusWingTitle: "כנף בזרימה למינרית",
    focusWingText: "כנף נמוכה בעלת מנת־ממדים גבוהה, מעבר מרכזי רציף שאינו מעובה, דיהדרל מתון וקצות כנף מורמים.",
    focusTailTitle: "מכלול הזנב",
    focusTailText: "מכלול זנב בתצורת T, קווי משטחי היגוי וכן נסע זנבי קצר המחובר באמצעות תושבת מבנית המשולבת ברציפות בגוף האחורי.",
    focusRemoteWeaponTitle: "עמדת נשק מרחוק מגומבלת",
    focusRemoteWeaponText: "גאומטריה חיצונית להמחשה בלבד של עמדה קומפקטית, עם מעטפת אווירודינמית, מיסב אזימוט קטן, ציר הטיה דו־צדדי ומעטפת קנה קדמית מצומצמת.",
    focusForwardCameraTitle: "מצלמת ניווט VR קדמית",
    focusForwardCameraText: "מצלמת ניווט חזותית קטנה בעלת שני פתחים, המשולבת בחיפוי הגחון הקדמי; כדור החיישנים האחורי הוסר.",
    focusFuselageBayTitle: "תא משימה אחורי פתוח",
    focusFuselageBayText: "נפח בגוף האחורי המוצג עם דלתות הנפתחות כלפי מטה ומחסניות מודולריות ניטרליות לקונספטים של רחפנים, חימוש משוטט או מטעני אנרגיה מכוונת; לא מוצגים פרטים מבצעיים.",
    focusExternalInterfaceTitle: "בידוני דלק חיצוניים",
    focusExternalInterfaceText: "שני בידוני דלק חיצוניים בעלי מעטפת טיפתית מחוברים באופן רציף למתלים שמתחת לכנפיים; פרטי מערכת הדלק הפנימית אינם מוצגים.",
    heroCaption: "מודל קונספט פרמטרי · משטחי PBR צבאיים עם אפיית טקסטורות · פרופורציות המבוססות על Ximango",
    targetsHeading: "יעדי תוכנית",
    metricEnduranceValue: "50+ שעות",
    metricEndurance: "יעד שהייה באוויר",
    metricPayloadValue: "450 ק״ג",
    metricPayload: "יעד מטען מרבי",
    metricAltitudeValue: "מעל 30,000 רגל",
    metricAltitude: "יעד פיתוח",
    metricCruiseValue: "150–170 קשר TAS",
    metricCruise: "מהירות שיוט מתוכננת",
    statusNoteLabel: "הבהרה לגבי הסטטוס",
    statusNoteText: "AI.onSuper היא תוכנית בפיתוח. לאורך האתר מוצגים בנפרד נתוני כלי הטיס לייחוס, הנחות התכן הנוכחיות ויעדי הביצועים העתידיים.",
    approachEyebrow: "גישת תכן",
    approachTitle: "כלי טיס אחד. ארכיטקטורת מערכת סדורה.",
    approachIntro: "הפלטפורמה מפותחת כמערכת משולבת: פונקציות קריטיות לטיסה מופרדות מיישומי המשימה, ממשקי המטען נשארים מודולריים וסמכות המפעיל מוגדרת מראשית התוכנית.",
    cardAirTitle: "כלי טיס",
    cardAirText: "כלי טיס בעל מוטת כנף גדולה, מבוסס מסלול, עם חלוקה ניתנת להתאמה בין דלק למטען משימה.",
    cardMissionTitle: "ארכיטקטורת משימה",
    cardMissionText: "ממשקים פתוחים מפרידים בין מחשוב המטען ויישומי המשימה לבין מערכות הבקרה הקריטיות לטיסה.",
    cardControlTitle: "שליטה ובקרה",
    cardControlText: "תקשורת בקו ראייה ומעבר לקו ראייה מתוכננת עם ערוצים יתירים והתנהגות מוגדרת במקרה של אובדן קשר.",
    cardHumanTitle: "סמכות אנושית",
    cardHumanText: "פונקציות אוטונומיות תומכות בניווט, חישה וסיוע בקבלת החלטות. פעולות קריטיות נשארות בסמכות מפעיל שהוגדר לכך.",
    architectureEyebrow: "ארכיטקטורת מערכת",
    architectureTitle: "הכירו את המערכת, שכבה אחר שכבה.",
    architectureIntro: "בחרו שכבה כדי לבחון את תפקידה, את הסטטוס הנוכחי בתוכנית ואת עקרונות התכן. התוכן מבחין בין ארכיטקטורה שכבר הוגדרה לבין רכיבים שעדיין דורשים אימות.",
    tabAirframe: "כלי טיס",
    tabFlight: "מערכת טיסה",
    tabCompute: "מחשוב משימה",
    tabLinks: "קווי נתונים",
    tabGcs: "בקרה קרקעית",
    performanceEyebrow: "בסיס תכנון",
    performanceTitle: "כלי הטיס לייחוס ויעדי Block 1.",
    performanceIntro: "Block 0 קובע את בסיס ניסויי הטיסה באמצעות הסבת כלי טיס קיים. Block 1 הוא יעד התכן לגרסה המיועדת לייצור, המבוססת על אותה גאומטריה כללית.",
    tableCaption: "השוואה בין נתוני התכנון של כלי הטיס לייחוס ב־Block 0 לבין יעדי התכן של Block 1",
    tableParameter: "פרמטר",
    tableBlock0: "כלי טיס לייחוס",
    tableBlock1: "יעד תכן",
    rowEngine: "מנוע",
    b0Engine: "Rotax 914 F3 · ‏115 כ״ס בהמראה",
    b1Engine: "Rotax 916 iS/iSc · יעד של 160 כ״ס",
    rowMtow: "משקל המראה מרבי",
    b0Mtow: "1,000 ק״ג · בסיס תכנון",
    b1Mtow: "1,200 ק״ג · יעד תכן",
    rowMass: "משקל הפלטפורמה",
    b0Mass: "כ־540 ק״ג · אומדן תכנוני",
    b1Mass: "יעד של 500 ק״ג",
    rowCapacity: "דלק ומטען",
    b0Capacity: "250 ק״ג דלק + כ־210 ק״ג מטען",
    b1Capacity: "חלוקה ניתנת להתאמה בתוך 700 ק״ג משקל שימושי",
    rowCruise: "שיוט",
    b0Cruise: "אומדן של 105–120 קשר TAS",
    b1Cruise: "יעד של 150–170 קשר TAS",
    rowAltitude: "גובה הפעלה",
    b0Altitude: "קטגוריית 20,000–26,000 רגל",
    b1Altitude: "23,000 רגל בבסיס · יעד פיתוח מעל 30,000 רגל",
    rowEndurance: "שהייה באוויר",
    b0Endurance: "אומדן אנליטי של 28+ שעות",
    b1Endurance: "יעד הנדסי של עד 50 שעות",
    rowStatus: "סטטוס תצורה",
    b0Status: "הסבה של כלי טיס קיים",
    b1Status: "תכן המיועד לייצור",
    performanceNote: "הנתונים הם אומדנים הנדסיים של הנהלת התוכנית. אין מדובר בנתוני ביצועים מאושרים, והם כפופים לתכן מפורט, לאישור ספקים, לבדיקות קרקע וטיסה, לכשירות אווירית ולאישור רגולטורי.",
    assuranceEyebrow: "הבטחה תפעולית",
    assuranceTitle: "אוטונומיה מחייבת גבולות שאפשר להסביר ולבדוק.",
    assuranceHumanTitle: "סמכות מוגדרת",
    assuranceHumanText: "פעולות קריטיות כפופות לאישור אנושי שהוגדר מראש ולכללי המשימה.",
    assuranceLossTitle: "התנהגות צפויה בתנאי כשל",
    assuranceLossText: "התנהגות בעת אובדן קשר או פגיעה בניווט חייבת להיות מתוכננת, מתועדת ונבדקת לפני שחרור לטיסה.",
    assuranceSeparateTitle: "הפרדת אחריות",
    assuranceSeparateText: "בקרת הטיסה הקריטית מבודדת מיישומי המטען ומסיוע בקבלת החלטות ברמת המשימה.",
    assuranceEvidenceTitle: "ראיות לפני הצהרות",
    assuranceEvidenceText: "הנחות, יעדים ותוצאות שאומתו מוצגים כקטגוריות נפרדות.",
    programEyebrow: "תוכנית פיתוח",
    programTitle: "מסלול של 18 חודשים מבסיס התכן להדגמה בטיסה.",
    programIntro: "רצף התוכנית מתקדם מהגדרת דרישות ובקרת ממשקים, דרך אינטגרציה קרקעית, ועד מסע ניסויי טיסה מבוקר.",
    phase1Title: "בסיס תכן ודרישות",
    phase1Text: "רכש כלי הטיס לייחוס, הקפאת דרישות, תכנון בטיחות ובקרת ממשקים.",
    phase2Title: "תכן ראשוני",
    phase2Text: "התאמות מבניות וחשמליות, ארכיטקטורת תקשורת והגדרת תחנת הבקרה הקרקעית.",
    phase3Title: "תכן קריטי ובדיקות קרקע",
    phase3Text: "סקר תכן קריטי, בדיקות מעבדה למחשב המשימה ואינטגרציית מטענים.",
    phase4Title: "אינטגרציית מערכת",
    phase4Text: "הרצות קרקע מלאות והדגמות משולבות של חיישנים, בקרה וקווי נתונים.",
    phase5Title: "אימות בטיסה",
    phase5Text: "טיסה ראשונה, הרחבת מעטפת הטיסה והדגמה משולבת של המערכת.",
    programNote: "לוחות הזמנים הם יעד תכנוני ותלויים במימון, בזמינות ספקים, בהיתרים, בפעילות כשירות אווירית ובאישורי ניסוי.",
    capitalLabel: "יעד ההון לתוכנית",
    capitalBasis: "בסיס תכנון של ההנהלה",
    capitalEyebrow: "תוכנית הון",
    capitalTitle: "המימון הופך את הבסיס ההנדסי לחומרה ולראיות מטיסה.",
    capitalText: "היעד הנוכחי כולל רכש כלי טיס, הנדסה, אינטגרציה, בדיקות קרקע, טיסה ראשונה והתקדמות לעבר תכן Block 1. תנאי המימון וההון אינם מוצגים בסקירה ציבורית זו.",
    capitalItem1: "כלי טיס לייחוס ומערכת הנעה",
    capitalItem2: "הנדסה ואינטגרציית מערכת",
    capitalItem3: "בקרה קרקעית ותקשורת",
    capitalItem4: "בדיקות קרקע וניסויי טיסה",
    teamEyebrow: "הנהלה",
    teamTitle: "ניסיון מצטבר בתעופה, בהנדסה ובבינה מלאכותית יישומית.",
    teamCommand: "תוכנית",
    teamEngineering: "הנדסה",
    teamAutonomy: "בינה מלאכותית ואוטונומיה",
    avielRole: "מייסד שותף ומנכ״ל · סא״ל (מיל׳), חיל האוויר",
    avielBio: "שלושה עשורים בתוכניות כלי טיס בלתי מאוישים וביטחון, לרבות ניהול תחום ההנעה באירונאוטיקס ועבודה מול משרד הביטחון ומפא״ת.",
    kobiRole: "מייסד שותף וסמנכ״ל טכנולוגיות · רס״ן (מיל׳), חיל האוויר",
    kobiBio: "שלושה עשורים בהנדסת מכונות, תוכנה וכלי טיס בלתי מאוישים באלביט, Silver Arrow ו־BlueBird.",
    doronRole: "מייסד שותף ומוביל תחום הבינה המלאכותית",
    doronBio: "שלושה עשורים בבינה מלאכותית, נתונים ותשתיות תוכנה ב־Texas Instruments, Samsung ו־Cybereason.",
    closingEyebrow: "שיחות מקצועיות",
    closingTitle: "חומרי הנדסה והשקעה מפורטים זמינים באמצעות צוות AirShield.AI.",
    closingText: "הסקירה הציבורית מוגבלת במכוון. יש לבחון פירוט עבודה טכני, הנחות עלות ופרטי אינטגרציה במסגרת שיחה מבוקרת.",
    footerTagline: "מערכות בלתי מאוישות לשהייה ממושכת · תוכנית בפיתוח",
    backTop: "חזרה לראש העמוד ↑",
    footerLegal: "AI.onSuper היא תוכנית בפיתוח. התצורה, לוחות הזמנים, התמחור, הביצועים והזמינות עשויים להשתנות. אין באתר זה משום אישור מוצר, טענה מבצעית, הצעה לניירות ערך או התחייבות מחייבת."
  }
};

const systemContent = {
  en: {
    airframe: {
      number: "01",
      kicker: "AIR VEHICLE",
      title: "Efficient runway-based air vehicle",
      description: "A Ximango-derived, long-span airframe supports the endurance objective while conventional runway operations simplify recovery, servicing and repeatable flight test.",
      statusLabel: "Program status",
      status: "Baseline defined · subject to detailed design",
      points: ["Configurable fuel and payload trade", "Runway take-off and landing", "Block 0 to Block 1 development path"]
    },
    flight: {
      number: "02",
      kicker: "FLIGHT SYSTEM",
      title: "Separated, flight-critical control",
      description: "Flight control, actuation, power management and vehicle health monitoring are treated as a protected safety domain, independent of mission applications.",
      statusLabel: "Program status",
      status: "Architecture defined · hardware selection in progress",
      points: ["Redundant sensing and actuation", "Defined degraded modes", "Airworthiness evidence by design"]
    },
    compute: {
      number: "03",
      kicker: "MISSION COMPUTE",
      title: "Onboard processing for sensing and decision support",
      description: "The mission-compute layer is intended to fuse payload data, prioritize information and support navigation without giving unrestricted authority over critical actions.",
      statusLabel: "Program status",
      status: "Design concept · bench validation pending",
      points: ["Modular payload applications", "Edge processing and sensor fusion", "Human authority for critical actions"]
    },
    links: {
      number: "04",
      kicker: "DATA LINKS",
      title: "Multiple paths with defined lost-link behavior",
      description: "The communications architecture considers line-of-sight and beyond-line-of-sight channels, encryption, redundancy and a predictable response when connectivity is degraded.",
      statusLabel: "Program status",
      status: "Option set defined · supplier and regulatory work pending",
      points: ["LOS and BLOS options", "Encrypted command and telemetry", "Testable lost-link logic"]
    },
    gcs: {
      number: "05",
      kicker: "GROUND CONTROL",
      title: "A unified operational picture for a small crew",
      description: "The ground segment is planned around clear operator roles, one mission picture and explicit authorization points for safety-critical and mission-critical activity.",
      statusLabel: "Program status",
      status: "Human-machine concept · detailed design pending",
      points: ["Unified mission display", "Role-based operator authority", "Open integration interfaces"]
    }
  },
  he: {
    airframe: {
      number: "01",
      kicker: "כלי טיס",
      title: "כלי טיס יעיל, מבוסס מסלול",
      description: "פלטפורמה בעלת מוטת כנף גדולה, המבוססת על פרופורציות Ximango, תומכת ביעד השהייה; הפעלה ממסלול מפשטת התאוששות, תחזוקה וניסויי טיסה חוזרים.",
      statusLabel: "סטטוס תוכנית",
      status: "בסיס התכן הוגדר · כפוף לתכן מפורט",
      points: ["חלוקה ניתנת להתאמה בין דלק למטען", "המראה ונחיתה ממסלול", "מסלול פיתוח מ־Block 0 ל־Block 1"]
    },
    flight: {
      number: "02",
      kicker: "מערכת טיסה",
      title: "בקרה קריטית לטיסה, המופרדת מיישומי המשימה",
      description: "בקרת הטיסה, ההנעה, ניהול החשמל וניטור בריאות כלי הטיס מטופלים כתחום בטיחות מוגן, שאינו תלוי ביישומי המשימה.",
      statusLabel: "סטטוס תוכנית",
      status: "הארכיטקטורה הוגדרה · בחירת החומרה בתהליך",
      points: ["חישה והפעלה יתירות", "מצבי פעולה מוגדרים בתנאי כשל", "ראיות לכשירות אווירית כחלק מהתכן"]
    },
    compute: {
      number: "03",
      kicker: "מחשוב משימה",
      title: "עיבוד על גבי כלי הטיס לחישה ולסיוע בקבלת החלטות",
      description: "שכבת מחשוב המשימה מיועדת לאחד נתוני מטענים, לתעדף מידע ולתמוך בניווט — ללא סמכות בלתי מוגבלת על פעולות קריטיות.",
      statusLabel: "סטטוס תוכנית",
      status: "קונספט תכן · אימות מעבדתי טרם בוצע",
      points: ["יישומי מטען מודולריים", "עיבוד קצה ואיחוי חיישנים", "סמכות אנושית בפעולות קריטיות"]
    },
    links: {
      number: "04",
      kicker: "קווי נתונים",
      title: "ערוצי תקשורת מרובים והתנהגות מוגדרת בעת אובדן קשר",
      description: "ארכיטקטורת התקשורת כוללת חלופות בקו ראייה ומעבר לקו ראייה, הצפנה, יתירות ותגובה צפויה כאשר הקישור נפגע.",
      statusLabel: "סטטוס תוכנית",
      status: "מערך החלופות הוגדר · נדרשת השלמת עבודה מול ספקים ורגולטורים",
      points: ["חלופות LOS ו־BLOS", "פיקוד וטלמטריה מוצפנים", "לוגיקה ניתנת לבדיקה בעת אובדן קשר"]
    },
    gcs: {
      number: "05",
      kicker: "בקרה קרקעית",
      title: "תמונה מבצעית אחודה לצוות מצומצם",
      description: "המקטע הקרקעי מתוכנן סביב תפקידי מפעיל ברורים, תמונת משימה אחת ונקודות אישור מפורשות לפעילות קריטית לבטיחות ולמשימה.",
      statusLabel: "סטטוס תוכנית",
      status: "קונספט ממשק אדם–מכונה · התכן המפורט טרם הושלם",
      points: ["תצוגת משימה אחודה", "סמכות מפעיל מבוססת תפקיד", "ממשקי אינטגרציה פתוחים"]
    }
  }
};

let language = "en";
let activeSystem = "airframe";

const languageToggle = document.getElementById("languageToggle");
const menuToggle = document.getElementById("menuToggle");
const mobileNav = document.getElementById("mobileNav");
const systemTabs = Array.from(document.querySelectorAll(".architecture-tab"));
const architecturePanel = document.querySelector(".architecture-panel");
const siteHeader = document.querySelector(".site-header");

function applyLanguage(nextLanguage) {
  language = nextLanguage;
  const dictionary = translations[language];
  document.documentElement.lang = language;
  document.documentElement.dir = language === "he" ? "rtl" : "ltr";
  document.title = dictionary.pageTitle;

  const description = document.querySelector('meta[name="description"]');
  if (description) description.setAttribute("content", dictionary.pageDescription);

  document.querySelectorAll("[data-i18n]").forEach((element) => {
    const key = element.dataset.i18n;
    if (dictionary[key] !== undefined) element.textContent = dictionary[key];
  });

  document.querySelectorAll("[data-i18n-alt]").forEach((element) => {
    const key = element.dataset.i18nAlt;
    if (dictionary[key] !== undefined) element.setAttribute("alt", dictionary[key]);
  });

  languageToggle.querySelector(".lang-current").textContent = language === "en" ? "EN" : "עברית";
  languageToggle.querySelector(".lang-next").textContent = language === "en" ? "עברית" : "EN";
  languageToggle.setAttribute("aria-label", language === "en" ? "Switch to Hebrew" : "Switch to English");

  renderSystem(activeSystem);
  updateModelFocusCard();

  try {
    localStorage.setItem("airshield-language", language);
  } catch (_) {
    // Language persistence is optional.
  }
}

function renderSystem(systemName) {
  activeSystem = systemName;
  const data = systemContent[language][systemName];
  document.getElementById("panelNumber").textContent = data.number;
  document.getElementById("panelKicker").textContent = data.kicker;
  document.getElementById("panelTitle").textContent = data.title;
  document.getElementById("panelDescription").textContent = data.description;
  document.getElementById("panelStatusLabel").textContent = data.statusLabel;
  document.getElementById("panelStatus").textContent = data.status;

  const pointList = document.getElementById("panelPoints");
  pointList.replaceChildren(...data.points.map((point) => {
    const item = document.createElement("li");
    item.textContent = point;
    return item;
  }));

  systemTabs.forEach((tab) => {
    const selected = tab.dataset.system === systemName;
    tab.classList.toggle("active", selected);
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
  });

  if (architecturePanel) {
    architecturePanel.classList.remove("is-refreshing");
    void architecturePanel.offsetWidth;
    architecturePanel.classList.add("is-refreshing");
  }
}

architecturePanel?.addEventListener("animationend", () => {
  architecturePanel.classList.remove("is-refreshing");
});

function closeMenu() {
  menuToggle.setAttribute("aria-expanded", "false");
  mobileNav.hidden = true;
  document.body.classList.remove("menu-open");
}

languageToggle.addEventListener("click", () => {
  applyLanguage(language === "en" ? "he" : "en");
});

menuToggle.addEventListener("click", () => {
  const shouldOpen = menuToggle.getAttribute("aria-expanded") !== "true";
  menuToggle.setAttribute("aria-expanded", String(shouldOpen));
  mobileNav.hidden = !shouldOpen;
  document.body.classList.toggle("menu-open", shouldOpen);
});

mobileNav.querySelectorAll("a").forEach((link) => link.addEventListener("click", closeMenu));

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && document.body.classList.contains("menu-open")) {
    closeMenu();
    menuToggle.focus();
  }
});

let scrollInterfaceFrame = 0;

function updateScrollInterface() {
  scrollInterfaceFrame = 0;
  if (!siteHeader) return;
  const scrollRange = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
  const progress = Math.min(1, Math.max(0, window.scrollY / scrollRange));
  siteHeader.style.setProperty("--scroll-progress", `${progress * 100}%`);
  siteHeader.classList.toggle("is-scrolled", window.scrollY > 18);
}

function scheduleScrollInterfaceUpdate() {
  if (scrollInterfaceFrame) return;
  scrollInterfaceFrame = window.requestAnimationFrame(updateScrollInterface);
}

window.addEventListener("scroll", scheduleScrollInterfaceUpdate, { passive: true });
window.addEventListener("resize", scheduleScrollInterfaceUpdate, { passive: true });
updateScrollInterface();

systemTabs.forEach((tab, index) => {
  tab.addEventListener("click", () => renderSystem(tab.dataset.system));
  tab.addEventListener("keydown", (event) => {
    if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key)) return;
    event.preventDefault();
    const increment = ["ArrowRight", "ArrowDown"].includes(event.key) ? 1 : -1;
    const nextIndex = (index + increment + systemTabs.length) % systemTabs.length;
    systemTabs[nextIndex].focus();
    renderSystem(systemTabs[nextIndex].dataset.system);
  });
});

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
  propeller: { station: "STA 01", title: "focusPropellerTitle", text: "focusPropellerText" },
  engine: { station: "STA 02", title: "focusEngineTitle", text: "focusEngineText" },
  flightComputer: { station: "STA 03", title: "focusFlightComputerTitle", text: "focusFlightComputerText" },
  datalink: { station: "STA 04", title: "focusDatalinkTitle", text: "focusDatalinkText" },
  landingGear: { station: "STA 05", title: "focusLandingGearTitle", text: "focusLandingGearText" },
  wing: { station: "STA 06", title: "focusWingTitle", text: "focusWingText" },
  tail: { station: "STA 07", title: "focusTailTitle", text: "focusTailText" },
  remoteWeapon: { station: "STA 08", title: "focusRemoteWeaponTitle", text: "focusRemoteWeaponText" },
  forwardCamera: { station: "STA 09", title: "focusForwardCameraTitle", text: "focusForwardCameraText" },
  fuselageBay: { station: "STA 10", title: "focusFuselageBayTitle", text: "focusFuselageBayText" },
  externalInterface: { station: "AUX 01", title: "focusExternalInterfaceTitle", text: "focusExternalInterfaceText" }
};
const lightingPresets = {
  studio: {
    environment: "environments/studio-softbox-1k.hdr",
    skybox: null,
    exposure: 1.04,
    shadowIntensity: 1.08,
    shadowSoftness: 0.82
  },
  daylight: {
    environment: "environments/daylight-noon-1k.hdr",
    skybox: "environments/daylight-noon-1k.hdr",
    exposure: 0.96,
    shadowIntensity: 1.62,
    shadowSoftness: 0.34
  },
  sky: {
    environment: "environments/sky-partly-cloudy-1k.hdr",
    skybox: "environments/sky-partly-cloudy-1k.hdr",
    exposure: 1.02,
    shadowIntensity: 1.30,
    shadowSoftness: 0.60
  },
  golden: {
    environment: "environments/golden-sunset-1k.hdr",
    skybox: "environments/golden-sunset-1k.hdr",
    exposure: 1.02,
    shadowIntensity: 1.44,
    shadowSoftness: 0.50
  },
  night: {
    environment: "environments/night-moonrise-1k.hdr",
    skybox: "environments/night-moonrise-1k.hdr",
    exposure: 1.12,
    shadowIntensity: 1.04,
    shadowSoftness: 0.70
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
  if (model) model.setAttribute("exposure", exposureControl.value);
});

function updateModelFocusCard() {
  if (!activeModelComponent || !modelFocusCard || !modelFocusTitle || !modelFocusText) return;
  const content = modelFocusContent[activeModelComponent];
  if (!content) return;
  if (modelFocusStation) modelFocusStation.textContent = content.station;
  modelFocusTitle.textContent = translations[language][content.title];
  modelFocusText.textContent = translations[language][content.text];
}

let hotspotDensityFrame = 0;

function updateHotspotDensity() {
  hotspotDensityFrame = 0;
  if (!model || !modelStage || typeof model.getCameraOrbit !== "function") return;
  const orbit = model.getCameraOrbit();
  const fieldOfView = model.getFieldOfView();
  const visibleHalfHeight = orbit.radius * Math.tan(fieldOfView * Math.PI / 360);
  const maximumLevel = visibleHalfHeight > 3.0 ? 1 : visibleHalfHeight > 1.25 ? 2 : 3;
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
  model.cameraTarget = "auto auto auto";
  model.cameraOrbit = "30deg 78deg 108%";
  model.fieldOfView = "32deg";
  model.setAttribute("auto-rotate", "");
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
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("revealed");
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: "0px 0px -40px" });

  document.querySelectorAll("[data-reveal]").forEach((element) => observer.observe(element));
} else {
  document.querySelectorAll("[data-reveal]").forEach((element) => element.classList.add("revealed"));
}

document.getElementById("year").textContent = String(new Date().getFullYear());

let savedLanguage = null;
try {
  savedLanguage = localStorage.getItem("airshield-language");
} catch (_) {
  savedLanguage = null;
}
applyLanguage(savedLanguage === "he" ? "he" : "en");
