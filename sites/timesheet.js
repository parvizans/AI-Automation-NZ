/* =========================
   ENGINEER / PM AUTO FILL
========================= */
document.getElementById("engineer").addEventListener("change", function(){
  const s = this.options[this.selectedIndex];
  document.getElementById("eng-email").value = s.value;
  document.getElementById("eng-phone").value = s.dataset.phone || "";
});

document.getElementById("pm").addEventListener("change", function(){
  document.getElementById("pm-email").value = this.value;
});

/* =========================
   HELPERS
========================= */
function getDayName(date){
  return ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"][date.getDay()];
}

/* =========================
   GENERATE MONTH
========================= */
function generateMonth(){

  const month = document.getElementById("month").value;
  if(month === "") return;

  const year = new Date().getFullYear();
  const days = new Date(year, parseInt(month) + 1, 0).getDate();

  const tbody = document.getElementById("timesheet-body");
  tbody.innerHTML = "";

  for(let i = 1; i <= days; i++){

    const d = new Date(year, parseInt(month), i);

    const day = String(d.getDate()).padStart(2, '0');
    const mon = String(d.getMonth() + 1).padStart(2, '0');
    const yearFull = d.getFullYear();

    const formattedDate = `${day}/${mon}/${yearFull}`;
    const weekday = d.toLocaleDateString("en-US", { weekday: "short" });

    const row = document.createElement("tr");

    row.innerHTML = `
      <td>${i}</td>
      <td><input type="text" value="${formattedDate}" readonly></td>
      <td>${weekday}</td>

      <td><input type="time" class="time-in" value="08:00"></td>

      <td>
        <select class="time-out-hour">
          ${[...Array(24).keys()].map(h =>
            `<option value="${h}">${String(h).padStart(2,'0')}</option>`
          ).join('')}
        </select>

        <select class="time-out-minute">
          <option value="0">00</option>
          <option value="15">15</option>
          <option value="30">30</option>
          <option value="45">45</option>
        </select>
      </td>

      <td class="total">0</td>
      <td class="ot">0</td>

      <td>
        <select class="row-location">
          <option>Sydney</option>
          <option>Outside Sydney</option>
        </select>
      </td>

      <td class="food">-</td>
    `;

    tbody.appendChild(row);
  }

  calculateTimes();
  updateAllowance();
  updateSummary();
}

// OUTSIDE ↓↓↓
document.getElementById("month").addEventListener("change", generateMonth);

/* =========================
   NAVIGATION
========================= */
function goHome(){
  window.scrollTo({ top:0, behavior:"smooth" });
}

function goInvoice(){
  saveToInvoice();
  window.location.href = "invoice.html";
}

function goExpenses(){
  window.location.href = "expenses.html";
}

/* =========================
   CALCULATE TIMES
========================= */
function calculateTimes(){

  document.querySelectorAll("#timesheet-body tr").forEach(row => {

    const timeIn = row.querySelector(".time-in")?.value;
    const hour = row.querySelector(".time-out-hour")?.value;
    const minute = row.querySelector(".time-out-minute")?.value;

    if(!timeIn) return;

    const [inH, inM] = timeIn.split(":").map(Number);
    const outH = parseInt(hour || 0);
    const outM = parseInt(minute || 0);

    let total = (outH + outM/60) - (inH + inM/60);
    if(total < 0) total = 0;

    row.querySelector(".total").innerText = total.toFixed(1);

    let ot = total > 8 ? total - 8 : 0;
    row.querySelector(".ot").innerText = ot.toFixed(1);
  });

  updateSummary();
}

/* =========================
   FOOD ALLOWANCE
========================= */
function updateAllowance(){

  let totalFood = 0;

  document.querySelectorAll("#timesheet-body tr").forEach(row => {

    const locationEl = row.querySelector(".row-location");
    const foodCell = row.querySelector(".food");

    const hour = row.querySelector(".time-out-hour")?.value;
    const minute = row.querySelector(".time-out-minute")?.value;

    if(!locationEl || !foodCell) return;

    const location = locationEl.value;

    // ✅ check if worked
    const worked = hour && (hour !== "00" || minute !== "00");

    let food = 0;

    // ✅ FINAL CONDITION
    if(worked && location.toLowerCase().includes("outside")){
      food = 50;
      foodCell.innerText = "$50";
      foodCell.style.color = "#32d296";
    } else {
      foodCell.innerText = "-";
      foodCell.style.color = "#888";
    }

    totalFood += food;

  });

  localStorage.setItem("foodTotal", totalFood);
}
/* =========================
   SUMMARY
========================= */
function updateSummary(){

  let wdDays = 0;
  let wdHours = 0;
  let wdOT = 0;

  let weDays = 0;
  let weOT = 0;

  document.querySelectorAll("#timesheet-body tr").forEach(row => {

    const day = row.children[2].innerText;
    const total = parseFloat(row.querySelector(".total").innerText) || 0;

    if(day === "Sat" || day === "Sun"){

      if(total >= 8){
        weDays++;
        weOT += (total - 8);
      } else {
        weOT += total;
      }

    } else {

      if(total >= 8){
        wdDays++;
        wdOT += (total - 8);
      } else if(total > 0){
        wdHours += total;
      }

    }

  });

  document.getElementById("wd-days").innerText = wdDays;
  document.getElementById("wd-hours").innerText = wdHours.toFixed(1);
  document.getElementById("wd-ot").innerText = wdOT.toFixed(1);

  document.getElementById("we-days").innerText = weDays;
  document.getElementById("we-ot").innerText = weOT.toFixed(1);

  // SAVE TO LOCALSTORAGE
  localStorage.setItem("invoiceData", JSON.stringify({
    engineer: document.getElementById("engineer").value,
    project: document.getElementById("project").value,
    wdDays,
    wdHours,
    wdOT,
    weDays,
    weOT
  }));
}

