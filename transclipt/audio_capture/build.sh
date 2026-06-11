#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT="${SCRIPT_DIR}/audio_capture"

if [ -f "$OUTPUT" ]; then
    echo "audio_capture binary already exists at $OUTPUT"
    exit 0
fi

echo "Compiling audio_capture helper..."
swiftc \
    -O \
    -parse-as-library \
    -o "$OUTPUT" \
    "$SCRIPT_DIR/main.swift" \
    -framework ScreenCaptureKit \
    -framework AVFoundation \
    -framework CoreMedia

echo "Built: $OUTPUT"
