import SwiftUI

struct EntryDetailView: View {
    let entry: Entry

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {

                // ── Header ────────────────────────────────────────────────
                VStack(alignment: .leading, spacing: 8) {
                    // Category pill
                    Label(entry.category.rawValue, systemImage: entry.category.systemImage)
                        .font(.caption.weight(.medium))
                        .foregroundStyle(.white)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 4)
                        .background(Color.accentColor, in: Capsule())

                    Text(entry.title)
                        .font(.largeTitle.weight(.bold))
                        .fixedSize(horizontal: false, vertical: true)

                    if !entry.subtitle.isEmpty {
                        Text(entry.subtitle)
                            .font(.title3)
                            .foregroundStyle(.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                    }

                    if !entry.dates.isEmpty {
                        Text(entry.dates)
                            .font(.subheadline)
                            .foregroundStyle(.tertiary)
                    }
                }
                .padding()

                Divider()
                    .padding(.horizontal)

                // ── Body ──────────────────────────────────────────────────
                if entry.bodyText.isEmpty {
                    Text("No content available.")
                        .font(.body)
                        .foregroundStyle(.secondary)
                        .padding()
                } else {
                    MarkdownBodyView(text: entry.bodyText)
                        .padding()
                }
            }
        }
        .navigationTitle(entry.title)
        .navigationBarTitleDisplayMode(.inline)
    }
}
