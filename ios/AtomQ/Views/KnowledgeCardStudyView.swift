import SwiftUI

// MARK: - KnowledgeCardStudyViewModel

@MainActor
final class KnowledgeCardStudyViewModel: ObservableObject {
    @Published var pageData = KnowledgeCardStudyContent(pointID: "demo", chapterID: "ch_01", sectionID: "sec_01", headerTitle: "1.1 信息与信息化", knowledgeMarkdown: "", keyPointsMarkdown: nil, mnemonicsMarkdown: nil, chipTitle: "知识卡片")
    @Published var sectionCards: [KnowledgeCardStudyContent] = []
    @Published var currentCardIndex: Int = 0
    @Published var directoryChapters: [KnowledgeDirectoryChapter] = []
    @Published var selectedChapterID: String = "ch_01"
    @Published var selectedSectionID: String = "sec_01"
    @Published var isDirectoryPresented = false
    @Published var loadErrorMessage: String?
    @Published var focusHighlightVisible = true
    @Published var isCurrentCardMastered = false
    @Published var shouldRenderAdjacentCards = false
    var isHorizontalPagingActive = false
    var isVerticalScrollActive = false
    var hasLoadedInitialData = false
    private var isLoadingInitialData = false
    private var hasRefreshedRemoteContent = false
    let topBarHeight: CGFloat = 56
    var onBack: (() -> Void)?

    enum CardSelectionAnchor { case first, firstUnmastered, last }
    enum KnowledgeBarState { case active, completed, pending }

    typealias LoadedStudyPayload = (chapters: [KnowledgeDirectoryChapter], chapterID: String, sectionID: String, cards: [KnowledgeCardStudyContent])

    struct AdjacentSectionTarget {
        let chapterID: String
        let sectionID: String
        let cards: [KnowledgeCardStudyContent]
        let cardIndex: Int

        var card: KnowledgeCardStudyContent {
            cards[cardIndex]
        }
    }

    var resolvedBackAction: () -> Void {
        if let onBack = onBack { return onBack }
        return {}
    }

    func presentDirectory() {
        isDirectoryPresented = true
        Task {
            await refreshDirectoryTreeForSheet()
        }
    }

    private func refreshDirectoryTreeForSheet() async {
        guard ContentPackageRemoteStore.canRefreshPublicContent else { return }

        do {
            try await ContentPackageRemoteStore.refreshDirectoryIndexRequired()
            KnowledgeCardDataStore.invalidateCache()
            let chapters = try await Task.detached(priority: .userInitiated) {
                try KnowledgeCardDataStore.loadDirectoryTree()
            }.value
            directoryChapters = chapters
        } catch {
            print("[AtomQ][StudyData] directory refresh failed: \(error.localizedDescription)")
            loadErrorMessage = error.localizedDescription
        }
    }

    func selectDirectorySection(chapter: KnowledgeDirectoryChapter, section: KnowledgeDirectorySection) {
        isDirectoryPresented = false
        guard chapter.id != selectedChapterID || section.id != selectedSectionID else { return }
        do { try loadSectionCards(chapterID: chapter.id, sectionID: section.id, anchor: .firstUnmastered) }
        catch { loadErrorMessage = error.localizedDescription }
    }

    func loadSectionCards(chapterID: String, sectionID: String, anchor: CardSelectionAnchor) throws {
        let cards = try KnowledgeCardDataStore.loadSectionCards(chapterID: chapterID, sectionID: sectionID)
        guard !cards.isEmpty else { throw NSError(domain: "KCSVM", code: 404) }
        sectionCards = cards
        selectedChapterID = chapterID
        selectedSectionID = sectionID
        switch anchor {
        case .first: currentCardIndex = 0
        case .last: currentCardIndex = cards.count - 1
        case .firstUnmastered:
            if let idx = cards.firstIndex(where: { !GuestUserLocalStore.isPointMastered($0.pointID) }) { currentCardIndex = idx }
            else { currentCardIndex = 0 }
        }
        syncCurrentCardFromIndex()
    }

    func syncCurrentCardFromIndex() {
        guard !sectionCards.isEmpty else { return }
        currentCardIndex = max(0, min(currentCardIndex, sectionCards.count - 1))
        pageData = sectionCards[currentCardIndex]
        syncMasteredStateForCurrentCard()
    }

    var knowledgeBarStates: [KnowledgeBarState] {
        guard !sectionCards.isEmpty else { return [.pending] }
        return sectionCards.enumerated().map { idx, card in
            if idx == currentCardIndex { return .active }
            if GuestUserLocalStore.isPointMastered(card.pointID) { return .completed }
            return .pending
        }
    }

    func orderedSections() -> [(chapter: KnowledgeDirectoryChapter, section: KnowledgeDirectorySection)] {
        directoryChapters.sorted(by: { $0.sortNo < $1.sortNo }).flatMap { chapter in
            chapter.sections.sorted(by: { $0.sortNo < $1.sortNo }).map { (chapter: chapter, section: $0) }
        }
    }

    func currentSectionPosition() -> Int? {
        orderedSections().firstIndex { $0.chapter.id == selectedChapterID && $0.section.id == selectedSectionID }
    }

    func navigateToAdjacentSection(offset: Int, anchor: CardSelectionAnchor) {
        do {
            guard let target = try adjacentSectionTarget(offset: offset, anchor: anchor) else { return }
            applyAdjacentSectionTarget(target)
        }
        catch { loadErrorMessage = error.localizedDescription }
    }

