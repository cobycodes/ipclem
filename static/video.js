function updateMuteButton(btn, video) {
  const muted = video.muted || video.volume === 0;
  btn.textContent = muted ? "Unmute" : "Mute";
  btn.setAttribute("aria-pressed", String(!muted));
}

function togglePlay(video) {
  if (video.paused) {
    const p = video.play();
    if (p && typeof p.catch === "function") p.catch(() => {});
  } else {
    video.pause();
  }
}

window.addEventListener("DOMContentLoaded", () => {
  const video = document.getElementById("clemVideo");
  const muteBtn = document.getElementById("clemMuteBtn");

  if (!video || !muteBtn) return;

  // Ensure we start muted for autoplay policies.
  video.muted = true;
  updateMuteButton(muteBtn, video);

  muteBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    video.muted = !video.muted;
    if (!video.muted && video.volume === 0) video.volume = 1;
    updateMuteButton(muteBtn, video);
  });

  video.addEventListener("click", () => togglePlay(video));
  video.addEventListener("volumechange", () => updateMuteButton(muteBtn, video));
});

