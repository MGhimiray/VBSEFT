#!/usr/bin/env python3

import re
import sys
import glob
from collections import OrderedDict

if len(sys.argv) < 2:
    print("Usage: python3 sum_yields.py 'log/vbs__20250_676_*.out'")
    sys.exit(1)

files = sorted(glob.glob(sys.argv[1]))

if not files:
    print("No files found")
    sys.exit(1)

pattern = re.compile(
    r"^(.*?):\s+pass=(\d+)\s+all=(\d+)\s+--\s+eff=.*?cumulative eff=.*?$"
)

yields = OrderedDict()

for fname in files:
    with open(fname, "r") as f:
        for line in f:
            line = line.strip()
            match = pattern.match(line)
            if not match:
                continue

            cut_name = match.group(1).strip()
            passed = int(match.group(2))
            total = int(match.group(3))

            if cut_name not in yields:
                yields[cut_name] = {"pass": 0, "all": 0}

            yields[cut_name]["pass"] += passed
            yields[cut_name]["all"] += total

# denominator for cumulative efficiency = first cut's all
first_cut = next(iter(yields))
cumulative_den = yields[first_cut]["all"]

print(f"Combined files: {len(files)}")
print()

for cut_name, vals in yields.items():
    passed = vals["pass"]
    total = vals["all"]

    eff = 100.0 * passed / total if total > 0 else 0.0
    cum_eff = 100.0 * passed / cumulative_den if cumulative_den > 0 else 0.0

    print(
        f"{cut_name}: pass={passed:<10d} all={total:<10d} "
        f"-- eff={eff:6.2f} % cumulative eff={cum_eff:6.2f} %"
    )
