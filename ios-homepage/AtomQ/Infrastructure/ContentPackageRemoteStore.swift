import Foundation

enum ContentPackageRemoteStore {
    static func refreshFreeContentRequired() async throws {
        guard let cacheRoot = ContentPackageConfig.publicContentCacheRoot else {
            throw RemoteStoreError.missingCacheRoot
        }

        var errors: [Error] = []

        if let signURL = ContentPackageConfig.ossSignURL {
            do {
                try await SignedURLContentDownloader(
                    signURL: signURL,
                    objectPrefix: ContentPackageConfig.ossObjectPrefix,
                    cacheRoot: cacheRoot
                ).refreshIfNeeded()
                return
            } catch {
                errors.append(error)
            }
        }

        guard let rawBaseURL = ContentPackageConfig.publicContentBaseURLRaw else {
            if errors.isEmpty {
                throw RemoteStoreError.missingBaseURL
            }
            throw RemoteStoreError.allCandidatesFailed(candidates: [], errors: errors)
        }
        let candidates = ContentPackageConfig.candidateBaseURLs(from: rawBaseURL)
        guard !candidates.isEmpty else {
            throw RemoteStoreError.invalidBaseURL(rawBaseURL)
        }

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

    static var ossSignURL: URL? {
        guard let raw = Bundle.main.object(forInfoDictionaryKey: "ATOMQ_OSS_SIGN_URL") as? String else {
            return nil
        }
        let value = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !value.isEmpty else { return nil }
        return URL(string: value)
    }

    static var ossObjectPrefix: String {
        let configured = (Bundle.main.object(forInfoDictionaryKey: "ATOMQ_OSS_OBJECT_PREFIX") as? String)?
            .trimmingCharacters(in: .whitespacesAndNewlines)
        let fallback = "atomq/content_package/public/"
        var prefix = (configured?.isEmpty == false) ? configured! : fallback
        if prefix.hasPrefix("/") {
            prefix.removeFirst()
        }
        if !prefix.hasSuffix("/") {
            prefix.append("/")
        }
        return prefix
    }
}

private struct PublicContentDownloader {
    let baseURL: URL
    let cacheRoot: URL

    func refreshIfNeeded() async throws {
        let remoteManifestData = try await fetch(relativePath: "manifest.json")
        let remoteManifest = try JSONDecoder().decode(ContentManifest.self, from: remoteManifestData)
        let fileIndexPath = remoteManifest.distribution?.fileIndex ?? "file_index.json"

        if let localManifest = try? loadLocalManifest(),
           localManifest.contentVersion == remoteManifest.contentVersion,
           isLocalCacheComplete(fileIndexRelativePath: fileIndexPath) {
            return
        }

        let fileIndexData = try await fetch(relativePath: fileIndexPath)
        let fileIndex = try JSONDecoder().decode(ContentFileIndex.self, from: fileIndexData)

        try write(remoteManifestData, to: "manifest.json")
        try write(fileIndexData, to: fileIndexPath)

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

    private func isLocalCacheComplete(fileIndexRelativePath: String) -> Bool {
        guard isSafeRelativePath(fileIndexRelativePath) else { return false }
        let fileIndexURL = cacheRoot.appendingPathComponent(fileIndexRelativePath)
        guard let data = try? Data(contentsOf: fileIndexURL),
              let localFileIndex = try? JSONDecoder().decode(ContentFileIndex.self, from: data)
        else { return false }

        for file in localFileIndex.files {
            guard isSafeRelativePath(file.path) else { return false }
            let fileURL = cacheRoot.appendingPathComponent(file.path)
            if !FileManager.default.fileExists(atPath: fileURL.path) {
                return false
            }
        }
        return true
    }

    private func isSafeRelativePath(_ value: String) -> Bool {
        !value.isEmpty && !value.hasPrefix("/") && !value.split(separator: "/").contains("..")
    }
}

private struct SignedURLContentDownloader {
    let signURL: URL
    let objectPrefix: String
    let cacheRoot: URL

