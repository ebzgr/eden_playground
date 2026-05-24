(function () {
  const PG = window.Playground;
  const checkbox = document.getElementById("consent-checkbox");
  const btn = document.getElementById("btn-start");
  if (!PG || !btn) return;

  const cfg = window.__PLAYGROUND__ || {};
  const sessionId =
    cfg.sessionId || PG.ensureWorldSession("intro_world");

  if (!PG.isPreview()) {
    PG.initTracker().catch(console.error);
  }

  btn.addEventListener("click", async () => {
    btn.disabled = true;
    try {
      const consented = checkbox && checkbox.checked;

      if (consented) {
        await PG.postConsent("granted");
        if (!PG.isPreview()) {
          await PG.initTracker();
          if (window.Tracker) {
            Tracker.setConsentGranted(true);
            PG.track("consent_granted", { via: "intro_consent_scene", surface: "intro_consent" });
            await Tracker.flushNow();
          }
        }
      } else {
        await PG.postConsent("denied");
        if (window.Tracker) {
          Tracker.setConsentGranted(false);
        }
      }

      const introSession = PG.ensureWorldSession("intro_world");
      PG.goToScene("intro_world", "demo", introSession);
    } catch (err) {
      console.error(err);
      btn.disabled = false;
      alert("Something went wrong. Please try again.");
    }
  });
})();
