import SwiftUI

struct CodicesView: View {
    @EnvironmentObject private var loader: ContentLoader

    var body: some View {
        List(loader.codices) { entry in
            NavigationLink(destination: EntryDetailView(entry: entry)) {
                EntryRowView(entry: entry)
            }
        }
        .listStyle(.insetGrouped)
        .navigationTitle("Codices")
    }
}
