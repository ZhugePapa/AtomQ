import SwiftUI

enum AppTab: String {
    case study
    case stats
    case profile
}

struct HomePageView: View {
    @Binding var selectedTab: AppTab
    @Binding var isDarkMode: Bool

    var body: some View {
        GeometryReader { geometry in
            let canvasWidth = min(geometry.size.width, 390)

            ZStack {
                Token.bgCanvas
                    .ignoresSafeArea()

                VStack(spacing: 0) {
                    Spacer().frame(height: 56)

                    if selectedTab == .study {
                        HeaderView()
                            .frame(maxWidth: .infinity)
                            .frame(height: 62)

                        ContentAreaView()
                            .frame(maxWidth: .infinity, maxHeight: .infinity)
                    } else if selectedTab == .profile {
                        ProfileCenterView(isDarkMode: $isDarkMode)
                            .frame(maxWidth: .infinity, maxHeight: .infinity)
                    } else {
                        StatsPlaceholderView()
                            .frame(maxWidth: .infinity, maxHeight: .infinity)
                    }

                    BottomTabBarView(selectedTab: $selectedTab)
                        .frame(maxWidth: .infinity)
                        .frame(height: 64)
                }
                .frame(width: canvasWidth)
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
            }
        }
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

    init(
        name: String,
        outerWidth: CGFloat,
        outerHeight: CGFloat,
        innerInsets: PercentInsets = .zero,
        imageInsets: PercentInsets = .zero,
        cssVariables: [String: Color] = [:]
    ) {
        self.name = name
        self.outerWidth = outerWidth
        self.outerHeight = outerHeight
        self.innerInsets = innerInsets
        self.imageInsets = imageInsets
        self.cssVariables = cssVariables
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

            SVGAssetView(name: name, cssVariables: cssVariables)
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
                Circle()
                    .fill(Token.fgDanger)
                    .overlay(
                        Circle().stroke(Token.fgWhiteInverse, lineWidth: 1)
                    )
                    .frame(width: 8, height: 8)
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
    var body: some View {
        ScrollView(.vertical, showsIndicators: false) {
            VStack(spacing: 0) {
                HeroCardView()
                    .frame(maxWidth: .infinity)
                    .frame(height: 192)

                Spacer().frame(height: 24)

                QuickActionRow()
                    .frame(maxWidth: .infinity)
                    .frame(height: 86)

                Spacer().frame(height: 32)

                TaskSectionView()
                    .frame(maxWidth: .infinity)

                Spacer().frame(height: 24)
            }
            .padding(.horizontal, 20)
        }
        .background(Token.bgCanvas)
    }
}

private struct HeroCardView: View {
    var body: some View {
        ZStack(alignment: .topLeading) {
            SVGAssetView(
                name: "bg-hero-subtract",
                cssVariables: ["fill-0": Token.focusRing]
            )
                .frame(width: 374, height: 216)
                .offset(x: -12, y: -7)

            HStack(spacing: 8) {
                SVGAssetView(name: "icon-hero-spark")
                    .frame(width: 24, height: 24)
                Text("学习中，坚持就是胜利！")
                    .font(.custom("PingFang SC", size: 16).weight(.medium))
                    .foregroundStyle(Token.textWhite)
                    .lineLimit(1)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.top, 20)
            .padding(.horizontal, 20)

            Text("上次停留：[刷题任务] 十大管理域综合\n进度：第 8 题 / 共 15 题")
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
            .padding(.bottom, 20)

            Button {
            } label: {
                HStack(spacing: 8) {
                    Text("继续学习")
                        .font(.custom("PingFang SC", size: 16).weight(.medium))
                        .foregroundStyle(Token.textWhite)
                    FigmaIconView(
                        name: "icon-play-circle",
                        outerWidth: 24,
                        outerHeight: 24,
                        innerInsets: PercentInsets(top: 0.0833, right: 0.0833, bottom: 0.0833, left: 0.0833),
                        imageInsets: PercentInsets(top: -0.0375, right: -0.0375, bottom: -0.0375, left: -0.0375)
                    )
                }
                .frame(height: Token.spacing48)
                .padding(.horizontal, 24)
                .background(Token.fgBrand)
                .clipShape(RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous))
            }
            .buttonStyle(.plain)
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottomTrailing)
        }
        .clipShape(RoundedRectangle(cornerRadius: Token.radiusMd, style: .continuous))
        .shadow(color: Token.shadowDownSm.color, radius: Token.shadowDownSm.radius, x: Token.shadowDownSm.x, y: Token.shadowDownSm.y)
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
                    .font(.custom("DIN", size: 20).weight(.medium))
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
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("今日任务")
                    .font(.custom("PingFang SC", size: 20).weight(.semibold))
                    .foregroundStyle(Token.textPrimary)

                Spacer()

                HStack(spacing: 6) {
                    Text("1/3")
                    Text("已完成")
                }
                .font(.custom("PingFang SC", size: 14).weight(.medium))
                .foregroundStyle(Token.textTertiary)
                .padding(.horizontal, 12)
                .frame(height: 28)
                .background(Token.bgSubtle)
                .clipShape(Capsule())
            }
            .frame(height: 30)

            TaskCardInProgress()
            TaskCardPending()
            TaskCardCompleted()
        }
    }
}

