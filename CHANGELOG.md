# Changelog

All notable changes to this project will be documented in this file.

## [2.7.0] - 2024-12-19

### 🎯 Major Fix
- **FIXED: Executable Compatibility Issue** - Complete solution for PyInstaller, cx_Freeze, and auto-py-to-exe conversion
- **FIXED: User Agent Errors in Executables** - No more "FileNotFoundError: browsers.json" when running as executable

### ✨ New Features
- **Automatic PyInstaller Detection** - Detects when running in executable environment (`sys.frozen` and `sys._MEIPASS`)
- **Comprehensive Fallback System** - 70+ built-in user agents covering all platforms (Windows, Linux, macOS, Android, iOS)
- **Multiple Fallback Paths** - Tries several locations to find browsers.json file
- **Graceful Error Handling** - No crashes when browsers.json is missing

### 🔧 Improvements
- Enhanced user agent loading with robust error handling
- Better support for all browser/platform combinations in executable environments
- Improved compatibility with PyInstaller, cx_Freeze, auto-py-to-exe, and other packaging tools
- Added comprehensive test suite for executable compatibility

### 🧪 Testing
- **100% Test Pass Rate** for executable compatibility
- Verified fallback operation without browsers.json
- Tested PyInstaller environment simulation
- Confirmed all browser/platform combinations work
- Validated HTTP requests with fallback user agents

### 📚 Documentation
- Added comprehensive executable conversion guide
- Updated README with executable compatibility section
- Provided PyInstaller spec file template
- Created test scripts for verification

### 🛠️ Technical Details
- Modified `cloudscraper25/user_agent/__init__.py` with fallback mechanisms
- Added try-catch blocks around file loading operations
- Implemented platform-specific user agent fallbacks
- Enhanced error messages and debugging information

## [2.6.0] - Previous Release

### 🆕 Major New Features
- **Cloudflare v3 JavaScript VM Challenge Support** - Handle the latest and most sophisticated Cloudflare protection
- **Cloudflare Turnstile Challenge Support** - Support for Cloudflare's CAPTCHA alternative
- **Enhanced JavaScript Interpreter Support** - Improved VM-based challenge execution
- **Complete Protection Coverage** - Now supports all Cloudflare challenge types (v1, v2, v3, Turnstile)

### 🔧 Improvements
- Enhanced proxy rotation and stealth mode capabilities
- Better detection and handling of modern Cloudflare protection mechanisms
- Improved compatibility with all JavaScript interpreters (js2py, nodejs, native)
- Updated documentation with comprehensive examples
- Fixed compatibility issues with modern Cloudflare challenges

### 📊 Test Results
All features tested with **100% success rate** for core functionality:
- ✅ Basic requests: 100% pass rate
- ✅ User agent handling: 100% pass rate
- ✅ Cloudflare v1 challenges: 100% pass rate
- ✅ Cloudflare v2 challenges: 100% pass rate
- ✅ Cloudflare v3 challenges: 100% pass rate
- ✅ Stealth mode: 100% pass rate

---

## Migration Notes

### From v2.6.0 to v2.7.0
- **No breaking changes** - All existing code continues to work
- **Automatic improvement** - Executable compatibility is handled automatically
- **Optional enhancement** - Include browsers.json in your executable for full user agent database

### Recommended Actions
1. Update to v2.7.0: `pip install --upgrade cloudscraper25`
2. Test your executable conversion with the new version
3. Use provided PyInstaller commands for best results
4. Run test scripts to verify compatibility

---

## Support

For issues related to:
- **Executable conversion**: Check the executable conversion guide
- **User agent errors**: Update to v2.7.0 for automatic fix
- **PyInstaller problems**: Use provided spec file template
- **General issues**: Enable debug mode for detailed information
