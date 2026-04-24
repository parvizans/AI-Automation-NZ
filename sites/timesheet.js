// =========================
// ENGINEER / PM AUTO FILL
// =========================
document.getElementById("engineer").addEventListener("change", function(){
  const s = this.options[this.selectedIndex];
  document.getElementById("eng-email").value = s.value;
  document.getElementById("eng-phone").value = s.dataset.phone || "";
});

document.getElementById("pm").addEventListener("change", function(){
  document.getElementById("pm-email").value = this.value;
});

// =========================
// GENERATE MONTH
// =========================
function generateMonth(){

  const month = document.getElementById("month").value;
  if(month === "") return;

  const year = new Date().getFullYear();
  const days = new Date(year, parseInt(month) + 1, 0).getDate();

  const tbody = document.getElementById("timesheet-body");
  tbody.innerHTML = "";

  for(let i = 1; i <= days; i++){

    const d = new Date(year, parseInt(month), i);
    const formattedDate = d.toLocaleDateString();
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

document.getElementById("month").addEventListener("change", generateMonth);

// =========================
// CALCULATE TIMES
// =========================
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

// =========================
// FOOD ALLOWANCE
// =========================
function updateAllowance(){

  let totalFood = 0;

  document.querySelectorAll("#timesheet-body tr").forEach(row => {

    const location = row.querySelector(".row-location")?.value;
    const hour = row.querySelector(".time-out-hour")?.value;
    const minute = row.querySelector(".time-out-minute")?.value;
    const foodCell = row.querySelector(".food");

    const worked = (hour !== "00" || minute !== "00");

    let food = 0;

    if(worked && location === "Outside Sydney"){
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

// =========================
// SUMMARY
// =========================
function updateSummary(){

  let wdDays=0, wdHours=0, wdOT=0, weDays=0, weOT=0;

  document.querySelectorAll("#timesheet-body tr").forEach(row=>{
    const day=row.children[2].innerText;
    const total=parseFloat(row.querySelector(".total").innerText)||0;

    if(day==="Sat"||day==="Sun"){
      weDays++;
      weOT+=total>8 ? total-8 : total;
    }else{
      if(total>=8) wdDays++;
      else wdHours+=total;
      wdOT+=total>8 ? total-8 : 0;
    }
  });

  document.getElementById("wd-days").innerText=wdDays;
  document.getElementById("wd-hours").innerText=wdHours.toFixed(1);
  document.getElementById("wd-ot").innerText=wdOT.toFixed(1);
  document.getElementById("we-days").innerText=weDays;
  document.getElementById("we-ot").innerText=weOT.toFixed(1);

  localStorage.setItem("invoiceData", JSON.stringify({
    engineer: document.getElementById("engineer").value,
    project: document.getElementById("project").value,
    wdDays, wdHours, wdOT, weDays, weOT
  }));
}

// =========================
// EVENTS
// =========================
document.addEventListener("change", function(e){
  if(e.target.matches("input, select")){
    calculateTimes();
    updateAllowance();
    updateSummary();
  }
});

// =========================
// NAVIGATION
// =========================
function goHome(){
  window.scrollTo({ top:0, behavior:"smooth" });
}

function goInvoice(){
  saveTimesheet();
  window.location.href = "invoice.html";
}

function goExpenses(){
  saveTimesheet();
  window.location.href = "expenses.html";
}

// =========================
// SAVE / RESET
// =========================
function saveTimesheet(){
  localStorage.setItem("timesheetBackup", document.getElementById("timesheet-body").innerHTML);
  alert("Saved ✅");
}

function resetTimesheet(){
  if(confirm("Reset all data?")){
    localStorage.clear();
    location.reload();
  }
}

// =========================
// LOAD
// =========================
window.addEventListener("load", function(){

  const saved = localStorage.getItem("timesheetBackup");

  if(saved){
    document.getElementById("timesheet-body").innerHTML = saved;
  } else {
    generateMonth();
  }

});
