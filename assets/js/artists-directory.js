(() => {
  const navContainer = document.getElementById("century-nav");
  const sectionsContainer = document.getElementById("century-sections");

  if (!navContainer || !sectionsContainer) {
    return;
  }

  function centuryToId(centuryName) {
    return `c-${centuryName.split(" ")[0].toLowerCase()}`;
  }

  function buildCenturyNav(centuries) {
    const fragment = document.createDocumentFragment();

    centuries.forEach((centuryName) => {
      const link = document.createElement("a");
      link.href = `#${centuryToId(centuryName)}`;
      link.textContent = centuryName.split(" ")[0];
      fragment.appendChild(link);
    });

    navContainer.replaceChildren(fragment);
  }

  function buildCenturySections(data) {
    const fragment = document.createDocumentFragment();

    Object.entries(data).forEach(([centuryName, artists]) => {
      const section = document.createElement("section");
      section.className = "century-section";
      section.id = centuryToId(centuryName);

      const heading = document.createElement("h2");
      heading.textContent = centuryName;

      const list = document.createElement("ul");

      artists.forEach((artist) => {
        const item = document.createElement("li");
        const link = document.createElement("a");
        link.href = artist.href;
        link.textContent = artist.name;
        item.appendChild(link);
        list.appendChild(item);
      });

      section.appendChild(heading);
      section.appendChild(list);
      fragment.appendChild(section);
    });

    sectionsContainer.replaceChildren(fragment);
  }

  function renderError() {
    sectionsContainer.innerHTML =
      '<section class="century-section"><p>Unable to load the artist directory data.</p><p>Please verify <strong>assets/data/artists-directory.json</strong> exists and is valid JSON.</p></section>';
  }

  fetch("assets/data/artists-directory.json")
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      const centuries = Object.keys(data);
      buildCenturyNav(centuries);
      buildCenturySections(data);
    })
    .catch(() => {
      renderError();
    });
})();
