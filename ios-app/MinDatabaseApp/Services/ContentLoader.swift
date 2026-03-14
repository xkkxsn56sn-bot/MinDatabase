import SwiftUI
import Foundation
import Combine

/// Loads and parses all Markdown content from the app bundle.
///
/// Call `load()` once on app launch. Results are published on the main thread.
class ContentLoader: ObservableObject {

    @Published var artists:  [Entry] = []
    @Published var churches: [Entry] = []
    @Published var codices:  [Entry] = []
    @Published var isLoaded: Bool = false

    // MARK: - Derived

    var artistsByCentury: [String: [Entry]] {
        Dictionary(grouping: artists, by: { $0.century ?? "Unknown" })
    }

    var sortedCenturies: [String] {
        artistsByCentury.keys.sorted { ContentLoader.centuryOrder($0) < ContentLoader.centuryOrder($1) }
    }

    // MARK: - Loading

    func load() {
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            guard let self else { return }
            let a = self.loadEntries(subpath: "Content/Artists",  category: .artists)
            let c = self.loadEntries(subpath: "Content/Churches", category: .churches)
            let d = self.loadEntries(subpath: "Content/Codex",    category: .codices)
            DispatchQueue.main.async {
                self.artists  = a
                self.churches = c
                self.codices  = d
                self.isLoaded = true
            }
        }
    }

    // MARK: - Private helpers

    private func loadEntries(subpath: String, category: EntryCategory) -> [Entry] {
        guard let bundleURL = Bundle.main.resourceURL else { return [] }
        let folderURL = bundleURL.appendingPathComponent(subpath)

        // Optional: log existence and root contents for debugging
        let exists = FileManager.default.fileExists(atPath: folderURL.path)
        print("[ContentLoader] \(exists ? "✅" : "❌") \(subpath) | root: \((try? FileManager.default.contentsOfDirectory(atPath: bundleURL.path))?.sorted() ?? [])")

        return scanDirectory(folderURL, category: category, inheritedCentury: nil)
    }

    private func scanDirectory(
        _ url: URL,
        category: EntryCategory,
        inheritedCentury: String?
    ) -> [Entry] {
        guard let contents = try? FileManager.default.contentsOfDirectory(
            at: url,
            includingPropertiesForKeys: [.isDirectoryKey],
            options: .skipsHiddenFiles
        ) else { return [] }

        var entries: [Entry] = []

        for itemURL in contents {
            let isDir = (try? itemURL.resourceValues(forKeys: [.isDirectoryKey]).isDirectory) ?? false
            if isDir {
                // Subdirectory name is the century label for artists
                let century = category == .artists ? itemURL.lastPathComponent : nil
                let sub = scanDirectory(itemURL, category: category, inheritedCentury: century)
                entries.append(contentsOf: sub)
            } else if itemURL.pathExtension.lowercased() == "md" {
                guard let text = try? String(contentsOf: itemURL, encoding: .utf8) else { continue }
                let entry = Self.parseEntry(
                    text: text,
                    filePath: itemURL,
                    category: category,
                    century: inheritedCentury
                )
                entries.append(entry)
            }
        }

        return entries.sorted { $0.title.localizedCompare($1.title) == .orderedAscending }
    }

    // MARK: - Parsing

    static func parseEntry(
        text: String,
        filePath: URL,
        category: EntryCategory,
        century: String?
    ) -> Entry {
        let (metadata, body) = parseFrontmatter(text)
        let title    = metadata["title"]    ?? filePath.deletingPathExtension().lastPathComponent
        let subtitle = metadata["subtitle"] ?? metadata["role"] ?? ""
        let dates    = metadata["dates"]    ?? ""
        return Entry(
            title:    title,
            subtitle: subtitle,
            dates:    dates,
            bodyText: body,
            category: category,
            century:  century
        )
    }

    /// Splits a Markdown file into YAML front-matter key-value pairs and the body text.
    ///
    /// Only top-level (non-indented) `key: value` lines are parsed; nested YAML structures
    /// are intentionally ignored because the body prose already contains all readable content.
    static func parseFrontmatter(_ text: String) -> (metadata: [String: String], body: String) {
        let lines = text.components(separatedBy: "\n")
        guard lines.first?.trimmingCharacters(in: .whitespaces) == "---" else {
            return ([:], text)
        }

        var metadata: [String: String] = [:]
        var bodyStart = lines.count

        for i in 1..<lines.count {
            let line = lines[i]
            if line.trimmingCharacters(in: .whitespaces) == "---" {
                bodyStart = i + 1
                break
            }
            // Skip indented (nested) lines
            guard !line.hasPrefix(" "), !line.hasPrefix("\t") else { continue }
            guard let colonIndex = line.firstIndex(of: ":") else { continue }

            let key = String(line[..<colonIndex]).trimmingCharacters(in: .whitespaces)
            var value = String(line[line.index(after: colonIndex)...]).trimmingCharacters(in: .whitespaces)

            // Strip surrounding single or double quotes
            if value.count >= 2,
               (value.hasPrefix("\"") && value.hasSuffix("\"")) ||
               (value.hasPrefix("'")  && value.hasSuffix("'")) {
                value = String(value.dropFirst().dropLast())
            }

            if !key.isEmpty, !value.isEmpty {
                metadata[key] = value
            }
        }

        let body: String
        if bodyStart < lines.count {
            body = lines[bodyStart...].joined(separator: "\n")
                .trimmingCharacters(in: .whitespacesAndNewlines)
        } else {
            body = ""
        }

        return (metadata, body)
    }

    // MARK: - Century sort order

    static func centuryOrder(_ century: String) -> Int {
        switch century {
        case "VII century":      return  7
        case "VIII century":     return  8
        case "IX century":       return  9
        case "X century":        return 10
        case "XI century":       return 11
        case "XII century":      return 12
        case "XIII century":     return 13
        case "XIII-XIV century": return 14
        case "XIV century":      return 15
        default:                 return 99
        }
    }
}

