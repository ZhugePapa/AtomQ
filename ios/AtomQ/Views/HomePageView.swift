import SwiftUI
import UIKit

enum AppTab: String {
    case study
    case stats
    case profile
}

struct HomePageView: View {
    private enum StudyNavDirection {
        case push
        case pop
    }

    @Binding var selectedTab: AppTab
    @Binding var isDarkMode: Bool
    @State private var showingKnowledgeCardStudy = false
    @State private var studyNavDirection: StudyNavDirection = .push

    private var studyPageTransition: AnyTransition {
        switch studyNavDirection {
        case .push:
            return .asymmetric(insertion: .move(edge: .trailing), removal: .move(edge: .leading))
        case .pop:
            return .asymmetric(insertion: .move(edge: .leading), removal: .move(edge: .trailing))
        }
    }

    var body: some View {
        GeometryReader { geometry in
            let canvasWidth = geometry.size.width

            ZStack {
                Token.bgCanvas
                    .ignoresSafeArea()

                VStack(spacing: 0) {
                    Spacer().frame(height: 56)

                    if selectedTab == .study {
                        ZStack {
                            if showingKnowledgeCardStudy {
                                KnowledgeCardStudyView(
                                    onBack: {
                                        DispatchQueue.main.async {
                                            studyNavDirection = .pop
                                            withAnimation(.easeInOut(duration: 0.25)) {
                                                showingKnowledgeCardStudy = false
                                            }
                                        }
                                    }
                                )
                                .transition(studyPageTransition)
                            } else {
                                VStack(spacing: 0) {
                                    HeaderView()
                                        .frame(maxWidth: .infinity)
                                        .frame(height: 62)

                                    ContentAreaView(
                                        onOpenKnowledgeCardStudy: {
                                            studyNavDirection = .push
                                            withAnimation(.easeInOut(duration: 0.25)) {
                                                showingKnowledgeCardStudy = true
                                            }
                                        }
                                    )
                                    .frame(maxWidth: .infinity, maxHeight: .infinity)

                                    BottomTabBarView(selectedTab: $selectedTab)
                                        .frame(maxWidth: .infinity)
                                        .frame(height: 64)
                                }
                                .transition(studyPageTransition)
                            }
                        }
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .clipped()
                    } else if selectedTab == .profile {
                        VStack(spacing: 0) {
                            ProfileCenterView(isDarkMode: $isDarkMode)
                                .frame(maxWidth: .infinity, maxHeight: .infinity)

                            BottomTabBarView(selectedTab: $selectedTab)
                                .frame(maxWidth: .infinity)
                                .frame(height: 64)
                        }
                    } else {
                        VStack(spacing: 0) {
                            StatsPlaceholderView()
                                .frame(maxWidth: .infinity, maxHeight: .infinity)

                            BottomTabBarView(selectedTab: $selectedTab)
                                .frame(maxWidth: .infinity)
                                .frame(height: 64)
                        }
                    }
                }
                .ignoresSafeArea(.all, edges: .top)
                .frame(width: canvasWidth)
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
            }
        }
        .preferredColorScheme(isDarkMode ? .dark : .light)
    }
}

private struct PercentInsets {
    let top: CGFloat
    let right: CGFloat
    let bottom: CGFloat
    let left: CGFloat

    static let zero = PercentInsets(top: 0, right: 0, bottom: 0, left: 0)
}

private struct FigmaIconView: View {
    let name: String
    let outerWidth: CGFloat
    let outerHeight: CGFloat
    let innerInsets: PercentInsets
    let imageInsets: PercentInsets
    let cssVariables: [String: Color]
    let cssValues: [String: String]

    init(
        name: String,
        outerWidth: CGFloat,
        outerHeight: CGFloat,
        innerInsets: PercentInsets = .zero,
        imageInsets: PercentInsets = .zero,
        cssVariables: [String: Color] = [:],
        cssValues: [String: String] = [:]
    ) {
        self.name = name
        self.outerWidth = outerWidth
        self.outerHeight = outerHeight
        self.innerInsets = innerInsets
        self.imageInsets = imageInsets
        self.cssVariables = cssVariables
        self.cssValues = cssValues
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
        .clipped()
    }
}

