"use strict";

const playgroundPreview = document.querySelector("[data-playground-motion]");

if (playgroundPreview) {
  const preference = window.matchMedia("(prefers-reduced-motion: reduce)");
  const toggle = playgroundPreview.querySelector("[data-playground-toggle]");
  const playLabel = toggle.querySelector("[data-playground-play]");
  const pauseLabel = toggle.querySelector("[data-playground-pause]");
  let userChoice;
  let inView = !("IntersectionObserver" in window);

  const enabled = () => userChoice ?? !preference.matches;

  function sync() {
    const play = enabled();
    playgroundPreview.classList.toggle("is-playing", play && inView && !document.hidden);
    playLabel.hidden = play;
    pauseLabel.hidden = !play;
  }

  toggle.addEventListener("click", () => {
    userChoice = !enabled();
    sync();
  });
  preference.addEventListener("change", sync);
  document.addEventListener("visibilitychange", sync);
  if ("IntersectionObserver" in window) {
    new IntersectionObserver(([entry]) => {
      inView = entry.isIntersecting;
      sync();
    }).observe(playgroundPreview);
  }
  sync();
  toggle.hidden = false;
}
