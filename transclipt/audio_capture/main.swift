import AVFoundation
import Foundation
import ScreenCaptureKit

@available(macOS 13.0, *)
final class AudioCapturer: NSObject, SCStreamDelegate, SCStreamOutput {
    private var stream: SCStream?
    private var audioFile: AVAudioFile?
    private let outputURL: URL
    private let duration: TimeInterval
    private let targetPID: pid_t?
    private let sampleRate: Double = 16000
    private let startTime = Date()
    private var capturedSamples = 0

    init(outputPath: String, duration: TimeInterval, targetPID: pid_t?) {
        self.outputURL = URL(fileURLWithPath: outputPath)
        self.duration = duration
        self.targetPID = targetPID
        super.init()
    }

    func start() async throws {
        let content = try await SCShareableContent.excludingDesktopWindows(
            false, onScreenWindowsOnly: true
        )

        let filter: SCContentFilter
        if let pid = targetPID,
           let app = content.applications.first(where: { $0.processID == pid }) {
            filter = SCContentFilter(display: content.displays[0], including: [app], exceptingWindows: [])
        } else {
            filter = SCContentFilter(display: content.displays[0], excludingApplications: [], exceptingWindows: [])
        }

        let config = SCStreamConfiguration()
        config.capturesAudio = true
        config.sampleRate = Int(sampleRate)
        config.channelCount = 1
        config.excludesCurrentProcessAudio = true
        config.width = 2
        config.height = 2

        let format = AVAudioFormat(
            commonFormat: .pcmFormatFloat32,
            sampleRate: sampleRate,
            channels: 1,
            interleaved: false
        )!
        audioFile = try AVAudioFile(
            forWriting: outputURL,
            settings: format.settings,
            commonFormat: .pcmFormatFloat32,
            interleaved: false
        )

        stream = SCStream(filter: filter, configuration: config, delegate: self)
        try stream!.addStreamOutput(self, type: .audio, sampleHandlerQueue: .global(qos: .userInteractive))
        try await stream!.startCapture()

        fputs("Recording audio for \(duration) seconds...\n", stderr)

        try await Task.sleep(nanoseconds: UInt64(duration * 1_000_000_000))

        try await stream!.stopCapture()
        audioFile = nil

        fputs("Captured \(capturedSamples) audio samples to \(outputURL.path)\n", stderr)
    }

    func stream(_ stream: SCStream, didOutputSampleBuffer sampleBuffer: CMSampleBuffer, of type: SCStreamOutputType) {
        guard type == .audio else { return }
        guard let audioFile = audioFile else { return }

        guard let blockBuffer = CMSampleBufferGetDataBuffer(sampleBuffer) else { return }
        let length = CMBlockBufferGetDataLength(blockBuffer)
        guard length > 0 else { return }

        let formatDesc = CMSampleBufferGetFormatDescription(sampleBuffer)
        guard let asbd = CMAudioFormatDescriptionGetStreamBasicDescription(formatDesc!)?.pointee else { return }

        let frameCount = AVAudioFrameCount(CMSampleBufferGetNumSamples(sampleBuffer))
        guard let pcmBuffer = AVAudioPCMBuffer(
            pcmFormat: audioFile.processingFormat,
            frameCapacity: frameCount
        ) else { return }

        pcmBuffer.frameLength = frameCount

        var dataPointer: UnsafeMutablePointer<Int8>?
        CMBlockBufferGetDataPointer(blockBuffer, atOffset: 0, lengthAtOffsetOut: nil, totalLengthOut: nil, dataPointerOut: &dataPointer)

        guard let srcData = dataPointer else { return }
        guard let dstData = pcmBuffer.floatChannelData?[0] else { return }

        if asbd.mFormatFlags & kAudioFormatFlagIsFloat != 0 {
            memcpy(dstData, srcData, length)
        }

        do {
            try audioFile.write(from: pcmBuffer)
            capturedSamples += Int(frameCount)
        } catch {
            fputs("Error writing audio: \(error)\n", stderr)
        }
    }

    func stream(_ stream: SCStream, didStopWithError error: Error) {
        fputs("Stream stopped with error: \(error)\n", stderr)
    }
}

@main
struct AudioCaptureCLI {
    static func main() async {
        guard #available(macOS 13.0, *) else {
            fputs("Error: macOS 13.0 or later required for audio capture.\n", stderr)
            exit(1)
        }

        let args = CommandLine.arguments
        guard args.count >= 3 else {
            fputs("Usage: audio_capture <output.wav> <duration_seconds> [pid]\n", stderr)
            exit(1)
        }

        let outputPath = args[1]
        guard let duration = Double(args[2]), duration > 0 else {
            fputs("Error: Invalid duration.\n", stderr)
            exit(1)
        }

        let pid: pid_t? = args.count >= 4 ? pid_t(args[3]) : nil

        let capturer = AudioCapturer(outputPath: outputPath, duration: duration, targetPID: pid)
        do {
            try await capturer.start()
        } catch {
            fputs("Error: \(error)\n", stderr)
            exit(1)
        }
    }
}
