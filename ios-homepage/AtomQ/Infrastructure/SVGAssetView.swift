import SwiftUI
import UIKit
import WebKit

struct SVGAssetView: View {
    let name: String
    let cssVariables: [String: Color]
    let cssValues: [String: String]

    init(name: String, cssVariables: [String: Color] = [:], cssValues: [String: String] = [:]) {
        self.name = name
        self.cssVariables = cssVariables
        self.cssValues = cssValues
    }

    var body: some View {
        SVGWebAssetView(name: name, cssVariables: cssVariables, cssValues: cssValues)
            .allowsHitTesting(false)
    }
}

private struct SVGWebAssetView: UIViewRepresentable {
    let name: String
    let cssVariables: [String: Color]
    let cssValues: [String: String]
    private static var resolvedURLCache: [String: URL] = [:]

    final class SVGRenderWebView: WKWebView {
        var svgSource: String = ""
        var svgBaseURL: URL?
        var svgKey: String = ""
        var cssVariables: [String: String] = [:]
        var lastSignature: String = ""

        override func layoutSubviews() {
            super.layoutSubviews()
            renderIfNeeded()
        }

        func renderIfNeeded(force: Bool = false) {
            guard !svgSource.isEmpty else { return }
            let width = max(1, bounds.width)
            let height = max(1, bounds.height)
            let normalizedWidth = (width * 1000).rounded() / 1000
            let normalizedHeight = (height * 1000).rounded() / 1000
            let variableSignature = cssVariables.keys.sorted().map { "\($0)=\(cssVariables[$0] ?? "")" }.joined(separator: ";")
            let signature = "\(svgKey)#\(normalizedWidth)x\(normalizedHeight)#\(variableSignature)"
            guard force || signature != lastSignature else { return }
            lastSignature = signature

            let widthPx = String(format: "%.3f", normalizedWidth)
            let heightPx = String(format: "%.3f", normalizedHeight)
            let cssVariableText = cssVariables.keys.sorted().map { key in
                "--\(key): \(cssVariables[key] ?? "transparent");"
            }.joined(separator: "\n")

            let html = """
            <!doctype html>
            <html>
            <head>
              <meta charset=\"utf-8\" />
              <meta name=\"viewport\" content=\"width=\(widthPx), height=\(heightPx), initial-scale=1, maximum-scale=1, user-scalable=no\" />
              <style>
                html, body {
                  margin: 0;
                  padding: 0;
                  width: \(widthPx)px;
                  height: \(heightPx)px;
                  overflow: hidden;
                  background: transparent;
                  -webkit-text-size-adjust: 100%;
                }
                #root {
                  position: relative;
                  width: 100%;
                  height: 100%;
                  overflow: hidden;
                }
                #root > svg {
                  position: absolute;
                  inset: 0;
                  display: block;
                }
                :root {
                  \(cssVariableText)
                }
              </style>
            </head>
            <body>
              <div id=\"root\">\(svgSource)</div>
            </body>
            </html>
            """

            loadHTMLString(html, baseURL: svgBaseURL)
        }
    }

    final class Coordinator: NSObject, WKNavigationDelegate {
        func webViewWebContentProcessDidTerminate(_ webView: WKWebView) {
            (webView as? SVGRenderWebView)?.renderIfNeeded(force: true)
        }

        func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: any Error) {
            (webView as? SVGRenderWebView)?.renderIfNeeded(force: true)
        }

