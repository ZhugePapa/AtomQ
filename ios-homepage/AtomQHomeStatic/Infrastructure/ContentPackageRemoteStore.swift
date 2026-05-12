import Foundation

enum ContentPackageRemoteStore {
    static func refreshFreeContentRequired() async throws {
        guard let rawBaseURL = ContentPackageConfig.publicContentBaseURLRaw else {
            throw RemoteStoreError.missingBaseURL
        }
        guard let cacheRoot = ContentPackageConfig.publicContentCacheRoot else {
            throw RemoteStoreError.missingCacheRoot
        }
        let candidates = ContentPackageConfig.candidateBaseURLs(from: rawBaseURL)
        guard !candidates.isEmpty else {
            throw RemoteStoreError.invalidBaseURL(rawBaseURL)
        }

        var errors: [Error] = []
        for candidate in candidates {
            do {
                try await PublicContentDownloader(baseURL: candidate, cacheRoot: cacheRoot).refreshIfNeeded()
                return
            } catch {
                errors.append(error)
            }
        }
        throw RemoteStoreError.allCandidatesFailed(candidates: candidates, errors: errors)
    }
}

private enum ContentPackageConfig {
    static var publicContentBaseURLRaw: String? {
        guard let rawValue = Bundle.main.object(forInfoDictionaryKey: "ATOMQ_PUBLIC_CONTENT_BASE_URL") as? String else {
            return nil
        }

        let value = rawValue.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !value.isEmpty, !value.contains("YOUR_OSS_BUCKET") else { return nil }
        return value
    }

    static func candidateBaseURLs(from rawValue: String) -> [URL] {
        guard let sourceURL = URL(string: rawValue) else { return [] }
        guard var components = URLComponents(url: sourceURL, resolvingAgainstBaseURL: false) else { return [] }

        let sourcePath = sourceURL.path
        var candidatePaths: [String] = []
        if sourcePath.isEmpty || sourcePath == "/" {
            candidatePaths = [
                "/content_package/public/",
                "/public/",
                "/content_package/",
                "/"
            ]
        } else {
            var normalized = sourcePath
            if !normalized.hasSuffix("/") {
                normalized.append("/")
            }
            candidatePaths.append(normalized)

            let trimmed = normalized.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
            if !trimmed.isEmpty {
                let segments = trimmed.split(separator: "/").map(String.init)
                if segments.last == "public", segments.count > 1 {
                    let parent = "/" + segments.dropLast().joined(separator: "/") + "/"
                    candidatePaths.append(parent)
                }
            }

            candidatePaths.append("/content_package/public/")
            candidatePaths.append("/public/")
            candidatePaths.append("/content_package/")
            candidatePaths.append("/")
        }

        var urls: [URL] = []
        var seen = Set<String>()
        for path in candidatePaths {
            components.path = path
            guard let url = components.url else { continue }
            let key = url.absoluteString
            if seen.insert(key).inserted {
                urls.append(url)
            }
        }
        return urls
    }

    static var publicContentCacheRoot: URL? {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)
            .first?
            .appendingPathComponent("cache/cards/content_package/public", isDirectory: true)
    }
}

private struct PublicContentDownloader {
    let baseURL: URL
    let cacheRoot: URL

    func refreshIfNeeded() async throws {
        let remoteManifestData = try await fetch(relativePath: "manifest.json")
        let remoteManifest = try JSONDecoder().decode(ContentManifest.self, from: remoteManifestData)

        if let localManifest = try? loadLocalManifest(),
           localManifest.contentVersion == remoteManifest.contentVersion,
           FileManager.default.fileExists(atPath: cacheRoot.appendingPathComponent("file_index.json").path) {
            return
        }

        let fileIndexData = try await fetch(relativePath: remoteManifest.distribution?.fileIndex ?? "file_index.json")
        let fileIndex = try JSONDecoder().decode(ContentFileIndex.self, from: fileIndexData)

        try write(remoteManifestData, to: "manifest.json")
        try write(fileIndexData, to: "file_index.json")

        for file in fileIndex.files where file.path != "manifest.json" && file.path != "file_index.json" {
            let data = try await fetch(relativePath: file.path)
            try write(data, to: file.path)
        }
    }

    private func fetch(relativePath: String) async throws -> Data {
        let url = baseURL.appendingPathComponent(relativePath)
        let (data, response) = try await URLSession.shared.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              (200..<300).contains(httpResponse.statusCode)
        else {
            let statusCode = (response as? HTTPURLResponse)?.statusCode ?? -1
            throw RemoteStoreError.badResponse(url: url.absoluteString, statusCode: statusCode)
        }

        return data
    }

    private func write(_ data: Data, to relativePath: String) throws {
        guard isSafeRelativePath(relativePath) else {
            throw RemoteStoreError.unsafePath(relativePath)
        }

        let destination = cacheRoot.appendingPathComponent(relativePath)
        try FileManager.default.createDirectory(
            at: destination.deletingLastPathComponent(),
            withIntermediateDirectories: true
        )
        try data.write(to: destination, options: .atomic)
    }

    private func loadLocalManifest() throws -> ContentManifest {
        let data = try Data(contentsOf: cacheRoot.appendingPathComponent("manifest.json"))
        return try JSONDecoder().decode(ContentManifest.self, from: data)
    }

    private func isSafeRelativePath(_ value: String) -> Bool {
        !value.isEmpty && !value.hasPrefix("/") && !value.split(separator: "/").contains("..")
    }
}

private struct ContentManifest: Decodable {
    let contentVersion: String
    let distribution: ContentDistribution?

    enum CodingKeys: String, CodingKey {
        case contentVersion = "content_version"
        case distribution
    }
}

private struct ContentDistribution: Decodable {
    let fileIndex: String?

    enum CodingKeys: String, CodingKey {
        case fileIndex = "file_index"
    }
}

private struct ContentFileIndex: Decodable {
    let files: [ContentFile]
}

private struct ContentFile: Decodable {
    let path: String
}

private enum RemoteStoreError: Error {
    case missingBaseURL
    case missingCacheRoot
    case invalidBaseURL(String)
    case badResponse(url: String, statusCode: Int)
    case allCandidatesFailed(candidates: [URL], errors: [Error])
    case unsafePath(String)
}

extension RemoteStoreError: LocalizedError {
    var errorDescription: String? {
        switch self {
        case .missingBaseURL:
            return "缺少 ATOMQ_PUBLIC_CONTENT_BASE_URL 配置。"
        case .missingCacheRoot:
            return "无法定位 App 的本地缓存目录。"
        case .invalidBaseURL(let raw):
            return "ATOMQ_PUBLIC_CONTENT_BASE_URL 不是合法 URL：\(raw)"
        case .badResponse(let url, let statusCode):
            return "远程资源访问失败（HTTP \(statusCode)）：\(url)"
        case .allCandidatesFailed(let candidates, let errors):
            let baseList = candidates.map(\.absoluteString).joined(separator: "\n")
            let details = errors.map { String(describing: $0) }.joined(separator: "\n")
            return "远程内容目录自动探测失败。\n候选目录：\n\(baseList)\n错误详情：\n\(details)"
        case .unsafePath(let path):
            return "远程文件路径不安全：\(path)"
        }
    }
}
