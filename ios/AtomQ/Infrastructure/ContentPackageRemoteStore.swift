import CryptoKit
import Foundation

enum ContentPackageRemoteStore {
    static let didClearLocalCacheNotification = Notification.Name("AtomQContentPackageRemoteStoreDidClearLocalCache")

    static var canRefreshPublicContent: Bool {
        ContentPackageConfig.publicContentCacheRoot != nil && ContentPackageConfig.remoteAccess != nil
    }

    static var hasCachedPublicContent: Bool {
        guard let cacheRoot = ContentPackageConfig.publicContentCacheRoot else {
            return false
        }

        let fm = FileManager.default
        let manifestURL = cacheRoot.appendingPathComponent("manifest.json")
        let fileIndexURL = cacheRoot.appendingPathComponent("file_index.json")
        let subjectIndexURL = cacheRoot.appendingPathComponent("subjects/high_itpmp/subject_index.json")
        return fm.fileExists(atPath: manifestURL.path)
            && fm.fileExists(atPath: fileIndexURL.path)
            && fm.fileExists(atPath: subjectIndexURL.path)
            && localPublicContentLooksComplete(cacheRoot: cacheRoot, fileIndexURL: fileIndexURL)
    }

    static func refreshFreeContentRequired() async throws {
        guard let cacheRoot = ContentPackageConfig.publicContentCacheRoot else {
            throw RemoteStoreError.missingCacheRoot
        }

        guard let remoteAccess = ContentPackageConfig.remoteAccess else {
            throw RemoteStoreError.missingRemoteAccess
        }
        print("[AtomQ][RemoteContent] refresh start cache=\(cacheRoot.path)")
        try await ContentPackageRefreshCoordinator.shared.refresh(remoteAccess: remoteAccess, cacheRoot: cacheRoot)
        print("[AtomQ][RemoteContent] refresh success")
    }

    static func clearLocalCache() throws {
        guard let cardsCacheRoot = ContentPackageConfig.cardsCacheRoot else {
            throw RemoteStoreError.missingCacheRoot
        }
        let fm = FileManager.default
        print("[AtomQ][RemoteContent] clear local cache root=\(cardsCacheRoot.path)")
        ContentPackageCacheState.invalidate()
        if fm.fileExists(atPath: cardsCacheRoot.path) {
            try fm.removeItem(at: cardsCacheRoot)
        }
        NotificationCenter.default.post(name: didClearLocalCacheNotification, object: nil)
    }

    private static func localPublicContentLooksComplete(cacheRoot: URL, fileIndexURL: URL) -> Bool {
        guard let fileIndexData = try? Data(contentsOf: fileIndexURL),
              let fileIndex = try? JSONDecoder().decode(ContentFileIndex.self, from: fileIndexData)
        else {
            return false
        }

        let fm = FileManager.default
        return fileIndex.files.allSatisfy { file in
            guard !file.path.isEmpty,
                  !file.path.hasPrefix("/"),
                  !file.path.split(separator: "/").contains("..")
            else {
                return false
            }

            let url = cacheRoot.appendingPathComponent(file.path)
            guard fm.fileExists(atPath: url.path) else {
                return false
            }

            if let expectedBytes = file.bytes,
               let attributes = try? fm.attributesOfItem(atPath: url.path),
               let actualBytes = attributes[.size] as? NSNumber {
                return actualBytes.intValue == expectedBytes
            }

            return true
        }
    }
}

private enum ContentPackageCacheState {
    private static let lock = NSLock()
    private static var generation = 0

    static var currentGeneration: Int {
        lock.lock()
        defer { lock.unlock() }
        return generation
    }

    static func invalidate() {
        lock.lock()
        generation += 1
        lock.unlock()
    }
}

