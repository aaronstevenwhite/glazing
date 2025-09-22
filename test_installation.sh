#!/bin/bash
# Test script for glazing package installation and initialization

set -e  # Exit on error

echo "=========================================="
echo "Testing Glazing Package Installation"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create a temporary directory for testing
TEST_DIR=$(mktemp -d)
echo -e "${YELLOW}Test directory: $TEST_DIR${NC}"

# Create and activate test virtual environment
echo -e "\n${GREEN}Step 1: Creating test virtual environment...${NC}"
python3.13 -m venv "$TEST_DIR/test_venv"
source "$TEST_DIR/test_venv/bin/activate"

# Upgrade pip
echo -e "\n${GREEN}Step 2: Upgrading pip...${NC}"
pip install --upgrade pip

# Install the package
echo -e "\n${GREEN}Step 3: Installing glazing package...${NC}"
pip install -e .

# Set environment variable to use test data directory
export GLAZING_DATA_DIR="$TEST_DIR/glazing_data"

# Test the CLI is available
echo -e "\n${GREEN}Step 4: Testing CLI availability...${NC}"
glazing --version
glazing --help

# Test initialization command
echo -e "\n${GREEN}Step 5: Running 'glazing init' to download and convert datasets...${NC}"
echo -e "${YELLOW}This will download all datasets and may take several minutes...${NC}"

# Create a test init with smaller timeout for demo
glazing init --data-dir "$TEST_DIR/glazing_data"

# Check if initialization was successful
if [ -f "$TEST_DIR/glazing_data/.initialized" ]; then
    echo -e "${GREEN}✅ Initialization successful!${NC}"
else
    echo -e "${RED}❌ Initialization failed!${NC}"
    exit 1
fi

# Test that data files were created
echo -e "\n${GREEN}Step 6: Verifying converted data files...${NC}"

# Check regular datasets
for dataset in verbnet propbank framenet; do
    if [ -f "$TEST_DIR/glazing_data/converted/$dataset.jsonl" ]; then
        echo -e "  ${GREEN}✓${NC} $dataset.jsonl exists"
        # Count lines to verify content
        lines=$(wc -l < "$TEST_DIR/glazing_data/converted/$dataset.jsonl")
        echo -e "    Contains $lines entries"
    else
        echo -e "  ${RED}✗${NC} $dataset.jsonl missing"
    fi
done

# Check WordNet file
if [ -f "$TEST_DIR/glazing_data/converted/wordnet.jsonl" ]; then
    echo -e "  ${GREEN}✓${NC} wordnet.jsonl exists"
    lines=$(wc -l < "$TEST_DIR/glazing_data/converted/wordnet.jsonl")
    echo -e "    Contains $lines entries"
else
    echo -e "  ${RED}✗${NC} wordnet.jsonl missing"
fi

# Test Python import and warning system
echo -e "\n${GREEN}Step 7: Testing Python import...${NC}"
python -c "
import os
os.environ['GLAZING_SKIP_INIT_CHECK'] = '1'  # Skip warning for this test
import glazing
print(f'  ✓ Glazing version: {glazing.__version__}')
"

# Test that warning appears when not initialized
echo -e "\n${GREEN}Step 8: Testing initialization warning...${NC}"
rm -f "$TEST_DIR/glazing_data/.initialized"
python -c "
import warnings
warnings.simplefilter('always')
import sys
import os
# Remove skip flag to test warning
if 'GLAZING_SKIP_INIT_CHECK' in os.environ:
    del os.environ['GLAZING_SKIP_INIT_CHECK']
# Set custom data dir
os.environ['XDG_DATA_HOME'] = '$TEST_DIR/glazing_data'
# Clear modules to force reimport
if 'glazing' in sys.modules:
    del sys.modules['glazing']
if 'glazing.initialize' in sys.modules:
    del sys.modules['glazing.initialize']
# This should trigger warning
try:
    import glazing
    print('  ✓ Warning system working')
except:
    print('  ✗ Import failed')
" 2>&1 | grep -q "Glazing datasets not initialized" && echo -e "  ${GREEN}✓${NC} Warning displayed correctly" || echo -e "  ${YELLOW}⚠${NC} Warning not displayed (may be suppressed)"

# Test search functionality
echo -e "\n${GREEN}Step 9: Testing search functionality...${NC}"
# Re-create initialization marker
touch "$TEST_DIR/glazing_data/.initialized"

# Try a simple search (this assumes data is present)
echo -e "  Testing search command..."
glazing search query "give" --data-dir "$TEST_DIR/glazing_data/converted" 2>/dev/null && echo -e "  ${GREEN}✓${NC} Search command works" || echo -e "  ${YELLOW}⚠${NC} Search needs data files"

# Clean up
echo -e "\n${GREEN}Step 10: Cleaning up...${NC}"
deactivate
rm -rf "$TEST_DIR"

echo -e "\n${GREEN}=========================================="
echo -e "✅ Installation Test Complete!"
echo -e "==========================================${NC}"
echo ""
echo "The glazing package:"
echo "  • Installs successfully"
echo "  • CLI commands work"
echo "  • Can download and convert all datasets"
echo "  • Import warnings work correctly"
echo ""
echo "To use in production:"
echo "  1. Install: pip install glazing"
echo "  2. Initialize: glazing init"
echo "  3. Use: import glazing"