        func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: any Error) {
            (webView as? SVGRenderWebView)?.renderIfNeeded(force: true)
        }
    }

    func makeCoordinator() -> Coordinator {
        Coordinator()
    }

    func makeUIView(context: Context) -> SVGRenderWebView {
        let config = WKWebViewConfiguration()
        config.allowsInlineMediaPlayback = true

        let webView = SVGRenderWebView(frame: .zero, configuration: config)
        webView.navigationDelegate = context.coordinator
        webView.isOpaque = false
        webView.backgroundColor = .clear
        webView.scrollView.isScrollEnabled = false
        webView.scrollView.backgroundColor = .clear
        webView.scrollView.bounces = false
        webView.scrollView.contentInsetAdjustmentBehavior = .never
        webView.isUserInteractionEnabled = false
        return webView
    }

    func updateUIView(_ webView: SVGRenderWebView, context: Context) {
        guard let url = resolveURL(for: name),
              let svg = try? String(contentsOf: url, encoding: .utf8) else {
            return
        }

        let colorScheme = context.environment.colorScheme
        let style: UIUserInterfaceStyle = colorScheme == .dark ? .dark : .light
        let forcedTrait = UITraitCollection(userInterfaceStyle: style)
        webView.overrideUserInterfaceStyle = style

        webView.svgSource = svg
        webView.svgBaseURL = nil
        webView.svgKey = "\(name)-\(url.lastPathComponent)"
        var resolvedVariables = resolveCssVariables(for: forcedTrait)
        for (name, value) in cssValues {
            resolvedVariables[name] = value
        }
        webView.cssVariables = resolvedVariables
        webView.renderIfNeeded()
    }

    private func resolveURL(for name: String) -> URL? {
        if let cached = Self.resolvedURLCache[name] {
            return cached
        }

        let fileName = "\(name).svg"
        let candidateBundles = Array(
            Set(
                [Bundle.main, Bundle(for: SVGRenderWebView.self)] +
                Bundle.allBundles +
                Bundle.allFrameworks
            )
        )

        for bundle in candidateBundles {
            if let url = bundle.url(forResource: name, withExtension: "svg") {
                Self.resolvedURLCache[name] = url
                return url
            }
            if let url = bundle.url(forResource: name, withExtension: "svg", subdirectory: "SVG") {
                Self.resolvedURLCache[name] = url
                return url
            }
            if let url = bundle.url(forResource: name, withExtension: "svg", subdirectory: "Resources/SVG") {
                Self.resolvedURLCache[name] = url
                return url
            }

            guard let resourceURL = bundle.resourceURL else { continue }
            let direct = resourceURL.appendingPathComponent(fileName)
            if FileManager.default.fileExists(atPath: direct.path) {
                Self.resolvedURLCache[name] = direct
                return direct
            }

            let svgDir = resourceURL.appendingPathComponent("SVG").appendingPathComponent(fileName)
            if FileManager.default.fileExists(atPath: svgDir.path) {
                Self.resolvedURLCache[name] = svgDir
                return svgDir
            }

            let nestedDir = resourceURL
                .appendingPathComponent("Resources")
                .appendingPathComponent("SVG")
                .appendingPathComponent(fileName)
            if FileManager.default.fileExists(atPath: nestedDir.path) {
                Self.resolvedURLCache[name] = nestedDir
                return nestedDir
            }
        }

        let sourceRootResourcePath = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .appendingPathComponent("Resources")
            .appendingPathComponent("SVG")
            .appendingPathComponent(fileName)
        if FileManager.default.fileExists(atPath: sourceRootResourcePath.path) {
            Self.resolvedURLCache[name] = sourceRootResourcePath
            return sourceRootResourcePath
        }

        return nil
    }

    private func resolveCssVariables(for traitCollection: UITraitCollection) -> [String: String] {
        var resolved: [String: String] = [:]
        for (name, color) in cssVariables {
            let uiColor = UIColor(color).resolvedColor(with: traitCollection)
            resolved[name] = uiColor.cssRGBAString
        }
        return resolved
    }
}

private extension UIColor {
    var cssRGBAString: String {
        var r: CGFloat = 0
        var g: CGFloat = 0
        var b: CGFloat = 0
        var a: CGFloat = 0
        if getRed(&r, green: &g, blue: &b, alpha: &a) {
            let red = Int((r * 255).rounded())
            let green = Int((g * 255).rounded())
            let blue = Int((b * 255).rounded())
            return "rgba(\(red), \(green), \(blue), \(a))"
        }

        guard
            let sRGB = CGColorSpace(name: CGColorSpace.sRGB),
            let converted = cgColor.converted(to: sRGB, intent: .defaultIntent, options: nil),
            let components = converted.components
        else {
            return "rgba(0, 0, 0, 1)"
        }

        switch components.count {
        case 4:
            let red = Int((components[0] * 255).rounded())
            let green = Int((components[1] * 255).rounded())
            let blue = Int((components[2] * 255).rounded())
            let alpha = max(0, min(1, components[3]))
            return "rgba(\(red), \(green), \(blue), \(alpha))"
        case 2:
            let gray = Int((components[0] * 255).rounded())
            let alpha = max(0, min(1, components[1]))
            return "rgba(\(gray), \(gray), \(gray), \(alpha))"
        default:
            return "rgba(0, 0, 0, 1)"
        }
    }
}
