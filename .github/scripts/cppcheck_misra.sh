#!/bin/bash
# Script to run cppcheck only on changed lines

# Default values
COMMIT_BASE="origin/main"
COMMIT_TARGET="HEAD"
OUTPUT_FILE="cppcheck-full.xml"
SUPPRESSION_FILE="$(dirname "$0")/cppcheck_misra.config"
SOURCE_DIR="."

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --commit-base) COMMIT_BASE="$2"; shift 2 ;;
            --commit-target) COMMIT_TARGET="$2"; shift 2 ;;
            --output) OUTPUT_FILE="$2"; shift 2 ;;
            --suppression-file) SUPPRESSION_FILE="$2"; shift 2 ;;
            --source-dir) SOURCE_DIR="$2"; shift 2 ;;
            *) echo "Unknown option: $1"; echo "Usage: $0 [--commit-base <base>] [--commit-target <target>] [--output <file>] [--suppression-file <file>] [--source-dir <dir>]"; exit 1 ;;
        esac
    done
}

get_changed_files() {
    git -C "$SOURCE_DIR" diff --name-only $COMMIT_BASE...$COMMIT_TARGET | grep -E '\.(c|cpp|cc|cxx|h|hpp)$'
}

parse_args "$@"

# Convert suppression file to absolute path before changing directory
if [ -f "$SUPPRESSION_FILE" ]; then
    SUPPRESSION_FILE=$(realpath "$SUPPRESSION_FILE")
fi

CHANGED_FILES=$(get_changed_files)

if [ -z "$CHANGED_FILES" ]; then
    echo "No C/C++ files changed"
    exit 0
fi

# Run cppcheck on changed files
CPPCHECK_ARGS=(
    --addon=misra
    --enable=all,style,warning,performance,portability,information,unusedFunction,missingInclude
    --suppressions-list="$SUPPRESSION_FILE"
    --inline-suppr
    --language=c
    --std=c89
    --xml
    --xml-version=2
)

(cd "$SOURCE_DIR" && cppcheck "${CPPCHECK_ARGS[@]}" $CHANGED_FILES) 2> "$OUTPUT_FILE"
