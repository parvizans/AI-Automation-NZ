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
  if(month==="") return;

  const year = new Date().getFullYear();
  const days = new Date(year, parseInt(month)+1, 0).getDate();

  const tbody = document.getElementById("timesheet-body");
  tbody.innerHTML="";

  for(let i=1;i<=days;i++){
    const d = new Date(year, month, i);
    const date = d.toISOString().split('T')[0];

    const row = document.createElement("tr");

    row.innerHTML = `
      <td>${i}</td>
      <td><input type="date" value="${date}"></td>
      <td>${getDayName(d)}</td>
      <td><input type="time" value="08:00" readonly></td>
      <td><input type="time" value="18:00"></td>
      <td class="total">0</td>
      <td class="ot">0</td>
      <td class="food">-</td>
    `;

    tbody.appendChild(row);
  }
}

document.getElementById("month").addEventListener("change", generateMonth);

function goHome(){
  window.scrollTo({ top:0, behavior:"smooth" });
}

function goExpenses(){
  window.location.href = "expenses.html";
}
function goInvoice(){
  window.location.href = "invoice.html";
}
function saveToInvoice(){

  const engineer = document.getElementById("engineer").value;
  const project = document.getElementById("project").value;

  let wdDays = 0;
  let weDays = 0;
  let wdHours = 0;
  let weOT = 0;

  document.querySelectorAll("#timesheet-body tr").forEach(row => {

    const day = row.children[2].innerText;
    const hours = 10; // (you can refine later)

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
