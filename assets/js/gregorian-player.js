(function () {
  var TRACKS = [
    {
      title: "Agnus Dei (polyphony)",
      src: "/assets/audio/gregoriano/Agnus-Dei-polyphony.mp3",
    },
    {
      title: "Antiphona et Magnificat",
      src: "/assets/audio/gregoriano/Antiphona-et-Magnificat.ogg",
    },
    {
      title: "De Profundis",
      src: "/assets/audio/gregoriano/De-profundis.ogg",
    },
    {
      title: "Dies Irae",
      src: "/assets/audio/gregoriano/Dies-Irae.mp3",
    },
    {
      title: "Kyrie",
      src: "/assets/audio/gregoriano/Kyrie.mp3",
    },
    {
      title: "Lamentation",
      src: "/assets/audio/gregoriano/Lamentation.ogg",
    },
    {
      title: "Loquetur Dominus",
      src: "/assets/audio/gregoriano/Loquetur-Dominus.ogg",
    },
    {
      title: "Pater Noster",
      src: "/assets/audio/gregoriano/Pater-Noster.ogg",
    },
    {
      title: "Salve Regina",
      src: "/assets/audio/gregoriano/Salve-Regina.ogg",
    },
    {
      title: "Sanctus (polyphony)",
      src: "/assets/audio/gregoriano/Sanctus-polyphony.mp3",
    },
    {
      title: "Veni Creator Spiritus",
      src: "/assets/audio/gregoriano/Veni-Creator-Spiritus.mp3",
    },
    {
      title: "Veni Sancte Spiritus",
      src: "/assets/audio/gregoriano/Veni-Sancte-Spiritus.ogg",
    },
  ];

  if (!TRACKS.length) {
    return;
  }

  var KEYS = {
    index: "gregorian.index",
    enabled: "gregorian.enabled",
    time: "gregorian.time",
    volume: "gregorian.volume",
    muted: "gregorian.muted",
    mode: "gregorian.mode",
  };

  function storage() {
    try {
      var test = "__gregorian_test__";
      window.sessionStorage.setItem(test, "1");
      window.sessionStorage.removeItem(test);
      return window.sessionStorage;
    } catch (error) {
      return null;
    }
  }

  var store = storage();
  if (!store) {
    return;
  }

  function toNumber(value, fallback) {
    var parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function toBoolean(value, fallback) {
    if (value === "true") return true;
    if (value === "false") return false;
    return fallback;
  }

  function pickRandomTrackIndex() {
    return Math.floor(Math.random() * TRACKS.length);
  }

  function getTrackIndex() {
    var saved = toNumber(store.getItem(KEYS.index), -1);
    if (saved >= 0 && saved < TRACKS.length) {
      return saved;
    }

    var randomIndex = pickRandomTrackIndex();
    store.setItem(KEYS.index, String(randomIndex));
    store.setItem(KEYS.time, "0");
    return randomIndex;
  }

  function saveCurrentTime(audio) {
    if (!audio || !Number.isFinite(audio.currentTime)) {
      return;
    }
    store.setItem(KEYS.time, String(audio.currentTime));
  }

  function formatTrackLabel(track) {
    return track && track.title ? track.title : "Canto gregoriano";
  }

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  function getMode() {
    var saved = store.getItem(KEYS.mode);
    return saved === "rotate" ? "rotate" : "loop";
  }

  function injectStyles() {
    if (document.getElementById("gregorian-player-style")) {
      return;
    }

    var style = document.createElement("style");
    style.id = "gregorian-player-style";
    style.textContent =
      ".gregorian-player{position:fixed;right:14px;bottom:14px;z-index:1200;display:flex;align-items:center;gap:.5rem;background:rgba(24,20,16,.9);color:#f5ecdd;border:1px solid rgba(255,229,173,.4);border-radius:999px;padding:.45rem .65rem;box-shadow:0 8px 18px rgba(0,0,0,.28);font-family:Georgia,serif;font-size:.86rem;max-width:min(94vw,780px)}" +
      ".gregorian-player__title{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:34ch;opacity:.95}" +
      ".gregorian-player__button{appearance:none;border:1px solid rgba(255,229,173,.4);background:rgba(201,169,97,.18);color:#fff4da;border-radius:999px;padding:.28rem .58rem;font:inherit;font-weight:700;cursor:pointer}" +
      ".gregorian-player__volume{accent-color:#f4c96f;width:120px;cursor:pointer}" +
      ".gregorian-player__volume-value{min-width:3.2ch;text-align:right;font-variant-numeric:tabular-nums;color:#f7dfad}" +
      ".gregorian-player__button:hover{background:rgba(201,169,97,.3)}" +
      ".gregorian-player__button:focus-visible{outline:2px solid #f4c96f;outline-offset:2px}" +
      "@media (max-width:700px){.gregorian-player{left:10px;right:10px;bottom:10px;border-radius:14px;justify-content:space-between;flex-wrap:wrap}.gregorian-player__title{max-width:70vw;flex:1 0 100%}.gregorian-player__volume{width:100px}}";
    document.head.appendChild(style);
  }

  function createUi(trackTitle) {
    var wrap = document.createElement("div");
    wrap.className = "gregorian-player";
    wrap.setAttribute("role", "group");
    wrap.setAttribute("aria-label", "Controlli canti gregoriani");

    var title = document.createElement("span");
    title.className = "gregorian-player__title";
    title.textContent = trackTitle;

    var toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "gregorian-player__button";
    toggle.textContent = "Attiva canti";

    var mute = document.createElement("button");
    mute.type = "button";
    mute.className = "gregorian-player__button";
    mute.textContent = "Muto";

    var mode = document.createElement("button");
    mode.type = "button";
    mode.className = "gregorian-player__button";
    mode.textContent = "Modalita: Loop";

    var volume = document.createElement("input");
    volume.type = "range";
    volume.className = "gregorian-player__volume";
    volume.min = "0";
    volume.max = "100";
    volume.step = "1";
    volume.value = "25";
    volume.setAttribute("aria-label", "Volume canti gregoriani");

    var volumeValue = document.createElement("span");
    volumeValue.className = "gregorian-player__volume-value";
    volumeValue.textContent = "25%";

    wrap.appendChild(title);
    wrap.appendChild(toggle);
    wrap.appendChild(mute);
    wrap.appendChild(mode);
    wrap.appendChild(volume);
    wrap.appendChild(volumeValue);

    document.body.appendChild(wrap);

    return {
      title: title,
      toggle: toggle,
      mute: mute,
      mode: mode,
      volume: volume,
      volumeValue: volumeValue,
    };
  }

  function initPlayer() {
    var trackIndex = getTrackIndex();
    var track = TRACKS[trackIndex];
    var shouldPlay = toBoolean(store.getItem(KEYS.enabled), false);
    var savedTime = Math.max(0, toNumber(store.getItem(KEYS.time), 0));
    var savedVolume = clamp(toNumber(store.getItem(KEYS.volume), 0.25), 0, 1);
    var savedMuted = toBoolean(store.getItem(KEYS.muted), false);
    var playMode = getMode();

    var audio = document.createElement("audio");
    audio.src = track.src;
    audio.preload = "auto";
    audio.loop = playMode === "loop";
    audio.volume = savedVolume;
    audio.muted = savedMuted;

    var inlineToggle = document.getElementById("gregorian-inline-toggle");
    var inlineVolume = document.getElementById("gregorian-inline-volume");
    if (!inlineToggle) {
      // Disable the floating player fallback: only pages with inline controls can use audio.
      return;
    }
    var ui;

    ui = { toggle: inlineToggle, inlineVolume: inlineVolume };
    if (audio.volume <= 0.001) {
      audio.volume = 0.25;
      store.setItem(KEYS.volume, "0.25");
    }
    if (audio.muted) {
      audio.muted = false;
      store.setItem(KEYS.muted, "false");
    }

    function refreshButtons() {
      ui.toggle.textContent = audio.paused ? "Riproduci" : "Pausa";
      if (!shouldPlay && audio.paused) {
        ui.toggle.textContent = inlineToggle ? "Attiva audio" : "Attiva canti";
      }
      if (ui.inlineVolume) {
        if (audio.muted) {
          ui.inlineVolume.textContent = "muted";
        } else {
          ui.inlineVolume.textContent =
            String(Math.round(audio.volume * 100)) + "%";
        }
      }
      if (ui.mute) {
        ui.mute.textContent = audio.muted ? "Audio" : "Muto";
      }
      if (ui.mode) {
        ui.mode.textContent =
          playMode === "loop" ? "Modalita: Loop" : "Modalita: Rotazione";
      }
    }

    audio.addEventListener("loadedmetadata", function () {
      if (savedTime > 0 && savedTime < audio.duration - 0.75) {
        audio.currentTime = savedTime;
      }
    });

    var saveTick = 0;
    audio.addEventListener("timeupdate", function () {
      var now = Date.now();
      if (now - saveTick > 1000) {
        saveTick = now;
        saveCurrentTime(audio);
      }
    });

    function attemptPlay() {
      if (!ui.volume) {
        if (audio.volume <= 0.001) {
          audio.volume = 0.25;
          store.setItem(KEYS.volume, "0.25");
        }
        if (audio.muted) {
          audio.muted = false;
          store.setItem(KEYS.muted, "false");
        }
      }

      var playPromise = audio.play();
      if (!playPromise || typeof playPromise.then !== "function") {
        return;
      }

      playPromise
        .then(function () {
          shouldPlay = true;
          store.setItem(KEYS.enabled, "true");
          refreshButtons();
        })
        .catch(function () {
          refreshButtons();
        });
    }

    ui.toggle.addEventListener("click", function () {
      if (audio.paused) {
        if (!ui.volume) {
          if (audio.volume <= 0.001) {
            audio.volume = 0.25;
            store.setItem(KEYS.volume, "0.25");
          }
          if (audio.muted) {
            audio.muted = false;
            store.setItem(KEYS.muted, "false");
          }
        }
        shouldPlay = true;
        store.setItem(KEYS.enabled, "true");
        attemptPlay();
      } else {
        audio.pause();
        store.setItem(KEYS.enabled, "false");
        shouldPlay = false;
        saveCurrentTime(audio);
        refreshButtons();
      }
    });

    if (ui.mute) {
      ui.mute.addEventListener("click", function () {
        audio.muted = !audio.muted;
        store.setItem(KEYS.muted, audio.muted ? "true" : "false");
        refreshButtons();
      });
    }

    if (ui.mode) {
      ui.mode.addEventListener("click", function () {
        playMode = playMode === "loop" ? "rotate" : "loop";
        audio.loop = playMode === "loop";
        store.setItem(KEYS.mode, playMode);
        refreshButtons();
      });
    }

    if (ui.volume) {
      ui.volume.addEventListener("input", function () {
        var level = clamp(toNumber(ui.volume.value, 25), 0, 100) / 100;
        audio.volume = level;
        ui.volumeValue.textContent = String(Math.round(level * 100)) + "%";
        if (audio.muted && level > 0) {
          audio.muted = false;
          store.setItem(KEYS.muted, "false");
        }
        refreshButtons();
      });
    }

    audio.addEventListener("volumechange", function () {
      store.setItem(KEYS.volume, String(audio.volume));
      if (ui.volume) {
        ui.volume.value = String(Math.round(audio.volume * 100));
      }
      if (ui.inlineVolume) {
        if (audio.muted) {
          ui.inlineVolume.textContent = "muted";
        } else {
          ui.inlineVolume.textContent =
            String(Math.round(audio.volume * 100)) + "%";
        }
      }
      if (ui.volumeValue) {
        var percent = String(Math.round(audio.volume * 100)) + "%";
        ui.volumeValue.textContent = percent;
      }
    });

    audio.addEventListener("ended", function () {
      if (playMode !== "rotate") {
        return;
      }

      var nextIndex = trackIndex;
      if (TRACKS.length > 1) {
        while (nextIndex === trackIndex) {
          nextIndex = pickRandomTrackIndex();
        }
      }

      trackIndex = nextIndex;
      track = TRACKS[trackIndex];
      store.setItem(KEYS.index, String(trackIndex));
      store.setItem(KEYS.time, "0");
      if (ui.title) {
        ui.title.textContent = formatTrackLabel(track);
      }
      audio.src = track.src;
      audio.currentTime = 0;

      if (shouldPlay) {
        attemptPlay();
      }
    });

    function persistBeforeLeave() {
      saveCurrentTime(audio);
    }

    window.addEventListener("pagehide", persistBeforeLeave);
    window.addEventListener("beforeunload", persistBeforeLeave);

    refreshButtons();

    if (shouldPlay) {
      attemptPlay();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initPlayer);
  } else {
    initPlayer();
  }
})();
