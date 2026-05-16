let chartIndex = 0;

const colors = [
  "#2563eb",
  "#16a34a",
  "#f59e0b",
  "#dc2626",
  "#7c3aed",
  "#0ea5e9"
];

let globalData = [];

/* =========================
   FILE LOAD
========================= */

document
  .getElementById("fileInput")
  .addEventListener("change", handleFile);

document
  .getElementById("limitInput")
  .addEventListener("input", applyFilters);

function handleFile(event){

  const file = event.target.files[0];

  if(!file) return;

  Papa.parse(file,{
    header:true,
    dynamicTyping:true,
    skipEmptyLines:true,

    complete:function(results){

      globalData =
        results.data.filter(
          row => Object.keys(row).length > 0
        );

      buildFilters(globalData);

      buildDashboard(globalData);

    }
  });

}

/* =========================
   FILTER ENGINE
========================= */

function buildFilters(data){

  const filterDiv =
    document.getElementById("filters");

  filterDiv.innerHTML = "";

  if(!data || data.length === 0) return;

  const keys = Object.keys(data[0]);

  keys.forEach(key=>{

    const uniqueValues =
      [...new Set(data.map(d=>d[key]))];

    if(
      uniqueValues.length < 20 &&
      typeof uniqueValues[0] !== "number"
    ){

      const wrapper =
        document.createElement("div");

      wrapper.className =
        "filter-box";

      const label =
        document.createElement("label");

      label.innerText = key;

      const select =
        document.createElement("select");

      select.multiple = true;

      select.dataset.key = key;

      const allOption =
        document.createElement("option");

      allOption.value = "__ALL__";

      allOption.innerText = "ALL";

      select.appendChild(allOption);

      uniqueValues.forEach(val=>{

        const opt =
          document.createElement("option");

        opt.value = val;

        opt.innerText = val;

        select.appendChild(opt);

      });

      select.addEventListener(
        "change",
        applyFilters
      );

      wrapper.appendChild(label);

      wrapper.appendChild(select);

      filterDiv.appendChild(wrapper);

    }

  });

}

function applyFilters(){

  const selects =
    document.querySelectorAll(
      "#filters select"
    );

  let filtered = [...globalData];

  selects.forEach(select=>{

    const key = select.dataset.key;

    const selected =
      [...select.selectedOptions]
      .map(o=>o.value);

    if(
      selected.length > 0 &&
      !selected.includes("__ALL__")
    ){

      filtered = filtered.filter(
        row =>
          selected.includes(
            String(row[key])
          )
      );

    }

  });

  buildDashboard(filtered);

}

/* =========================
   DASHBOARD ENGINE
========================= */

function buildDashboard(data){

  if(!data || data.length === 0) return;

  chartIndex = 0;

  document.querySelector(".kpi-grid").innerHTML = "";

  document.querySelector(".charts-grid").innerHTML = "";

  const keys = Object.keys(data[0]);

  keys.forEach(key=>{

    let values =
      data
      .map(row=>row[key])
      .filter(v=>typeof v === "number");

    const limit =
      parseInt(
        document.getElementById("limitInput").value
      );

    if(!isNaN(limit) && limit > 0){

      values = values.slice(-limit);

    }

    if(values.length > 0){

      createKPI(key, values);

      createChart(key, values, data);

    }

  });

  const insights =
    runRAC(data);

  showRAC(insights);

}

/* =========================
   KPI ENGINE
========================= */

function detectKPIType(name){

  const kpi =
    name.toLowerCase();

  if(
    kpi.includes("rate") ||
    kpi.includes("success") ||
    kpi.includes("availability") ||
    kpi.includes("retain") ||
    kpi.includes("drop")
  ){
    return "percentage";
  }

  if(
    kpi.includes("rsrp") ||
    kpi.includes("rsrq") ||
    kpi.includes("sinr")
  ){
    return "radio";
  }

  return "generic";

}

