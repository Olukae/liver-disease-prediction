(function () {
  "use strict";

  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function baseOptions(extra = {}) {
    return Object.assign({
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: cssVar("--ink-soft"), font: { family: "Manrope", weight: 600 } } },
        tooltip: { backgroundColor: cssVar("--surface-solid"), titleColor: cssVar("--ink"), bodyColor: cssVar("--ink-soft"), borderColor: cssVar("--surface-border"), borderWidth: 1, padding: 10, cornerRadius: 10 },
      },
      scales: {
        x: { ticks: { color: cssVar("--ink-faint"), font: { family: "Manrope" } }, grid: { display: false } },
        y: { ticks: { color: cssVar("--ink-faint"), font: { family: "Manrope" } }, grid: { color: cssVar("--surface-border") }, beginAtZero: true },
      },
    }, extra);
  }

  async function fetchJSON(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to load chart data");
    return res.json();
  }

  async function renderRiskDistribution() {
    const el = document.getElementById("riskDistributionChart");
    if (!el) return;
    const data = await fetchJSON("/api/charts/risk-distribution");
    new Chart(el, {
      type: "doughnut",
      data: {
        labels: data.labels,
        datasets: [{
          data: data.values,
          backgroundColor: [cssVar("--success"), cssVar("--warning"), cssVar("--danger")],
          borderWidth: 0,
          hoverOffset: 8,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false, cutout: "68%",
        plugins: { legend: { position: "bottom", labels: { color: cssVar("--ink-soft"), padding: 16, font: { family: "Manrope", weight: 600 } } } },
      },
    });
  }

  async function renderPredictionsTrend() {
    const el = document.getElementById("predictionsTrendChart");
    if (!el) return;
    const data = await fetchJSON("/api/charts/predictions-trend");
    new Chart(el, {
      type: "line",
      data: {
        labels: data.labels,
        datasets: [{
          label: "Predictions",
          data: data.values,
          borderColor: cssVar("--primary"),
          backgroundColor: "rgba(37,99,235,0.12)",
          fill: true, tension: 0.4, pointRadius: 3, pointBackgroundColor: cssVar("--primary"),
        }],
      },
      options: baseOptions({ plugins: { legend: { display: false } } }),
    });
  }

  async function renderUserActivity() {
    const el = document.getElementById("userActivityChart");
    if (!el) return;
    const data = await fetchJSON("/api/charts/user-activity");
    new Chart(el, {
      type: "bar",
      data: {
        labels: data.labels,
        datasets: [{
          label: "New Users",
          data: data.values,
          backgroundColor: cssVar("--accent"),
          borderRadius: 6, maxBarThickness: 22,
        }],
      },
      options: baseOptions({ plugins: { legend: { display: false } } }),
    });
  }

  async function renderParameterAnalysis() {
    const el = document.getElementById("parameterAnalysisChart");
    if (!el) return;
    const data = await fetchJSON("/api/charts/parameter-analysis");
    new Chart(el, {
      type: "bar",
      data: {
        labels: data.labels,
        datasets: [
          { label: "Disease Detected (avg)", data: data.disease, backgroundColor: cssVar("--danger"), borderRadius: 6, maxBarThickness: 18 },
          { label: "No Disease (avg)", data: data.healthy, backgroundColor: cssVar("--secondary"), borderRadius: 6, maxBarThickness: 18 },
        ],
      },
      options: baseOptions(),
    });
  }

  async function renderMyHistory() {
    const el = document.getElementById("myHistoryChart");
    if (!el) return;
    const data = await fetchJSON("/api/charts/my-history");
    if (!data.labels.length) {
      el.closest(".chart-card")?.querySelector(".chart-empty")?.classList.remove("d-none");
      el.style.display = "none";
      return;
    }
    new Chart(el, {
      type: "line",
      data: {
        labels: data.labels,
        datasets: [{
          label: "Confidence %",
          data: data.confidence,
          borderColor: cssVar("--primary"),
          backgroundColor: "rgba(37,99,235,0.12)",
          fill: true, tension: 0.4, pointRadius: 4, pointBackgroundColor: cssVar("--primary"),
        }],
      },
      options: baseOptions({ plugins: { legend: { display: false } }, scales: { y: { min: 0, max: 100, ticks: { color: cssVar("--ink-faint") }, grid: { color: cssVar("--surface-border") } }, x: { ticks: { color: cssVar("--ink-faint") }, grid: { display: false } } } }),
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    renderRiskDistribution();
    renderPredictionsTrend();
    renderUserActivity();
    renderParameterAnalysis();
    renderMyHistory();
  });
})();
