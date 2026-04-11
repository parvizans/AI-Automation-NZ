document.getElementById("engineer").addEventListener("change", function(){
  const s = this.options[this.selectedIndex];
  document.getElementById("eng-email").value = s.value;
  document.getElementById("eng-phone").value = s.dataset.phone || "";
});

document.getElementById("pm").addEventListener("change", function(){
  document.getElementById("pm-email").value = this.value;
});

function getDayName(date){
  return ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"][date.getDay()];
}

function generateMonth(){
  const month = document.getElementById("month").value;

  if(month === "") return;  // 🚫 do nothing if not selected

  const year = new Date().getFullYear();
  const days = new Date(year, parseInt(month)+1, 0).getDate();

  const tbody = document.getElementById("timesheet-body");
 
  tbody.innerHTML = "";   // ✅ THIS IS THE ONLY LINE YOU NEED

  for(let i=1;i<=days;i++){

    const d = new Date(year, month, i);
    const date = d.toISOString().split('T')[0];

    const row = document.createElement("tr");

row.innerHTML = `
  <td>${i}</td>
  <td><input type="date" value="${date}"></td>
  <td>${getDayName(d)}</td>

  <td><input type="time" class="time-in" value="08:00"></td>

 <td>
  <select class="time-out-hour">
    ${[...Array(24).keys()].map(h =>
      `<option value="${h}">${String(h).padStart(2,'0')}</option>`
    ).join('')}
  </select>

  <select class="time-out-minute">
    <option value="00">00</option>
    <option value="15">15</option>
    <option value="30">30</option>
    <option value="45">45</option>
  </select>
</td>

  <td class="total">0</td>
  <td class="ot">0</td>

  <td>
    <select class="row-location">
      <option value="Sydney">Sydney</option>
      <option value="Outside Sydney">Outside Sydney</option>
    </select>
  </td>

  <td class="food">-</td>
`

tbody.appendChild(row);
}
}

document.getElementById("month").addEventListener("change", generateMonth);

/* =========================
   NAVIGATION
========================= */
function goHome(){
  window.scrollTo({ top:0, behavior:"smooth" });
}

function goExpenses(){
  window.location.href = "expenses.html";
}

function goInvoice(){
  saveToInvoice();   // 🔥 ADD THIS
  window.location.href = "invoice.html";
}

/* =========================
   SAVE TO INVOICE
========================= */
function saveToInvoice(){

  const engineer = document.getElementById("engineer").value;
  const project = document.getElementById("project").value;
  
  let weDays = 0;
  let wdDays = 0;
  let weHours = 0;
  let wdHours = 0;
  let weOT = 0;
  
  document.querySelectorAll("#timesheet-body tr").forEach(row => {

    const day = row.children[2].innerText;

    const total = parseFloat(row.querySelector(".total").innerText) || 0;

  if(day === "Sat" || day === "Sun"){

  if(total >= 8){
    weDays++;
  }

  weOT += total;

} else {

  if(total > 0){
    wdDays++;
    wdHours += total;
  }

}
  });

  const data = {
    engineer,
    project,
    wdDays,
    weDays,
    wdHours,
    weOT
  };

  localStorage.setItem("invoiceData", JSON.stringify(data));

  alert("🔥 Sent to Invoice!");
}

/* =========================
   FOOD ALLOWANCE
========================= */
function updateAllowance(){

  document.querySelectorAll("#timesheet-body tr").forEach(row => {

    const location = row.querySelector(".row-location")?.value;
    const hour = row.querySelector(".time-out-hour")?.value;
    const minute = row.querySelector(".time-out-minute")?.value;

    let timeOut = null;
    if(hour !== undefined && minute !== undefined){
      timeOut = `${hour}:${minute}`;
    }

    const foodCell = row.querySelector(".food");
    if(!foodCell) return;

    if(timeOut){
     if(location === "Outside Sydney" && total > 0){
        foodCell.innerText = "$50";
        foodCell.style.color = "#32d296";
      } else {
        foodCell.innerText = "-";
        foodCell.style.color = "#888";
      }
    } else {
      foodCell.innerText = "-";
      foodCell.style.color = "#888";
    }

  });

}

