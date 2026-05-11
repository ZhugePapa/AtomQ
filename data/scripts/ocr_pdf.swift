import Foundation
import PDFKit
import Vision
import CoreGraphics

struct OCRConfig {
    let pdfPath: String
    let outputPath: String
    let startPage: Int
    let endPage: Int
    let scale: CGFloat
}

func parseArgs() -> OCRConfig? {
    let args = CommandLine.arguments
    guard args.count >= 3 else {
        fputs("Usage: swift ocr_pdf.swift <input.pdf> <output.txt> [startPage] [endPage] [scale]\n", stderr)
        return nil
    }
    let startPage = args.count > 3 ? Int(args[3]) ?? 1 : 1
    let endPage = args.count > 4 ? Int(args[4]) ?? startPage : startPage
    let scale = args.count > 5 ? CGFloat(Double(args[5]) ?? 2.0) : 2.0
    return OCRConfig(pdfPath: args[1], outputPath: args[2], startPage: startPage, endPage: endPage, scale: scale)
}

func renderPage(_ page: PDFPage, scale: CGFloat) -> CGImage? {
    let bounds = page.bounds(for: .mediaBox)
    let width = Int(bounds.width * scale)
    let height = Int(bounds.height * scale)
    guard width > 0, height > 0 else { return nil }

    let colorSpace = CGColorSpaceCreateDeviceRGB()
    guard let context = CGContext(
        data: nil,
        width: width,
        height: height,
        bitsPerComponent: 8,
        bytesPerRow: 0,
        space: colorSpace,
        bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
    ) else {
        return nil
    }

    context.setFillColor(CGColor.white)
    context.fill(CGRect(x: 0, y: 0, width: CGFloat(width), height: CGFloat(height)))
    context.saveGState()
    context.scaleBy(x: scale, y: scale)
    page.draw(with: .mediaBox, to: context)
    context.restoreGState()
    return context.makeImage()
}

func recognizeText(in image: CGImage) throws -> String {
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = true
    request.recognitionLanguages = ["zh-Hans", "en-US"]
    request.minimumTextHeight = 0.006

    let handler = VNImageRequestHandler(cgImage: image, options: [:])
    try handler.perform([request])

    let observations = request.results ?? []
    return observations
        .compactMap { $0.topCandidates(1).first?.string }
        .joined(separator: "\n")
}

guard let config = parseArgs() else {
    exit(2)
}

let pdfURL = URL(fileURLWithPath: config.pdfPath)
guard let document = PDFDocument(url: pdfURL) else {
    fputs("Cannot open PDF: \(config.pdfPath)\n", stderr)
    exit(1)
}

let pageCount = document.pageCount
let start = max(1, config.startPage)
let end = min(pageCount, max(start, config.endPage))
var chunks: [String] = []

for pageNumber in start...end {
    autoreleasepool {
        guard let page = document.page(at: pageNumber - 1), let image = renderPage(page, scale: config.scale) else {
            chunks.append("\n=== Page \(pageNumber) ===\n[render failed]\n")
            return
        }
        do {
            let text = try recognizeText(in: image)
            chunks.append("\n=== Page \(pageNumber) ===\n\(text)\n")
            print("OCR page \(pageNumber)/\(pageCount): \(text.count) chars")
        } catch {
            chunks.append("\n=== Page \(pageNumber) ===\n[ocr failed: \(error)]\n")
            print("OCR page \(pageNumber)/\(pageCount): failed \(error)")
        }
    }
}

let output = chunks.joined(separator: "\n")
try output.write(to: URL(fileURLWithPath: config.outputPath), atomically: true, encoding: .utf8)
print("Saved \(config.outputPath)")
