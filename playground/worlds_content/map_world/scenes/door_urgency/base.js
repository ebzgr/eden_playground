(function () {
  const PG = window.Playground;
  if (!PG) return;
  const worldId = (window.__PLAYGROUND__ || {}).worldId || "map_world";
  if (!PG.isPreview()) PG.initTracker().catch(console.error);

  document.getElementById("btn-back-map")?.addEventListener("click", () => {
    PG.goToScene(worldId, "map", PG.ensureWorldSession(worldId));
  });

  const el = document.getElementById("countdown");
  if (!el) return;
  let sec = 30;
  const t = setInterval(() => {
    sec = Math.max(0, sec - 1);
    el.textContent = String(Math.floor(sec / 60)).padStart(2, "0") + ":" + String(sec % 60).padStart(2, "0");
    if (sec === 0) clearInterval(t);
  }, 1000);
})();
