/**
 * Demo SDK — YAML-driven scroll-scrubbed scene demos.
 * Requires GSAP + ScrollTrigger (loaded before this script).
 */
(function (global) {
  "use strict";

  var DEFAULT_EASE = "power2.inOut";
  var SLIDE_OFFSET = 40;

  var debugCounters = {};

  function registerDebug(kind) {
    debugCounters[kind] = (debugCounters[kind] || 0) + 1;
  }

  function prefersReducedMotion() {
    return global.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function parseParallax(value) {
    if (value == null) return null;
    if (typeof value === "number") return { y: value, x: 0 };
    if (typeof value === "object") {
      return {
        y: value.y != null ? value.y : 1,
        x: value.x != null ? value.x : 0,
      };
    }
    return null;
  }

  function splitTextContent(el, mode) {
    var text = el.textContent;
    el.textContent = "";
    el.setAttribute("aria-label", text);
    if (mode === "chars") {
      for (var i = 0; i < text.length; i++) {
        var c = text[i];
        var span = document.createElement("span");
        span.className = "demo-split-char";
        span.textContent = c === " " ? "\u00a0" : c;
        el.appendChild(span);
      }
      return el.querySelectorAll(".demo-split-char");
    }
    var parts = text.split(/(\s+)/);
    var nodes = [];
    parts.forEach(function (part) {
      if (!part) return;
      var span = document.createElement("span");
      span.className = part.trim() ? "demo-split-word" : "demo-split-space";
      span.textContent = part;
      el.appendChild(span);
      if (part.trim()) nodes.push(span);
    });
    return nodes;
  }

  function resolveAnchorStyles(anchor) {
    var map = {
      center: { left: "50%", top: "50%" },
      top: { left: "50%", top: "0%" },
      bottom: { left: "50%", top: "100%" },
      left: { left: "0%", top: "50%" },
      right: { left: "100%", top: "50%" },
      "top-left": { left: "0%", top: "0%" },
      "top-right": { left: "100%", top: "0%" },
      "bottom-left": { left: "0%", top: "100%" },
      "bottom-right": { left: "100%", top: "100%" },
    };
    return map[anchor || "center"] || map.center;
  }

  function applyInitialProps(el, initial) {
    if (!initial) return;
    var props = {};
    if (initial.x != null) props.x = initial.x;
    if (initial.y != null) props.y = initial.y;
    if (initial.scale != null) props.scale = initial.scale;
    if (initial.rotation != null) props.rotation = initial.rotation;
    if (initial.opacity != null) props.opacity = initial.opacity;
    if (initial.z != null) el.style.zIndex = String(initial.z);
    if (Object.keys(props).length) {
      global.gsap.set(el, props);
    }
  }

  function directionOffset(dir) {
    switch (dir) {
      case "up":
        return { y: SLIDE_OFFSET };
      case "down":
        return { y: -SLIDE_OFFSET };
      case "left":
        return { x: SLIDE_OFFSET };
      case "right":
        return { x: -SLIDE_OFFSET };
      default:
        return {};
    }
  }

  function DemoRuntime(config, options) {
    this.config = config;
    this.options = options || {};
    this.root =
      document.getElementById("demo-root") ||
      document.querySelector("main") ||
      document.body;
    this.layers = {};
    this.verses = {};
    this.parallax = {};
    this.timeline = null;
    this.scrollTrigger = null;
    this.progressEl = null;
    this.reduced = prefersReducedMotion();
  }

  DemoRuntime.prototype.buildDom = function () {
    var cfg = this.config;
    var root = document.createElement("div");
    root.className = "demo-root";
    this.root.innerHTML = "";
    this.root.appendChild(root);

    if (cfg.progress_bar !== false) {
      this.progressEl = document.createElement("div");
      this.progressEl.className = "demo-progress";
      this.progressEl.setAttribute("role", "progressbar");
      this.progressEl.setAttribute("aria-valuemin", "0");
      this.progressEl.setAttribute("aria-valuemax", "100");
      document.body.appendChild(this.progressEl);
    }

    var stage = document.createElement("div");
    stage.className = "demo-stage";
    if (cfg.background && cfg.background.value) {
      var bg = document.createElement("div");
      bg.className = "demo-stage-bg";
      bg.style.background = cfg.background.value;
      stage.appendChild(bg);
    }

    var layersHost = document.createElement("div");
    layersHost.className = "demo-layers";
    stage.appendChild(layersHost);

    var versesHost = document.createElement("div");
    versesHost.className = "demo-verses";
    stage.appendChild(versesHost);

    (cfg.layers || []).forEach(function (layer) {
      var wrap = document.createElement("div");
      wrap.className = "demo-layer-wrap";
      wrap.dataset.layerId = layer.id;
      var anchor = resolveAnchorStyles(layer.anchor);
      wrap.style.left = anchor.left;
      wrap.style.top = anchor.top;
      if (layer.z != null) wrap.style.zIndex = String(layer.z);

      var inner = document.createElement("div");
      inner.className = "demo-layer-inner";
      if (layer.class) inner.classList.add(layer.class);
      if (layer.style) inner.setAttribute("style", layer.style);

      var type = layer.type || "div";
      if (type === "image") {
        var img = document.createElement("img");
        img.src = layer.src || "";
        img.alt = layer.alt || "";
        inner.appendChild(img);
      } else if (type === "text") {
        inner.classList.add("demo-text-layer");
        inner.textContent = layer.text || "";
      } else if (type === "svg") {
        inner.innerHTML = layer.html || "";
      } else {
        if (layer.html) inner.innerHTML = layer.html;
      }

      wrap.appendChild(inner);
      layersHost.appendChild(wrap);

      var parallax = parseParallax(layer.parallax);
      if (parallax) {
        this.parallax[layer.id] = { wrap: wrap, factor: parallax };
      }

      applyInitialProps(inner, layer.initial);
      this.layers[layer.id] = { wrap: wrap, inner: inner, layer: layer };
    }, this);

    (cfg.verses || []).forEach(function (verse) {
      var el = document.createElement("p");
      el.className = "demo-verse demo-verse--" + (verse.style || "poem");
      el.dataset.verseId = verse.id;
      el.textContent = verse.text || "";

      // Centering uses xPercent/yPercent so later `y` tweens (e.g. "30vh")
      // stack on top of the centering offset instead of overwriting it.
      var initial = { autoAlpha: 0 };
      if (verse.position === "top") {
        el.style.left = "50%";
        el.style.top = "12%";
        el.style.bottom = "auto";
        initial.xPercent = -50;
      } else if (verse.position === "bottom") {
        el.style.left = "50%";
        el.style.bottom = "12%";
        el.style.top = "auto";
        initial.xPercent = -50;
      } else if (verse.position && typeof verse.position === "object") {
        if (verse.position.x != null) el.style.left = verse.position.x;
        if (verse.position.y != null) el.style.top = verse.position.y;
      } else {
        el.style.left = "50%";
        el.style.top = "50%";
        initial.xPercent = -50;
        initial.yPercent = -50;
      }
      global.gsap.set(el, initial);

      versesHost.appendChild(el);
      this.verses[verse.id] = { el: el, verse: verse, splitNodes: null };
    }, this);

    root.appendChild(stage);

    var spacer = document.createElement("div");
    spacer.className = "demo-scroll-spacer";
    spacer.style.height = (cfg.length || 2000) + "px";
    root.appendChild(spacer);

    this.stage = stage;
    this.spacer = spacer;
  };

  DemoRuntime.prototype.resolveTarget = function (target) {
    if (!target) return null;
    if (this.layers[target]) return { type: "layer", inner: this.layers[target].inner, wrap: this.layers[target].wrap };
    if (this.verses[target]) return { type: "verse", el: this.verses[target].el, meta: this.verses[target] };
    if (target.charAt(0) === "#" || target.charAt(0) === ".") {
      var el = this.root.querySelector(target) || document.querySelector(target);
      return el ? { type: "selector", el: el } : null;
    }
    return null;
  };

  DemoRuntime.prototype.addCue = function (tl, cue, length, defaultEase) {
    var kind = cue.kind;
    registerDebug(kind);
    var at = (cue.at || 0) * length;
    var to = (cue.to != null ? cue.to : cue.at || 0) * length;
    var ease = cue.ease || defaultEase || DEFAULT_EASE;
    var target = this.resolveTarget(cue.target);
    if (!target && kind !== "pause") return;

    var self = this;

    if (kind === "pause") {
      tl.to({}, { duration: Math.max(0, to - at) }, at);
      return;
    }

    if (kind === "set") {
      var setProps = cue.props || {};
      var setEl =
        target.type === "verse" || target.type === "selector"
          ? target.el
          : target.inner;
      if (setProps.z != null) {
        var setWrap = target.wrap || setEl;
        setWrap.style.zIndex = String(setProps.z);
      }
      var gsapProps = {};
      [
        "x",
        "y",
        "scale",
        "rotation",
        "opacity",
        "autoAlpha",
        "xPercent",
        "yPercent",
      ].forEach(function (k) {
        if (setProps[k] != null) gsapProps[k] = setProps[k];
      });
      if (Object.keys(gsapProps).length) tl.set(setEl, gsapProps, at);
      return;
    }

    var el =
      target.type === "verse" || target.type === "selector"
        ? target.el
        : target.inner;

    if (kind === "show") {
      var fromDir = cue.from || "none";
      var offset = directionOffset(fromDir);
      var hasOffset = Object.keys(offset).length > 0;
      // Only animate x/y when a direction was requested; otherwise leave
      // x/y alone so a preceding `set` (e.g. y: "30vh") is preserved.
      var resetXY = hasOffset ? { x: 0, y: 0 } : {};

      if (target.type === "verse" && cue.text_reveal) {
        var nodes = splitTextContent(el, cue.text_reveal === "chars" ? "chars" : "words");
        target.meta.splitNodes = nodes;
        tl.set(el, { autoAlpha: 1 }, at);
        tl.fromTo(
          nodes,
          Object.assign({ autoAlpha: 0 }, offset),
          Object.assign(
            {
              autoAlpha: 1,
              duration: to - at,
              ease: ease,
              stagger: cue.stagger != null ? cue.stagger : 0.04,
            },
            resetXY
          ),
          at
        );
      } else {
        tl.fromTo(
          el,
          Object.assign({ autoAlpha: 0 }, offset),
          Object.assign(
            { autoAlpha: 1, duration: to - at, ease: ease },
            resetXY
          ),
          at
        );
      }
      return;
    }

    if (kind === "hide") {
      var exitDir = cue.exit || "none";
      var hideOffset = directionOffset(exitDir);
      if (target.meta && target.meta.splitNodes) {
        tl.to(
          target.meta.splitNodes,
          { autoAlpha: 0, duration: (to - at) * 0.6, ease: ease, stagger: 0.02 },
          at
        );
      }
      // autoAlpha animates opacity AND toggles visibility, and reverses
      // automatically when the scrub plays backward across this range —
      // no onComplete visibility flip needed.
      tl.to(
        el,
        Object.assign(
          { autoAlpha: 0, duration: to - at, ease: ease },
          hideOffset
        ),
        at
      );
      return;
    }

    var props = cue.props || {};
    if (kind === "move") {
      tl.to(el, { x: props.x, y: props.y, duration: to - at, ease: ease }, at);
    } else if (kind === "zoom") {
      tl.to(el, { scale: props.scale, duration: to - at, ease: ease }, at);
    } else if (kind === "fade") {
      tl.to(el, { opacity: props.opacity, duration: to - at, ease: ease }, at);
    }
  };

  DemoRuntime.prototype.buildTimeline = function () {
    var cfg = this.config;
    var length = cfg.length || 2000;
    var self = this;
    var defaultEase = cfg.default_ease || DEFAULT_EASE;

    // Demo scenes pin scroll to <html> via demo.css (so ScrollTrigger and
    // wheel/trackpad agree). Tell ScrollTrigger about it explicitly instead
    // of relying on the default window scroller matching by accident.
    var scroller = document.scrollingElement || document.documentElement;

    this.timeline = global.gsap.timeline({
      scrollTrigger: {
        trigger: this.stage,
        scroller: scroller,
        start: "top top",
        end: "+=" + length,
        pin: cfg.pin !== false,
        scrub: cfg.scrub != null ? cfg.scrub : 1.5,
        invalidateOnRefresh: true,
        onUpdate: function (st) {
          if (self.progressEl) {
            var pct = Math.round(st.progress * 100);
            self.progressEl.style.width = pct + "%";
            self.progressEl.setAttribute("aria-valuenow", String(pct));
          }
          self.applyParallax(st.progress);
          if (st.progress >= 0.995 && self.options.onComplete) {
            self.options.onComplete();
          }
        },
      },
    });
    this.scrollTrigger = this.timeline.scrollTrigger;

    (cfg.timeline || []).forEach(function (cue) {
      self.addCue(self.timeline, cue, length, defaultEase);
    });
  };

  DemoRuntime.prototype.applyParallax = function (progress) {
    var scrollPx = progress * (this.config.length || 2000);
    Object.keys(this.parallax).forEach(function (id) {
      var entry = this.parallax[id];
      var y = scrollPx * (entry.factor.y - 1) * 0.1;
      var x = scrollPx * entry.factor.x * 0.1;
      global.gsap.set(entry.wrap, { x: x, y: y });
    }, this);
  };

  DemoRuntime.prototype.applyReducedMotion = function () {
    var cfg = this.config;
    (cfg.timeline || []).forEach(function (cue) {
      if (cue.kind === "pause") return;
      var target = this.resolveTarget(cue.target);
      if (!target) return;
      var el =
        target.type === "verse" || target.type === "selector"
          ? target.el
          : target.inner;
      if (cue.kind === "hide") {
        global.gsap.set(el, { autoAlpha: 0 });
      } else if (cue.kind === "show" || ["move", "zoom", "fade", "set"].indexOf(cue.kind) >= 0) {
        global.gsap.set(el, { autoAlpha: 1 });
        var props = cue.props || {};
        if (cue.kind === "move") global.gsap.set(el, { x: props.x, y: props.y });
        if (cue.kind === "zoom") global.gsap.set(el, { scale: props.scale });
        if (cue.kind === "fade") global.gsap.set(el, { opacity: props.opacity });
        if (cue.kind === "set" && cue.props) {
          applyInitialProps(el, cue.props);
        }
      }
    }, this);
    if (this.options.onComplete) this.options.onComplete();
  };

  DemoRuntime.prototype.refresh = function () {
    if (global.ScrollTrigger) global.ScrollTrigger.refresh();
  };

  DemoRuntime.prototype.mount = function () {
    document.documentElement.classList.add("pg-scene--demo");
    document.body.classList.add("pg-scene--demo", "pg-scene--scroll");

    this.buildDom();

    if (this.reduced) {
      this.applyReducedMotion();
      return;
    }

    if (!global.gsap || !global.ScrollTrigger) {
      console.error("Demo SDK requires GSAP and ScrollTrigger");
      return;
    }
    global.gsap.registerPlugin(global.ScrollTrigger);

    // Smoother cross-browser scroll feel — normalize wheel/touch deltas,
    // and avoid jitter when the mobile address bar resizes the viewport.
    // Both are idempotent and safe to call once per page load.
    if (!global.__demoScrollNormalized) {
      try {
        global.ScrollTrigger.normalizeScroll(true);
        global.ScrollTrigger.config({ ignoreMobileResize: true });
      } catch (err) {
        // Older ScrollTrigger builds may not expose these — ignore.
      }
      global.__demoScrollNormalized = true;
    }

    var self = this;
    var imgs = this.root.querySelectorAll("img");
    var pending = imgs.length;
    var done = function () {
      self.buildTimeline();
      self.refresh();
    };
    if (!pending) {
      done();
      return;
    }
    imgs.forEach(function (img) {
      if (img.complete) {
        pending -= 1;
        if (pending <= 0) done();
      } else {
        img.addEventListener("load", function () {
          pending -= 1;
          if (pending <= 0) done();
        });
        img.addEventListener("error", function () {
          pending -= 1;
          if (pending <= 0) done();
        });
      }
    });

    global.addEventListener("resize", function () {
      self.refresh();
    });
  };

  DemoRuntime.prototype.destroy = function () {
    if (this.timeline) this.timeline.kill();
    if (this.scrollTrigger) this.scrollTrigger.kill();
    if (this.progressEl && this.progressEl.parentNode) {
      this.progressEl.parentNode.removeChild(this.progressEl);
    }
  };

  function resolveDeviceConfig(config) {
    var mobileBlock = config.mobile || {};
    var maxWidth = mobileBlock.max_width != null ? mobileBlock.max_width : 768;
    var isMobile = global.matchMedia("(max-width: " + maxWidth + "px)").matches;
    var resolved = JSON.parse(JSON.stringify(config));
    if (isMobile && mobileBlock) {
      ["length", "scrub", "pin", "default_ease", "progress_bar"].forEach(function (key) {
        if (mobileBlock[key] !== undefined) resolved[key] = mobileBlock[key];
      });
      if (mobileBlock.background) resolved.background = mobileBlock.background;
      if (mobileBlock.layers) {
        var byId = {};
        (resolved.layers || []).forEach(function (layer) {
          byId[layer.id] = layer;
        });
        Object.keys(mobileBlock.layers).forEach(function (id) {
          if (!byId[id]) return;
          var patch = mobileBlock.layers[id];
          Object.keys(patch).forEach(function (k) {
            if (k === "initial" && typeof patch.initial === "object") {
              byId[id].initial = Object.assign({}, byId[id].initial || {}, patch.initial);
            } else {
              byId[id][k] = patch[k];
            }
          });
        });
        resolved.layers = Object.keys(byId).map(function (k) {
          return byId[k];
        });
      }
      if (mobileBlock.timeline) resolved.timeline = mobileBlock.timeline;
    }
    var device = isMobile ? "mobile" : "desktop";
    resolved.timeline = (resolved.timeline || []).filter(function (cue) {
      var d = cue.device || "all";
      return d === "all" || d === device;
    });
    resolved._resolvedDevice = device;
    return resolved;
  }

  function run(config, options) {
    if (!config) return null;
    var resolved = resolveDeviceConfig(config);
    var runtime = new DemoRuntime(resolved, options);
    runtime.mount();

    var maxWidth = (config.mobile && config.mobile.max_width) || 768;
    var mq = global.matchMedia("(max-width: " + maxWidth + "px)");
    var reinit = function () {
      runtime.destroy();
      runtime = new DemoRuntime(resolveDeviceConfig(config), options);
      runtime.mount();
    };
    if (mq.addEventListener) {
      mq.addEventListener("change", reinit);
    }

    return runtime;
  }

  global.Demo = {
    run: run,
    resolveDeviceConfig: resolveDeviceConfig,
    __debug: debugCounters,
    _DemoRuntime: DemoRuntime,
  };
})(typeof window !== "undefined" ? window : globalThis);
