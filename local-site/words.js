(() => {
  "use strict";

  const data = window.ICELAND_CONTENT;
  const escapeHtml = value => String(value ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const placeAudio = Object.fromEntries(Object.values(data.placeAudio?.items || {}).filter(entry => entry.showInApp).map(entry => [entry.local, entry]));

  const audioControls = local => {
    const clip = placeAudio[local];
    if (!clip) return `<button class="audio-placeholder" type="button" disabled aria-label="Audio for ${escapeHtml(local)} not available yet">▶ <span>audio placeholder</span></button>`;
    return `<span class="audio-controls"><button class="audio-play" type="button" data-audio="${escapeHtml(clip.files.normal.file)}" aria-label="Play pronunciation of ${escapeHtml(local)}">▶ Play</button></span>`;
  };

  const vocab = data.vocabulary;
  if (vocab?.groups?.length) {
    document.querySelector("#words-intro").textContent = vocab.intro;
    document.querySelector("#words-note").textContent = vocab.note;
    document.querySelector("#words-jump").innerHTML = vocab.groups.map(group => `<a href="#words-${escapeHtml(group.id)}">${escapeHtml(group.title)}</a>`).join("");
    document.querySelector("#words-groups").innerHTML = vocab.groups.map(group => `
      <section class="word-group" id="words-${escapeHtml(group.id)}" aria-labelledby="words-${escapeHtml(group.id)}-title">
        <h2 id="words-${escapeHtml(group.id)}-title">${escapeHtml(group.title)}</h2>
        <p class="word-group-intro">${escapeHtml(group.intro)}</p>
        ${group.callout ? `<p class="word-callout">${escapeHtml(group.callout)}</p>` : ""}
        <ul class="word-list">${group.items.map(item => `
          <li class="word-row">
            <div class="word-main"><strong class="word-local">${escapeHtml(item.local)}</strong><span class="word-meaning">${escapeHtml(item.meaning)}</span>${item.when ? `<span class="word-when">${escapeHtml(item.when)}</span>` : ""}</div>
            <div class="word-say"><span class="word-respelling">${escapeHtml(item.respelling)}</span>${audioControls(item.local)}</div>
          </li>`).join("")}</ul>
      </section>`).join("");
  }

  let currentAudio = null;
  document.addEventListener("click", event => {
    const button = event.target.closest("[data-audio]");
    if (!button) return;
    if (currentAudio) currentAudio.pause();
    const src = button.dataset.audio;
    const audio = currentAudio = new Audio(src);
    audio.addEventListener("error", () => {
      const retry = window.mfvFallbackUrl && window.mfvFallbackUrl(src); // local file missing: use the public copy
      if (retry && audio === currentAudio) { currentAudio = new Audio(retry); currentAudio.play().catch(() => {}); }
    }, { once: true });
    audio.play().catch(() => {});
  });

  document.querySelector(".theme-button").addEventListener("click", () => document.body.classList.toggle("night"));
  document.querySelector(".menu-button").addEventListener("click", event => {
    const nav = document.querySelector("#primary-nav");
    const open = nav.classList.toggle("open");
    event.currentTarget.setAttribute("aria-expanded", String(open));
  });
})();
