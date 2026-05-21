const fs = require("fs");
const path = require("path");

const DATA_PATH = path.join(
  __dirname,
  "..",
  "assets",
  "data",
  "artists-directory.json",
);

function sortArtistsDirectory() {
  const raw = fs.readFileSync(DATA_PATH, "utf8");
  const parsed = JSON.parse(raw);

  const sortedByCentury = {};

  for (const [century, artists] of Object.entries(parsed)) {
    sortedByCentury[century] = [...artists].sort((a, b) =>
      a.name.localeCompare(b.name, "it", { sensitivity: "base" }),
    );
  }

  fs.writeFileSync(
    DATA_PATH,
    `${JSON.stringify(sortedByCentury, null, 2)}\n`,
    "utf8",
  );

  const centuryCount = Object.keys(sortedByCentury).length;
  const totalArtists = Object.values(sortedByCentury).reduce(
    (total, artists) => total + artists.length,
    0,
  );

  console.log(
    `Sorted ${totalArtists} artists across ${centuryCount} centuries.`,
  );
}

sortArtistsDirectory();
