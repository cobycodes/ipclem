(function () {
  const SPEED_PX_PER_SEC = 21.78;
  const GAP_PX = 18;
  const PAUSE_MS = 3500;
  const SNAP_MS = 420;

  const ICON_MUTED =
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">' +
    '<path fill="currentColor" d="M5 9v6h4l5 5V4L9 9H5z"/>' +
    '<path fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" d="M3.5 3.5l17 17"/>' +
    "</svg>";

  const ICON_UNMUTED =
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">' +
    '<path fill="currentColor" d="M5 9v6h4l5 5V4L9 9H5z"/>' +
    '<path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" d="M16.5 8.5a5 5 0 010 7"/>' +
    '<path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" d="M18.7 6.3a8 8 0 010 11.4"/>' +
    "</svg>";

  const ICON_PREV =
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">' +
    '<path fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" d="M15 5l-7 7 7 7"/>' +
    "</svg>";

  const ICON_NEXT =
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">' +
    '<path fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/>' +
    "</svg>";

  window.addEventListener("DOMContentLoaded", () => {
    const root = document.getElementById("clemSlideshow");
    const track = root && root.querySelector(".hero-slideshow__track");
    const items = window.CLEM_SLIDES || [];

    if (!root || !track || items.length === 0) return;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    // Duplicate the set so the loop can wrap seamlessly
    const loopItems = items.concat(items);
    const videoEls = [];
    /** @type {string|null} id of the one video allowed to play sound; null = all muted */
    let activeVideoId = null;

    function videoIdForItem(item) {
      const primary = (item.sources && item.sources[0] && item.sources[0].src) || "";
      return primary;
    }

    function syncMuteUi() {
      videoEls.forEach((video) => {
        const id = video.dataset.videoId;
        const isActive = activeVideoId !== null && id === activeVideoId;
        const btn = video
          .closest(".hero-slideshow__slide")
          ?.querySelector(".hero-slideshow__mute");
        if (!btn) return;
        btn.innerHTML = isActive ? ICON_UNMUTED : ICON_MUTED;
        btn.setAttribute("aria-label", isActive ? "Mute video" : "Unmute video");
        btn.setAttribute("aria-pressed", isActive ? "true" : "false");
        btn.classList.toggle("is-unmuted", isActive);
      });
    }

    function applyVideoAudio() {
      // At most one video has sound, and only while it is in the spotlight
      videoEls.forEach((video) => {
        const slide = video.closest(".hero-slideshow__slide");
        const isActive =
          activeVideoId !== null && video.dataset.videoId === activeVideoId;
        const inSpotlight = !!(slide && slide.classList.contains("is-spotlight"));
        video.muted = !(isActive && inSpotlight);
      });
    }

    function toggleVideoMute(videoId) {
      // Exclusive unmute: turning on A automatically mutes any other video
      if (activeVideoId === videoId) {
        activeVideoId = null;
      } else {
        activeVideoId = videoId;
      }
      syncMuteUi();
      applyVideoAudio();
    }

    function createSlide(item, index) {
      const slide = document.createElement("div");
      slide.className = "hero-slideshow__slide";
      slide.setAttribute("role", "button");
      slide.tabIndex = 0;

      const baseIndex = index % items.length;

      if (item.type === "video") {
        const videoId = videoIdForItem(item);
        slide.classList.add("hero-slideshow__slide--video");
        slide.setAttribute("aria-label", "Clementine video");

        const video = document.createElement("video");
        video.className = "hero-slideshow__media";
        video.dataset.videoId = videoId;
        video.muted = true;
        video.defaultMuted = true;
        video.volume = 1;
        video.loop = true;
        video.playsInline = true;
        video.setAttribute("playsinline", "");
        video.setAttribute("muted", "");
        video.preload = "metadata";
        video.draggable = false;

        (item.sources || []).forEach((source) => {
          const el = document.createElement("source");
          el.src = source.src;
          if (source.type) el.type = source.type;
          video.appendChild(el);
        });

        slide.appendChild(video);
        videoEls.push(video);

        const dim = document.createElement("div");
        dim.className = "hero-slideshow__dim";
        dim.setAttribute("aria-hidden", "true");
        slide.appendChild(dim);

        const muteBtn = document.createElement("button");
        muteBtn.type = "button";
        muteBtn.className = "hero-slideshow__mute";
        muteBtn.addEventListener("click", (event) => {
          event.stopPropagation();
          toggleVideoMute(videoId);
          video.play().catch(() => {});
        });
        slide.appendChild(muteBtn);
      } else {
        slide.setAttribute("aria-label", `Clementine photo ${baseIndex + 1}`);

        const img = document.createElement("img");
        img.className = "hero-slideshow__media";
        img.src = item.src;
        img.alt = `Clementine photo ${baseIndex + 1}`;
        img.loading = index < 2 ? "eager" : "lazy";
        img.draggable = false;
        slide.appendChild(img);
      }

      track.appendChild(slide);
      return slide;
    }

    const slides = loopItems.map((item, i) => createSlide(item, i));
    // Start fully muted — sync icons to that state
    activeVideoId = null;
    syncMuteUi();
    applyVideoAudio();

    let paused = reducedMotion;
    let offset = 0;
    let loopWidth = 0;
    let rafId = null;
    let lastTs = 0;
    let resumeTimer = null;
    let snapping = false;
    let snapFrom = 0;
    let snapTo = 0;
    let snapStart = 0;

    function measure() {
      const half = slides.length / 2;
      let width = 0;
      for (let i = 0; i < half; i++) {
        width += slides[i].offsetWidth;
      }
      width += GAP_PX * half;
      loopWidth = width;
    }

    function normalizeOffset(value) {
      if (loopWidth <= 0) return value;
      while (value >= 0) value -= loopWidth;
      while (value < -loopWidth) value += loopWidth;
      return value;
    }

    function applyTrackTransform() {
      // Snap to half-pixels to reduce subpixel edge shimmer
      const x = Math.round(offset * 2) / 2;
      track.style.transform = `translate3d(${x}px, 0, 0)`;
    }

    function updateSpotlight() {
      const rootRect = root.getBoundingClientRect();
      const centerX = rootRect.left + rootRect.width / 2;

      slides.forEach((slide) => {
        const rect = slide.getBoundingClientRect();
        const slideCenter = rect.left + rect.width / 2;
        const dist = Math.abs(slideCenter - centerX);
        const maxDist = rootRect.width * 0.55;
        const t = Math.min(1, dist / maxDist);
        const isVideo = slide.classList.contains("hero-slideshow__slide--video");

        const scale = 1 - t * 0.22;
        const opacity = 1 - t * 0.42;

        if (isVideo) {
          // Never fade <video> with opacity — it pixelates badly while scrolling.
          // Dim with an overlay and keep the video fully opaque.
          slide.style.transform = `translateZ(0) scale(${scale})`;
          slide.style.opacity = "1";
          slide.style.filter = "";
          const dim = slide.querySelector(".hero-slideshow__dim");
          if (dim) dim.style.opacity = String(t * 0.42);
        } else {
          slide.style.transform = `translateZ(0) scale(${scale})`;
          slide.style.opacity = String(opacity);
          slide.style.filter = "";
        }

        slide.classList.toggle("is-spotlight", t < 0.18);
      });

      applyVideoAudio();
    }

    function easeOutCubic(t) {
      return 1 - Math.pow(1 - t, 3);
    }

    function scheduleResume() {
      clearTimeout(resumeTimer);
      if (reducedMotion) return;
      resumeTimer = setTimeout(() => {
        paused = false;
        lastTs = 0;
      }, PAUSE_MS);
    }

    function pauseScrollBriefly() {
      paused = true;
      scheduleResume();
    }

    function snapSlideToCenter(slide) {
      const rootRect = root.getBoundingClientRect();
      const centerX = rootRect.left + rootRect.width / 2;
      const slideRect = slide.getBoundingClientRect();
      const slideCenter = slideRect.left + slideRect.width / 2;
      const delta = centerX - slideCenter;

      if (Math.abs(delta) < 2) {
        pauseScrollBriefly();
        return;
      }

      snapFrom = offset;
      snapTo = offset + delta;
      snapStart = performance.now();
      snapping = true;
      paused = true;
      clearTimeout(resumeTimer);
    }

    function onSlideActivate(slide) {
      if (snapping) return;
      snapSlideToCenter(slide);
    }

    function tick(ts) {
      if (!lastTs) lastTs = ts;
      const dt = Math.min(48, ts - lastTs) / 1000;
      lastTs = ts;

      if (snapping) {
        const elapsed = ts - snapStart;
        const t = Math.min(1, elapsed / SNAP_MS);
        const eased = reducedMotion ? 1 : easeOutCubic(t);
        offset = snapFrom + (snapTo - snapFrom) * eased;
        applyTrackTransform();

        if (t >= 1) {
          offset = normalizeOffset(snapTo);
          snapping = false;
          applyTrackTransform();
          pauseScrollBriefly();
        }
      } else if (!paused && loopWidth > 0) {
        offset += SPEED_PX_PER_SEC * dt;
        if (offset >= 0) offset -= loopWidth;
        applyTrackTransform();
      }

      updateSpotlight();
      rafId = requestAnimationFrame(tick);
    }

    function ensureVideosPlaying() {
      videoEls.forEach((video) => {
        video.play().catch(() => {});
      });
    }

    function start() {
      measure();
      offset = loopWidth > 0 ? -loopWidth : 0;
      applyTrackTransform();
      updateSpotlight();
      ensureVideosPlaying();

      if (rafId) cancelAnimationFrame(rafId);
      lastTs = 0;
      rafId = requestAnimationFrame(tick);
    }

    function getClosestSlideIndex() {
      const rootRect = root.getBoundingClientRect();
      const centerX = rootRect.left + rootRect.width / 2;
      let bestIndex = 0;
      let bestDist = Infinity;

      slides.forEach((slide, i) => {
        const rect = slide.getBoundingClientRect();
        const slideCenter = rect.left + rect.width / 2;
        const dist = Math.abs(slideCenter - centerX);
        if (dist < bestDist) {
          bestDist = dist;
          bestIndex = i;
        }
      });

      return bestIndex;
    }

    function finishSnapNow() {
      if (!snapping) return;
      offset = normalizeOffset(snapTo);
      snapping = false;
      applyTrackTransform();
      updateSpotlight();
    }

    function step(direction) {
      // direction: -1 = previous (left), +1 = next (right)
      finishSnapNow();
      const current = getClosestSlideIndex();
      const targetIndex = (current + direction + slides.length) % slides.length;
      snapSlideToCenter(slides[targetIndex]);
    }

    function createNavButton(kind, label, icon, direction) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = `hero-slideshow__nav hero-slideshow__nav--${kind}`;
      btn.setAttribute("aria-label", label);
      btn.innerHTML = icon;
      btn.addEventListener("click", (event) => {
        event.stopPropagation();
        step(direction);
      });
      root.appendChild(btn);
      return btn;
    }

    createNavButton("prev", "Previous photo", ICON_PREV, -1);
    createNavButton("next", "Next photo", ICON_NEXT, 1);

    slides.forEach((slide) => {
      slide.addEventListener("click", (event) => {
        event.stopPropagation();
        onSlideActivate(slide);
      });

      slide.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSlideActivate(slide);
        }
      });
    });

    window.addEventListener("resize", () => {
      measure();
      offset = normalizeOffset(offset);
      applyTrackTransform();
      updateSpotlight();
    });

    // Wait for media so measurements are accurate
    const media = track.querySelectorAll("img, video");
    let pending = media.length;
    const onReady = () => {
      pending -= 1;
      if (pending <= 0) start();
    };
    media.forEach((el) => {
      if (el.tagName === "IMG") {
        if (el.complete) onReady();
        else {
          el.addEventListener("load", onReady, { once: true });
          el.addEventListener("error", onReady, { once: true });
        }
      } else {
        if (el.readyState >= 1) onReady();
        else {
          el.addEventListener("loadedmetadata", onReady, { once: true });
          el.addEventListener("error", onReady, { once: true });
        }
      }
    });

    window.setTimeout(() => {
      if (pending > 0) start();
    }, 1500);

    // Browsers sometimes pause background tabs — kick playback on return
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) ensureVideosPlaying();
    });
  });
})();
