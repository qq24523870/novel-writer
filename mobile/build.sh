#!/bin/bash
# ============================================================
#   AI Novel Writer - Android APK Builder (Linux)
#   Run this on any Linux machine (Ubuntu/Debian recommended)
#   Dev: QingYi  QQ:24523870
# ============================================================
set -e

echo "=============================================="
echo "  AI Novel Writer - APK Builder"
echo "  Dev: QingYi  QQ:24523870"
echo "=============================================="
echo ""

# Install dependencies
echo "[1/4] Installing Python dependencies..."
pip3 install flet openai loguru python-docx markdown lxml httpx tiktoken 2>/dev/null || \
pip install flet openai loguru python-docx markdown lxml httpx tiktoken

# Copy core modules (if not already present)
echo "[2/4] Preparing source..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

mkdir -p "$SCRIPT_DIR/core" "$SCRIPT_DIR/models" "$SCRIPT_DIR/utils" "$SCRIPT_DIR/config" 2>/dev/null

cp -n "$PROJECT_DIR/core/"*.py "$SCRIPT_DIR/core/" 2>/dev/null || true
cp -n "$PROJECT_DIR/models/"*.py "$SCRIPT_DIR/models/" 2>/dev/null || true
cp -n "$PROJECT_DIR/utils/"*.py "$SCRIPT_DIR/utils/" 2>/dev/null || true
cp -n "$PROJECT_DIR/config/default_config.json" "$SCRIPT_DIR/config/" 2>/dev/null || true

echo "[3/4] Building Android APK (5-15 minutes)..."
cd "$SCRIPT_DIR"
flet build apk --name "AI Novel Writer" --org "com.qingyi.novelwriter" 2>&1

# Check output
echo ""
echo "[4/4] Checking output..."
if [ -f "build/apk/app-release.apk" ]; then
    SIZE=$(du -h "build/apk/app-release.apk" | cut -f1)
    cp "build/apk/app-release.apk" "AI_Novel_Writer.apk"
    echo "=============================================="
    echo "  BUILD SUCCESS!"
    echo "  APK file: AI_Novel_Writer.apk ($SIZE)"
    echo "  Install on any Android 8.0+ phone"
    echo "  Works with: HyperOS, HarmonyOS, ColorOS..."
    echo "=============================================="
else
    echo ""
    echo "[ERROR] APK not found. Check the logs above."
    echo "If you see 'command not found', make sure flet is installed:"
    echo "  pip3 install flet"
    exit 1
fi
