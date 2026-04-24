// =========================
// GLOBAL DATA MODEL
// =========================
function getProjectData(){
  return JSON.parse(localStorage.getItem("projectData") || "{}");
}

function saveProjectData(data){
  localStorage.setItem("projectData", JSON.stringify(data));
}

// =========================
// ENGINEER / PM AUTO FILL
// =========================
document.getElementById("engineer").addEventListener("change", function(){
  const s = this.options[this.selectedIndex];
  document.getElementById("eng-email").value = s.value;
  document.getElementById("eng-phone").value = s.dataset.phone || "";
});

// =========================
// GENERATE MONTH
// =========================
function generateMonth(){
  const month = document.getElementById("month").value;
  if(month === "") return;

  const year = new Date().getFullYear();
  const days = new Date(year, parseInt(month)+1, 0).getDate();

  const tbody = document.getElementById("timesheet-body");
  tbody.innerHTML = "";

  for(let i=1;i<=days;i++){
    const d = new Date(year, month, i);
    const row = document.createElement("tr");

    row.innerHTML = `
      <td>${i}</td>
      <td>${d.toLocaleDateString()}</td>
      <td>${d.toLocaleDateString("en-US",{weekday:"short"})}</td>
      <td><input type="time" class="time-in" value="08:00"></td>
      <td><input type="time" class="time-out"></td>
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
}

// =========================
// CALCULATE
// =========================
function calculate(){
  let wdDays=0, wdHours=0, wdOT=0, weDays=0, weOT=0;

  document.querySelectorAll("#timesheet-body tr").forEach(row=>{
    const ti = row.querySelector(".time-in").value;
    const to = row.querySelector(".time-out").value;

    if(!to) return;

    const [ih,im]=ti.split(":").map(Number);
    const [oh,om]=to.split(":").map(Number);

    let total=(oh+om/60)-(ih+im/60);
    if(total<0) total=0;

    row.querySelector(".total").innerText = total.toFixed(1);

    let ot = total>8 ? total-8 : 0;
    row.querySelector(".ot").innerText = ot.toFixed(1);

    const day=row.children[2].innerText;

    if(day==="Sat"||day==="Sun"){
      weDays++;
      weOT+=ot;
    }else{
      if(total>=8) wdDays++;
      else wdHours+=total;
      wdOT+=ot;
    }
  });

  document.getElementById("wd-days").innerText=wdDays;
  document.getElementById("wd-hours").innerText=wdHours.toFixed(1);
  document.getElementById("wd-ot").innerText=wdOT.toFixed(1);
  document.getElementById("we-days").innerText=weDays;
  document.getElementById("we-ot").innerText=weOT.toFixed(1);

  saveData();
}

// =========================
// SAVE DATA (🔥 CORE)
// =========================
function saveData(){
  const data = getProjectData();

  data.engineer = document.getElementById("engineer").value;
  data.project = document.getElementById("project").value;

 data.timesheet = {
  wdDays: Number(document.getElementById("wd-days").innerText),
  wdHours: Number(document.getElementById("wd-hours").innerText),
  wdOT: Number(document.getElementById("wd-ot").innerText),
  weDays: Number(document.getElementById("we-days").innerText),
  weOT: Number(document.getElementById("we-ot").innerText)
};

  saveProjectData(data);
}

// =========================
// EVENTS
// =========================
document.addEventListener("change", e=>{
  if(e.target.matches("input, select")){
    calculate();
    updateAllowance();   // 🔥 ADD THIS
  }
});

// INIT
document.getElementById("month").addEventListener("change", generateMonth);
// =========================
// NAVIGATION FIX 🔥
// =========================
function goInvoice(){
  saveData(); // save before leaving
  window.location.href = "invoice.html";
}

function goExpenses(){
  saveData(); // save before leaving
  window.location.href = "expenses.html";
}
// =========================
// FOOD ALLOWANCE (FIXED)
// =========================
function updateAllowance(){

  let totalFood = 0;

  document.querySelectorAll("#timesheet-body tr").forEach(row => {

    const locationEl = row.querySelector(".row-location");
    const foodCell = row.querySelector(".food");

    const hour = row.querySelector(".time-out-hour")?.value;

    if(!locationEl || !foodCell) return;

    const location = locationEl.value;

    const worked = hour && hour !== "00";

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