private actor ContentPackageRefreshCoordinator {
    static let shared = ContentPackageRefreshCoordinator()

    private var inFlightRefresh: (generation: Int, task: Task<Void, Error>)?

    func refresh(remoteAccess: ContentPackageConfig.RemoteAccess, cacheRoot: URL) async throws {
        let generation = ContentPackageCacheState.currentGeneration
        if let inFlightRefresh, inFlightRefresh.generation == generation {
            print("[AtomQ][RemoteContent] joining in-flight refresh")
            try await inFlightRefresh.task.value
            return
        }
        if let inFlightRefresh {
            inFlightRefresh.task.cancel()
            self.inFlightRefresh = nil
        }

        let task = Task {
            try await PublicContentDownloader(remoteAccess: remoteAccess, cacheRoot: cacheRoot).refreshIfNeeded()
        }
        inFlightRefresh = (generation, task)

        do {
            try await task.value
            if inFlightRefresh?.generation == generation {
                inFlightRefresh = nil
            }
        } catch {
            if inFlightRefresh?.generation == generation {
                inFlightRefresh = nil
            }
            throw error
        }
    }
}

private enum ContentPackageConfig {
    struct RemoteAccess {
        let publicBaseURL: URL?
        let signURL: URL?
        let objectPrefix: String
    }

    static var remoteAccess: RemoteAccess? {
        let baseURL = publicContentBaseURL
        let signURL = ossSignURL
        guard baseURL != nil || signURL != nil else { return nil }

        return RemoteAccess(
            publicBaseURL: baseURL,
            signURL: signURL,
            objectPrefix: ossObjectPrefix
        )
    }

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

    static var ossSignURL: URL? {
        guard let rawValue = Bundle.main.object(forInfoDictionaryKey: "ATOMQ_OSS_SIGN_URL") as? String else {
            return nil
        }

        let value = rawValue.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !value.isEmpty, !value.contains("YOUR_SIGNER") else { return nil }
        return URL(string: value)
    }

    static var ossObjectPrefix: String {
        guard let rawValue = Bundle.main.object(forInfoDictionaryKey: "ATOMQ_OSS_OBJECT_PREFIX") as? String else {
            return "atomq/content_package/public/"
        }

        var value = rawValue.trimmingCharacters(in: .whitespacesAndNewlines)
        while value.hasPrefix("/") { value.removeFirst() }
        if !value.hasSuffix("/") { value.append("/") }
        return value
    }

    static var publicContentCacheRoot: URL? {
        cardsCacheRoot?.appendingPathComponent("content_package/public", isDirectory: true)
    }

    static var cardsCacheRoot: URL? {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)
            .first?
            .appendingPathComponent("cache/cards", isDirectory: true)
    }
}

private struct PublicContentDownloader {
    let remoteAccess: ContentPackageConfig.RemoteAccess
    let cacheRoot: URL
    private let cacheGeneration: Int
    private let session: URLSession

    init(remoteAccess: ContentPackageConfig.RemoteAccess, cacheRoot: URL) {
        self.remoteAccess = remoteAccess
        self.cacheRoot = cacheRoot
        self.cacheGeneration = ContentPackageCacheState.currentGeneration

        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 15
        config.timeoutIntervalForResource = 45
        config.waitsForConnectivity = true
        self.session = URLSession(configuration: config)
    }

    func refreshIfNeeded() async throws {
        print("[AtomQ][RemoteContent] fetch manifest.json")
        let remoteManifestData = try await fetch(relativePath: "manifest.json")
        let remoteManifest = try JSONDecoder().decode(ContentManifest.self, from: remoteManifestData)
        let fileIndexPath = remoteManifest.distribution?.fileIndex ?? "file_index.json"

        print("[AtomQ][RemoteContent] fetch \(fileIndexPath)")
        let fileIndexData = try await fetch(relativePath: fileIndexPath)
        let fileIndex = try JSONDecoder().decode(ContentFileIndex.self, from: fileIndexData)
        print("[AtomQ][RemoteContent] file count=\(fileIndex.files.count)")

        if let localManifest = try? loadLocalManifest(),
           localManifest.contentVersion == remoteManifest.contentVersion,
           isLocalCacheCurrent(remoteFileIndex: fileIndex) {
            print("[AtomQ][RemoteContent] cache complete version=\(remoteManifest.contentVersion)")
            return
        }

        try write(remoteManifestData, to: "manifest.json")
        try write(fileIndexData, to: fileIndexPath)

        let downloadableFiles = fileIndex.files.filter { file in
            file.path != "manifest.json"
                && file.path != "file_index.json"
                && !isLocalFileCurrent(file)
        }
        let orderedFiles = prioritizedFiles(from: downloadableFiles)

        print("[AtomQ][RemoteContent] download file count=\(orderedFiles.count)")
        for (index, file) in orderedFiles.enumerated() {
            try await download(file, progress: "\(index + 1)/\(orderedFiles.count)")
        }
        print("[AtomQ][RemoteContent] refresh download complete")
    }

