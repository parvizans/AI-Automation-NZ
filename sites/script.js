function calculate() {

  // GET VALUES
  let power = parseFloat(document.getElementById("power").value);
  let bodyLoss = parseFloat(document.getElementById("bodyLoss").value);
  let buildingLoss = parseFloat(document.getElementById("buildingLoss").value);
  let interference = parseFloat(document.getElementById("interference").value);
  let model = parseFloat(document.getElementById("model").value);
  let vegetation = parseFloat(document.getElementById("vegetation").value);
  let antennaGain = parseFloat(document.getElementById("antennaGain").value);
  let frequency = parseFloat(document.getElementById("frequency").value);
  let cableLoss = parseFloat(document.getElementById("cableLoss").value);
  let fading = parseFloat(document.getElementById("fading").value);
  let radio = parseFloat(document.getElementById("radio").value);

  // CONVERT POWER TO dBm
  let powerDbm = 10 * Math.log10(power * 1000);

  // LINK BUDGET
  let totalLoss = bodyLoss + buildingLoss + interference + vegetation + fading + cableLoss;

  let linkBudget = powerDbm + antennaGain + radio - totalLoss;

  // PATH LOSS MODEL (simplified)
  let pathLoss = model + 20 * Math.log10(frequency);

  // DISTANCE ESTIMATION
  let distance = Math.pow(10, (linkBudget - pathLoss) / 20) * 1000;

  // OUTPUT
  document.getElementById("distance").innerText =
    "Cell Edge Distance: " + distance.toFixed(0) + " meters";

  document.getElementById("pathloss").innerText =
    "Path Loss: " + pathLoss.toFixed(2) + " dB";

  document.getElementById("summary").innerText =
    "Link Budget: " + linkBudget.toFixed(2) + " dBm";
}
