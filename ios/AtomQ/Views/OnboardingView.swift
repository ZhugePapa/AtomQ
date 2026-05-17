import SwiftUI

struct OnboardingView: View {
    let onFinish: () -> Void

    @State private var step: OnboardingStep = .welcome
    @State private var selectedLevel: ExamLevel = .advanced
    @State private var selectedSubject = "信息系统项目管理师"
    @State private var selectedYear = Calendar.current.component(.year, from: Date())
    @State private var selectedExamTime = "5月下旬"

    var body: some View {
        GeometryReader { proxy in
            ZStack {
                Token.bgCanvas.ignoresSafeArea()

                HStack(spacing: 0) {
                    WelcomeOnboardingPage(
                        safeAreaTop: proxy.safeAreaInsets.top,
                        safeAreaBottom: proxy.safeAreaInsets.bottom
                    ) {
                        goForward(to: .subject)
                    }
                    .frame(width: proxy.size.width, height: proxy.size.height)

                    SubjectOnboardingPage(
                        safeAreaTop: proxy.safeAreaInsets.top,
                        safeAreaBottom: proxy.safeAreaInsets.bottom,
                        selectedLevel: $selectedLevel,
                        selectedSubject: $selectedSubject
                    ) {
                        goForward(to: .plan)
                    }
                    .frame(width: proxy.size.width, height: proxy.size.height)

                    PlanOnboardingPage(
                        safeAreaTop: proxy.safeAreaInsets.top,
                        safeAreaBottom: proxy.safeAreaInsets.bottom,
                        selectedSubject: selectedSubject,
                        selectedYear: $selectedYear,
                        selectedExamTime: $selectedExamTime,
                        onFinish: onFinish
                    )
                    .frame(width: proxy.size.width, height: proxy.size.height)
                }
                .frame(
                    width: proxy.size.width * CGFloat(OnboardingStep.allCases.count),
                    height: proxy.size.height,
                    alignment: .leading
                )
                .offset(x: -CGFloat(step.index) * proxy.size.width)
                .animation(.smooth(duration: 0.34, extraBounce: 0), value: step)
                .frame(width: proxy.size.width, height: proxy.size.height, alignment: .leading)
                .clipped()
            }
            .frame(width: proxy.size.width, height: proxy.size.height)
            .clipped()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .simultaneousGesture(edgeBackGesture)
    }

    private var edgeBackGesture: some Gesture {
        DragGesture(minimumDistance: 16, coordinateSpace: .local)
            .onEnded { value in
                guard value.startLocation.x <= 28 else { return }
                guard value.translation.width > 64 else { return }
                guard abs(value.translation.height) < 60 else { return }
                goBack()
            }
    }

    private func goForward(to nextStep: OnboardingStep) {
        step = nextStep
    }

    private func goBack() {
        guard let previousStep = step.previous else { return }
        step = previousStep
    }
}

private enum OnboardingStep: CaseIterable {
    case welcome
    case subject
    case plan

    var index: Int {
        switch self {
        case .welcome:
            0
        case .subject:
            1
        case .plan:
            2
        }
    }

    var previous: OnboardingStep? {
        switch self {
        case .welcome:
            nil
        case .subject:
            .welcome
        case .plan:
            .subject
        }
    }
}

private enum ExamLevel: String, CaseIterable, Identifiable {
    case advanced = "高级"
    case intermediate = "中级"
    case junior = "初级"

    var id: String { rawValue }
}

// MARK: - Welcome

private struct WelcomeOnboardingPage: View {
    var safeAreaTop: CGFloat = 0
    var safeAreaBottom: CGFloat = 0
    let onContinueAsGuest: () -> Void

    private let features = [
        OnboardingFeature(icon: "onboarding-feature-puzzle", title: "碎片时间学习不断", subtitle: "3 分钟完成学习、刷题小任务"),
        OnboardingFeature(icon: "onboarding-feature-pie", title: "学习进度一目了然", subtitle: "掌握度、错题和每日计划持续跟进"),
        OnboardingFeature(icon: "onboarding-feature-energy", title: "弱网也能继续学", subtitle: "离线学习，联网后记录自动备份")
    ]