    private func prioritizedFiles(from files: [ContentFile]) -> [ContentFile] {
        let requiredPaths = Set([
            "subjects/high_itpmp/subject_index.json"
        ])
        var seenPaths = Set<String>()
        var prioritized: [ContentFile] = []

        func append(_ file: ContentFile) {
            guard !seenPaths.contains(file.path) else { return }
            seenPaths.insert(file.path)
            prioritized.append(file)
        }

        // Fetch the first screen first, then keep going until the local package is complete.
        for file in files where requiredPaths.contains(file.path) {
            append(file)
        }
        for file in files where file.path == "subjects/high_itpmp/chapters/ch_01/chapter_meta.json" {
            append(file)
        }
        for file in files where file.path.hasPrefix("subjects/high_itpmp/chapters/ch_01/cards/ch_01_sec_01_") {
            append(file)
        }
        for file in files {
            append(file)
        }

        return prioritized
    }

    private func download(_ file: ContentFile, progress: String) async throws {
        print("[AtomQ][RemoteContent] downloading \(progress): \(file.path)")
        let data = try await fetch(relativePath: file.path)
        try write(data, to: file.path)
    }

    private func fetch(relativePath: String) async throws -> Data {
        guard isSafeRelativePath(relativePath) else {
            throw RemoteStoreError.unsafePath(relativePath)
        }

        if let signURL = remoteAccess.signURL {
            let signedURL = try await signedDownloadURL(for: relativePath, signURL: signURL)
            return try await fetchData(from: signedURL, label: relativePath)
        }

        guard let baseURL = remoteAccess.publicBaseURL else {
            throw RemoteStoreError.missingRemoteAccess
        }
        return try await fetchData(from: baseURL.appendingPathComponent(relativePath), label: relativePath)
    }

    private func signedDownloadURL(for relativePath: String, signURL: URL) async throws -> URL {
        let objectKey = remoteAccess.objectPrefix + relativePath
        var components = URLComponents(url: signURL, resolvingAgainstBaseURL: false)
        var queryItems = components?.queryItems ?? []
        queryItems.append(URLQueryItem(name: "path", value: objectKey))
        components?.queryItems = queryItems

        guard let requestURL = components?.url else {
            throw RemoteStoreError.invalidSignURL(signURL.absoluteString)
        }

        let data = try await fetchData(from: requestURL, label: "sign:\(objectKey)")
        let payload = try JSONDecoder().decode(SignedURLPayload.self, from: data)
        guard let url = URL(string: payload.url) else {
            throw RemoteStoreError.invalidSignedURL(payload.url)
        }
        return url
    }

    private func fetchData(from url: URL, label: String) async throws -> Data {
        var lastError: Error?

        for attempt in 1...3 {
            do {
                let (data, response) = try await session.data(from: url)
                guard let httpResponse = response as? HTTPURLResponse,
                      (200..<300).contains(httpResponse.statusCode)
                else {
                    let statusCode = (response as? HTTPURLResponse)?.statusCode ?? -1
                    throw RemoteStoreError.badResponse(url: url.absoluteString, statusCode: statusCode)
                }
                return data
            } catch {
                lastError = error
                guard attempt < 3, shouldRetry(error) else { break }
                try await Task.sleep(nanoseconds: UInt64(attempt) * 400_000_000)
            }
        }

        throw RemoteStoreError.requestFailed(path: label, url: url.absoluteString, underlying: lastError?.localizedDescription ?? "unknown")
    }

