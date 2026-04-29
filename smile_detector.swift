import Vision
import CoreImage
import Foundation
import CoreGraphics

guard CommandLine.arguments.count > 1 else {
    print("0.3")
    exit(0)
}

let path = CommandLine.arguments[1]
let url = URL(fileURLWithPath: path)

guard var ciImage = CIImage(contentsOf: url) else {
    print("0.3")
    exit(0)
}

// Resize to max 1500px
let maxDim: CGFloat = 1500
let longest = max(ciImage.extent.width, ciImage.extent.height)
if longest > maxDim {
    let scale = maxDim / longest
    ciImage = ciImage.transformed(by: CGAffineTransform(scaleX: scale, y: scale))
}

// Use DetectFaceCaptureQuality request directly
let request = VNDetectFaceCaptureQualityRequest()
request.revision = VNDetectFaceCaptureQualityRequestRevision2

let handler = VNImageRequestHandler(ciImage: ciImage, options: [:])

do {
    try handler.perform([request])
} catch {
    print("0.3")
    exit(0)
}

guard let results = request.results, !results.isEmpty else {
    print("0.3")
    exit(0)
}

let scores = results.compactMap { $0.faceCaptureQuality.map { Double($0) } }

if scores.isEmpty {
    print("0.3")
} else {
    let best = scores.max()!
    print(String(format: "%.3f", best))
}
