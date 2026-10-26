#!/usr/bin/env bash
# Render a markdown file in the terminal using glow.
# Usage: ./lvr view-md [file.md]
# Default: data/LVR_Q_Study_Outline.md

set -euo pipefail

file="${1:-data/LVR_Q_Study_Outline.md}"

if [ ! -f "$file" ]; then
  echo "File not found: $file" >&2
  exit 1
fi

exec glow -p "$file"
