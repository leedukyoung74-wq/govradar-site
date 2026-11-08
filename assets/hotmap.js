/* GOV RADAR hot-zone mini maps: regional map + rotating radar sweep + rippling hotspot.
   Usage: <div class="hotmap" data-focus="IR,OM,AE" data-hl="IR" data-pts='[[26.57,56.25]]'></div> */
(function () {
  let n = 0;
  function ripple(box) {
    box.querySelectorAll(".hm-wave").forEach(x => x.remove());
    const marks = box.querySelectorAll("circle.jvm-marker, .jvm-markers-group circle");
    const host = box.getBoundingClientRect();
    marks.forEach((m, i) => {
      const cx = m.getAttribute("cx"), cy = m.getAttribute("cy"); if (cx == null) return;
      for (let k = 0; k < 3; k++) {
        const c = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        c.setAttribute("cx", cx); c.setAttribute("cy", cy); c.setAttribute("r", m.getAttribute("r") || 4);
        c.setAttribute("class", "hm-wave"); c.style.animationDelay = (k * 0.8 + i * 0.3) + "s";
        m.parentNode.insertBefore(c, m);
      }
      if (i === 0) { const r = m.getBoundingClientRect(); box.style.setProperty("--cx", ((r.left + r.width / 2 - host.left) / host.width * 100) + "%"); box.style.setProperty("--cy", ((r.top + r.height / 2 - host.top) / host.height * 100) + "%"); }
    });
  }
  function draw(box) {
    if (box.dataset.done) return; box.dataset.done = "1";
    const focus = (box.dataset.focus || "").split(",").filter(Boolean), hl = (box.dataset.hl || "").split(",").filter(Boolean);
    let pts = []; try { pts = JSON.parse(box.dataset.pts || "[]"); } catch (e) {}
    const sw = document.createElement("div"); sw.className = "hm-sweep"; box.appendChild(sw);
    const rings = document.createElement("div"); rings.className = "hm-rings"; box.appendChild(rings);
    if (typeof jsVectorMap === "undefined") { box.classList.add("nomap"); return; }
    const inner = document.createElement("div"); inner.className = "hm-map"; inner.id = "hm" + (++n); box.insertBefore(inner, sw);
    const vals = {}; hl.forEach(k => vals[k] = "hl");
    try {
      const map = new jsVectorMap({
        selector: "#" + inner.id, map: "world", zoomButtons: false, zoomOnScroll: false, draggable: false, zoomMax: 40,
        backgroundColor: "transparent", showTooltip: false,
        regionStyle: { initial: { fill: "#303945", stroke: "#0b0e12", strokeWidth: 0.4, fillOpacity: 1 }, hover: { fill: "#303945", cursor: "default" } },
        series: { regions: [{ attribute: "fill", values: vals, scale: { hl: "#743226" } }] },
        markers: pts.map(p => ({ coords: [p[0], p[1]] })),
        markerStyle: { initial: { fill: "#ff5a3c", stroke: "#ffd9cf", strokeWidth: 1.4, r: 4.5 }, hover: { fill: "#ff5a3c" } },
        focusOn: focus.length && focus[0] !== "WORLD" ? { regions: focus, animate: false } : undefined
      });
      const go = () => ripple(box);
      setTimeout(go, 120); setTimeout(go, 700);
      let t; window.addEventListener("resize", () => { clearTimeout(t); t = setTimeout(go, 250); });
      box._map = map;
    } catch (e) { box.classList.add("nomap"); }
  }
  function init() {
    const all = document.querySelectorAll(".hotmap"); if (!all.length) return;
    if ("IntersectionObserver" in window) {
      const io = new IntersectionObserver(es => es.forEach(x => { if (x.isIntersecting) { draw(x.target); io.unobserve(x.target); } }), { rootMargin: "200px" });
      all.forEach(b => io.observe(b));
      setTimeout(() => all.forEach(b => { if (!b.dataset.done) { io.unobserve(b); draw(b); } }), 2500);
    } else all.forEach(draw);
  }
  window.gvHotmap = function (el) { if (el) draw(el); };
  if (document.readyState === "complete") init(); else window.addEventListener("load", init);
})();
