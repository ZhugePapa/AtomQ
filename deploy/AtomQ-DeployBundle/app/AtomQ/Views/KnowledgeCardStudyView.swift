import SwiftUI

struct KnowledgeCardStudyView: View {
    @Environment(\.dismiss) private var dismiss

    var onBack: (() -> Void)? = nil
    @State private var pageData = KnowledgeCardStudyContent(
        chapterID: "ch_01",
        sectionID: "sec_01_01",
        headerTitle: "1.1 信息与信息化",
        knowledgeMarkdown: "",
        keyPointsMarkdown: nil,
        mnemonicsMarkdown: nil,
        chipTitle: "知识卡片"
    )
    @State private var directoryChapters: [KnowledgeDirectoryChapter] = []
    @State private var selectedChapterID: String = "ch_01"
    @State private var selectedSectionID: String = "sec_01_01"
    @State private var expandedChapterID: String?
    @State private var isDirectorySheetPresented = false
    @State private var isDirectoryPanelPresented = false
    @State private var loadErrorMessage: String?
    @State private var focusHighlightVisible = true
    @State private var topBarCollapseProgress: CGFloat = 0
    @State private var edgeSwipeBackTriggered = false
    private let topBarHeight: CGFloat = 56
    
    private var resolvedBackAction: () -> Void {
        if let onBack {
            return onBack
        }
        return { dismiss() }
    }

    private func presentDirectorySheet() {
        guard !isDirectorySheetPresented else { return }
        expandedChapterID = selectedChapterID
        isDirectorySheetPresented = true
        DispatchQueue.main.async {
            withAnimation(.spring(response: 0.3, dampingFraction: 0.86)) {
                isDirectoryPanelPresented = true
            }
        }
    }

    private func dismissDirectorySheet() {
        withAnimation(.spring(response: 0.3, dampingFraction: 0.86)) {
            isDirectoryPanelPresented = false
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.30) {
            if !isDirectoryPanelPresented {
                isDirectorySheetPresented = false
            }
        }
    }

    private func closeDirectoryAndLoad(chapter: KnowledgeDirectoryChapter, section: KnowledgeDirectorySection) {
        selectedChapterID = chapter.id
        selectedSectionID = section.id
        do {
            pageData = try KnowledgeCardDataStore.loadStudyContent(chapterID: chapter.id, sectionID: section.id)
        } catch {
            loadErrorMessage = error.localizedDescription
        }
        withAnimation(.spring(response: 0.3, dampingFraction: 0.86)) {
            isDirectoryPanelPresented = false
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.30) {
            if !isDirectoryPanelPresented {
                isDirectorySheetPresented = false
            }
        }
    }

