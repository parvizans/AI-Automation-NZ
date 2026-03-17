const canvas = document.getElementById("networkCanvas");

if(canvas){

const ctx = canvas.getContext("2d");

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

let nodes = [];

for(let i=0;i<60;i++){
  nodes.push({
    x:Math.random()*canvas.width,
    y:Math.random()*canvas.height,
    vx:(Math.random()-0.5)*0.5,
    vy:(Math.random()-0.5)*0.5
  });
}

function animate(){
  ctx.clearRect(0,0,canvas.width,canvas.height);

  nodes.forEach(n=>{
    n.x+=n.vx;
    n.y+=n.vy;

    if(n.x<0||n.x>canvas.width) n.vx*=-1;
    if(n.y<0||n.y>canvas.height) n.vy*=-1;

    ctx.beginPath();
    ctx.arc(n.x,n.y,2,0,Math.PI*2);
    ctx.fillStyle="#32d296";
    ctx.fill();
  });

  requestAnimationFrame(animate);
}

animate();

  function calculateThroughput(){

  let bw = document.getElementById("bw").value;
  let se = document.getElementById("se").value;
  let layers = document.getElementById("layers").value;
  let overhead = document.getElementById("overhead").value;

  let throughput = bw * se * layers * (1 - overhead/100);

  document.getElementById("result").innerText =
    "Result: " + throughput.toFixed(2) + " Mbps";
}

}
