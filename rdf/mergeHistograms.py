#!/usr/bin/env python3

import argparse
import math
import re
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path

import ROOT

# python3 mergeHistograms_fast.py --year 20220
# python3 mergeHistograms_fast.py --dir 1013 --year 20240

ROOT.PyConfig.DisableRootLogon = True
ROOT.gROOT.SetBatch(True)


# ============================================================
# Default configuration
#
# These values are used when no command-line arguments are given.
# ============================================================

BASE_DIRECTORY = Path(
    "/mnt/home/mghimiray/VBSStudies/Outputs_EFT/fakerratecheck"
)

DEFAULT_DIRS = [
#    "1000",
     "1000",
#     "1016",
#     "1013",
]

DEFAULT_CUTOFFS = [
     "0000",
#     "1000",
#     "1200",
#     "1500",
#     "2000",
#     "3000",
]

DEFAULT_YEARS = [
    "20220",
    "20221",
    "20230",
    "20231",
    "20240",
    "20250",
]

# None means process every histogram variable found in the ROOT file.
DEFAULT_VARIABLES = None

# To process only selected variables, use something like:
#
# DEFAULT_VARIABLES = {
#     10,
#     11,
#     12,
#     115,
# }

DEFAULT_PREFIX = "fillhisto_wzAnalysis"
DEFAULT_OUTPUT_SUBDIRECTORY = "merge1"

# Number of parallel processes used by hadd.
DEFAULT_HADD_JOBS = 8

# Keep the complete hadd output file in addition to the split files.
DEFAULT_KEEP_COMBINED_FILE = False


# ============================================================
# General utility functions
# ============================================================

def parse_string_list(value):
    """
    Convert a comma-separated string into a list.

    Example:
        "20220,20221,20230"
    becomes:
        ["20220", "20221", "20230"]
    """
    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


def parse_variable_list(value):
    """
    Convert the --variables argument into a set of integers.

    Examples:
        --variables all
            returns None

        --variables 10,11,12,115
            returns {10, 11, 12, 115}
    """
    if value is None:
        return None

    if value.lower() == "all":
        return None

    return {
        int(item.strip())
        for item in value.split(",")
        if item.strip()
    }


# ============================================================
# Overflow handling for 1D histograms
# ============================================================

def add_1d_bin(histogram, destination_bin, source_bin):
    """
    Add the content and uncertainty of source_bin into destination_bin.
    """
    new_content = (
        histogram.GetBinContent(destination_bin)
        + histogram.GetBinContent(source_bin)
    )

    new_error = math.hypot(
        histogram.GetBinError(destination_bin),
        histogram.GetBinError(source_bin)
    )

    histogram.SetBinContent(destination_bin, new_content)
    histogram.SetBinError(destination_bin, new_error)

    histogram.SetBinContent(source_bin, 0.0)
    histogram.SetBinError(source_bin, 0.0)


def fold_1d_overflow(histogram):
    """
    Fold the overflow into the last regular bin.
    """
    last_regular_bin = histogram.GetNbinsX()
    overflow_bin = last_regular_bin + 1

    add_1d_bin(
        histogram,
        last_regular_bin,
        overflow_bin
    )


# ============================================================
# Overflow handling for 2D histograms
# ============================================================

def add_2d_bin(
    histogram,
    destination_x,
    destination_y,
    source_x,
    source_y
):
    """
    Add one 2D bin into another and combine errors in quadrature.
    """
    destination_content = histogram.GetBinContent(
        destination_x,
        destination_y
    )

    source_content = histogram.GetBinContent(
        source_x,
        source_y
    )

    destination_error = histogram.GetBinError(
        destination_x,
        destination_y
    )

    source_error = histogram.GetBinError(
        source_x,
        source_y
    )

    histogram.SetBinContent(
        destination_x,
        destination_y,
        destination_content + source_content
    )

    histogram.SetBinError(
        destination_x,
        destination_y,
        math.hypot(destination_error, source_error)
    )

    histogram.SetBinContent(
        source_x,
        source_y,
        0.0
    )

    histogram.SetBinError(
        source_x,
        source_y,
        0.0
    )


