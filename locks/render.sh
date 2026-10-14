#!/bin/sh
# Render all lock scenes.  Usage: ./render.sh [quality flag, default -qh]
#   -ql  480p15 (fast preview)   -qh  1080p60   -qk  4K
cd "$(dirname "$0")" && exec manim "${1:--qh}" -a scenes.py