private struct HeaderView: View {
    var body: some View {
        HStack(alignment: .center, spacing: 0) {
            VStack(alignment: .leading, spacing: 2) {
                (
                    Text("距考试还有 ")
                    + Text("187").foregroundStyle(Token.textBrand)
                    + Text(" 天")
                )
                .font(.custom("PingFang SC", size: 20).weight(.semibold))
                .frame(height: 30, alignment: .leading)
                .foregroundStyle(Token.textPrimary)

                Text("信息系统项目管理师")
                    .font(.custom("PingFang SC", size: 14).weight(.regular))
                    .foregroundStyle(Token.textTertiary)
                    .frame(height: 22, alignment: .leading)
                    .lineLimit(1)
            }
            .frame(maxWidth: .infinity, alignment: .leading)

            ZStack(alignment: .topTrailing) {
                FigmaIconView(
                    name: "icon-notification",
                    outerWidth: 24,
                    outerHeight: 24,
                    innerInsets: PercentInsets(top: 0.0938, right: 0.1560, bottom: 0.0938, left: 0.1559),
                    imageInsets: PercentInsets(top: -0.0513, right: -0.0611, bottom: -0.0513, left: -0.0612),
                    cssVariables: ["stroke-0": Token.fgPrimary]
                )
                FigmaIconView(
                    name: "icon-red-dot",
                    outerWidth: 8,
                    outerHeight: 8,
                    imageInsets: PercentInsets(top: -0.125, right: -0.125, bottom: -0.125, left: -0.125),
                    cssVariables: [
                        "fill-0": Token.fgDanger,
                        "stroke-0": Token.fgWhiteInverse,
                    ]
                )
                    .offset(x: -1, y: 1)
            }
            .frame(width: 24, height: 24)
        }
        .padding(.horizontal, 20)
        .padding(.bottom, 8)
        .background(Token.bgCanvas)
    }
}

private struct ContentAreaView: View {
    let onOpenKnowledgeCardStudy: () -> Void

    var body: some View {
        ScrollView(.vertical, showsIndicators: false) {
            VStack(spacing: 0) {
                GeometryReader { geometry in
                    let ctaWidth: CGFloat = 144
                    let ctaHeight: CGFloat = 48
                    let iconSize: CGFloat = 24

                    ZStack(alignment: .topLeading) {
                        HeroCardCutoutShape()
                            .fill(Token.focusRing)
                            .shadow(
                                color: Token.shadowDownSm.color,
                                radius: Token.shadowDownSm.radius,
                                x: Token.shadowDownSm.x,
                                y: Token.shadowDownSm.y
                            )

                        HeroDecorativeOverlay()
                            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topTrailing)

                        HStack(spacing: 8) {
                            SVGAssetView(name: "icon-hero-spark")
                                .frame(width: 24, height: 24)
                            Text("已完成全部任务，太棒了！")
                                .font(.custom("PingFang SC", size: 16).weight(.medium))
                                .foregroundStyle(Token.textWhite)
                                .lineLimit(1)
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.top, 20)
                        .padding(.horizontal, 20)

                        Text("学有余力？去【学习统计】看看您的知识雷达盲区，或者刷一套历年真题吧。")
                            .font(.custom("PingFang SC", size: 12).weight(.regular))
                            .foregroundStyle(Token.textDisabled)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 8)
                            .background(Token.overlayHeroMask)
                            .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
                            .padding(.top, 56)
                            .padding(.horizontal, 20)

                        HStack(spacing: 24) {
                            HeroMetric(title: "今日学习", value: "24", unit: "min")
                            HeroMetric(title: "连续打卡", value: "27", unit: "day")
                        }
                        .frame(width: 136, alignment: .leading)
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottomLeading)
                        .padding(.leading, 20)
                        .padding(.bottom, 16)

                        Button {
                        } label: {
                            HStack(spacing: 8) {
                                Text("继续学习")
                                    .font(.custom("PingFang SC", size: 16).weight(.medium))
                                    .foregroundStyle(Token.textWhite)
                                FigmaIconView(
                                    name: "icon-play-circle",
                                    outerWidth: iconSize,
                                    outerHeight: iconSize,
                                    innerInsets: PercentInsets(top: 0.0833, right: 0.0833, bottom: 0.0833, left: 0.0833),
                                    imageInsets: PercentInsets(top: -0.0375, right: -0.0375, bottom: -0.0375, left: -0.0375)
                                )
                            }
                            .frame(width: ctaWidth, height: ctaHeight)
                            .background(Token.fgBrand)
                            .clipShape(RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous))
                        }
                        .buttonStyle(.plain)
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottomTrailing)
                    }
                }
                .frame(maxWidth: .infinity)
                .frame(height: 192)

                Spacer().frame(height: 24)

                QuickActionRow()
                    .frame(maxWidth: .infinity)
                    .frame(height: 86)

                Spacer().frame(height: 32)

                TaskSectionView(
                    onOpenKnowledgeCardStudy: onOpenKnowledgeCardStudy
                )
                    .frame(maxWidth: .infinity)

                Spacer().frame(height: 24)
            }
            .padding(.horizontal, 20)
        }
        .background(Token.bgCanvas)
    }
}

