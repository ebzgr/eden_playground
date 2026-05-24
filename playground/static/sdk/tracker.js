/**
 * Eden Playground event tracker SDK (v0).
 * Respects previewMode — no events are queued or sent in admin preview.
 */
(function (global) {
  const QUEUE = [];
  let cfg = {};
  let consentGranted = false;
  let flushTimer = null;

  function isPreview() {
    return !!(cfg.previewMode || cfg.preview);
  }

  function headers() {
    const h = { "Content-Type": "application/json" };
    if (isPreview()) {
      h["X-Playground-Preview"] = "1";
    }
    const code = localStorage.getItem("return_code");
    if (code) h["X-Return-Code"] = code;
    return h;
  }

  function experimentPayload(extra) {
    const base = extra && typeof extra === "object" ? { ...extra } : {};
    if (cfg.experiment && cfg.experiment.id) {
      base.experiment_id = cfg.experiment.id;
      if (cfg.experiment.armId) base.arm_id = cfg.experiment.armId;
      if (cfg.experiment.assignmentScope) {
        base.assignment_scope = cfg.experiment.assignmentScope;
      }
    }
    if (cfg.versionId) base.scene_version_id = cfg.versionId;
    return base;
  }

  async function ensureIdentity() {
    if (isPreview()) {
      return { consent_state: "preview", preview: true };
    }
    let code = localStorage.getItem("return_code");
    const res = await fetch((cfg.apiBase || "") + "/identity", {
      method: "POST",
      credentials: "include",
      headers: code ? { "X-Return-Code": code } : {},
    });
    const data = await res.json();
    localStorage.setItem("return_code", data.return_code);
    consentGranted = data.consent_state === "granted";
    return data;
  }

  function buildEventItem(eventType, payload) {
    return {
      event_type: eventType,
      payload: experimentPayload(payload),
      world_id: cfg.worldId || null,
      scene_id: cfg.sceneId || null,
      scene_version_id: cfg.versionId || null,
      experiment_arms: cfg.experimentArms || null,
      ts_client: new Date().toISOString(),
    };
  }

  function postEventsBody(events) {
    return JSON.stringify({
      session_id: cfg.sessionId,
      events: events,
    });
  }

  async function flush() {
    if (isPreview() || !consentGranted || QUEUE.length === 0 || !cfg.sessionId) {
      return;
    }
    const batch = QUEUE.splice(0, QUEUE.length);
    await fetch((cfg.apiBase || "") + "/events", {
      method: "POST",
      credentials: "include",
      headers: headers(),
      body: postEventsBody(batch),
    });
  }

  function sendImmediate(eventType, payload) {
    if (isPreview() || !consentGranted || !cfg.sessionId) {
      return;
    }
    const item = buildEventItem(eventType, payload);
    const body = postEventsBody([item]);
    const url = (cfg.apiBase || "") + "/events";
    const hdrs = headers();

    if (typeof navigator !== "undefined" && navigator.sendBeacon) {
      try {
        const blob = new Blob([body], { type: "application/json" });
        if (navigator.sendBeacon(url, blob)) {
          return;
        }
      } catch (_) {
        /* fall through */
      }
    }

    try {
      fetch(url, {
        method: "POST",
        credentials: "include",
        headers: hdrs,
        body: body,
        keepalive: true,
      });
    } catch (_) {
      /* best effort on unload */
    }
  }

  function scheduleFlush() {
    if (isPreview()) return;
    if (flushTimer) clearTimeout(flushTimer);
    flushTimer = setTimeout(flush, 2000);
  }

  const Tracker = {
    async init(options) {
      cfg = options || {};
      if (isPreview()) {
        consentGranted = false;
        return { consent_state: "preview", preview: true };
      }
      await ensureIdentity();
      if (cfg.autoConsent) {
        await fetch((cfg.apiBase || "") + "/consent", {
          method: "POST",
          credentials: "include",
          headers: headers(),
          body: JSON.stringify({ state: "granted" }),
        });
        consentGranted = true;
      }
    },

    event(eventType, payload) {
      if (isPreview()) return;
      QUEUE.push(buildEventItem(eventType, payload));
      scheduleFlush();
    },

    sendImmediate: sendImmediate,

    async flushNow() {
      if (isPreview()) return;
      await flush();
    },

    setConsentGranted(granted) {
      if (isPreview()) return;
      consentGranted = !!granted;
      if (consentGranted) scheduleFlush();
    },

    isConsentGranted() {
      return !isPreview() && consentGranted;
    },

    isPreview() {
      return isPreview();
    },
  };

  global.Tracker = Tracker;
})(typeof window !== "undefined" ? window : globalThis);
