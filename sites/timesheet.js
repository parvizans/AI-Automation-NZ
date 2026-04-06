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
  if(month === "") return;

  const year = new Date().getFullYear();
  const days = new Date(year, parseInt(month)+1, 0).getDate();

  const tbody = document.getElementById("timesheet-body");
  tbody.innerHTML = "";

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
   <input type="time" class="time-out" step="900">
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
  window.location.href = "invoice.html";
}

/* =========================
   SAVE TO INVOICE
========================= */
function saveToInvoice(){

  const engineer = document.getElementById("engineer").value;
  const project = document.getElementById("project").value;

  let wdDays = 0;
  let weDays = 0;
  let wdHours = 0;
  let weOT = 0;

  document.querySelectorAll("#timesheet-body tr").forEach(row => {

    const day = row.children[2].innerText;
    const hours = 10;

    if(day === "Sat" || day === "Sun"){
      weDays++;
      weOT += hours;
    } else {
      wdDays++;
      wdHours += hours;
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
    const timeOut = row.querySelector(".time-out")?.value;
    const foodCell = row.querySelector(".food");

    if(!foodCell) return;

    if(timeOut){

      if(location === "Outside Sydney"){
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
function calculateTimes(){

  document.querySelectorAll("#timesheet-body tr").forEach(row => {

    const timeIn = row.querySelector(".time-in")?.value;
    const timeOut = row.querySelector(".time-out")?.value;

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

    // OT = anything above 8h
    let ot = totalHours > 8 ? totalHours - 8 : 0;
    otCell.innerText = ot.toFixed(1);

  });

}
/* =========================
   SINGLE CLEAN LISTENER (FINAL)
========================= */
document.addEventListener("change", function(e){

  // TIME IN / TIME OUT
  if(
    e.target.classList.contains("time-in") ||
    e.target.classList.contains("time-out")
  ){

    // 🔥 FORCE minutes to 00 / 15 / 30 / 45
    if(e.target.classList.contains("time-out")){

      let value = e.target.value;
      if(value){

        let [h,m] = value.split(":").map(Number);

        if(m < 15) m = 0;
        else if(m < 30) m = 15;
        else if(m < 45) m = 30;
        else m = 45;

        e.target.value =
          String(h).padStart(2,'0') + ":" +
          String(m).padStart(2,'0');
      }
    }

    // 🔥 UPDATE CALCULATIONS
    calculateTimes();
    updateAllowance();
  }

  // LOCATION CHANGE
  if(e.target.classList.contains("row-location")){
    updateAllowance();
  }

});


/* =========================
   INITIAL LOAD
========================= */
window.addEventListener("load", function(){
  updateAllowance();
});
