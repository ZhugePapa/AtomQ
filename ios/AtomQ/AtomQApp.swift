import SwiftUI

// MARK: - AppTab & HomeViewModel

enum AppTab: String {
    case study
    case stats
    case profile
}

@MainActor
final class HomeViewModel: ObservableObject {
    @Published var selectedTab: AppTab = .study
    @Published var showingKnowledgeCardStudy = false
    let studyViewModel = KnowledgeCardStudyViewModel()
    private var contentCacheObserver: NSObjectProtocol?

    init() {
        contentCacheObserver = NotificationCenter.default.addObserver(
            forName: ContentPackageRemoteStore.didClearLocalCacheNotification,
            object: nil,
            queue: .main
        ) { [weak self] _ in
            Task { @MainActor in
                await self?.studyViewModel.reloadAfterContentCacheClear()
            }
        }
    }

    deinit {
        if let contentCacheObserver {
            NotificationCenter.default.removeObserver(contentCacheObserver)
        }
    }

    func openKnowledgeCardStudy() {
        withAnimation(.easeInOut(duration: 0.3)) { showingKnowledgeCardStudy = true }
    }

    func closeKnowledgeCardStudy() {
        withAnimation(.easeInOut(duration: 0.3)) { showingKnowledgeCardStudy = false }
    }
}

// MARK: - App

@main
struct AtomQApp: App {
    @StateObject private var viewModel = HomeViewModel()
    @AppStorage("atomq.darkMode.enabled") private var isDarkMode = false

    var body: some Scene {
        WindowGroup {
            HomePageView(viewModel: viewModel)
                .background(Token.bgCanvas)
                .preferredColorScheme(isDarkMode ? .dark : .light)
        }
    }
}