    func adjacentSectionTarget(offset: Int, anchor: CardSelectionAnchor) throws -> AdjacentSectionTarget? {
        let sections = orderedSections()
        guard let index = currentSectionPosition() else { return nil }
        let nextIndex = index + offset
        guard sections.indices.contains(nextIndex) else { return nil }
        let target = sections[nextIndex]
        let cards = try KnowledgeCardDataStore.loadSectionCards(chapterID: target.chapter.id, sectionID: target.section.id)
        guard !cards.isEmpty else { return nil }

        let cardIndex: Int
        switch anchor {
        case .first:
            cardIndex = 0
        case .last:
            cardIndex = cards.count - 1
        case .firstUnmastered:
            cardIndex = cards.firstIndex(where: { !GuestUserLocalStore.isPointMastered($0.pointID) }) ?? 0
        }

        return AdjacentSectionTarget(
            chapterID: target.chapter.id,
            sectionID: target.section.id,
            cards: cards,
            cardIndex: cardIndex
        )
    }

    func adjacentSectionTargetIfAvailable(offset: Int, anchor: CardSelectionAnchor) -> AdjacentSectionTarget? {
        try? adjacentSectionTarget(offset: offset, anchor: anchor)
    }

    func applyAdjacentSectionTarget(_ target: AdjacentSectionTarget) {
        sectionCards = target.cards
        selectedChapterID = target.chapterID
        selectedSectionID = target.sectionID
        currentCardIndex = target.cardIndex
        syncCurrentCardFromIndex()
    }

    func goForwardCard() {
        guard !sectionCards.isEmpty else { return }
        if currentCardIndex + 1 < sectionCards.count { currentCardIndex += 1; syncCurrentCardFromIndex() }
        else { navigateToAdjacentSection(offset: 1, anchor: .first) }
    }

    func goBackwardCard() {
        guard !sectionCards.isEmpty else { return }
        if currentCardIndex > 0 { currentCardIndex -= 1; syncCurrentCardFromIndex() }
        else { navigateToAdjacentSection(offset: -1, anchor: .last) }
    }

    func hasNextCardGlobally() -> Bool {
        if currentCardIndex + 1 < sectionCards.count { return true }
        guard let pos = currentSectionPosition() else { return false }
        return pos + 1 < orderedSections().count
    }

    func hasPreviousCardGlobally() -> Bool {
        if currentCardIndex > 0 { return true }
        guard let pos = currentSectionPosition() else { return false }
        return pos - 1 >= 0
    }

    func dampedInteractiveOffset(_ rawOffset: CGFloat) -> CGFloat {
        if rawOffset > 0, !hasPreviousCardGlobally() { return rawOffset * 0.2 }
        if rawOffset < 0, !hasNextCardGlobally() { return rawOffset * 0.2 }
        return rawOffset
    }

    func visibleCardIndices() -> [Int] {
        guard !sectionCards.isEmpty else { return [] }
        if !shouldRenderAdjacentCards { return [currentCardIndex] }
        let lower = max(0, currentCardIndex - 1)
        let upper = min(sectionCards.count - 1, currentCardIndex + 1)
        return Array(lower...upper)
    }

    func goToNextUnmasteredCard() {
        guard !sectionCards.isEmpty else { return }
        if currentCardIndex + 1 < sectionCards.count {
            if let idx = sectionCards[(currentCardIndex+1)...].firstIndex(where: { !GuestUserLocalStore.isPointMastered($0.pointID) }) {
                currentCardIndex = idx; syncCurrentCardFromIndex(); return
            }
        }
        let sections = orderedSections()
        guard let pos = currentSectionPosition(), pos + 1 < sections.count else { return }
        for idx in (pos + 1)..<sections.count {
            let target = sections[idx]
            guard let cards = try? KnowledgeCardDataStore.loadSectionCards(chapterID: target.chapter.id, sectionID: target.section.id),
                  let next = cards.firstIndex(where: { !GuestUserLocalStore.isPointMastered($0.pointID) }) else { continue }
            sectionCards = cards; selectedChapterID = target.chapter.id; selectedSectionID = target.section.id
            currentCardIndex = next; syncCurrentCardFromIndex(); return
        }
    }

    func syncMasteredStateForCurrentCard() {
        isCurrentCardMastered = GuestUserLocalStore.isPointMastered(pageData.pointID)
    }

    func toggleCurrentCardMastered() {
        let nextValue = !isCurrentCardMastered
        GuestUserLocalStore.setPointMastered(pageData.pointID, mastered: nextValue)
        isCurrentCardMastered = nextValue
        if nextValue { withAnimation(.easeInOut(duration: 0.24)) { goToNextUnmasteredCard() } }
    }

    func loadStudyPayload(fallbackChapterID: String, fallbackSectionID: String) async throws -> LoadedStudyPayload {
        try await Task.detached(priority: .userInitiated) {
            let chapters = try KnowledgeCardDataStore.loadDirectoryTree()
            let cid = chapters.first?.id ?? fallbackChapterID
            let sid = chapters.first?.sections.first?.id ?? fallbackSectionID
            let cards = try KnowledgeCardDataStore.loadSectionCards(chapterID: cid, sectionID: sid)
            return (chapters, cid, sid, cards)
        }.value
    }

    func applyLoadedStudyPayload(_ loaded: LoadedStudyPayload) {
        directoryChapters = loaded.chapters; selectedChapterID = loaded.chapterID; selectedSectionID = loaded.sectionID
        sectionCards = loaded.cards
        if let idx = sectionCards.firstIndex(where: { !GuestUserLocalStore.isPointMastered($0.pointID) }) { currentCardIndex = idx }
        else { currentCardIndex = 0 }
        syncCurrentCardFromIndex()
        loadErrorMessage = nil
    }

