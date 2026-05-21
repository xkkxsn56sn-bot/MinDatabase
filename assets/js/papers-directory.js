(() => {
  const heading = document.getElementById("papers-heading");
  const list = document.getElementById("papers-list");

  if (!heading || !list) {
    return;
  }

  function renderError() {
    list.innerHTML =
      "<li>Unable to load papers data. Please verify <strong>assets/data/papers-directory.json</strong>.</li>";
  }

  fetch("/assets/data/papers-directory.json")
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      const [sectionTitle, entries] = Object.entries(data)[0] || [];

      if (!sectionTitle || !Array.isArray(entries)) {
        throw new Error("Invalid papers data");
      }

      heading.textContent = sectionTitle;

      const fragment = document.createDocumentFragment();
      entries.forEach((entry) => {
        const item = document.createElement("li");
        const link = document.createElement("a");
        link.href = entry.href;
        link.textContent = entry.name;
        item.appendChild(link);
        fragment.appendChild(item);
      });

      list.replaceChildren(fragment);
    })
    .catch(() => {
      renderError();
    });
})();
