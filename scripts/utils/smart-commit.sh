#!/bin/bash
#
# Smart Commit - Git Commit with Automatic Version Bumping
# =========================================================
#
# This script automates version bumping based on conventional commits:
#   - "feat:" or "Feat:" or "FEAT:"     → Minor bump (0.3.0 → 0.4.0)
#   - "fix:" or "Fix:" or "FIX:"        → Patch bump (0.3.0 → 0.3.1)
#   - "BREAKING CHANGE:" or "!:"         → Major bump (0.3.0 → 1.0.0)
#
# Enhanced Features:
#   - Case-insensitive commit type detection
#   - Comprehensive error handling and validation
#   - Detailed logging to .logs/smart_commit.log
#   - Version validation before and after bump
#
# Usage:
#   ./scripts/utils/smart-commit.sh "feat: add new feature"
#   ./scripts/utils/smart-commit.sh "fix: bug fix"  
#   ./scripts/utils/smart-commit.sh "feat!: breaking change"
#
# Or create a git alias:
#   git config alias.sc '!bash scripts/utils/smart-commit.sh'
#   git sc "feat: new feature"
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get repository root
REPO_ROOT=$(git rev-parse --show-toplevel)
VERSION_FILE="$REPO_ROOT/__version__.py"
BUMP_SCRIPT="$REPO_ROOT/.git/hooks/bump-version"
LOG_DIR="$REPO_ROOT/.logs"
LOG_FILE="$LOG_DIR/smart_commit.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Logging function
log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# Get commit message
COMMIT_MSG="$1"

if [ -z "$COMMIT_MSG" ]; then
    echo -e "${RED}✗ Error: Commit message required${NC}" >&2
    echo -e "${YELLOW}Usage: $0 \"commit message\"${NC}" >&2
    log_message "ERROR" "No commit message provided"
    exit 1
fi

log_message "INFO" "Smart commit initiated with message: $COMMIT_MSG"

# Check for unstaged changes
if ! git diff --quiet ||  ! git diff --cached --quiet; then
    echo -e "${BLUE}→ Analyzing commit message...${NC}"
    log_message "INFO" "Changes detected, proceeding with version bump"
    
    # Get current version before bump (supports both annotated and plain syntax)
    CURRENT_VERSION=$(grep -E '^__version__\s*(:\s*\w+\s*)?=\s*"' "$VERSION_FILE" | sed 's/.*"\(.*\)".*/\1/')
    log_message "INFO" "Current version: $CURRENT_VERSION"
    
    # Check if version bump script exists
    if [ -x "$BUMP_SCRIPT" ]; then
        echo -e "${BLUE}→ Running version bump script...${NC}"
        
        # Bump version based on commit message
        BUMP_OUTPUT=$("$BUMP_SCRIPT" auto "$COMMIT_MSG" 2>&1)
        BUMP_EXIT_CODE=$?
        
        if [ $BUMP_EXIT_CODE -eq 0 ]; then
            # Get new version after bump (supports both annotated and plain syntax)
            NEW_VERSION=$(grep -E '^__version__\s*(:\s*\w+\s*)?=\s*"' "$VERSION_FILE" | sed 's/.*"\(.*\)".*/\1/')
            
            echo -e "${GREEN}✓ Version bumped successfully${NC}"
            echo -e "${BLUE}  $CURRENT_VERSION → $NEW_VERSION${NC}"
            log_message "SUCCESS" "Version bumped: $CURRENT_VERSION → $NEW_VERSION"
            
            # Stage the version file
            git add "$VERSION_FILE"
            echo -e "${GREEN}✓ Version file staged${NC}"
            log_message "INFO" "Version file staged for commit"
        else
            echo -e "${RED}✗ Error: Version bump failed${NC}" >&2
            echo -e "${YELLOW}Output:${NC}" >&2
            echo "$BUMP_OUTPUT" >&2
            log_message "ERROR" "Version bump failed with exit code $BUMP_EXIT_CODE"
            log_message "ERROR" "Bump output: $BUMP_OUTPUT"
            exit 1
        fi
    else
        echo -e "${YELLOW}⚠  Warning: bump-version script not found or not executable${NC}"
        echo -e "${YELLOW}   Expected location: $BUMP_SCRIPT${NC}"
        log_message "WARNING" "bump-version script not found at $BUMP_SCRIPT"
    fi
    
    # Perform the commit
    echo -e "${BLUE}→ Committing changes...${NC}"
    if git commit -m "$COMMIT_MSG"; then
        echo -e "${GREEN}✓ Commit successful${NC}"
        log_message "SUCCESS" "Commit completed: $COMMIT_MSG"
        
        # Display commit info
        COMMIT_HASH=$(git rev-parse --short HEAD)
        echo -e "${BLUE}  Commit: $COMMIT_HASH${NC}"
        log_message "INFO" "Commit hash: $COMMIT_HASH"
    else
        echo -e "${RED}✗ Error: Commit failed${NC}" >&2
        log_message "ERROR" "Git commit failed"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠  No changes to commit${NC}"
    log_message "WARNING" "No changes detected, nothing to commit"
    exit 1
fi
