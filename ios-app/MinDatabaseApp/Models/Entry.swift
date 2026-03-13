import Foundation

// MARK: - Category

enum EntryCategory: String, CaseIterable, Identifiable {
    case artists = "Artists"
    case churches = "Churches"
    case codices = "Codices"

    var id: String { rawValue }

    var systemImage: String {
        switch self {
        case .artists:  return "person.crop.rectangle.stack"
        case .churches: return "building.columns"
        case .codices:  return "book.closed"
        }
    }
}

// MARK: - Entry

struct Entry: Identifiable, Hashable {
    let id: UUID
    let title: String
    let subtitle: String
    let dates: String
    let bodyText: String
    let category: EntryCategory
    /// Non-nil only for artists; contains the century folder name (e.g. "XIII century").
    let century: String?

    init(
        title: String,
        subtitle: String = "",
        dates: String = "",
        bodyText: String = "",
        category: EntryCategory,
        century: String? = nil
    ) {
        self.id       = UUID()
        self.title    = title
        self.subtitle = subtitle
        self.dates    = dates
        self.bodyText = bodyText
        self.category = category
        self.century  = century
    }

    static func == (lhs: Entry, rhs: Entry) -> Bool { lhs.id == rhs.id }
    func hash(into hasher: inout Hasher) { hasher.combine(id) }
}
