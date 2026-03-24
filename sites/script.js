// ⭐ STARS BACKGROUND
window.onload = function(){

  const canvas = document.getElementById("stars");

  if(!canvas){
    console.log("Canvas not found");
    return;
  }

  const ctx = canvas.getContext("2d");

  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  let stars = [];

  for(let i = 0; i < 620; i++){
    stars.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      size: Math.random() * 2,
      speed: Math.random() * 2.5 + 0.5
    });
  }

  function drawStars(){
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    stars.forEach(star => {

      // ⭐ star
      ctx.fillStyle = "rgba(50,210,150," + Math.random() + ")";
      ctx.beginPath();
      ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2);
      ctx.fill();

      // ⭐ shooting star
      if(Math.random() < 0.002){
        ctx.beginPath();
        ctx.moveTo(star.x, star.y);
        ctx.lineTo(star.x + 20, star.y + 5);
        ctx.strokeStyle = "#32d296";
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
};


// 🚀 CALCULATOR
function calculate5G(){

  const mode = document.getElementById("mode").value;
  let sinr = parseFloat(document.getElementById("sinr").value);
  let mcs = 0;

  const bandwidth = parseFloat(document.getElementById("bandwidth").value);
  const mimo = parseFloat(document.getElementById("mimo").value);
  const overhead = parseFloat(document.getElementById("overhead").value);
  const duplex = parseFloat(document.getElementById("duplex").value);
  const bler = parseFloat(document.getElementById("bler").value);
  const freq = parseFloat(document.getElementById("freqBand").value);
  
let freqFactor = 1;   // ✅ MUST be here (outside if)
if (freq < 1000) {
  freqFactor = 0.4;   // was 0.6
} else if (freq < 3000) {
  freqFactor = 0.7;   // was 0.8
} else if (freq < 6000) {
  freqFactor = 1.2;   // was 1.0
} else {
  freqFactor = 2.0;   // was 1.5
}


  

  // SINR → CQI mapping
  const sinrToCqi = [
    {sinr:-5, cqi:0},{sinr:-2, cqi:1},{sinr:0, cqi:2},{sinr:2, cqi:3},
    {sinr:4, cqi:4},{sinr:6, cqi:5},{sinr:8, cqi:6},{sinr:10, cqi:7},
    {sinr:12, cqi:8},{sinr:14, cqi:9},{sinr:16, cqi:10},
    {sinr:18, cqi:11},{sinr:20, cqi:12},{sinr:22, cqi:13},{sinr:24, cqi:14},{sinr:26, cqi:15}
  ];

  let cqi = 0;

  if(mode === "auto"){
    for(let i=0;i<sinrToCqi.length;i++){
      if(sinr >= sinrToCqi[i].sinr){
        cqi = sinrToCqi[i].cqi;
      }
    }
    mcs = Math.min(27, Math.floor(cqi * 1.7));
    // 📡 Frequency Band Impact
let freqFactor = 1;

if (freq < 1000) {
  freqFactor = 0.6;   // Low band (coverage focused)
} else if (freq < 3000) {
  freqFactor = 0.8;   // Mid band LTE/NR
} else if (freq < 6000) {
  freqFactor = 1.0;   // C-band (optimal 5G)
} else {
  freqFactor = 1.5;   // mmWave (high capacity)
}
  }

  const specEff = [
    0.2344,0.377,0.6016,0.877,1.1758,1.4766,1.6953,1.9141,
    2.1602,2.4063,2.5703,2.7305,3.0293,3.3223,3.6094,
    3.9023,4.2129,4.5234,4.8164,5.1152,5.332,5.5547,
    6.2266,6.9141,7.4063
  ];

  let efficiency = specEff[mcs] || 1;

let throughput = 
  bandwidth * efficiency * mimo * duplex *
  (1 - overhead/100) *
  (1 - bler/100);

// 📡 Apply frequency impact
throughput = throughput * freqFactor;

  throughput = throughput * 10;

  document.getElementById("result").innerText =
    `Result: ${throughput.toFixed(2)} Mbps (CQI: ${cqi}, MCS: ${mcs})`;
}
document.getElementById("calcBtn").addEventListener("click", calculate);

function getValue(id) {
  let val = parseFloat(document.getElementById(id).value);
  return isNaN(val) ? 0 : val;
}
function calculate() {

  try {

    // INPUTS
    let power = getValue("power");
    let bodyLoss = getValue("bodyLoss");
    let buildingLoss = getValue("buildingLoss");
    let interference = getValue("interference");
    let vegetation = getValue("vegetation");
    let antennaGain = getValue("antennaGain");
    let frequency = getValue("frequency");
    let cableLoss = getValue("cableLoss");
    let fading = getValue("fading");
    let radio = getValue("radio");
    let model = getValue("model");

    if (power <= 0 || frequency <= 0) {
      throw "Invalid input values";
    }

    // POWER CONVERSION
    let powerDbm = 10 * Math.log10(power * 1000);

    // TOTAL LOSS
    let totalLoss =
      bodyLoss +
      buildingLoss +
      interference +
      vegetation +
      fading +
      cableLoss;

    // LINK BUDGET
    let linkBudget = powerDbm + antennaGain + radio - totalLoss;

    // PATH LOSS MODEL
    let pathLoss = model + 20 * Math.log10(frequency);

    // DISTANCE (ESTIMATION)
    let distance = Math.pow(10, (linkBudget - pathLoss) / 20) * 1000;

    // OUTPUT
    document.getElementById("distance").innerText =
      "Cell Edge Distance: " + distance.toFixed(0) + " meters";

    document.getElementById("pathloss").innerText =
      "Path Loss: " + pathLoss.toFixed(2) + " dB";

    document.getElementById("linkbudget").innerText =
      "Link Budget: " + linkBudget.toFixed(2) + " dBm";

    document.getElementById("status").innerText =
      "Status: ✅ Calculation Successful";

  } catch (error) {

    document.getElementById("status").innerText =
      "Status: ❌ Error - " + error;

  }
}
