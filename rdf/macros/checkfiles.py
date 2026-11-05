#!/usr/bin/env python3

import os
import ROOT

from utilsAna import SwitchSample, getMClist


# ==========================================================
# Configuration
# ==========================================================

skimType = "3l"


# ==========================================================
# MC samples grouped by year
# ==========================================================

samples = {

    # ------------------------------------------------------
    # 2022 pre-EE
    # ------------------------------------------------------
    "20220": [
        179, 183,
        114, 115, 116, 117, 118, 119,
        120, 121, 122, 123, 124,
        129, 130, 131, 132,
        139, 140, 141,
        144,
        148, 149,
        155,
        159, 160, 161, 162, 163, 164,
        178, 182, 190
    ],


    # ------------------------------------------------------
    # 2022 post-EE
    # ------------------------------------------------------
    "20221": [
        279, 283,
        214, 215, 216, 217, 218, 219,
        220, 221, 222, 223, 224,
        229, 230, 231, 232,
        239, 240, 241,
        244,
        248, 249,
        255,
        259, 260, 261, 262, 263, 264,
        278, 282, 290
    ],


    # ------------------------------------------------------
    # 2023 pre-BPix
    # ------------------------------------------------------
    "20230": [
        379, 383,
        314, 315, 316, 317, 318, 319,
        320, 321, 322, 323, 324,
        329, 330, 331, 332,
        344,
        348, 349,
        355,
        359, 360, 361, 362, 363, 364,
        378, 382, 390
    ],


    # ------------------------------------------------------
    # 2023 post-BPix
    # ------------------------------------------------------
    "20231": [
        479, 483,
        414, 415, 416, 417, 418, 419,
        420, 421, 422, 423, 424,
        429, 430, 431, 432,
        444,
        448, 449,
        455,
        459, 460, 461, 462, 463, 464,
        478, 482, 490
    ],


    # ------------------------------------------------------
    # 2024
    # ------------------------------------------------------
    "20240": [
        579, 583,
        514, 515, 516, 517, 518, 519,
        520, 521, 522, 523, 524,
        529,
        532,
        539,
        548, 549,
        555,
        559, 560, 561, 562, 563, 564,
        578, 582,
        586, 587, 588,
        590
    ],


    # ------------------------------------------------------
    # 2025
    # NOTE: these intentionally use the corresponding
    #       2024 MC samples in utilsAna
    # ------------------------------------------------------
    "20250": [
        679, 683,
        614, 615, 616, 617, 618, 619,
        620, 621, 622, 623, 624,
        629,
        632,
        639,
        648, 649,
        655,
        659, 660, 661, 662, 663, 664,
        678, 682,
        686, 687, 688,
        690
    ]

}


# ==========================================================
# ROOT file validation
# ==========================================================

def check_root_file(fname):

    try:

        # Convert ROOT string object to Python string
        fname = str(fname)

        f = ROOT.TFile.Open(fname)

        if not f or f.IsZombie():
            return False, "CORRUPTED ROOT FILE"

        events = f.Get("Events")
        runs   = f.Get("Runs")

        hasEvents = events is not None
        hasRuns   = runs is not None

        nev = -1

        if hasEvents:
            nev = events.GetEntries()

        f.Close()

        if not hasEvents:
            return False, "NO Events TREE"

        if not hasRuns:
            return False, "NO Runs TREE"

        if nev == 0:
            return False, "EMPTY Events TREE"

        return True, nev

    except Exception as e:
        return False, str(e)


# ==========================================================
# Check duplicate sample IDs
# ==========================================================

all_samples = []

for year, ids in samples.items():
    all_samples.extend(ids)


duplicates = [
    x for x in set(all_samples)
    if all_samples.count(x) > 1
]


print("\n==============================")
print("Duplicate sample IDs")
print("==============================")

if duplicates:
    print(sorted(duplicates))
else:
    print("None")


# ==========================================================
# Main validation
# ==========================================================

print("\n\n==============================")
print(" MC SAMPLE VALIDATION")
print("==============================")


summary = []


for year, sample_list in samples.items():

    print("\n\n################################")
    print("Checking year:", year)
    print("################################")

    for sample in sample_list:

        print("\n--------------------------------")
        print("Sample ID:", sample)

        try:
            info = SwitchSample(sample, skimType)

        except Exception as e:

            print("❌ SwitchSample failed:", e)

            summary.append(
                (year, sample, "NO DEFINITION")
            )

            continue


        directory = info[0]
        xs        = info[1]
        category  = info[2]


        print("Category :", category)
        print("XS       :", xs)

        print("Directory:")
        print(directory)


        # --------------------------------------------------
        # Check directory
        # --------------------------------------------------

        if not os.path.exists(directory):

            print("❌ DIRECTORY MISSING")

            summary.append(
                (year, sample, "MISSING DIRECTORY")
            )

            continue


        # --------------------------------------------------
        # Get ROOT files
        # --------------------------------------------------

        try:
            files = getMClist(sample, skimType)

        except Exception as e:

            print("❌ getMClist failed:", e)

            summary.append(
                (year, sample, "getMClist FAILED")
            )

            continue


        print("ROOT files found:", len(files))


        if len(files) == 0:

            print("❌ NO ROOT FILES")

            summary.append(
                (year, sample, "NO FILES")
            )

            continue


        # --------------------------------------------------
        # Validate ROOT files
        # --------------------------------------------------

        good = 0
        bad  = []

        total_events = 0


        for fname in files:

            ok, result = check_root_file(fname)

            if ok:

                good += 1
                total_events += result

            else:

                bad.append(
                    (fname, result)
                )


        print("Good files   :", good)
        print("Bad files    :", len(bad))
        print("Total events :", total_events)


        # --------------------------------------------------
        # Report problems
        # --------------------------------------------------

        if bad:

            print("\nBAD FILES:")

            for bf, msg in bad:

                print(" ", bf)
                print("   ", msg)

            summary.append(
                (year, sample, "BAD ROOT")
            )


        elif total_events < 100:

            print("⚠️ VERY LOW EVENT COUNT")

            summary.append(
                (year, sample, "LOW EVENTS")
            )


        else:

            print("✅ SAMPLE OK")

            summary.append(
                (year, sample, "OK")
            )


# ==========================================================
# Final summary
# ==========================================================

print("\n\n==============================")
print(" FINAL SUMMARY")
print("==============================")


problem_count = 0

for year, sample, status in summary:

    if status != "OK":

        problem_count += 1

        print(
            f"{year}  sample={sample}  --> {status}"
        )


print("\n------------------------------")

if problem_count == 0:
    print("✅ ALL SAMPLES OK")
else:
    print(f"❌ Total problematic samples: {problem_count}")

print("------------------------------")

print("\nDONE")