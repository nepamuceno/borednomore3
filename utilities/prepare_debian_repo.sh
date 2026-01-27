#!/bin/bash

# BoredNoMore3 Debian Repository Preparation Script
# This script prepares the source tarball and triggers debuild

VERSION="0.5.4"
SOURCE_DIR="borednomore3"
PARENT_DIR=".."

echo "--- 1. Cleaning up local build trash ---"
# Remove local Nuitka artifacts so they don't end up in the source package
rm -rf dist/ *.build/ *.dist/ *.onefile-build/ __pycache__/

echo "--- 2. Verifying debian/rules permissions ---"
if [ -f "debian/rules" ]; then
    chmod +x debian/rules
else
    echo "❌ Error: debian/rules not found!"
    exit 1
fi

echo "--- 3. Creating the Clean .orig tarball in parent directory ---"
# This is the step that was failing before. We exclude non-source files.
cd $PARENT_DIR
tar -cJf "${SOURCE_DIR}_${VERSION}.orig.tar.xz" \
    --exclude='debian' \
    --exclude='dist' \
    --exclude='history' \
    --exclude='__pycache__' \
    --exclude='*.env' \
    --exclude='*.sh' \
    --exclude='.git' \
    --exclude='*.deb' \
    $SOURCE_DIR

echo "--- 4. Starting the Debian Build (debuild) ---"
cd $SOURCE_DIR
# -us: do not sign source
# -uc: do not sign .changes
debuild -us -uc

echo "------------------------------------------------"
echo "Build process finished."
echo "Check the parent directory for your .deb, .dsc, and .changes files."
