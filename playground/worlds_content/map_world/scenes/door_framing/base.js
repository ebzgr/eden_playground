(function () {
  const PG = window.Playground;
  if (!PG) return;
  const worldId = (window.__PLAYGROUND__ || {}).worldId || "map_world";
  if (!PG.isPreview()) PG.initTracker().catch(console.error);

  document.getElementById("btn-back-map")?.addEventListener("click", () => {
    PG.goToScene(worldId, "map", PG.ensureWorldSession(worldId));
  });

  const rollBtn = document.getElementById("btn-roll");
  const rollerText = document.getElementById("roller-text");
  const rollerIcon = document.getElementById("roller-icon");
  const result = document.getElementById("access-result");
  const icons = ["🎲", "🎯", "⭐", "💎", "👑"];

  rollBtn?.addEventListener("click", () => {
    if (rollBtn.disabled) return;
    rollBtn.disabled = true;
    let n = 0;
    const spin = setInterval(() => {
      if (rollerIcon) rollerIcon.textContent = icons[n % icons.length];
      n += 1;
      if (n > 12) {
        clearInterval(spin);
        if (rollerText) rollerText.textContent = "Access granted!";
        if (rollerIcon) rollerIcon.textContent = "👑";
        if (result) result.hidden = false;
      }
    }, 120);
  });
})();
