import SwiftUI

struct SearchView: View {
    @EnvironmentObject private var loader: ContentLoader
    @State private var query = ""

    private var allEntries: [Entry] {
        loader.artists + loader.churches + loader.codices
    }

    private var results: [Entry] {
        guard !query.isEmpty else { return [] }
        let q = query.lowercased()
        return allEntries.filter {
            $0.title.lowercased().contains(q) ||
            $0.subtitle.lowercased().contains(q) ||
            $0.bodyText.lowercased().contains(q)
        }
        .sorted { $0.title.localizedCompare($1.title) == .orderedAscending }
    }

    var body: some View {
        List {
            if query.isEmpty {
                emptyPrompt(
                    icon: "magnifyingglass",
                    title: "Search MinDatabase",
                    message: "Enter a name, title, or keyword to search across all content."
                )
                .listRowBackground(Color.clear)
                .listRowSeparator(.hidden)
            } else if results.isEmpty {
                emptyPrompt(
                    icon: "magnifyingglass.circle",
                    title: "No Results",
                    message: "Nothing found for \"\(query)\"."
                )
                .listRowBackground(Color.clear)
                .listRowSeparator(.hidden)
            } else {
                ForEach(results) { entry in
                    NavigationLink(destination: EntryDetailView(entry: entry)) {
                        VStack(alignment: .leading, spacing: 3) {
                            Text(entry.title)
                                .font(.headline)
                            HStack(spacing: 6) {
                                Label(entry.category.rawValue,
                                      systemImage: entry.category.systemImage)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                if let century = entry.century {
                                    Text("·")
                                        .foregroundStyle(.tertiary)
                                    Text(century)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                            }
                            if !entry.subtitle.isEmpty {
                                Text(entry.subtitle)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                    .lineLimit(2)
                            }
                        }
                        .padding(.vertical, 2)
                    }
                }
            }
        }
        .listStyle(.insetGrouped)
        .searchable(text: $query, prompt: "Artists, churches, codices…")
        .navigationTitle("Search")
    }

    // MARK: - Private

    @ViewBuilder
    private func emptyPrompt(icon: String, title: String, message: String) -> some View {
        VStack(spacing: 14) {
            Image(systemName: icon)
                .font(.system(size: 48))
                .foregroundStyle(.tertiary)
            Text(title)
                .font(.title3.weight(.semibold))
            Text(message)
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 60)
    }
}
