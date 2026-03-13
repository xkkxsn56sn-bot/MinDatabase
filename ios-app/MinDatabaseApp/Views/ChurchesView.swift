import SwiftUI

struct ChurchesView: View {
    @EnvironmentObject private var loader: ContentLoader

    var body: some View {
        List(loader.churches) { entry in
            NavigationLink(destination: EntryDetailView(entry: entry)) {
                EntryRowView(entry: entry)
            }
        }
        .listStyle(.insetGrouped)
        .navigationTitle("Churches")
    }
}