def fold_2d_overflow(histogram):
    """
    Fold both X and Y overflow bins into the final regular bins.

    The X-overflow/Y-overflow corner is also included.
    """
    number_of_x_bins = histogram.GetNbinsX()
    number_of_y_bins = histogram.GetNbinsY()

    x_overflow = number_of_x_bins + 1
    y_overflow = number_of_y_bins + 1

    # Fold Y overflow for all normal X bins.
    for x_bin in range(1, number_of_x_bins + 1):
        add_2d_bin(
            histogram,
            x_bin,
            number_of_y_bins,
            x_bin,
            y_overflow
        )

    # Fold X overflow for all normal Y bins.
    for y_bin in range(1, number_of_y_bins + 1):
        add_2d_bin(
            histogram,
            number_of_x_bins,
            y_bin,
            x_overflow,
            y_bin
        )

    # Fold the X-overflow/Y-overflow corner.
    add_2d_bin(
        histogram,
        number_of_x_bins,
        number_of_y_bins,
        x_overflow,
        y_overflow
    )


# ============================================================
# ROOT key discovery
# ============================================================

def discover_histograms(input_file, selected_variables=None):
    """
    Inspect the ROOT file and determine which histograms actually exist.

    This avoids looping over all 1600 possible histogram indices.
    """
    histograms_1d = defaultdict(dict)
    histograms_mva = defaultdict(dict)
    histograms_2d = defaultdict(dict)

    histograms_nonprompt = {}
    histograms_wrongsign = {}

    regular_1d_pattern = re.compile(
        r"^histo_(\d+)_(\d+)$"
    )

    mva_pattern = re.compile(
        r"^histoMVA_(\d+)_(\d+)$"
    )

    regular_2d_pattern = re.compile(
        r"^histo2d_(\d+)_(\d+)$"
    )

    nonprompt_pattern = re.compile(
        r"^histoNonPrompt_(\d+)$"
    )

    wrongsign_pattern = re.compile(
        r"^histoWS_(\d+)$"
    )

    for key in input_file.GetListOfKeys():
        histogram_name = key.GetName()

        # Regular 1D histogram
        match = regular_1d_pattern.match(histogram_name)

        if match:
            variable_index = int(match.group(1))
            category_index = int(match.group(2))

            if (
                selected_variables is None
                or variable_index in selected_variables
            ):
                histograms_1d[variable_index][category_index] = (
                    histogram_name
                )

            continue

        # MVA histogram
        match = mva_pattern.match(histogram_name)

        if match:
            variable_index = int(match.group(1))
            category_index = int(match.group(2))

            if (
                selected_variables is None
                or variable_index in selected_variables
            ):
                histograms_mva[variable_index][category_index] = (
                    histogram_name
                )

            continue

        # Regular 2D histogram
        match = regular_2d_pattern.match(histogram_name)

        if match:
            variable_index = int(match.group(1))
            category_index = int(match.group(2))

            if (
                selected_variables is None
                or variable_index in selected_variables
            ):
                histograms_2d[variable_index][category_index] = (
                    histogram_name
                )

            continue

        # Nonprompt histogram
        match = nonprompt_pattern.match(histogram_name)

        if match:
            category_index = int(match.group(1))
            histograms_nonprompt[category_index] = histogram_name
            continue

        # Wrong-sign histogram
        match = wrongsign_pattern.match(histogram_name)

        if match:
            category_index = int(match.group(1))
            histograms_wrongsign[category_index] = histogram_name

    return (
        histograms_1d,
        histograms_mva,
        histograms_2d,
        histograms_nonprompt,
        histograms_wrongsign
    )


