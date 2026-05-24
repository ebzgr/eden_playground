(function () {
  const PG = window.Playground;
  const link = document.getElementById("link-meet-gaia");

  function bootDemo() {
    if (!window.Demo || !window.__DEMO__) return;
    window.Demo.run(window.__DEMO__, {
      onComplete: function () {
        if (!link) return;
        link.removeAttribute("aria-hidden");
        link.classList.add("ready");
      },
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootDemo);
  } else {
    bootDemo();
  }

  if (!link || !PG) return;

  if (!PG.isPreview()) {
    PG.initTracker().catch(console.error);
  }

  link.addEventListener("click", function () {
    link.disabled = true;
    const mapSession = PG.ensureWorldSession("map_world");
    PG.goToScene("map_world", "welcome", mapSession);
  });
})();
