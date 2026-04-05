🔹 // STEP 2.1 — CSV PARSER (ROBUST)
function parseCSV(text) {
  const lines = text.trim().split("\n");
  const headers = lines[0].split(",");

  return lines.slice(1).map(line => {
    const values = line.split(",");
    let obj = {};
    headers.forEach((h, i) => {
      obj[h.trim()] = values[i]?.trim();
    });
    return obj;
  });
}
🔹 // STEP 2.2 — SAFE COLUMN EXTRACTION
function getColumn(data, key) {
  return data.map(row => {
    let val = row[key];
    return val !== undefined && val !== "" ? parseFloat(val) : null;
  });
}
🔹// STEP 2.3 — GET LATEST VALUE (FIX NaN)
function getLatestValue(arr) {
  const valid = arr.filter(v => v !== null && !isNaN(v));
  return valid.length ? valid[valid.length - 1] : "-";
}
🟡 PHASE 3 — AUTO KPI + AUTO CHART ENGINE 🔥

👉 THIS is the big upgrade (no more limit)

🔹 // STEP 3.1 — FILE UPLOAD HANDLER
document.getElementById("fileInput").addEventListener("change", function(e) {
  const file = e.target.files[0];
  const reader = new FileReader();

  reader.onload = function(event) {
    const text = event.target.result;
    const data = parseCSV(text);

    buildDashboard(data);
  };

  reader.readAsText(file);
});
🔹 // STEP 3.2 — MAIN ENGINE
function buildDashboard(data) {

  document.querySelector(".charts-grid").innerHTML = "";

  const keys = Object.keys(data[0]);

  keys.forEach((key, index) => {

    const values = getColumn(data, key);

    createChart(key, values, index);

    updateKPICard(key, values);

  });
}
🔹 // STEP 3.3 — CREATE CHART (AUTO)
function createChart(title, values, index) {

  const container = document.createElement("div");
  container.className = "chart-card";

  const canvas = document.createElement("canvas");
  canvas.id = "chart_" + index;

  container.appendChild(canvas);
  document.querySelector(".charts-grid").appendChild(container);

  new Chart(canvas, {
    type: "line",
    data: {
      labels: values.map((_, i) => i + 1),
      datasets: [{
        label: title,
        data: values,
        borderWidth: 2,
        tension: 0.3
      }]
    }
  });
}
🔹 // STEP 3.4 — KPI CARD UPDATE

👉 (Assumes you already have KPI divs)

function updateKPICard(key, values) {

  let id = key.toLowerCase();

  const el = document.getElementById(id);

  if (el) {
    el.innerText = getLatestValue(values);
  }
}
