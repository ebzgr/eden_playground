/**
 * Playground event handler — auto lifecycle events and declarative bindings.
 * Requires tracker.js and playground.js (init via Playground.initTracker).
 */
(function (global) {
  const PREV_SCENE_KEY = "pg:prev_scene";
  const DEBUG_KEY = "pg:debug";

  let enterTs = 0;
  let exitSent = false;
  let debug = false;
  let bound = false;

  function pgCfg() {
    return global.__PLAYGROUND__ || {};
  }

  function isDebugEnabled() {
    try {
      if (new URLSearchParams(global.location.search).get("pg_debug") === "1") {
        localStorage.setItem(DEBUG_KEY, "1");
        return true;
      }
      return localStorage.getItem(DEBUG_KEY) === "1";
    } catch (_) {
      return false;
    }
  }

  function log(msg, data) {
    if (!debug) return;
    if (data !== undefined) {
      console.log("[pg]", msg, data);
    } else {
      console.log("[pg]", msg);
    }
  }

  function readPrevScene() {
    try {
      const raw = sessionStorage.getItem(PREV_SCENE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (_) {
      return null;
    }
  }

  function writePrevScene(worldId, sceneId) {
    try {
      sessionStorage.setItem(
        PREV_SCENE_KEY,
        JSON.stringify({ world: worldId, scene: sceneId })
      );
    } catch (_) {}
  }

  function canTrack() {
    const Tracker = global.Tracker;
    if (!Tracker) return false;
    if (Tracker.isPreview && Tracker.isPreview()) return false;
    if (Tracker.isConsentGranted && !Tracker.isConsentGranted()) return false;
    return true;
  }

  function track(eventType, payload) {
    if (!canTrack()) {
      log("skip (preview/consent)", eventType);
      return;
    }
    log(eventType, payload);
    if (global.Playground && global.Playground.track) {
      global.Playground.track(eventType, payload);
    } else if (global.Tracker) {
      global.Tracker.event(eventType, payload);
    }
  }

  function parsePayload(el) {
    const raw = el.getAttribute("data-pg-payload");
    if (!raw) return {};
    try {
      return JSON.parse(raw);
    } catch (e) {
      log("bad data-pg-payload JSON", raw);
      return {};
    }
  }

  function formPayload(el) {
    const base = parsePayload(el);
    const tag = (el.tagName || "").toLowerCase();
    if (tag === "input" || tag === "select" || tag === "textarea") {
      if (el.type === "checkbox" || el.type === "radio") {
        base.checked = !!el.checked;
        if (el.value) base.value = el.value;
      } else {
        base.value = el.value;
      }
    }
    return base;
  }

  function bindDeclarative(root) {
    const scope = root || document;
    const nodes = scope.querySelectorAll("[data-pg-event]");
    nodes.forEach(function (el) {
      const eventType = el.getAttribute("data-pg-event");
      if (!eventType) return;

      const tag = (el.tagName || "").toLowerCase();
      const useChange =
        tag === "input" || tag === "select" || tag === "textarea";

      if (useChange) {
        el.addEventListener("change", function () {
          track(eventType, formPayload(el));
        });
      } else {
        el.addEventListener("click", function () {
          track(eventType, formPayload(el));
        });
      }
    });
    log("declarative bindings", nodes.length);
  }

  function sendSceneExit(reason) {
    if (exitSent) return;
    exitSent = true;

    const c = pgCfg();
    const durationMs = enterTs ? Math.max(0, Date.now() - enterTs) : 0;
    const payload = { duration_ms: durationMs, reason: reason || "unload" };

    writePrevScene(c.worldId, c.sceneId);
    log("scene_exit", payload);

    if (!canTrack()) return;

    if (global.Tracker && global.Tracker.sendImmediate) {
      global.Tracker.sendImmediate("scene_exit", payload);
    } else {
      track("scene_exit", payload);
      if (global.Tracker && global.Tracker.flushNow) {
        global.Tracker.flushNow();
      }
    }
  }

  function onVisibilityChange() {
    if (document.visibilityState === "hidden") {
      sendSceneExit("hidden");
    }
  }

  function onPageHide() {
    sendSceneExit("pagehide");
  }

  function init(options) {
    options = options || {};
    debug = options.debug !== undefined ? options.debug : isDebugEnabled();
    enterTs = Date.now();
    exitSent = false;

    if (!bound) {
      bound = true;
      document.addEventListener("visibilitychange", onVisibilityChange);
      window.addEventListener("pagehide", onPageHide);
    }

    bindDeclarative(document);

    const prev = readPrevScene();
    const enteredFrom =
      prev && prev.world && prev.scene
        ? { world: prev.world, scene: prev.scene }
        : null;

    track("scene_view", enteredFrom ? { entered_from: enteredFrom } : {});
  }

  const PlaygroundEvents = {
    init: init,
    bindDeclarative: bindDeclarative,
    markExit: sendSceneExit,
  };

  global.PlaygroundEvents = PlaygroundEvents;
})(typeof window !== "undefined" ? window : globalThis);
