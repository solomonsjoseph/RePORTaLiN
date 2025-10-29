#!/bin/bash
#
# Quick Reference: Documentation Maintenance Commands
# =====================================================
#
# This file contains commonly used commands for documentation maintenance.
# You can source this file or copy individual commands as needed.

# Repository root (adjust if needed)
REPO_ROOT="/Users/sj1136/Documents/VSCode_files/gitRepo/Work/RePORTaLiN"

# Function: Run documentation quality check
doc_quality_check() {
    echo "🔍 Running Documentation Quality Check..."
    cd "$REPO_ROOT" || return 1
    python3 scripts/utils/check_documentation_quality.py
}

# Function: Run style checker
doc_style_check() {
    echo "✨ Running Documentation Style Check..."
    cd "$REPO_ROOT/scripts/utils" || return 1
    ./check_docs_style.sh
}

# Function: Build documentation
doc_build() {
    echo "📚 Building Documentation..."
    cd "$REPO_ROOT/docs/sphinx" || return 1
    make clean
    make html
    echo ""
    echo "✅ Documentation built successfully!"
    echo "📂 Output: $REPO_ROOT/docs/sphinx/_build/html/index.html"
}

# Function: Build and open documentation
doc_build_open() {
    doc_build
    echo "🌐 Opening documentation in browser..."
    open "$REPO_ROOT/docs/sphinx/_build/html/index.html"
}

# Function: Check current version
check_version() {
    echo "📌 Current Version:"
    cd "$REPO_ROOT" || return 1
    cat __version__.py
}

# Function: Quick commit with version bump
# Usage: quick_commit "feat: add new feature"
#        quick_commit "fix: resolve bug"
#        quick_commit "feat!: breaking change" "BREAKING CHANGE: details"
quick_commit() {
    local msg="$1"
    local breaking="$2"
    
    cd "$REPO_ROOT" || return 1
    
    echo "📝 Current version:"
    cat __version__.py
    
    git add .
    
    if [ -n "$breaking" ]; then
        git commit -m "$msg" -m "$breaking"
    else
        git commit -m "$msg"
    fi
    
    echo ""
    echo "📌 New version:"
    cat __version__.py
}

# Function: Full documentation maintenance check
full_maintenance() {
    echo "🚀 Running Full Documentation Maintenance Check..."
    echo ""
    
    echo "1️⃣ Checking version..."
    check_version
    echo ""
    
    echo "2️⃣ Running quality check..."
    doc_quality_check
    echo ""
    
    echo "3️⃣ Running style check..."
    doc_style_check
    echo ""
    
    echo "4️⃣ Building documentation..."
    doc_build
    echo ""
    
    echo "✅ Full maintenance check complete!"
}

# Print usage if script is run directly
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    echo "Documentation Maintenance Quick Reference"
    echo "========================================="
    echo ""
    echo "Available commands:"
    echo ""
    echo "  doc_quality_check   - Run comprehensive quality check"
    echo "  doc_style_check     - Run style compliance check"
    echo "  doc_build           - Build HTML documentation"
    echo "  doc_build_open      - Build and open in browser"
    echo "  check_version       - Show current version"
    echo "  quick_commit <msg>  - Commit with automatic version bump"
    echo "  full_maintenance    - Run all maintenance checks"
    echo ""
    echo "Usage:"
    echo "  source $0"
    echo "  doc_quality_check"
    echo ""
    echo "Or copy commands directly from this file."
fi

# Export functions if sourced
if [ "${BASH_SOURCE[0]}" != "${0}" ]; then
    export -f doc_quality_check
    export -f doc_style_check
    export -f doc_build
    export -f doc_build_open
    export -f check_version
    export -f quick_commit
    export -f full_maintenance
    echo "✅ Documentation maintenance functions loaded!"
    echo "💡 Type 'full_maintenance' to run all checks"
fi