    func loadInitialData() async {
        guard !isLoadingInitialData else { return }
        let shouldRefreshBeforeFirstRender = ContentPackageRemoteStore.canRefreshPublicContent
        guard sectionCards.isEmpty || (shouldRefreshBeforeFirstRender && !hasRefreshedRemoteContent) else {
            return
        }
        guard !hasLoadedInitialData || (shouldRefreshBeforeFirstRender && !hasRefreshedRemoteContent) else {
            return
        }

        isLoadingInitialData = true
        defer { isLoadingInitialData = false }
        hasLoadedInitialData = true
        shouldRenderAdjacentCards = false
        let prevCID = selectedChapterID, prevSID = selectedSectionID
        var initialRemoteError: Error?

        if shouldRefreshBeforeFirstRender {
            do {
                try await Task.detached(priority: .userInitiated) {
                    try ContentPackageRemoteStore.resetIncompatibleLocalCacheIfNeeded()
                }.value
                print("[AtomQ][StudyData] refreshing remote section before first render")
                try await ContentPackageRemoteStore.refreshContentRequired(chapterID: prevCID, sectionID: prevSID)
                hasRefreshedRemoteContent = true
                KnowledgeCardDataStore.invalidateCache()
                print("[AtomQ][StudyData] initial remote section refresh finished")
            } catch {
                initialRemoteError = error
                print("[AtomQ][StudyData] initial remote section refresh failed: \(error.localizedDescription)")
            }
        }

        do {
            let local = try await loadStudyPayload(fallbackChapterID: prevCID, fallbackSectionID: prevSID)
            applyLoadedStudyPayload(local)
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.08) { [weak self] in
                self?.shouldRenderAdjacentCards = true
            }
        } catch {
            let localLoadError = error
            print("[AtomQ][StudyData] local load failed: \(localLoadError.localizedDescription)")

            if !shouldRefreshBeforeFirstRender {
                do {
                    print("[AtomQ][StudyData] local cache exists but load failed, refreshing remote content")
                    try await ContentPackageRemoteStore.refreshFreeContentRequired(chapterID: prevCID, sectionID: prevSID)
                    KnowledgeCardDataStore.invalidateCache()
                    let refreshed = try await loadStudyPayload(fallbackChapterID: prevCID, fallbackSectionID: prevSID)
                    applyLoadedStudyPayload(refreshed)
                    shouldRenderAdjacentCards = true
                    return
                } catch {
                    initialRemoteError = error
                    print("[AtomQ][StudyData] recovery remote refresh/load failed: \(error.localizedDescription)")
                }
            }

            loadErrorMessage = makeLoadErrorMessage(remoteError: initialRemoteError, localError: localLoadError)
            hasLoadedInitialData = false
            return
        }

        Task.detached(priority: .background) { [weak self] in
            do {
                print("[AtomQ][StudyData] background directory refresh start")
                try await ContentPackageRemoteStore.refreshDirectoryIndexRequired()
                print("[AtomQ][StudyData] background full content refresh start")
                try await ContentPackageRemoteStore.refreshFreeContentRequired(chapterID: prevCID, sectionID: prevSID)
                KnowledgeCardDataStore.invalidateCache()
                guard let self else { return }
                if let refreshed = try? await self.loadStudyPayload(fallbackChapterID: prevCID, fallbackSectionID: prevSID) {
                    await MainActor.run {
                        self.applyLoadedStudyPayload(refreshed)
                        self.shouldRenderAdjacentCards = true
                    }
                }
                print("[AtomQ][StudyData] background full content refresh finished")
            } catch {
                print("[AtomQ][StudyData] background full content refresh failed: \(error.localizedDescription)")
            }
        }
    }

    private func makeLoadErrorMessage(remoteError: Error?, localError: Error) -> String {
        var message = "未找到学习数据。"
        if let remoteError {
            message += "\n\n远程刷新失败：\(remoteError.localizedDescription)"
        }
        message += "\n\n本地读取失败：\(localError.localizedDescription)"
        return message
    }

    func reloadAfterContentCacheClear() async {
        sectionCards = []
        directoryChapters = []
        currentCardIndex = 0
        shouldRenderAdjacentCards = false
        hasLoadedInitialData = false
        hasRefreshedRemoteContent = false
        KnowledgeCardDataStore.invalidateCache()
        await loadInitialData()
    }
}

// MARK: - KnowledgeCardStudyView

struct KnowledgeCardStudyView: View {
    @ObservedObject var viewModel: KnowledgeCardStudyViewModel
    var onBack: (() -> Void)? = nil

    @GestureState private var interactiveCardOffsetX: CGFloat = 0
    @State private var renderedCardIndices: [Int] = []
    @State private var renderedCardRefreshRevision = 0
    @State private var settlingCardOffsetX: CGFloat = 0
    private let topBarHeight: CGFloat = 56
    private let edgeSwipeActivationWidth: CGFloat = 24
    private let edgeSwipeDistanceThreshold: CGFloat = 64
    private let edgeSwipePredictedThreshold: CGFloat = 96
    private let cardSwipeAnimation = Animation.spring(duration: 0.30, bounce: 0.0, blendDuration: 0.04)

    init(viewModel: KnowledgeCardStudyViewModel, onBack: (() -> Void)? = nil) {
        self.viewModel = viewModel
        self.onBack = onBack
        viewModel.onBack = onBack
    }

    private var resolvedBackAction: () -> Void {
        if let onBack = onBack {
            return onBack
        }
        return { /* handled by parent */ }
    }

    // MARK: - Card swipe gesture (must stay in View for @GestureState)

