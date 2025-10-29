#!/bin/bash
#
# Smart Commit - Git Commit with Automatic Version Bumping
# =========================================================
#
# This script automates version bumping based on conventional commits:
#   - "feat:" or "feat(scope):"     → Minor bump (0.3.0 → 0.4.0)
#   - "fix:" or "fix(scope):"       → Patch bump (0.3.0 → 0.3.1)
#   - "BREAKING CHANGE:" or "!:"    → Major bump (0.3.0 → 1.0.0)
#
# Usage:
#   ./scripts/utils/smart-commit "feat: add new feature"
#   ./scripts/utils/smart-commit "fix: bug fix"  
#   ./scripts/utils/smart-commit "feat!: breaking change"
#
# Or create a git alias:
#   git config alias.sc '!bash scripts/utils/smart-commit'
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

# Get commit message
COMMIT_MSG="$1"

if [ -z "$COMMIT_MSG" ]; then
    echo -e "${RED}✗ Error: Commit message required${NC}" >&2
    echo -e "${YELLOW}Usage: $0 \"commit message\"${NC}" >&2
    exit 1
fi

# Check for unstaged changes
if ! git diff --quiet ||  ! git diff --cached --quiet; then
    echo -e "${BLUE}→ Analyzing commit message...${NC}"
    
    # Check if version bump is needed
    if [ -x "$BUMP_SCRIPT" ]; then
        # Bump version based on commit message
        "$BUMP_SCRIPT" auto "$COMMIT_MSG"
        
        # Stage the version file
        git add "$VERSION_FILE"
        echo -e "${GREEN}✓ Version bumped and staged${NC}"
    else
        echo -e "${YELLOW}⚠  bump-version script not found${NC}"
    fi
    
    # Perform the commit
    git commit -m "$COMMIT_MSG"
else
    echo -e "${YELLOW}⚠  No changes to commit${NC}"
    exit 1
fi
