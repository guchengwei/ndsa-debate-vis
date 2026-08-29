(() => {
  const MOBILE_MAX_WIDTH = 620;

  function centerGraph(graph) {
    if (window.innerWidth > MOBILE_MAX_WIDTH || graph.dataset.mobileCentered === "true") {
      return;
    }
    if (!graph.querySelector(".js-plotly-plot")) {
      return;
    }

    const maxScroll = graph.scrollWidth - graph.clientWidth;
    if (maxScroll > 0) {
      graph.scrollLeft = maxScroll / 2;
      graph.dataset.mobileCentered = "true";
    }
  }

  function centerGraphs() {
    document.querySelectorAll(".graph").forEach(centerGraph);
  }

  const observer = new MutationObserver(() => requestAnimationFrame(centerGraphs));

  function start() {
    centerGraphs();
    observer.observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start, { once: true });
  } else {
    start();
  }
})();
