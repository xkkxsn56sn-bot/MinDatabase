import SwiftUI

struct ContentView: View {
    @StateObject private var loader = ContentLoader()

    var body: some View {
        Group {
            if loader.isLoaded {
                mainTabs
            } else {
                loadingScreen
            }
        }
        .environmentObject(loader)
        .onAppear { loader.load() }
    }

    // MARK: - Tabs

    private var mainTabs: some View {
        TabView {
            NavigationStack {
                ArtistsView()
            }
            .tabItem {
                Label("Artists", systemImage: EntryCategory.artists.systemImage)
            }

            NavigationStack {
                ChurchesView()
            }
            .tabItem {
                Label("Churches", systemImage: EntryCategory.churches.systemImage)
            }

            NavigationStack {
                CodicesView()
            }
            .tabItem {
                Label("Codices", systemImage: EntryCategory.codices.systemImage)
            }

            NavigationStack {
                SearchView()
            }
            .tabItem {
                Label("Search", systemImage: "magnifyingglass")
            }
        }
    }

    // MARK: - Loading screen

    private var loadingScreen: some View {
        VStack(spacing: 20) {
            Image(systemName: "book.closed")
                .font(.system(size: 56))
                .foregroundStyle(.secondary)
            Text("MinDatabase")
                .font(.largeTitle.weight(.bold))
            Text("Loading content…")
                .font(.subheadline)
                .foregroundStyle(.secondary)
            ProgressView()
                .padding(.top, 4)
        }
    }
}
