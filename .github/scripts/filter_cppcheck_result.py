#!/usr/bin/env python3
import argparse
import bisect
import csv
import os
import re
import subprocess
import sys
import defusedxml.ElementTree as ET


def get_changed_ranges(file_path, git_diff_range, source_dir="."):
    """Get changed line ranges for a file"""
    if not re.match(r"^[a-zA-Z0-9._/-]+\.\.\.[a-zA-Z0-9._/-]+$", git_diff_range):
        raise ValueError("Invalid git diff range format")

    cmd = ["git", "-C", source_dir, "diff", "-U0", git_diff_range, "--", file_path]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return parse_diff_ranges(result.stdout)
    except Exception as e:
        print(f"Error getting changed lines for {file_path}: {e}")
        return []


def parse_diff_ranges(diff_output):
    """Parse git diff output to extract line ranges"""
    ranges = []
    for line in diff_output.split("\n"):
        if line.startswith("@@"):
            match = re.search(r"\+(\d+)(?:,(\d+))?", line)
            if match:
                start = int(match.group(1))
                count = int(match.group(2)) if match.group(2) else 1
                if count > 0:
                    ranges.append((start, start + count - 1))
    return ranges


def is_line_in_ranges(line_num, ranges):
    """Check if line number is in any of the ranges"""
    if len(ranges) <= 5:
        return any(start <= line_num <= end for start, end in ranges)

    sorted_ranges = sorted(ranges)
    idx = bisect.bisect_left(sorted_ranges, (line_num, line_num))

    for i in [idx - 1, idx]:
        if 0 <= i < len(sorted_ranges):
            start, end = sorted_ranges[i]
            if start <= line_num <= end:
                return True
    return False


def filter_errors_by_changed_lines(root, git_diff_range, source_dir="."):
    """Filter XML errors to only include those in changed lines"""
    filtered_errors = []
    file_ranges_cache = {}

    for error in root.findall(".//error"):
        if not error.get("id", "").startswith("misra-c2012"):
            continue

        for location in error.findall("location"):
            file_path = location.get("file")
            line_num = int(location.get("line", 0))

            if file_path and line_num > 0:
                if file_path not in file_ranges_cache:
                    file_ranges_cache[file_path] = get_changed_ranges(
                        file_path, git_diff_range, source_dir
                    )

                if is_line_in_ranges(line_num, file_ranges_cache[file_path]):
                    filtered_errors.append(error)
                    break

    return filtered_errors


def write_csv_output(filtered_errors, output_file, max_size=None):
    """Write filtered errors to CSV file"""
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["misra-c2012-rule", "severity", "file", "line", "column"])

        for error in filtered_errors:
            error_id = error.get("id", "").replace("misra-c2012-", "")
            severity = error.get("severity", "")

            for location in error.findall("location"):
                file_path = location.get("file", "")
                line_num = location.get("line", "")
                column = location.get("column", "")

                if max_size:
                    row_size = len(
                        f"{error_id},{severity},{file_path},{line_num},{column}\n"
                    )
                    if csvfile.tell() + row_size > max_size:
                        print(f"Output file size limit ({max_size} bytes) reached")
                        return

                writer.writerow([error_id, severity, file_path, line_num, column])


def print_human_readable(filtered_errors):
    """Print errors in human-readable format"""
    for error in filtered_errors:
        severity = error.get("severity", "unknown")
        msg = error.get("msg", "")
        error_id = error.get("id", "")

        for location in error.findall("location"):
            file_path = location.get("file")
            line_num = location.get("line")
            print(f"{file_path}:{line_num}: {severity}: {msg} [{error_id}]")


def filter_cppcheck_results(
    xml_file, git_diff_range, output_file, max_size=None, source_dir="."
):
    """Filter cppcheck XML results to only include changed lines"""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        filtered_errors = filter_errors_by_changed_lines(
            root, git_diff_range, source_dir
        )
        write_csv_output(filtered_errors, output_file, max_size)
        print_human_readable(filtered_errors)

        print(f"Found {len(filtered_errors)} issues in changed lines")
        return len(filtered_errors)

    except Exception as e:
        print(f"Error filtering results: {e}")
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Filter cppcheck results for MISRA violations in changed lines"
    )
    parser.add_argument("--input", required=True, help="Path to cppcheck XML file")
    parser.add_argument(
        "--output", required=True, help="Output CSV for filtered results file path"
    )
    parser.add_argument(
        "--git-diff",
        default="origin/main...HEAD",
        help="Git diff range (default: origin/main...HEAD)",
    )
    parser.add_argument(
        "--max-size",
        type=int,
        help="Maximum output file size in bytes",
    )
    parser.add_argument(
        "--source-dir",
        default=".",
        help="Source code directory (default: current directory)",
    )

    args = parser.parse_args()
    num_issues = filter_cppcheck_results(
        args.input, args.git_diff, args.output, args.max_size, args.source_dir
    )
    print(f"Found {num_issues} misra violations")
    sys.exit(0)
