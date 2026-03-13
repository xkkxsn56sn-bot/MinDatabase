# MinDatabaseApp — iOS

A SwiftUI app for iPhone and iPad that lets you browse and read the complete MinDatabase scholarly content: medieval artists (VII–XIV century), churches, and codices — fully offline.

---

## Requirements

| Requirement | Version |
|---|---|
| Xcode | 15 or later |
| iOS deployment target | 16.0 or later |
| macOS (host) | Ventura 13.0 or later |

---

## Setting up the Xcode project

### 1. Create a new iOS app

1. Open Xcode → **File › New › Project…**
2. Choose **iOS › App**, click **Next**
3. Fill in:
   - **Product Name:** `MinDatabaseApp`
   - **Team:** your Apple Developer account
   - **Organization Identifier:** e.g. `com.yourname`
   - **Interface:** SwiftUI
   - **Language:** Swift
4. Set **Minimum Deployments** to **iOS 16.0**
5. Save the project to any convenient location on your Mac (e.g. your Desktop or Documents).  
   ⚠️ Do **not** save inside the cloned `ios-app/` folder — Xcode would try to create a `MinDatabaseApp/` subfolder there, but that directory already exists.

### 2. Add the source files

Delete the default `ContentView.swift` and `<AppName>App.swift` that Xcode generated.

Then drag the entire `MinDatabaseApp/` folder from this directory into the Xcode project navigator.  
In the dialog that appears choose:
- ✅ **Copy items if needed** (if the folder is outside your project directory)
- **Added folders:** Create groups

You should end up with the following groups in the navigator:

```
MinDatabaseApp/
├── App/
│   ├── MinDatabaseApp.swift   ← @main entry point
│   └── ContentView.swift
├── Models/
│   └── Entry.swift
├── Services/
│   └── ContentLoader.swift
└── Views/
    ├── ArtistsView.swift
    ├── ChurchesView.swift
    ├── CodicesView.swift
    ├── EntryDetailView.swift
    ├── EntryRowView.swift
    ├── MarkdownBodyView.swift
    └── SearchView.swift
```

### 3. Bundle the content

The app reads Markdown files directly from the **app bundle** at runtime.

1. In the Finder, locate the `Content/` folder at the **root of this repository**.
2. Drag it into the Xcode project navigator (anywhere inside the yellow app group).
3. In the dialog:
   - **Added folders:** choose **"Create folder references"** (the folder icon turns **blue**)  
     ⚠️ *Do not* choose "Create groups" — the app uses `FileManager` to enumerate the folder hierarchy, which only works with blue folder references.
4. Make sure **"Copy items if needed"** is checked if working from a separate location.

After this step the Xcode project tree should show a blue `Content` folder containing `Artists/`, `Churches/`, and `Codex/`.

### 4. Build & Run

Select an iPhone or iPad simulator (iOS 16+), press **⌘R**.  
The app launches with a loading screen, then opens the four-tab interface.

---

## App structure

| Tab | Content | Behaviour |
|---|---|---|
| **Artists** | All artist entries | Grouped by century (VII → XIV); tap for full essay |
| **Churches** | All church entries | Alphabetical list; tap for full entry |
| **Codices** | All codex/manuscript entries | Alphabetical list; tap for full entry |
| **Search** | Across all content | Searches title, subtitle and full body text |

### Detail view

Each entry shows:
- Category pill (Artists / Churches / Codices)
- Title, subtitle and date range
- Full scholarly prose with `## Section headings` rendered as styled headers and inline Markdown (bold, italic) rendered correctly

---

## Adding new content

Any `.md` file added to `Content/Artists/[Century]/`, `Content/Churches/`, or `Content/Codex/` will automatically appear in the app on the next build (the folder is a live reference, not a snapshot).

The file must have a YAML front-matter block with at least a `title:` field:

```yaml
---
title: "Artist Name"
subtitle: "Short description"
dates: "c. 1200 – c. 1260"
---

Body prose begins here…
```

---

## Roadmap ideas

- **Images** — add the `images/` folder as another folder reference and display artwork thumbnails on detail pages
- **Related entries** — parse the `links:` list in the YAML front-matter and show cross-reference buttons
- **Bookmarks** — persist favourite entries with `@AppStorage` or SwiftData
- **iPad split view** — replace `NavigationStack` inside each tab with `NavigationSplitView` for a master-detail layout on large screens
- **Export / share** — share sheet for copying the entry text
