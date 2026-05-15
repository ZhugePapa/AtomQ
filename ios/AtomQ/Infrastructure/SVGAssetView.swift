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

// MARK: - Shared SVG Render Engine (single WKWebView for all icons)

@MainActor
final class SVGRenderEngine: NSObject, WKNavigationDelegate {
    static let shared = SVGRenderEngine()

    private var webView: WKWebView?
    private var isWebViewReady = false
    private var warmupCompletion: (() -> Void)?

    private typealias PendingItem = (cacheKey: String, svgHTML: String, size: CGSize, completion: (UIImage?) -> Void)
    private var pending: [PendingItem] = []
    private var rendering = false
    private var snapshotCompletion: (() -> Void)?

    private override init() {
        super.init()
        preWarmWebView()
    }

    /// Pre-warm the WKWebView at app startup so it's ready when icons need rendering
    private func preWarmWebView() {
        let wv = createWebView()
        // Load a minimal page to initialize the WebContent process immediately
        wv.loadHTMLString("<html><body></body></html>", baseURL: nil)
    }

    private func createWebView() -> WKWebView {
        let config = WKWebViewConfiguration()
        config.allowsInlineMediaPlayback = true
        let wv = WKWebView(frame: CGRect(origin: .zero, size: CGSize(width: 1, height: 1)), configuration: config)
        wv.navigationDelegate = self
        wv.isOpaque = false
        wv.backgroundColor = .clear
        wv.scrollView.isScrollEnabled = false
        wv.isUserInteractionEnabled = false
        webView = wv
        return wv
    }

    func enqueueRender(
        cacheKey: String,
        svgHTML: String,
        size: CGSize,
        completion: @escaping (UIImage?) -> Void
    ) {
        pending.append((cacheKey: cacheKey, svgHTML: svgHTML, size: size, completion: completion))
        if !rendering && isWebViewReady {
            processNext()
        }
    }

    private func processNext() {
        guard !pending.isEmpty else {
            rendering = false
            return
        }
        rendering = true
        let item = pending.removeFirst()

        let wv = webView!
        wv.frame = CGRect(origin: .zero, size: item.size)
        wv.loadHTMLString(item.svgHTML, baseURL: nil)

        snapshotCompletion = { [weak self, weak wv] in
            guard let self, let wv else { return }
            let config = WKSnapshotConfiguration()
            config.rect = CGRect(origin: .zero, size: item.size)
            wv.takeSnapshot(with: config) { image, _ in
                if let image {
                    SVGImageCache.setImage(image, forKey: item.cacheKey)
                }
                item.completion(image)
                self.processNext()
            }
        }
    }

    // MARK: - WKNavigationDelegate

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        if !isWebViewReady {
            isWebViewReady = true
            // Start processing pending items now that WebView is warm
            if !pending.isEmpty && !rendering {
                processNext()
            }
        } else {
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.02) { [weak self] in
                self?.snapshotCompletion?()
                self?.snapshotCompletion = nil
            }
        }
    }

    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: any Error) {
        if !isWebViewReady { isWebViewReady = true } // Mark ready even on failure
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) { [weak self] in
            self?.snapshotCompletion?()
            self?.snapshotCompletion = nil
        }
    }

    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: any Error) {
        if !isWebViewReady { isWebViewReady = true }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) { [weak self] in
            self?.snapshotCompletion?()
            self?.snapshotCompletion = nil
        }
    }
}

// MARK: - SVG Asset View (public API unchanged)

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

// MARK: - SVG Render View

private struct SVGRenderView: View {
    let name: String
    let cssVariables: [String: Color]
    let cssValues: [String: String]

    @State private var cachedImage: UIImage?
    @State private var cachedImageKey: String?
    @AppStorage("atomq.darkMode.enabled") private var isDarkMode = false

