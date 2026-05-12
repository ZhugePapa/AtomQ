import Foundation
import PDFKit
import Vision
import CoreGraphics

struct Config {
    let pdfPath: String
    let outputPath: String
    let startPage: Int
    let endPage: Int
    let scale: CGFloat
}

struct LineRecord: Encodable {
    let page: Int
    let text: String
    let x: Double
    let y: Double
    let width: Double
    let height: Double
    let redRatio: Double
    let inkPixels: Int
    let redPixels: Int
    let color: String
}

func parseArgs() -> Config? {
    let args = CommandLine.arguments
    guard args.count >= 5 else {
        fputs("Usage: swift ocr_pdf_with_color.swift <input.pdf> <output.json> <startPage> <endPage> [scale]\n", stderr)
        return nil
    }
    let scale = args.count > 5 ? CGFloat(Double(args[5]) ?? 3.0) : 3.0
    return Config(
        pdfPath: args[1],
        outputPath: args[2],
        startPage: Int(args[3]) ?? 1,
        endPage: Int(args[4]) ?? Int(args[3]) ?? 1,
        scale: scale
    )
}

func renderPage(_ page: PDFPage, scale: CGFloat) -> (CGImage, [UInt8], Int, Int)? {
    let bounds = page.bounds(for: .mediaBox)
    let width = Int(bounds.width * scale)
    let height = Int(bounds.height * scale)
    guard width > 0, height > 0 else { return nil }

    var pixels = [UInt8](repeating: 255, count: width * height * 4)
    let colorSpace = CGColorSpaceCreateDeviceRGB()
    guard let context = CGContext(
        data: &pixels,
        width: width,
        height: height,
        bitsPerComponent: 8,
        bytesPerRow: width * 4,
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

    guard let image = context.makeImage() else { return nil }
    return (image, pixels, width, height)
}

func redStats(pixels: [UInt8], imageWidth: Int, imageHeight: Int, rect: CGRect) -> (Double, Int, Int) {
    let minX = max(0, Int(floor(rect.minX)))
    let maxX = min(imageWidth - 1, Int(ceil(rect.maxX)))
    let minY = max(0, Int(floor(rect.minY)))
    let maxY = min(imageHeight - 1, Int(ceil(rect.maxY)))
    if minX >= maxX || minY >= maxY { return (0, 0, 0) }

    var ink = 0
    var red = 0
    let step = max(1, min(maxX - minX, maxY - minY) / 80)
    var y = minY
    while y <= maxY {
        var x = minX
        while x <= maxX {
            let index = (y * imageWidth + x) * 4
            let r = Int(pixels[index])
            let g = Int(pixels[index + 1])
            let b = Int(pixels[index + 2])
            let darkEnough = r < 245 || g < 245 || b < 245
            if darkEnough {
                ink += 1
                if r > 120 && r > g + 35 && r > b + 35 {
                    red += 1
                }
            }
            x += step
        }
        y += step
    }
    return (ink == 0 ? 0 : Double(red) / Double(ink), ink, red)
}

func recognize(image: CGImage, pixels: [UInt8], width: Int, height: Int, pageNumber: Int) throws -> [LineRecord] {
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = true
    request.recognitionLanguages = ["zh-Hans", "en-US"]
    request.minimumTextHeight = 0.004

    let handler = VNImageRequestHandler(cgImage: image, options: [:])
    try handler.perform([request])

    return (request.results ?? []).compactMap { observation in
        guard let candidate = observation.topCandidates(1).first else { return nil }
        let text = candidate.string.trimmingCharacters(in: .whitespacesAndNewlines)
        if text.isEmpty { return nil }

        let box = observation.boundingBox
        let rect = CGRect(
            x: box.minX * CGFloat(width),
            y: (1.0 - box.maxY) * CGFloat(height),
            width: box.width * CGFloat(width),
            height: box.height * CGFloat(height)
        ).insetBy(dx: -2, dy: -2)
        let (ratio, ink, red) = redStats(pixels: pixels, imageWidth: width, imageHeight: height, rect: rect)
        return LineRecord(
            page: pageNumber,
            text: text,
            x: Double(box.minX),
            y: Double(box.minY),
            width: Double(box.width),
            height: Double(box.height),
            redRatio: ratio,
            inkPixels: ink,
            redPixels: red,
            color: ratio >= 0.18 && red >= 5 ? "red" : "black"
        )
    }
}

guard let config = parseArgs() else { exit(2) }
guard let document = PDFDocument(url: URL(fileURLWithPath: config.pdfPath)) else {
    fputs("Cannot open PDF: \(config.pdfPath)\n", stderr)
    exit(1)
}

let pageCount = document.pageCount
let start = max(1, config.startPage)
let end = min(pageCount, max(start, config.endPage))
var records: [LineRecord] = []

for pageNumber in start...end {
    autoreleasepool {
        guard let page = document.page(at: pageNumber - 1),
              let rendered = renderPage(page, scale: config.scale) else {
            return
        }
        do {
            let pageRecords = try recognize(
                image: rendered.0,
                pixels: rendered.1,
                width: rendered.2,
                height: rendered.3,
                pageNumber: pageNumber
            )
            records.append(contentsOf: pageRecords)
            let redCount = pageRecords.filter { $0.color == "red" }.count
            print("OCR page \(pageNumber)/\(pageCount): \(pageRecords.count) lines, red=\(redCount)")
        } catch {
            print("OCR page \(pageNumber)/\(pageCount): failed \(error)")
        }
    }
}

let encoder = JSONEncoder()
encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
let data = try encoder.encode(records)
try data.write(to: URL(fileURLWithPath: config.outputPath), options: .atomic)
print("Saved \(config.outputPath)")
