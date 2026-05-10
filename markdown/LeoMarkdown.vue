<script lang="ts">
import DOMPurify, { type Config as DOMPurifyConfig } from 'dompurify'
import { Marked, type MarkedExtension } from 'marked'
import {
  computed,
  defineComponent,
  h,
  Text,
  type Component,
  type PropType,
  type VNodeChild,
} from 'vue'

export type LeoMarkdownTheme = 'light' | 'dark'
export type LeoMarkdownStreamStatus = 'loading' | 'done'
export type LeoMarkdownIncompleteType =
  | 'link'
  | 'image'
  | 'html'
  | 'emphasis'
  | 'list'
  | 'table'
  | 'inline-code'
  | 'code'

export interface LeoMarkdownTailConfig {
  content?: string
  component?: Component
}

export interface LeoMarkdownStreamingOption {
  hasNextChunk?: boolean
  enableAnimation?: boolean
  tail?: boolean | LeoMarkdownTailConfig
  incompleteMarkdownComponentMap?: Partial<Record<LeoMarkdownIncompleteType, string>>
}

export type LeoMarkdownComponentMap = Record<string, Component | string>

interface PreparedMarkdown {
  source: string
  incompleteTypes: LeoMarkdownIncompleteType[]
}

type SyntaxTokenKind =
  | 'plain'
  | 'comment'
  | 'string'
  | 'number'
  | 'keyword'
  | 'constant'
  | 'function'
  | 'property'
  | 'operator'
  | 'punctuation'
  | 'tag'
  | 'attribute'
  | 'builtin'

interface SyntaxToken {
  kind: SyntaxTokenKind
  value: string
}

const placeholderTagByType: Record<LeoMarkdownIncompleteType, string> = {
  link: 'leo-md-incomplete-link',
  image: 'leo-md-incomplete-image',
  html: 'leo-md-incomplete-html',
  emphasis: 'leo-md-incomplete-emphasis',
  list: 'leo-md-incomplete-list',
  table: 'leo-md-incomplete-table',
  'inline-code': 'leo-md-incomplete-inline-code',
  code: 'leo-md-incomplete-code',
}

const placeholderTypeByTag = Object.fromEntries(
  Object.entries(placeholderTagByType).map(([type, tag]) => [tag, type]),
) as Record<string, LeoMarkdownIncompleteType>

function escapeHtml(source: string): string {
  return source
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function countMatches(source: string, pattern: RegExp): number {
  return source.match(pattern)?.length ?? 0
}

function buildPlaceholder(type: LeoMarkdownIncompleteType, streaming: LeoMarkdownStreamingOption): string {
  const tagName = streaming.incompleteMarkdownComponentMap?.[type] ?? placeholderTagByType[type]
  return `<${tagName}></${tagName}>`
}

function prepareStreamingMarkdown(
  source: string,
  streaming: LeoMarkdownStreamingOption,
): PreparedMarkdown {
  if (!streaming.hasNextChunk) {
    return { source, incompleteTypes: [] }
  }

  let nextSource = source
  const incompleteTypes: LeoMarkdownIncompleteType[] = []

  const addPlaceholder = (type: LeoMarkdownIncompleteType): void => {
    if (!incompleteTypes.includes(type)) {
      incompleteTypes.push(type)
      nextSource = `${nextSource}\n\n${buildPlaceholder(type, streaming)}`
    }
  }

  const fenceMatches = nextSource.match(/(^|\n)(```|~~~)/g) ?? []
  if (fenceMatches.length % 2 === 1) {
    const lastFence = fenceMatches[fenceMatches.length - 1]
    const fence = lastFence.includes('~~~') ? '~~~' : '```'
    nextSource = `${nextSource}\n${fence}`
    addPlaceholder('code')
  }

  if (countMatches(nextSource, /(^|[^\\])`/g) % 2 === 1) {
    nextSource = `${nextSource}\``
    addPlaceholder('inline-code')
  }

  if (/!\[[^\]\n]*(?:\]\([^\)\n]*)?$/.test(nextSource)) {
    nextSource = nextSource.replace(/!\[[^\]\n]*(?:\]\([^\)\n]*)?$/, '')
    addPlaceholder('image')
  } else if (/(^|[^!])\[[^\]\n]*(?:\]\([^\)\n]*)?$/.test(nextSource)) {
    nextSource = nextSource.replace(/(^|[^!])\[[^\]\n]*(?:\]\([^\)\n]*)?$/, '$1')
    addPlaceholder('link')
  }

  if (/<[a-z][\w-]*(?:\s[^<>]*)?$/i.test(nextSource)) {
    nextSource = nextSource.replace(/<[a-z][\w-]*(?:\s[^<>]*)?$/i, '')
    addPlaceholder('html')
  }

  const lastLine = nextSource.trimEnd().split('\n').at(-1) ?? ''
  if (lastLine.includes('|') && !/^\s*\|?[\s:-]+\|[\s|:-]*$/.test(lastLine)) {
    addPlaceholder('table')
  }

  return { source: nextSource, incompleteTypes }
}