    var body: some View {
        ZStack {
            Token.bgCanvas
                .ignoresSafeArea()

            VStack(spacing: 0) {
                ProgressHeaderView()
                    .padding(.horizontal, 20)
                    .padding(.top, 8)
                    .padding(.bottom, 8)

                TopActionBar(
                    title: pageData.headerTitle,
                    onBack: resolvedBackAction,
                    onOpenCatalog: presentDirectorySheet
                )
                .frame(height: topBarHeight)
                .opacity(1 - topBarCollapseProgress)
                .offset(y: -24 * topBarCollapseProgress)
                .padding(.bottom, -topBarHeight * topBarCollapseProgress)
                .clipped()
                .zIndex(10)

                GeometryReader { _ in
                    ZStack {
                        ScrollView(.vertical, showsIndicators: false) {
                            VStack(spacing: 16) {
                                KnowledgeBodyCard(
                                    markdown: pageData.knowledgeMarkdown,
                                    focusHighlightVisible: focusHighlightVisible
                                )

                                if let keyPoints = pageData.keyPointsMarkdown {
                                    NoteCard(
                                        icon: "icon-target-04",
                                        iconStrokeColor: Token.fgBrand,
                                        iconBackground: Token.fgBrandSubtle,
                                        title: "高频考点",
                                        titleColor: Token.textBrand,
                                        markdown: keyPoints,
                                        focusHighlightVisible: focusHighlightVisible
                                    )
                                }

                                if let mnemonics = pageData.mnemonicsMarkdown {
                                    NoteCard(
                                        icon: "icon-stars-03",
                                        iconStrokeColor: Token.fgWarning,
                                        iconBackground: Token.fgWarningSubtle,
                                        title: "记忆口诀",
                                        titleColor: Token.textWarning,
                                        markdown: mnemonics,
                                        focusHighlightVisible: focusHighlightVisible
                                    )
                                }

                                HStack(spacing: 16) {
                                    Text(pageData.chipTitle)
                                        .font(.custom("PingFang SC", size: 14).weight(.medium))
                                        .foregroundStyle(Token.textBrand)
                                        .padding(.horizontal, 12)
                                        .frame(height: 32)
                                        .background(Token.fgBrandSubtle)
                                        .clipShape(Capsule())

                                    Spacer(minLength: 0)

                                    IconWrapper(
                                        name: "icon-star-01",
                                        outerWidth: 24,
                                        outerHeight: 24,
                                        innerInsets: IconInsets(top: 0.1096, right: 0.1073, bottom: 0.1416, left: 0.1073),
                                        imageInsets: IconInsets(top: -0.0556, right: -0.0530, bottom: -0.0556, left: -0.0530),
                                        cssVariables: ["stroke-0": Token.fgTertiary]
                                    )

                                    IconWrapper(
                                        name: "icon-dots-horizontal",
                                        outerWidth: 24,
                                        outerHeight: 24,
                                        innerInsets: IconInsets(top: 0.4583, right: 0.1667, bottom: 0.4583, left: 0.1667),
                                        imageInsets: IconInsets(top: -0.5000, right: -0.0625, bottom: -0.5000, left: -0.0625),
                                        cssVariables: ["stroke-0": Token.fgTertiary]
                                    )
                                }
                            }
                            .padding(.horizontal, 20)
                            .padding(.top, 8)
                            .padding(.bottom, 120)
                            .onGeometryChange(for: CGFloat.self) { proxy in
                                proxy.frame(in: .scrollView).minY
                            } action: { minY in
                                let progress = max(0, min(1, -minY / topBarHeight))
                                topBarCollapseProgress = progress
                            }
                        }

                        LinearGradient(
                            stops: [
                                .init(color: Token.componentsAlpha0, location: 0.03125),
                                .init(color: Token.componentsAlpha100, location: 0.796875),
                            ],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                        .frame(height: 96)
                        .frame(maxHeight: .infinity, alignment: .bottom)
                        .allowsHitTesting(false)

                        Text("TIPS：左右滑动可切换知识卡片")
                            .font(.custom("PingFang SC", size: 12).weight(.regular))
                            .foregroundStyle(Token.textTertiary)
                            .padding(.horizontal, 12)
                            .frame(height: 24)
                            .background(Token.bgSubtleAlt)
                            .clipShape(Capsule())
                            .padding(.bottom, 12)
                            .frame(maxHeight: .infinity, alignment: .bottom)
                            .zIndex(1)
                    }
                    .clipped()
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)

                BottomActions(
                    focusHighlightVisible: $focusHighlightVisible
                )
            }

            if isDirectorySheetPresented {
                ZStack(alignment: .bottom) {
                    Color.black.opacity(0.25)
                        .onTapGesture(perform: dismissDirectorySheet)
                        .transition(.identity)

                    if isDirectoryPanelPresented {
                        DirectorySheetOverlay(
                            chapters: directoryChapters,
                            selectedChapterID: selectedChapterID,
                            selectedSectionID: selectedSectionID,
                            expandedChapterID: $expandedChapterID,
                            onClose: dismissDirectorySheet,
                            onSelectSection: closeDirectoryAndLoad
                        )
                        .transition(.move(edge: .bottom))
                    }
                }
                .ignoresSafeArea()
                .zIndex(400)
            }

            // Hard fallback hit area for back action (left corner only).
            VStack {
                Button(action: resolvedBackAction) {
                    Color.black.opacity(0.001).frame(width: 88, height: 56)
                }
                .buttonStyle(.plain)
                .padding(.top, 24)
                .padding(.leading, 0)
                Spacer(minLength: 0)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
            .allowsHitTesting(!isDirectorySheetPresented)
            .zIndex(1000)

            // Hard fallback hit area for catalog action (right corner only).
            VStack {
                HStack {
                    Spacer(minLength: 0)
                    Button(action: presentDirectorySheet) {
                        Color.black.opacity(0.001).frame(width: 88, height: 56)
                    }
                    .buttonStyle(.plain)
                }
                .padding(.top, 24)
                Spacer(minLength: 0)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topTrailing)
            .allowsHitTesting(!isDirectorySheetPresented)
            .zIndex(1001)

            // Left-edge swipe back: drag right from screen edge to go back.
            HStack(spacing: 0) {
                Color.black.opacity(0.001)
                    .frame(width: 20)
                    .contentShape(Rectangle())
                    .gesture(
                        DragGesture(minimumDistance: 8)
                            .onChanged { value in
                                guard !edgeSwipeBackTriggered else { return }
                                let movedRight = value.translation.width > 56
                                let stableVertical = abs(value.translation.height) < 40
                                if movedRight && stableVertical {
                                    edgeSwipeBackTriggered = true
                                    resolvedBackAction()
                                }
                            }
                            .onEnded { _ in
                                edgeSwipeBackTriggered = false
                            }
                    )
                Spacer(minLength: 0)
            }
            .allowsHitTesting(!isDirectorySheetPresented)
            .zIndex(999)
        }
        .task {
            do {
                directoryChapters = try await KnowledgeCardDataStore.refreshFreeContentAndLoadDirectoryTree()
                if let firstChapter = directoryChapters.first {
                    let defaultSection = firstChapter.sections.first?.id ?? selectedSectionID
                    selectedChapterID = firstChapter.id
                    selectedSectionID = defaultSection
                }

                pageData = try await KnowledgeCardDataStore.refreshFreeContentAndLoadStudyContent(
                    chapterID: selectedChapterID,
                    sectionID: selectedSectionID
                )
                selectedChapterID = pageData.chapterID
                selectedSectionID = pageData.sectionID
                if expandedChapterID == nil {
                    expandedChapterID = selectedChapterID
                }
                loadErrorMessage = nil
            } catch {
                directoryChapters = []
                loadErrorMessage = error.localizedDescription
            }
        }
        .alert("数据加载失败", isPresented: Binding(
            get: { loadErrorMessage != nil },
            set: { newValue in
                if !newValue { loadErrorMessage = nil }
            }
        )) {
            Button("确定", role: .cancel) { loadErrorMessage = nil }
        } message: {
            Text(loadErrorMessage ?? "")
        }
    }
}

private struct ProgressHeaderView: View {
    private let barStates: [ProgressState] = [.success, .success, .disabled, .success, .success, .active, .disabled]

    var body: some View {
        HStack(spacing: 4) {
            ForEach(Array(barStates.enumerated()), id: \.offset) { _, state in
                Capsule()
                    .fill(state.color)
                    .frame(height: state == .active ? 6 : 4)
                    .shadow(color: state == .active ? Token.fgBrand.opacity(0.20) : .clear, radius: 2, x: 0, y: 1)
            }
        }
        .frame(height: 8)
    }

    private enum ProgressState {
        case active
        case success
        case disabled

        var color: Color {
            switch self {
            case .active:
                return Token.fgBrand
            case .success:
                return Token.fgSuccessSecondary
            case .disabled:
                return Token.fgDisabled
            }
        }
    }
}

private struct TopActionBar: View {
    let title: String
    let onBack: () -> Void
    let onOpenCatalog: () -> Void

    var body: some View {
        ZStack {
            HStack {
                Button(action: onBack) {
                    IconWrapper(
                        name: "icon-arrow-left",
                        outerWidth: 24,
                        outerHeight: 24,
                        innerInsets: IconInsets(top: 0.2083, right: 0.2083, bottom: 0.2083, left: 0.2083),
                        imageInsets: IconInsets(top: -0.0714, right: -0.0714, bottom: -0.0714, left: -0.0714),
                        cssVariables: ["stroke-0": Token.fgPrimary]
                    )
                    .frame(width: 44, height: 44)
                    .contentShape(Rectangle())
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
                    IconWrapper(
                        name: "icon-menu-03",
                        outerWidth: 24,
                        outerHeight: 24,
                        innerInsets: IconInsets(top: 0.2500, right: 0.1250, bottom: 0.2500, left: 0.1250),
                        imageInsets: IconInsets(top: -0.0833, right: -0.0556, bottom: -0.0833, left: -0.0556),
                        cssVariables: ["stroke-0": Token.fgPrimary]
                    )
                    .frame(width: 44, height: 44)
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
            }
            
            // Fallback touch target: left area only, avoid blocking right menu button.
            HStack {
                Button(action: onBack) {
                    Color.black.opacity(0.001).frame(width: 64, height: 56)
                }
                .buttonStyle(.plain)
                Spacer(minLength: 0)
            }
            .allowsHitTesting(false)
        }
        .padding(.horizontal, 20)
        .frame(height: 56)
    }
}

private struct DirectorySheetOverlay: View {
    let chapters: [KnowledgeDirectoryChapter]
    let selectedChapterID: String
    let selectedSectionID: String
    @Binding var expandedChapterID: String?
    let onClose: () -> Void
    let onSelectSection: (KnowledgeDirectoryChapter, KnowledgeDirectorySection) -> Void

    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 8) {
                Text("目录")
                    .font(.custom("PingFang SC", size: 20).weight(.semibold))
                    .foregroundStyle(Token.textPrimary)
                    .frame(maxWidth: .infinity, alignment: .leading)

                IconWrapper(
                    name: "icon-dir-x-close",
                    outerWidth: 24,
                    outerHeight: 24,
                    innerInsets: IconInsets(top: 0.25, right: 0.25, bottom: 0.25, left: 0.25),
                    imageInsets: IconInsets(top: -0.0833, right: -0.0833, bottom: -0.0833, left: -0.0833),
                    cssVariables: ["stroke-0": Token.fgTertiary]
                )
                .contentShape(Rectangle())
                .onTapGesture(perform: onClose)
            }
            .padding(.horizontal, 20)
            .padding(.top, 20)
            .padding(.bottom, 20)
            .background(Token.bgCanvas)
            .overlay(alignment: .top) {
                DirectoryDragIndicator(onClose: onClose)
            }
            .overlay(alignment: .bottom) {
                Rectangle()
                    .fill(Token.borderDefault)
                    .frame(height: 1)
            }

            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: 0) {
                    ForEach(chapters) { chapter in
                        DirectoryChapterRow(
                            chapter: chapter,
                            selectedChapterID: selectedChapterID,
                            selectedSectionID: selectedSectionID,
                            isExpanded: expandedChapterID == chapter.id,
                            onToggleExpand: {
                                if expandedChapterID == chapter.id {
                                    expandedChapterID = nil
                                } else {
                                    expandedChapterID = chapter.id
                                }
                            },
                            onSelectSection: { section in
                                onSelectSection(chapter, section)
                            }
                        )
                    }
                }
                .padding(.bottom, 24)
            }
        }
        .frame(maxWidth: .infinity)
        .frame(height: 640)
        .background(Token.bgCanvas)
        .clipShape(
            UnevenRoundedRectangle(
                topLeadingRadius: 24,
                bottomLeadingRadius: 0,
                bottomTrailingRadius: 0,
                topTrailingRadius: 24
            )
        )
        .overlay(
            UnevenRoundedRectangle(
                topLeadingRadius: 24,
                bottomLeadingRadius: 0,
                bottomTrailingRadius: 0,
                topTrailingRadius: 24
            )
            .stroke(Token.borderDefault, lineWidth: 1)
        )
        .gesture(
            DragGesture(minimumDistance: 8)
                .onEnded { value in
                    if value.translation.height > 48 {
                        onClose()
                    }
                }
        )
    }
}