private struct HeroCardCutoutShape: Shape {
    var cornerRadius: CGFloat = Token.radiusMd
    var notchWidth: CGFloat = 152
    var notchHeight: CGFloat = 56

    func path(in rect: CGRect) -> Path {
        let notchW = max(0, min(rect.width, notchWidth))
        let notchH = max(0, min(rect.height, notchHeight))
        let radius = min(
            cornerRadius,
            notchW / 2,
            notchH / 2,
            rect.width / 2,
            rect.height / 2
        )

        let x0 = rect.minX
        let y0 = rect.minY
        let x1 = rect.maxX
        let y1 = rect.maxY

        let notchTopY = y1 - notchH
        let notchLeftX = x1 - notchW

        var path = Path()
        path.move(to: CGPoint(x: x0 + radius, y: y0))

        // 外轮廓：上边 -> 右上角 -> 右边
        path.addLine(to: CGPoint(x: x1 - radius, y: y0))
        path.addQuadCurve(
            to: CGPoint(x: x1, y: y0 + radius),
            control: CGPoint(x: x1, y: y0)
        )
        path.addLine(to: CGPoint(x: x1, y: notchTopY - radius))

        // 凹口：右侧拐入 -> 顶边向左 -> 左侧向下（内凹两角）
        path.addQuadCurve(
            to: CGPoint(x: x1 - radius, y: notchTopY),
            control: CGPoint(x: x1, y: notchTopY)
        )
        path.addLine(to: CGPoint(x: notchLeftX + radius, y: notchTopY))
        path.addQuadCurve(
            to: CGPoint(x: notchLeftX, y: notchTopY + radius),
            control: CGPoint(x: notchLeftX, y: notchTopY)
        )
        path.addLine(to: CGPoint(x: notchLeftX, y: y1 - radius))

        // 外轮廓：下边 -> 左下角 -> 左边 -> 左上角闭合
        path.addQuadCurve(
            to: CGPoint(x: notchLeftX - radius, y: y1),
            control: CGPoint(x: notchLeftX, y: y1)
        )
        path.addLine(to: CGPoint(x: x0 + radius, y: y1))
        path.addQuadCurve(
            to: CGPoint(x: x0, y: y1 - radius),
            control: CGPoint(x: x0, y: y1)
        )
        path.addLine(to: CGPoint(x: x0, y: y0 + radius))
        path.addQuadCurve(
            to: CGPoint(x: x0 + radius, y: y0),
            control: CGPoint(x: x0, y: y0)
        )
        path.closeSubpath()
        return path
    }
}

private struct HeroDecorativeOverlay: View {
    var body: some View {
        SVGAssetView(name: "hero-decor-frame-146")
        .frame(width: 255, height: 136)
        .clipped()
        .clipShape(RoundedRectangle(cornerRadius: Token.radiusMd, style: .continuous))
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topTrailing)
    }
}

private enum FigmaFont {
    static func dataXlgDINBold() -> Font {
        let size: CGFloat = 20
        let candidates = [
            "DIN-Bold",
            "DINAlternate-Bold",
            "DIN Alternate Bold",
            "DINCondensed-Bold",
            "DIN Condensed Bold",
            "DIN",
        ]
        for name in candidates where UIFont(name: name, size: size) != nil {
            return .custom(name, size: size)
        }
        return .system(size: size, weight: .bold)
    }
}

