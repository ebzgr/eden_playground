(function () {
  const cfg = window.__PLAYGROUND__ || {};
  const apiBase = cfg.apiBase || "";

  async function ensureIdentity() {
    let code = localStorage.getItem("return_code");
    const res = await fetch(apiBase + "/identity", {
      method: "POST",
      credentials: "include",
      headers: code ? { "X-Return-Code": code } : {},
    });
    const data = await res.json();
    localStorage.setItem("return_code", data.return_code);
    return data;
  }

  async function grantConsent() {
    await fetch(apiBase + "/consent", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        "X-Return-Code": localStorage.getItem("return_code"),
      },
      body: JSON.stringify({ state: "granted" }),
    });
  }

  document.getElementById("cta")?.addEventListener("click", async () => {
    await ensureIdentity();
    await grantConsent();
    if (window.Tracker) {
      Tracker.init({ apiBase, worldId: cfg.worldId, sceneId: cfg.sceneId, sessionId: cfg.sessionId });
      Tracker.event("cta_click", {});
    }
    const res = await fetch(
      apiBase +
        "/worlds/" +
        cfg.worldId +
        "/scenes/" +
        cfg.sceneId +
        "/transition",
      {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-Return-Code": localStorage.getItem("return_code"),
        },
        body: JSON.stringify({ event: "cta_click", session_id: cfg.sessionId }),
      }
    );
    const data = await res.json();
    if (data.next_scene) {
      window.location.href =
        apiBase +
        "/worlds/" +
        cfg.worldId +
        "/scenes/" +
        data.next_scene +
        "/view?session_id=" +
        encodeURIComponent(cfg.sessionId);
    }
  });

  ensureIdentity().then(grantConsent);
})();
