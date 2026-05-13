import Foundation

struct KnowledgeCardStudyContent {
    let pointID: String
    let chapterID: String
    let sectionID: String
    let headerTitle: String
    let knowledgeMarkdown: String
    let keyPointsMarkdown: String?
    let mnemonicsMarkdown: String?
    let chipTitle: String
}

struct KnowledgeDirectoryChapter: Identifiable, Equatable {
    let id: String
    let title: String
    let sortNo: Int
    let sections: [KnowledgeDirectorySection]
}

struct KnowledgeDirectorySection: Identifiable, Equatable {
    let id: String
    let title: String
    let sortNo: Int
}

enum KnowledgeCardDataStore {
    private static var cachedDirectoryTree: [KnowledgeDirectoryChapter]?
    private static var cachedSectionCards: [String: [KnowledgeCardStudyContent]] = [:]

    static func loadStudyContent(
        chapterID: String = "ch_01",
        sectionID: String = "sec_01"
    ) throws -> KnowledgeCardStudyContent {
        guard let first = try loadSectionCards(chapterID: chapterID, sectionID: sectionID).first else {
            throw DataStoreError.notFound(diagnostics: makeRootDiagnostics())
        }
        return first
    }

    static func refreshFreeContentAndLoadStudyContent(
        chapterID: String = "ch_01",
        sectionID: String = "sec_01"
    ) async throws -> KnowledgeCardStudyContent {
        try await ContentPackageRemoteStore.refreshFreeContentRequired()
        return try loadStudyContent(chapterID: chapterID, sectionID: sectionID)
    }

    static func loadSectionCards(
        chapterID: String = "ch_01",
        sectionID: String = "sec_01"
    ) throws -> [KnowledgeCardStudyContent] {
        let cacheKey = "\(chapterID)|\(sectionID)"
        if let cached = cachedSectionCards[cacheKey] {
            return cached
        }
        let cards = try loadSectionCardsFromDataSources(chapterID: chapterID, sectionID: sectionID)
        cachedSectionCards[cacheKey] = cards
        return cards
    }

    static func refreshFreeContentAndLoadSectionCards(
        chapterID: String = "ch_01",
        sectionID: String = "sec_01"
    ) async throws -> [KnowledgeCardStudyContent] {
        try await ContentPackageRemoteStore.refreshFreeContentRequired()
        invalidateCache()
        return try loadSectionCards(chapterID: chapterID, sectionID: sectionID)
    }

    static func loadDirectoryTree() throws -> [KnowledgeDirectoryChapter] {
        if let cached = cachedDirectoryTree {
            return cached
        }
        let tree = try loadDirectoryTreeFromDataSources()
        cachedDirectoryTree = tree
        return tree
    }

    static func refreshFreeContentAndLoadDirectoryTree() async throws -> [KnowledgeDirectoryChapter] {
        try await ContentPackageRemoteStore.refreshFreeContentRequired()
        invalidateCache()
        return try loadDirectoryTree()
    }

    static func invalidateCache() {
        cachedDirectoryTree = nil
        cachedSectionCards = [:]
    }

    private static func loadSectionCardsFromDataSources(
        chapterID: String,
        sectionID: String
    ) throws -> [KnowledgeCardStudyContent] {
        for root in candidateRootDirectories() {
            for chapterPath in chapterPathCandidates(chapterID: chapterID) {
                let chapterDir = root.appendingPathComponent(chapterPath, isDirectory: true)
                let cardsDir = chapterDir.appendingPathComponent("cards", isDirectory: true)

                guard FileManager.default.fileExists(atPath: cardsDir.path) else { continue }

                let cardFiles = try cardMetaURLs(in: cardsDir)
                let cards = try cardFiles
                    .compactMap { url -> KnowledgePointMeta? in
                        let data = try Data(contentsOf: url)
                        return try JSONDecoder().decode(KnowledgePointMeta.self, from: data)
                    }

                let sectionCards = cards
                    .filter({ $0.sectionID == sectionID })
                    .sorted(by: { $0.sortNo < $1.sortNo })
                guard !sectionCards.isEmpty else {
                    continue
                }

                let chapterMetaURL = chapterDir.appendingPathComponent("chapter_meta.json")
                let chapterMeta = try? decodeChapterMeta(at: chapterMetaURL)
                let contents: [KnowledgeCardStudyContent] = sectionCards.compactMap { card in
                    let markdownURL = cardsDir.appendingPathComponent(card.contentFile)
                    guard let markdown = try? String(contentsOf: markdownURL, encoding: .utf8) else { return nil }
                    let section = chapterMeta?.sections.first(where: { $0.sectionID == card.sectionID })
                    let headerTitle = makeHeaderTitle(chapterMeta: chapterMeta, section: section)
                    let chipTitle = "知识卡片 \(card.sortNo)"

                    return KnowledgeCardStudyContent(
                        pointID: card.pointID,
                        chapterID: chapterID,
                        sectionID: card.sectionID,
                        headerTitle: headerTitle,
                        knowledgeMarkdown: markdown,
                        keyPointsMarkdown: normalizedText(card.keyPoints),
                        mnemonicsMarkdown: normalizedText(card.mnemonics),
                        chipTitle: chipTitle
                    )
                }

                if !contents.isEmpty {
                    return contents
                }
            }
        }

        throw DataStoreError.notFound(diagnostics: makeRootDiagnostics())
    }

