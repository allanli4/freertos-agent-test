#!/usr/bin/env python3

import argparse
import json
import re
import urllib.error
import urllib.request

URL = "https://raw.githubusercontent.com/FreeRTOS/FreeRTOS-Kernel/main/examples/coverity/coverity_misra.config"


def fetch_misra_rules():
    """Download and extract MISRA rules from Coverity config"""
    try:
        with urllib.request.urlopen(URL) as response:
            data = json.loads(response.read().decode())
        return extract_rules(data["deviations"])
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        print(
            f"Warning: Could not fetch MISRA rules from URL ({e}). Generating config with static rules only."
        )
        return []


def extract_rules(deviations):
    """Extract rule numbers from deviations and convert to cppcheck format"""
    rules = []
    for deviation in deviations:
        match = re.search(r"(Rule|Directive)\s+(\d+\.\d+)", deviation["deviation"])
        if match:
            rule_num = match.group(2)
            rules.append(f"misra-c2012-{rule_num}")
    return rules


def write_config_file(filename, rules):
    """Write suppression rules to config file"""
    static_rules = [
        "missingIncludeSystem",
        "checkersReport",
        "unmatchedSuppression",
        "misra-config",
    ]
    with open(filename, "w") as f:
        for rule in static_rules + rules:
            f.write(f"{rule}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cppcheck_suppress_file",
        required=True,
        help="Output cppcheck suppression file",
    )
    args = parser.parse_args()

    rules = fetch_misra_rules()
    write_config_file(args.cppcheck_suppress_file, rules)

    if rules:
        print(f"Generated {args.cppcheck_suppress_file} with {len(rules)} MISRA rules")
    else:
        print(
            f"Generated {args.cppcheck_suppress_file} with static rules only (no MISRA rules from URL)"
        )


if __name__ == "__main__":
    main()
