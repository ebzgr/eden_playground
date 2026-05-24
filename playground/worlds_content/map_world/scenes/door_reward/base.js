(function () {
  const PG = window.Playground;
  if (!PG) return;
  const worldId = (window.__PLAYGROUND__ || {}).worldId || "map_world";
  if (!PG.isPreview()) PG.initTracker().catch(console.error);

  document.getElementById("btn-back-map")?.addEventListener("click", () => {
    PG.goToScene(worldId, "map", PG.ensureWorldSession(worldId));
  });

  let score = 0;
  const scoreEl = document.getElementById("total-score");
  const statusEl = document.getElementById("player-status");
  const flash = document.getElementById("bonus-flash");
  const statuses = ["Select", "Bronze", "Silver", "Gold", "Platinum"];

  document.getElementById("btn-push")?.addEventListener("click", () => {
    score += 10;
    if (scoreEl) scoreEl.textContent = String(score);
    const idx = Math.min(statuses.length - 1, Math.floor(score / 30));
    if (statusEl) statusEl.textContent = statuses[idx];
    if (flash) {
      flash.hidden = false;
      setTimeout(() => {
        flash.hidden = true;
      }, 800);
    }
  });
})();
