import SwiftUI
import UIKit
import WebKit

enum LeoMarkdownTheme {
    case light
    case dark
    case automatic

    func resolved(using colorScheme: ColorScheme) -> String {
        switch self {
        case .light:
            return "light"
        case .dark:
            return "dark"
        case .automatic:
            return colorScheme == .dark ? "dark" : "light"
        }
    }
}

enum LeoMarkdownVariant {
    case knowledgeCard
    case keyPoints
    case studyNote
}

struct LeoMarkdownStreamingOption {
    var hasNextChunk: Bool = false
    var enableAnimation: Bool = false
    var tail: String = "▋"
}

struct LeoMarkdownView: View {
    let content: String
    var theme: LeoMarkdownTheme = .automatic
    var variant: LeoMarkdownVariant = .knowledgeCard
    var focusHighlightVisible: Bool = true
    var streaming: LeoMarkdownStreamingOption = .init()
    var openLinksInNewTab: Bool = false
    var escapeRawHtml: Bool = false

    @Environment(\.colorScheme) private var colorScheme
    @State private var renderedHeight: CGFloat = 1

    var body: some View {
        LeoMarkdownWebView(
            content: content,
            resolvedTheme: theme.resolved(using: colorScheme),
            variant: variant,
            focusHighlightVisible: focusHighlightVisible,
            streaming: streaming,
            openLinksInNewTab: openLinksInNewTab,
            escapeRawHtml: escapeRawHtml,
            renderedHeight: $renderedHeight
        )
        .frame(height: max(1, renderedHeight))
    }
}

private struct LeoMarkdownWebView: UIViewRepresentable {
    let content: String
    let resolvedTheme: String
    let variant: LeoMarkdownVariant
    let focusHighlightVisible: Bool
    let streaming: LeoMarkdownStreamingOption
    let openLinksInNewTab: Bool
    let escapeRawHtml: Bool