    var body: some View {
        GeometryReader { proxy in
            let metrics = OnboardingPageMetrics(
                size: proxy.size,
                safeAreaTop: safeAreaTop,
                safeAreaBottom: safeAreaBottom
            )

            VStack(spacing: 0) {
                Spacer().frame(height: metrics.welcomeTopSpacing)

                OnboardingLogoMark()

                Spacer().frame(height: metrics.welcomeLogoToWordmarkSpacing)

                Image("onboarding-wordmark")
                    .resizable()
                    .renderingMode(.original)
                    .frame(width: 144, height: 36)

                Spacer().frame(height: metrics.welcomeWordmarkToCardsSpacing)

                VStack(spacing: metrics.cardSpacing) {
                    ForEach(features) { feature in
                        OnboardingFeatureCard(feature: feature)
                    }
                }
                .frame(width: metrics.contentWidth)

                Spacer(minLength: metrics.minimumFlexibleSpacing)

                VStack(spacing: 12) {
                    OnboardingPrimaryButton(title: "登录") {
                        // 登录功能后续接入账号体系时再实现。
                    }

                    Button(action: onContinueAsGuest) {
                        Text("游客继续")
                            .font(.custom("PingFang SC", size: 16).weight(.medium))
                            .foregroundStyle(Token.textPrimary)
                            .frame(maxWidth: .infinity)
                            .frame(height: 56)
                    }
                    .buttonStyle(OnboardingGuestButtonStyle())
                }
                .frame(width: metrics.contentWidth)
                .padding(.bottom, metrics.bottomPadding)
            }
            .frame(width: proxy.size.width, height: proxy.size.height, alignment: .top)
        }
    }
}

private struct OnboardingLogoMark: View {
    var body: some View {
        Image("onboarding-logo")
            .resizable()
            .renderingMode(.original)
            .frame(width: 112, height: 112)
    }
}

private struct OnboardingFeature: Identifiable {
    let icon: String
    let title: String
    let subtitle: String

    var id: String { title }
}

private struct OnboardingFeatureCard: View {
    let feature: OnboardingFeature

    var body: some View {
        HStack(spacing: 16) {
            ZStack {
                RoundedRectangle(cornerRadius: Token.radiusXs, style: .continuous)
                    .fill(Token.bgSubtle2)

                Image(feature.icon)
                    .renderingMode(.template)
                    .resizable()
                    .foregroundStyle(Token.fgPrimary)
                    .frame(width: 24, height: 24)
            }
            .frame(width: 48, height: 48)

            VStack(alignment: .leading, spacing: 2) {
                Text(feature.title)
                    .font(.custom("PingFang SC", size: 16).weight(.medium))
                    .foregroundStyle(Token.textPrimary)
                    .frame(height: 24, alignment: .center)

                Text(feature.subtitle)
                    .font(.custom("PingFang SC", size: 14).weight(.regular))
                    .foregroundStyle(Token.textTertiary)
                    .frame(height: 22, alignment: .center)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(20)
        .frame(maxWidth: .infinity)
        .background(Token.bgSurface)
        .clipShape(RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous)
                .stroke(Token.borderDefault, lineWidth: 1)
        )
    }
}

// MARK: - Subject

private struct SubjectOnboardingPage: View {
    var safeAreaTop: CGFloat = 0
    var safeAreaBottom: CGFloat = 0
    @Binding var selectedLevel: ExamLevel
    @Binding var selectedSubject: String
    let onNext: () -> Void

    private let subjects = ["系统架构设计师", "信息系统项目管理师"]