private struct HeroMetric: View {
    let title: String
    let value: String
    let unit: String

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text(title)
                .font(.custom("PingFang SC", size: 12).weight(.regular))
                .foregroundStyle(Token.textTertiary)
                .lineLimit(1)
                .frame(height: 20, alignment: .leading)

            HStack(alignment: .lastTextBaseline, spacing: 6) {
                Text(value)
                    .font(FigmaFont.dataXlgDINBold())
                    .foregroundStyle(Token.textWhite)
                    .frame(height: 28, alignment: .bottom)
                Text(unit)
                    .font(.custom("PingFang SC", size: 14).weight(.medium))
                    .foregroundStyle(Token.textWhite)
                    .frame(height: 22, alignment: .bottom)
            }
            .frame(height: 28, alignment: .bottom)
        }
        .frame(width: 56, alignment: .leading)
    }
}

private struct QuickActionRow: View {
    var body: some View {
        HStack(spacing: 16) {
            QuickActionItem(icon: "icon-graduation-hat", title: "每日一练")
            QuickActionItem(icon: "icon-certificate", title: "历年真题")
            QuickActionItem(icon: "icon-atom", title: "考点速记")
            QuickActionItem(icon: "icon-beaker", title: "模拟测试")
        }
        .frame(maxWidth: .infinity)
    }
}

private struct QuickActionItem: View {
    let icon: String
    let title: String

    var body: some View {
        VStack(spacing: 8) {
            ZStack {
                switch icon {
                case "icon-graduation-hat":
                    FigmaIconView(
                        name: icon,
                        outerWidth: 24,
                        outerHeight: 24,
                        innerInsets: PercentInsets(top: 0.1483, right: 0.0833, bottom: 0.1292, left: 0.0833),
                        imageInsets: PercentInsets(top: -0.0577, right: -0.0500, bottom: -0.0577, left: -0.0500),
                        cssVariables: ["stroke-0": Token.fgPrimary]
                    )
                case "icon-certificate":
                    FigmaIconView(
                        name: icon,
                        outerWidth: 24,
                        outerHeight: 24,
                        innerInsets: PercentInsets(top: 0.0833, right: 0.1250, bottom: 0.0833, left: 0.1250),
                        imageInsets: PercentInsets(top: -0.0500, right: -0.0556, bottom: -0.0500, left: -0.0556),
                        cssVariables: ["stroke-0": Token.fgPrimary]
                    )
                case "icon-atom":
                    FigmaIconView(
                        name: icon,
                        outerWidth: 24,
                        outerHeight: 24,
                        innerInsets: PercentInsets(top: 0.1316, right: 0.1299, bottom: 0.1299, left: 0.1316),
                        imageInsets: PercentInsets(top: -0.0564, right: -0.0564, bottom: -0.0564, left: -0.0564),
                        cssVariables: ["stroke-0": Token.fgPrimary]
                    )
                case "icon-beaker":
                    FigmaIconView(
                        name: icon,
                        outerWidth: 24,
                        outerHeight: 24,
                        innerInsets: PercentInsets(top: 0.0833, right: 0.1250, bottom: 0.0833, left: 0.1250),
                        imageInsets: PercentInsets(top: -0.0500, right: -0.0556, bottom: -0.0500, left: -0.0556),
                        cssVariables: ["stroke-0": Token.fgPrimary]
                    )
                default:
                    SVGAssetView(name: icon)
                        .frame(width: 24, height: 24)
                }
            }
            .frame(width: Token.spacing56, height: Token.spacing56)
            .background(Token.bgSubtle)
            .clipShape(RoundedRectangle(cornerRadius: Token.radiusMd, style: .continuous))

            Text(title)
                .font(.custom("PingFang SC", size: 14).weight(.regular))
                .foregroundStyle(Token.textSecondary)
                .lineLimit(1)
        }
        .frame(maxWidth: .infinity)
        .frame(height: 86)
    }
}

private struct TaskSectionView: View {
    let onOpenKnowledgeCardStudy: () -> Void