    private func cardSwipeGesture(pageWidth: CGFloat) -> some Gesture {
        let dynamicDistanceThreshold = max(56, min(96, pageWidth * 0.18))
        let dynamicPredictedThreshold = max(84, min(140, pageWidth * 0.24))
        let activationDistance: CGFloat = 18

        return DragGesture(minimumDistance: 8)
            .onChanged { value in
                let horizontal = abs(value.translation.width)
                let vertical = abs(value.translation.height)
                if isEdgeBackSwipeCandidate(value) { return }
                guard horizontal > vertical + 8, horizontal > activationDistance, !viewModel.isVerticalScrollActive else { return }
                if !viewModel.isHorizontalPagingActive {
                    viewModel.isHorizontalPagingActive = true
                }
            }
            .updating($interactiveCardOffsetX) { value, state, transaction in
                let horizontal = value.translation.width
                let vertical = value.translation.height
                if isEdgeBackSwipeCandidate(value) { return }
                guard
                    !viewModel.isVerticalScrollActive,
                    abs(horizontal) > max(abs(vertical) + 8, activationDistance)
                else { return }
                transaction.disablesAnimations = true
                state = viewModel.dampedInteractiveOffset(horizontal)
            }
            .onEnded { value in
                defer { viewModel.isHorizontalPagingActive = false }
                let horizontal = value.translation.width
                let vertical = value.translation.height
                if isEdgeBackSwipeCandidate(value) { return }
                guard
                    !viewModel.isVerticalScrollActive,
                    abs(horizontal) > max(abs(vertical) + 8, activationDistance)
                else { return }

                let predicted = value.predictedEndTranslation.width
                let projectedExtra = predicted - horizontal

                let movedFarEnough = abs(horizontal) >= dynamicDistanceThreshold
                let isQuickFlick = abs(projectedExtra) >= 36 || abs(predicted) >= dynamicPredictedThreshold

                guard movedFarEnough || isQuickFlick else {
                    return
                }

                let resolved = abs(predicted) > abs(horizontal) ? predicted : horizontal
                if resolved < 0 {
                    if viewModel.currentCardIndex + 1 >= viewModel.sectionCards.count {
                        do {
                            guard let target = try viewModel.adjacentSectionTarget(offset: 1, anchor: .first) else { return }
                            performBoundarySectionTransition(
                                target: target,
                                direction: 1,
                                pageWidth: pageWidth,
                                startingOffset: viewModel.dampedInteractiveOffset(horizontal)
                            )
                        } catch {
                            viewModel.loadErrorMessage = error.localizedDescription
                        }
                        return
                    }
                    withAnimation(cardSwipeAnimation) {
                        viewModel.goForwardCard()
                    }
                } else {
                    if viewModel.currentCardIndex <= 0 {
                        do {
                            guard let target = try viewModel.adjacentSectionTarget(offset: -1, anchor: .last) else { return }
                            performBoundarySectionTransition(
                                target: target,
                                direction: -1,
                                pageWidth: pageWidth,
                                startingOffset: viewModel.dampedInteractiveOffset(horizontal)
                            )
                        } catch {
                            viewModel.loadErrorMessage = error.localizedDescription
                        }
                        return
                    }
                    withAnimation(cardSwipeAnimation) {
                        viewModel.goBackwardCard()
                    }
                }
            }
    }

