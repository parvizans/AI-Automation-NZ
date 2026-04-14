// ================= NAVIGATION =================
function goHome(){
  window.location.href = "timesheet.html";
}

function goInvoice(){
  window.open("invoice.html", "_blank");
}

function goExpenses(){
  window.location.href = "expenses.html";
}

// ================= SAVE / RESET =================
function saveTimesheet(){
  localStorage.setItem("timesheetBackup", document.getElementById("timesheet-body").innerHTML);
  alert("Saved ✅");
}

function resetTimesheet(){
  localStorage.removeItem("timesheetBackup");
  location.reload();
}

// ================= LOAD =================
function loadTimesheet(){
  const saved = localStorage.getItem("timesheetBackup");
  if(saved){
    document.getElementById("timesheet-body").innerHTML = saved;
  }
}

// ================= GENERATE MONTH =================
function generateMonth(){

  const month = document.getElementById("month").value;
  if(month === "") return;

  const year = new Date().getFullYear();
  const days = new Date(year, parseInt(month)+1, 0).getDate();

  const tbody = document.getElementById("timesheet-body");
  tbody.innerHTML = "";

  for(let i=1;i<=days;i++){

    const d = new Date(year, parseInt(month), i);
    const date = d.toLocaleDateString("en-GB");
    const weekday = d.toLocaleDateString("en-US", { weekday: "short" });

    const row = document.createElement("tr");

    row.innerHTML = `
      <td>${i}</td>
      <td>${date}</td>
      <td>${weekday}</td>
      <td><input type="time" value="08:00"></td>
      <td>--</td>
      <td>0</td>
      <td>0</td>
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

  updateAllowance();
}

// ================= FOOD =================
function updateAllowance(){

  document.querySelectorAll("#timesheet-body tr").forEach(row => {

    const location = row.querySelector(".row-location")?.value;
    const foodCell = row.querySelector(".food");

    if(location === "Outside Sydney"){
      foodCell.innerText = "$50";
      foodCell.style.color = "#32d296";
    } else {
      foodCell.innerText = "-";
      foodCell.style.color = "#888";
    }
  });
}

// ================= INIT =================
window.addEventListener("load", function(){

  loadTimesheet();

  document.getElementById("month")
    .addEventListener("change", generateMonth);

});
