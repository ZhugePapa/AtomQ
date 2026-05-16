import SwiftUI
import UIKit

enum Token {
    static let bgCanvas = Color(lightHex: "#ffffff", darkHex: "#0b111a")
    static let bgSecondary = Color(lightHex: "#f8fafc", darkHex: "#1b2533")
    static let bgSurface = Color(lightHex: "#ffffff", darkHex: "#121b26")
    static let bgSubtle = Color(lightHex: "#f8fafc", darkHex: "#1b2533")
    static let bgSubtleAlt = Color(lightHex: "#f8fafc", darkHex: "#1b2533")
    static let bgSubtle2 = Color(lightHex: "#f3f5f8", darkHex: "#2f3c4f")
    static let bgTertiary = Color(lightHex: "#f7f9fb", darkHex: "#1b2533")
    static let bgTaskSubtle = Color(lightHex: "#ffffff", darkHex: "#0b111a")
    static let textPrimary = Color(lightHex: "#121b26", darkHex: "#f3f5f8")
    static let textSecondary = Color(lightHex: "#404c63", darkHex: "#d9e0e8")
    static let textTertiary = Color(lightHex: "#6e7e94", darkHex: "#97a6b8")
    static let textDisabled = Color(lightHex: "#c2ccd8", darkHex: "#536279")
    static let textWhite = Color(lightHex: "#ffffff", darkHex: "#ffffff")
    static let textBrand = Color(lightHex: "#1362fe", darkHex: "#1362fe")
    static let textWarning = Color(lightHex: "#fd5e0d", darkHex: "#fd5e0d")

    static let borderDefault = Color(lightHex: "#e9edf2", darkHex: "#2f3c4f")
    static let borderStrong = Color(lightHex: "#d9e0e8", darkHex: "#404c63")
    static let borderWarning = Color(lightHex: "#ffe5cf", darkHex: "#a13913")

    static let fgPrimary = Color(lightHex: "#121b26", darkHex: "#f3f5f8")
    static let fgWarning = Color(lightHex: "#fd5e0d", darkHex: "#fd5e0d")
    static let fgWarningSubtle = Color(lightHex: "#fff5ec", darkHex: "#452019")
    static let fgDangerSubtle = Color(lightHex: "#feeef0", darkHex: "#441b2e")
    static let fgBrand = Color(lightHex: "#1362fe", darkHex: "#1362fe")
    static let fgBrandSubtle = Color(lightHex: "#ecf5ff", darkHex: "#162049")
    static let fgBrandSecondary = Color(lightHex: "#71aafe", darkHex: "#153aa4")
    static let fgSuccess = Color(lightHex: "#1fbe65", darkHex: "#1fbe65")
    static let fgSuccessSecondary = Color(lightHex: "#79d89d", darkHex: "#1c7c4e")
    static let fgDanger = Color(lightHex: "#f6285f", darkHex: "#f6285f")
    static let fgAssist = Color(lightHex: "#894cf3", darkHex: "#894cf3")
    static let fgDisabled = Color(lightHex: "#d9e0e8", darkHex: "#404c63")
    static let fgTertiary = Color(lightHex: "#6e7e94", darkHex: "#6e7e94")
    static let fgWhite = Color(lightHex: "#ffffff", darkHex: "#ffffff")
    static let fgWhiteInverse = Color(lightHex: "#ffffff", darkHex: "#1b2533")
    static let componentsCard = Color(lightHex: "#071947", darkHex: "#1c2839")
    static let focusRing = componentsCard
    static let componentsAlpha0 = Color(
        UIColor { trait in
            trait.userInterfaceStyle == .dark
                ? UIColor(red: 11 / 255, green: 17 / 255, blue: 26 / 255, alpha: 0)
                : UIColor(red: 1, green: 1, blue: 1, alpha: 0)
        }
    )
    static let componentsAlpha100 = Color(
        UIColor { trait in
            trait.userInterfaceStyle == .dark
                ? UIColor(red: 11 / 255, green: 17 / 255, blue: 26 / 255, alpha: 1)
                : UIColor(red: 1, green: 1, blue: 1, alpha: 1)
        }
    )
    static let componentsEmphasisInvisible = Color(lightHex: "#e9edf2", darkHex: "#404c63")

    static let overlayHeroMask = Color(
        UIColor { trait in
            if trait.userInterfaceStyle == .dark {
                return UIColor(red: 0, green: 0, blue: 0, alpha: 0.24)
            }
            return UIColor(red: 1, green: 1, blue: 1, alpha: 0.12)
        }
    )
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

// MARK: - Color extensions

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
            r = 0; g = 0; b = 0
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
            r = 0; g = 0; b = 0
        }
        self.init(red: r, green: g, blue: b, alpha: 1)
    }

    var cssRGBAString: String {
        var r: CGFloat = 0, g: CGFloat = 0, b: CGFloat = 0, a: CGFloat = 0
        if getRed(&r, green: &g, blue: &b, alpha: &a) {
            return "rgba(\(Int((r*255).rounded())), \(Int((g*255).rounded())), \(Int((b*255).rounded())), \(a))"
        }
        guard let sRGB = CGColorSpace(name: CGColorSpace.sRGB),
              let converted = cgColor.converted(to: sRGB, intent: .defaultIntent, options: nil),
              let components = converted.components
        else { return "rgba(0, 0, 0, 1)" }
        switch components.count {
        case 4:
            return "rgba(\(Int((components[0]*255).rounded())), \(Int((components[1]*255).rounded())), \(Int((components[2]*255).rounded())), \(max(0, min(1, components[3]))))"
        case 2:
            return "rgba(\(Int((components[0]*255).rounded())), \(Int((components[0]*255).rounded())), \(Int((components[0]*255).rounded())), \(max(0, min(1, components[1]))))"
        default:
            return "rgba(0, 0, 0, 1)"
        }
    }
}
