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
      speed: Math.random() * 1.5 + 0.5
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

function calculateLinkBudget(){

  // 📥 INPUTS
  const freq = parseFloat(document.getElementById("freqLB").value);
  const distance = parseFloat(document.getElementById("distance").value);
  const txPower = parseFloat(document.getElementById("txPower").value);
  const txGain = parseFloat(document.getElementById("txGain").value);
  const rxGain = parseFloat(document.getElementById("rxGain").value);
  const losses = parseFloat(document.getElementById("losses").value);
  const bodyLoss = parseFloat(document.getElementById("bodyLoss").value);
  const vegLoss = parseFloat(document.getElementById("vegLoss").value);
  const area = parseFloat(document.getElementById("area").value);
  const cellThroughput = parseFloat(document.getElementById("cellTHP").value);
  const propModel = document.getElementById("propModel").value;

  // 📡 PROPAGATION MODEL LOSS
  let modelLoss = 0;
  if (propModel === "urban") modelLoss = 20;
  else if (propModel === "suburban") modelLoss = 10;
  else if (propModel === "rural") modelLoss = 5;

  // 📡 FREE SPACE PATH LOSS
  const fspl = 32.44 + 20 * Math.log10(freq) + 20 * Math.log10(distance);

  // 📡 TOTAL LOSS
  const totalLoss = losses + bodyLoss + vegLoss + modelLoss;

  // 📡 RECEIVED POWER
  const rxPower = txPower + txGain + rxGain - fspl - totalLoss;

  // 📡 LINK QUALITY
  let quality = "";
  if (rxPower > -80) quality = "Excellent";
  else if (rxPower > -95) quality = "Good";
  else if (rxPower > -105) quality = "Fair";
  else quality = "Poor";

  // 📡 REQUIRED RSRP (BASED ON THROUGHPUT)
  let requiredRSRP;
  if (cellThroughput <= 5) requiredRSRP = -105;
  else if (cellThroughput <= 20) requiredRSRP = -95;
  else if (cellThroughput <= 50) requiredRSRP = -85;
  else requiredRSRP = -75;

  // 📡 CELL RADIUS ESTIMATION
  let radius;
  if (rxPower >= requiredRSRP) {
    radius = 1.2;
  } else if (rxPower >= requiredRSRP - 10) {
    radius = 0.8;
  } else {
    radius = 0.4;
  }

  // 📡 CELL AREA
  const cellArea = Math.PI * radius * radius;

  // 📡 NUMBER OF SITES
  const sites = area / cellArea;

  // 📊 RESULT 1 (LINK)
  document.getElementById("lbResult").innerHTML = `
    <h3>Path Loss: ${fspl.toFixed(2)} dB</h3>
    <h3>Total Loss: ${totalLoss.toFixed(2)} dB</h3>
    <h3>Received Power: ${rxPower.toFixed(2)} dBm</h3>
    <h3>Link Quality: ${quality}</h3>
  `;

  // 📊 RESULT 2 (COVERAGE)
  document.getElementById("coverageResult").innerHTML = `
    <h3>Required RSRP: ${requiredRSRP} dBm</h3>
    <h3>Cell Edge Throughput: ${cellThroughput} Mbps</h3>
    <h3>Estimated Cell Radius: ${(radius * 1000).toFixed(0)} meters</h3>
    <h3>Number of Sites Required: ${Math.ceil(sites)}</h3>
  `;
}
