/* Jéjé-TCG — ouverture du sachet avant la séquence de révélation.
   Déclenché au clic (clavier + tactile), sans dépendance.
   Sans JS : l'intro est masquée (js-only) et le deck reste visible.
   Mouvement réduit : bascule instantanée, sans animation. */
(function () {
  function init(root) {
    if (!root || root.dataset.packReady === "true") return;
    var btn = root.querySelector("[data-pack-open]");
    var scene = root.querySelector("[data-pack-scene]");
    if (!btn) return;
    root.dataset.packReady = "true";

    var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function done() {
      root.setAttribute("data-opened", "true");
      var live = root.querySelector("[data-reveal-live]");
      if (live) {
        live.textContent =
          "Pack ouvert. Carte 1 sur 5 : touchez la carte ou le bouton pour révéler.";
      }
      var next = root.querySelector("[data-reveal-next]");
      if (next) next.focus({ preventScroll: true });
    }

    btn.addEventListener("click", function () {
      btn.disabled = true;
      if (reduceMotion || !scene) {
        done();
        return;
      }
      scene.classList.add("is-tearing");
      window.setTimeout(done, 1500);
    });
  }

  function initAll(root) {
    (root || document).querySelectorAll("[data-reveal-root]").forEach(init);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      initAll(document);
    });
  } else {
    initAll(document);
  }
  document.addEventListener("htmx:afterSwap", function (event) {
    initAll(event.target);
  });
})();