private struct TaskCardInProgress: View {
    var body: some View {
        HStack(spacing: 16) {
            SVGAssetView(
                name: "icon-uncheck-progress",
                cssVariables: [
                    "stroke-0": Token.borderWarning,
                    "stroke-1": Token.fgWarning,
                ]
            )
                .frame(width: 24, height: 24)

            VStack(alignment: .leading, spacing: 4) {
                Text("刷题任务")
                    .font(.custom("PingFang SC", size: 16).weight(.semibold))
                    .foregroundStyle(Token.textPrimary)
                Text("进度：17/24")
                    .font(.custom("PingFang SC", size: 14).weight(.regular))
                    .foregroundStyle(Token.textTertiary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)

            HStack(spacing: 8) {
                Text("继续")
                    .font(.custom("PingFang SC", size: 16).weight(.medium))
                    .foregroundStyle(Token.textWhite)
                FigmaIconView(
                    name: "icon-arrow-forward",
                    outerWidth: 16,
                    outerHeight: 16,
                    innerInsets: PercentInsets(top: 0.2188, right: 0.1953, bottom: 0.2188, left: 0.1953),
                    imageInsets: PercentInsets(top: -0.0833, right: -0.0769, bottom: -0.0833, left: -0.0769)
                )
            }
            .padding(.horizontal, 16)
            .frame(height: 36)
            .background(Token.fgWarning)
            .clipShape(Capsule())
        }
        .padding(.horizontal, 20)
        .frame(maxWidth: .infinity)
        .frame(height: 82)
        .background(Token.fgWarningSubtle)
        .overlay(
            RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous)
                .stroke(Token.borderWarning, lineWidth: 1)
        )
        .clipShape(RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous))
    }
}

private struct TaskCardPending: View {
    var body: some View {
        HStack(spacing: 16) {
            FigmaIconView(
                name: "icon-uncheck-outline",
                outerWidth: 24,
                outerHeight: 24,
                innerInsets: PercentInsets(top: 0.0833, right: 0.0833, bottom: 0.0833, left: 0.0833),
                imageInsets: PercentInsets(top: -0.0500, right: -0.0500, bottom: -0.0500, left: -0.0500),
                cssVariables: ["stroke-0": Token.borderStrong]
            )

            VStack(alignment: .leading, spacing: 4) {
                Text("复习任务")
                    .font(.custom("PingFang SC", size: 16).weight(.semibold))
                    .foregroundStyle(Token.textPrimary)
                Text("15 题丨艾宾浩斯濒危错题")
                    .font(.custom("PingFang SC", size: 14).weight(.regular))
                    .foregroundStyle(Token.textTertiary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)

            FigmaIconView(
                name: "icon-chevron-forward",
                outerWidth: 16,
                outerHeight: 16,
                innerInsets: PercentInsets(top: 0.2188, right: 0.3594, bottom: 0.2188, left: 0.3594),
                imageInsets: PercentInsets(top: -0.0833, right: -0.1667, bottom: -0.0833, left: -0.1667),
                cssVariables: ["stroke-0": Token.fgTertiary]
            )
        }
        .padding(.horizontal, 20)
        .frame(maxWidth: .infinity)
        .frame(height: 82)
        .background(Token.bgSurface)
        .overlay(
            RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous)
                .stroke(Token.borderDefault, lineWidth: 1)
        )
        .clipShape(RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous))
    }
}

private struct TaskCardCompleted: View {
    var body: some View {
        HStack(spacing: 16) {
            FigmaIconView(
                name: "icon-check-circle",
                outerWidth: 24,
                outerHeight: 24,
                innerInsets: PercentInsets(top: 0.0833, right: 0.0833, bottom: 0.0833, left: 0.0833),
                imageInsets: PercentInsets(top: -0.0500, right: -0.0500, bottom: -0.0500, left: -0.0500),
                cssVariables: ["stroke-0": Token.fgSuccessSecondary]
            )

            VStack(alignment: .leading, spacing: 4) {
                Text("学习任务：项目可行性分析")
                    .font(.custom("PingFang SC", size: 16).weight(.semibold))
                    .foregroundStyle(Token.textDisabled)
                    .strikethrough(true, color: Token.textDisabled)
                    .lineLimit(1)
                Text("已完成学习")
                    .font(.custom("PingFang SC", size: 14).weight(.regular))
                    .foregroundStyle(Token.textDisabled)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(.horizontal, 20)
        .frame(maxWidth: .infinity)
        .frame(height: 82)
        .background(Token.bgTaskSubtle)
        .overlay(
            RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous)
                .stroke(Token.borderDefault, lineWidth: 1)
        )
        .clipShape(RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous))
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
                        imageInsets: PercentInsets(top: -0.0534, right: -0.0556, bottom: -0.0534, left: -0.0556),
                        cssVariables: ["stroke-0": active ? Token.fgPrimary : Token.fgDisabled]
                    )
                case "icon-bar-chart":
                    FigmaIconView(
                        name: icon,
                        outerWidth: 24,
                        outerHeight: 24,
                        innerInsets: PercentInsets(top: 0.1250, right: 0.1250, bottom: 0.1250, left: 0.1250),
                        imageInsets: PercentInsets(top: -0.0417, right: -0.0417, bottom: -0.0417, left: -0.0417),
                        cssVariables: ["stroke-0": active ? Token.fgPrimary : Token.fgDisabled]
                    )
                case "icon-user":
                    FigmaIconView(
                        name: icon,
                        outerWidth: 24,
                        outerHeight: 24,
                        innerInsets: PercentInsets(top: 0.1250, right: 0.1667, bottom: 0.1250, left: 0.1667),
                        imageInsets: PercentInsets(top: -0.0417, right: -0.0469, bottom: -0.0417, left: -0.0469),
                        cssVariables: ["stroke-0": active ? Token.fgPrimary : Token.fgDisabled]
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

            Spacer()
        }
        .padding(.top, 24)
        .padding(.horizontal, 20)
        .background(Token.bgCanvas)
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
