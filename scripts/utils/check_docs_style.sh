#!/usr/bin/env bash
#
# Documentation Style Compliance Checker
# Verifies that all documentation follows the style guide standards
#
# Enhanced Features:
#   - Comprehensive error and warning tracking
#   - Detailed logging to .logs/docs_style_check.log
#   - Color-coded terminal output
#   - Exit codes for CI/CD integration
#
# Usage: ./scripts/utils/check_docs_style.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get repository root
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo ".")
LOG_DIR="$REPO_ROOT/.logs"
LOG_FILE="$LOG_DIR/docs_style_check.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Logging function
log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

log_message "INFO" "Documentation style check started"

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
        log_message "ERROR" "Missing header in $file - Expected: **${expected_prefix}...**"
        ((ERRORS++))
    else
        echo -e "${GREEN}✓ PASS${NC}: $file"
        log_message "INFO" "Header check passed: $file"
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
                    log_message "WARNING" "Technical jargon found in $(basename $file)"
                    FOUND=1
                fi
                echo -e "  ${YELLOW}• Found: \"$term\"${NC}"
                log_message "WARNING" "  Term: \"$term\" in $(basename $file)"
                ((WARNINGS++))
            fi
        done
    fi
done

if [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ No technical jargon found in user guide${NC}"
    log_message "INFO" "No technical jargon found in user guide"
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
        log_message "ERROR" "Build issues: $WARN_COUNT warnings, $ERROR_COUNT errors"
        ((ERRORS++))
    else
        echo -e "${GREEN}✓ Build successful (0 warnings, 0 errors)${NC}"
        log_message "INFO" "Sphinx build successful with no issues"
    fi
else
    echo -e "${RED}✗ BUILD FAILED${NC}"
    log_message "ERROR" "Sphinx build failed with status $BUILD_STATUS"
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

log_message "INFO" "Check completed - Errors: $ERRORS, Warnings: $WARNINGS"

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}✗ COMPLIANCE CHECK FAILED${NC}"
    echo ""
    echo "Please fix the errors above and review:"
    echo "  docs/sphinx/developer_guide/documentation_style_guide.rst"
    log_message "ERROR" "Compliance check FAILED"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠ COMPLIANCE CHECK PASSED WITH WARNINGS${NC}"
    echo ""
    echo "Consider reviewing warnings to improve documentation quality."
    echo "  docs/sphinx/developer_guide/documentation_style_guide.rst"
    log_message "WARNING" "Compliance check passed with warnings"
    exit 0
else
    echo -e "${GREEN}✓ ALL COMPLIANCE CHECKS PASSED${NC}"
    echo ""
    echo "Documentation meets style guide standards!"
    log_message "SUCCESS" "All compliance checks PASSED"
    exit 0
fi
