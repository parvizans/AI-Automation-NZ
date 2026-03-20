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

    ctx.fillStyle = "#32d296";

   stars.forEach(star => {
  ctx.beginPath();
  ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2);
  ctx.fill();

  // ⭐ Twinkle effect
  ctx.fillStyle = "rgba(50,210,150," + Math.random() + ")";

  // ⭐ Shooting star
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

ctx.fillStyle = "rgba(50,210,150," + Math.random() + ")";

if(Math.random() < 0.002){
  ctx.beginPath();
  ctx.moveTo(star.x, star.y);
  ctx.lineTo(star.x + 20, star.y + 5);
  ctx.strokeStyle = "#32d296";
  ctx.stroke();
}
function calculate5G(){

  const mode = document.getElementById("mode").value;
  let sinr = parseFloat(document.getElementById("sinr").value);
  let mcs = parseInt(document.getElementById("mcs").value);

  const bandwidth = parseFloat(document.getElementById("bandwidth").value);
  const mimo = parseFloat(document.getElementById("mimo").value);
  const overhead = parseFloat(document.getElementById("overhead").value);
  const duplex = parseFloat(document.getElementById("duplex").value);
  const bler = parseFloat(document.getElementById("bler").value);

  // SINR → CQI mapping (approx real-world)
  const sinrToCqi = [
    {sinr:-5, cqi:0},{sinr:-2, cqi:1},{sinr:0, cqi:2},{sinr:2, cqi:3},
    {sinr:4, cqi:4},{sinr:6, cqi:5},{sinr:8, cqi:6},{sinr:10, cqi:7},
    {sinr:12, cqi:8},{sinr:14, cqi:9},{sinr:16, cqi:10},
    {sinr:18, cqi:11},{sinr:20, cqi:12},{sinr:22, cqi:13},{sinr:24, cqi:14},{sinr:26, cqi:15}
  ];

  let cqi = 0;

if(mode === "auto"){
  label.innerText = "MCS (Auto Calculated)";
} else {
  label.innerText = "MCS (Manual Input)";
      }
    }
    // CQI → MCS approximation
    mcs = Math.min(27, Math.floor(cqi * 1.7));
  }

  // Spectral efficiency (3GPP approx)
  const specEff = [
    0.2344,0.377,0.6016,0.877,1.1758,1.4766,1.6953,1.9141,
    2.1602,2.4063,2.5703,2.7305,3.0293,3.3223,3.6094,
    3.9023,4.2129,4.5234,4.8164,5.1152,5.332,5.5547,
    6.2266,6.9141,7.4063
  ];

  let efficiency = specEff[mcs] || 1;

  // FINAL THROUGHPUT
  let throughput =
    bandwidth * efficiency * mimo * duplex *
    (1 - overhead/100) *
    (1 - bler/100);

  throughput = throughput * 10;

  document.getElementById("result").innerText =
    `Result: ${throughput.toFixed(2)} Mbps 
     (CQI: ${cqi}, MCS: ${mcs})`;
}
function toggleMode(){
  const mode = document.getElementById("mode").value;
  const mcsInput = document.getElementById("mcs");
  const sinrInput = document.getElementById("sinr");

  if(mode === "auto"){
    mcsInput.disabled = true;
    sinrInput.disabled = false;
  } else {
    mcsInput.disabled = false;
    sinrInput.disabled = true;
  }
}
window.onload = toggleMode;
