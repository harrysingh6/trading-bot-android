#!/bin/bash

# Trading Bot APK Builder
# Quick script to build Android APK

echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║          📱 TRADING BOT - APK BUILDER 🤖                  ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "⚠️  This script must run on Linux (Ubuntu/Debian)"
    echo ""
    echo "Options:"
    echo "1. Use WSL2 (Windows Subsystem for Linux)"
    echo "2. Use a Linux VM"
    echo "3. Use GitHub Actions (see APK_BUILD_GUIDE.md)"
    echo "4. Use Google Colab"
    echo ""
    exit 1
fi

# Check for required commands
echo "🔍 Checking system requirements..."

command -v python3 >/dev/null 2>&1 || {
    echo "❌ Python3 is required but not installed."
    echo "Install: sudo apt-get install python3 python3-pip"
    exit 1
}

command -v java >/dev/null 2>&1 || {
    echo "❌ Java is required but not installed."
    echo "Install: sudo apt-get install openjdk-17-jdk"
    exit 1
}

echo "✅ Python found: $(python3 --version)"
echo "✅ Java found: $(java -version 2>&1 | head -n 1)"

# Check if buildozer is installed
if ! command -v buildozer &> /dev/null; then
    echo ""
    echo "📦 Buildozer not found. Installing..."
    pip3 install buildozer cython
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install buildozer"
        exit 1
    fi
    echo "✅ Buildozer installed"
fi

# Check if icons exist
if [ ! -f "icon.png" ]; then
    echo ""
    echo "🎨 Generating app icons..."
    python3 create_android_icon.py
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "Starting APK Build Process"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "⏰ This will take 30-60 minutes on first build"
echo "⏰ Subsequent builds will be much faster (~5 minutes)"
echo ""

# Ask user for build type
echo "Select build type:"
echo "1) Debug APK (faster, for testing)"
echo "2) Release APK (optimized, for distribution)"
read -p "Choice (1 or 2): " build_type

if [ "$build_type" = "2" ]; then
    echo ""
    echo "🔐 Building release APK..."
    buildozer android release
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Release APK built successfully!"
        echo ""
        echo "⚠️  Note: Release APK needs to be signed before distribution"
        echo "See APK_BUILD_GUIDE.md for signing instructions"
    else
        echo ""
        echo "❌ Build failed. Check errors above."
        exit 1
    fi
else
    echo ""
    echo "🔨 Building debug APK..."
    buildozer android debug
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "════════════════════════════════════════════════════════════"
        echo "✅ APK BUILT SUCCESSFULLY!"
        echo "════════════════════════════════════════════════════════════"
        echo ""
        
        # Find the APK
        APK_FILE=$(ls bin/*.apk 2>/dev/null | head -n 1)
        
        if [ -n "$APK_FILE" ]; then
            APK_SIZE=$(du -h "$APK_FILE" | cut -f1)
            echo "📦 APK Location: $APK_FILE"
            echo "📊 APK Size: $APK_SIZE"
            echo ""
            echo "📲 To install on your phone:"
            echo "   1. Copy APK to your phone"
            echo "   2. Enable 'Install from Unknown Sources'"
            echo "   3. Tap the APK file to install"
            echo ""
            echo "🌐 Or start a local server:"
            echo "   python3 -m http.server 8000"
            echo "   Then visit http://YOUR_IP:8000 from your phone"
            echo ""
        fi
    else
        echo ""
        echo "❌ Build failed. Common solutions:"
        echo ""
        echo "1. Install system dependencies:"
        echo "   sudo apt-get install -y openjdk-17-jdk git zip unzip"
        echo ""
        echo "2. Check Java version (need Java 17):"
        echo "   java -version"
        echo ""
        echo "3. Clean and retry:"
        echo "   buildozer android clean"
        echo "   buildozer android debug"
        echo ""
        echo "See APK_BUILD_GUIDE.md for detailed troubleshooting"
        exit 1
    fi
fi

echo "════════════════════════════════════════════════════════════"
echo ""
