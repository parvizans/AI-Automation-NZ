let globalData = [];

function buildFilters(data) {
  const filterDiv = document.getElementById("filters");
  filterDiv.innerHTML = "";

  const keys = Object.keys(data[0]);

  keys.forEach(key => {
    const uniqueValues = [...new Set(data.map(d => d[key]))];

    if (uniqueValues.length < 20 && typeof uniqueValues[0] !== "number") {
      const select = document.createElement("select");
      select.multiple = true;
      select.dataset.key = key;

      uniqueValues.forEach(val => {
        const opt = document.createElement("option");
        opt.value = val;
        opt.innerText = val;
        select.appendChild(opt);
      });

      filterDiv.appendChild(document.createTextNode(key));
      filterDiv.appendChild(select);
    }
  });
}
