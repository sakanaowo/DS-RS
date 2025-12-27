#!/bin/bash
# Organize workspace files

echo "🧹 Cleaning up workspace..."
echo

# Move documentation to documents/
echo "📚 Moving documentation..."
mv -v DEBUG_GUIDE.md documents/
mv -v QUICKSTART.md documents/
mv -v ROOT_CAUSE_FIX.md documents/

# Move test scripts to tests/
echo "🧪 Moving test scripts..."
mv -v test_encoding_speed.py tests/
mv -v test_fix.py tests/

# Move shell scripts to scripts/
echo "🔧 Moving shell scripts..."
mv -v start_server.sh scripts/
mv -v start_with_progress.sh scripts/

# Move old/backup files to archive/
echo "📦 Moving old files to archive..."
mkdir -p archive/old_apps
mv -v app_old.py archive/old_apps/
mv -v app_simple.py archive/old_apps/

# Clean up logs
echo "🗑️  Cleaning up logs..."
mkdir -p logs
mv -v streamlit.log logs/ 2>/dev/null || true
mv -v temp.txt archive/ 2>/dev/null || true

echo
echo "✅ Workspace organized!"
echo
echo "Structure:"
echo "  documents/ - Documentation (DEBUG_GUIDE, QUICKSTART, ROOT_CAUSE_FIX)"
echo "  tests/ - Test scripts"
echo "  scripts/ - Shell scripts"
echo "  archive/old_apps/ - Old app versions"
echo "  logs/ - Log files"
