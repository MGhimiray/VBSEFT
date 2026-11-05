#!/usr/bin/env python3

import ROOT

from utilsAna import getDATAlist


# ==========================================================
# Configuration
# ==========================================================

skimType = "3l"


# ==========================================================
# DATA samples grouped by analysis year
# ==========================================================

samples = {

    # 2022 pre-EE
    "20220": [
        1001, 1002,
        1011, 1012,
        1021, 1022, 1023,
        1031, 1032, 1033,
        1042, 1043
    ],

    # 2022 post-EE
    "20221": [
        1024, 1025, 1026,
        1034, 1035, 1036,
        1044, 1045, 1046
    ],

    # 2023 pre-BPix
    "20230": [
        1022,
        1032,
        1042
    ],

    # 2023 post-BPix
    "20231": [
        1023,
        1033,
        1043
    ],

    # 2024
    "20240": [
        1022, 1023, 1024, 1025, 1026, 1027, 1028,
        1032, 1033, 1034, 1035, 1036, 1037, 1038,
        1042, 1043, 1044, 1045, 1046, 1047, 1048
    ],

    # 2025
    "20250": [
        1021, 1022, 1023, 1024, 1025, 1026,
        1031, 1032, 1033, 1034, 1035, 1036,
        1041, 1042, 1043, 1044, 1045, 1046
    ],

    # 2026
    "20260": [
        1020, 1021, 1023,
        1030, 1031, 1033, 1034,
        1040, 1041, 1043
    ]
}


# ==========================================================
# Convert analysis-year code to actual year
# ==========================================================

year_lookup = {
    "20220": 2022,
    "20221": 2022,
    "20230": 2023,
    "20231": 2023,
    "20240": 2024,
    "20250": 2025,
    "20260": 2026,
}


# ==========================================================
# ROOT file validation
# ==========================================================

def check_root_file(fname):

    try:

        fname = str(fname)

        f = ROOT.TFile.Open(fname)

        if not f or f.IsZombie():
            return False, "CORRUPTED ROOT FILE"

        events = f.Get("Events")

        if events is None:
            f.Close()
            return False, "NO Events TREE"

        nev = events.GetEntries()

        f.Close()

        if nev == 0:
            return False, "EMPTY Events TREE"

        return True, nev

    except Exception as e:
        return False, str(e)


# ==========================================================
# Check duplicate IDs inside each year
#
# Same data ID appearing in DIFFERENT years is completely
# normal, e.g. 1022 exists for several years.
# ==========================================================

print("\n==============================")
print("Duplicate IDs within each year")
print("==============================")

for year_code, ids in samples.items():

    duplicates = sorted({
        x for x in ids
        if ids.count(x) > 1
    })

    if duplicates:
        print(year_code, ":", duplicates)
    else:
        print(year_code, ": None")


# ==========================================================
# Main validation
# ==========================================================

print("\n\n==============================")
print(" DATA SAMPLE VALIDATION")
print("==============================")


summary = []


for year_code, sample_list in samples.items():

    actual_year = year_lookup[year_code]

    print("\n\n################################")
    print("Analysis year :", year_code)
    print("DATA year     :", actual_year)
    print("################################")

    for sample in sample_list:

        print("\n--------------------------------")
        print("Sample ID :", sample)
        print("Year      :", actual_year)

        # --------------------------------------------------
        # Get DATA files
        # --------------------------------------------------

        try:

            files = getDATAlist(
                sample,
                actual_year,
                skimType
            )

        except Exception as e:

            print("❌ getDATAlist failed:", e)

            summary.append(
                (year_code, sample, "NO DEFINITION")
            )

            continue


        # Convert to ordinary Python list if necessary
        try:
            nfiles = len(files)
        except Exception:
            nfiles = files.size()


        print("ROOT files found:", nfiles)


        if nfiles == 0:

            print("❌ NO ROOT FILES")

            summary.append(
                (year_code, sample, "NO FILES")
            )

            continue


        # --------------------------------------------------
        # Validate ROOT files
        # --------------------------------------------------

        good = 0
        bad = []

        total_events = 0


        for fname in files:

            ok, result = check_root_file(fname)

            if ok:

                good += 1
                total_events += result

            else:

                bad.append(
                    (str(fname), result)
                )


        print("Good files   :", good)
        print("Bad files    :", len(bad))
        print("Total events :", total_events)


        # --------------------------------------------------
        # Report
        # --------------------------------------------------

        if bad:

            print("\nBAD FILES:")

            for bf, msg in bad:

                print(" ", bf)
                print("    ", msg)

            summary.append(
                (year_code, sample, "BAD ROOT")
            )

        elif total_events == 0:

            print("❌ ZERO EVENTS")

            summary.append(
                (year_code, sample, "ZERO EVENTS")
            )

        else:

            print("✅ DATA SAMPLE OK")

            summary.append(
                (year_code, sample, "OK")
            )


# ==========================================================
# Final summary
# ==========================================================

print("\n\n==============================")
print(" FINAL SUMMARY")
print("==============================")


problem_count = 0


for year_code, sample, status in summary:

    if status != "OK":

        problem_count += 1

        print(
            f"{year_code}  sample={sample}  --> {status}"
        )


print("\n------------------------------")

if problem_count == 0:

    print("✅ ALL DATA SAMPLES OK")

else:

    print(
        f"❌ Total problematic data samples: {problem_count}"
    )

print("------------------------------")

print("\nDONE")
