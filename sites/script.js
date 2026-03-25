console.log("START JS");

// ==========================
// ⭐ STARS BACKGROUND
// ==========================
window.addEventListener("load", function(){

  const canvas = document.getElementById("stars");
  if(!canvas) return;

  const ctx = canvas.getContext("2d");

  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  let stars = [];

  for(let i = 0; i < 400; i++){
    stars.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      size: Math.random() * 2,
      speed: Math.random() * 1 + 0.2
    });
  }

  function drawStars(){
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    stars.forEach(star => {

      ctx.shadowBlur = 10;
      ctx.shadowColor = "#32d296";

      ctx.fillStyle = "#32d296";
      ctx.beginPath();
      ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2);
      ctx.fill();

      if(Math.random() < 0.004){
        ctx.beginPath();
        ctx.moveTo(star.x, star.y);
        ctx.lineTo(star.x + 60, star.y + 10);
        ctx.strokeStyle = "#32d296";
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      star.y += star.speed;

      if(star.y > canvas.height){
        star.y = 0;
        star.x = Math.random() * canvas.width;
      }
    });

    requestAnimationFrame(drawStars);
  }

  drawStars();
});
  

  function drawStars(){
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    stars.forEach(star => {
      ctx.fillStyle = "#32d296";
      ctx.beginPath();
      ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2);
      ctx.fill();

      star.y += star.speed;

      if(star.y > canvas.height){
        star.y = 0;
        star.x = Math.random() * canvas.width;
      }
    });

    requestAnimationFrame(drawStars);
  }

  drawStars();
});


// ==========================
// 🚀 5G THROUGHPUT
// ==========================
function calculate5G(){

  let sinr = parseFloat(document.getElementById("sinr").value);
  let bandwidth = parseFloat(document.getElementById("bandwidth").value);
  let mimo = parseFloat(document.getElementById("mimo").value);
  let bler = parseFloat(document.getElementById("bler").value);
  let overhead = parseFloat(document.getElementById("overhead").value);
  let duplex = parseFloat(document.getElementById("duplex").value);
  let freq = parseFloat(document.getElementById("freqBand").value);

  if(isNaN(sinr) || isNaN(bandwidth)){
    alert("Invalid input");
    return;
  }

  let efficiency = Math.max(0.2, sinr / 10);

  let throughput =
    bandwidth *
    mimo *
    efficiency *
    duplex *
    (1 - overhead/100) *
    (1 - bler/100);

  // Frequency factor
  if(freq < 1000) throughput *= 0.5;
  else if(freq < 3000) throughput *= 0.8;
  else if(freq < 6000) throughput *= 1.2;
  else throughput *= 1.8;

  throughput *= 10;

  document.getElementById("result").innerText =
    "Result: " + throughput.toFixed(2) + " Mbps";
}


// ==========================
// 📡 LINK BUDGET
// ==========================
function calculateLinkBudget(){

  let power = parseFloat(document.getElementById("lb_power").value);
  let freq = parseFloat(document.getElementById("lb_freq").value);
  let gain = parseFloat(document.getElementById("lb_gain").value);
  let cable = parseFloat(document.getElementById("lb_cable").value);

  let body = parseFloat(document.getElementById("lb_body").value);
  let building = parseFloat(document.getElementById("lb_building").value);
  let interference = parseFloat(document.getElementById("lb_interference").value);
  let fading = parseFloat(document.getElementById("lb_fading").value);

  let throughput = parseFloat(document.getElementById("lb_throughput").value);
  let area = parseFloat(document.getElementById("lb_area").value);
  let model = document.getElementById("lb_model").value;

  if(isNaN(power) || power <= 0){
    alert("Invalid Power");
    return;
  }

  // Power → dBm
  let powerDbm = 10 * Math.log10(power * 1000);

  let linkBudget =
    powerDbm +
    gain -
    cable -
    body -
    building -
    interference -
    fading;

  // Throughput → SINR
  let sinr = throughput <=10 ? 2 :
             throughput <=20 ? 6 :
             throughput <=30 ? 10 : 15;

  let effectiveBudget = linkBudget - (-100 + sinr);
  
  // 📡 Propagation model impact
let modelLoss;

if(model == "120"){        // Rural
  modelLoss = 20;
}
else if(model == "135"){   // Suburban
  modelLoss = 30;
}
else{                      // Urban
  modelLoss = 45;
}

  // Distance
  // 📡 Environment loss correction
let envLoss;

if(freq < 1000) envLoss = 20;
else if(freq < 3000) envLoss = 30;
else envLoss = 40;  // 3.5 GHz penalty


// 📡 NEW realistic distance
let distance = Math.pow(
  10,
  (effectiveBudget - 32.45 - 20*Math.log10(freq) - modelLoss) / 20
) * 1000;

  // Path Loss
  let pathLoss =
    32.45 +
    20*Math.log10(freq) +
    20*Math.log10(distance / 1000);

  // Sites
  let radiusKm = distance / 1000;
  let sites = area / (Math.PI * radiusKm * radiusKm);

  // OUTPUT
  document.getElementById("lb_distance").innerText =
    "Distance: " + distance.toFixed(0) + " meters";

  document.getElementById("lb_pathloss").innerText =
    "Path Loss: " + pathLoss.toFixed(2) + " dB";

  document.getElementById("lb_budget").innerText =
    "Link Budget: " + linkBudget.toFixed(2) + " dBm";

  document.getElementById("lb_sites").innerText =
    "Sites Required: " + Math.ceil(sites);
}
