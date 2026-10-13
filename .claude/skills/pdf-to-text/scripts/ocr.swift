// OCR a PDF with macOS's built-in Vision framework (for scanned PDFs with no text layer).
// Usage: ocr IN.pdf OUT.txt
// Writes each page's text separated by "\f" and prints "pages<TAB>chars".
import Foundation
import PDFKit
import Vision

let args = CommandLine.arguments
guard args.count == 3, let doc = PDFDocument(url: URL(fileURLWithPath: args[1])) else {
  FileHandle.standardError.write("usage: ocr IN.pdf OUT.txt (or unreadable PDF)\n".data(using: .utf8)!)
  exit(1)
}

var pages: [String] = []
for i in 0..<doc.pageCount {
  guard let page = doc.page(at: i) else { pages.append(""); continue }
  // Render at ~200 dpi: sharp enough for body text, cheap enough to stay fast.
  let box = page.bounds(for: .mediaBox)
  let size = NSSize(width: box.width * 200 / 72, height: box.height * 200 / 72)
  let image = page.thumbnail(of: size, for: .mediaBox)
  guard let cg = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else { pages.append(""); continue }

  let request = VNRecognizeTextRequest()
  request.recognitionLevel = .accurate
  request.usesLanguageCorrection = true
  request.recognitionLanguages = ["en-US", "fr-FR"]
  try? VNImageRequestHandler(cgImage: cg).perform([request])
  let lines = (request.results ?? []).compactMap { $0.topCandidates(1).first?.string }
  pages.append(lines.joined(separator: "\n"))
}

let text = pages.joined(separator: "\u{0C}")
try text.write(toFile: args[2], atomically: true, encoding: .utf8)
print("\(doc.pageCount)\t\(text.filter { !$0.isWhitespace }.count)")
