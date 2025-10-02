# RePORTaLiN Documentation

This directory contains the Sphinx documentation for RePORTaLiN.

## Building the Documentation

### Prerequisites

Install documentation dependencies:

```bash
pip install -r requirements.txt
```

### Build Options

#### 🎯 User Mode (Default for End Users)
Build documentation **without** developer guides and API reference:

```bash
cd docs/sphinx
make user-mode
```

**Includes:**
- ✅ User Guide (installation, quickstart, usage, troubleshooting)
- ✅ Configuration guide
- ✅ Changelog and license

**Excludes:**
- ❌ Developer Guide
- ❌ API Reference
- ❌ Technical architecture details

---

#### 🔧 Developer Mode (Full Documentation)
Build **complete** documentation including developer and API docs:

```bash
cd docs/sphinx
make dev-mode
```

**Includes:**
- ✅ Everything from User Mode
- ✅ Developer Guide (architecture, contributing, testing)
- ✅ API Reference (all modules documented)
- ✅ Technical implementation details

---

#### 🏗️ Standard HTML Build (Default: Developer Mode)
```bash
cd docs/sphinx
make html
```

This builds with `developer_mode = True` (full documentation).

### View Documentation

```bash
open _build/html/index.html
```

### Clean Build

```bash
cd docs/sphinx
make clean
```

---

## Documentation Structure

```
docs/sphinx/
├── index.rst              # Main documentation page
├── conf.py                # Sphinx configuration (developer_mode toggle)
├── Makefile               # Build commands (user-mode, dev-mode)
│
├── user_guide/            # 👥 For end users
│   ├── introduction.rst
│   ├── installation.rst
│   ├── quickstart.rst
│   ├── configuration.rst
│   ├── usage.rst
│   └── troubleshooting.rst
│
├── developer_guide/       # 🔧 For developers (excluded in user-mode)
│   ├── architecture.rst
│   ├── contributing.rst
│   ├── extending.rst
│   └── testing.rst
│
├── api/                   # 📚 API Reference (excluded in user-mode)
│   ├── modules.rst
│   ├── config.rst
│   ├── main.rst
│   └── ...
│
├── changelog.rst          # Version history
├── license.rst            # License information
│
└── _build/                # Generated HTML
    └── html/              # Open index.html to view
```

---

## Switching Modes

### Option 1: Use Make Targets (Recommended)
```bash
make user-mode    # User documentation only
make dev-mode     # Full documentation
```

### Option 2: Edit conf.py Manually
Open `conf.py` and change:
```python
# Set to False for user-only documentation
# Set to True for full documentation
developer_mode = True  # Change to False for user mode
```

Then build:
```bash
make html
```

---

## Quick Commands

```bash
# Build user documentation
make user-mode

# Build developer documentation  
make dev-mode

# Clean build files
make clean

# View documentation
open _build/html/index.html

# Rebuild from scratch (user mode)
make clean && make user-mode

# Rebuild from scratch (dev mode)
make clean && make dev-mode
```

---

## What Users See vs What Developers See

### 👥 User Mode Documentation
- Installation guide
- Quick start tutorial
- Configuration options
- Usage examples
- Troubleshooting
- **~10 pages**

### 🔧 Developer Mode Documentation
- Everything from User Mode
- Architecture and design
- Contributing guidelines
- Testing procedures
- API reference for all modules
- **~27 pages**

---

## Tips

1. **For Public Release**: Build with `make user-mode` to keep documentation simple
2. **For Development**: Build with `make dev-mode` to see all details
3. **Default**: `make html` uses developer mode (full documentation)
4. **Clean Builds**: Run `make clean` before switching modes for best results
│   │   ├── configuration.rst
│   │   ├── usage.rst
│   │   └── troubleshooting.rst
│   ├── developer_guide/       # Developer documentation
│   │   ├── architecture.rst
│   │   ├── contributing.rst
│   │   ├── testing.rst
│   │   └── extending.rst
│   ├── api/                   # API reference
│   │   ├── modules.rst
│   │   ├── main.rst
│   │   ├── config.rst
│   │   └── scripts.rst
│   ├── changelog.rst          # Version history
│   └── license.rst            # License information
└── build/                     # Generated documentation (ignored by git)
```

## Viewing the Documentation

After building:

```bash
# macOS
open build/html/index.html

# Linux
xdg-open build/html/index.html

# Windows
start build/html/index.html
```

## Updating Documentation

1. Edit .rst files in `source/` directory
2. Add docstrings to Python code
3. Rebuild documentation: `make html`
4. Check for errors and warnings
5. Review changes in browser

## Documentation Style

- Use reStructuredText (.rst) format
- Include code examples
- Add cross-references to related functions
- Keep explanations clear and concise
- Follow Google-style docstrings in code
