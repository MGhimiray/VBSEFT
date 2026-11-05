import ROOT
from ROOT import TFile, TH1D, TH2D
import os
import sys
import getopt
import glob
import math

sys.path.append(
    '/mnt/home/mghimiray/VBSStudies/VBSEFTII/MitAnalysisRunIII/rdf/macros'
)

from utilsCategory import plotCategory


if __name__ == "__main__":

    # ============================================================
    # Configuration
    # ============================================================

    path = "fillhisto_sswwAnalysis1013"
    year = 2027

    output = (
        "/mnt/home/mghimiray/VBSStudies/Outputs_EFT/fakerrate/1013/0000/merge2/"
    )

    showUnc = 1

    # ============================================================
    # Command-line options
    # ============================================================

    valid = [
        'path=',
        'year=',
        'output=',
        'unc=',
        'help'
    ]

    usage = "Usage: ana.py --path=<{0}>\n".format(path)
    usage += "              --year=<{0}>\n".format(year)
    usage += "              --output=<{0}>\n".format(output)
    usage += "              --unc=<{0}>\n".format(showUnc)

    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "",
            valid
        )

    except getopt.GetoptError as ex:
        print(usage)
        print(str(ex))
        sys.exit(1)

    for opt, arg in opts:

        if opt == "--help":
            print(usage)
            sys.exit(0)

        elif opt == "--path":
            path = str(arg)

        elif opt == "--year":
            year = int(arg)

        elif opt == "--output":
            output = str(arg)

        elif opt == "--unc":
            showUnc = int(arg)

    # ============================================================
    # Histogram selections
    # ============================================================

    histo = []
    signalDict0 = []
    signalDict1 = []

    # ------------------------------------------------------------
    # SSWW
    # ------------------------------------------------------------

    if 'sswwAnalysis' in path:

        histo.append(18)

        signalDict0.append(
            plotCategory("kPlotEWKSSWW")
        )

        signalDict1.append(
            plotCategory("kPlotEWKSSWW")
        )

        histo.append(19)

        signalDict0.append(
            plotCategory("kPlotEWKSSWW")
        )

        signalDict1.append(
            plotCategory("kPlotEWKSSWW")
        )

    # ------------------------------------------------------------
    # ZZ
    # ------------------------------------------------------------

    elif 'zzAna' in path:

        histo.append(8)

        signalDict0.append(
            plotCategory("kPlotZZ")
        )

        signalDict1.append(
            plotCategory("kPlotZZ")
        )

        histo.append(16)

        signalDict0.append(
            plotCategory("kPlotZZ")
        )

        signalDict1.append(
            plotCategory("kPlotZZ")
        )

    # ------------------------------------------------------------
    # WZ
    # ------------------------------------------------------------

    elif 'wzAna' in path or 'wzAnalysis' in path:

        histo.append(11)

        signalDict0.append(
            plotCategory("kPlotWZ")
        )

        signalDict1.append(
            plotCategory("kPlotWZ")
        )

        histo.append(12)

        signalDict0.append(
            plotCategory("kPlotWZ")
        )

        signalDict1.append(
            plotCategory("kPlotWZ")
        )

        histo.append(17)

        signalDict0.append(
            plotCategory("kPlotWZ")
        )

        signalDict1.append(
            plotCategory("kPlotWZ")
        )

        histo.append(18)

        signalDict0.append(
            plotCategory("kPlotWZ")
        )

        signalDict1.append(
            plotCategory("kPlotWZ")
        )

        histo.append(27)

        signalDict0.append(
            plotCategory("kPlotEWKWZ")
        )

        signalDict1.append(
            plotCategory("kPlotEWKWZ")
        )

        histo.append(28)

        signalDict0.append(
            plotCategory("kPlotEWKWZ")
        )

        signalDict1.append(
            plotCategory("kPlotEWKWZ")
        )

    # ------------------------------------------------------------
    # ZMET
    # ------------------------------------------------------------

    elif 'zmetAna' in path:

        histo.append(34)

        signalDict0.append(
            plotCategory("kPlotZZ")
        )

        signalDict1.append(
            plotCategory("kPlotZZ")
        )

        histo.append(35)

        signalDict0.append(
            plotCategory("kPlotZZ")
        )

        signalDict1.append(
            plotCategory("kPlotZZ")
        )

    # ------------------------------------------------------------
    # WW
    # ------------------------------------------------------------

    elif 'wwAna' in path:

        histo.append(42)

        signalDict0.append(
            plotCategory("kPlotNonPrompt")
        )

        signalDict1.append(
            plotCategory("kPlotNonPrompt")
        )

        histo.append(71)

        signalDict0.append(
            plotCategory("kPlotNonPrompt")
        )

        signalDict1.append(
            plotCategory("kPlotNonPrompt")
        )

        histo.append(72)

        signalDict0.append(
            plotCategory("kPlotNonPrompt")
        )

        signalDict1.append(
            plotCategory("kPlotNonPrompt")
        )

        histo.append(43)

        signalDict0.append(
            plotCategory("kPlotqqWW")
        )

        signalDict1.append(
            plotCategory("kPlotggWW")
        )

        histo.append(44)

        signalDict0.append(
            plotCategory("kPlotDY")
        )

        signalDict1.append(
            plotCategory("kPlotDY")
        )

        histo.append(45)

        signalDict0.append(
            plotCategory("kPlotTT")
        )

        signalDict1.append(
            plotCategory("kPlotTW")
        )

        histo.append(57)

        signalDict0.append(
            plotCategory("kPlotHiggs")
        )

        signalDict1.append(
            plotCategory("kPlotHiggs")
        )

    # ------------------------------------------------------------
    # Z
    # ------------------------------------------------------------

    elif 'zAna' in path:

        histo.append(27)

        signalDict0.append(
            plotCategory("kPlotDY")
        )

        signalDict1.append(
            plotCategory("kPlotDY")
        )

        histo.append(28)

        signalDict0.append(
            plotCategory("kPlotDY")
        )

        signalDict1.append(
            plotCategory("kPlotDY")
        )

        histo.append(29)

        signalDict0.append(
            plotCategory("kPlotDY")
        )

        signalDict1.append(
            plotCategory("kPlotDY")
        )

    else:

        print("ERROR: Could not identify analysis from path:")
        print(path)
        sys.exit(1)

    # ============================================================
    # Number of categories
    # ============================================================

    nCat = plotCategory("kPlotCategories")

    # ============================================================
    # Categories excluded from nominal SM Data/Prediction
    #
    # 19 = BSM
    # 20-25 = signal templates
    # 26-53 = EFT templates
    #
    # Nominal SM prediction therefore uses:
    #
    #   1 ... 18
    #
    # Data is category 0.
    # ============================================================

    firstNonSMCategory = plotCategory("kPlotBSM")

    nonSMCategories = set(
        range(
            firstNonSMCategory,
            nCat
        )
    )

    print("")
    print("=" * 80)
    print("CONFIGURATION")
    print("=" * 80)

    print("Path              :", path)
    print("Year              :", year)
    print("Output            :", output)
    print("Number categories :", nCat)
    print("Histograms        :", histo)

    print(
        "Non-SM categories:",
        sorted(nonSMCategories)
    )

    print(
        "SM categories     : 0-{}".format(
            firstNonSMCategory - 1
        )
    )

    print("=" * 80)
    print("")

    # ============================================================
    # Loop over requested histograms
    # ============================================================

    for nh in range(len(histo)):

        histoNumber = histo[nh]

        print("")
        print("=" * 100)

        print(
            "********** HISTO: {0} **********".format(
                histoNumber
            )
        )

        print("=" * 100)

        # ========================================================
        # Input ROOT file
        # ========================================================

        inputFileName = "{0}/{1}_{2}_{3}.root".format(
            output.rstrip("/"),
            os.path.basename(path),
            year,
            histoNumber
        )

        print("")
        print("Opening:")
        print(inputFileName)

        if not os.path.exists(inputFileName):

            print("")
            print("ERROR: ROOT file does not exist:")
            print(inputFileName)

            continue

        inputFile = TFile(
            inputFileName,
            "READ"
        )

        if not inputFile or inputFile.IsZombie():

            print("")
            print("ERROR: Could not open ROOT file:")
            print(inputFileName)

            continue

        # ========================================================
        # Load histograms
        # ========================================================

        histoSel = [
            None for _ in range(nCat)
        ]

        missingCategories = []
        existingCategories = []

        for i in range(nCat):

            histName = "histo{0}".format(i)

            h = inputFile.Get(histName)

            if not h:

                missingCategories.append(i)

                continue

            histoSel[i] = h.Clone(
                "{0}_clone".format(histName)
            )

            histoSel[i].SetDirectory(0)

            existingCategories.append(i)

        # ========================================================
        # Diagnostics
        # ========================================================

        print("")
        print("----------------------------------------------")
        print("Histogram categories found")
        print("----------------------------------------------")

        print(existingCategories)

        if missingCategories:

            print("")
            print("Missing histogram categories:")

            print(missingCategories)

        else:

            print("")
            print(
                "All {} categories exist.".format(
                    nCat
                )
            )

        # ========================================================
        # Need at least one real histogram
        # ========================================================

        if len(existingCategories) == 0:

            print("")
            print(
                "ERROR: No histoN objects found inside file."
            )

            inputFile.Close()

            continue

        # ========================================================
        # Reference histogram
        # ========================================================

        referenceCategory = existingCategories[0]

        referenceHistogram = histoSel[
            referenceCategory
        ]

        # ========================================================
        # Create empty histograms for missing categories
        # ========================================================

        for i in missingCategories:

            histName = "histo{0}".format(i)

            histoSel[i] = referenceHistogram.Clone(
                "{0}_empty".format(histName)
            )

            histoSel[i].Reset("ICES")

            histoSel[i].SetNameTitle(
                histName,
                histName
            )

            histoSel[i].SetDirectory(0)

        inputFile.Close()

        # ========================================================
        # Integral diagnostic
        # ========================================================

        print("")
        print("=" * 100)
        print("CATEGORY INTEGRALS")
        print("=" * 100)

        for i in range(nCat):

            integral = histoSel[i].Integral(
                0,
                histoSel[i].GetNbinsX() + 1
            )

            if i in missingCategories:

                status = "MISSING -> zero"

            elif i in nonSMCategories:

                status = "EFT/BSM -> excluded from SM prediction"

            else:

                status = "SM"

            print(
                "histo{0:2d} : "
                "{1:15.6f}    {2}".format(
                    i,
                    integral,
                    status
                )
            )

        print("=" * 100)
        print("")

        # ========================================================
        # Yield containers
        #
        # index 0 = Data
        # index 1 = SM signal
        # index 2 = SM backgrounds
        # ========================================================

        theYields = [
            0.0,
            0.0,
            0.0
        ]

        theYieldsE2 = [
            0.0,
            0.0,
            0.0
        ]

        # --------------------------------------------------------
        # Per-process SM yields
        # --------------------------------------------------------

        theYieldsProcess = [
            0.0 for _ in range(nCat)
        ]

        theYieldsProcessUnc2 = [
            0.0 for _ in range(nCat)
        ]

        # ========================================================
        # Number of bins
        # ========================================================

        numberOfBins = (
            referenceHistogram.GetNbinsX()
        )

        # ========================================================
        # Loop over bins
        # ========================================================

        for nb in range(
            1,
            numberOfBins + 1
        ):

            streamYield = ""

            mcYield = 0.0

            processesWithEvents = []

            for i in range(nCat):

                binContent = (
                    histoSel[i].GetBinContent(nb)
                )

                binError = (
                    histoSel[i].GetBinError(nb)
                )

                # =================================================
                # Store per-process yield regardless of whether it
                # is SM or EFT, useful for diagnostics.
                # =================================================

                theYieldsProcess[i] += (
                    binContent
                )

                theYieldsProcessUnc2[i] += (
                    binError * binError
                )

                # =================================================
                # Data
                # =================================================

                if i == plotCategory("kPlotData"):

                    theYields[0] += (
                        binContent
                    )

                    theYieldsE2[0] += (
                        binError * binError
                    )

                # =================================================
                # EFT / BSM
                #
                # Do not include in nominal prediction.
                # =================================================

                elif i in nonSMCategories:

                    continue

                # =================================================
                # SM signal
                # =================================================

                elif (
                    i == signalDict0[nh]
                    or
                    i == signalDict1[nh]
                ):

                    theYields[1] += (
                        binContent
                    )

                    theYieldsE2[1] += (
                        binError * binError
                    )

                    mcYield += (
                        binContent
                    )

                # =================================================
                # SM background
                # =================================================

                else:

                    theYields[2] += (
                        binContent
                    )

                    theYieldsE2[2] += (
                        binError * binError
                    )

                    mcYield += (
                        binContent
                    )

                # =================================================
                # Print ONLY Data + nominal SM processes
                # =================================================

                if (
                    i not in nonSMCategories
                    and
                    (
                        histoSel[i].GetSumOfWeights() > 0
                        or
                        i == plotCategory("kPlotData")
                    )
                ):

                    if showUnc == 0:

                        streamYield += (
                            " {0:7.1f}".format(
                                binContent
                            )
                        )

                    else:

                        streamYield += (
                            " {0:7.1f} +/- {1:5.1f}".format(
                                binContent,
                                binError
                            )
                        )

                    processesWithEvents.append(i)

            # =====================================================
            # Print bin
            # =====================================================

            streamYield = (
                "({0:2d}) {1:7.1f}".format(
                    nb,
                    mcYield
                )
                + streamYield
            )

            if nb == 1:

                streamProcess = (
                    "         "
                )

                for pr in processesWithEvents:

                    streamProcess += (
                        " {0:7d}".format(pr)
                    )

                print(streamProcess)

            print(streamYield)

        # ========================================================
        # Per-process uncertainties
        # ========================================================

        theYieldsProcessUnc = [
            math.sqrt(x)
            for x in theYieldsProcessUnc2
        ]

        # ========================================================
        # Total line
        #
        # Print ONLY Data + nominal SM processes.
        # ========================================================

        streamYield = ""

        for i in range(nCat):

            if i in nonSMCategories:
                continue

            if (
                histoSel[i].GetSumOfWeights() > 0
                or
                i == plotCategory("kPlotData")
            ):

                if showUnc == 0:

                    streamYield += (
                        " {0:7.1f}".format(
                            theYieldsProcess[i]
                        )
                    )

                else:

                    streamYield += (
                        " {0:7.1f} +/- {1:5.1f}".format(
                            theYieldsProcess[i],
                            theYieldsProcessUnc[i]
                        )
                    )

        # ========================================================
        # Total Data/Signal/Background uncertainties
        # ========================================================

        theYieldsE = [
            math.sqrt(x)
            for x in theYieldsE2
        ]

        totalPrediction = (
            theYields[1]
            +
            theYields[2]
        )

        streamYield = (
            "(xx) {0:7.1f}".format(
                totalPrediction
            )
            + streamYield
        )

        print(streamYield)

        # ========================================================
        # Summary
        # ========================================================

        print("")

        print(
            "DA: {0:7.1f} +/- {1:5.1f} / "
            "SM SIG: {2:7.1f} +/- {3:5.1f} / "
            "SM BG: {4:7.1f} +/- {5:5.1f}".format(
                theYields[0],
                theYieldsE[0],
                theYields[1],
                theYieldsE[1],
                theYields[2],
                theYieldsE[2]
            )
        )

        print(
            "TOTAL SM PREDICTION: "
            "{0:.3f}".format(
                totalPrediction
            )
        )

        # ========================================================
        # S/B
        # ========================================================

        if theYields[2] != 0.0:

            SB = (
                theYields[1]
                /
                theYields[2]
            )

        else:

            SB = float("nan")

        # ========================================================
        # Data / SM prediction
        # ========================================================

        if totalPrediction != 0.0:

            DataVsPred = (
                theYields[0]
                /
                totalPrediction
            )

        else:

            DataVsPred = float("nan")

        # ========================================================
        # Prediction uncertainty
        #
        # Combine SM signal and SM background statistical
        # uncertainties in quadrature.
        # ========================================================

        predictionUncertainty = math.sqrt(
            theYieldsE[1] ** 2
            +
            theYieldsE[2] ** 2
        )

        # ========================================================
        # Data/SM uncertainty
        # ========================================================

        if (
            theYields[0] != 0.0
            and
            totalPrediction != 0.0
        ):

            DataVsPredE = (
                DataVsPred
                *
                math.sqrt(
                    (
                        theYieldsE[0]
                        /
                        theYields[0]
                    ) ** 2
                    +
                    (
                        predictionUncertainty
                        /
                        totalPrediction
                    ) ** 2
                )
            )

        else:

            DataVsPredE = float("nan")

        print(
            "S/B(SM): {0:.3f} / "
            "DataVsSM: {1:.3f} +/- {2:.3f}".format(
                SB,
                DataVsPred,
                DataVsPredE
            )
        )

        print("")
        print(
            "NOTE: categories {}-{} are excluded "
            "from the nominal SM prediction.".format(
                firstNonSMCategory,
                nCat - 1
            )
        )

        print("")
