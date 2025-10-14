Colored Output Enhancement
==========================

**Added: October 14, 2025**

Overview
--------

RePORTaLiN now features enhanced colored console output for improved readability and user experience. The color system provides visual distinction between different log levels, status indicators, and progress bars.

Features
--------

### Color-Coded Log Levels

**Console Output:**
- 🟢 **SUCCESS** (Green, Bold) - Successful operations
- 🔴 **ERROR** (Red) - Error messages
- 🔴 **CRITICAL** (Bold Red on Red background) - Critical failures
- 🔵 **INFO** (Cyan) - Informational messages (file only)
- 🟡 **WARNING** (Yellow) - Warning messages (file only)
- ⚫ **DEBUG** (Dim gray) - Debug information (file only)

**Note:** Only SUCCESS, ERROR, and CRITICAL messages appear in the console by default. All levels are logged to the file.

### Visual Indicators

The system uses colored symbols for status indication:

- ✓ (Green) - Success/completion
- ⊙ (Yellow) - Skipped/already exists
- → (Cyan) - Information/direction
- ✗ (Red) - Error/failure
- ⚠ (Yellow) - Warning

### Colored Progress Bars

Progress bars now feature colors based on operation type:
- **Green bars** - Data extraction operations
- **Cyan bars** - Dictionary processing operations

Usage
-----

### Default Behavior

Colors are **enabled by default** when running in a terminal that supports ANSI color codes:

.. code-block:: bash

   python main.py

### Disable Colors

If you prefer plain text output or are redirecting to a file:

.. code-block:: bash

   # Disable color output
   python main.py --no-color
   
   # Redirect to file (automatically disables colors)
   python main.py > output.log

### Test Colored Output

Run the test script to see all color options:

.. code-block:: bash

   python test_colored_logging.py

Platform Support
----------------

### macOS & Linux

✅ Full color support out of the box

### Windows

✅ Full color support on Windows 10+ (Anniversary Update and later)
- ANSI escape codes are automatically enabled
- Windows Terminal, PowerShell, and Command Prompt supported

### Terminals & Environments

**Supported:**
- macOS Terminal
- iTerm2
- GNOME Terminal
- KDE Konsole
- Windows Terminal
- VS Code integrated terminal
- PyCharm terminal
- Most modern terminal emulators

**Automatic Fallback:**
- Non-TTY outputs (pipes, redirects)
- Older Windows versions
- Terminals without ANSI support

Example Output
--------------

Console Output with Colors
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   ====================================================================
   RePORTaLiN - Report India Clinical Study Data Pipeline
   ====================================================================

   --- Sheet: 'tblENROL' ---
   INFO: Found 2 table(s) in 'tblENROL'
   Processing sheets: 100%|████████████████| 14/14 [00:00<00:00, 122.71sheet/s]
   SUCCESS: Excel processing complete!
   SUCCESS: Step 0: Loading Data Dictionary completed successfully.

   Found 43 Excel files to process...
   Processing files: 100%|████████████████| 43/43 [00:15<00:00, 2.87file/s]

   Extraction complete:
     ✓ 1,854,110 total records processed
     ✓ 43 JSONL files created
     ⊙ 5 files skipped (already exist)
     → Output directory: results/dataset/Indo-vap

   SUCCESS: Step 1: Extracting Raw Data to JSONL completed successfully.

Technical Details
-----------------

### Implementation

Color support is implemented using ANSI escape codes:

.. code-block:: python

   # Example: Green bold text
   print(f"\033[1m\033[32mSuccess!\033[0m")

### Color Codes Reference

==================  ==============  ===================
Color               ANSI Code       Usage
==================  ==============  ===================
Reset               \\033[0m        End color formatting
Bold                \\033[1m        Bold text
Green               \\033[32m       Success indicators
Red                 \\033[31m       Errors
Yellow              \\033[33m       Warnings/skipped
Cyan                \\033[36m       Info/progress
Bright Green        \\033[92m       SUCCESS log level
Bright Cyan         \\033[96m       INFO log level
==================  ==============  ===================

### Auto-Detection

The system automatically detects color support:

.. code-block:: python

   def _supports_color() -> bool:
       """Check if the terminal supports color output."""
       # Check if output is a terminal
       if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
           return False
       
       # Windows: Enable ANSI codes
       if sys.platform == 'win32':
           try:
               import ctypes
               kernel32 = ctypes.windll.kernel32
               kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
               return True
           except:
               return False
       
       # Unix-like systems
       return True

API Reference
-------------

### setup_logger()

.. code-block:: python

   def setup_logger(
       name: str = "reportalin",
       log_level: int = logging.INFO,
       use_color: bool = True
   ) -> logging.Logger:
       """
       Set up central logger with file and console handlers.
       
       Args:
           name: Logger name
           log_level: Minimum log level to capture
           use_color: Enable colored console output (default: True)
       
       Returns:
           Configured logger instance
       """

### ColoredFormatter

.. code-block:: python

   class ColoredFormatter(logging.Formatter):
       """Custom log formatter with color support for console output."""
       
       LEVEL_COLORS = {
           logging.DEBUG: Colors.BRIGHT_BLACK,
           logging.INFO: Colors.CYAN,
           logging.WARNING: Colors.YELLOW,
           logging.ERROR: Colors.RED,
           logging.CRITICAL: Colors.BOLD + Colors.BG_RED + Colors.WHITE,
           SUCCESS: Colors.BOLD + Colors.GREEN,
       }

Configuration
-------------

### Environment Variables

Force disable colors using environment variable:

.. code-block:: bash

   # Disable colors
   export NO_COLOR=1
   python main.py
   
   # Or use command-line flag
   python main.py --no-color

### Programmatic Control

Control colors in your own scripts:

.. code-block:: python

   from scripts.utils import logging as log
   
   # Enable colors
   logger = log.setup_logger(use_color=True)
   
   # Disable colors
   logger = log.setup_logger(use_color=False)

Best Practices
--------------

**When to Use Colors:**
- Interactive terminal sessions
- Development and debugging
- Real-time monitoring

**When to Disable Colors:**
- Redirecting output to files
- CI/CD pipelines
- Log aggregation systems
- Terminals without ANSI support
- Accessibility requirements (screen readers)

Troubleshooting
---------------

### Colors Not Showing

**Issue:** Colors not appearing in output

**Solutions:**

1. Check terminal support:

   .. code-block:: bash
   
      # Test if your terminal supports colors
      echo -e "\033[32mThis should be green\033[0m"

2. Ensure output is a TTY:

   .. code-block:: bash
   
      # Colors won't show when piping
      python main.py | less  # No colors
      
      # Use this instead:
      python main.py         # Colors work

3. Windows users: Update to Windows 10 Anniversary Update or later

### Garbled Output

**Issue:** Seeing escape codes like `\033[32m` instead of colors

**Solution:** Your terminal doesn't support ANSI codes. Use `--no-color`:

.. code-block:: bash

   python main.py --no-color

### Colors in Log Files

**Issue:** Color codes appearing in log files

**Solution:** This should not happen. File output uses plain formatting. If you see escape codes in files, please report as a bug.

Future Enhancements
-------------------

Potential future additions:

- Custom color schemes
- Color configuration file
- 256-color palette support
- RGB color support for modern terminals
- Configurable color mappings per log level
- Theme presets (dark mode, light mode, high contrast)

See Also
--------

- :doc:`../user_guide/usage` - Usage guide
- :doc:`../user_guide/configuration` - Configuration options
- :doc:`architecture` - System architecture
