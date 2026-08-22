const planTabs = Array.from(document.querySelectorAll("[data-plan-tab]"));
const planPanels = Array.from(document.querySelectorAll("[data-plan-panel]"));
const planStage = document.getElementById("planStage");
const planPrev = document.getElementById("planPrev");
const planNext = document.getElementById("planNext");
const planPrevLabel = document.getElementById("planPrevLabel");
const planNextLabel = document.getElementById("planNextLabel");
const planProgress = document.getElementById("planProgress");
const planCounter = document.getElementById("planCounter");

const planChapters = [
  { key: "allocation", label: "שימוש בהון" },
  { key: "nre", label: "מפת NRE" },
  { key: "execution", label: "מסלול ביצוע" },
  { key: "economics", label: "כלכלת יחידה" }
];

let activePlanIndex = 0;
let planTouchStartX = null;

function activatePlanChapter(index, { focus = false } = {}) {
  const chapterCount = planChapters.length;
  activePlanIndex = (index + chapterCount) % chapterCount;
  const activeChapter = planChapters[activePlanIndex];

  planStage?.classList.add("is-changing");
  planStage?.setAttribute("data-active-panel", activeChapter.key);

  planTabs.forEach((tab, tabIndex) => {
    const selected = tabIndex === activePlanIndex;
    tab.classList.toggle("is-active", selected);
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
    if (selected && focus) tab.focus();
  });

  planPanels.forEach((panel, panelIndex) => {
    const selected = panelIndex === activePlanIndex;
    panel.hidden = !selected;
    panel.classList.toggle("is-active", selected);
  });

  const previous = planChapters[(activePlanIndex - 1 + chapterCount) % chapterCount];
  const next = planChapters[(activePlanIndex + 1) % chapterCount];
  if (planPrevLabel) planPrevLabel.textContent = previous.label;
  if (planNextLabel) planNextLabel.textContent = next.label;
  if (planCounter) planCounter.textContent = `${String(activePlanIndex + 1).padStart(2, "0")} / ${String(chapterCount).padStart(2, "0")}`;
  if (planProgress) planProgress.style.width = `${((activePlanIndex + 1) / chapterCount) * 100}%`;

  window.setTimeout(() => planStage?.classList.remove("is-changing"), 320);
}

planTabs.forEach((tab, index) => {
  tab.addEventListener("click", () => activatePlanChapter(index));
  tab.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      activatePlanChapter(index + 1, { focus: true });
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      activatePlanChapter(index - 1, { focus: true });
    } else if (event.key === "Home") {
      event.preventDefault();
      activatePlanChapter(0, { focus: true });
    } else if (event.key === "End") {
      event.preventDefault();
      activatePlanChapter(planChapters.length - 1, { focus: true });
    }
  });
});

planPrev?.addEventListener("click", () => activatePlanChapter(activePlanIndex - 1));
planNext?.addEventListener("click", () => activatePlanChapter(activePlanIndex + 1));

planStage?.addEventListener("touchstart", (event) => {
  planTouchStartX = event.changedTouches[0]?.clientX ?? null;
}, { passive: true });

planStage?.addEventListener("touchend", (event) => {
  if (planTouchStartX === null) return;
  const touchEndX = event.changedTouches[0]?.clientX ?? planTouchStartX;
  const deltaX = touchEndX - planTouchStartX;
  planTouchStartX = null;
  if (Math.abs(deltaX) < 48) return;
  activatePlanChapter(activePlanIndex + (deltaX < 0 ? 1 : -1));
}, { passive: true });

activatePlanChapter(0);
