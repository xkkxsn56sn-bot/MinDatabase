(() => {
  function formatAmendedDate(raw) {
    const parsed = new Date(raw);

    if (Number.isNaN(parsed.getTime())) {
      return raw;
    }

    return parsed.toLocaleDateString("en-GB", {
      year: "numeric",
      month: "long",
      day: "2-digit",
    });
  }

  function findContainer() {
    return (
      document.querySelector(".site-footer") ||
      document.querySelector(".entry__nav-footer") ||
      document.querySelector(".endnotes-page__nav-footer") ||
      document.querySelector("main")
    );
  }

  const container = findContainer();
  if (!container || container.querySelector(".amended-on-flag")) {
    return;
  }

  const flag = document.createElement("p");
  flag.className = "amended-on-flag";
  flag.textContent = `Amended on: ${formatAmendedDate(document.lastModified)}`;

  flag.style.marginTop = "0.65rem";
  flag.style.fontSize = "0.85rem";
  flag.style.opacity = "0.75";

  container.appendChild(flag);
})();