/* =========================
   SAVE TO INVOICE
========================= */
function saveToInvoice(){

  saveTimesheet(); // 🔥 IMPORTANT

  // Save summary values
  localStorage.setItem("totalHours", document.getElementById("total-hours")?.innerText || 0);
  localStorage.setItem("totalOT", document.getElementById("total-ot")?.innerText || 0);
  localStorage.setItem("foodTotal", localStorage.getItem("foodTotal") || 0);

  alert("🔥 Sent to Invoice!");

  window.open("invoice.html", "_blank"); // optional but recommended
}

/* =========================
   EVENTS
========================= */
document.addEventListener("change", function(e){

  if(
    e.target.classList.contains("time-in") ||
    e.target.classList.contains("time-out-hour") ||
    e.target.classList.contains("time-out-minute") ||
    e.target.classList.contains("row-location")
  ){
    calculateTimes();
    updateAllowance();
    updateSummary();
    saveTimesheet(); // 🔥 GLOBAL SAVE
  }

});

/* =========================
   SAVE / LOAD / RESET
========================= */
function saveTimesheet(){

  // SAVE TABLE
  localStorage.setItem("timesheetBackup", document.getElementById("timesheet-body").innerHTML);

  // 🔥 SAVE GLOBAL HEADER DATA
  localStorage.setItem("projectName", document.getElementById("project")?.value || "");
  localStorage.setItem("engineer", document.getElementById("engineer")?.value || "");
  localStorage.setItem("engEmail", document.getElementById("eng-email")?.value || "");
  localStorage.setItem("engPhone", document.getElementById("eng-phone")?.value || "");
  localStorage.setItem("locationGlobal", document.getElementById("location")?.value || "");

  // TOAST
  const toast = document.getElementById("saveToast");
  if(toast){
    toast.style.display = "block";
    setTimeout(() => toast.style.display = "none", 1000);
  }
}

function loadTimesheet(){

  const saved = localStorage.getItem("timesheetBackup");

  if(saved){
    document.getElementById("timesheet-body").innerHTML = saved;
  }

  // 🔥 RESTORE HEADER DATA
  document.getElementById("project").value = localStorage.getItem("projectName") || "";
  document.getElementById("engineer").value = localStorage.getItem("engineer") || "";
  document.getElementById("eng-email").value = localStorage.getItem("engEmail") || "";
  document.getElementById("eng-phone").value = localStorage.getItem("engPhone") || "";
  document.getElementById("location").value = localStorage.getItem("locationGlobal") || "";

  calculateTimes();
  updateAllowance();
  updateSummary();
}

function resetTimesheet(){
  localStorage.clear(); // 🔥 FULL RESET SYSTEM
  location.reload();
}
/* =========================
   INITIAL LOAD
========================= */
window.addEventListener("load", function(){

  const saved = localStorage.getItem("timesheetBackup");

  if(saved){
    document.getElementById("timesheet-body").innerHTML = saved;
  } else {
    generateMonth();
  }

  loadTimesheet(); // 🔥 FULL RESTORE

});


/* =========================
   LOAD DATA FROM TIMESHEET & EXPENSES
========================= */
window.addEventListener("load", function(){

  // 🔥 LOAD TIMESHEET DATA
  const data = JSON.parse(localStorage.getItem("invoiceData") || "{}");

  if(data){
    document.getElementById("project").value = data.project || "";
    document.getElementById("engineer").value = data.engineer || "";

    document.getElementById("wd-days").innerText = data.wdDays || 0;
    document.getElementById("wd-hours").innerText = data.wdHours || 0;
    document.getElementById("wd-ot").innerText = data.wdOT || 0;

    document.getElementById("we-days").innerText = data.weDays || 0;
    document.getElementById("we-ot").innerText = data.weOT || 0;
  }

  // 🔥 FOOD
  let food = localStorage.getItem("foodTotal") || 0;
  if(document.getElementById("foodQty")){
    document.getElementById("foodQty").innerText = food / 50;
  }

  // 🔥 EXPENSES
  let expenses = localStorage.getItem("invoiceExpenses") || 0;
  if(document.getElementById("expensesInput")){
    document.getElementById("expensesInput").value = expenses;
  }

});
