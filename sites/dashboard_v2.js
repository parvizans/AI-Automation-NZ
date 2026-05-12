```javascript
// ========================================
// AUTOMATIONPARK DASHBOARD V2
// SMART OPERATIONAL ENGINE
// ========================================

let globalData = [];
let charts = [];

// ========================================
// COLORS
// ========================================

const colors = [
  "#32d296",
  "#2563eb",
  "#f59e0b",
  "#dc2626",
  "#7c3aed",
  "#0ea5e9"
];

// ========================================
// FILE LOAD
// ========================================

document.getElementById("fileInput").addEventListener("change", loadFile);

function loadFile(event) {

  const file = event.target.files[0];

  Papa.parse(file, {
    header: true,
    dynamicTyping: true,

    complete: function(results) {

      globalData = results.data.filter(
        row => Object.keys(row).length > 0
      );

      buildFilters(globalData);

      buildDashboard(globalData);
    }
  });
}

// ========================================
// SMART FILTERS
// ========================================

function buildFilters(data) {

  const container = document.getElementById("filters");

  container.innerHTML = "";

  const keys = Object.keys(data[0]);

  keys.forEach(key => {

    const uniqueValues = [
      ...new Set(data.map(d => d[key]))
    ];

    // ONLY IMPORTANT FILTERS
    if (
      uniqueValues.length > 1 &&
      uniqueValues.length < 15 &&
      typeof uniqueValues[0] !== "number"
    ) {

      const wrapper = document.createElement("div");

      const label = document.createElement("label");
      label.innerText = key;

      const select = document.createElement("select");

      select.dataset.key = key;

      const all = document.createElement("option");

      all.value = "";
      all.innerText = "ALL";

      select.appendChild(all);

      uniqueValues.forEach(v => {

        const option = document.createElement("option");

        option.value = v;
        option.innerText = v;

        select.appendChild(option);
      });

      select.addEventListener("change", applyFilters);

      wrapper.appendChild(label);
      wrapper.appendChild(select);

      container.appendChild(wrapper);
    }
  });
}

// ========================================
// APPLY FILTERS
// ========================================

function applyFilters() {

  const selects = document.querySelectorAll("#filters select");

  let filtered = [...globalData];

  selects.forEach(select => {

    const key = select.dataset.key;

    const value = select.value;

    if (value !== "") {

      filtered = filtered.filter(
        row => String(row[key]) === value
      );
    }
  });

  buildDashboard(filtered);
}

// ========================================
// KPI ENGINE
// ========================================

function buildKPIs(data) {

  const container = document.querySelector(".kpi-grid");

  container.innerHTML = "";

  const keys = Object.keys(data[0]);

  const numeric = keys.filter(
    k => typeof data[0][k] === "number"
  );

  numeric.slice(0,5).forEach((k, index) => {

    const values = data
      .map(d => d[k])
      .filter(v => typeof v === "number");

    const avg =
      values.reduce((a,b)=>a+b,0) / values.length;

    const card = document.createElement("div");

    card.className = "kpi-card";

    card.innerHTML = `
      <h3>${k}</h3>
      <p>${avg.toFixed(2)}</p>
    `;

    container.appendChild(card);
  });
}

// ========================================
// AGGREGATION ENGINE
// ========================================

function aggregateData(data, categoryKey, valueKey, mode="sum") {

  const grouped = {};

  data.forEach(row => {

    const category = row[categoryKey];

    const value = row[valueKey];

    if (typeof value !== "number") return;

    if (!grouped[category]) {
      grouped[category] = [];
    }

    grouped[category].push(value);
  });

  const labels = Object.keys(grouped);

  const values = labels.map(label => {

    const arr = grouped[label];

    switch(mode) {

      case "avg":
        return (
          arr.reduce((a,b)=>a+b,0) / arr.length
        );

      case "max":
        return Math.max(...arr);

      case "min":
        return Math.min(...arr);

      case "count":
        return arr.length;

      default:
        return arr.reduce((a,b)=>a+b,0);
    }
  });

  return {
    labels,
    values
  };
}

// ========================================
// CHART ENGINE
// ========================================

function buildCharts(data) {

  const container =
    document.querySelector(".charts-grid");

  container.innerHTML = "";

  charts.forEach(c => c.destroy());

  charts = [];

  const keys = Object.keys(data[0]);

  const numeric = keys.filter(
    k => typeof data[0][k] === "number"
  );

  const category =
    keys.find(k => typeof data[0][k] !== "number");

  numeric.forEach((k, index) => {

    const chartBox = document.createElement("div");

    chartBox.className = "chart-box";

    const title = document.createElement("h3");

    title.innerText = k;

    const canvas = document.createElement("canvas");

    chartBox.appendChild(title);
    chartBox.appendChild(canvas);

    container.appendChild(chartBox);

    // ====================================
    // SMART AGGREGATION
    // ====================================

    let mode = "sum";

    if (
      k.toLowerCase().includes("rate") ||
      k.toLowerCase().includes("availability") ||
      k.toLowerCase().includes("rsrp") ||
      k.toLowerCase().includes("sinr")
    ) {
      mode = "avg";
    }

    const grouped =
      aggregateData(
        data,
        category,
        k,
        mode
      );

    const chart = new Chart(canvas, {

      type: "bar",

      data: {

        labels: grouped.labels,

        datasets: [{

          label: `${k} (${mode})`,

          data: grouped.values,

          backgroundColor:
            colors[index % colors.length] + "88",

          borderColor:
            colors[index % colors.length],

          borderWidth: 2
        }]
      },

      options: {

        responsive: true,

        plugins: {

          legend: {
            display: true,
            position: "top"
          }
        }
      }
    });

    charts.push(chart);
  });
}

// ========================================
// MAIN DASHBOARD
// ========================================

function buildDashboard(data) {

  if (!data || data.length === 0) return;

  buildKPIs(data);

  buildCharts(data);
}
```

