import SwiftUI
import UIKit

enum Token {
    static let bgCanvas = Color(lightHex: "#ffffff", darkHex: "#0b111a")
    static let bgSurface = Color(lightHex: "#ffffff", darkHex: "#121b26")
    static let bgSubtle = Color(lightHex: "#f7f9fb", darkHex: "#1b2533")
    static let bgTaskSubtle = Color(lightHex: "#ffffff", darkHex: "#0b111a")
    static let textPrimary = Color(lightHex: "#121b26", darkHex: "#f3f4f6")
    static let textSecondary = Color(lightHex: "#404c63", darkHex: "#c2ccd8")
    static let textTertiary = Color(lightHex: "#6e7e94", darkHex: "#6e7e94")
    static let textDisabled = Color(lightHex: "#c2ccd8", darkHex: "#404c63")
    static let textWhite = Color(lightHex: "#ffffff", darkHex: "#ffffff")
    static let textBrand = Color(lightHex: "#1362fe", darkHex: "#1362fe")

    static let borderDefault = Color(lightHex: "#e9edf2", darkHex: "#2f3c4f")
    static let borderStrong = Color(lightHex: "#d9e0e8", darkHex: "#404c63")
    static let borderWarning = Color(lightHex: "#ffe5cf", darkHex: "#a13913")

    static let fgPrimary = Color(lightHex: "#121b26", darkHex: "#f3f4f6")
    static let fgWarning = Color(lightHex: "#fd5e0d", darkHex: "#fd5e0d")
    static let fgWarningSubtle = Color(lightHex: "#fff5ec", darkHex: "#452019")
    static let fgBrand = Color(lightHex: "#1362fe", darkHex: "#1362fe")
    static let fgSuccessSecondary = Color(lightHex: "#a5e5bb", darkHex: "#1c7c4e")
    static let fgDanger = Color(lightHex: "#f6285f", darkHex: "#f6285f")
    static let fgDisabled = Color(lightHex: "#d9e0e8", darkHex: "#404c63")
    static let fgTertiary = Color(lightHex: "#6e7e94", darkHex: "#6e7e94")
    static let fgWhiteInverse = Color(lightHex: "#ffffff", darkHex: "#1b2533")
    static let focusRing = Color(lightHex: "#071947", darkHex: "#1c2839")

    static let overlayHeroMask = Color(lightHex: "#000000", darkHex: "#000000").opacity(0.20)
    static let overlaySoft = Color.black.opacity(0.05)
    static let shadowDownSm = ShadowSpec(color: overlaySoft, x: 0, y: 5, radius: 12)

    static let radiusSm: CGFloat = 12
    static let radiusMd: CGFloat = 16
    static let radiusFull: CGFloat = 999

    static let spacing24: CGFloat = 24
    static let spacing48: CGFloat = 48
    static let spacing56: CGFloat = 56
}

struct ShadowSpec {
    let color: Color
    let x: CGFloat
    let y: CGFloat
    let radius: CGFloat
}

extension Color {
    init(hex: String) {
        let cleaned = hex.replacingOccurrences(of: "#", with: "")
        var value: UInt64 = 0
        Scanner(string: cleaned).scanHexInt64(&value)

        let r, g, b: Double
        switch cleaned.count {
        case 6:
            r = Double((value & 0xFF0000) >> 16) / 255.0
            g = Double((value & 0x00FF00) >> 8) / 255.0
            b = Double(value & 0x0000FF) / 255.0
        default:
            r = 0
            g = 0
            b = 0
        }

        self.init(.sRGB, red: r, green: g, blue: b, opacity: 1)
    }

    init(lightHex: String, darkHex: String) {
        let light = UIColor(lightHex)
        let dark = UIColor(darkHex)
        self.init(UIColor { trait in
            trait.userInterfaceStyle == .dark ? dark : light
        })
    }
}

extension UIColor {
    convenience init(_ hex: String) {
        let cleaned = hex.replacingOccurrences(of: "#", with: "")
        var value: UInt64 = 0
        Scanner(string: cleaned).scanHexInt64(&value)

        let r, g, b: CGFloat
        switch cleaned.count {
        case 6:
            r = CGFloat((value & 0xFF0000) >> 16) / 255.0
            g = CGFloat((value & 0x00FF00) >> 8) / 255.0
            b = CGFloat(value & 0x0000FF) / 255.0
        default:
            r = 0
            g = 0
            b = 0
        }

        self.init(red: r, green: g, blue: b, alpha: 1)
    }
}
