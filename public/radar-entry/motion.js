"use strict";

const reducedRadarMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

for (const video of document.querySelectorAll("video[data-radar-motion]")) {
  const toggle = video.parentElement.querySelector("[data-radar-toggle]");
  const playText = toggle.querySelector("[data-radar-play]");
  const pauseText = toggle.querySelector("[data-radar-pause]");
  let userChoice;
  let inView = false;

  function sync() {
    const allowMotion = userChoice ?? !reducedRadarMotion.matches;
    if (!allowMotion || !inView || document.hidden) {
      video.pause();
      return;
    }
    if (!video.hasAttribute("src")) video.src = "/radar-entry/gov-radar-intro.mp4";
    video.play().catch(() => {});
  }

  function updateToggle() {
    playText.hidden = !video.paused;
    pauseText.hidden = video.paused;
  }

  toggle.addEventListener("click", () => {
    userChoice = video.paused;
    sync();
  });
  video.addEventListener("play", updateToggle);
  video.addEventListener("pause", updateToggle);
  video.addEventListener("error", () => { toggle.hidden = true; });
  document.addEventListener("visibilitychange", sync);
  reducedRadarMotion.addEventListener("change", sync);
  new IntersectionObserver(([entry]) => {
    inView = entry.isIntersecting;
    sync();
  }).observe(video);
  toggle.hidden = false;
}