function mergeSanitizeConfig(
  customTags: string[],
  config?: DOMPurifyConfig,
): DOMPurifyConfig {
  const defaultTags = Object.values(placeholderTagByType)
  const extraTags = Array.isArray(config?.ADD_TAGS) ? config.ADD_TAGS : []
  const extraAttrs = Array.isArray(config?.ADD_ATTR) ? config.ADD_ATTR : []

  return {
    ...config,
    ADD_TAGS: [...new Set([...defaultTags, ...customTags, ...extraTags])],
    ADD_ATTR: [...new Set(['target', 'rel', 'class', 'data-language', ...extraAttrs])],
  }
}

function attributesFor(element: Element): Record<string, string | boolean> {
  const attrs: Record<string, string | boolean> = {}

  for (const attribute of Array.from(element.attributes)) {
    if (attribute.name === 'class') {
      attrs.class = attribute.value
      continue
    }

    if (attribute.name === 'checked') {
      attrs.checked = true
      continue
    }

    attrs[attribute.name] = attribute.value
  }

  return attrs
}

const syntaxPattern =
  /(\/\*[\s\S]*?\*\/|\/\/[^\n\r]*|#[^\n\r]*|<!--[\s\S]*?-->)|(`(?:\\[\s\S]|[^`\\])*`|"(?:\\[\s\S]|[^"\\])*"|'(?:\\[\s\S]|[^'\\])*')|(<\/?[a-zA-Z][\w:-]*|\/?>)|(\b[a-zA-Z_][\w:-]*(?=\s*=))|(\b(?:abstract|as|async|await|break|case|catch|class|const|continue|debugger|declare|def|default|delete|do|elif|else|enum|export|extends|final|finally|for|from|function|if|implements|import|in|interface|is|lambda|let|match|new|of|package|private|protected|public|raise|readonly|return|static|super|switch|this|throw|try|type|var|void|while|with|yield)\b)|(\b(?:true|false|null|undefined|None|True|False|NaN|Infinity)\b)|(\b(?:Array|Boolean|Date|Dict|Error|JSON|List|Map|Math|Number|Object|Promise|Record|RegExp|Set|String|Tuple|console|document|print|window)\b)|(\b(?:0x[\da-fA-F]+|\d+(?:\.\d+)?(?:e[+-]?\d+)?)\b)|(\b[a-zA-Z_$][\w$-]*(?=\s*\())|([+\-*/%=&|!<>?~^]+)|([{}()[\],.;:])/g

function kindForSyntaxMatch(match: RegExpExecArray): SyntaxTokenKind {
  if (match[1]) return 'comment'
  if (match[2]) return 'string'
  if (match[3]) return 'tag'
  if (match[4]) return 'attribute'
  if (match[5]) return 'keyword'
  if (match[6]) return 'constant'
  if (match[7]) return 'builtin'
  if (match[8]) return 'number'
  if (match[9]) return 'function'
  if (match[10]) return 'operator'
  if (match[11]) return 'punctuation'
  return 'plain'
}

function highlightCode(source: string): SyntaxToken[] {
  const tokens: SyntaxToken[] = []
  let cursor = 0

  syntaxPattern.lastIndex = 0

  for (const match of source.matchAll(syntaxPattern)) {
    const index = match.index ?? 0
    if (index > cursor) {
      tokens.push({ kind: 'plain', value: source.slice(cursor, index) })
    }
    tokens.push({ kind: kindForSyntaxMatch(match), value: match[0] })
    cursor = index + match[0].length
  }

  if (cursor < source.length) {
    tokens.push({ kind: 'plain', value: source.slice(cursor) })
  }

  return tokens
}

export default defineComponent({
  name: 'LeoMarkdown',
  props: {
    content: {
      type: String,
      default: undefined,
    },
    components: {
      type: Object as PropType<LeoMarkdownComponentMap>,
      default: () => ({}),
    },
    streaming: {
      type: Object as PropType<LeoMarkdownStreamingOption>,
      default: () => ({}),
    },
    config: {
      type: Object as PropType<MarkedExtension>,
      default: () => ({ gfm: true }),
    },
    className: {
      type: String,
      default: '',
    },
    rootClassName: {
      type: String,
      default: '',
    },
    theme: {
      type: String as PropType<LeoMarkdownTheme>,
      default: 'light',
    },
    openLinksInNewTab: {
      type: Boolean,
      default: false,
    },
    dompurifyConfig: {
      type: Object as PropType<DOMPurifyConfig>,
      default: undefined,
    },
    customTags: {
      type: Array as PropType<string[]>,
      default: () => [],
    },
    escapeRawHtml: {
      type: Boolean,
      default: false,
    },
    debug: {
      type: Boolean,
      default: false,
    },
  },
  setup(props, { slots }) {
    const markdownSource = computed(() => props.content ?? String(slots.default?.()[0]?.children ?? ''))

    const preparedMarkdown = computed(() => {
      const source = props.escapeRawHtml ? escapeHtml(markdownSource.value) : markdownSource.value
      return prepareStreamingMarkdown(source, props.streaming)
    })

    const sanitizedHtml = computed(() => {
      const marked = new Marked({ gfm: true }, props.config)
      const parsed = marked.parse(preparedMarkdown.value.source, { async: false })
      return DOMPurify.sanitize(
        parsed,
        mergeSanitizeConfig(props.customTags, props.dompurifyConfig),
      )
    })

    const parsedNodes = computed(() => {
      if (typeof document === 'undefined') return []

      const template = document.createElement('template')
      template.innerHTML = sanitizedHtml.value
      return Array.from(template.content.childNodes)
    })

    const streamStatus = computed<LeoMarkdownStreamStatus>(() =>
      props.streaming.hasNextChunk ? 'loading' : 'done',
    )

    function renderNode(node: ChildNode, index: number): VNodeChild {
      if (node.nodeType === Node.TEXT_NODE) {
        return h(Text, String(node.textContent ?? ''))
      }

      if (node.nodeType !== Node.ELEMENT_NODE) {
        return null
      }

      const element = node as Element
      const tagName = element.tagName.toLowerCase()
      const placeholderType = placeholderTypeByTag[tagName]

      if (placeholderType) {
        return h(
          placeholderType === 'table' || placeholderType === 'code' ? 'div' : 'span',
          {
            key: `${tagName}-${index}`,
            class: ['leo-markdown__incomplete', `leo-markdown__incomplete--${placeholderType}`],
            'data-type': placeholderType,
            'aria-hidden': 'true',
          },
        )
      }

      const attrs = attributesFor(element)
      attrs.key = `${tagName}-${index}`

      if (tagName === 'a' && props.openLinksInNewTab) {
        attrs.target = '_blank'
        attrs.rel = 'noopener noreferrer'
      }

      const isCodeBlock = tagName === 'code' && element.parentElement?.tagName.toLowerCase() === 'pre'

      if (tagName === 'code') {
        const language = String(attrs.class ?? '').match(/language-([a-z0-9_-]+)/i)?.[1]
        if (language) {
          attrs['data-language'] = language
        }
      }

      const children = isCodeBlock
        ? highlightCode(String(element.textContent ?? '')).map((token, tokenIndex) =>
          token.kind === 'plain'
            ? h(Text, token.value)
            : h(
              'span',
              {
                key: `${tagName}-${index}-syntax-${tokenIndex}`,
                class: ['leo-markdown__syntax', `leo-markdown__syntax--${token.kind}`],
              },
              token.value,
            ),
        )
        : Array.from(element.childNodes).map(renderNode)
      const mappedComponent = props.components[tagName]

      if (mappedComponent) {
        return h(mappedComponent, { ...attrs, streamStatus: streamStatus.value }, () => children)
      }

      return h(tagName, attrs, children)
    }

    function renderTail(): VNodeChild {
      const tail = props.streaming.tail
      if (!props.streaming.hasNextChunk || !tail) return null

      if (typeof tail === 'object' && tail.component) {
        return h(tail.component, { content: tail.content })
      }

      const content = typeof tail === 'object' ? (tail.content ?? '▋') : '▋'
      return h('span', { class: 'leo-markdown__tail', 'aria-hidden': 'true' }, content)
    }

    return () =>
      h(
        'div',
        {
          class: [
            'leo-markdown-root',
            props.rootClassName,
          ],
          'data-theme': props.theme === 'dark' ? 'dark' : undefined,
        },
        [
          h(
            'div',
            {
              class: [
                'leo-markdown',
                `leo-markdown--${props.theme}`,
                props.className,
                {
                  'leo-markdown--streaming': props.streaming.hasNextChunk,
                  'leo-markdown--animated': props.streaming.enableAnimation,
                },
              ],
              'data-stream-status': streamStatus.value,
            },
            [
              ...parsedNodes.value.map(renderNode),
              renderTail(),
              props.debug
                ? h('pre', { class: 'leo-markdown__debug' }, JSON.stringify(preparedMarkdown.value, null, 2))
                : null,
            ],
          ),
        ],
      )
  },
})
</script>

<style>
.leo-markdown {
  color: var(--color-text-secondary);
  font-size: 14px;
  line-height: 24px;
  inline-size: 100%;
}

.leo-markdown p,
.leo-markdown div,
.leo-markdown span,
.leo-markdown li {
  overflow-wrap: break-word;
  word-break: break-word;
}

.leo-markdown h1,
.leo-markdown h2,
.leo-markdown h3,
.leo-markdown h4 {
  color: var(--color-text-primary);
  font-weight: 600;
  margin: 0 0 16px 0;
}

.leo-markdown h1 {
  font-size: 24px;
  line-height: 36px;
}

.leo-markdown h2 {
  font-size: 20px;
  line-height: 30px;
}

.leo-markdown h3 {
  font-size: 18px;
  line-height: 27px;
}

.leo-markdown h4 {
  font-size: 16px;
  line-height: 24px;
}

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

.leo-markdown ul,
.leo-markdown ol {
  display: flow-root;
  margin: 0 0 16px 16px;
  padding: 0 0 0 16px;
}

.leo-markdown ol > li {
  list-style: decimal;
}

.leo-markdown ul > li {
  list-style: disc;
}

.leo-markdown li {
  color: var(--color-text-secondary);
  margin: 0 0 8px 0;
  position: relative;
}

.leo-markdown li::marker {
  color: var(--color-fg-primary);
  font-size: 16px;
  font-weight: 400;
  line-height: 28px;
}

.leo-markdown hr {
  border: 0;
  border-top: 1px solid var(--color-border-default);
  margin: 24px 0;
}

.leo-markdown table {
  background: var(--color-bg-canvas);
  border: 1px solid var(--color-border-default);
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
  background-color: var(--color-bg-tertiary);
}

.leo-markdown tbody,
.leo-markdown tbody tr {
  background-color: var(--color-bg-surface);
}

.leo-markdown tbody tr {
  transition: background-color 200ms linear;
}

.leo-markdown tbody tr:hover {
  background-color: var(--color-bg-secondary);
}

.leo-markdown th,
.leo-markdown td {
  border: 0;
  border-inline-end: 1px solid var(--color-border-default);
  border-block-end: 1px solid var(--color-border-default);
  padding: 10px 12px;
}

.leo-markdown tr > :last-child {
  border-inline-end: 0;
}

.leo-markdown tbody tr:last-child > td {
  border-block-end: 0;
}

.leo-markdown th {
  color: var(--color-text-primary);
  font-weight: 600;
  text-align: left;
}

.leo-markdown td {
  color: var(--color-text-secondary);
}

.leo-markdown strong {
  color: var(--color-text-primary);
}

.leo-markdown blockquote {
  background-color: var(--color-bg-surface);
  border: 1px solid var(--color-border-default);
  border-left: 5px solid var(--color-fg-disabled);
  border-radius: 6px;
  margin: 16px 0;
  padding: 12px;
  transition: background-color 0.2s ease;
}

.leo-markdown blockquote:hover {
  background-color: var(--color-bg-tertiary);
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
  background: var(--color-bg-secondary) !important;
  border-radius: 6px;
  color: var(--color-text-secondary) !important;
  display: block;
  font-size: 14px;
  line-height: 1.5;
  margin: 0;
  padding: 16px;
}

.leo-markdown__syntax--comment {
  color: var(--color-text-disabled);
}

.leo-markdown__syntax--punctuation {
  color: var(--color-text-secondary);
}

.leo-markdown__syntax--string {
  color: var(--color-utility-green-500);
}

.leo-markdown__syntax--number {
  color: var(--color-utility-orange-500);
}

.leo-markdown__syntax--keyword {
  color: var(--color-utility-blue-500);
}

.leo-markdown__syntax--constant {
  color: var(--color-utility-purple-500);
}

.leo-markdown__syntax--function {
  color: var(--color-utility-cyan-500);
}

.leo-markdown__syntax--property {
  color: var(--color-utility-aqua-500);
}

.leo-markdown__syntax--operator {
  color: var(--color-utility-pink-500);
}

.leo-markdown__syntax--tag {
  color: var(--color-utility-pink-500);
}

.leo-markdown__syntax--attribute {
  color: var(--color-utility-violet-500);
}

.leo-markdown__syntax--builtin {
  color: var(--color-utility-moss-500);
}

.leo-markdown code:not(pre code) {
  display: inline-flex;
  align-items: center;
  background-color: var(--color-bg-secondary) !important;
  border: 1px solid var(--color-border-default);
  border-radius: 4px;
  color: var(--color-text-secondary) !important;
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
  color: var(--color-fg-brand-primary);
  position: relative;
  text-decoration: none;
  transition: color 0.2s ease;
}

.leo-markdown a:hover {
  color: var(--color-fg-brand-primary-hover);
  text-decoration: underline;
}

.leo-markdown__tail {
  animation: leo-markdown-tail-blink 1s steps(2, start) infinite;
  color: var(--color-text-secondary);
  display: inline;
  font-size: inherit;
  line-height: inherit;
}

.leo-markdown__incomplete {
  background: var(--color-bg-secondary);
  border-radius: 6px;
  display: inline-block;
  inline-size: 4.5em;
  block-size: 1em;
  margin-inline: 3px;
  vertical-align: -0.12em;
}

.leo-markdown__incomplete--table,
.leo-markdown__incomplete--code {
  block-size: 48px;
  display: block;
  inline-size: min(100%, 360px);
  margin: 0 0 16px 0;
}

.leo-markdown--animated > * {
  animation: leo-markdown-fade-in 200ms ease-in-out;
}

.leo-markdown__debug {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-default);
  border-radius: 6px;
  color: var(--color-text-secondary);
  font-size: 12px;
  margin-top: 16px;
  overflow: auto;
  padding: 12px;
}

@keyframes leo-markdown-fade-in {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

@keyframes leo-markdown-tail-blink {
  0%,
  45% {
    opacity: 1;
  }

  46%,
  100% {
    opacity: 0.2;
  }
}
</style>
