(function () {
  const PG = window.Playground;
  if (!PG) return;
  const worldId = (window.__PLAYGROUND__ || {}).worldId || "map_world";
  if (!PG.isPreview()) PG.initTracker().catch(console.error);

  document.getElementById("btn-back-map")?.addEventListener("click", () => {
    PG.goToScene(worldId, "map", PG.ensureWorldSession(worldId));
  });
})();
