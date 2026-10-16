/* Jéjé-TCG — révélation séquentielle d'un booster (5 cartes, une à une). */
(function () {
  function initDeck(deck) {
    if (deck.dataset.revealReady === "true") return;
    deck.dataset.revealReady = "true";

    var slots = Array.prototype.slice.call(deck.querySelectorAll("[data-reveal-slot]"));
    if (!slots.length) return;
    var scope = deck.closest("[data-reveal-root]") || document;
    var counter = scope.querySelector("[data-reveal-counter]");
    var nextBtn = scope.querySelector("[data-reveal-next]");
    var allBtn = scope.querySelector("[data-reveal-all]");
    var live = scope.querySelector("[data-reveal-live]");
    var summary = scope.querySelector("[data-reveal-summary]");
    var controls = scope.querySelectorAll("[data-reveal-controls]");
    var found = scope.querySelector("[data-reveal-found]");
    var foundList = scope.querySelector("[data-reveal-found-list]");
    var foundCount = scope.querySelector("[data-reveal-found-count]");
    var index = 0;

    function announce(text) {
      if (live) live.textContent = text;
    }

    function showSlot(i) {
      slots.forEach(function (s, n) {
        if (n === i) s.setAttribute("data-current", "true");
        else s.removeAttribute("data-current");
      });
    }

    function hideControls() {
      controls.forEach(function (el) { el.classList.add("hidden"); });
    }

    function addToFound(slot) {
      if (!found || !foundList || !slot || slot.dataset.foundAdded === "true") return;
      slot.dataset.foundAdded = "true";
      var name = slot.getAttribute("data-card-name") || "Carte";
      var rarity = slot.getAttribute("data-card-rarity") || "";
      // La photo de la carte uniquement : jamais la miniature du drapeau
      // en légende (pk-card__flag-img), sinon la vignette affiche un
      // drapeau flou étiré quand la carte n'a pas de photo.
      var imgs = slot.querySelectorAll(".reveal-face img");
      var img = null;
      for (var i = 0; i < imgs.length; i++) {
        if (imgs[i].getAttribute("src") && imgs[i].className.indexOf("pk-card__flag-img") === -1) {
          img = imgs[i];
          break;
        }
      }
      var li = document.createElement("li");
      li.className = "reveal-found-item";
      var visual = document.createElement("span");
      visual.className = "reveal-found-thumb";
      visual.setAttribute("aria-hidden", "true");
      if (img && img.getAttribute("src")) {
        var thumb = document.createElement("img");
        thumb.setAttribute("src", img.getAttribute("src"));
        thumb.setAttribute("alt", "");
        thumb.setAttribute("loading", "lazy");
        visual.appendChild(thumb);
      } else {
        // Repli sans photo : monogramme teinté par rareté, plus lisible
        // que le drapeau de légende et cohérent avec les badges.
        visual.textContent = (name || "?").charAt(0).toUpperCase();
        var rarityClass = (slot.className.match(/reveal-slot--([a-z]+)/) || [])[1];
        if (
          rarityClass === "common" ||
          rarityClass === "uncommon" ||
          rarityClass === "rare" ||
          rarityClass === "epic" ||
          rarityClass === "legendary"
        ) {
          visual.style.background = "var(--color-" + rarityClass + "-tint)";
          visual.style.color = "var(--color-" + rarityClass + "-ink)";
        }
      }
      var label = document.createElement("span");
      label.className = "reveal-found-label";
      label.textContent = name;
      li.appendChild(visual);
      li.appendChild(label);
      if (rarity) li.setAttribute("title", name + " — " + rarity);
      foundList.appendChild(li);
      if (foundCount) foundCount.textContent = String(foundList.children.length);
      found.hidden = false;
    }

    function finish() {
      deck.setAttribute("data-phase", "all");
      slots.forEach(function (s) {
        s.setAttribute("data-state", "revealed");
        s.removeAttribute("data-current");
      });
      hideControls();
      if (found) found.hidden = true;
      if (summary) summary.hidden = false;
      var legendary = slots.filter(function (s) {
        return (s.getAttribute("data-card-rarity") || "").toLowerCase().indexOf("gend") !== -1;
      }).length;
      announce(
        "Booster terminé. " + slots.length + " cartes révélées" +
        (legendary ? ", dont " + legendary + " légendaire." : ".")
      );
      if (summary) summary.scrollIntoView({ block: "nearest" });
    }

    function setNextLabel() {
      if (!nextBtn) return;
      var slot = slots[index];
      var revealed = slot && slot.getAttribute("data-state") === "revealed";
      if (!revealed) {
        nextBtn.textContent = index === 0 ? "Révéler la première carte" : "Révéler la carte suivante";
      } else if (index < slots.length - 1) {
        nextBtn.textContent = "Passer à la carte suivante";
      } else {
        nextBtn.textContent = "Voir le récapitulatif";
      }
    }

    function step() {
      var slot = slots[index];
      if (!slot) return;
      if (slot.getAttribute("data-state") !== "revealed") {
        // 1er temps : la carte se révèle et reste affichée en grand au milieu.
        slot.setAttribute("data-state", "revealed");
        addToFound(slot);
        announce(
          "Carte " + (index + 1) + " sur " + slots.length + " : " +
          (slot.getAttribute("data-card-name") || "") + ", " +
          (slot.getAttribute("data-card-rarity") || "") + "."
        );
      } else if (index < slots.length - 1) {
        // 2e temps : on passe au dos de la carte suivante.
        index += 1;
        showSlot(index);
        if (counter) counter.textContent = String(index + 1);
        announce("Carte " + (index + 1) + " sur " + slots.length + ", face cachée.");
      } else {
        finish();
      }
      setNextLabel();
    }

    if (nextBtn) nextBtn.addEventListener("click", step);
    if (allBtn) allBtn.addEventListener("click", function () {
      slots.forEach(function (s) {
        if (s.getAttribute("data-state") !== "revealed") {
          s.setAttribute("data-state", "revealed");
          addToFound(s);
        }
      });
      finish();
      return;
    });
    deck.addEventListener("click", function (event) {
      if (event.target.closest("a, button")) return;
      step();
    });

    showSlot(0);
    if (counter) counter.textContent = "1";
    setNextLabel();
  }

  function initAll(root) {
    (root || document).querySelectorAll("[data-reveal-deck]").forEach(initDeck);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { initAll(document); });
  } else {
    initAll(document);
  }
  document.addEventListener("htmx:afterSwap", function (event) { initAll(event.target); });
})();