/* =========================
   CALCULATE TIMES
========================= */
function calculateTimes(){

  document.querySelectorAll("#timesheet-body tr").forEach(row => {

    const timeIn = row.querySelector(".time-in")?.value;
    const hour = row.querySelector(".time-out-hour")?.value;
    const minute = row.querySelector(".time-out-minute")?.value;

    let timeOut = null;
    if(hour !== undefined && minute !== undefined){
      timeOut = `${hour}:${minute}`;
    }

    const totalCell = row.querySelector(".total");
    const otCell = row.querySelector(".ot");

    if(!timeIn || !timeOut){
      totalCell.innerText = "0";
      otCell.innerText = "0";
      return;
    }

    const [inH, inM] = timeIn.split(":").map(Number);
    const [outH, outM] = timeOut.split(":").map(Number);

    let totalHours = (outH + outM/60) - (inH + inM/60);
    if(totalHours < 0) totalHours = 0;

    totalCell.innerText = totalHours.toFixed(1);

    let ot = totalHours > 8 ? totalHours - 8 : 0;
    otCell.innerText = ot.toFixed(1);

  });

  updateSummary(); // 🔥 CRITICAL
}

/* =========================
   SUMMARY
========================= */
function updateSummary(){

  let wdDays = 0;
  let weDays = 0;
  let weHours = 0;
  let wdOT = 0;
  let weOT = 0;

  document.querySelectorAll("#timesheet-body tr").forEach(row => {

    const day = row.children[2].innerText;
    const total = parseFloat(row.querySelector(".total").innerText) || 0;

    // 🔴 WEEKEND
    if(day === "Sat" || day === "Sun"){

      if(total >= 8){
        weDays++;   // full day
        weOT += (total - 8);   // ONLY extra is OT
      } else {
        weOT += total;  // all hours OT if <8
      }

    }

    // 🔵 WEEKDAY
    else {

      if(total >= 8){
        wdDays++;                 // full day
        wdOT += (total - 8);      // only extra
      } 
      else if(total > 0){
        wdHours += total;         // half-day bucket
      }

    }

  });

  // UI UPDATE
  document.getElementById("wd-days").innerText = wdDays;
  document.getElementById("wd-hours").innerText = wdHours.toFixed(1);
  document.getElementById("wd-ot").innerText = wdOT.toFixed(1);

  document.getElementById("we-days").innerText = weDays;
  document.getElementById("we-ot").innerText = weOT.toFixed(1);

  // SAVE → INVOICE
// ✅ ALWAYS RECALCULATE BEFORE SAVE
updateSummary();

localStorage.setItem("invoiceData", JSON.stringify({
  engineer: document.getElementById("engineer").value,
  project: document.getElementById("project").value,
  wdDays,
  wdHours,
  wdOT,
  weDays,
  weOT
}));

console.log("✅ SAVED DATA:", {
  wdDays, wdHours, wdOT, weDays, weOT
});
/* =========================
   INITIAL LOAD
========================= */
window.addEventListener("load", function(){

  const today = new Date();

document.getElementById("month").value = today.getMonth();

  loadTimesheet();
  calculateTimes();
  updateAllowance();
  updateSummary();

});

/* =========================
   EVENTS
========================= */
document.addEventListener("change", function(e){

  if(
    e.target.classList.contains("time-in") ||
    e.target.classList.contains("time-out-hour") ||
    e.target.classList.contains("time-out-minute")
  ){
    calculateTimes();
    updateAllowance();
  }

  if(e.target.classList.contains("row-location")){
    updateAllowance();
  }

});

/* =========================
   Save.Load,Reset Timesheet
========================= */
function saveTimesheet(){
  localStorage.setItem("timesheetBackup", document.getElementById("timesheet-body").innerHTML);
  alert("Saved ✅");
}

function loadTimesheet(){
  const saved = localStorage.getItem("timesheetBackup");
  if(saved){
    document.getElementById("timesheet-body").innerHTML = saved;
  }
}

function resetTimesheet(){
  localStorage.removeItem("timesheetBackup");
  location.reload();
}
