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
   FILTER ENGINE
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

      // ALL
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

  const insights = runRAC(data);

  showRAC(insights);

}

     /*=======================
     KPI
     ========================= */

function detectKPIType(name){

  const kpi = name.toLowerCase();

  // =========================
  // PERCENTAGE KPIs
  // =========================
  if(
    kpi.includes("rate") ||
    kpi.includes("success") ||
    kpi.includes("availability") ||
    kpi.includes("retain") ||
    kpi.includes("drop") ||
    kpi.includes("access") ||
    kpi.includes("cssr") ||
    kpi.includes("sr")
  ){
    return "percentage";
  }

  // =========================
  // RADIO KPIs
  // =========================
  if(
    kpi.includes("rsrp") ||
    kpi.includes("rsrq") ||
    kpi.includes("sinr") ||
    kpi.includes("cqi") ||
    kpi.includes("ta")
  ){
    return "radio";
  }

  // =========================
  // COUNTERS / TRAFFIC
  // =========================
  if(
    kpi.includes("traffic") ||
    kpi.includes("volume") ||
    kpi.includes("throughput") ||
    kpi.includes("users") ||
    kpi.includes("attempt") ||
    kpi.includes("paging")
  ){
    return "counter";
  }

  return "generic";
}

function calculateKPIValue(type, values){

  // REMOVE INVALID VALUES
  values = values.filter(v =>
    typeof v === "number" &&
    !isNaN(v)
  );

  if(values.length === 0) return 0;

  // =========================
  // PERCENTAGE KPIs
  // =========================
  if(type === "percentage"){

    return (
      values.reduce((a,b)=>a+b,0)
      / values.length
    ).toFixed(2);

  }

  // =========================
  // RADIO KPIs
  // =========================
  if(type === "radio"){

    return (
      values.reduce((a,b)=>a+b,0)
      / values.length
    ).toFixed(2);

  }

  // =========================
  // COUNTERS
  // =========================
  if(type === "counter"){

    return values
      .reduce((a,b)=>a+b,0)
      .toLocaleString();

  }

  // =========================
  // GENERIC
  // =========================
  return (
    values.reduce((a,b)=>a+b,0)
    / values.length
  ).toFixed(2);

}

function createKPI(name, values){

  const type =
    detectKPIType(name);

  const result =
    calculateKPIValue(type, values);

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

function createChart(name, values, data){

  const type =
    detectKPIType(name);

  // =========================
  // CREATE CONTAINER
  // =========================

  const container =
    document.createElement("div");

  container.className = "chart-box";
  container.style.height = "420px";

  // =========================
  // CREATE SELECTOR
  // =========================

  const selector =
    document.createElement("select");

  selector.innerHTML = `
    <option value="line">line</option>
    <option value="bar">bar</option>
    <option value="doughnut">doughnut</option>
    <option value="pie">pie</option>
    <option value="scatter">scatter</option>
  `;

  container.appendChild(selector);

  // =========================
  // CREATE CANVAS
  // =========================

  const canvas =
    document.createElement("canvas");

  container.appendChild(canvas);

  // APPEND ONLY ONCE
  document
    .querySelector(".charts-grid")
    .appendChild(container);

  // =========================
  // LABEL ENGINE
  // =========================

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
            k.toLowerCase().includes("month")
          )

          ||

          keys.find(k =>
            typeof row[k] === "string"
          )

          ||

          keys[0];

        return row[xKey] || `Row ${i+1}`;

      });

  // =========================
  // AXIS LOGIC
  // =========================

  let yAxis = {};

  // PERCENTAGE KPI
  if(type === "percentage"){

    yAxis = {
      min: 0,
      max: 100
    };

  }

  // RADIO KPI
  else if(type === "radio"){

    yAxis = {

      suggestedMin:
        Math.min(...values) - 5,

      suggestedMax:
        Math.max(...values) + 5

    };

  }

  // =========================
  // CHART CONFIG
  // =========================

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
          ] + "55",

        borderColor:
          colors[
            chartIndex % colors.length
          ],

        borderWidth:3,

        tension:0.4,

        pointRadius:2,

        fill:false

      }]
    },

    options:{

      responsive:true,

      maintainAspectRatio:false,
      resizeDelay:100,

      animation:false,

      plugins:{

        legend:{
          labels:{
            color:"white"
          }
        }

      },

      scales:{

        x:{
  ticks:{
    color:"#cbd5e1"
  },

  grid:{
    color:"rgba(255,255,255,0.04)"
  }
},

        y:{
  ticks:{
    color:"#cbd5e1"
  },

  grid:{
    color:"rgba(255,255,255,0.04)"
  },

  ...yAxis
}

        }

      }

    }

  };

  // =========================
  // INITIAL CHART
  // =========================

  const ctx = canvas.getContext("2d");

let chart =
    new Chart(ctx, chartConfig);

  // =========================
  // CHART TYPE SWITCHER
  // =========================

  selector.addEventListener("change",()=>{

  // DESTROY OLD CHART
  if(chart){
    chart.destroy();
  }

  // REMOVE OLD CANVAS
  container.querySelector("canvas").remove();

  // CREATE CLEAN NEW CANVAS
  const freshCanvas =
    document.createElement("canvas");

  // RESET HEIGHT
  freshCanvas.height = 320;

  container.appendChild(freshCanvas);

  // UPDATE TYPE
  chartConfig.type =
    selector.value;

  // RECREATE CHART
  const freshCtx =
    freshCanvas.getContext("2d");

chart =
    new Chart(freshCtx, chartConfig);

});

  chartIndex++;




/* =========================
   RAC ENGINE
========================= */

function runRAC(data){

  let insights = [];

  insights.push({

    title:"🧠 RAC ENGINE",

    cause:"Dashboard loaded successfully",

    action:"Charts & KPIs operational"

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

        <strong>${i.title}</strong><br>

        <b>Cause:</b> ${i.cause}<br>

        <b>Action:</b> ${i.action}

      </div>

    `;

  });

}
