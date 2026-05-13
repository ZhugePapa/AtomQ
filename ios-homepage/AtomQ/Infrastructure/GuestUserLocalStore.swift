import Foundation

enum GuestUserLocalStore {
    private static let masteredPointIDsKey = "guest.mastered_point_ids.v1"

    static func isPointMastered(_ pointID: String) -> Bool {
        let normalized = normalize(pointID)
        guard !normalized.isEmpty else { return false }
        return masteredPointIDs().contains(normalized)
    }

    static func setPointMastered(_ pointID: String, mastered: Bool) {
        let normalized = normalize(pointID)
        guard !normalized.isEmpty else { return }

        var current = masteredPointIDs()
        if mastered {
            current.insert(normalized)
        } else {
            current.remove(normalized)
        }
        UserDefaults.standard.set(Array(current).sorted(), forKey: masteredPointIDsKey)
    }

    static func masteredPointIDs() -> Set<String> {
        let raw = UserDefaults.standard.array(forKey: masteredPointIDsKey) as? [String] ?? []
        return Set(raw.map(normalize).filter { !$0.isEmpty })
    }

    static func clearAll() {
        UserDefaults.standard.removeObject(forKey: masteredPointIDsKey)
    }

    private static func normalize(_ value: String) -> String {
        value.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
    }
}
