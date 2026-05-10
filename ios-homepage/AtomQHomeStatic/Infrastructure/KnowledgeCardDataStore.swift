import Foundation

struct KnowledgeCardStudyContent {
    let headerTitle: String
    let knowledgeMarkdown: String
    let keyPointsMarkdown: String?
    let mnemonicsMarkdown: String?
    let chipTitle: String
}

enum KnowledgeCardDataStore {
    static func loadStudyContent(
        chapterID: String = "ch_01",
        sectionID: String = "sec_01_01"
    ) -> KnowledgeCardStudyContent {
        do {
            return try loadFromDataSources(chapterID: chapterID, sectionID: sectionID)
        } catch {
            return KnowledgeCardStudyContent(
                headerTitle: "1.1 信息与信息化",
                knowledgeMarkdown: "信息是==物质、能量及其属性的标示的集合==，是==确定性的增加==。",
                keyPointsMarkdown: nil,
                mnemonicsMarkdown: nil,
                chipTitle: "知识卡片 1"
            )
        }
    }

    private static func loadFromDataSources(
        chapterID: String,
        sectionID: String
    ) throws -> KnowledgeCardStudyContent {
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

                guard let targetCard = cards
                    .filter({ $0.sectionID == sectionID })
                    .sorted(by: { $0.sortNo < $1.sortNo })
                    .first ?? cards.sorted(by: { $0.sortNo < $1.sortNo }).first
                else {
                    continue
                }

                let markdownURL = cardsDir.appendingPathComponent(targetCard.contentFile)
                guard let markdown = try? String(contentsOf: markdownURL, encoding: .utf8) else { continue }

                let chapterMetaURL = chapterDir.appendingPathComponent("chapter_meta.json")
                let chapterMeta = try? decodeChapterMeta(at: chapterMetaURL)
                let section = chapterMeta?.sections.first(where: { $0.sectionID == targetCard.sectionID })
                let headerTitle = makeHeaderTitle(chapterMeta: chapterMeta, section: section)
                let chipTitle = "知识卡片 \(targetCard.sortNo)"

                return KnowledgeCardStudyContent(
                    headerTitle: headerTitle,
                    knowledgeMarkdown: markdown,
                    keyPointsMarkdown: normalizedText(targetCard.keyPoints),
                    mnemonicsMarkdown: normalizedText(targetCard.mnemonics),
                    chipTitle: chipTitle
                )
            }
        }

        throw DataStoreError.notFound
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

    private static func candidateRootDirectories() -> [URL] {
        var roots: [URL] = []
        let fm = FileManager.default

        #if DEBUG
        let repoRoot = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
        roots.append(repoRoot.appendingPathComponent("data/知识点集合", isDirectory: true))
        #endif

        if let docs = fm.urls(for: .documentDirectory, in: .userDomainMask).first {
            roots.append(docs.appendingPathComponent("cache/cards", isDirectory: true))
        }

        if let resourceURL = Bundle.main.resourceURL {
            roots.append(resourceURL.appendingPathComponent("default_cards", isDirectory: true))
            roots.append(resourceURL.appendingPathComponent("Resources/default_cards", isDirectory: true))
        }

        let sourceFallback = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .appendingPathComponent("Resources/default_cards", isDirectory: true)
        roots.append(sourceFallback)

        var uniqueRoots: [URL] = []
        var seen = Set<String>()
        for root in roots where seen.insert(root.path).inserted {
            uniqueRoots.append(root)
        }
        return uniqueRoots
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

    private enum DataStoreError: Error {
        case notFound
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
        case keyPoints = "key_points"
        case mnemonics
    }
}

private struct ChapterMeta: Decodable {
    let sortNo: Int
    let sections: [ChapterSection]

    enum CodingKeys: String, CodingKey {
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
