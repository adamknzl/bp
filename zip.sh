#!/bin/bash
# @file  zip.sh
# @brief Creates a clean submission zip for bachelor's thesis.
# Run from the project root: bash zip.sh

set -e

OUTPUT="xkinzea00.zip"

# Remove old zip if it exists
if [ -f "$OUTPUT" ]; then
    echo "Removing old $OUTPUT..."
    rm "$OUTPUT"
fi

echo "Creating $OUTPUT..."

zip -r "$OUTPUT" . \
    --exclude ".git/*" \
    --exclude ".git" \
    --exclude "*/node_modules/*" \
    --exclude "*/__pycache__/*" \
    --exclude "*/dist/*" \
    --exclude "*/env/*" \
    --exclude "*/build/*" \
    --exclude "*/.env" \
    --exclude "*/.vscode/*" \
    --exclude "*/res_data.csv" \
    --exclude "*/fetched_urls.csv" \
    --exclude "*/search_cache/*" \
    --exclude "zip_output.txt" \
    --exclude "file_structure.txt" \
    --exclude "zip.sh" \
    --exclude "*.zip"

# Print summary
echo ""
echo "Done: $OUTPUT"
echo "Size: $(du -sh $OUTPUT | cut -f1)"
echo "Files: $(unzip -l $OUTPUT | tail -1 | awk '{print $2}')"
echo ""

# Sanity checks
echo "--- Sanity checks ---"

if unzip -l "$OUTPUT" | grep -q "\.git/"; then
    echo "WARNING: .git directory found in zip!"
else
    echo "OK: No .git directory"
fi

if unzip -l "$OUTPUT" | grep -q "node_modules/"; then
    echo "WARNING: node_modules found in zip!"
else
    echo "OK: No node_modules"
fi

if unzip -l "$OUTPUT" | grep -qE "^.*\.env$" | grep -v "\.env\.example"; then
    echo "WARNING: .env file with credentials found in zip!"
else
    echo "OK: No .env credential files"
fi

if unzip -l "$OUTPUT" | grep -q "res_data.csv"; then
    echo "WARNING: res_data.csv (500MB source file) found in zip!"
else
    echo "OK: No res_data.csv"
fi

echo "---------------------"