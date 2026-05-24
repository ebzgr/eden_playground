(function () {
  const PG = window.Playground;
  const link = document.getElementById("link-continue");
  const lines = Array.from(document.querySelectorAll(".lab-line"));
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const SCRAMBLE_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%&*";

  if (link && PG && !PG.isPreview()) {
    PG.initTracker().catch(console.error);
  }

  function navigateToConsent(ev) {
    if (ev) ev.preventDefault();
    if (!link) return;
    if (!PG) {
      window.location.href = "/worlds/intro_world/scenes/consent/view";
      return;
    }
    link.classList.remove("is-ready");
    link.style.pointerEvents = "none";
    PG.postIdentity()
      .then(() => {
        const sessionId = PG.ensureWorldSession("intro_world");
        PG.goToScene("intro_world", "consent", sessionId);
      })
      .catch((err) => {
        console.error(err);
        link.classList.add("is-ready");
        link.style.pointerEvents = "";
        alert("Something went wrong. Please try again.");
      });
  }

  if (link) link.addEventListener("click", navigateToConsent);

  function revealLink() {
    if (!link) return;
    link.removeAttribute("aria-hidden");
    if (window.gsap) {
      window.gsap.to(link, {
        autoAlpha: 1,
        y: 0,
        duration: 0.8,
        ease: "power2.out",
        onComplete: function () {
          link.classList.add("is-ready");
        },
      });
    } else {
      link.style.visibility = "visible";
      link.style.opacity = "1";
      link.classList.add("is-ready");
    }
  }

  // Fallback path: reduced-motion or GSAP missing — just show everything.
  if (reduced || !window.gsap) {
    lines.forEach(function (el) {
      el.style.visibility = "visible";
      el.style.opacity = "1";
    });
    revealLink();
    return;
  }

  /**
   * Custom scramble built on a GSAP tween. We tween a `progress` value
   * from 0→1 across `duration`; on each frame, the first `progress * len`
   * characters are locked to the target string and the rest cycle through
   * random characters (re-randomised every `cycleEvery` frames so the
   * decrypting feel reads at ~15 Hz instead of a blurry 60 Hz).
   *
   * Returns the tween, added to `tl` at `opts.position`.
   */
  function addScramble(tl, el, opts) {
    opts = opts || {};
    const target = el.dataset.text || el.textContent || "";
    const chars = opts.chars || SCRAMBLE_CHARS;
    const duration = opts.duration != null ? opts.duration : 1.4;
    const cycleEvery = opts.cycleEvery || 4;
    const ease = opts.ease || "power2.inOut";
    const len = target.length;
    const cached = new Array(len);
    for (let i = 0; i < len; i++) {
      cached[i] = chars.charAt(Math.floor(Math.random() * chars.length));
    }
    const state = { progress: 0, frame: 0 };

    function render() {
      const revealed = Math.floor(state.progress * len);
      let out = "";
      for (let i = 0; i < len; i++) {
        const t = target.charAt(i);
        if (t === " " || t === "\n" || t === "\t") {
          out += t;
        } else if (i < revealed) {
          out += t;
        } else {
          out += cached[i];
        }
      }
      el.textContent = out;
    }

    return tl.to(
      state,
      {
        progress: 1,
        duration: duration,
        ease: ease,
        onStart: function () {
          window.gsap.set(el, { autoAlpha: 1 });
          el.classList.add("is-scrambling");
          render();
        },
        onUpdate: function () {
          state.frame += 1;
          if (state.frame % cycleEvery === 0) {
            const revealed = Math.floor(state.progress * len);
            for (let i = revealed; i < len; i++) {
              const t = target.charAt(i);
              if (t === " " || t === "\n" || t === "\t") continue;
              cached[i] = chars.charAt(Math.floor(Math.random() * chars.length));
            }
          }
          render();
        },
        onComplete: function () {
          el.textContent = target;
          el.classList.remove("is-scrambling");
        },
      },
      opts.position
    );
  }

  function boot() {
    if (!window.gsap || lines.length < 3) return;
    window.gsap.set(link, { autoAlpha: 0, y: 8 });
    const tl = window.gsap.timeline({
      delay: 0.15,
      onComplete: revealLink,
    });
    addScramble(tl, lines[0], { duration: 2.0 });
    addScramble(tl, lines[1], { duration: 0.7, position: "+=0.25" });
    addScramble(tl, lines[2], { duration: 2.4, position: "+=0.35" });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