    private static func makeHeaderTitle(
        chapterMeta: ChapterMeta?,
        section: ChapterSection?
    ) -> String {
        guard let chapterMeta, let section else {
            return "1.1 信息与信息化"
        }
        return "\(chapterMeta.sortNo).\(section.sortNo) \(section.title)"
    }

    private static func chapterPathCandidates(chapterID: String) -> [String] {
        ["chapters/\(chapterID)", chapterID]
    }

    private static func loadDirectoryTreeFromDataSources() throws -> [KnowledgeDirectoryChapter] {
        for root in candidateRootDirectories() {
            let subjectIndexURL = root.appendingPathComponent("subject_index.json")
            guard FileManager.default.fileExists(atPath: subjectIndexURL.path) else { continue }

            let subjectIndexData = try Data(contentsOf: subjectIndexURL)
            let subjectIndex = try JSONDecoder().decode(SubjectIndex.self, from: subjectIndexData)

            var chapters: [KnowledgeDirectoryChapter] = []
            for (position, chapterItem) in subjectIndex.chapters.enumerated() {
                let chapterSortNo = position + 1
                let chapterMeta = loadChapterMeta(root: root, chapterID: chapterItem.chapterID)

                let resolvedSortNo = chapterMeta?.sortNo ?? chapterSortNo
                let chapterTitle = "第\(toChineseNumeral(resolvedSortNo))章 \(chapterMeta?.title ?? chapterItem.title)"
                let sections: [KnowledgeDirectorySection] = (chapterMeta?.sections ?? [])
                    .sorted { $0.sortNo < $1.sortNo }
                    .map { section in
                        KnowledgeDirectorySection(
                            id: section.sectionID,
                            title: "\(resolvedSortNo).\(section.sortNo) \(section.title)",
                            sortNo: section.sortNo
                        )
                    }

                chapters.append(
                    KnowledgeDirectoryChapter(
                        id: chapterItem.chapterID,
                        title: chapterTitle,
                        sortNo: resolvedSortNo,
                        sections: sections
                    )
                )
            }

            if !chapters.isEmpty {
                return chapters.sorted { $0.sortNo < $1.sortNo }
            }
        }

        throw DataStoreError.notFound(diagnostics: makeRootDiagnostics())
    }

    private static func loadChapterMeta(root: URL, chapterID: String) -> ChapterMeta? {
        for chapterPath in chapterPathCandidates(chapterID: chapterID) {
            let chapterMetaURL = root
                .appendingPathComponent(chapterPath, isDirectory: true)
                .appendingPathComponent("chapter_meta.json")
            if let chapterMeta = try? decodeChapterMeta(at: chapterMetaURL) {
                return chapterMeta
            }
        }
        return nil
    }

    private static func toChineseNumeral(_ value: Int) -> String {
        let numerals = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
        guard value > 0 else { return "零" }
        if value < 10 { return numerals[value] }
        if value == 10 { return "十" }
        if value < 20 { return "十\(numerals[value - 10])" }
        if value % 10 == 0 {
            return "\(numerals[value / 10])十"
        }
        return "\(numerals[value / 10])十\(numerals[value % 10])"
    }

    private static func candidateRootDirectories() -> [URL] {
        guard let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first else {
            return []
        }
        return [
            docs.appendingPathComponent("cache/cards/content_package/public/subjects/high_itpmp", isDirectory: true),
            docs.appendingPathComponent("cache/cards/subjects/high_itpmp", isDirectory: true),
            docs.appendingPathComponent("cache/cards", isDirectory: true)
        ]
    }

