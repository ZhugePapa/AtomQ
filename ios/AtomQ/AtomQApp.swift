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
    var studyNavDirection: StudyNavDirection = .push

    enum StudyNavDirection { case push, pop }

    var studyPageTransition: AnyTransition {
        switch studyNavDirection {
        case .push:
            return .asymmetric(insertion: .move(edge: .trailing), removal: .move(edge: .leading))
        case .pop:
            return .asymmetric(insertion: .move(edge: .leading), removal: .move(edge: .trailing))
        }
    }

    func openKnowledgeCardStudy() {
        studyNavDirection = .push
        withAnimation(.easeInOut(duration: 0.25)) { showingKnowledgeCardStudy = true }
    }

    func closeKnowledgeCardStudy() {
        studyNavDirection = .pop
        withAnimation(.easeInOut(duration: 0.25)) { showingKnowledgeCardStudy = false }
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