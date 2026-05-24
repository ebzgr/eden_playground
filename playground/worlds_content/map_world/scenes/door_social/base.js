(function () {
  const PG = window.Playground;
  if (!PG) return;
  const worldId = (window.__PLAYGROUND__ || {}).worldId || "map_world";
  if (!PG.isPreview()) PG.initTracker().catch(console.error);

  document.getElementById("btn-back-map")?.addEventListener("click", () => {
    PG.goToScene(worldId, "map", PG.ensureWorldSession(worldId));
  });

  const slides = [
    { text: '"This changed my life! 10/10 would recommend!"', author: "— Sarah M., Marketing Expert" },
    { text: '"I learned so much! My brain is now 300% smarter!"', author: "— John D., PhD in Everything" },
    { text: '"Best website ever! My cat even learned marketing!"', author: "— Fluffy, Certified Cat" },
    { text: '"I made $1M in 24 hours after visiting this site!"', author: "— Mike R., Overnight Millionaire" },
    { text: '"My plants started growing better after I learned these techniques!"', author: "— Green Thumb Gary" },
  ];

  let idx = 0;
  const textEl = document.getElementById("testimonial-text");
  const authorEl = document.getElementById("testimonial-author");
  const dotsRoot = document.getElementById("carousel-dots");

  function show(i) {
    idx = i;
    const s = slides[i];
    if (textEl) textEl.textContent = s.text;
    if (authorEl) authorEl.textContent = s.author;
    dotsRoot?.querySelectorAll("button").forEach((btn, j) => {
      btn.setAttribute("aria-selected", j === i ? "true" : "false");
    });
  }

  if (dotsRoot) {
    slides.forEach((_, i) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.setAttribute("aria-label", "Testimonial " + (i + 1));
      btn.addEventListener("click", () => show(i));
      dotsRoot.appendChild(btn);
    });
    show(0);
    setInterval(() => show((idx + 1) % slides.length), 5000);
  }

  const joinEl = document.getElementById("join-message");
  const cities = ["Amsterdam", "Berlin", "London", "Paris", "Tokyo"];
  if (joinEl) {
    setInterval(() => {
      const city = cities[Math.floor(Math.random() * cities.length)];
      joinEl.textContent = "👤 Someone in " + city + " just joined the crowd!";
    }, 4000);
  }
})();
