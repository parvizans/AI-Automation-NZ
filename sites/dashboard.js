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

      createChart(key, values);

    }

  });

  const insights = runRAC(data);

  showRAC(insights);

}

/* =========================
   KPI
========================= */

function createKPI(name, values){

  const avg =
    (
      values.reduce((a,b)=>a+b,0)
      / values.length
    ).toFixed(2);

  const card =
    document.createElement("div");

  card.className = "kpi-card";

  card.innerHTML = `
    <h3>${name}</h3>
    <p>${Number(avg).toLocaleString()}</p>
  `;

  document
    .querySelector(".kpi-grid")
    .appendChild(card);

}

/* =========================
   CHART ENGINE
========================= */

function createChart(name, values){

  const container =
    document.createElement("div");

  container.className = "chart-box";

  const canvas =
    document.createElement("canvas");

  container.appendChild(canvas);

  document
    .querySelector(".charts-grid")
    .appendChild(container);

  new Chart(canvas,{

    type:"bar",

    data:{

     labels:
     data
    .slice(-values.length)
    .map((row,i)=>{

      const firstKey =
        Object.keys(row)[0];

      return row[firstKey] || `Row ${i+1}`;

    }),

      datasets:[{

        label:name,

        data:values,

        backgroundColor:
          colors[
            chartIndex % colors.length
          ] + "66",

        borderColor:
          colors[
            chartIndex % colors.length
          ],

        borderWidth:2

      }]
    },

    options:{
      responsive:true,
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
            color:"white"
          }
        },
        y:{
          ticks:{
            color:"white"
          }
        }
      }
    }

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
