import SwiftUI

enum TaskCardStatus {
    case notStarted
    case inProgress
    case completed
}

struct TaskCardView: View {
    let status: TaskCardStatus
    let title: String
    let subtitle: String
    var onTap: (() -> Void)? = nil
    @GestureState private var isPressed = false

    var body: some View {
        Button {
            onTap?()
        } label: {
            HStack(spacing: 16) {
                leadingIcon

                VStack(alignment: .leading, spacing: 4) {
                    Text(title)
                        .font(.custom("PingFang SC", size: 16).weight(.semibold))
                        .foregroundStyle(titleColor)
                        .strikethrough(status == .completed, color: Token.textDisabled)
                        .lineLimit(1)
                    Text(subtitle)
                        .font(.custom("PingFang SC", size: 14).weight(.regular))
                        .foregroundStyle(subtitleColor)
                        .lineLimit(1)
                }
                .frame(maxWidth: .infinity, alignment: .leading)

                trailingContent
            }
            .padding(.horizontal, 20)
            .frame(maxWidth: .infinity)
            .frame(height: 82)
            .background(effectiveCardBackground)
            .overlay(
                RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous)
                    .stroke(cardBorder, lineWidth: 1)
            )
            .clipShape(RoundedRectangle(cornerRadius: Token.radiusSm, style: .continuous))
        }
        .buttonStyle(.plain)
        .simultaneousGesture(
            DragGesture(minimumDistance: 0)
                .updating($isPressed) { _, state, _ in
                    state = true
                }
        )
    }

    @ViewBuilder
    private var leadingIcon: some View {
        switch status {
        case .notStarted:
            TaskFigmaIconView(
                name: "icon-uncheck-outline",
                outerWidth: 24,
                outerHeight: 24,
                innerInsets: TaskPercentInsets(top: 0.0833, right: 0.0833, bottom: 0.0833, left: 0.0833),
                imageInsets: TaskPercentInsets(top: -0.0500, right: -0.0500, bottom: -0.0500, left: -0.0500),
                cssVariables: ["stroke-0": Token.borderStrong]
            )
        case .inProgress:
            SVGAssetView(
                name: "icon-uncheck-progress",
                cssVariables: [
                    "stroke-0": Token.borderWarning,
                    "stroke-1": Token.fgWarning,
                ]
            )
            .frame(width: 24, height: 24)
        case .completed:
            TaskFigmaIconView(
                name: "icon-check-circle",
                outerWidth: 24,
                outerHeight: 24,
                innerInsets: TaskPercentInsets(top: 0.0833, right: 0.0833, bottom: 0.0833, left: 0.0833),
                imageInsets: TaskPercentInsets(top: -0.0500, right: -0.0500, bottom: -0.0500, left: -0.0500),
                cssVariables: ["stroke-0": Token.fgSuccessSecondary]
            )
        }
    }

    @ViewBuilder
    private var trailingContent: some View {
        switch status {
        case .notStarted:
            TaskFigmaIconView(
                name: "icon-chevron-forward",
                outerWidth: 16,
                outerHeight: 16,
                innerInsets: TaskPercentInsets(top: 0.2188, right: 0.3594, bottom: 0.2188, left: 0.3594),
                imageInsets: TaskPercentInsets(top: -0.0833, right: -0.1667, bottom: -0.0833, left: -0.1667),
                cssVariables: ["stroke-0": Token.fgTertiary]
            )
        case .inProgress:
            HStack(spacing: 8) {
                Text("继续")
                    .font(.custom("PingFang SC", size: 16).weight(.medium))
                    .foregroundStyle(Token.textWhite)
                TaskFigmaIconView(
                    name: "icon-arrow-forward",
                    outerWidth: 16,
                    outerHeight: 16,
                    innerInsets: TaskPercentInsets(top: 0.2188, right: 0.1953, bottom: 0.2188, left: 0.1953),
                    imageInsets: TaskPercentInsets(top: -0.0833, right: -0.0769, bottom: -0.0833, left: -0.0769)
                )
            }
            .padding(.horizontal, 16)
            .frame(height: 36)
            .background(Token.fgWarning)
            .clipShape(Capsule())
        case .completed:
            EmptyView()
        }
    }

    private var titleColor: Color {
        status == .completed ? Token.textDisabled : Token.textPrimary
    }

    private var subtitleColor: Color {
        status == .completed ? Token.textDisabled : Token.textTertiary
    }

    private var cardBackground: Color {
        switch status {
        case .inProgress:
            return Token.fgWarningSubtle
        case .completed:
            return Token.bgTaskSubtle
        case .notStarted:
            return Token.bgSurface
        }
    }

    private var effectiveCardBackground: Color {
        if status == .notStarted && isPressed {
            return Token.bgSubtle
        }
        return cardBackground
    }

    private var cardBorder: Color {
        status == .inProgress ? Token.borderWarning : Token.borderDefault
    }
}

private struct TaskPercentInsets {
    let top: CGFloat
    let right: CGFloat
    let bottom: CGFloat
    let left: CGFloat

    static let zero = TaskPercentInsets(top: 0, right: 0, bottom: 0, left: 0)
}

private struct TaskFigmaIconView: View {
    let name: String
    let outerWidth: CGFloat
    let outerHeight: CGFloat
    let innerInsets: TaskPercentInsets
    let imageInsets: TaskPercentInsets
    let cssVariables: [String: Color]
    let cssValues: [String: String]

    init(
        name: String,
        outerWidth: CGFloat,
        outerHeight: CGFloat,
        innerInsets: TaskPercentInsets = .zero,
        imageInsets: TaskPercentInsets = .zero,
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
