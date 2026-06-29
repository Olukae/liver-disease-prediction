(function () {
  "use strict";
  const steps = Array.from(document.querySelectorAll(".form-step"));
  const trackerItems = Array.from(document.querySelectorAll(".step-item"));
  if (!steps.length) return;

  let current = 0;

  function show(index) {
    steps.forEach((s, i) => s.classList.toggle("active", i === index));
    trackerItems.forEach((t, i) => {
      t.classList.toggle("active", i === index);
      t.classList.toggle("done", i < index);
    });
    current = index;
    window.scrollTo({ top: document.querySelector(".prediction-form-card").offsetTop - 90, behavior: "smooth" });
  }

  function fieldsValid(stepEl) {
    const inputs = stepEl.querySelectorAll("input, select");
    let valid = true;
    inputs.forEach((input) => {
      if (!input.checkValidity()) {
        valid = false;
        input.classList.add("field-invalid");
        input.reportValidity();
      } else {
        input.classList.remove("field-invalid");
        input.classList.add("field-valid");
      }
    });
    return valid;
  }

  document.querySelectorAll("[data-next]").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (!fieldsValid(steps[current])) return;
      if (current < steps.length - 1) show(current + 1);
    });
  });

  document.querySelectorAll("[data-prev]").forEach((btn) => {
    btn.addEventListener("click", () => show(Math.max(0, current - 1)));
  });

  // Live summary on the final review step
  const summaryEl = document.getElementById("reviewSummary");
  document.querySelectorAll("[data-next]").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (summaryEl && current === steps.length - 1) {
        const rows = [];
        document.querySelectorAll("#predictionForm [data-summary-label]").forEach((input) => {
          const label = input.getAttribute("data-summary-label");
          let val = input.value;
          if (input.tagName === "SELECT") val = input.options[input.selectedIndex].text;
          rows.push(`<div class="d-flex justify-content-between py-2 border-bottom"><span class="text-soft">${label}</span><strong>${val || "-"}</strong></div>`);
        });
        summaryEl.innerHTML = rows.join("");
      }
    });
  });

  show(0);
})();