    var body: some View {
        GeometryReader { proxy in
            let metrics = OnboardingPageMetrics(
                size: proxy.size,
                safeAreaTop: safeAreaTop,
                safeAreaBottom: safeAreaBottom
            )

            VStack(alignment: .leading, spacing: 0) {
                Spacer().frame(height: metrics.pageTopSpacing)

                Text("选择考试科目")
                    .font(.custom("PingFang SC", size: 28).weight(.semibold))
                    .foregroundStyle(Token.textPrimary)
                    .frame(height: 42, alignment: .center)

                Spacer().frame(height: 3)

                Text("确定目标，开启您的备考之旅")
                    .font(.custom("PingFang SC", size: 16).weight(.regular))
                    .foregroundStyle(Token.textSecondary)
                    .frame(height: 24, alignment: .center)

                Spacer().frame(height: 32)

                HStack(spacing: 8) {
                    ForEach(ExamLevel.allCases) { level in
                        Button {
                            withAnimation(.easeInOut(duration: 0.22)) {
                                selectedLevel = level
                            }
                        } label: {
                            Text(level.rawValue)
                                .font(.custom("PingFang SC", size: 14).weight(level == selectedLevel ? .semibold : .regular))
                                .foregroundStyle(level == selectedLevel ? Token.textWhite : Token.textTertiary)
                                .frame(height: 32)
                                .padding(.horizontal, metrics.levelPillHorizontalPadding)
                                .background(level == selectedLevel ? Token.fgPrimary : Color.clear)
                                .clipShape(Capsule())
                        }
                        .buttonStyle(.plain)
                    }
                }

                Spacer().frame(height: metrics.cardSpacing)

                VStack(spacing: metrics.cardSpacing) {
                    ForEach(subjects, id: \.self) { subject in
                        SubjectTile(
                            title: subject,
                            isSelected: subject == selectedSubject
                        ) {
                            selectedSubject = subject
                        }
                    }
                }

                Spacer(minLength: metrics.minimumFlexibleSpacing)

                OnboardingPrimaryButton(
                    title: "下一步",
                    trailingIcon: "icon-arrow-forward",
                    trailingIconSize: 16,
                    action: onNext
                )
                    .padding(.bottom, metrics.bottomPadding)
            }
            .frame(width: metrics.contentWidth, alignment: .topLeading)
            .frame(maxHeight: .infinity, alignment: .topLeading)
            .frame(width: proxy.size.width, height: proxy.size.height, alignment: .top)
            .gesture(
                DragGesture(minimumDistance: 24)
                    .onEnded { value in
                        guard value.startLocation.x > 32 else { return }
                        guard abs(value.translation.width) > abs(value.translation.height) else { return }
                        updateLevel(by: value.translation.width < 0 ? 1 : -1)
                    }
            )
        }
    }

    private func updateLevel(by delta: Int) {
        let all = ExamLevel.allCases
        guard let currentIndex = all.firstIndex(of: selectedLevel) else { return }
        let nextIndex = min(max(currentIndex + delta, 0), all.count - 1)
        withAnimation(.easeInOut(duration: 0.22)) {
            selectedLevel = all[nextIndex]
        }
    }
}

private struct SubjectTile: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 16) {
                Text(title)
                    .font(.custom("PingFang SC", size: 16).weight(isSelected ? .semibold : .regular))
                    .foregroundStyle(isSelected ? Token.textPrimary : Token.textSecondary)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .frame(height: 24)

                if isSelected {
                    Image("onboarding-check")
                        .renderingMode(.template)
                        .resizable()
                        .foregroundStyle(Token.fgPrimary)
                        .frame(width: 18, height: 18)
                        .frame(width: 24, height: 24)
                }
            }
            .padding(16)
            .frame(maxWidth: .infinity)
            .background(isSelected ? Token.bgSubtle : Token.bgSurface)
            .clipShape(RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous)
                    .stroke(isSelected ? Token.fgPrimary : Token.borderDefault, lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Plan

private struct PlanOnboardingPage: View {
    var safeAreaTop: CGFloat = 0
    var safeAreaBottom: CGFloat = 0
    let selectedSubject: String
    @Binding var selectedYear: Int
    @Binding var selectedExamTime: String
    let onFinish: () -> Void

    private var years: [Int] {
        let current = Calendar.current.component(.year, from: Date())
        return [current, current + 1, current + 2]
    }

    var body: some View {
        GeometryReader { proxy in
            let metrics = OnboardingPageMetrics(
                size: proxy.size,
                safeAreaTop: safeAreaTop,
                safeAreaBottom: safeAreaBottom
            )

            VStack(alignment: .leading, spacing: 0) {
                Spacer().frame(height: metrics.pageTopSpacing)

                Text("选择考试时间")
                    .font(.custom("PingFang SC", size: 28).weight(.semibold))
                    .foregroundStyle(Token.textPrimary)
                    .frame(height: 42, alignment: .center)

                Spacer().frame(height: 3)

                Text("为您制定专属的学习计划")
                    .font(.custom("PingFang SC", size: 16).weight(.regular))
                    .foregroundStyle(Token.textSecondary)
                    .frame(height: 24, alignment: .center)

                Spacer().frame(height: 32)

                Text("高级 - \(selectedSubject)")
                    .font(.custom("PingFang SC", size: 14).weight(.medium))
                    .foregroundStyle(Token.textPrimary)
                    .frame(height: 24)
                    .padding(.horizontal, 12)
                    .background(Token.bgSubtle2)
                    .clipShape(Capsule())

                Spacer().frame(height: metrics.cardSpacing)

                HStack(spacing: metrics.cardSpacing) {
                    PlanMetricCard(icon: "onboarding-calendar-check", title: "距离考试", value: "128", unit: "天")
                    PlanMetricCard(icon: "onboarding-plan-pie", title: "建议学习量", value: "2.5", unit: "小时/日")
                }

                Spacer(minLength: metrics.minimumFlexibleSpacing)

                VStack(alignment: .leading, spacing: 24) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("考试年份")
                            .font(.custom("PingFang SC", size: 14).weight(.medium))
                            .foregroundStyle(Token.textTertiary)
                            .frame(height: 22)

                        OnboardingSegmentedControl(
                            items: years.map(String.init),
                            selected: Binding(
                                get: { String(selectedYear) },
                                set: { selectedYear = Int($0) ?? selectedYear }
                            )
                        )
                    }

                    VStack(alignment: .leading, spacing: 8) {
                        Text("考试时间")
                            .font(.custom("PingFang SC", size: 14).weight(.medium))
                            .foregroundStyle(Token.textTertiary)
                            .frame(height: 22)

                        OnboardingSegmentedControl(
                            items: ["5月下旬", "11月上旬"],
                            selected: $selectedExamTime
                        )
                    }

                    OnboardingPrimaryButton(title: "开始学习", leadingIcon: "onboarding-stars", action: onFinish)
                }
                .padding(.top, 24)
                .padding(.horizontal, metrics.horizontalPadding)
                .frame(width: proxy.size.width)
                .background(Token.bgSurface)
                .clipShape(UnevenRoundedRectangle(topLeadingRadius: 24, topTrailingRadius: 24))
                .shadow(color: Token.overlaySoft, radius: 30, x: 0, y: -10)
                .offset(x: -metrics.horizontalPadding)
                .padding(.bottom, metrics.bottomPadding)
            }
            .frame(width: metrics.contentWidth, alignment: .topLeading)
            .frame(maxHeight: .infinity, alignment: .topLeading)
            .frame(width: proxy.size.width, height: proxy.size.height, alignment: .top)
        }
    }
}

