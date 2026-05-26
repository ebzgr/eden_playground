(function () {
  const PG = window.Playground;
  const gsap = window.gsap;

  if (!PG || !gsap) return;

  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const ORBS = [
    { id: "clarity",      name: "Orb of Clarity",      color: "#7dd3fc" },
    { id: "presence",     name: "Orb of Presence",      color: "#c084fc" },
    { id: "wisdom",       name: "Orb of Wisdom",        color: "#38bdf8" },
    { id: "resistance",   name: "Orb of Resistance",    color: "#86efac" },
    { id: "authenticity", name: "Orb of Authenticity",  color: "#fbbf24" },
  ];

  const CARD_COUNT = ORBS.length;

  const POS = {
    "-2": { xPct: -140, scale: 0.5, opacity: 0, zIndex: 0 },
    "-1": { xPct: -85,  scale: 0.72, opacity: 0.5, zIndex: 5 },
     "0": { xPct: 0,    scale: 1,    opacity: 1,   zIndex: 10 },
     "1": { xPct: 85,   scale: 0.72, opacity: 0.5, zIndex: 5 },
     "2": { xPct: 140,  scale: 0.5,  opacity: 0,   zIndex: 0 },
  };

  const cards = Array.from(document.querySelectorAll(".mw-card"));
  const dots  = Array.from(document.querySelectorAll(".mw-dot"));
  const prevBtn = document.querySelector(".mw-nav--prev");
  const nextBtn = document.querySelector(".mw-nav--next");
  const track  = document.querySelector(".mw-track");
  const gaiaBtn = document.querySelector(".mw-gaia-btn");

  let activeIndex = 0;
  const wrap = gsap.utils.wrap(0, CARD_COUNT);

  function applyGrantedOrbIds(orbIds) {
    const granted = new Set(
      (Array.isArray(orbIds) ? orbIds : []).map((id) => String(id))
    );
    cards.forEach((card) => {
      const orbId = card.getAttribute("data-orb-id");
      card.classList.toggle("is-granted", granted.has(orbId));
    });
  }

  function goTo(newIndex, instant) {
    const prevOrb = ORBS[activeIndex];
    activeIndex = wrap(newIndex);
    const nextOrb = ORBS[activeIndex];

    cards.forEach((card, cardIndex) => {
      const rawDist = cardIndex - activeIndex;
      let dist = rawDist;
      if (dist > CARD_COUNT / 2)  dist -= CARD_COUNT;
      if (dist < -CARD_COUNT / 2) dist += CARD_COUNT;
      const distKey = String(Math.max(-2, Math.min(2, dist)));
      const pos = POS[distKey];

      const animate = instant || reduced ? gsap.set : gsap.to;
      const tweenOpts = instant || reduced
        ? {}
        : { duration: 0.5, ease: "power2.inOut" };

      animate(card, {
        x: pos.xPct + "%",
        scale: pos.scale,
        opacity: pos.opacity,
        zIndex: pos.zIndex,
        ...tweenOpts,
      });

      card.classList.toggle("is-active", cardIndex === activeIndex);
      card.setAttribute("aria-hidden", String(Math.abs(dist) >= 2));
    });

    dots.forEach((dot, i) => dot.classList.toggle("is-active", i === activeIndex));

    if (!instant) {
      PG.track("map_orb_viewed", {
        orb_id:      nextOrb.id,
        orb_name:    nextOrb.name,
        from_orb_id: prevOrb.id,
      });
    }
  }

  function initSlider() {
    goTo(0, true);
    PG.track("map_orb_viewed", {
      orb_id:      ORBS[0].id,
      orb_name:    ORBS[0].name,
      from_orb_id: null,
    });

    prevBtn.addEventListener("click", () => goTo(activeIndex - 1, false));
    nextBtn.addEventListener("click", () => goTo(activeIndex + 1, false));

    dots.forEach((dot) => {
      dot.addEventListener("click", () => {
        const idx = parseInt(dot.getAttribute("data-dot-index"), 10);
        if (idx !== activeIndex) goTo(idx, false);
      });
    });

    cards.forEach((card) => {
      card.addEventListener("click", (e) => {
        if (e.target.closest(".mw-enter-btn")) return;
        const cardIndex = parseInt(card.getAttribute("data-orb-index"), 10);
        if (cardIndex === activeIndex) return;
        let dist = cardIndex - activeIndex;
        if (dist > CARD_COUNT / 2)  dist -= CARD_COUNT;
        if (dist < -CARD_COUNT / 2) dist += CARD_COUNT;
        if (Math.abs(dist) === 1) {
          goTo(activeIndex + Math.sign(dist), false);
        }
      });
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "ArrowLeft")  { e.preventDefault(); goTo(activeIndex - 1, false); }
      if (e.key === "ArrowRight") { e.preventDefault(); goTo(activeIndex + 1, false); }
    });

    let dragStartX = null;
    let isDragging = false;
    const DRAG_THRESHOLD = 40;

    track.addEventListener("pointerdown", (e) => {
      dragStartX = e.clientX;
      isDragging = false;
      track.setPointerCapture(e.pointerId);
    });

    track.addEventListener("pointermove", (e) => {
      if (dragStartX === null) return;
      if (Math.abs(e.clientX - dragStartX) > 5) isDragging = true;
    });

    track.addEventListener("pointerup", (e) => {
      if (dragStartX === null) return;
      const delta = e.clientX - dragStartX;
      dragStartX = null;
      if (!isDragging || Math.abs(delta) < DRAG_THRESHOLD) return;
      goTo(delta > 0 ? activeIndex - 1 : activeIndex + 1, false);
    });

    track.addEventListener("pointercancel", () => {
      dragStartX = null;
      isDragging = false;
    });
  }

  if (gaiaBtn) {
    gaiaBtn.addEventListener("click", () => {
      const worldId = (window.__PLAYGROUND__ || {}).worldId || "map_world";
      PG.postIdentity()
        .then(() => {
          const sessionId = PG.ensureWorldSession(worldId);
          PG.goToScene(worldId, "welcome", sessionId);
        })
        .catch(console.error);
    });
  }

  async function bootstrap() {
    if (!PG.isPreview()) {
      PG.ensureReturnCodeFromUrl();
      try {
        await PG.postIdentity();
        await PG.initTracker();
        const orbs = await PG.getState("journey.orbs");
        applyGrantedOrbIds(orbs);
      } catch (err) {
        console.error(err);
      }
    }
    initSlider();
  }

  bootstrap();
})();
