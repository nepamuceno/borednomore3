#!/bin/bash

# Create main package directory
mkdir -p bnm3_transitions/categories/fades
mkdir -p bnm3_transitions/categories/slides
mkdir -p bnm3_transitions/categories/wipes

# Create core files
touch bnm3_transitions/__init__.py
touch bnm3_transitions/base.py
touch bnm3_transitions/manager.py

# Create Fade category files
touch bnm3_transitions/categories/fades/__init__.py
touch bnm3_transitions/categories/fades/meta.json
touch bnm3_transitions/categories/fades/engine.py

# Create Slide category files
touch bnm3_transitions/categories/slides/__init__.py
touch bnm3_transitions/categories/slides/meta.json
touch bnm3_transitions/categories/slides/engine.py

# Create Wipe category files
touch bnm3_transitions/categories/wipes/__init__.py
touch bnm3_transitions/categories/wipes/meta.json
touch bnm3_transitions/categories/wipes/engine.py

echo "Structure created successfully."
ls -R bnm3_transitions/
