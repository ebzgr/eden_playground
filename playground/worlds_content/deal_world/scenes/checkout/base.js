document.getElementById("done")?.addEventListener("click", () => {
  const cfg = window.__PLAYGROUND__ || {};
  window.location.href =
    (cfg.apiBase || "") +
    "/worlds/deal_world/scenes/intro/view?session_id=" +
    encodeURIComponent(cfg.sessionId || "");
});
