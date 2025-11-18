#!/bin/bash

# Universal installer for Latent Knowledge Explorer
# Works on Ubuntu 24, macOS, and other Linux distributions

set -e

echo "======================================"
echo "Latent Knowledge Explorer Installer"
echo "======================================"
echo ""

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
fi

echo "Detected OS: $OS"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install based on OS and available tools
install_lke() {
    # Check for UV first (fastest, works everywhere)
    if command_exists uv; then
        echo "✓ Found UV - using for installation (recommended)"
        uv pip install --system git+https://github.com/johnjanik/LatentKnowledgeExplorer.git
        return 0
    fi

    # OS-specific installation
    case $OS in
        ubuntu|debian)
            echo "Ubuntu/Debian detected - checking for pipx..."

            if ! command_exists pipx; then
                echo "Installing pipx first..."
                sudo apt update
                sudo apt install -y pipx python3-full
                pipx ensurepath
                echo "✓ pipx installed"
                echo ""
                echo "⚠️  You may need to restart your shell or run:"
                echo "    source ~/.bashrc"
                echo ""
            fi

            echo "Installing LKE with pipx..."
            pipx install git+https://github.com/johnjanik/LatentKnowledgeExplorer.git
            ;;

        macos)
            echo "macOS detected - checking for Homebrew..."

            if ! command_exists brew; then
                echo "❌ Homebrew not found. Install from https://brew.sh"
                echo "Or install UV:"
                echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
                exit 1
            fi

            echo "Installing with Homebrew..."
            brew tap johnjanik/tap 2>/dev/null || true
            brew install --HEAD johnjanik/tap/lke
            ;;

        fedora|centos|rhel)
            echo "Fedora/RHEL detected - using pip with --user..."
            python3 -m pip install --user git+https://github.com/johnjanik/LatentKnowledgeExplorer.git
            echo ""
            echo "⚠️  Make sure ~/.local/bin is in your PATH"
            ;;

        *)
            echo "Using standard pip installation..."
            if python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
                # Python 3.11+ with PEP 668
                echo "Detected Python 3.11+ with PEP 668 restrictions"
                echo "Using --user installation..."
                python3 -m pip install --user git+https://github.com/johnjanik/LatentKnowledgeExplorer.git
                echo ""
                echo "⚠️  Make sure ~/.local/bin is in your PATH"
            else
                # Older Python, try direct pip
                pip3 install git+https://github.com/johnjanik/LatentKnowledgeExplorer.git
            fi
            ;;
    esac
}

# Install UV if user wants (recommended)
install_uv() {
    echo ""
    echo "UV is the recommended installer (fast and reliable)."
    read -p "Install UV now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
        echo "✓ UV installed. Please restart your shell and run this script again."
        exit 0
    fi
}

# Main installation flow
main() {
    # Check if already installed
    if command_exists lke; then
        echo "✓ LKE is already installed!"
        lke --version
        exit 0
    fi

    # Offer UV installation if not present
    if ! command_exists uv; then
        install_uv
    fi

    # Proceed with installation
    echo "Installing Latent Knowledge Explorer..."
    install_lke

    echo ""
    echo "======================================"

    # Verify installation
    if command_exists lke; then
        echo "✅ Installation successful!"
        echo ""
        echo "Next steps:"
        echo "1. Configure LKE: lke configure"
        echo "2. Check Ollama: lke check-ollama"
        echo "3. Start exploring: lke --help"
    else
        echo "⚠️  Installation completed but 'lke' command not found."
        echo ""
        echo "You may need to:"
        echo "1. Restart your shell"
        echo "2. Add ~/.local/bin to your PATH"
        echo "3. Run: source ~/.bashrc"
    fi
}

main "$@"