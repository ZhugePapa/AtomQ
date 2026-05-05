import SwiftUI
import WebKit

struct SVGAssetView: UIViewRepresentable {
    let name: String
    let cssVariables: [String: Color]

    init(name: String, cssVariables: [String: Color] = [:]) {
        self.name = name
        self.cssVariables = cssVariables
    }

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

        func renderIfNeeded() {
            guard !svgSource.isEmpty else { return }
            let width = max(1, bounds.width)
            let height = max(1, bounds.height)
            let normalizedWidth = (width * 1000).rounded() / 1000
            let normalizedHeight = (height * 1000).rounded() / 1000
            let variableSignature = cssVariables.keys.sorted().map { "\($0)=\(cssVariables[$0] ?? "")" }.joined(separator: ";")
            let signature = "\(svgKey)#\(normalizedWidth)x\(normalizedHeight)#\(variableSignature)"
            guard signature != lastSignature else { return }
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

    func makeUIView(context: Context) -> SVGRenderWebView {
        let config = WKWebViewConfiguration()
        config.allowsInlineMediaPlayback = true

        let webView = SVGRenderWebView(frame: .zero, configuration: config)
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

        webView.svgSource = svg
        webView.svgBaseURL = url.deletingLastPathComponent()
        webView.svgKey = "\(name)-\(url.lastPathComponent)"
        webView.cssVariables = resolveCssVariables(for: webView.traitCollection)
        webView.renderIfNeeded()
    }

    private func resolveURL(for name: String) -> URL? {
        if let url = Bundle.main.url(forResource: name, withExtension: "svg") { return url }
        if let url = Bundle.main.url(forResource: name, withExtension: "svg", subdirectory: "SVG") { return url }
        if let url = Bundle.main.url(forResource: name, withExtension: "svg", subdirectory: "Resources/SVG") { return url }
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
        getRed(&r, green: &g, blue: &b, alpha: &a)
        let red = Int((r * 255).rounded())
        let green = Int((g * 255).rounded())
        let blue = Int((b * 255).rounded())
        return "rgba(\(red), \(green), \(blue), \(a))"
    }
}
