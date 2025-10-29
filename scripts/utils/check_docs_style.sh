#!/usr/bin/env bash
#
# Documentation Style Compliance Checker
# Verifies that all documentation follows the style guide standards
#
# Usage: ./scripts/utils/check_docs_style.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        Documentation Style Compliance Checker                ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

ERRORS=0
WARNINGS=0

# Function to check for required header
check_header() {
    local file=$1
    local expected_prefix=$2
    local friendly_name=$3
    
    if ! grep -q "^\*\*${expected_prefix}" "$file"; then
        echo -e "${RED}✗ MISSING${NC}: $file"
        echo -e "  ${YELLOW}Expected: **${expected_prefix}...**${NC}"
        ((ERRORS++))
    else
        echo -e "${GREEN}✓ PASS${NC}: $file"
    fi
}

echo -e "${BLUE}Checking User Guide Files...${NC}"
echo "────────────────────────────────────────────────────────────────"

for file in docs/sphinx/user_guide/*.rst; do
    if [ -f "$file" ]; then
        check_header "$file" "For Users:" "$(basename $file)"
    fi
done

echo ""
echo -e "${BLUE}Checking Developer Guide Files...${NC}"
echo "────────────────────────────────────────────────────────────────"

for file in docs/sphinx/developer_guide/*.rst; do
    if [ -f "$file" ]; then
        check_header "$file" "For Developers:" "$(basename $file)"
    fi
done

echo ""
echo -e "${BLUE}Checking for Technical Jargon in User Guide...${NC}"
echo "────────────────────────────────────────────────────────────────"

# Technical terms that shouldn't appear in user guide prose (code blocks are OK)
# We'll use a simple heuristic: check for terms outside of code blocks
TECH_TERMS=(
    "module reference"
    "function call"
    "class method"
    " API documentation"
    "parameter list"
    "decorator pattern"
    "singleton instance"
    "algorithm implementation"
    "dataclass definition"
    "instantiate object"
    "thread-safe implementation"
    "REPL environment"
    "__init__ method"
)

for file in docs/sphinx/user_guide/*.rst; do
    if [ -f "$file" ]; then
        FOUND=0
        for term in "${TECH_TERMS[@]}"; do
            # Search for term but exclude code blocks (lines with '.. code-block::' nearby)
            if grep -v "code-block::" "$file" | grep -q "$term"; then
                if [ $FOUND -eq 0 ]; then
                    echo -e "${YELLOW}⚠ WARNING${NC}: $(basename $file) contains technical terms:"
                    FOUND=1
                fi
                echo -e "  ${YELLOW}• Found: \"$term\"${NC}"
                ((WARNINGS++))
            fi
        done
    fi
done

if [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ No technical jargon found in user guide${NC}"
fi

echo ""
echo -e "${BLUE}Checking Sphinx Build...${NC}"
echo "────────────────────────────────────────────────────────────────"

cd docs/sphinx
BUILD_OUTPUT=$(make html 2>&1)
BUILD_STATUS=$?

if [ $BUILD_STATUS -eq 0 ]; then
    WARN_COUNT=$(echo "$BUILD_OUTPUT" | grep -c "WARNING" || true)
    ERROR_COUNT=$(echo "$BUILD_OUTPUT" | grep -c "ERROR" || true)
    
    if [ $WARN_COUNT -gt 0 ] || [ $ERROR_COUNT -gt 0 ]; then
        echo -e "${RED}✗ BUILD ISSUES${NC}: $WARN_COUNT warnings, $ERROR_COUNT errors"
        ((ERRORS++))
    else
        echo -e "${GREEN}✓ Build successful (0 warnings, 0 errors)${NC}"
    fi
else
    echo -e "${RED}✗ BUILD FAILED${NC}"
    ((ERRORS++))
fi

cd ../..

echo ""
echo "══════════════════════════════════════════════════════════════"
echo -e "${BLUE}Summary:${NC}"
echo "──────────────────────────────────────────────────────────────"
echo -e "Errors:   ${RED}$ERRORS${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
echo "══════════════════════════════════════════════════════════════"

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}✗ COMPLIANCE CHECK FAILED${NC}"
    echo ""
    echo "Please fix the errors above and review:"
    echo "  docs/sphinx/developer_guide/documentation_style_guide.rst"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠ COMPLIANCE CHECK PASSED WITH WARNINGS${NC}"
    echo ""
    echo "Consider reviewing warnings to improve documentation quality."
    echo "  docs/sphinx/developer_guide/documentation_style_guide.rst"
    exit 0
else
    echo -e "${GREEN}✓ ALL COMPLIANCE CHECKS PASSED${NC}"
    echo ""
    echo "Documentation meets style guide standards!"
    exit 0
fi