    private func performBoundarySectionTransition(
        target: KnowledgeCardStudyViewModel.AdjacentSectionTarget,
        direction: Int,
        pageWidth: CGFloat,
        startingOffset: CGFloat
    ) {
        let finalOffset = direction > 0 ? -pageWidth : pageWidth

        var transaction = Transaction()
        transaction.disablesAnimations = true
        withTransaction(transaction) {
            settlingCardOffsetX = startingOffset
        }

        withAnimation(cardSwipeAnimation) {
            settlingCardOffsetX = finalOffset
        }

        renderedCardRefreshRevision += 1
        let revision = renderedCardRefreshRevision
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.34) {
            guard renderedCardRefreshRevision == revision else { return }
            var resetTransaction = Transaction()
            resetTransaction.disablesAnimations = true
            withTransaction(resetTransaction) {
                viewModel.applyAdjacentSectionTarget(target)
                settlingCardOffsetX = 0
                syncRenderedCardWindow(immediate: true)
            }
        }
    }

    private func isEdgeBackSwipeCandidate(_ value: DragGesture.Value) -> Bool {
        value.startLocation.x <= edgeSwipeActivationWidth && value.translation.width > 0
    }

    private var edgeBackSwipeGesture: some Gesture {
        DragGesture(minimumDistance: 10, coordinateSpace: .local)
            .onChanged { value in
                guard isEdgeBackSwipeCandidate(value) else { return }
                let horizontal = value.translation.width
                let vertical = abs(value.translation.height)
                if horizontal > vertical + 8 {
                    viewModel.isHorizontalPagingActive = false
                    viewModel.isVerticalScrollActive = false
                }
            }
            .onEnded { value in
                guard isEdgeBackSwipeCandidate(value) else { return }
                let horizontal = value.translation.width
                let vertical = abs(value.translation.height)
                let predicted = value.predictedEndTranslation.width
                let movedFarEnough = horizontal >= edgeSwipeDistanceThreshold
                let flickedFarEnough = predicted >= edgeSwipePredictedThreshold
                guard horizontal > vertical + 12, movedFarEnough || flickedFarEnough else { return }
                resolvedBackAction()
            }
    }

    private var verticalScrollLockGesture: some Gesture {
        DragGesture(minimumDistance: 4)
            .onChanged { value in
                let horizontal = abs(value.translation.width)
                let vertical = abs(value.translation.height)
                if vertical > horizontal + 2, !viewModel.isHorizontalPagingActive {
                    viewModel.isVerticalScrollActive = true
                }
            }
            .onEnded { _ in
                viewModel.isVerticalScrollActive = false
            }
    }

    // MARK: - Card pages

    private var activeRenderedCardIndices: [Int] {
        let visible = viewModel.visibleCardIndices()
        let candidates = renderedCardIndices.isEmpty ? visible : renderedCardIndices
        return candidates.filter { viewModel.sectionCards.indices.contains($0) }
    }

    private func syncRenderedCardWindow(immediate: Bool = false) {
        let visible = viewModel.visibleCardIndices()
        guard !visible.isEmpty else {
            renderedCardIndices = []
            return
        }

        if immediate || renderedCardIndices.isEmpty {
            renderedCardIndices = visible
            return
        }

        // Keep both the outgoing and incoming cards alive until the page animation finishes.
        renderedCardIndices = Array(Set(renderedCardIndices + visible)).sorted()
        renderedCardRefreshRevision += 1
        let revision = renderedCardRefreshRevision
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.34) {
            guard renderedCardRefreshRevision == revision else { return }
            renderedCardIndices = viewModel.visibleCardIndices()
        }
    }

    @ViewBuilder
    private func cardPagerPages(
        renderedIndices: Set<Int>,
        previousBoundaryTarget: KnowledgeCardStudyViewModel.AdjacentSectionTarget?,
        nextBoundaryTarget: KnowledgeCardStudyViewModel.AdjacentSectionTarget?,
        pageWidth: CGFloat
    ) -> some View {
        if let previousBoundaryTarget {
            cardPage(
                card: previousBoundaryTarget.card,
                isCurrentCard: false,
                pageWidth: pageWidth,
                onToggleCurrentCardMastered: {}
            )
        }

        ForEach(viewModel.sectionCards.indices, id: \.self) { idx in
            if renderedIndices.contains(idx) {
                cardPage(at: idx, pageWidth: pageWidth)
            } else {
                Color.clear
                    .frame(width: pageWidth)
            }
        }

        if let nextBoundaryTarget {
            cardPage(
                card: nextBoundaryTarget.card,
                isCurrentCard: false,
                pageWidth: pageWidth,
                onToggleCurrentCardMastered: {}
            )
        }
    }

    private func cardPage(at idx: Int, pageWidth: CGFloat) -> some View {
        let card = viewModel.sectionCards[idx]
        return cardPage(
            card: card,
            isCurrentCard: idx == viewModel.currentCardIndex,
            pageWidth: pageWidth,
            onToggleCurrentCardMastered: {
                guard idx == viewModel.currentCardIndex else { return }
                viewModel.toggleCurrentCardMastered()
            }
        )
        .allowsHitTesting(idx == viewModel.currentCardIndex)
    }

    private func cardPage(
        card: KnowledgeCardStudyContent,
        isCurrentCard: Bool,
        pageWidth: CGFloat,
        onToggleCurrentCardMastered: @escaping () -> Void
    ) -> some View {
        return VStack(spacing: 0) {
            ZStack(alignment: .bottom) {
                ScrollView(.vertical, showsIndicators: false) {
                    VStack(spacing: 16) {
                        KnowledgeBodyCard(
                            markdown: card.knowledgeMarkdown,
                            focusHighlightVisible: viewModel.focusHighlightVisible
                        )

                        if let keyPoints = card.keyPointsMarkdown {
                            NoteCard(
                                icon: "icon-target-04",
                                iconStrokeColor: Token.fgBrand,
                                iconBackground: Token.fgBrandSubtle,
                                title: "高频考点",
                                titleColor: Token.textBrand,
                                markdown: keyPoints,
                                focusHighlightVisible: viewModel.focusHighlightVisible
                            )
                        }

                        if let mnemonics = card.mnemonicsMarkdown {
                            NoteCard(
                                icon: "icon-stars-03",
                                iconStrokeColor: Token.fgWarning,
                                iconBackground: Token.fgWarningSubtle,
                                title: "记忆口诀",
                                titleColor: Token.textWarning,
                                markdown: mnemonics,
                                focusHighlightVisible: viewModel.focusHighlightVisible
                            )
                        }

                        HStack(spacing: 16) {
                            Text(card.chipTitle)
                                .font(.custom("PingFang SC", size: 14).weight(.medium))
                                .foregroundStyle(Token.textBrand)
                                .padding(.horizontal, 12)
                                .frame(height: 32)
                                .background(Token.fgBrandSubtle)
                                .clipShape(Capsule())

                            Spacer(minLength: 0)

                            SvgIconView(
                                name: "icon-star-01",
                                outerWidth: 24,
                                outerHeight: 24,
                                innerInsets: SvgIconInsets(top: 0.1096, right: 0.1073, bottom: 0.1416, left: 0.1073),
                                imageInsets: SvgIconInsets(top: -0.0556, right: -0.0530, bottom: -0.0556, left: -0.0530),
                                cssVariables: ["stroke-0": Token.fgTertiary]
                            )

                            SvgIconView(
                                name: "icon-dots-horizontal",
                                outerWidth: 24,
                                outerHeight: 24,
                                innerInsets: SvgIconInsets(top: 0.4583, right: 0.1667, bottom: 0.4583, left: 0.1667),
                                imageInsets: SvgIconInsets(top: -0.5000, right: -0.0625, bottom: -0.5000, left: -0.0625),
                                cssVariables: ["stroke-0": Token.fgTertiary]
                            )
                        }
                    }
                    .padding(.horizontal, 20)
                    .padding(.top, 8)
                    .padding(.bottom, 64)
                }
                .scrollDisabled(viewModel.isHorizontalPagingActive)
                .simultaneousGesture(verticalScrollLockGesture)

                LinearGradient(
                    stops: [
                        .init(color: Token.componentsAlpha0, location: 0.03125),
                        .init(color: Token.componentsAlpha100, location: 0.796875),
                    ],
                    startPoint: .top,
                    endPoint: .bottom
                )
                .frame(height: 96)
                .frame(maxWidth: .infinity, alignment: .bottom)
                .allowsHitTesting(false)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)

            BottomActions(
                focusHighlightVisible: $viewModel.focusHighlightVisible,
                isCurrentCardMastered: isCurrentCard ? viewModel.isCurrentCardMastered : GuestUserLocalStore.isPointMastered(card.pointID),
                onToggleCurrentCardMastered: onToggleCurrentCardMastered
            )
        }
        .frame(width: pageWidth)
        .contentShape(Rectangle())
    }

    // MARK: - Body

    var body: some View {
        ZStack {
            Token.bgCanvas
                .ignoresSafeArea()

            VStack(spacing: 0) {
                ProgressHeaderView(states: viewModel.knowledgeBarStates)
                    .padding(.horizontal, 20)
                    .padding(.top, 8)
                    .padding(.bottom, 8)

                TopActionBar(
                    title: viewModel.pageData.headerTitle,
                    onBack: resolvedBackAction,
                    onOpenCatalog: { viewModel.presentDirectory() }
                )
                .frame(height: topBarHeight)

                GeometryReader { viewport in
                    let pageWidth = viewport.size.width
                    let renderedIndices = Set(activeRenderedCardIndices)
                    let previousBoundaryTarget = viewModel.currentCardIndex == 0
                        ? viewModel.adjacentSectionTargetIfAvailable(offset: -1, anchor: .last)
                        : nil
                    let nextBoundaryTarget = viewModel.currentCardIndex == viewModel.sectionCards.count - 1
                        ? viewModel.adjacentSectionTargetIfAvailable(offset: 1, anchor: .first)
                        : nil
                    let leadingBoundaryPageCount = previousBoundaryTarget == nil ? 0 : 1
                    let totalPageCount = max(
                        1,
                        viewModel.sectionCards.count
                        + leadingBoundaryPageCount
                        + (nextBoundaryTarget == nil ? 0 : 1)
                    )
                    let totalPageWidth = CGFloat(totalPageCount) * pageWidth
                    ZStack {
                        ZStack {
                            HStack(spacing: 0) {
                                cardPagerPages(
                                    renderedIndices: renderedIndices,
                                    previousBoundaryTarget: previousBoundaryTarget,
                                    nextBoundaryTarget: nextBoundaryTarget,
                                    pageWidth: pageWidth
                                )
                            }
                            .frame(width: totalPageWidth, alignment: .leading)
                            .offset(
                                x: (-CGFloat(viewModel.currentCardIndex + leadingBoundaryPageCount) * pageWidth)
                                + interactiveCardOffsetX
                                + settlingCardOffsetX
                            )
                            .animation(cardSwipeAnimation, value: viewModel.currentCardIndex)
                        }
                    }
                    .simultaneousGesture(cardSwipeGesture(pageWidth: pageWidth))
                    .clipped()
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
            .contentShape(Rectangle())
            .simultaneousGesture(edgeBackSwipeGesture)
        }
        .sheet(isPresented: $viewModel.isDirectoryPresented) {
            DirectorySheet(viewModel: viewModel)
                .presentationDetents([.medium, .large])
                .presentationDragIndicator(.visible)
        }
        .task {
            await viewModel.loadInitialData()
        }
        .onAppear {
            syncRenderedCardWindow(immediate: true)
        }
        .onChange(of: viewModel.currentCardIndex) { _, _ in
            syncRenderedCardWindow()
        }
        .onChange(of: viewModel.shouldRenderAdjacentCards) { _, _ in
            syncRenderedCardWindow(immediate: true)
        }
        .onChange(of: viewModel.sectionCards.map(\.pointID)) { _, _ in
            syncRenderedCardWindow(immediate: true)
        }
        .onReceive(NotificationCenter.default.publisher(for: ContentPackageRemoteStore.didClearLocalCacheNotification)) { _ in
            Task {
                await viewModel.reloadAfterContentCacheClear()
                syncRenderedCardWindow(immediate: true)
            }
        }
        .alert("数据加载失败", isPresented: Binding(
            get: { viewModel.loadErrorMessage != nil },
            set: { newValue in
                if !newValue { viewModel.loadErrorMessage = nil }
            }
        )) {
            Button("确定", role: .cancel) { viewModel.loadErrorMessage = nil }
        } message: {
            Text(viewModel.loadErrorMessage ?? "")
        }
    }
}

// MARK: - Progress Header

private struct ProgressHeaderView: View {
    let states: [KnowledgeCardStudyViewModel.KnowledgeBarState]
    private let spacing: CGFloat = 4
    private let defaultWidth: CGFloat = 21

    var body: some View {
        GeometryReader { proxy in
            let count = max(states.count, 1)
            let totalSpacing = CGFloat(max(count - 1, 0)) * spacing
            let requiredWidth = (CGFloat(count) * defaultWidth) + totalSpacing
            let barWidth = requiredWidth <= proxy.size.width
                ? defaultWidth
                : max(2, (proxy.size.width - totalSpacing) / CGFloat(count))

            HStack(spacing: spacing) {
                ForEach(Array(states.enumerated()), id: \.offset) { _, state in
                    Capsule()
                        .fill(state.color)
                        .frame(width: barWidth, height: state == .active ? 6 : 4)
                        .shadow(color: state == .active ? Token.fgBrand.opacity(0.20) : .clear, radius: 2, x: 0, y: 1)
                }
            }
            .frame(maxWidth: .infinity, alignment: .center)
        }
        .frame(height: 8)
    }
}

private extension KnowledgeCardStudyViewModel.KnowledgeBarState {
    var color: Color {
        switch self {
        case .active:
            return Token.fgBrand
        case .completed:
            return Token.fgBrandSecondary
        case .pending:
            return Token.fgDisabled
        }
    }
}

// MARK: - Top Action Bar

private struct TopActionBar: View {
    let title: String
    let onBack: () -> Void
    let onOpenCatalog: () -> Void

    var body: some View {
        HStack(spacing: 0) {
            Button(action: onBack) {
                SvgIconView(
                    name: "icon-arrow-left",
                    outerWidth: 24,
                    outerHeight: 24,
                    innerInsets: SvgIconInsets(top: 0.2083, right: 0.2083, bottom: 0.2083, left: 0.2083),
                    imageInsets: SvgIconInsets(top: -0.0714, right: -0.0714, bottom: -0.0714, left: -0.0714),
                    cssVariables: ["stroke-0": Token.fgPrimary]
                )
                .frame(width: 24, height: 24)
                .contentShape(Rectangle())
                .padding(.leading, 20)
                .padding(.trailing, 12)
            }
            .buttonStyle(.plain)

            Spacer()

            Text(title)
                .font(.custom("PingFang SC", size: 18).weight(.semibold))
                .foregroundStyle(Token.textPrimary)
                .frame(height: 28)
                .lineLimit(1)

            Spacer()

            Button(action: onOpenCatalog) {
                SvgIconView(
                    name: "icon-menu-03",
                    outerWidth: 24,
                    outerHeight: 24,
                    innerInsets: SvgIconInsets(top: 0.2500, right: 0.1250, bottom: 0.2500, left: 0.1250),
                    imageInsets: SvgIconInsets(top: -0.0833, right: -0.0556, bottom: -0.0833, left: -0.0556),
                    cssVariables: ["stroke-0": Token.fgPrimary]
                )
                .frame(width: 24, height: 24)
                .contentShape(Rectangle())
                .padding(.leading, 12)
                .padding(.trailing, 20)
            }
            .buttonStyle(.plain)
        }
        .frame(height: 56)
    }
}

// MARK: - Directory Sheet (iOS native sheet)

private struct DirectorySheet: View {
    @ObservedObject var viewModel: KnowledgeCardStudyViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var expandedChapterID: String?

    private let accordionAnimation = Animation.timingCurve(0.25, 0.1, 0.25, 1, duration: 0.28)

    private var chapters: [KnowledgeDirectoryChapter] {
        viewModel.directoryChapters.sorted { $0.sortNo < $1.sortNo }
    }

    var body: some View {
        VStack(spacing: 0) {
            directoryHeader

            ScrollView(.vertical, showsIndicators: false) {
                VStack(alignment: .leading, spacing: 0) {
                    Color.clear
                        .frame(height: 16)

                    ForEach(chapters) { chapter in
                        VStack(spacing: 0) {
                            chapterRow(chapter)

                            if expandedChapterID == chapter.id {
                                VStack(spacing: 0) {
                                    ForEach(chapter.sections.sorted { $0.sortNo < $1.sortNo }) { section in
                                        sectionRow(section, in: chapter)
                                    }
                                }
                                .clipped()
                                .transition(.opacity)
                            }
                        }
                        .animation(accordionAnimation, value: expandedChapterID)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .topLeading)
            }
        }
        .background(Token.bgCanvas)
        .onAppear {
            if expandedChapterID == nil {
                expandedChapterID = viewModel.selectedChapterID
            }
        }
    }

    private var directoryHeader: some View {
        ZStack(alignment: .top) {
            HStack(spacing: 8) {
                Text("目录")
                    .font(.custom("PingFang SC", size: 20).weight(.semibold))
                    .lineSpacing(0)
                    .foregroundStyle(Token.textPrimary)
                    .frame(maxWidth: .infinity, alignment: .leading)

                Button(action: closeSheet) {
                    directoryCloseIcon
                        .frame(width: 24, height: 24)
                        .frame(width: 44, height: 44)
                        .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityLabel("关闭目录")
            }
            .padding(20)
            .frame(height: 72)

            RoundedRectangle(cornerRadius: 100, style: .continuous)
                .fill(Token.fgDisabled)
                .frame(width: 32, height: 5)
                .padding(.top, 6)
        }
        .background(Token.bgCanvas)
        .overlay(alignment: .bottom) {
            Rectangle()
                .fill(Token.borderDefault)
                .frame(height: 1)
        }
    }

    private func chapterRow(_ chapter: KnowledgeDirectoryChapter) -> some View {
        let isExpanded = expandedChapterID == chapter.id

        return Button {
            withAnimation(accordionAnimation) {
                expandedChapterID = isExpanded ? nil : chapter.id
            }
        } label: {
            HStack(spacing: 8) {
                Text(chapter.title)
                    .font(.custom("PingFang SC", size: 16).weight(.medium))
                    .lineSpacing(0)
                    .foregroundStyle(Token.textSecondary)
                    .frame(maxWidth: .infinity, alignment: .leading)

                directoryChevronIcon(isExpanded: isExpanded)
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 16)
            .contentShape(RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous))
        }
        .buttonStyle(.plain)
    }

    private func sectionRow(_ section: KnowledgeDirectorySection, in chapter: KnowledgeDirectoryChapter) -> some View {
        let isSelected = viewModel.selectedChapterID == chapter.id && viewModel.selectedSectionID == section.id

        return Button {
            viewModel.selectDirectorySection(chapter: chapter, section: section)
        } label: {
            HStack(spacing: 8) {
                Text(section.title)
                    .font(.custom("PingFang SC", size: 16).weight(isSelected ? .medium : .regular))
                    .lineSpacing(0)
                    .foregroundStyle(isSelected ? Token.textBrand : Token.textSecondary)
                    .frame(maxWidth: .infinity, alignment: .leading)

                if isSelected {
                    currentSectionBadge
                        .transition(.opacity)
                }
            }
            .padding(.leading, 40)
            .padding(.trailing, 20)
            .padding(.vertical, 16)
            .contentShape(RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous))
        }
        .buttonStyle(.plain)
    }

    private func closeSheet() {
        viewModel.isDirectoryPresented = false
        dismiss()
    }

    private var directoryCloseIcon: some View {
        SvgIconView(
            name: "icon-dir-x-close",
            outerWidth: 24,
            outerHeight: 24,
            innerInsets: SvgIconInsets(top: 0.25, right: 0.25, bottom: 0.25, left: 0.25),
            imageInsets: SvgIconInsets(top: -0.0833, right: -0.0833, bottom: -0.0833, left: -0.0833),
            cssVariables: ["stroke-0": Token.textTertiary]
        )
    }

    private func directoryChevronIcon(isExpanded: Bool) -> some View {
        SvgIconView(
            name: "icon-dir-chevron-left",
            outerWidth: 24,
            outerHeight: 24,
            innerInsets: SvgIconInsets(top: 0.25, right: 0.375, bottom: 0.25, left: 0.375),
            imageInsets: SvgIconInsets(top: -0.0833, right: -0.1667, bottom: -0.0833, left: -0.1667),
            cssVariables: ["stroke-0": Token.fgTertiary]
        )
        .rotationEffect(.degrees(isExpanded ? -90 : 0))
        .animation(accordionAnimation, value: isExpanded)
    }

    private var currentSectionBadge: some View {
        Text("当前")
            .font(.custom("PingFang SC", size: 14).weight(.regular))
            .lineSpacing(0)
            .foregroundStyle(Token.textBrand)
            .frame(height: 22, alignment: .center)
            .padding(.horizontal, 8)
            .frame(height: 24, alignment: .center)
            .background(Token.fgBrandSubtle)
            .clipShape(Capsule())
    }
}

// MARK: - Knowledge Body Card

private struct KnowledgeBodyCard: View {
    let markdown: String
    let focusHighlightVisible: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            LeoMarkdownView(
                content: markdown,
                theme: .automatic,
                variant: .knowledgeCard,
                focusHighlightVisible: focusHighlightVisible
            )
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Token.bgSubtleAlt)
        .clipShape(RoundedRectangle(cornerRadius: Token.radiusMd, style: .continuous))
    }
}