    private func shouldRetry(_ error: Error) -> Bool {
        if case RemoteStoreError.badResponse(_, let statusCode) = error {
            return statusCode == 408 || statusCode == 425 || statusCode == 429 || (500..<600).contains(statusCode)
        }

        guard let urlError = error as? URLError else { return false }
        switch urlError.code {
        case .timedOut,
             .cannotFindHost,
             .cannotConnectToHost,
             .networkConnectionLost,
             .dnsLookupFailed,
             .notConnectedToInternet,
             .internationalRoamingOff,
             .callIsActive,
             .dataNotAllowed:
            return true
        default:
            return false
        }
    }

    private func write(_ data: Data, to relativePath: String) throws {
        guard isSafeRelativePath(relativePath) else {
            throw RemoteStoreError.unsafePath(relativePath)
        }
        guard isCacheGenerationCurrent else {
            throw RemoteStoreError.cacheInvalidated
        }

        let destination = cacheRoot.appendingPathComponent(relativePath)
        try FileManager.default.createDirectory(
            at: destination.deletingLastPathComponent(),
            withIntermediateDirectories: true
        )
        try data.write(to: destination, options: .atomic)
    }

    private var isCacheGenerationCurrent: Bool {
        cacheGeneration == ContentPackageCacheState.currentGeneration
    }

    private func loadLocalManifest() throws -> ContentManifest {
        let data = try Data(contentsOf: cacheRoot.appendingPathComponent("manifest.json"))
        return try JSONDecoder().decode(ContentManifest.self, from: data)
    }

    private func isLocalCacheCurrent(remoteFileIndex: ContentFileIndex) -> Bool {
        remoteFileIndex.files.allSatisfy { isLocalFileCurrent($0) }
    }

    private func isLocalFileCurrent(_ file: ContentFile) -> Bool {
        guard isSafeRelativePath(file.path) else { return false }
        let fileURL = cacheRoot.appendingPathComponent(file.path)
        guard let data = try? Data(contentsOf: fileURL) else { return false }

        if let expectedBytes = file.bytes, data.count != expectedBytes {
            return false
        }

        guard let expectedSHA256 = file.sha256?.lowercased(), !expectedSHA256.isEmpty else {
            return true
        }

        let digest = SHA256.hash(data: data)
        let actualSHA256 = digest.map { String(format: "%02x", $0) }.joined()
        return actualSHA256 == expectedSHA256
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
    let bytes: Int?
    let sha256: String?
}

private struct SignedURLPayload: Decodable {
    let url: String
}

private enum RemoteStoreError: Error {
    case missingRemoteAccess
    case missingCacheRoot
    case badResponse(url: String, statusCode: Int)
    case invalidSignURL(String)
    case invalidSignedURL(String)
    case requestFailed(path: String, url: String, underlying: String)
    case cacheInvalidated
    case unsafePath(String)
}

extension RemoteStoreError: LocalizedError {
    var errorDescription: String? {
        switch self {
        case .missingRemoteAccess:
            return "缺少远程内容配置：请配置 ATOMQ_PUBLIC_CONTENT_BASE_URL，或配置 ATOMQ_OSS_SIGN_URL + ATOMQ_OSS_OBJECT_PREFIX。"
        case .missingCacheRoot:
            return "无法定位 App 的本地缓存目录。"
        case .badResponse(let url, let statusCode):
            return "远程资源访问失败（HTTP \(statusCode)）：\(url)"
        case .invalidSignURL(let url):
            return "OSS 签名服务地址无效：\(url)"
        case .invalidSignedURL(let url):
            return "OSS 签名服务返回了无效下载地址：\(url)"
        case .requestFailed(let path, let url, let underlying):
            return "远程资源请求失败：\(path)\nURL：\(url)\n原因：\(underlying)"
        case .cacheInvalidated:
            return "本地内容缓存已被清除，本次下载已取消。"
        case .unsafePath(let path):
            return "远程文件路径不安全：\(path)"
        }
    }
}
