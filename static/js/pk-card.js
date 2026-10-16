/* WikiCards — inclinaison + reflet des cartes TCG (inspiration holo, code original). */
(function () {
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var finePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  if (reduceMotion || !finePointer) return;

  function bind(card) {
    var inner = card.querySelector("[data-pk-tilt]");
    if (!inner) return;
    var raf = 0;

    function setFromEvent(event) {
      var rect = card.getBoundingClientRect();
      var px = (event.clientX - rect.left) / rect.width;
      var py = (event.clientY - rect.top) / rect.height;
      px = Math.min(1, Math.max(0, px));
      py = Math.min(1, Math.max(0, py));
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(function () {
        card.style.setProperty("--mx", (px * 100).toFixed(1) + "%");
        card.style.setProperty("--my", (py * 100).toFixed(1) + "%");
        card.style.setProperty("--ry", ((px - 0.5) * 16).toFixed(2) + "deg");
        card.style.setProperty("--rx", ((0.5 - py) * 14).toFixed(2) + "deg");
        card.classList.add("is-tilting");
      });
    }

    function reset() {
      cancelAnimationFrame(raf);
      card.classList.remove("is-tilting");
      card.style.setProperty("--rx", "0deg");
      card.style.setProperty("--ry", "0deg");
    }

    card.addEventListener("pointermove", setFromEvent);
    card.addEventListener("pointerleave", reset);
    card.addEventListener("pointercancel", reset);
  }

  function init(root) {
    (root || document).querySelectorAll(".pk-card--holo").forEach(bind);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { init(document); });
  } else {
    init(document);
  }
  document.addEventListener("htmx:afterSwap", function (event) { init(event.target); });
})();
