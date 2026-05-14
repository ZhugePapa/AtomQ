import SwiftUI
import UIKit
import WebKit

// MARK: - SVG Image Cache

private enum SVGImageCache {
    private static let lock = NSLock()
    private static var cache: [String: UIImage] = [:]

    static func image(forKey key: String) -> UIImage? {
        lock.lock(); defer { lock.unlock() }
        return cache[key]
    }

    static func setImage(_ image: UIImage, forKey key: String) {
        lock.lock(); defer { lock.unlock() }
        cache[key] = image
    }
}

// MARK: - SVGAssetView (public API unchanged)

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
        SVGRenderView(name: name, cssVariables: cssVariables, cssValues: cssValues)
            .allowsHitTesting(false)
    }
}

// MARK: - SVG Render View (cached image with WKWebView fallback)

private struct SVGRenderView: View {
    let name: String
    let cssVariables: [String: Color]
    let cssValues: [String: String]

    @State private var cachedImage: UIImage?

    var body: some View {
        GeometryReader { geometry in
            let width = geometry.size.width
            let height = geometry.size.height

            if width > 0, height > 0 {
                let cacheKey = makeCacheKey(name: name, width: width, height: height, cssVariables: cssVariables, cssValues: cssValues)

                // Check in-memory state first, then global cache
                if let image = cachedImage ?? SVGImageCache.image(forKey: cacheKey) {
                    Image(uiImage: image)
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .frame(width: width, height: height)
                        .onAppear { cachedImage = image }
                } else {
                    SVGWebAssetView(
                        name: name,
                        cssVariables: cssVariables,
                        cssValues: cssValues,
                        cacheKey: cacheKey,
                        onImageCached: { cachedImage = $0 }
                    )
                    .frame(width: width, height: height)
                }
            }
        }
    }

    private func makeCacheKey(
        name: String,
        width: CGFloat,
        height: CGFloat,
        cssVariables: [String: Color],
        cssValues: [String: String]
    ) -> String {
        let varPart = cssVariables.keys.sorted().map { "\($0)=\(cssVariables[$0]?.description ?? "")" }.joined(separator: ",")
        let valPart = cssValues.keys.sorted().map { "\($0)=\(cssValues[$0] ?? "")" }.joined(separator: ",")
        let w = String(format: "%.0f", width)
        let h = String(format: "%.0f", height)
        return "\(name)|\(w)x\(h)|\(varPart)|\(valPart)"
    }
}

// MARK: - WKWebView-based SVG renderer (only created on cache miss)

private struct SVGWebAssetView: UIViewRepresentable {
    let name: String
    let cssVariables: [String: Color]
    let cssValues: [String: String]
    let cacheKey: String
    let onImageCached: (UIImage) -> Void

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
              <meta charset="utf-8" />
              <meta name="viewport" content="width=\(widthPx), height=\(heightPx), initial-scale=1, maximum-scale=1, user-scalable=no" />
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
              <div id="root">\(svgSource)</div>
            </body>
            </html>
            """

            loadHTMLString(html, baseURL: svgBaseURL)
        }
    }

    final class Coordinator: NSObject, WKNavigationDelegate {
        let parent: SVGWebAssetView

        init(_ parent: SVGWebAssetView) {
            self.parent = parent
        }

        func webViewWebContentProcessDidTerminate(_ webView: WKWebView) {
            (webView as? SVGRenderWebView)?.renderIfNeeded(force: true)
        }

        func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: any Error) {
            (webView as? SVGRenderWebView)?.renderIfNeeded(force: true)
        }

        func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: any Error) {
            (webView as? SVGRenderWebView)?.renderIfNeeded(force: true)
        }

        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            // Wait for SVG to paint, then snapshot and cache
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.02) {
                let config = WKSnapshotConfiguration()
                config.rect = CGRect(origin: .zero, size: webView.bounds.size)
                webView.takeSnapshot(with: config) { image, _ in
                    guard let image else { return }
                    SVGImageCache.setImage(image, forKey: self.parent.cacheKey)
                    self.parent.onImageCached(image)
                }
            }
        }
    }

    func makeCoordinator() -> Coordinator {
        Coordinator(self)
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

// MARK: - Shared SVG Icon Component

struct SvgIconInsets {
    let top: CGFloat
    let right: CGFloat
    let bottom: CGFloat
    let left: CGFloat
    static let zero = SvgIconInsets(top: 0, right: 0, bottom: 0, left: 0)
}

struct SvgIconView: View {
    let name: String
    let outerWidth: CGFloat
    let outerHeight: CGFloat
    let innerInsets: SvgIconInsets
    let imageInsets: SvgIconInsets
    let cssVariables: [String: Color]
    let cssValues: [String: String]
    let shouldClip: Bool

    init(
        name: String,
        outerWidth: CGFloat,
        outerHeight: CGFloat,
        innerInsets: SvgIconInsets = .zero,
        imageInsets: SvgIconInsets = .zero,
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
        .modifier(SvgClipModifier(isEnabled: shouldClip))
    }
}

private struct SvgClipModifier: ViewModifier {
    let isEnabled: Bool
    func body(content: Content) -> some View {
        if isEnabled { content.clipped() } else { content }
    }
}
