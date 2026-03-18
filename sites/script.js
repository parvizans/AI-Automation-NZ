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

  for(let i = 0; i < 220; i++){
    stars.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      size: Math.random() * 2,
      speed: Math.random() * 1.5 + 0.5
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