    private static func cardMetaURLs(in cardsDirectory: URL) throws -> [URL] {
        let urls = try FileManager.default.contentsOfDirectory(
            at: cardsDirectory,
            includingPropertiesForKeys: nil,
            options: [.skipsHiddenFiles]
        )
        return urls
            .filter { $0.pathExtension == "json" }
            .sorted { $0.lastPathComponent < $1.lastPathComponent }
    }

    private static func decodeChapterMeta(at url: URL) throws -> ChapterMeta {
        let data = try Data(contentsOf: url)
        return try JSONDecoder().decode(ChapterMeta.self, from: data)
    }

    private static func normalizedText(_ input: String?) -> String? {
        guard let input else { return nil }
        let value = input.trimmingCharacters(in: .whitespacesAndNewlines)
        return value.isEmpty ? nil : value
    }

    private static func makeRootDiagnostics() -> String {
        let roots = candidateRootDirectories()
        if roots.isEmpty {
            return "no document directory"
        }
        return roots.map { root in
            let exists = FileManager.default.fileExists(atPath: root.path)
            let subjectIndex = root.appendingPathComponent("subject_index.json")
            let hasSubjectIndex = FileManager.default.fileExists(atPath: subjectIndex.path)
            return "[\(exists ? "exists" : "missing")] \(root.path) | subject_index.json: \(hasSubjectIndex ? "yes" : "no")"
        }.joined(separator: "\n")
    }

    enum DataStoreError: Error {
        case notFound(diagnostics: String)
    }
}

extension KnowledgeCardDataStore.DataStoreError: LocalizedError {
    var errorDescription: String? {
        switch self {
        case .notFound(let diagnostics):
            return "未找到可用的知识卡数据目录。\n\(diagnostics)"
        }
    }
}

private struct KnowledgePointMeta: Decodable {
    let pointID: String
    let sectionID: String
    let sortNo: Int
    let contentFile: String
    let keyPoints: String?
    let mnemonics: String?

    enum CodingKeys: String, CodingKey {
        case pointID = "point_id"
        case sectionID = "section_id"
        case sortNo = "sort_no"
        case contentFile = "content_file"
        case contentMDPath = "content_md_path"
        case keyPoints = "key_points"
        case mnemonics
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        pointID = try container.decode(String.self, forKey: .pointID)
        sectionID = try container.decode(String.self, forKey: .sectionID)
        sortNo = try container.decode(Int.self, forKey: .sortNo)

        if let directFile = try container.decodeIfPresent(String.self, forKey: .contentFile),
           !directFile.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            contentFile = directFile
        } else if let mdPath = try container.decodeIfPresent(String.self, forKey: .contentMDPath) {
            let fallback = URL(fileURLWithPath: mdPath).lastPathComponent
            guard !fallback.isEmpty else {
                throw DecodingError.dataCorruptedError(
                    forKey: .contentFile,
                    in: container,
                    debugDescription: "missing content_file/content_md_path"
                )
            }
            contentFile = fallback
        } else {
            throw DecodingError.dataCorruptedError(
                forKey: .contentFile,
                in: container,
                debugDescription: "missing content_file/content_md_path"
            )
        }

        keyPoints = try Self.decodeFlexibleText(forKey: .keyPoints, in: container)
        mnemonics = try Self.decodeFlexibleText(forKey: .mnemonics, in: container)
    }

    private static func decodeFlexibleText(
        forKey key: CodingKeys,
        in container: KeyedDecodingContainer<CodingKeys>
    ) throws -> String? {
        if let scalar = try container.decodeIfPresent(String.self, forKey: key) {
            return scalar
        }
        if let list = try container.decodeIfPresent([String].self, forKey: key) {
            let merged = list
                .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
                .filter { !$0.isEmpty }
                .joined(separator: "\n")
            return merged.isEmpty ? nil : merged
        }
        return nil
    }
}

private struct ChapterMeta: Decodable {
    let chapterID: String
    let title: String
    let sortNo: Int
    let sections: [ChapterSection]

    enum CodingKeys: String, CodingKey {
        case chapterID = "chapter_id"
        case title
        case sortNo = "sort_no"
        case sections
    }
}

private struct ChapterSection: Decodable {
    let sectionID: String
    let title: String
    let sortNo: Int

    enum CodingKeys: String, CodingKey {
        case sectionID = "section_id"
        case title
        case sortNo = "sort_no"
    }
}

private struct SubjectIndex: Decodable {
    let chapters: [SubjectChapter]
}

private struct SubjectChapter: Decodable {
    let chapterID: String
    let title: String

    enum CodingKeys: String, CodingKey {
        case chapterID = "chapter_id"
        case title
    }
}
