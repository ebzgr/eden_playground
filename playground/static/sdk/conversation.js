/**
 * ConversationBox SDK
 *
 * Animates text inside any element that carries the class `conversation`,
 * word-by-word, with natural pauses at punctuation.
 *
 * Usage
 * -----
 * 1. Add the class `conversation` to a container element:
 *
 *      <div class="mw-dialogue conversation">
 *        <p>Hello, world. This will animate.</p>
 *        <button>Continue</button>
 *      </div>
 *
 * 2. Include this script after the element exists in the DOM:
 *
 *      <script src="/static/sdk/conversation.js"></script>
 *
 * Options (HTML attributes on the `.conversation` element)
 * -------
 *   data-word-delay   ms between words          default: 75
 *   data-comma-pause  extra ms after , or ;      default: 220
 *   data-period-pause extra ms after . ! ? …     default: 400
 *
 * Behaviour
 * ---------
 * - Text is revealed word by word.
 * - <button> children are hidden until animation completes, then fade in.
 * - Clicking anywhere inside the container skips to the end immediately.
 * - Respects prefers-reduced-motion: skips animation, shows everything at once.
 *
 * Programmatic API
 * ----------------
 *   window.ConversationBox.init(element)   // run on a specific element
 *   window.ConversationBox.initAll()       // run on all .conversation in document
 */
(function (global) {
  "use strict";

  var DEFAULTS = {
    wordDelay:   75,
    commaPause:  220,
    periodPause: 400,
  };

  var PERIOD_CHARS = new Set([".", "!", "?", "…"]);
  var COMMA_CHARS  = new Set([",", ";"]);

  function reduced() {
    return (
      typeof window !== "undefined" &&
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    );
  }

  function extraPause(word, commaPause, periodPause) {
    var last = word[word.length - 1];
    if (PERIOD_CHARS.has(last)) return periodPause;
    if (COMMA_CHARS.has(last))  return commaPause;
    return 0;
  }

  /**
   * Collect all text from a node tree, skipping interactive elements
   * (button, a, input…). Returns an array of {text, node} pairs where
   * `node` is the text node.
   */
  function collectTextNodes(root) {
    var walker = document.createTreeWalker(
      root,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: function (node) {
          var p = node.parentElement;
          while (p && p !== root) {
            var tag = p.tagName.toLowerCase();
            if (tag === "button" || tag === "a" || tag === "input" || tag === "select") {
              return NodeFilter.FILTER_REJECT;
            }
            p = p.parentElement;
          }
          return node.nodeValue.trim()
            ? NodeFilter.FILTER_ACCEPT
            : NodeFilter.FILTER_REJECT;
        },
      }
    );
    var nodes = [];
    var n;
    while ((n = walker.nextNode())) nodes.push(n);
    return nodes;
  }

  function buildWordSpans(text) {
    var words = text.match(/\S+/g) || [];
    return words.map(function (w) {
      var span = document.createElement("span");
      span.className = "cb-word";
      span.textContent = w + " ";
      span.style.cssText = "opacity:0;transition:opacity 0.12s ease;display:inline;";
      return span;
    });
  }

  function revealAll(spans, buttons) {
    spans.forEach(function (s) {
      s.style.opacity = "1";
    });
    showButtons(buttons);
  }

  function showButtons(buttons) {
    buttons.forEach(function (btn) {
      btn.style.transition = "opacity 0.3s ease";
      btn.style.opacity    = "1";
      btn.style.pointerEvents = "";
      btn.removeAttribute("aria-hidden");
      btn.removeAttribute("tabindex");
    });
  }

  function init(el) {
    if (!el || el.dataset.cbInit) return;
    el.dataset.cbInit = "1";

    var wordDelay   = parseInt(el.dataset.wordDelay,   10) || DEFAULTS.wordDelay;
    var commaPause  = parseInt(el.dataset.commaPause,  10) || DEFAULTS.commaPause;
    var periodPause = parseInt(el.dataset.periodPause, 10) || DEFAULTS.periodPause;

    var buttons = Array.from(el.querySelectorAll("button"));

    // Hide buttons immediately
    buttons.forEach(function (btn) {
      btn.style.opacity       = "0";
      btn.style.pointerEvents = "none";
      btn.setAttribute("aria-hidden", "true");
      btn.setAttribute("tabindex", "-1");
    });

    // Skip animation for reduced-motion users
    if (reduced()) {
      revealAll([], buttons);
      return;
    }

    var textNodes = collectTextNodes(el);
    if (!textNodes.length) {
      revealAll([], buttons);
      return;
    }

    // Replace every text node with word spans
    var allSpans = [];
    textNodes.forEach(function (tn) {
      var frag = document.createDocumentFragment();
      var spans = buildWordSpans(tn.nodeValue);
      spans.forEach(function (s) { frag.appendChild(s); });
      allSpans = allSpans.concat(spans);
      tn.parentNode.replaceChild(frag, tn);
    });

    var done = false;
    var currentIdx = 0;
    var timeoutId  = null;

    function finish() {
      if (done) return;
      done = true;
      if (timeoutId) clearTimeout(timeoutId);
      revealAll(allSpans, buttons);
    }

    // Click anywhere inside → skip to end
    el.addEventListener("click", finish, { once: true });

    function revealNext() {
      if (done) return;
      if (currentIdx >= allSpans.length) {
        finish();
        return;
      }
      var span = allSpans[currentIdx];
      span.style.opacity = "1";

      var word  = span.textContent.trim();
      var pause = wordDelay + extraPause(word, commaPause, periodPause);
      currentIdx++;
      timeoutId = setTimeout(revealNext, pause);
    }

    // Start after a short settle delay so layout is stable
    timeoutId = setTimeout(revealNext, 120);
  }

  function initAll() {
    var els = document.querySelectorAll(".conversation");
    els.forEach(init);
  }

  // Auto-init
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAll);
  } else {
    initAll();
  }

  global.ConversationBox = { init: init, initAll: initAll };
})(typeof window !== "undefined" ? window : globalThis);
