#!/usr/bin/env bash
# ============================================================
# Smart Resume Builder — one-command setup + launch (Linux/macOS)
# Installs Python dependencies, installs LaTeX if missing,
# then launches the desktop app.
# ============================================================
set -e

echo "===================================="
echo " Latex Resume Builder — Setup"
echo "===================================="

# --- 1. Check for Python 3 ---
if ! command -v python3 &> /dev/null; then
    echo "Python 3 was not found on this system."
    echo "Install it from https://www.python.org/downloads/ and re-run this script."
    exit 1
fi
echo "[1/5] Python 3 found: $(python3 --version)"

# --- 2. Check Tkinter is available (some Linux distros ship it separately) ---
if ! python3 -c "import tkinter" &> /dev/null; then
    echo "[2/5] Tkinter not found."
    if [[ "$OSTYPE" == "linux-gnu"* ]] && command -v apt &> /dev/null; then
        echo "Installing python3-tk via apt..."
        sudo apt update
        sudo apt install -y python3-tk
    else
        echo "Please install Tkinter for your Python installation, then re-run this script."
        echo "On most systems this comes bundled with Python already."
        exit 1
    fi
else
    echo "[2/5] Tkinter available, skipping."
fi

# --- 3. Create a virtual environment if one doesn't exist yet ---
if [ ! -d "venv" ]; then
    echo "[3/5] Creating virtual environment..."
    python3 -m venv venv
else
    echo "[3/5] Virtual environment already exists, skipping."
fi

# shellcheck disable=SC1091
source venv/bin/activate

echo "Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# --- 4. Check for pdflatex, install if missing ---
if command -v pdflatex &> /dev/null; then
    echo "[4/5] LaTeX already installed, skipping."
else
    echo "[4/5] LaTeX not found — installing (this can take a few minutes)..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt &> /dev/null; then
            sudo apt update
            sudo apt install -y texlive-latex-base texlive-latex-extra texlive-fonts-recommended
        else
            echo "Could not detect 'apt' on this Linux system."
            echo "Please install a LaTeX distribution manually (TeX Live is recommended), then re-run this script."
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install --cask mactex-no-gui
        else
            echo "Homebrew was not found."
            echo "Install it from https://brew.sh, then re-run this script."
            echo "(Or install MacTeX manually from https://tug.org/mactex/)"
            exit 1
        fi
    else
        echo "Automatic LaTeX install isn't supported for this OS ($OSTYPE)."
        echo "Please install TeX Live or MacTeX manually, then re-run this script."
        exit 1
    fi
fi

# --- 5. Launch the desktop app ---
echo "[5/5] Starting Smart Resume Builder..."
python3 gui.py