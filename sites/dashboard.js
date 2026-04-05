// CSV PARSER
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

// GET COLUMN
function getColumn(data, key) {
  return data.map(row => {
    let val = row[key];
    return val !== undefined && val !== "" ? parseFloat(val) : null;
  });
}

// LATEST VALUE
function getLatestValue(arr) {
  const valid = arr.filter(v => v !== null && !isNaN(v));
  return valid.length ? valid[valid.length - 1] : "-";
}

// FILE UPLOAD
document.getElementById("fileInput").addEventListener("change", function(e) {
  const file = e.target.files[0];
  const reader = new FileReader();

  reader.onload = function(event) {
    const data = parseCSV(event.target.result);
    buildDashboard(data);
    generateRCA(data);
  };

  reader.readAsText(file);
});

// MAIN ENGINE
function buildDashboard(data) {

  if (!data || data.length === 0) return;

  document.querySelector(".charts-grid").innerHTML = "";

const keys = Object.keys(data[0]).filter(k => {
  const name = k.toLowerCase();

  return (
    name.includes("throughput") ||
    name.includes("rsrp") ||
    name.includes("rsrq") ||
    name.includes("sinr") ||
    name.includes("snir") ||
    name.includes("drop")
  );
});
  keys.forEach((key, index) => {

    const values = getColumn(data, key);

    createChart(key, values, index);
    updateKPICard(key, values);

  });
}

// CREATE CHART
function createChart(title, values, index) {

  let color = "#32d296";
  if (title.toLowerCase().includes("drop")) color = "#ff6b6b";
  if (title.toLowerCase().includes("rsrp")) color = "#4dabf7";
  if (title.toLowerCase().includes("sinr")) color = "#ffd43b";

  const container = document.createElement("div");
  container.className = "chart-card";

  const canvas = document.createElement("canvas");

  container.appendChild(canvas);
  document.querySelector(".charts-grid").appendChild(container);

  new Chart(canvas, {
    type: "line",
    data: {
      labels: values.map((_, i) => i + 1),
      datasets: [{
        label: title,
        data: values,
        borderColor: color,
        backgroundColor: color + "33",
        borderWidth: 2,
        tension: 0.3
      }]
    }
  });
}

// KPI UPDATE
function updateKPICard(key, values) {

  const el = document.getElementById(key.toLowerCase());
  if (!el) return;

  let val = getLatestValue(values);
  if (val === "-") {
    el.innerText = "--";
    return;
  }

  if (key.toLowerCase().includes("rsrp")) el.innerText = val + " dBm";
  else if (key.toLowerCase().includes("rsrq") || key.toLowerCase().includes("sinr")) el.innerText = val + " dB";
  else if (key.toLowerCase().includes("drop")) el.innerText = val + " %";
  else if (key.toLowerCase().includes("throughput")) el.innerText = val + " Mbps";
  else el.innerText = val;
}

// RCA ENGINE
function generateRCA(data) {

  let insights = [];

const keys = Object.keys(data[0]).filter(k => {
  const name = k.toLowerCase();
  return (
    name.includes("throughput") ||
    name.includes("rsrp") ||
    name.includes("rsrq") ||
    name.includes("sinr") ||
    name.includes("snir") ||
    name.includes("drop")
  );
});

  keys.forEach(key => {

    const values = getColumn(data, key);
    const latest = getLatestValue(values);

    if (latest === "-" || isNaN(latest)) return;

    const name = key.toLowerCase();

   if (name.includes("rsrp") && latest < -110)
  insights.push("🔴 Critical: Coverage failure");

else if (name.includes("rsrp") && latest < -105)
  insights.push("🟠 Warning: Weak coverage");

    if ((name.includes("sinr") || name.includes("snir")) && latest < 5)
   insights.push("⚠ Interference suspected: Low SINR indicates signal quality degradation likely caused by interference or noise.");
    
    if (name.includes("drop") && latest > 2)
      insights.push("⚠ High drop rate (mobility issue)");

    if (name.includes("throughput") && latest < 5)
      insights.push("⚠ Low throughput (possible congestion)");
  });

  displayAlerts(insights);
}

// SHOW ALERTS
function displayAlerts(insights) {

  const alertBox = document.querySelector(".alerts");
  alertBox.innerHTML = "<h3>🚨 Network Insights</h3>";

  if (insights.length === 0) {
    alertBox.innerHTML += "<div class='alert'>✅ Network OK</div>";
    return;
  }

  insights.forEach(msg => {
    const div = document.createElement("div");
    div.className = "alert";
    div.innerText = msg;
    alertBox.appendChild(div);
  });
}
insights.push("⚠ Coverage issue: Low RSRP indicates weak signal strength, likely due to distance or obstruction.");

insights.push("⚠ Mobility issue: High drop rate suggests handover failure or unstable radio conditions.");

insights.push("⚠ Congestion: Low throughput despite acceptable signal conditions indicates capacity limitation.");