    private enum TaskType: Int {
        case learning = 0
        case practice = 1
        case review = 2
    }

    private struct TaskItem: Identifiable {
        let id: String
        let type: TaskType
        let status: TaskCardStatus
        let title: String
        let subtitle: String
        let onTap: (() -> Void)?
    }

    private var tasks: [TaskItem] {
        let initial: [TaskItem] = [
            TaskItem(
                id: "learning-task",
                type: .learning,
                status: .notStarted,
                title: "学习任务：项目可行性分析",
                subtitle: "已完成学习",
                onTap: onOpenKnowledgeCardStudy
            ),
            TaskItem(
                id: "practice-task",
                type: .practice,
                status: .notStarted,
                title: "刷题任务",
                subtitle: "进度：17/24",
                onTap: nil
            ),
            TaskItem(
                id: "review-task",
                type: .review,
                status: .notStarted,
                title: "复习任务",
                subtitle: "15 题丨艾宾浩斯濒危错题",
                onTap: nil
            ),
        ]

        return initial.sorted { lhs, rhs in
            let lhsCompleted = lhs.status == .completed
            let rhsCompleted = rhs.status == .completed
            if lhsCompleted != rhsCompleted {
                return !lhsCompleted
            }
            return lhs.type.rawValue < rhs.type.rawValue
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("今日任务")
                    .font(.custom("PingFang SC", size: 20).weight(.semibold))
                    .foregroundStyle(Token.textPrimary)

                Spacer()

                HStack(spacing: 6) {
                    Text("1/3")
                    Text("进行中")
                }
                .font(.custom("PingFang SC", size: 14).weight(.regular))
                .foregroundStyle(Token.textTertiary)
                .padding(.horizontal, 12)
                .frame(height: 28)
                .background(Token.bgSubtle)
                .clipShape(Capsule())
            }
            .frame(height: 30)

            ForEach(tasks) { task in
                TaskCardView(
                    status: task.status,
                    title: task.title,
                    subtitle: task.subtitle,
                    onTap: task.onTap
                )
            }
        }
    }
}

private struct BottomTabBarView: View {
    @Binding var selectedTab: AppTab

    var body: some View {
        HStack(spacing: 24) {
            TabItem(icon: "icon-home-line", label: "学习", active: selectedTab == .study) {
                selectedTab = .study
            }
            TabItem(icon: "icon-bar-chart", label: "统计", active: selectedTab == .stats) {
                selectedTab = .stats
            }
            TabItem(icon: "icon-user", label: "个人中心", active: selectedTab == .profile) {
                selectedTab = .profile
            }
        }
        .padding(.horizontal, 24)
        .padding(.bottom, 0)
        .frame(height: 64, alignment: .bottom)
        .background(Token.bgCanvas)
        .overlay(alignment: .top) {
            Rectangle()
                .fill(Token.borderDefault)
                .frame(height: 1)
        }
    }
}

