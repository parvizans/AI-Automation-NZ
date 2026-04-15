let globalData = [];

/* =========================
   FILE LOAD
========================= */
document.getElementById("fileInput").addEventListener("change", handleFile);

document.getElementById("limitInput").addEventListener("input", () => {
  applyFilters();
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

      // ALL option
      const allOption = document.createElement("option");
      allOption.value = "__ALL__";
      allOption.innerText = "ALL";
      select.appendChild(allOption);

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

  const keys = Object.keys(data[0]);

  document.querySelector(".kpi-grid").innerHTML = "";
  document.querySelector(".charts-grid").innerHTML = "";

  keys.forEach(key => {
    let values = data.map(row => row[key]).filter(v => typeof v === "number");

    const limit = parseInt(document.getElementById("limitInput").value);

    if (!isNaN(limit) && limit > 0) {
      values = values.slice(-limit);
    }

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

  // 🔥 AGGREGATED INSIGHTS
  createAggregatedChart(data, "Country", "Sales");
  createAggregatedChart(data, "Segment", "Profit");
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
    <p>${Number(avg).toLocaleString()}</p>
  `;

  document.querySelector(".kpi-grid").appendChild(card);
}

/* =========================
   CHART ENGINE
========================= */
function createChart(name, values) {

  const container = document.createElement("div");
  container.className = "chart-box";

  // Controls container (clean UI)
  const controls = document.createElement("div");
  controls.style.display = "flex";
  controls.style.justifyContent = "space-between";
  controls.style.marginBottom = "10px";

  // Checkbox
  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.checked = true;

  // Chart selector
  const select = document.createElement("select");
  ["line","bar","pie","scatter"].forEach(t=>{
    const o=document.createElement("option");
    o.value=t;
    o.innerText=t;
    select.appendChild(o);
  });

  controls.appendChild(checkbox);
  controls.appendChild(select);

  const canvas = document.createElement("canvas");

  container.appendChild(controls);
  container.appendChild(canvas);

  document.querySelector(".charts-grid").appendChild(container);

  // 🔥 FUNCTION TO PREPARE DATA BASED ON CHART TYPE
  function getDataset(chartType) {

    // SCATTER FIX
    if (chartType === "scatter") {
      return values.map((v, i) => ({ x: i, y: v }));
    }

    return values;
  }


 // 🔥 FUNCTION TO BUILD CHART
function buildChart(chartType) {

  // ✅ DEFINE FIRST (outside Chart config)
  let displayValues = values;

  // 🔴 LIMIT PIE SIZE
  if (chartType === "pie" && values.length > 6) {
    displayValues = values.slice(0, 6);
  }

  return new Chart(canvas, {
    type: chartType,
    data: {
      labels: chartType === "pie" 
        ? displayValues.map((_, i) => `Part ${i + 1}`)
        : displayValues.map((_, i) => `Pt ${i + 1}`),

      datasets: [{
        label: name,
        data: chartType === "scatter"
          ? values.map((v, i) => ({ x: i, y: v }))
          : displayValues,

        // 🎨 STYLE
        backgroundColor: "rgba(50,210,150,0.4)",
        borderColor: "#32d296",
        borderWidth: 2,
        fill: chartType === "line" ? false : true
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          display: true
        }
      }
    }
  });
}
  // INITIAL CHART
  let chart = buildChart("line");

  // 🔁 CHANGE CHART TYPE
  select.addEventListener("change", () => {
    chart.destroy();
    chart = buildChart(select.value);
  });

  // 👁️ SHOW / HIDE
  checkbox.addEventListener("change", () => {
    container.style.display = checkbox.checked ? "block" : "none";
  });
}

/* =========================
   AGGREGATION ENGINE
========================= */
function groupBy(data, key, valueField) {
  const result = {};

  data.forEach(row => {
    const group = row[key];
    const value = row[valueField];

    if (typeof value !== "number") return;

    if (!result[group]) result[group] = 0;
    result[group] += value;
  });

  return result;
}

function createAggregatedChart(data, groupKey, valueKey) {

  const grouped = groupBy(data, groupKey, valueKey);

  const labels = Object.keys(grouped);
  const values = Object.values(grouped);

  const container = document.createElement("div");
  container.className = "chart-box";

  const title = document.createElement("h4");
  title.innerText = `${valueKey} by ${groupKey}`;

  const canvas = document.createElement("canvas");

  container.appendChild(title);
  container.appendChild(canvas);

  document.querySelector(".charts-grid").appendChild(container);

  new Chart(canvas, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: valueKey,
        data: values
      }]
    }
  });
}

function runRAC(data) {

  let insights = [];

  const keys = Object.keys(data[0]);

  // Extract common fields safely
  let sales = data.map(d => d["Sales"]).filter(v => typeof v === "number");
  let profit = data.map(d => d["Profit"]).filter(v => typeof v === "number");
  let discounts = data.map(d => d["Discounts"]).filter(v => typeof v === "number");
  let units = data.map(d => d["Units Sold"]).filter(v => typeof v === "number");

  const sum = arr => arr.reduce((a,b)=>a+b,0);

  if (profit.length && sum(profit) < 0) {
    insights.push({
      title: "📉 Loss Detected",
      cause: "Total profit is negative",
      action: "Check pricing or reduce discounts"
    });
  }

  if (discounts.length && sales.length && sum(discounts) > sum(sales) * 0.2) {
    insights.push({
      title: "⚠️ High Discount Impact",
      cause: "Discounts are too high compared to sales",
      action: "Optimize discount strategy"
    });
  }

  if (units.length && profit.length && sum(units) > 1000 && sum(profit) < 0) {
    insights.push({
      title: "📦 High Volume, Low Profit",
      cause: "Selling high quantity but low margin",
      action: "Review product pricing or supplier cost"
    });
  }

  return insights;
}