private struct DirectoryDragIndicator: View {
    let onClose: () -> Void

    var body: some View {
        Capsule()
            .fill(Token.fgDisabled)
            .frame(width: 32, height: 5)
            .padding(.top, 6)
            .padding(.bottom, 4)
            .contentShape(Rectangle())
            .onTapGesture(perform: onClose)
            .simultaneousGesture(
                DragGesture(minimumDistance: 4)
                    .onEnded { value in
                        if value.translation.height > 20 {
                            onClose()
                        }
                    }
            )
    }
}

private struct DirectoryChapterRow: View {
    let chapter: KnowledgeDirectoryChapter
    let selectedChapterID: String
    let selectedSectionID: String
    let isExpanded: Bool
    let onToggleExpand: () -> Void
    let onSelectSection: (KnowledgeDirectorySection) -> Void

    var body: some View {
        VStack(spacing: 0) {
            Button(action: onToggleExpand) {
                HStack(spacing: 8) {
                    Text(chapter.title)
                        .font(.custom("PingFang SC", size: 16).weight(.medium))
                        .foregroundStyle(Token.textSecondary)
                        .frame(maxWidth: .infinity, alignment: .leading)

                    IconWrapper(
                        name: isExpanded ? "icon-dir-chevron-down" : "icon-dir-chevron-left",
                        outerWidth: 24,
                        outerHeight: 24,
                        innerInsets: isExpanded
                            ? IconInsets(top: 0.3750, right: 0.2500, bottom: 0.3750, left: 0.2500)
                            : IconInsets(top: 0.2500, right: 0.3750, bottom: 0.2500, left: 0.3750),
                        imageInsets: isExpanded
                            ? IconInsets(top: -0.1667, right: -0.0833, bottom: -0.1667, left: -0.0833)
                            : IconInsets(top: -0.0833, right: -0.1667, bottom: -0.0833, left: -0.1667),
                        cssVariables: ["stroke-0": Token.fgTertiary]
                    )
                }
                .padding(.horizontal, 20)
                .frame(height: 56)
                .contentShape(Rectangle())
            }
            .buttonStyle(DirectoryPressableRowStyle(pressedBackground: Token.bgSubtle))

            if isExpanded {
                ForEach(chapter.sections) { section in
                    DirectorySectionRow(
                        title: section.title,
                        isSelected: section.id == selectedSectionID && chapter.id == selectedChapterID,
                        onTap: { onSelectSection(section) }
                    )
                }
            }
        }
    }
}