# ============================================================
# Write output ROOT files
# ============================================================

def write_histogram_group(
    input_file,
    histogram_names,
    output_filename,
    output_name_function,
    is_2d=False
):
    """
    Write one group of histograms to an output ROOT file.

    histogram_names is a dictionary:

        category_index -> histogram_name
    """
    if not histogram_names:
        return

    output_filename.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = ROOT.TFile(
        str(output_filename),
        "RECREATE"
    )

    if not output_file or output_file.IsZombie():
        raise RuntimeError(
            f"Could not create output file: {output_filename}"
        )

    number_written = 0

    for category_index, input_histogram_name in sorted(
        histogram_names.items()
    ):
        source_histogram = input_file.Get(
            input_histogram_name
        )

        if not source_histogram:
            print(
                "Warning: could not read "
                f"{input_histogram_name}"
            )
            continue

        output_histogram_name = output_name_function(
            category_index
        )

        histogram = source_histogram.Clone(
            output_histogram_name
        )

        histogram.SetDirectory(0)

        histogram.SetNameTitle(
            output_histogram_name,
            output_histogram_name
        )

        if is_2d:
            fold_2d_overflow(histogram)
        else:
            fold_1d_overflow(histogram)

        output_file.cd()

        histogram.Write(
            "",
            ROOT.TObject.kOverwrite
        )

        number_written += 1

    output_file.Close()

    if number_written == 0:
        output_filename.unlink(missing_ok=True)
    else:
        print(f"Created: {output_filename}")


# ============================================================
# Merge job files with hadd
# ============================================================

def run_hadd(
    input_files,
    output_file,
    number_of_processes
):
    """
    Merge all ROOT job files once using hadd.

    -f:
        overwrite the existing output file

    -T:
        do not merge TTrees

    -j:
        use multiple processes
    """
    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file.unlink(missing_ok=True)

    command = [
        "hadd",
        "-f",
        "-T",
        "-j",
        str(number_of_processes),
        str(output_file),
    ]

    command.extend(
        str(input_file)
        for input_file in input_files
    )

    print()
    print(
        f"Merging {len(input_files)} ROOT files "
        f"with {number_of_processes} hadd processes"
    )

    print(f"Temporary merged file: {output_file}")

    try:
        subprocess.run(
            command,
            check=True
        )
    except FileNotFoundError as error:
        raise RuntimeError(
            "The hadd command was not found. "
            "Make sure ROOT is configured before running the script."
        ) from error
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            f"hadd failed for output file {output_file}"
        ) from error


# ============================================================
# Process one directory, cutoff and year
# ============================================================

