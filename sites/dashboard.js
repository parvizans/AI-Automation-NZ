let chartIndex = 0;

const colors = [
  "#3b82f6",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#06b6d4",
  "#f97316",
  "#14b8a6"
];

let globalData = [];

Chart.defaults.color = "#cbd5e1";
Chart.defaults.font.family = "Segoe UI";

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

  Papa.parse(file,{

    header:true,

    dynamicTyping:true,

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
FILTERS
========================= */

function buildFilters(data){

  const filterDiv =
    document.getElementById("filters");

  filterDiv.innerHTML = "";

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
DASHBOARD
========================= */

function buildDashboard(data){

  if(!data || data.length === 0) return;

  document.querySelector(".kpi-grid").innerHTML = "";

  document.querySelector(".charts-grid").innerHTML = "";

  const keys = Object.keys(data[0]);

  const numericKeys =
    keys.filter(key =>
      data.some(
        row => typeof row[key] === "number"
      )
    );

  numericKeys.forEach((key,index)=>{

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

      createChart(
        key,
        values,
        data,
        numericKeys
      );

    }

  });

  const insights = runRAC(data);

  showRAC(insights);

}

/* =========================
KPI
========================= */

function createKPI(name, values){

  const result = (
    values.reduce((a,b)=>a+b,0)
    / values.length
  ).toFixed(2);

  const card =
    document.createElement("div");

  card.className = "kpi-card";

  card.innerHTML = `
    <h3>${name}</h3>
    <p>${result}</p>
  `;

  document
    .querySelector(".kpi-grid")
    .appendChild(card);

}

/* =========================
CHART ENGINE
========================= */

function createChart(
  name,
  values,
  data,
  numericKeys
){

  const container =
    document.createElement("div");

  container.className = "chart-box";

  /* =========================
  HEADER
  ========================= */

  const header =
    document.createElement("div");

  header.className = "chart-header";

  /* =========================
  KPI2 DROPDOWN
  ========================= */

  let optionsHTML = "";

  numericKeys.forEach(kpi=>{

    optionsHTML += `
      <option value="${kpi}">
        ${kpi}
      </option>
    `;

  });

  header.innerHTML = `

    <div>

      <div class="kpi-main">
        KPI1: ${name}
      </div>

      <div class="kpi-secondary">
        KPI2:
      </div>

      <select class="chart-selector kpi2-selector">
        ${optionsHTML}
      </select>

    </div>

  `;

  container.appendChild(header);

  const selector =
    document.createElement("select");

  selector.className = "chart-selector";

  selector.innerHTML = `
    <option value="line">Line</option>
    <option value="bar">Bar</option>
    <option value="radar">Radar</option>
    <option value="scatter">Scatter</option>
    <option value="doughnut">Doughnut</option>
    <option value="pie">Pie</option>
  `;

  container.appendChild(selector);

  const canvas =
    document.createElement("canvas");

  container.appendChild(canvas);

  document
    .querySelector(".charts-grid")
    .appendChild(container);

  const kpi2Selector =
    container.querySelector(".kpi2-selector");

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
          k.toLowerCase().includes("time")
        )

        ||

        keys.find(k =>
          typeof row[k] === "string"
        )

        ||

        keys[0];

      return row[xKey] || `Row ${i+1}`;

    });

  const primaryColor =
    colors[chartIndex % colors.length];

  const secondaryColor =
    colors[(chartIndex + 2) % colors.length];

  let chart;

  function renderChart(){

    const secondKPI =
      kpi2Selector.value;

    const secondValues =
      data
      .map(row=>row[secondKPI])
      .filter(v=>typeof v === "number")
      .slice(-values.length);

    if(chart){

      chart.destroy();

    }

    const crosshairPlugin = {

      id:"crosshairLine",

      afterDraw: chart => {

        if(chart.tooltip?._active?.length){

          const ctx = chart.ctx;

          const x =
            chart.tooltip._active[0].element.x;

          const topY =
            chart.scales.y.top;

          const bottomY =
            chart.scales.y.bottom;

          ctx.save();

          ctx.beginPath();

          ctx.moveTo(x, topY);

          ctx.lineTo(x, bottomY);

          ctx.lineWidth = 1;

          ctx.strokeStyle =
            "rgba(255,255,255,0.35)";

          ctx.stroke();

          ctx.restore();

        }

      }

    };

    chart = new Chart(canvas,{

      type: selector.value,

      data:{

        labels: labels,

        datasets:[

          {

            label:name,

            data:values,

            borderColor:primaryColor,

            backgroundColor:
              primaryColor + "33",

            borderWidth:3,

            tension:0.45,

            pointRadius:2,

            pointHoverRadius:5,

            fill:false,

            yAxisID:"y"

          },

          {

            label:secondKPI,

            data:secondValues,

            borderColor:secondaryColor,

            backgroundColor:
              secondaryColor + "33",

            borderWidth:2,

            borderDash:[5,5],

            tension:0.45,

            pointRadius:1,

            fill:false,

            yAxisID:"y1"

          }

        ]

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
              color:"white",
              usePointStyle:true
            }

          },

          tooltip:{

            backgroundColor:
              "rgba(15,23,42,0.95)",

            borderColor:"#3b82f6",

            borderWidth:1

          }

        },

        scales:{

          x:{

            grid:{
              color:"rgba(180,180,180,0.08)"
            },

            ticks:{
              color:"#cbd5e1"
            }

          },

          y:{

            position:"left",

            grid:{
              color:"rgba(180,180,180,0.08)",
              borderDash:[2,4]
            },

            ticks:{
              color:primaryColor
            }

          },

          y1:{

            position:"right",

            grid:{
              drawOnChartArea:false
            },

            ticks:{
              color:secondaryColor
            }

          }

        }

      },

      plugins:[crosshairPlugin]

    });

  }

  renderChart();

  selector.addEventListener(
    "change",
    renderChart
  );

  kpi2Selector.addEventListener(
    "change",
    renderChart
  );

  chartIndex++;

}

/* =========================
RCA
========================= */

function runRAC(data){

  let insights = [];

  insights.push({

    title:"🧠 RAC ENGINE",

    cause:
      "Dashboard operational with dual KPI analytics",

    action:
      "GeoAI + RCA layer ready"

  });

  insights.push({

    title:"📊 Smart Overlay",

    cause:
      "Dynamic KPI2 selector enabled",

    action:
      "Advanced telecom comparison analytics"

  });

  return insights;

}

function showRAC(insights){

  const container =
    document.getElementById("rac-results");

  container.innerHTML = "";

  insights.forEach(i=>{

    container.innerHTML += `

      <div class="rac-card">

        <strong>${i.title}</strong><br><br>

        <b>Cause:</b> ${i.cause}<br><br>

        <b>Action:</b> ${i.action}

      </div>

    `;

  });

}
