(() => {
  const $ = (id) => document.getElementById(id);

  const apiBaseEl = $("apiBase");
  const themeBtn = $("themeBtn");

  const fileEl = $("file");
  const uploadBtn = $("uploadBtn");
  const uploadMsg = $("uploadMsg");

  const datasetIdEl = $("datasetId");
  const columnEl = $("column");
  const algoEl = $("algo");
  const binsWrap = $("binsWrap");
  const binsEl = $("bins");
  const runBtn = $("runBtn");
  const runMsg = $("runMsg");

  const outEl = $("out");
  const chartCanvas = $("chart");

  const THEME_KEY = "stats_lab_theme";
  const lastTheme = localStorage.getItem(THEME_KEY);
  if (lastTheme) document.documentElement.dataset.theme = lastTheme;

  themeBtn.addEventListener("click", () => {
    const current = document.documentElement.dataset.theme === "light" ? "light" : "dark";
    const next = current === "light" ? "dark" : "light";
    document.documentElement.dataset.theme = next;
    localStorage.setItem(THEME_KEY, next);
  });

  function setMsg(el, text){ el.textContent = text || ""; }

  function apiUrl(path){
    const base = (apiBaseEl.value || "").trim().replace(/\/+$/, "");
    return base + path;
  }

  function populateColumns(cols){
    columnEl.innerHTML = "";
    for (const c of cols){
      const opt = document.createElement("option");
      opt.value = c;
      opt.textContent = c;
      columnEl.appendChild(opt);
    }
  }

  let chart = null;
  function clearChart(){
    if (chart) { chart.destroy(); chart = null; }
  }

  function renderJSON(obj){
    outEl.textContent = JSON.stringify(obj, null, 2);
  }

  function renderHistogram(hist){
    clearChart();
    chart = new Chart(chartCanvas, {
      type: "bar",
      data: {
        labels: hist.labels,
        datasets: [{ label: "Count", data: hist.counts }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: true } },
        scales: { x: { ticks: { maxRotation: 60, minRotation: 40 } } }
      }
    });
  }

  function algoNeedsBins(algo){
    return algo === "histogram";
  }

  algoEl.addEventListener("change", () => {
    binsWrap.style.display = algoNeedsBins(algoEl.value) ? "block" : "none";
  });
  binsWrap.style.display = algoNeedsBins(algoEl.value) ? "block" : "none";

  uploadBtn.addEventListener("click", async () => {
    clearChart();
    renderJSON({});
    setMsg(uploadMsg, "");
    setMsg(runMsg, "");

    const f = fileEl.files?.[0];
    if (!f){
      setMsg(uploadMsg, "Choose a CSV file first.");
      return;
    }
    if (!f.name.toLowerCase().endsWith(".csv")){
      setMsg(uploadMsg, "Please upload a .csv file.");
      return;
    }

    const fd = new FormData();
    fd.append("file", f);

    uploadBtn.disabled = true;
    setMsg(uploadMsg, "Uploading…");

    try{
      const res = await fetch(apiUrl("/upload"), { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok){
        throw new Error(data?.detail || "Upload failed.");
      }
      datasetIdEl.value = data.dataset_id;
      populateColumns(data.columns);
      setMsg(uploadMsg, "Uploaded. Now pick a column + algorithm.");
    }catch(e){
      setMsg(uploadMsg, String(e.message || e));
    }finally{
      uploadBtn.disabled = false;
    }
  });

  runBtn.addEventListener("click", async () => {
    clearChart();
    setMsg(runMsg, "");
    const dataset_id = (datasetIdEl.value || "").trim();
    const column = columnEl.value;
    const algorithm = algoEl.value;
    const bins = Number(binsEl.value || 12);

    if (!dataset_id){
      setMsg(runMsg, "Upload a file first.");
      return;
    }
    if (!column){
      setMsg(runMsg, "Choose a column.");
      return;
    }

    runBtn.disabled = true;
    setMsg(runMsg, "Running…");

    try{
      const payload = { dataset_id, column, algorithm, bins };
      const res = await fetch(apiUrl("/analyze"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok){
        throw new Error(data?.detail || "Analyze failed.");
      }
      renderJSON(data);
      if (algorithm === "histogram"){
        renderHistogram(data.result);
      }
      setMsg(runMsg, "Done.");
      setTimeout(() => setMsg(runMsg, ""), 1200);
    }catch(e){
      renderJSON({ error: String(e.message || e) });
      setMsg(runMsg, String(e.message || e));
    }finally{
      runBtn.disabled = false;
    }
  });

  // initial
  renderJSON({ info: "Start by uploading a CSV." });
})();