(function () {
  const PG = window.Playground;
  const btn = document.getElementById("btn-open-map");
  const orbSlots = Array.from(document.querySelectorAll(".mw-orb-slot"));

  if (!PG || !btn) return;

  const worldId = (window.__PLAYGROUND__ || {}).worldId || "map_world";

  function applyGrantedOrbIds(orbIds) {
    const granted = new Set(
      (Array.isArray(orbIds) ? orbIds : []).map((id) => String(id))
    );
    orbSlots.forEach((slot) => {
      const orbId = slot.getAttribute("data-orb-id");
      slot.classList.toggle("is-granted", granted.has(orbId));
    });
  }

  btn.addEventListener("click", () => {
    const sessionId = PG.ensureWorldSession(worldId);
    PG.goToScene(worldId, "map", sessionId);
  });

  if (!PG.isPreview()) {
    PG.ensureReturnCodeFromUrl();
    PG.postIdentity()
      .then(() => PG.initTracker())
      .then(() => PG.getState("journey.orbs"))
      .then(applyGrantedOrbIds)
      .catch(console.error);
  }
})();