    var body: some View {
        GeometryReader { geometry in
            let width = geometry.size.width
            let height = geometry.size.height

            if width > 0, height > 0 {
                let resolvedCSSVariables = resolveCSSVariables(isDarkMode: isDarkMode)
                let cacheKey = makeCacheKey(
                    name: name,
                    width: width,
                    height: height,
                    resolvedCSSVariables: resolvedCSSVariables
                )

                if let image = cachedImage(for: cacheKey) ?? SVGImageCache.image(forKey: cacheKey) {
                    Image(uiImage: image)
                        .resizable()
                        .onAppear { cache(image, for: cacheKey) }
                } else {
                    SVGPlaceholderView(
                        name: name,
                        resolvedCSSVariables: resolvedCSSVariables,
                        cssValues: cssValues,
                        cacheKey: cacheKey,
                        size: CGSize(width: width, height: height),
                        onImageCached: { cache($0, for: cacheKey) }
                    )
                }
            }
        }
    }

    private func cachedImage(for cacheKey: String) -> UIImage? {
        cachedImageKey == cacheKey ? cachedImage : nil
    }

    private func cache(_ image: UIImage, for cacheKey: String) {
        cachedImage = image
        cachedImageKey = cacheKey
    }

    private func makeCacheKey(
        name: String,
        width: CGFloat,
        height: CGFloat,
        resolvedCSSVariables: [String: String]
    ) -> String {
        let varSig = resolvedCSSVariables.keys.sorted().map { "\($0)=\(resolvedCSSVariables[$0] ?? "")" }.joined()
        let valSig = cssValues.keys.sorted().map { "\($0)=\(cssValues[$0] ?? "")" }.joined()
        let w = String(format: "%.0f", width)
        let h = String(format: "%.0f", height)
        return "\(name)|\(w)x\(h)|\(varSig)|\(valSig)"
    }

    private func resolveCSSVariables(isDarkMode: Bool) -> [String: String] {
        let style: UIUserInterfaceStyle = isDarkMode ? .dark : .light
        let trait = UITraitCollection(userInterfaceStyle: style)

        return cssVariables.reduce(into: [:]) { result, item in
            result[item.key] = UIColor(item.value).resolvedColor(with: trait).cssRGBAString
        }
    }
}

// MARK: - SVG Placeholder (enqueues to shared renderer)

private struct SVGPlaceholderView: View {
    let name: String
    let resolvedCSSVariables: [String: String]
    let cssValues: [String: String]
    let cacheKey: String
    let size: CGSize
    let onImageCached: (UIImage) -> Void

    @State private var loadedImage: UIImage?

    var body: some View {
        if let image = loadedImage {
            Image(uiImage: image)
                .resizable()
        } else {
            Rectangle()
                .fill(Color.clear)
                .onAppear {
                    requestRender()
                }
        }
    }

    private func requestRender() {
        var cssVarStrings = resolvedCSSVariables
        for (name, value) in cssValues {
            cssVarStrings[name] = value
        }

        let cssText = cssVarStrings.keys.sorted().map { key in
            "--\(key): \(cssVarStrings[key] ?? "transparent");"
        }.joined(separator: " ")

        guard let svgSource = try? String(contentsOf: resolveSVGURL(name: name), encoding: .utf8) else { return }

        let w = String(format: "%.0f", size.width)
        let h = String(format: "%.0f", size.height)
        let html = "<!doctype html><html><head><meta charset=utf-8><meta name=viewport content=\"width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no\"><style>html,body{margin:0;padding:0;width:\(w)px;height:\(h)px;overflow:hidden;background:transparent;}#root{position:relative;width:100%;height:100%;overflow:hidden;}#root>svg{position:absolute;inset:0;display:block;}:root{\(cssText)}</style></head><body><div id=root>\(svgSource)</div></body></html>"

        SVGRenderEngine.shared.enqueueRender(
            cacheKey: cacheKey,
            svgHTML: html,
            size: size
        ) { image in
            if let image {
                DispatchQueue.main.async {
                    self.loadedImage = image
                    self.onImageCached(image)
                }
            }
        }
    }

    private func resolveSVGURL(name: String) -> URL {
        // Try Bundle.main resource lookups
        if let url = Bundle.main.url(forResource: name, withExtension: "svg", subdirectory: "SVG") { return url }
        if let url = Bundle.main.url(forResource: name, withExtension: "svg") { return url }
        // Fallback: construct path from resourceURL (works for folder references)
        return Bundle.main.resourceURL!.appendingPathComponent("SVG/\(name).svg")
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
