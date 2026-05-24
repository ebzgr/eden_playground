/**
 * Shared helpers for world scenes (identity, sessions, navigation, tracking).
 */
(function (global) {
  const SESSION_KEY = "playground_session";

  function cfg() {
    return global.__PLAYGROUND__ || {};
  }

  function isPreview() {
    const c = cfg();
    return !!(c.previewMode || c.preview);
  }

  function apiBase() {
    return cfg().apiBase || "";
  }

  function headers() {
    const h = { "Content-Type": "application/json" };
    if (isPreview()) h["X-Playground-Preview"] = "1";
    const code = localStorage.getItem("return_code");
    if (code) h["X-Return-Code"] = code;
    return h;
  }

  async function postIdentity() {
    if (isPreview()) return { consent_state: "preview", preview: true };
    const code = localStorage.getItem("return_code");
    const res = await fetch(apiBase() + "/identity", {
      method: "POST",
      credentials: "include",
      headers: code ? { "X-Return-Code": code } : {},
    });
    if (!res.ok) throw new Error("identity failed");
    const data = await res.json();
    localStorage.setItem("return_code", data.return_code);
    return data;
  }

  async function postConsent(state) {
    if (isPreview()) return { state: state, preview: true };
    const res = await fetch(apiBase() + "/consent", {
      method: "POST",
      credentials: "include",
      headers: headers(),
      body: JSON.stringify({ state }),
    });
    if (!res.ok) throw new Error("consent failed");
    return res.json();
  }

  function ensureWorldSession(worldId) {
    if (isPreview()) {
      return "preview-" + worldId;
    }
    let stored = null;
    try {
      stored = JSON.parse(localStorage.getItem(SESSION_KEY) || "null");
    } catch (_) {
      stored = null;
    }
    if (stored && stored.world_id === worldId && stored.session_id) {
      return stored.session_id;
    }
    const sessionId =
      typeof crypto !== "undefined" && crypto.randomUUID
        ? crypto.randomUUID()
        : "sess-" + Math.random().toString(36).slice(2);
    localStorage.setItem(
      SESSION_KEY,
      JSON.stringify({
        world_id: worldId,
        session_id: sessionId,
        started_at: new Date().toISOString(),
      })
    );
    return sessionId;
  }

  function getWorldSession(worldId) {
    if (isPreview()) return "preview-" + worldId;
    try {
      const stored = JSON.parse(localStorage.getItem(SESSION_KEY) || "null");
      if (stored && stored.world_id === worldId) return stored.session_id;
    } catch (_) {}
    return null;
  }

  function sceneViewUrl(worldId, sceneId, sessionId, opts) {
    opts = opts || {};
    const c = cfg();
    if (isPreview() || opts.preview) {
      let url =
        apiBase() +
        "/admin/worlds/" +
        encodeURIComponent(worldId) +
        "/scenes/" +
        encodeURIComponent(sceneId) +
        "/preview";
      const params = [];
      if (opts.version || c.versionId) {
        params.push("version=" + encodeURIComponent(opts.version || c.versionId));
      }
      if (params.length) url += "?" + params.join("&");
      return url;
    }
    let url =
      apiBase() +
      "/worlds/" +
      encodeURIComponent(worldId) +
      "/scenes/" +
      encodeURIComponent(sceneId) +
      "/view";
    if (sessionId) {
      url += "?session_id=" + encodeURIComponent(sessionId);
    }
    if (opts.version) {
      url += (sessionId ? "&" : "?") + "force_version=" + encodeURIComponent(opts.version);
    }
    return url;
  }

  function goToScene(worldId, sceneId, sessionId) {
    const c = cfg();
    if (global.PlaygroundEvents && global.PlaygroundEvents.markExit) {
      global.PlaygroundEvents.markExit("nav");
    }
    window.location.href = sceneViewUrl(worldId, sceneId, sessionId);
  }

  async function initTracker() {
    if (!global.Tracker) return;
    const c = cfg();
    await Tracker.init({
      apiBase: apiBase(),
      worldId: c.worldId,
      sceneId: c.sceneId,
      sessionId: c.sessionId || getWorldSession(c.worldId),
      versionId: c.versionId,
      experiment: c.experiment,
      experimentArms: c.experimentArms,
      previewMode: isPreview(),
    });
    if (global.PlaygroundEvents && global.PlaygroundEvents.init) {
      const debug =
        new URLSearchParams(global.location.search).get("pg_debug") === "1";
      global.PlaygroundEvents.init({ debug: debug });
    }
  }

  function markSceneExit(reason) {
    if (global.PlaygroundEvents && global.PlaygroundEvents.markExit) {
      global.PlaygroundEvents.markExit(reason);
    }
  }

  /**
   * Preferred way to record events — attaches experiment + version automatically.
   */
  function track(eventType, payload) {
    if (isPreview()) return;
    if (!global.Tracker) return;
    Tracker.event(eventType, payload);
  }

  global.Playground = {
    postIdentity,
    postConsent,
    ensureWorldSession,
    getWorldSession,
    sceneViewUrl,
    goToScene,
    initTracker,
    track,
    markSceneExit,
    isPreview,
    headers,
    apiBase,
  };
})(typeof window !== "undefined" ? window : globalThis);