// MARK: - Note Card

private struct NoteCard: View {
    let icon: String
    let iconStrokeColor: Color
    let iconBackground: Color
    let title: String
    let titleColor: Color
    let markdown: String
    let focusHighlightVisible: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 8) {
                ZStack {
                    RoundedRectangle(cornerRadius: 8, style: .continuous)
                        .fill(iconBackground)

                    SvgIconView(
                        name: icon,
                        outerWidth: 16,
                        outerHeight: 16,
                        innerInsets: SvgIconInsets(top: 0.0833, right: 0.0833, bottom: 0.0833, left: 0.0833),
                        imageInsets: SvgIconInsets(top: -0.0563, right: -0.0562, bottom: -0.0562, left: -0.0563),
                        cssVariables: ["stroke-0": iconStrokeColor],
                        cssValues: ["stroke-width-0": "1.2"]
                    )
                }
                .frame(width: 32, height: 32)

                Text(title)
                    .font(.custom("PingFang SC", size: 18).weight(.semibold))
                    .foregroundStyle(titleColor)
                    .lineLimit(1)

                Spacer(minLength: 0)
            }

            LeoMarkdownView(
                content: markdown,
                theme: .automatic,
                variant: .studyNote,
                focusHighlightVisible: focusHighlightVisible
            )
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Token.bgSurface)
        .overlay(
            RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous)
                .stroke(Token.borderDefault, lineWidth: 1)
        )
        .clipShape(RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous))
    }
}