private struct DirectorySectionRow: View {
    let title: String
    let isSelected: Bool
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            HStack(spacing: 8) {
                Text(title)
                    .font(.custom("PingFang SC", size: 16).weight(isSelected ? .medium : .regular))
                    .foregroundStyle(isSelected ? Token.textBrand : Token.textSecondary)
                    .frame(maxWidth: .infinity, alignment: .leading)

                if isSelected {
                    IconWrapper(
                        name: "icon-dir-check",
                        outerWidth: 24,
                        outerHeight: 24,
                        innerInsets: IconInsets(top: 0.2706, right: 0.1667, bottom: 0.2710, left: 0.1667),
                        imageInsets: IconInsets(top: -0.0909, right: -0.0625, bottom: -0.0909, left: -0.0625),
                        cssVariables: ["stroke-0": Token.fgBrand]
                    )
                }
            }
            .padding(.leading, 40)
            .padding(.trailing, 20)
            .frame(height: 56)
            .contentShape(Rectangle())
        }
        .buttonStyle(
            DirectoryPressableRowStyle(
                pressedBackground: isSelected ? Token.fgBrandSubtle : Token.bgSubtle
            )
        )
    }
}

private struct DirectoryPressableRowStyle: ButtonStyle {
    let pressedBackground: Color

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .background(configuration.isPressed ? pressedBackground : Color.clear)
            .clipShape(RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous))
    }
}

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

                    IconWrapper(
                        name: icon,
                        outerWidth: 16,
                        outerHeight: 16,
                        innerInsets: IconInsets(top: 0.0833, right: 0.0833, bottom: 0.0833, left: 0.0833),
                        imageInsets: IconInsets(top: -0.0563, right: -0.0562, bottom: -0.0562, left: -0.0563),
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

private struct BottomActions: View {
    @Binding var focusHighlightVisible: Bool
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

            Button(action: {}) {
                Text("已掌握")
                    .font(.custom("PingFang SC", size: 16).weight(.medium))
                    .foregroundStyle(Token.textWhite)
                    .frame(maxWidth: .infinity)
                    .frame(height: 48)
                    .background(Token.fgBrand)
                    .clipShape(RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous))
            }
            .buttonStyle(.plain)
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

private struct IconInsets {
    let top: CGFloat
    let right: CGFloat
    let bottom: CGFloat
    let left: CGFloat

    static let zero = IconInsets(top: 0, right: 0, bottom: 0, left: 0)
}

private struct IconWrapper: View {
    let name: String
    let outerWidth: CGFloat
    let outerHeight: CGFloat
    let innerInsets: IconInsets
    let imageInsets: IconInsets
    let cssVariables: [String: Color]
    let cssValues: [String: String]
    let shouldClip: Bool

    init(
        name: String,
        outerWidth: CGFloat,
        outerHeight: CGFloat,
        innerInsets: IconInsets = .zero,
        imageInsets: IconInsets = .zero,
        cssVariables: [String: Color] = [:],
        cssValues: [String: String] = [:],
        shouldClip: Bool = true
    ) {
        self.name = name
        self.outerWidth = outerWidth
        self.outerHeight = outerHeight
        self.innerInsets = innerInsets
        self.imageInsets = imageInsets
        self.cssVariables = cssVariables
        self.cssValues = cssValues
        self.shouldClip = shouldClip
    }

    var body: some View {
        GeometryReader { geometry in
            let width = geometry.size.width
            let height = geometry.size.height

            let innerX = width * innerInsets.left
            let innerY = height * innerInsets.top
            let innerWidth = max(0, width * (1 - innerInsets.left - innerInsets.right))
            let innerHeight = max(0, height * (1 - innerInsets.top - innerInsets.bottom))

            let imageX = innerX + innerWidth * imageInsets.left
            let imageY = innerY + innerHeight * imageInsets.top
            let imageWidth = max(0, innerWidth * (1 - imageInsets.left - imageInsets.right))
            let imageHeight = max(0, innerHeight * (1 - imageInsets.top - imageInsets.bottom))

            SVGAssetView(name: name, cssVariables: cssVariables, cssValues: cssValues)
                .frame(width: imageWidth, height: imageHeight)
                .position(x: imageX + imageWidth / 2, y: imageY + imageHeight / 2)
        }
        .frame(width: outerWidth, height: outerHeight)
        .modifier(ClipModifier(isEnabled: shouldClip))
    }
}

private struct ClipModifier: ViewModifier {
    let isEnabled: Bool

    @ViewBuilder
    func body(content: Content) -> some View {
        if isEnabled {
            content.clipped()
        } else {
            content
        }
    }
}

#Preview {
    KnowledgeCardStudyView()
}