private struct PlanMetricCard: View {
    let icon: String
    let title: String
    let value: String
    let unit: String

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            ZStack {
                RoundedRectangle(cornerRadius: Token.radiusXs, style: .continuous)
                    .fill(Token.bgSubtle2)

                Image(icon)
                    .renderingMode(.template)
                    .resizable()
                    .foregroundStyle(Token.fgPrimary)
                    .frame(width: 24, height: 24)
            }
            .frame(width: 48, height: 48)

            Spacer().frame(height: 8)

            Text(title)
                .font(.custom("PingFang SC", size: 14).weight(.medium))
                .foregroundStyle(Token.textPrimary)
                .frame(height: 22)

            HStack(alignment: .lastTextBaseline, spacing: 6) {
                Text(value)
                    .font(OnboardingFont.dataXxxlgDINBold())
                    .foregroundStyle(Token.textBrand)
                    .frame(height: 48, alignment: .bottom)

                Text(unit)
                    .font(.custom("PingFang SC", size: 12).weight(.regular))
                    .foregroundStyle(Token.textTertiary)
                    .padding(.bottom, 6)

                Spacer(minLength: 0)
            }
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Token.bgSurface)
        .clipShape(RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous)
                .stroke(Token.borderDefault, lineWidth: 1)
        )
    }
}

private struct OnboardingSegmentedControl: View {
    let items: [String]
    @Binding var selected: String

