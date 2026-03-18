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

  for(let i = 0; i < 320; i++){
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
.nvidia-section{
  padding: 60px 0;
}

.nvidia-row{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 60px;
  max-width: 1100px;
  margin: auto;
}

.nvidia-img img{
  width: 100%;
  max-width: 450px;
  border-radius: 10px;
}

.nvidia-text{
  max-width: 500px;
}

.nvidia-text h3{
  font-size: 24px;
  margin-bottom: 10px;
}

.nvidia-text p{
  color: #b8c3e6;
  margin-bottom: 10px;
}

.nvidia-text a{
  color: #32d296;
  text-decoration: none;
}