private struct TabItem: View {
    let icon: String
    let label: String
    let active: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 4) {
                switch icon {
                case "icon-home-line":
                    FigmaIconView(
                        name: icon,
                        outerWidth: 24,
                        outerHeight: 24,
                        innerInsets: PercentInsets(top: 0.0945, right: 0.1250, bottom: 0.1250, left: 0.1250),
                        imageInsets: active
                            ? PercentInsets(top: -0.0534, right: -0.0556, bottom: -0.0534, left: -0.0556)
                            : PercentInsets(top: -0.0400, right: -0.0417, bottom: -0.0400, left: -0.0417),
                        cssVariables: ["stroke-0": active ? Token.fgPrimary : Token.fgDisabled],
                        cssValues: ["stroke-width-0": active ? "2" : "1.5"]
                    )
                case "icon-bar-chart":
                    FigmaIconView(
                        name: icon,
                        outerWidth: 24,
                        outerHeight: 24,
                        innerInsets: PercentInsets(top: 0.1250, right: 0.1250, bottom: 0.1250, left: 0.1250),
                        imageInsets: active
                            ? PercentInsets(top: -0.0556, right: -0.0556, bottom: -0.0556, left: -0.0556)
                            : PercentInsets(top: -0.0417, right: -0.0417, bottom: -0.0417, left: -0.0417),
                        cssVariables: ["stroke-0": active ? Token.fgPrimary : Token.fgDisabled],
                        cssValues: ["stroke-width-0": active ? "2" : "1.5"]
                    )
                case "icon-user":
                    FigmaIconView(
                        name: icon,
                        outerWidth: 24,
                        outerHeight: 24,
                        innerInsets: PercentInsets(top: 0.1250, right: 0.1667, bottom: 0.1250, left: 0.1667),
                        imageInsets: active
                            ? PercentInsets(top: -0.0556, right: -0.0625, bottom: -0.0556, left: -0.0625)
                            : PercentInsets(top: -0.0417, right: -0.0469, bottom: -0.0417, left: -0.0469),
                        cssVariables: ["stroke-0": active ? Token.fgPrimary : Token.fgDisabled],
                        cssValues: ["stroke-width-0": active ? "2" : "1.5"]
                    )
                default:
                    SVGAssetView(name: icon)
                        .frame(width: 24, height: 24)
                }
                Text(label)
                    .font(.custom("PingFang SC", size: 14).weight(active ? .semibold : .regular))
                    .foregroundStyle(active ? Token.textPrimary : Token.textDisabled)
            }
            .frame(maxWidth: .infinity)
        }
        .buttonStyle(.plain)
    }
}

private struct ProfileCenterView: View {
    @Binding var isDarkMode: Bool
    @State private var showClearCacheConfirm = false
    @State private var clearCacheResultMessage: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("个人中心")
                .font(.custom("PingFang SC", size: 20).weight(.semibold))
                .foregroundStyle(Token.textPrimary)

            Toggle(isOn: $isDarkMode) {
                Text("深色模式")
                    .font(.custom("PingFang SC", size: 16).weight(.medium))
                    .foregroundStyle(Token.textPrimary)
            }
            .tint(Token.fgBrand)

            Button {
                showClearCacheConfirm = true
            } label: {
                HStack(spacing: 12) {
                    Text("清除本地缓存")
                        .font(.custom("PingFang SC", size: 16).weight(.medium))
                        .foregroundStyle(Token.textPrimary)
                    Spacer(minLength: 0)
                    Text("清理")
                        .font(.custom("PingFang SC", size: 14).weight(.medium))
                        .foregroundStyle(Token.textWarning)
                }
                .padding(.horizontal, 16)
                .frame(height: 56)
                .background(Token.bgSurface)
                .overlay(
                    RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous)
                        .stroke(Token.borderDefault, lineWidth: 1)
                )
                .clipShape(RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous))
            }
            .buttonStyle(.plain)

            Spacer()
        }
        .padding(.top, 24)
        .padding(.horizontal, 20)
        .background(Token.bgCanvas)
        .alert("清除本地缓存", isPresented: $showClearCacheConfirm) {
            Button("取消", role: .cancel) {}
            Button("清除", role: .destructive) {
                do {
                    GuestUserLocalStore.clearAll()
                    try ContentPackageRemoteStore.clearLocalCache()
                    clearCacheResultMessage = "本地缓存已清除。"
                } catch {
                    clearCacheResultMessage = "清除失败：\(error.localizedDescription)"
                }
            }
        } message: {
            Text("将清除本地学习状态和已下载内容缓存。")
        }
        .alert("清除结果", isPresented: Binding(
            get: { clearCacheResultMessage != nil },
            set: { newValue in
                if !newValue { clearCacheResultMessage = nil }
            }
        )) {
            Button("确定", role: .cancel) { clearCacheResultMessage = nil }
        } message: {
            Text(clearCacheResultMessage ?? "")
        }
    }
}

private struct StatsPlaceholderView: View {
    var body: some View {
        Token.bgCanvas
            .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

private struct HomePageInteractivePreview: View {
    @State private var selectedTab: AppTab = .study
    @State private var isDarkMode = false

    var body: some View {
        HomePageView(selectedTab: $selectedTab, isDarkMode: $isDarkMode)
            .preferredColorScheme(isDarkMode ? .dark : .light)
    }
}

#Preview {
    HomePageInteractivePreview()
}
