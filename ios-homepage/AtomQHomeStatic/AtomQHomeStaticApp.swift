import SwiftUI

@main
struct AtomQHomeStaticApp: App {
    @State private var selectedTab: AppTab = .study
    @AppStorage("atomq.darkMode.enabled") private var isDarkMode = false

    var body: some Scene {
        WindowGroup {
            HomePageView(selectedTab: $selectedTab, isDarkMode: $isDarkMode)
                .background(Token.bgCanvas)
                .preferredColorScheme(isDarkMode ? .dark : .light)
        }
    }
}