function createKPI(name, values){

  const avg =
    (
      values.reduce((a,b)=>a+b,0)
      / values.length
    ).toFixed(2);

  const card =
    document.createElement("div");

  card.className =
    "kpi-card";

  card.innerHTML = `
    <h3>${name}</h3>
    <p>${avg}</p>
  `;

  document
    .querySelector(".kpi-grid")
    .appendChild(card);

}

/* =========================
   CHART ENGINE
========================= */

function createChart(name, values, data){

  const container =
    document.createElement("div");

  container.className =
    "chart-box";

  /* HEADER */
  const header =
    document.createElement("div");

  header.className =
    "chart-header";

  header.innerHTML = `
    <div class="kpi-title-group">
      <span class="kpi-main">
        KPI1: ${name}
      </span>

      <span class="kpi-secondary">
        KPI2: Future Overlay
      </span>
    </div>
  `;

  container.appendChild(header);

  /* SELECTOR */
  const selector =
    document.createElement("select");

  selector.className =
    "chart-selector";

  selector.innerHTML = `
    <option value="line">Line</option>
    <option value="bar">Bar</option>
    <option value="doughnut">Doughnut</option>
    <option value="pie">Pie</option>
    <option value="scatter">Scatter</option>
  `;

  container.appendChild(selector);

  /* CANVAS */
  const canvas =
    document.createElement("canvas");

  container.appendChild(canvas);

  document
    .querySelector(".charts-grid")
    .appendChild(container);

  /* LABELS */
  const labels =
    data
      .slice(-values.length)
      .map((row, i)=>{

        const keys =
          Object.keys(row);

        const xKey =

          keys.find(k =>
            k.toLowerCase().includes("date")
          )

          ||

          keys.find(k =>
            k.toLowerCase().includes("month")
          )

          ||

          keys[0];

        return row[xKey] || `Row ${i+1}`;

      });

  /* CHART */
  const chartConfig = {

    type: selector.value,

    data:{

      labels: labels,

      datasets:[{

        label:name,

        data:values,

        backgroundColor:
          colors[
            chartIndex % colors.length
          ] + "22",

        borderColor:
          colors[
            chartIndex % colors.length
          ],

        borderWidth:3,

        tension:0.35,

        pointRadius:2,

        pointHoverRadius:6,

        fill:false

      }]

    },

    options:{

      responsive:true,

      maintainAspectRatio:false,

      interaction:{
        mode:"index",
        intersect:false
      },

      plugins:{

        legend:{
          position:"top",
          labels:{
            color:"#e2e8f0"
          }
        }

      },

      scales:{

        x:{

          ticks:{
            color:"#cbd5e1"
          },

          grid:{
            color:"rgba(255,255,255,0.05)"
          }

        },

        y:{

          ticks:{
            color:"#cbd5e1"
          },

          grid:{
            color:"rgba(255,255,255,0.05)"
          }

        }

      }

    }

  };

  let chart =
    new Chart(
      canvas.getContext("2d"),
      chartConfig
    );

  /* CHART SWITCHER */

  selector.addEventListener("change",()=>{

    chart.destroy();

    chartConfig.type =
      selector.value;

    chart =
      new Chart(
        canvas.getContext("2d"),
        chartConfig
      );

  });

  chartIndex++;

}

/* =========================
   RAC ENGINE
========================= */

function runRAC(data){

  let insights = [];

  insights.push({

    title:"🧠 RAC ENGINE",

    cause:"Dashboard operational",

    action:"AI RCA ready"

  });

  return insights;

}

function showRAC(insights){

  const container =
    document.getElementById("rac-results");

  if(!container) return;

  container.innerHTML = "";

  insights.forEach(i=>{

    container.innerHTML += `

      <div class="rac-card">

        <strong>${i.title}</strong><br>

        <b>Cause:</b> ${i.cause}<br>

        <b>Action:</b> ${i.action}

      </div>

    `;

  });

}
