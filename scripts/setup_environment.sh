#!/bin/bash

# Video Downloader Environment Setup Script
# Linux/macOS version

set -e  # Exit on any error

echo "========================================"
echo "Video Downloader Environment Setup"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Step 1: Check Python installation
echo -e "${YELLOW}[1/5] Checking Python installation...${NC}"
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ Python is installed: $PYTHON_VERSION${NC}"
    PYTHON_CMD="python3"
elif command_exists python; then
    PYTHON_VERSION=$(python --version)
    echo -e "${GREEN}✓ Python is installed: $PYTHON_VERSION${NC}"
    PYTHON_CMD="python"
else
    echo -e "${RED}ERROR: Python is not installed or not in PATH${NC}"
    echo -e "${RED}Please install Python 3.8+ from https://python.org${NC}"
    exit 1
fi

# Step 2: Check pip installation
echo ""
echo -e "${YELLOW}[2/5] Checking pip installation...${NC}"
if command_exists pip3; then
    PIP_VERSION=$(pip3 --version)
    echo -e "${GREEN}✓ pip is available: $PIP_VERSION${NC}"
    PIP_CMD="pip3"
elif command_exists pip; then
    PIP_VERSION=$(pip --version)
    echo -e "${GREEN}✓ pip is available: $PIP_VERSION${NC}"
    PIP_CMD="pip"
else
    echo -e "${RED}ERROR: pip is not available${NC}"
    echo -e "${RED}Please ensure pip is installed with Python${NC}"
    exit 1
fi

# Step 3: Upgrade pip
echo ""
echo -e "${YELLOW}[3/5] Upgrading pip to latest version...${NC}"
if $PYTHON_CMD -m pip install --upgrade pip; then
    echo -e "${GREEN}✓ pip upgraded successfully${NC}"
else
    echo -e "${YELLOW}WARNING: Failed to upgrade pip, continuing...${NC}"
fi

# Step 4: Install dependencies
echo ""
echo -e "${YELLOW}[4/5] Installing project dependencies...${NC}"
if $PIP_CMD install -r requirements.txt; then
    echo -e "${GREEN}✓ Dependencies installed successfully${NC}"
else
    echo -e "${RED}ERROR: Failed to install dependencies${NC}"
    echo -e "${RED}Please check your internet connection and try again${NC}"
    exit 1
fi

# Step 5: Create downloads directory
echo ""
echo -e "${YELLOW}[5/5] Creating downloads directory...${NC}"
if [ ! -d "downloads" ]; then
    mkdir -p downloads
fi
echo -e "${GREEN}✓ Downloads directory created${NC}"

# Success message
echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}Setup completed successfully!${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo "You can now run the video downloader:"
echo -e "${CYAN}  • GUI mode: $PYTHON_CMD src/main_downloader.py --gui${NC}"
echo -e "${CYAN}  • CLI mode: $PYTHON_CMD src/main_downloader.py${NC}"
echo ""
echo "For more information, see README.md"
echo ""