let rawData = [];
let globalFilters = {};

// =====================
// FILE LOAD
// =====================
document.getElementById("fileInput").addEventListener("change", function(e){

  Papa.parse(e.target.files[0], {
    header: true,
    dynamicTyping: true,

    complete: function(results){

      rawData = results.data.filter(
        row => Object.keys(row).length > 0
      );

      createFilters(rawData);

      redrawDashboard();
    }
  });

});

// =====================
// FILTER ENGINE
// =====================
function createFilters(data){

  const container = document.getElementById("filters-container");

  container.innerHTML = "";

  const keys = Object.keys(data[0]);

  keys.forEach(key => {

    const values = [...new Set(data.map(d => d[key]))];

    // ONLY TEXT FILTERS
    if(values.length < 20 && isNaN(values[0])){

      const card = document.createElement("div");

      card.className = "filter-card";

      const label = document.createElement("div");

      label.innerText = key;

      const select = document.createElement("select");

      const all = document.createElement("option");

      all.value = "";

      all.innerText = "ALL";

      select.appendChild(all);

      values.forEach(v => {

        const opt = document.createElement("option");

        opt.value = v;

        opt.innerText = v;

        select.appendChild(opt);

      });

      select.onchange = () => {

        globalFilters[key] = select.value;

        redrawDashboard();

      };

      card.appendChild(label);

      card.appendChild(select);

      container.appendChild(card);

    }

  });

}

// =====================
// APPLY FILTERS
// =====================
function applyFilters(data){

  return data.filter(row => {

    return Object.keys(globalFilters).every(key => {

      if(!globalFilters[key]) return true;

      return row[key] == globalFilters[key];

    });

  });

}

// =====================
// KPI ENGINE
// =====================
function renderKPIs(data){

  const container = document.getElementById("kpi-container");

  container.innerHTML = "";

  const keys = Object.keys(data[0]);

  let numeric = keys.filter(k => !isNaN(data[0][k]));

  // 🔥 ALL KPI CARDS
  numeric.forEach(k => {

    const sum = data.reduce(
      (a,b)=> a + Number(b[k] || 0),
      0
    );

    const div = document.createElement("div");

    div.className = "kpi";

    div.innerHTML = `
      <h3>${k}</h3>
      <p>${Math.round(sum).toLocaleString()}</p>
    `;

    container.appendChild(div);

  });

}

// =====================
// MULTI CHART ENGINE
// =====================
function renderCharts(data){

  const chartsContainer =
    document.getElementById("charts-container");

  chartsContainer.innerHTML = "";

  const keys = Object.keys(data[0]);

  let numeric =
    keys.filter(k => !isNaN(data[0][k]));

  let category =
    keys.find(k => isNaN(data[0][k]));

  numeric.forEach(metric => {

    const grouped = {};

    data.forEach(d => {

      const cat = d[category];

      const val = Number(d[metric] || 0);

      if(!grouped[cat]) grouped[cat] = 0;

      grouped[cat] += val;

    });

    // =====================
    // CHART BOX
    // =====================
    const box = document.createElement("div");

    box.className = "chart-box";

    // TITLE
    const title = document.createElement("h3");

    title.innerText = metric;

    title.style.marginBottom = "10px";

    // CANVAS
    const canvas = document.createElement("canvas");

    box.appendChild(title);

    box.appendChild(canvas);

    chartsContainer.appendChild(box);

    // =====================
    // CHART TYPE LOGIC
    // =====================
    let chartType = "bar";

    if(metric.toLowerCase().includes("rating")){
      chartType = "line";
    }

    // =====================
    // CREATE CHART
    // =====================
    new Chart(canvas, {

      type: chartType,

      data: {

        labels: Object.keys(grouped),

        datasets: [{

          label: metric,

          data: Object.values(grouped),

          backgroundColor: "#32d296",

          borderColor: "#32d296",

          borderWidth: 2,

          fill: false,

          tension: 0.3

        }]

      },

      options: {

        responsive: true,

        plugins: {

          legend: {

            labels: {

              color: "white"

            }

          }

        },

        scales: {

          x: {

            ticks: {

              color: "white"

            }

          },

          y: {

            ticks: {

              color: "white"

            }

          }

        }

      }

    });

  });

}

// =====================
// MAIN RENDER
// =====================
function redrawDashboard(){

  const filtered = applyFilters(rawData);

  renderKPIs(filtered);

  renderCharts(filtered);

}
