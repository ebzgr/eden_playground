(function () {
  const PG = window.Playground;
  const btn = document.getElementById("btn-open-map");
  if (!PG || !btn) return;

  const worldId = (window.__PLAYGROUND__ || {}).worldId || "map_world";

  if (!PG.isPreview()) {
    PG.initTracker().catch(console.error);
  }

  function setupTyping(el, phrases, speeds) {
    if (!el) return;
    let pi = 0;
    let ci = 0;
    let del = false;
    function tick() {
      const word = phrases[pi];
      if (del) {
        el.textContent = word.substring(0, ci - 1);
        ci--;
      } else {
        el.textContent = word.substring(0, ci + 1);
        ci++;
      }
      let wait = del ? speeds.delete : speeds.type;
      if (!del && ci === word.length) {
        wait = speeds.pauseEnd;
        del = true;
      } else if (del && ci === 0) {
        del = false;
        pi = (pi + 1) % phrases.length;
        wait = speeds.pauseStart;
      }
      setTimeout(tick, wait);
    }
    tick();
  }

  setupTyping(
    document.getElementById("typing-a"),
    ["mislead", "persuade", "teach", "warn", "lure", "inspire"],
    { type: 80, delete: 30, pauseEnd: 1200, pauseStart: 300 }
  );
  setupTyping(
    document.getElementById("typing-b"),
    ["notice", "realize", "learn", "change", "understand", "grow"],
    { type: 120, delete: 50, pauseEnd: 2000, pauseStart: 500 }
  );

  btn.addEventListener("click", () => {
    const sessionId = PG.ensureWorldSession(worldId);
    PG.goToScene(worldId, "map", sessionId);
  });
})();