def process_configuration(
    base_directory,
    analysis_directory,
    cutoff,
    year,
    prefix,
    output_subdirectory,
    number_of_processes,
    selected_variables,
    keep_combined_file
):
    """
    Process one combination of:

        analysis directory
        cutoff
        year
    """
    input_directory = (
        base_directory
        / analysis_directory
        / cutoff
        / "histo"
        / prefix
    )

    input_pattern = (
        f"{prefix}{analysis_directory}"
        f"_sample*_year{year}_job*.root"
    )

    input_files = sorted(
        input_directory.glob(input_pattern)
    )

    print()
    print("=" * 80)
    print(f"Analysis directory : {analysis_directory}")
    print(f"Cutoff             : {cutoff}")
    print(f"Year               : {year}")
    print(f"Input directory    : {input_directory}")
    print(f"Input pattern      : {input_pattern}")
    print(f"Number of files    : {len(input_files)}")
    print("=" * 80)

    if not input_files:
        print("No matching input files were found. Skipping.")
        return

    output_directory = (
        base_directory
        / analysis_directory
        / cutoff
        / output_subdirectory
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    temporary_combined_file = (
        output_directory
        / f".{prefix}_{year}_combined_raw.root"
    )

    run_hadd(
        input_files=input_files,
        output_file=temporary_combined_file,
        number_of_processes=number_of_processes
    )

    input_file = ROOT.TFile.Open(
        str(temporary_combined_file),
        "READ"
    )

    if not input_file or input_file.IsZombie():
        raise RuntimeError(
            "Could not open merged ROOT file: "
            f"{temporary_combined_file}"
        )

    (
        histograms_1d,
        histograms_mva,
        histograms_2d,
        histograms_nonprompt,
        histograms_wrongsign
    ) = discover_histograms(
        input_file=input_file,
        selected_variables=selected_variables
    )

    print()
    print("Histograms found:")
    print(f"  1D variables         : {len(histograms_1d)}")
    print(f"  MVA variables        : {len(histograms_mva)}")
    print(f"  2D variables         : {len(histograms_2d)}")
    print(
        "  Nonprompt categories : "
        f"{len(histograms_nonprompt)}"
    )
    print(
        "  Wrong-sign categories: "
        f"{len(histograms_wrongsign)}"
    )

    # --------------------------------------------------------
    # Nonprompt histograms
    # --------------------------------------------------------

    write_histogram_group(
        input_file=input_file,
        histogram_names=histograms_nonprompt,
        output_filename=(
            output_directory
            / f"{prefix}_{year}_nonprompt.root"
        ),
        output_name_function=lambda category: (
            f"histoNonPrompt_{category}"
        ),
        is_2d=False
    )

    # --------------------------------------------------------
    # Wrong-sign histograms
    # --------------------------------------------------------

    write_histogram_group(
        input_file=input_file,
        histogram_names=histograms_wrongsign,
        output_filename=(
            output_directory
            / f"{prefix}_{year}_wrongsign.root"
        ),
        output_name_function=lambda category: (
            f"histoWS_{category}"
        ),
        is_2d=False
    )

    # --------------------------------------------------------
    # Regular 1D histograms
    # --------------------------------------------------------

    for variable_index, category_histograms in sorted(
        histograms_1d.items()
    ):
        output_filename = (
            output_directory
            / f"{prefix}_{year}_{variable_index}.root"
        )

        write_histogram_group(
            input_file=input_file,
            histogram_names=category_histograms,
            output_filename=output_filename,
            output_name_function=lambda category: (
                f"histo{category}"
            ),
            is_2d=False
        )

    # --------------------------------------------------------
    # MVA histograms
    # --------------------------------------------------------

    for variable_index, category_histograms in sorted(
        histograms_mva.items()
    ):
        output_filename = (
            output_directory
            / f"{prefix}_{year}_{variable_index}_mva.root"
        )

        write_histogram_group(
            input_file=input_file,
            histogram_names=category_histograms,
            output_filename=output_filename,
            output_name_function=lambda category: (
                f"histoMVA{category}"
            ),
            is_2d=False
        )

    # --------------------------------------------------------
    # 2D histograms
    # --------------------------------------------------------

    for variable_index, category_histograms in sorted(
        histograms_2d.items()
    ):
        output_filename = (
            output_directory
            / f"{prefix}_{year}_{variable_index}_2d.root"
        )

        write_histogram_group(
            input_file=input_file,
            histogram_names=category_histograms,
            output_filename=output_filename,
            output_name_function=lambda category: (
                f"histo2d{category}"
            ),
            is_2d=True
        )

    input_file.Close()

    # --------------------------------------------------------
    # Keep or delete the temporary complete merged file
    # --------------------------------------------------------

    if keep_combined_file:
        final_combined_file = (
            output_directory
            / f"{prefix}_{year}_all.root"
        )

        final_combined_file.unlink(missing_ok=True)

        shutil.move(
            str(temporary_combined_file),
            str(final_combined_file)
        )

        print()
        print(
            "Complete merged ROOT file retained as:"
        )
        print(final_combined_file)

    else:
        temporary_combined_file.unlink(
            missing_ok=True
        )

    print()
    print(
        f"Finished directory={analysis_directory}, "
        f"cutoff={cutoff}, year={year}"
    )


# ============================================================
# Command-line arguments
# ============================================================

def create_argument_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Fast merging and splitting of EFT ROOT histograms"
        )
    )

    parser.add_argument(
        "--base",
        default=None,
        help=(
            "Base EFT output directory. "
            "When omitted, BASE_DIRECTORY from the script is used."
        )
    )

    parser.add_argument(
        "--dir",
        dest="single_directory",
        default=None,
        help=(
            "Process one analysis directory, "
            "for example --dir 1010"
        )
    )

    parser.add_argument(
        "--dirs",
        default=None,
        help=(
            "Process comma-separated analysis directories, "
            "for example --dirs 1010,1011,1013"
        )
    )

    parser.add_argument(
        "--year",
        dest="single_year",
        default=None,
        help=(
            "Process one year, "
            "for example --year 20220"
        )
    )

    parser.add_argument(
        "--years",
        default=None,
        help=(
            "Process comma-separated years, "
            "for example --years 20220,20221,20230"
        )
    )

    parser.add_argument(
        "--cutoff",
        dest="single_cutoff",
        default=None,
        help=(
            "Process one cutoff, "
            "for example --cutoff 0000"
        )
    )

    parser.add_argument(
        "--cutoffs",
        default=None,
        help=(
            "Process comma-separated cutoffs, "
            "for example --cutoffs 0000,1200,1500"
        )
    )

    parser.add_argument(
        "--variables",
        default=None,
        help=(
            "Comma-separated histogram variable indices, "
            "for example --variables 10,11,12,115. "
            "Use --variables all to process everything."
        )
    )

    parser.add_argument(
        "--prefix",
        "--path",
        dest="prefix",
        default=None,
        help=(
            "Histogram filename prefix. "
            "The default is fillhisto_sswwAnalysis."
        )
    )

    parser.add_argument(
        "--output-subdir",
        default=None,
        help=(
            "Output subdirectory name. "
            "The default is merge1."
        )
    )

    parser.add_argument(
        "--jobs",
        type=int,
        default=None,
        help=(
            "Number of parallel hadd processes. "
            "The default is set inside the script."
        )
    )

    parser.add_argument(
        "--keep-combined",
        action="store_true",
        help=(
            "Keep one complete merged ROOT file for each year."
        )
    )

    parser.add_argument(
        "--do-not-keep-combined",
        action="store_true",
        help=(
            "Delete the temporary complete merged ROOT file."
        )
    )

    return parser