    @Binding var renderedHeight: CGFloat

    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }

    func makeUIView(context: Context) -> MarkdownRenderWebView {
        let config = WKWebViewConfiguration()
        config.userContentController.add(context.coordinator, name: "leoMarkdownHeight")
        let webView = MarkdownRenderWebView(frame: .zero, configuration: config)
        webView.navigationDelegate = context.coordinator
        webView.isOpaque = false
        webView.backgroundColor = .clear
        webView.scrollView.backgroundColor = .clear
        webView.scrollView.isScrollEnabled = false
        webView.scrollView.bounces = false
        webView.scrollView.contentInsetAdjustmentBehavior = .never
        webView.isUserInteractionEnabled = true
        return webView
    }

    func updateUIView(_ webView: MarkdownRenderWebView, context: Context) {
        let traitStyle: UIUserInterfaceStyle = resolvedTheme == "dark" ? .dark : .light
        let traitCollection = UITraitCollection(userInterfaceStyle: traitStyle)

        let cssVariables = resolveTokenCssVariables(for: traitCollection)
        let cssVariableSignature = cssVariables.keys.sorted().map { "\($0)=\(cssVariables[$0] ?? "")" }.joined(separator: ";")

        let signature = [
            content,
            resolvedTheme,
            variant == .knowledgeCard ? "knowledge-card" : "key-points",
            focusHighlightVisible ? "focus-visible" : "focus-hidden",
            streaming.hasNextChunk ? "1" : "0",
            streaming.enableAnimation ? "1" : "0",
            streaming.tail,
            openLinksInNewTab ? "1" : "0",
            escapeRawHtml ? "1" : "0",
            cssVariableSignature,
        ].joined(separator: "#")

        guard signature != webView.lastRenderSignature else {
            context.coordinator.updateHeight(for: webView)
            return
        }

        webView.lastRenderSignature = signature
        webView.overrideUserInterfaceStyle = traitStyle

        let html = buildHTML(cssVariables: cssVariables)
        webView.loadHTMLString(html, baseURL: Bundle.main.bundleURL)
    }

    private func buildHTML(cssVariables: [String: String]) -> String {
        let markdownScript = Self.loadMarkedScript()
        let markdownJSON = jsonEncoded(content)
        let tailJSON = jsonEncoded(streaming.tail)
        let cssVariableText = cssVariables.keys.sorted().map { key in
            "--\(key): \(cssVariables[key] ?? "rgba(0,0,0,1)");"
        }.joined(separator: "\n")
        let textColor: String
        let textSize: String
        let textLineHeight: String
        let variantClass: String
        let hideAllContent: Bool
        switch variant {
        case .knowledgeCard:
            textColor = "var(--ios-color-text-primary)"
            textSize = "16px"
            textLineHeight = "28px"
            variantClass = "leo-markdown--knowledge-card"
            hideAllContent = false
        case .keyPoints:
            textColor = "var(--ios-color-text-secondary)"
            textSize = "16px"
            textLineHeight = "24px"
            variantClass = "leo-markdown--key-points"
            hideAllContent = !focusHighlightVisible
        case .studyNote:
            textColor = "var(--ios-color-text-secondary)"
            textSize = "16px"
            textLineHeight = "24px"
            variantClass = "leo-markdown--study-note"
            hideAllContent = !focusHighlightVisible
        }

        let script = """
        const syntaxPattern = /(\\/\\*[\\s\\S]*?\\*\\/|\\/\\/[^\\n\\r]*|#[^\\n\\r]*|<!--[\\s\\S]*?-->)|(`(?:\\\\[\\s\\S]|[^`\\\\])*`|\"(?:\\\\[\\s\\S]|[^\"\\\\])*\"|'(?:\\\\[\\s\\S]|[^'\\\\])*')|(<\\/?[a-zA-Z][\\w:-]*|\\/?>)|(\\b[a-zA-Z_][\\w:-]*(?=\\s*=))|(\\b(?:abstract|as|async|await|break|case|catch|class|const|continue|debugger|declare|def|default|delete|do|elif|else|enum|export|extends|final|finally|for|from|function|if|implements|import|in|interface|is|lambda|let|match|new|of|package|private|protected|public|raise|readonly|return|static|super|switch|this|throw|try|type|var|void|while|with|yield)\\b)|(\\b(?:true|false|null|undefined|None|True|False|NaN|Infinity)\\b)|(\\b(?:Array|Boolean|Date|Dict|Error|JSON|List|Map|Math|Number|Object|Promise|Record|RegExp|Set|String|Tuple|console|document|print|window)\\b)|(\\b(?:0x[\\da-fA-F]+|\\d+(?:\\.\\d+)?(?:e[+-]?\\d+)?)\\b)|(\\b[a-zA-Z_$][\\w$-]*(?=\\s*\\())|([+\\-*/%=&|!<>?~^]+)|([{}()[\\],.;:])/g;

        function escapeHtml(source) {
          return source
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\"/g, '&quot;')
            .replace(/'/g, '&#39;');
        }

        function sanitize(html) {
          let safe = html.replace(/<script[\\s\\S]*?>[\\s\\S]*?<\\/script>/gi, '');
          safe = safe.replace(/on[a-z]+\\s*=\\s*\"[^\"]*\"/gi, '');
          safe = safe.replace(/on[a-z]+\\s*=\\s*'[^']*'/gi, '');
          return safe;
        }

        function kindForSyntaxMatch(match) {
          if (match[1]) return 'comment';
          if (match[2]) return 'string';
          if (match[3]) return 'tag';
          if (match[4]) return 'attribute';
          if (match[5]) return 'keyword';
          if (match[6]) return 'constant';
          if (match[7]) return 'builtin';
          if (match[8]) return 'number';
          if (match[9]) return 'function';
          if (match[10]) return 'operator';
          if (match[11]) return 'punctuation';
          return 'plain';
        }

        function highlightCode(source) {
          const tokens = [];
          let cursor = 0;
          syntaxPattern.lastIndex = 0;
          const matches = source.matchAll(syntaxPattern);

          for (const match of matches) {
            const index = match.index || 0;
            if (index > cursor) {
              tokens.push({ kind: 'plain', value: source.slice(cursor, index) });
            }
            tokens.push({ kind: kindForSyntaxMatch(match), value: match[0] });
            cursor = index + match[0].length;
          }

          if (cursor < source.length) {
            tokens.push({ kind: 'plain', value: source.slice(cursor) });
          }

          return tokens;
        }

        function enhanceCodeBlocks() {
          document.querySelectorAll('pre code').forEach((codeEl) => {
            const source = codeEl.textContent || '';
            const languageMatch = (codeEl.className || '').match(/language-([a-z0-9_-]+)/i);
            if (languageMatch && languageMatch[1]) {
              codeEl.dataset.language = languageMatch[1];
            }

            const fragments = highlightCode(source).map((token) => {
              if (token.kind === 'plain') {
                return token.value
                  .replace(/&/g, '&amp;')
                  .replace(/</g, '&lt;')
                  .replace(/>/g, '&gt;');
              }
              const value = token.value
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
              return `<span class=\"leo-markdown__syntax leo-markdown__syntax--${token.kind}\">${value}</span>`;
            });

            codeEl.innerHTML = fragments.join('');
          });
        }

        function encodeFocusHighlights(source, focusHighlightVisible) {
          const stateClass = focusHighlightVisible
            ? 'leo-markdown__focus--visible'
            : 'leo-markdown__focus--hidden';
          let count = 0;
          const encodedSource = source.replace(/==([\\s\\S]+?)==/g, (_, rawText) => {
            const index = count;
            count += 1;
            return `@@LEO_FOCUS_START_${index}@@${String(rawText || '')}@@LEO_FOCUS_END_${index}@@`;
          });
          return { source: encodedSource, count, stateClass };
        }

        function applyFocusHighlights(html, focusCount, stateClass) {
          let nextHTML = html;
          for (let index = 0; index < focusCount; index += 1) {
            const startToken = `@@LEO_FOCUS_START_${index}@@`;
            const endToken = `@@LEO_FOCUS_END_${index}@@`;
            const startHTML = `<span class=\"leo-markdown__focus ${stateClass}\"><span class=\"leo-markdown__focus-text\">`;
            const endHTML = '</span></span>';
            nextHTML = nextHTML.split(startToken).join(startHTML);
            nextHTML = nextHTML.split(endToken).join(endHTML);
          }
          return nextHTML;
        }

        function render() {
          const content = \(markdownJSON);
          const options = {
            hasNextChunk: \(streaming.hasNextChunk ? "true" : "false"),
            enableAnimation: \(streaming.enableAnimation ? "true" : "false"),
            tail: \(tailJSON),
            openLinksInNewTab: \(openLinksInNewTab ? "true" : "false"),
            escapeRawHtml: \(escapeRawHtml ? "true" : "false"),
            focusHighlightVisible: \(focusHighlightVisible ? "true" : "false")
          };

          let source = content || '';
          if (options.escapeRawHtml) {
            source = escapeHtml(source);
          }

          const focusEncoding = encodeFocusHighlights(source, options.focusHighlightVisible);
          source = focusEncoding.source;

          let html = '';
          if (window.marked && typeof window.marked.parse === 'function') {
            html = window.marked.parse(source, { gfm: true, breaks: false, async: false });
          } else {
            html = source.replace(/\\n/g, '<br/>');
          }

          html = sanitize(html);
          html = applyFocusHighlights(html, focusEncoding.count, focusEncoding.stateClass);

          const root = document.getElementById('leo-markdown-content');
          root.innerHTML = html;

          if (options.openLinksInNewTab) {
            root.querySelectorAll('a').forEach((anchor) => {
              anchor.setAttribute('target', '_blank');
              anchor.setAttribute('rel', 'noopener noreferrer');
            });
          }

          enhanceCodeBlocks();

          if (options.hasNextChunk) {
            const tail = document.createElement('span');
            tail.className = 'leo-markdown__tail';
            tail.setAttribute('aria-hidden', 'true');
            tail.textContent = options.tail || '▋';
            root.appendChild(tail);

            root.classList.add('leo-markdown--streaming');
            if (options.enableAnimation) {
              root.classList.add('leo-markdown--animated');
            }
          }

          requestAnimationFrame(() => {
            const contentEl = document.getElementById('leo-markdown-content');
            const contentHeight = contentEl
              ? Math.ceil(Math.max(contentEl.scrollHeight, contentEl.getBoundingClientRect().height))
              : 1;
            window.webkit?.messageHandlers?.leoMarkdownHeight?.postMessage(contentHeight);
          });
        }

        render();
        """

        return """
        <!doctype html>
        <html>
        <head>
          <meta charset=\"utf-8\" />
          <meta name=\"viewport\" content=\"width=device-width, initial-scale=1, maximum-scale=1\" />
          <style>
            :root {
              \(cssVariableText)
            }

            html, body {
              margin: 0;
              padding: 0;
              background: transparent;
            }

            #leo-markdown-root {
              inline-size: 100%;
            }

            .leo-markdown {
              color: \(textColor);
              font-size: \(textSize);
              line-height: \(textLineHeight);
              inline-size: 100%;
              font-family: "PingFang SC", -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
            }

            .leo-markdown p,
            .leo-markdown div,
            .leo-markdown span,
            .leo-markdown li {
              overflow-wrap: break-word;
              word-break: break-word;
              color: \(textColor);
              font-size: \(textSize);
              line-height: \(textLineHeight);
            }

            .leo-markdown h1,
            .leo-markdown h2,
            .leo-markdown h3,
            .leo-markdown h4 {
              color: var(--ios-color-text-primary);
              font-weight: 600;
              margin: 0 0 16px 0;
            }

            .leo-markdown h1 { font-size: 24px; line-height: 36px; }
            .leo-markdown h2 { font-size: 20px; line-height: 30px; }
            .leo-markdown h3 { font-size: 18px; line-height: 27px; }
            .leo-markdown h4 { font-size: 16px; line-height: 24px; }

            .leo-markdown p {
              margin: 0 0 16px 0;
            }

            .leo-markdown p:first-child,
            .leo-markdown ul:first-child,
            .leo-markdown ol:first-child,
            .leo-markdown pre:first-child,
            .leo-markdown table:first-child {
              margin-top: 0;
            }

            .leo-markdown p:last-child,
            .leo-markdown ul:last-child,
            .leo-markdown ol:last-child,
            .leo-markdown pre:last-child,
            .leo-markdown table:last-child {
              margin-bottom: 0;
            }

            .leo-markdown > :last-child {
              margin-bottom: 0 !important;
            }

            .leo-markdown ul,
            .leo-markdown ol {
              display: flow-root;
              margin: 0 0 16px 16px;
              padding: 0 0 0 16px;
            }

            .leo-markdown ol > li { list-style: decimal; }
            .leo-markdown ul > li { list-style: disc; }

            .leo-markdown li {
              color: inherit;
              margin: 0 0 8px 0;
              position: relative;
            }

            .leo-markdown li::marker {
              color: var(--ios-color-fg-primary);
              font-size: 16px;
              font-weight: 400;
              line-height: 28px;
            }

            .leo-markdown hr {
              border: 0;
              border-top: 1px solid var(--ios-color-border-default);
              margin: 24px 0;
            }

            .leo-markdown table {
              background: var(--ios-color-bg-canvas);
              border: 1px solid var(--ios-color-border-default);
              border-collapse: separate;
              border-radius: 6px;
              border-spacing: 0;
              display: block;
              inline-size: max-content;
              margin: 0 0 24px 0;
              max-inline-size: 100%;
              overflow: auto;
            }

            .leo-markdown thead {
              background-color: var(--ios-color-bg-subtle);
            }

            .leo-markdown tbody,
            .leo-markdown tbody tr {
              background-color: var(--ios-color-bg-surface);
            }

            .leo-markdown tbody tr { transition: background-color 200ms linear; }
            .leo-markdown tbody tr:hover { background-color: var(--ios-color-bg-subtle); }

            .leo-markdown th,
            .leo-markdown td {
              border: 0;
              border-inline-end: 1px solid var(--ios-color-border-default);
              border-block-end: 1px solid var(--ios-color-border-default);
              padding: 10px 12px;
            }

            .leo-markdown tr > :last-child { border-inline-end: 0; }
            .leo-markdown tbody tr:last-child > td { border-block-end: 0; }
            .leo-markdown th { color: var(--ios-color-text-primary); font-weight: 600; text-align: left; }
            .leo-markdown td { color: var(--ios-color-text-secondary); }
            .leo-markdown strong { color: var(--ios-color-text-primary); }

            .leo-markdown blockquote {
              background-color: var(--ios-color-bg-surface);
              border: 1px solid var(--ios-color-border-default);
              border-left: 5px solid var(--ios-color-fg-disabled);
              border-radius: 6px;
              margin: 16px 0;
              padding: 12px;
              transition: background-color 0.2s ease;
            }

            .leo-markdown blockquote:hover {
              background-color: var(--ios-color-bg-subtle);
            }

            .leo-markdown pre,
            .leo-markdown code {
              overflow-wrap: break-word;
              white-space: pre-wrap;
              word-break: break-word;
            }

            .leo-markdown pre {
              margin: 0 0 16px 0;
              overflow-x: auto;
            }

            .leo-markdown pre code {
              background: var(--ios-color-bg-subtle) !important;
              border-radius: 6px;
              color: var(--ios-color-text-secondary) !important;
              display: block;
              font-size: 14px;
              line-height: 1.5;
              margin: 0;
              padding: 16px;
            }

            .leo-markdown__syntax--comment { color: var(--ios-color-text-disabled); }
            .leo-markdown__syntax--punctuation { color: var(--ios-color-text-secondary); }
            .leo-markdown__syntax--string { color: var(--ios-color-fg-success); }
            .leo-markdown__syntax--number { color: var(--ios-color-fg-warning); }
            .leo-markdown__syntax--keyword { color: var(--ios-color-fg-brand); }
            .leo-markdown__syntax--constant { color: var(--ios-color-fg-assist); }
            .leo-markdown__syntax--function { color: var(--ios-color-fg-success); }
            .leo-markdown__syntax--property { color: var(--ios-color-fg-brand); }
            .leo-markdown__syntax--operator { color: var(--ios-color-fg-danger); }
            .leo-markdown__syntax--tag { color: var(--ios-color-fg-danger); }
            .leo-markdown__syntax--attribute { color: var(--ios-color-fg-assist); }
            .leo-markdown__syntax--builtin { color: var(--ios-color-fg-success); }

            .leo-markdown code:not(pre code) {
              display: inline-flex;
              align-items: center;
              background-color: var(--ios-color-bg-subtle) !important;
              border: 1px solid var(--ios-color-border-default);
              border-radius: 4px;
              color: var(--ios-color-text-secondary) !important;
              font-size: 12px;
              line-height: 16px;
              margin-inline: 2px;
              padding: 1px 5px;
              vertical-align: 0.08em;
            }

            .leo-markdown img {
              block-size: auto;
              margin: 0.5em 0;
              max-inline-size: 100%;
            }

            .leo-markdown a {
              color: var(--ios-color-fg-brand);
              position: relative;
              text-decoration: none;
              transition: color 0.2s ease;
            }

            .leo-markdown a:hover {
              color: var(--ios-color-fg-brand-secondary);
              text-decoration: underline;
            }

            .leo-markdown__focus {
              align-items: center;
              border: 1px solid transparent;
              border-radius: 8px;
              box-sizing: border-box;
              display: inline-flex;
              justify-content: center;
              margin-inline: 4px;
              padding-block: 0;
              vertical-align: middle;
              white-space: nowrap;
            }

            .leo-markdown__focus-text {
              font-family: "PingFang SC", -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
              font-style: normal;
              font-weight: 400;
            }

            .leo-markdown__focus--visible {
              background: var(--ios-color-fg-danger-subtle);
              border-color: transparent;
            }

            .leo-markdown__focus--visible .leo-markdown__focus-text {
              color: var(--ios-color-text-danger);
              opacity: 1;
            }

            .leo-markdown__focus--visible strong {
              color: var(--ios-color-text-danger);
              font-weight: 600;
            }

            .leo-markdown__focus--hidden {
              background: var(--ios-color-components-emphasis-invisible);
              border-color: transparent;
            }

            .leo-markdown__focus--hidden .leo-markdown__focus-text {
              color: var(--ios-color-text-primary);
              opacity: 0;
            }

            .leo-markdown__focus {
              height: 24px;
              padding-inline: 6px;
            }

            .leo-markdown__focus-text {
              font-size: 16px;
              line-height: 24px;
            }

            .leo-markdown--all-hidden p,
            .leo-markdown--all-hidden li {
              background: var(--ios-color-bg-subtle-2);
              border-radius: 8px;
              color: transparent !important;
            }

            .leo-markdown--all-hidden p *,
            .leo-markdown--all-hidden li * { color: transparent !important; }

            .leo-markdown__tail {
              animation: leo-markdown-tail-blink 1s steps(2, start) infinite;
              color: var(--ios-color-text-secondary);
              display: inline;
              font-size: inherit;
              line-height: inherit;
            }

            .leo-markdown--animated > * {
              animation: leo-markdown-fade-in 200ms ease-in-out;
            }

            @keyframes leo-markdown-fade-in {
              from { opacity: 0; }
              to { opacity: 1; }
            }

            @keyframes leo-markdown-tail-blink {
              0%, 45% { opacity: 1; }
              46%, 100% { opacity: 0.2; }
            }
          </style>
          <script>\(markdownScript)</script>
        </head>
        <body>
          <div id=\"leo-markdown-root\">
            <div id=\"leo-markdown-content\" class=\"leo-markdown leo-markdown--\(resolvedTheme) \(variantClass) \(hideAllContent ? "leo-markdown--all-hidden" : "")\"></div>
          </div>
          <script>\(script)</script>
        </body>
        </html>
        """
    }

    private func resolveTokenCssVariables(for traitCollection: UITraitCollection) -> [String: String] {
        let tokenMap: [String: Color] = [
            "ios-color-bg-canvas": Token.bgCanvas,
            "ios-color-bg-subtle": Token.bgSubtle,
            "ios-color-bg-subtle-2": Token.bgSubtle2,
            "ios-color-components-emphasis-invisible": Token.componentsEmphasisInvisible,
            "ios-color-bg-surface": Token.bgSurface,
            "ios-color-border-default": Token.borderDefault,
            "ios-color-fg-primary": Token.fgPrimary,
            "ios-color-fg-disabled": Token.fgDisabled,
            "ios-color-fg-warning-subtle": Token.fgWarningSubtle,
            "ios-color-fg-danger-subtle": Token.fgDangerSubtle,
            "ios-color-text-primary": Token.textPrimary,
            "ios-color-text-secondary": Token.textSecondary,
            "ios-color-text-disabled": Token.textDisabled,
            "ios-color-text-warning": Token.textWarning,
            "ios-color-text-danger": Token.fgDanger,
            "ios-color-fg-brand": Token.fgBrand,
            "ios-color-fg-brand-secondary": Token.fgBrandSecondary,
            "ios-color-fg-success": Token.fgSuccess,
            "ios-color-fg-warning": Token.fgWarning,
            "ios-color-fg-danger": Token.fgDanger,
            "ios-color-fg-assist": Token.fgAssist,
        ]

        var resolved: [String: String] = [:]
        for (key, color) in tokenMap {
            let uiColor = UIColor(color).resolvedColor(with: traitCollection)
            resolved[key] = uiColor.cssRGBAString
        }
        return resolved
    }

    private func jsonEncoded(_ value: String) -> String {
        guard
            let data = try? JSONSerialization.data(withJSONObject: ["value": value], options: []),
            let object = try? JSONSerialization.jsonObject(with: data) as? [String: String],
            let encoded = object["value"]
        else {
            return "\"\""
        }
        return "\"\(encoded.replacingOccurrences(of: "\\", with: "\\\\").replacingOccurrences(of: "\"", with: "\\\"").replacingOccurrences(of: "\n", with: "\\n").replacingOccurrences(of: "\r", with: "\\r").replacingOccurrences(of: "\u{2028}", with: "\\u2028").replacingOccurrences(of: "\u{2029}", with: "\\u2029"))\""
    }

    private static var markedScriptCache: String?

    private static func loadMarkedScript() -> String {
        if let cached = markedScriptCache {
            return cached
        }

        guard let url = Bundle.main.url(forResource: "marked.min", withExtension: "js", subdirectory: "Markdown") ??
                Bundle.main.url(forResource: "marked.min", withExtension: "js")
        else {
            return ""
        }

        let script = (try? String(contentsOf: url, encoding: .utf8)) ?? ""
        markedScriptCache = script
        return script
    }

    final class Coordinator: NSObject, WKNavigationDelegate, WKScriptMessageHandler {
        private let parent: LeoMarkdownWebView

        init(_ parent: LeoMarkdownWebView) {
            self.parent = parent
        }

        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            updateHeight(for: webView)
        }

        func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
            if message.name == "leoMarkdownHeight", let height = message.body as? CGFloat {
                let newHeight = max(1, height)
                // Only update if height changed by more than 1pt to avoid micro-jitter
                guard abs(newHeight - parent.renderedHeight) > 1 else { return }
                DispatchQueue.main.async {
                    self.parent.renderedHeight = newHeight
                }
            }
        }

        func updateHeight(for webView: WKWebView) {
            webView.evaluateJavaScript("""
            (function () {
              const contentEl = document.getElementById('leo-markdown-content');
              if (!contentEl) return 1;
              return Math.ceil(Math.max(contentEl.scrollHeight, contentEl.getBoundingClientRect().height));
            })();
            """) { value, _ in
                guard let height = value as? CGFloat else { return }
                let newHeight = max(1, height)
                guard abs(newHeight - self.parent.renderedHeight) > 1 else { return }
                DispatchQueue.main.async {
                    self.parent.renderedHeight = newHeight
                }
            }
        }
    }
}

private final class MarkdownRenderWebView: WKWebView {
    var lastRenderSignature: String = ""
}


#Preview {
    ScrollView {
        LeoMarkdownView(
            content: """
            # 知识卡片标题

            这是一个支持 **Markdown** 的 iOS 组件，包含 `inline code`、[链接](https://example.com) 和列表。

            - 第一项
            - 第二项
            - 第三项

            > 引用块示例

            ```swift
            struct Example {
                let value = 27
                func run() {
                    print(value)
                }
            }
            ```

            | 字段 | 值 |
            | --- | --- |
            | 模块 | Markdown |
            | 平台 | iOS |
            """
        )
        .padding(20)
    }
    .background(Token.bgCanvas)
}
