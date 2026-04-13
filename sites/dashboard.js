let globalData = [];

/* =========================
   FILE LOAD
========================= */
document.getElementById("fileInput").addEventListener("change", handleFile);

document.getElementById("limitInput").addEventListener("input", () => {
  applyFilters(); // re-run dashboard
});

function handleFile(event) {
  const file = event.target.files[0];

  Papa.parse(file, {
    header: true,
    dynamicTyping: true,
    complete: function(results) {
      globalData = results.data.filter(row => Object.keys(row).length > 0);
      buildFilters(globalData);
      buildDashboard(globalData);
    }
  });
}

/* =========================
   FILTER ENGINE
========================= */
function buildFilters(data) {
  const filterDiv = document.getElementById("filters");
  filterDiv.innerHTML = "";

  const keys = Object.keys(data[0]);

  keys.forEach(key => {
    const uniqueValues = [...new Set(data.map(d => d[key]))];

    if (uniqueValues.length < 20 && typeof uniqueValues[0] !== "number") {
      const wrapper = document.createElement("div");

      const label = document.createElement("label");
      label.innerText = key;

      const select = document.createElement("select");
      select.multiple = true;
      select.dataset.key = key;

// Add ALL option
const allOption = document.createElement("option");
allOption.value = "__ALL__";
allOption.innerText = "ALL";
select.appendChild(allOption);

// Existing loop (keep it)
uniqueValues.forEach(val => {
  const opt = document.createElement("option");
  opt.value = val;
  opt.innerText = val;
  select.appendChild(opt);
});
      select.addEventListener("change", applyFilters);

      wrapper.appendChild(label);
      wrapper.appendChild(select);

      filterDiv.appendChild(wrapper);
    }
  });
}

function applyFilters() {
  const selects = document.querySelectorAll("#filters select");

  let filtered = [...globalData];

  selects.forEach(select => {
    const key = select.dataset.key;
    const selected = [...select.selectedOptions].map(o => o.value);

   if (selected.length > 0 && !selected.includes("__ALL__")) {
      filtered = filtered.filter(row => selected.includes(String(row[key])));
    }
  });

  buildDashboard(filtered);
}

/* =========================
   DASHBOARD ENGINE
========================= */
function buildDashboard(data) {
  if (!data || data.length === 0) return;

  const limit = parseInt(document.getElementById("limitInput").value);
  const keys = Object.keys(data[0]);

  document.querySelector(".kpi-grid").innerHTML = "";
  document.querySelector(".charts-grid").innerHTML = "";

keys.forEach(key => {
  let values = data.map(row => row[key]).filter(v => typeof v === "number");

  // 🔥 ADD THIS (N-point logic)
  const limit = parseInt(document.getElementById("limitInput").value);

  if (!isNaN(limit) && limit > 0) {
    values = values.slice(-limit);
  }

  // Existing condition
  if (
    values.length > 0 &&
    !key.toLowerCase().includes("year") &&
    !key.toLowerCase().includes("day") &&
    !key.toLowerCase().includes("month")
  ) {
    createKPI(key, values);
    createChart(key, values);
  }
});
}

/* =========================
   KPI
========================= */
function createKPI(name, values) {
  const avg = (values.reduce((a,b)=>a+b,0) / values.length).toFixed(2);

  const card = document.createElement("div");
  card.className = "kpi-card";

  card.innerHTML = `
    <h3>${name}</h3>
    <p>${avg}</p>
  `;

  document.querySelector(".kpi-grid").appendChild(card);
}

/* =========================
   RCA ENGINE
========================= */
function detectIssues(name, values) {
  if (values.length < 15) return null;

  const avg = values.reduce((a,b)=>a+b,0) / values.length;
  const last = values[values.length - 1];

  const deviation = Math.abs(last - avg) / avg;

  if (deviation > 1.0) return "🔴 Critical";
  if (deviation > 0.6) return "🟠 Warning";

  return null;
}

/* =========================
   CHART ENGINE
========================= */
function createChart(name, values) {

  const container = document.createElement("div");
  container.className = "chart-box";

  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.checked = true;

  const select = document.createElement("select");
  ["line","bar","pie"].forEach(t=>{
    const o=document.createElement("option");
    o.value=t;
    o.innerText=t;
    select.appendChild(o);
  });

  const canvas = document.createElement("canvas");

  container.appendChild(checkbox);
  container.appendChild(select);
  container.appendChild(canvas);

  document.querySelector(".charts-grid").appendChild(container);

  let chart = new Chart(canvas, {
    type: "line",
    data: {
   labels: values.map((_, i) => `Pt ${i + 1}`),
datasets: [{
        label: name,
        data: values
      }]
    }
  });

  select.addEventListener("change", () => {
    chart.destroy();
    chart = new Chart(canvas, {
      type: select.value,
      data: {
      labels: values.map((_, i) => `Pt ${i + 1}`),
        datasets: [{
          label: name,
          data: values
        }]
      }
    });
  });

  checkbox.addEventListener("change", () => {
    container.style.display = checkbox.checked ? "block" : "none";
  });

  const issue = detectIssues(name, values);
  if (issue) {
    const alert = document.createElement("div");
    alert.style.color = "red";
    alert.innerText = issue;
    container.appendChild(alert);
  }
}