# ============================================================
# Main program
# ============================================================

def main():
    parser = create_argument_parser()
    arguments = parser.parse_args()

    # --------------------------------------------------------
    # Base directory
    # --------------------------------------------------------

    if arguments.base is not None:
        base_directory = Path(arguments.base)
    else:
        base_directory = BASE_DIRECTORY

    # --------------------------------------------------------
    # Analysis directories
    #
    # Priority:
    #   1. --dir
    #   2. --dirs
    #   3. DEFAULT_DIRS
    # --------------------------------------------------------

    if arguments.single_directory is not None:
        analysis_directories = [
            arguments.single_directory
        ]

    elif arguments.dirs is not None:
        analysis_directories = parse_string_list(
            arguments.dirs
        )

    else:
        analysis_directories = DEFAULT_DIRS

    # --------------------------------------------------------
    # Years
    #
    # Priority:
    #   1. --year
    #   2. --years
    #   3. DEFAULT_YEARS
    # --------------------------------------------------------

    if arguments.single_year is not None:
        years = [
            arguments.single_year
        ]

    elif arguments.years is not None:
        years = parse_string_list(
            arguments.years
        )

    else:
        years = DEFAULT_YEARS

    # --------------------------------------------------------
    # Cutoffs
    #
    # Priority:
    #   1. --cutoff
    #   2. --cutoffs
    #   3. DEFAULT_CUTOFFS
    # --------------------------------------------------------

    if arguments.single_cutoff is not None:
        cutoffs = [
            arguments.single_cutoff
        ]

    elif arguments.cutoffs is not None:
        cutoffs = parse_string_list(
            arguments.cutoffs
        )

    else:
        cutoffs = DEFAULT_CUTOFFS

    # --------------------------------------------------------
    # Variables
    # --------------------------------------------------------

    if arguments.variables is not None:
        selected_variables = parse_variable_list(
            arguments.variables
        )
    else:
        selected_variables = DEFAULT_VARIABLES

    # --------------------------------------------------------
    # Prefix
    # --------------------------------------------------------

    if arguments.prefix is not None:
        prefix = arguments.prefix
    else:
        prefix = DEFAULT_PREFIX

    # --------------------------------------------------------
    # Output subdirectory
    # --------------------------------------------------------

    if arguments.output_subdir is not None:
        output_subdirectory = arguments.output_subdir
    else:
        output_subdirectory = (
            DEFAULT_OUTPUT_SUBDIRECTORY
        )

    # --------------------------------------------------------
    # Number of hadd processes
    # --------------------------------------------------------

    if arguments.jobs is not None:
        number_of_processes = arguments.jobs
    else:
        number_of_processes = DEFAULT_HADD_JOBS

    if number_of_processes < 1:
        raise ValueError(
            "--jobs must be at least 1"
        )

    # --------------------------------------------------------
    # Keep complete merged file
    # --------------------------------------------------------

    keep_combined_file = DEFAULT_KEEP_COMBINED_FILE

    if arguments.keep_combined:
        keep_combined_file = True

    if arguments.do_not_keep_combined:
        keep_combined_file = False

    # --------------------------------------------------------
    # Print configuration
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("MERGING CONFIGURATION")
    print("=" * 80)
    print(f"Base directory : {base_directory}")
    print(f"Directories    : {analysis_directories}")
    print(f"Cutoffs        : {cutoffs}")
    print(f"Years          : {years}")
    print(f"Prefix         : {prefix}")
    print(f"Output folder  : {output_subdirectory}")
    print(f"hadd processes : {number_of_processes}")
    print(f"Keep combined  : {keep_combined_file}")

    if selected_variables is None:
        print("Variables      : all available variables")
    else:
        print(
            "Variables      : "
            f"{sorted(selected_variables)}"
        )

    print("=" * 80)

    # --------------------------------------------------------
    # Process every requested combination
    # --------------------------------------------------------

    failed_configurations = []

    for analysis_directory in analysis_directories:
        for cutoff in cutoffs:
            for year in years:
                try:
                    process_configuration(
                        base_directory=base_directory,
                        analysis_directory=analysis_directory,
                        cutoff=cutoff,
                        year=year,
                        prefix=prefix,
                        output_subdirectory=output_subdirectory,
                        number_of_processes=number_of_processes,
                        selected_variables=selected_variables,
                        keep_combined_file=keep_combined_file
                    )

                except Exception as error:
                    print()
                    print(
                        "ERROR while processing "
                        f"directory={analysis_directory}, "
                        f"cutoff={cutoff}, "
                        f"year={year}"
                    )

                    print(str(error))

                    failed_configurations.append(
                        (
                            analysis_directory,
                            cutoff,
                            year,
                            str(error)
                        )
                    )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print()
    print("=" * 80)

    if failed_configurations:
        print(
            "MERGING COMPLETED WITH SOME FAILURES"
        )

        for (
            analysis_directory,
            cutoff,
            year,
            error_message
        ) in failed_configurations:
            print(
                f"  dir={analysis_directory}, "
                f"cutoff={cutoff}, "
                f"year={year}: "
                f"{error_message}"
            )

        raise SystemExit(1)

    print("ALL REQUESTED MERGING COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()
