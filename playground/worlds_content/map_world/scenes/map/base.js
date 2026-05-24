(function () {
  const PG = window.Playground;
  if (!PG) return;

  const worldId = (window.__PLAYGROUND__ || {}).worldId || "map_world";

  if (!PG.isPreview()) {
    PG.initTracker().catch(console.error);
  }

  document.querySelectorAll("[data-door]").forEach((el) => {
    el.addEventListener("click", () => {
      const sceneId = el.getAttribute("data-door");
      if (!sceneId) return;
      const sessionId = PG.ensureWorldSession(worldId);
      PG.goToScene(worldId, sceneId, sessionId);
    });
  });
})();
