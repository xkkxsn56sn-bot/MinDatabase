import SwiftUI

struct ArtistsView: View {
    @EnvironmentObject private var loader: ContentLoader

    var body: some View {
        List {
            ForEach(loader.sortedCenturies, id: \.self) { century in
                Section(century) {
                    ForEach(loader.artistsByCentury[century] ?? []) { entry in
                        NavigationLink(destination: EntryDetailView(entry: entry)) {
                            EntryRowView(entry: entry)
                        }
                    }
                }
            }
        }
        .listStyle(.insetGrouped)
        .navigationTitle("Artists")
    }
}
