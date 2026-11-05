#!/usr/bin/env python3

import ROOT
import sys
import os
import glob
import re

ROOT.gROOT.SetBatch(True)

# ============================================================
# Usage
# ============================================================
#
# python3 checkemptybins.py \
# ../../../../Outputs_EFT/fakerrate/1018/0000/datacards/merged/
#
# ============================================================

if len(sys.argv) != 2:
    print(f"Usage: python3 {sys.argv[0]} merged_directory")
    sys.exit(1)

directory = sys.argv[1]

if not os.path.isdir(directory):
    print(f"Directory does not exist: {directory}")
    sys.exit(1)


def is_systematic(name):
    return name.endswith("Up") or name.endswith("Down")


def is_data(name):
    n = name.lower()

    return (
        "data_obs" in n
        or n == "data"
        or n == "histo_data"
        or n.startswith("histo_data_")
    )


def is_interference(name):
    n = name.lower()

    return (
        "histo_int_" in n
        or n.startswith("int_")
        or "_interference_" in n
    )


def is_quadratic(name):
    n = name.lower()

    return (
        "histo_quad_" in n
        or n.startswith("quad_")
        or "_quadratic_" in n
    )


# ============================================================
# Find all EFT ROOT files
# ============================================================

files = glob.glob(
    os.path.join(
        directory,
        "output_sswwAnalysis*_allYears_bin0.root"
    )
)


# Operator order
operator_order = [
    "M0",
    "M1",
    "M7",
    "S0",
    "T0",
    "T1",
    "T2",
]


operator_files = {}

for filename in files:

    basename = os.path.basename(filename)

    match = re.search(
        r"output_sswwAnalysis\d+_([MST]\d+)_allYears_bin0\.root",
        basename
    )

    if match:
        operator = match.group(1)
        operator_files[operator] = filename


# ============================================================
# Process one ROOT file
# ============================================================

def process_file(filename):

    f = ROOT.TFile.Open(filename)

    if not f or f.IsZombie():
        return None

    sm_histograms = {}
    int_histograms = {}
    quad_histograms = {}

    nbins = None

    # --------------------------------------------------------
    # Read nominal histograms
    # --------------------------------------------------------

    for key in f.GetListOfKeys():

        obj = key.ReadObj()

        if not obj.InheritsFrom("TH1"):
            continue

        name = obj.GetName()

        # Ignore systematic variations
        if is_systematic(name):
            continue

        # Determine number of bins from first histogram
        if nbins is None:
            nbins = obj.GetNbinsX()

        # Only use histograms with same binning
        if obj.GetNbinsX() != nbins:
            continue

        # Ignore data
        if is_data(name):
            continue

        if is_interference(name):
            int_histograms[name] = obj

        elif is_quadratic(name):
            quad_histograms[name] = obj

        else:
            sm_histograms[name] = obj


    if nbins is None:
        f.Close()
        return None


    # --------------------------------------------------------
    # Construct SM, LIN, QUAD
    # --------------------------------------------------------

    sm_content = [0.0] * (nbins + 1)
    lin_content = [0.0] * (nbins + 1)
    quad_content = [0.0] * (nbins + 1)


    for h in sm_histograms.values():

        for ibin in range(1, nbins + 1):
            sm_content[ibin] += h.GetBinContent(ibin)


    for h in int_histograms.values():

        for ibin in range(1, nbins + 1):
            lin_content[ibin] += h.GetBinContent(ibin)


    for h in quad_histograms.values():

        for ibin in range(1, nbins + 1):
            quad_content[ibin] += h.GetBinContent(ibin)


    # --------------------------------------------------------
    # Find empty bins
    # --------------------------------------------------------

    eps = 1e-12

    empty_sm = []
    empty_sm_lin_quad = []
    empty_quad = []


    for ibin in range(1, nbins + 1):

        sm = sm_content[ibin]
        lin = lin_content[ibin]
        quad = quad_content[ibin]

        sm_lin_quad = sm + lin + quad


        if abs(sm) < eps:
            empty_sm.append(ibin)


        if abs(sm_lin_quad) < eps:
            empty_sm_lin_quad.append(ibin)


        if abs(quad) < eps:
            empty_quad.append(ibin)


    f.Close()

    return (
        nbins,
        empty_sm,
        empty_sm_lin_quad,
        empty_quad,
    )


# ============================================================
# Print results
# ============================================================

for operator in operator_order:

    if operator not in operator_files:
        continue

    result = process_file(operator_files[operator])

    if result is None:
        continue

    nbins, empty_sm, empty_sm_lin_quad, empty_quad = result


    print()
    print(operator)

    print(
        f"SM empty bins: {len(empty_sm)} / {nbins}"
    )
    print(empty_sm)

    print(
        f"SM+LIN+QUAD empty bins: "
        f"{len(empty_sm_lin_quad)} / {nbins}"
    )
    print(empty_sm_lin_quad)

    print(
        f"QUAD empty bins: {len(empty_quad)} / {nbins}"
    )
    print(empty_quad)