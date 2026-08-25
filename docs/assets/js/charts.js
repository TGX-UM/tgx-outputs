// Render every <div class="tgx-chart" data-spec='...'> with vega-embed.
// Re-renders on theme change so the axis colours follow Material's light/dark toggle.
(function () {
  // Where the site is deployed. Derived from this script's own src, so it is correct
  // at the site root, on a sub-page, and under a GitHub Pages project subpath alike.
  var SELF = document.currentScript && document.currentScript.src;
  var BASE = SELF ? SELF.replace(/assets\/js\/charts\.js.*$/, "") : "/";

  // Vega-Lite's width:"container" measures the parent at embed time, and on this
  // theme that measurement can land before layout has settled -- which renders an SVG
  // of width 0 and a chart that is silently invisible rather than broken. Measuring
  // here and passing a number avoids the whole failure mode.
  function sized(spec, el) {
    var w = el.clientWidth || (el.parentElement && el.parentElement.clientWidth) || 0;
    if (w <= 0) { return spec; }
    // A faceted spec carries no width of its own: the number belongs to the panel
    // inside it, and setting it at the top level is ignored with only a console
    // warning. Leave room for the row-header labels down the left.
    if (spec.facet && spec.spec) {
      spec.spec.width = Math.max(220, w - 96);
    } else {
      spec.width = Math.max(260, w - 8);
    }
    return spec;
  }

  function absolutise(spec) {
    if (spec && spec.data && typeof spec.data.url === "string" &&
        !/^([a-z]+:)?\/\//i.test(spec.data.url)) {
      spec.data.url = BASE + spec.data.url.replace(/^\.?\//, "");
    }
    return spec;
  }

  function currentScheme() {
    return document.body.getAttribute("data-md-color-scheme") === "slate"
      ? "dark" : "light";
  }

  function themed(spec) {
    var ink = currentScheme() === "dark" ? "#b6bcc6" : "#5b6470";
    var clone = JSON.parse(JSON.stringify(spec));
    clone.config = clone.config || {};
    clone.config.axis = Object.assign({}, clone.config.axis,
      { labelColor: ink, titleColor: ink });
    clone.config.legend = Object.assign({}, clone.config.legend,
      { labelColor: ink, titleColor: ink });
    return clone;
  }

  function renderAll() {
    document.querySelectorAll(".tgx-chart").forEach(function (el) {
      var holder = el.querySelector("script.tgx-spec");
      if (!holder) { return; }
      var spec;
      try {
        spec = JSON.parse(holder.textContent);
      } catch (err) {
        // A malformed spec must be visible, not silently blank.
        el.innerHTML = '<p class="tgx-chart-error">Chart failed to load.</p>';
        return;
      }
      if (el.dataset.rendered === "1" && !el.querySelector("script.tgx-spec")) { return; }
      var target = el.querySelector(".tgx-chart-target");
      if (!target) {
        target = document.createElement("div");
        target.className = "tgx-chart-target";
        el.appendChild(target);
      }
      vegaEmbed(target, sized(absolutise(themed(spec)), el), { actions: false, renderer: "svg" })
        .then(function () {
          // The min-height reserves the column while the chart is still loading, so
          // the page does not jump. Once something is drawn it is dead space, and a
          // faceted chart of two rows leaves a hand's width of it above the caption.
          el.style.minHeight = "0";
        })
        .catch(function () {
          target.innerHTML =
            '<p class="tgx-chart-error">Chart failed to load. ' +
            'The data behind it is still available as CSV below.</p>';
        });
    });
  }

  // A timer, not requestAnimationFrame: rAF is throttled indefinitely in a background
  // tab, so a page opened in one would show no charts at all until it was focused.
  function schedule() { setTimeout(renderAll, 0); }

  if (document.readyState === "complete") { schedule(); }
  else { window.addEventListener("load", schedule); }

  var resizeTimer = null;
  window.addEventListener("resize", function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(renderAll, 250);
  });

  new MutationObserver(function (muts) {
    muts.forEach(function (m) {
      if (m.attributeName === "data-md-color-scheme") { renderAll(); }
    });
  }).observe(document.body, { attributes: true });
})();