    func refreshIfNeeded() async throws {
        let remoteManifestData = try await fetch(relativePath: "manifest.json")
        let remoteManifest = try JSONDecoder().decode(ContentManifest.self, from: remoteManifestData)
        let fileIndexPath = remoteManifest.distribution?.fileIndex ?? "file_index.json"

        if let localManifest = try? loadLocalManifest(),
           localManifest.contentVersion == remoteManifest.contentVersion,
           isLocalCacheComplete(fileIndexRelativePath: fileIndexPath) {
            return
        }

        let fileIndexData = try await fetch(relativePath: fileIndexPath)
        let fileIndex = try JSONDecoder().decode(ContentFileIndex.self, from: fileIndexData)

        try write(remoteManifestData, to: "manifest.json")
        try write(fileIndexData, to: fileIndexPath)

        for file in fileIndex.files where file.path != "manifest.json" && file.path != "file_index.json" {
            let data = try await fetch(relativePath: file.path)
            try write(data, to: file.path)
        }
    }

    private func fetch(relativePath: String) async throws -> Data {
        guard !relativePath.isEmpty else {
            throw RemoteStoreError.unsafePath(relativePath)
        }

        var components = URLComponents(url: signURL, resolvingAgainstBaseURL: false)
        let fullPath = objectPrefix + relativePath
        components?.queryItems = [URLQueryItem(name: "path", value: fullPath)]
        guard let requestURL = components?.url else {
            throw RemoteStoreError.invalidSignURL(signURL.absoluteString)
        }

        let (signData, signResponse) = try await URLSession.shared.data(from: requestURL)
        guard let signHttp = signResponse as? HTTPURLResponse, (200..<300).contains(signHttp.statusCode) else {
            let code = (signResponse as? HTTPURLResponse)?.statusCode ?? -1
            throw RemoteStoreError.badSignerResponse(url: requestURL.absoluteString, statusCode: code)
        }
        let signed = try JSONDecoder().decode(SignedURLResponse.self, from: signData)
        guard let downloadURL = URL(string: signed.url) else {
            throw RemoteStoreError.invalidSignedURL(signed.url)
        }

        let (data, response) = try await URLSession.shared.data(from: downloadURL)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            let code = (response as? HTTPURLResponse)?.statusCode ?? -1
            throw RemoteStoreError.badResponse(url: downloadURL.absoluteString, statusCode: code)
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

    private func isLocalCacheComplete(fileIndexRelativePath: String) -> Bool {
        guard isSafeRelativePath(fileIndexRelativePath) else { return false }
        let fileIndexURL = cacheRoot.appendingPathComponent(fileIndexRelativePath)
        guard let data = try? Data(contentsOf: fileIndexURL),
              let localFileIndex = try? JSONDecoder().decode(ContentFileIndex.self, from: data)
        else { return false }

        for file in localFileIndex.files {
            guard isSafeRelativePath(file.path) else { return false }
            let fileURL = cacheRoot.appendingPathComponent(file.path)
            if !FileManager.default.fileExists(atPath: fileURL.path) {
                return false
            }
        }
        return true
    }

    private func isSafeRelativePath(_ value: String) -> Bool {
        !value.isEmpty && !value.hasPrefix("/") && !value.split(separator: "/").contains("..")
    }
}

private struct SignedURLResponse: Decodable {
    let url: String
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
    case badSignerResponse(url: String, statusCode: Int)
    case invalidSignURL(String)
    case invalidSignedURL(String)
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
        case .badSignerResponse(let url, let statusCode):
            return "签名服务访问失败（HTTP \(statusCode)）：\(url)"
        case .invalidSignURL(let url):
            return "签名服务地址非法：\(url)"
        case .invalidSignedURL(let url):
            return "签名服务返回了非法下载地址：\(url)"
        case .allCandidatesFailed(let candidates, let errors):
            let baseList = candidates.map(\.absoluteString).joined(separator: "\n")
            let details = errors.map { String(describing: $0) }.joined(separator: "\n")
            return "远程内容目录自动探测失败。\n候选目录：\n\(baseList)\n错误详情：\n\(details)"
        case .unsafePath(let path):
            return "远程文件路径不安全：\(path)"
        }
    }
}
