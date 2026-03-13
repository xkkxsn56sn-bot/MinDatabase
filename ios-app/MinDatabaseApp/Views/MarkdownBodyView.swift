import SwiftUI

// MARK: - Block model

private struct MarkdownBlock: Identifiable {
    enum Kind { case h2, h3, body }
    let id = UUID()
    let kind: Kind
    let content: String
}

// MARK: - View

/// Renders the prose body of a Markdown entry.
///
/// Handles `## H2` and `### H3` headings as styled `Text` views and interprets
/// inline Markdown (bold, italic, links) in body paragraphs via `AttributedString`.
struct MarkdownBodyView: View {
    let text: String

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            ForEach(blocks) { block in
                switch block.kind {
                case .h2:
                    Text(block.content)
                        .font(.title2.weight(.semibold))
                        .foregroundStyle(.primary)
                        .padding(.top, 12)

                case .h3:
                    Text(block.content)
                        .font(.headline)
                        .foregroundStyle(.primary)
                        .padding(.top, 6)

                case .body:
                    bodyText(for: block.content)
                        .font(.body)
                        .lineSpacing(5)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
        }
    }

    // MARK: - Body rendering

    @ViewBuilder
    private func bodyText(for content: String) -> some View {
        if let attributed = try? AttributedString(
            markdown: content,
            options: AttributedString.MarkdownParsingOptions(
                interpretedSyntax: .inlinesOnlyPreservingWhitespace
            )
        ) {
            Text(attributed)
        } else {
            Text(content)
        }
    }

    // MARK: - Block parsing

    private var blocks: [MarkdownBlock] {
        var result: [MarkdownBlock] = []
        var pendingLines: [String] = []

        func flushParagraph() {
            let text = pendingLines.joined(separator: " ")
                .trimmingCharacters(in: .whitespaces)
            if !text.isEmpty {
                result.append(MarkdownBlock(kind: .body, content: text))
            }
            pendingLines = []
        }

        for line in text.components(separatedBy: "\n") {
            if line.hasPrefix("## ") {
                flushParagraph()
                let heading = String(line.dropFirst(3)).trimmingCharacters(in: .whitespaces)
                result.append(MarkdownBlock(kind: .h2, content: heading))
            } else if line.hasPrefix("### ") {
                flushParagraph()
                let heading = String(line.dropFirst(4)).trimmingCharacters(in: .whitespaces)
                result.append(MarkdownBlock(kind: .h3, content: heading))
            } else if line.trimmingCharacters(in: .whitespaces).isEmpty {
                flushParagraph()
            } else {
                pendingLines.append(line)
            }
        }
        flushParagraph()

        return result
    }
}