// MARK: - Bottom Actions

private struct BottomActions: View {
    @Binding var focusHighlightVisible: Bool
    let isCurrentCardMastered: Bool
    let onToggleCurrentCardMastered: () -> Void
    @State private var focusToggleAnimationTick = 0

    var body: some View {
        HStack(spacing: 16) {
            Button {
                focusToggleAnimationTick += 1
                focusHighlightVisible.toggle()
            } label: {
                FocusVisibilityToggleButton(isVisible: focusHighlightVisible)
                    .phaseAnimator([1.0, 1.08, 1.0], trigger: focusToggleAnimationTick) { content, phase in
                        content.scaleEffect(phase)
                    } animation: { phase in
                        phase == 1.08
                            ? .spring(response: 0.18, dampingFraction: 0.62)
                            : .spring(response: 0.22, dampingFraction: 0.78)
                    }
            }
            .buttonStyle(.plain)
            .frame(width: 56)

            Button(action: onToggleCurrentCardMastered) {
                Text(isCurrentCardMastered ? "已掌握" : "记住了")
                    .font(.custom("PingFang SC", size: 16).weight(.medium))
                    .foregroundStyle(isCurrentCardMastered ? Token.textSecondary : Token.textWhite)
                    .frame(maxWidth: .infinity)
                    .frame(height: 48)
                    .background(isCurrentCardMastered ? Token.fgDisabled : Token.fgBrand)
                    .clipShape(RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous))
            }
            .buttonStyle(.plain)
            .frame(maxWidth: .infinity)
        }
        .padding(.horizontal, 20)
        .padding(.bottom, 12)
        .frame(maxWidth: .infinity)
        .background(Token.bgCanvas)
    }
}

private struct FocusVisibilityToggleButton: View {
    let isVisible: Bool

    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous)
                .fill(isVisible ? Token.fgWarningSubtle : Token.bgSubtle2)

            ZStack {
                SVGAssetView(
                    name: "icon-lightbulb-02",
                    cssVariables: ["stroke-0": Token.fgWarning]
                )
                .frame(width: 22, height: 22)
                .opacity(isVisible ? 1 : 0)

                SVGAssetView(
                    name: "icon-lightbulb-03",
                    cssVariables: ["stroke-0": Token.fgTertiary]
                )
                .frame(width: 24, height: 24)
                .opacity(isVisible ? 0 : 1)
            }
            .animation(.easeInOut(duration: 0.12), value: isVisible)
        }
        .frame(width: 48, height: 48)
    }
}

// MARK: - Preview

#Preview {
    KnowledgeCardStudyView(viewModel: KnowledgeCardStudyViewModel())
}
