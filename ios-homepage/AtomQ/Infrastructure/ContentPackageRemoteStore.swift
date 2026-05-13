import Foundation

enum ContentPackageRemoteStore {
    static func refreshFreeContentRequired() async throws {
        guard let cacheRoot = ContentPackageConfig.publicContentCacheRoot else {
            throw RemoteStoreError.missingCacheRoot
        }

        guard let baseURL = ContentPackageConfig.publicContentBaseURL else {
            throw RemoteStoreError.missingBaseURL
        }
        try await PublicContentDownloader(baseURL: baseURL, cacheRoot: cacheRoot).refreshIfNeeded()
    }
}

private enum ContentPackageConfig {
    static var publicContentBaseURL: URL? {
        guard let rawValue = Bundle.main.object(forInfoDictionaryKey: "ATOMQ_PUBLIC_CONTENT_BASE_URL") as? String else {
            return nil
        }

        var value = rawValue.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !value.isEmpty, !value.contains("YOUR_OSS_BUCKET") else { return nil }
        if !value.hasSuffix("/") {
            value.append("/")
        }
        return URL(string: value)
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
    case badResponse(url: String, statusCode: Int)
    case unsafePath(String)
}

extension RemoteStoreError: LocalizedError {
    var errorDescription: String? {
        switch self {
        case .missingBaseURL:
            return "缺少 ATOMQ_PUBLIC_CONTENT_BASE_URL 配置。"
        case .missingCacheRoot:
            return "无法定位 App 的本地缓存目录。"
        case .badResponse(let url, let statusCode):
            return "远程资源访问失败（HTTP \(statusCode)）：\(url)"
        case .unsafePath(let path):
            return "远程文件路径不安全：\(path)"
        }
    }
}