    var body: some View {
        GeometryReader { proxy in
            let count = max(items.count, 1)
            let itemWidth = proxy.size.width / CGFloat(count)
            let selectedIndex = items.firstIndex(of: selected) ?? 0

            ZStack(alignment: .leading) {
                RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous)
                    .fill(Token.bgSurface)
                    .shadow(color: Color.black.opacity(0.03), radius: 6, x: 1, y: 2)
                    .frame(width: itemWidth, height: 40)
                    .offset(x: itemWidth * CGFloat(selectedIndex))
                    .animation(.smooth(duration: 0.24, extraBounce: 0), value: selectedIndex)

                HStack(spacing: 0) {
                    ForEach(items, id: \.self) { item in
                        Button {
                            selected = item
                        } label: {
                            Text(item)
                                .font(.custom("PingFang SC", size: 16).weight(item == selected ? .semibold : .regular))
                                .foregroundStyle(item == selected ? Token.textPrimary : Token.textTertiary)
                                .frame(maxWidth: .infinity)
                                .frame(height: 40)
                                .contentShape(RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous))
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
        }
        .padding(4)
        .frame(height: 48)
        .background(Token.bgSubtle2)
        .clipShape(RoundedRectangle(cornerRadius: Token.radiusMd, style: .continuous))
    }
}

// MARK: - Layout

private struct OnboardingPageMetrics {
    let size: CGSize
    let safeAreaTop: CGFloat
    let safeAreaBottom: CGFloat

    var horizontalPadding: CGFloat {
        24
    }

    var contentWidth: CGFloat {
        max(size.width - horizontalPadding * 2, 0)
    }

    var welcomeTopSpacing: CGFloat {
        48
    }

    var welcomeLogoToWordmarkSpacing: CGFloat {
        size.height < 760 ? 8 : 12
    }

    var welcomeWordmarkToCardsSpacing: CGFloat {
        40
    }

    var pageTopSpacing: CGFloat {
        24
    }

    var sectionSpacing: CGFloat {
        clamp(size.height * 0.024, min: 16, max: 24)
    }

    var cardSpacing: CGFloat {
        size.height < 760 ? 12 : 16
    }

    var minimumFlexibleSpacing: CGFloat {
        size.height < 760 ? 16 : 28
    }

    var bottomPadding: CGFloat {
        0
    }

    var levelPillHorizontalPadding: CGFloat {
        size.width < 375 ? 18 : 24
    }

    private func clamp(_ value: CGFloat, min minValue: CGFloat, max maxValue: CGFloat) -> CGFloat {
        Swift.min(Swift.max(value, minValue), maxValue)
    }
}

// MARK: - Shared

private struct OnboardingPrimaryButton: View {
    let title: String
    var leadingIcon: String?
    var leadingIconSize: CGFloat = 20
    var trailingIcon: String?
    var trailingIconSize: CGFloat = 20
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 12) {
                if let leadingIcon {
                    Image(leadingIcon)
                        .renderingMode(.template)
                        .resizable()
                        .foregroundStyle(Token.fgWhite)
                        .frame(width: leadingIconSize, height: leadingIconSize)
                }

                Text(title)
                    .font(.custom("PingFang SC", size: 16).weight(.medium))
                    .foregroundStyle(Token.textWhite)

                if let trailingIcon {
                    Image(trailingIcon)
                        .renderingMode(.template)
                        .resizable()
                        .foregroundStyle(Token.fgWhite)
                        .frame(width: trailingIconSize, height: trailingIconSize)
                }
            }
            .frame(maxWidth: .infinity)
            .frame(height: 56)
            .background(Token.fgPrimary)
            .clipShape(RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous))
        }
        .buttonStyle(.plain)
    }
}

private struct OnboardingGuestButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .background(configuration.isPressed ? Token.bgSubtle : Token.bgCanvas)
            .clipShape(RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous)
                    .stroke(Token.borderDefault, lineWidth: 1)
            )
            .animation(.easeInOut(duration: 0.12), value: configuration.isPressed)
    }
}

private enum OnboardingFont {
    static func dataLgDINMedium() -> Font {
        din(size: 16, weight: .medium)
    }

    static func dataXxxlgDINBold() -> Font {
        din(size: 32, weight: .bold)
    }

    private static func din(size: CGFloat, weight: Font.Weight) -> Font {
        let candidates = [
            "DIN-Bold",
            "DIN-Medium",
            "DINAlternate-Bold",
            "DIN Alternate Bold",
            "DINCondensed-Bold",
            "DIN Condensed Bold",
            "DIN",
        ]
        for name in candidates where UIFont(name: name, size: size) != nil {
            return .custom(name, size: size)
        }
        return .system(size: size, weight: weight)
    }
}

// MARK: - Preview

struct OnboardingView_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            OnboardingView {}
                .previewDisplayName("Onboarding - Flow")

            WelcomeOnboardingPage {}
                .background(Token.bgCanvas)
                .previewDisplayName("Onboarding - Welcome")

            SubjectOnboardingPage(
                selectedLevel: .constant(.advanced),
                selectedSubject: .constant("信息系统项目管理师")
            ) {}
            .background(Token.bgCanvas)
            .previewDisplayName("Onboarding - Subject")

            PlanOnboardingPage(
                selectedSubject: "信息系统项目管理师",
                selectedYear: .constant(Calendar.current.component(.year, from: Date())),
                selectedExamTime: .constant("5月下旬")
            ) {}
            .background(Token.bgCanvas)
            .previewDisplayName("Onboarding - Plan")
        }
        .frame(width: 390, height: 844)
    }
}
