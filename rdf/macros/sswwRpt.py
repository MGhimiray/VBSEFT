#!/usr/bin/env python3

import ROOT
import os
import sys
import getopt

ROOT.ROOT.EnableImplicitMT(1)

# ============================================================
# Use exactly the same analysis machinery as sswwAnalysis.py
# ============================================================

from utilsCategory import plotCategory

from utilsAna import (
    getMClist,
    SwitchSample,
    groupFiles
)

from utilsSelection import selectionGenLepJet

# Import the SAME nominal selection used by the real analysis.
#
# This gives us:
#   fake leptons
#   selected jets
#   M01Def
#   vbs_rpt
#   vbs_mjj
#   vbs_detajj
#   vbs_zepvv
#   etc.
#
from sswwAnalysis import (
    selectionLL,
    altMass,
    metCut
)


# ============================================================
# SETTINGS
# ============================================================

skimType = "2l"

# Same grouping as your normal sswwAnalysis.py
group = 15


# ============================================================
# 2D histogram binning
#
# X = M01
# Y = RpT
#
# These are ONLY display bins.
# They are NOT your datacard flattened bins.
# ============================================================

M01_NBINS = 100
M01_MIN   = 0.0
M01_MAX   = 4000.0

RPT_NBINS = 100
RPT_MIN   = -3.0
RPT_MAX   = 1.0


# ============================================================
# OUTPUT
# ============================================================

OUTPUT_BASE = (
    "/mnt/home/mghimiray/VBSStudies/"
    "Outputs_EFT/M01_RpT_2D"
)


# ============================================================
# EFT categories
# ============================================================

def isEFTCategory(category):

    eftCategories = [
        plotCategory("kPlotEFTM0Int"),
        plotCategory("kPlotEFTM0Quad"),

        plotCategory("kPlotEFTM1Int"),
        plotCategory("kPlotEFTM1Quad"),

        plotCategory("kPlotEFTM7Int"),
        plotCategory("kPlotEFTM7Quad"),

        plotCategory("kPlotEFTS0Int"),
        plotCategory("kPlotEFTS0Quad"),

        plotCategory("kPlotEFTT0Int"),
        plotCategory("kPlotEFTT0Quad"),

        plotCategory("kPlotEFTT1Int"),
        plotCategory("kPlotEFTT1Quad"),

        plotCategory("kPlotEFTT2Int"),
        plotCategory("kPlotEFTT2Quad"),
    ]

    return category in eftCategories


# ============================================================
# ANALYSIS
# ============================================================

def make2DHistogram(
    df,
    sampleNOW,
    year,
    PDType,
    whichJob,
    cutOff
):

    print("")
    print("========================================================")
    print(" M01 vs RpT 2D study")
    print("========================================================")
    print("Sample      :", sampleNOW)
    print("Year        :", year)
    print("PDType      :", PDType)
    print("Job         :", whichJob)
    print("Cutoff      :", cutOff)
    print("========================================================")


    # ========================================================
    # 1. Run the SAME basic ssWW selection
    #
    # This already creates:
    #
    #   M01Def
    #   vbs_rpt
    #   vbs_mjj
    #   vbs_detajj
    #   vbs_zepvv
    #   nvbs_jets
    #   nbtag_goodbtag_Jet_bjet
    #   etc.
    # ========================================================

    dftag = selectionLL(
        df,
        year,
        PDType,
        "false",
        sampleNOW
    )


    # ========================================================
    # Identify category
    # ========================================================

    category = SwitchSample(
        sampleNOW,
        skimType
    )[2]

    isEFT = isEFTCategory(category)

    print("Category    :", category)
    print("Is EFT      :", isEFT)


    # ========================================================
    # 2. EFT samples:
    #
    # Your normal sswwAnalysis imposes nTight == 2 for EFT.
    # Keep exactly the same behaviour here.
    # ========================================================

    if isEFT:

        dftag = dftag.Filter(
            "nTight == 2",
            "Two tight leptons for EFT"
        )


    # ========================================================
    # 3. Generator information
    #
    # Needed only for the EFT mWW cutoff.
    # ========================================================

    if isEFT:

        dftag = selectionGenLepJet(
            dftag,
            20,
            30,
            5.0
        )

        dftag = dftag.Define(
            "invariant_mass",
            """
            Get_mww(
                good_GenDressedLepton_pt,
                good_GenDressedLepton_eta,
                good_GenDressedLepton_phi,
                good_GenDressedLepton_mass,
                good_GenDressedLepton_pz,
                GenMET_pt,
                GenMET_phi
            )
            """
        )


        # ----------------------------------------------------
        # EFT unitarity cutoff
        # ----------------------------------------------------

        cutOffVal = int(cutOff)

        if cutOffVal > 0:

            dftag = dftag.Filter(
                "invariant_mass < {0}".format(cutOffVal),
                "mww < {0} GeV".format(cutOffVal)
            )


    # ========================================================
    # 4. NOMINAL SSWW VBS SIGNAL REGION
    #
    # This is the same nominal region you use in sswwAnalysis.
    #
    #   mll > 20
    #   pTl1 > 25
    #   pTl2 > 20
    #   Z veto for ee
    #   b veto
    #   >= 2 VBS jets
    #   mjj > 500
    #   deta_jj > 2.5
    #   zepvv < 1
    #   MET > 30
    # ========================================================

    signalRegion = """
        mllDef > 20
        &&
        ptl1Def > 25
        &&
        ptl2Def > 20
        &&
        (
            DiLepton_flavor != 2
            ||
            abs(mllDef - 86.1876) > 20
        )
        &&
        nbtag_goodbtag_Jet_bjet == 0
        &&
        nvbs_jets >= 2
        &&
        vbs_mjj > 500
        &&
        vbs_detajj > 2.5
        &&
        vbs_zepvv < 1.0
        &&
        PuppiMET_ptDef > {0}
    """.format(metCut)


    dfSR = dftag.Filter(
        signalRegion,
        "Nominal ssWW VBS signal region"
    )


    # ========================================================
    # 5. Protect against pathological values
    # ========================================================

    dfSR = dfSR.Filter(
        """
        std::isfinite(M01Def)
        &&
        std::isfinite(vbs_rpt)
        &&
        M01Def >= 0.0
        """,
        "Valid M01 and RpT"
    )


    # ========================================================
    # 6. Make 2D histogram
    #
    # IMPORTANT:
    #
    # This is deliberately UNWEIGHTED.
    #
    # Each entry = one selected MC event.
    #
    # This is what you asked for first:
    # inspect the actual event population/correlation between
    # M01 and RpT without datacard flattening or systematics.
    # ========================================================

    hist2D = dfSR.Histo2D(
        (
            "h2_M01_vs_RpT",
            ";M_{01} [GeV];R_{pT};Events",
            M01_NBINS,
            M01_MIN,
            M01_MAX,
            RPT_NBINS,
            RPT_MIN,
            RPT_MAX
        ),
        "M01Def",
        "vbs_rpt"
    )


    # Also count selected events
    nSelected = dfSR.Count()


    # Run both actions together
    ROOT.RDF.RunGraphs([
        hist2D,
        nSelected
    ])


    nEvents = nSelected.GetValue()
    h2 = hist2D.GetValue()


    print("")
    print("---------------------------------------------")
    print("Selected events :", nEvents)
    print("Histogram entries:", h2.GetEntries())
    print("---------------------------------------------")


    # ========================================================
    # 7. Output directory
    # ========================================================

    histDir = os.path.join(
        OUTPUT_BASE,
        str(cutOff),
        "histo"
    )

    plotDir = os.path.join(
        OUTPUT_BASE,
        str(cutOff),
        "plots"
    )

    os.makedirs(
        histDir,
        exist_ok=True
    )

    os.makedirs(
        plotDir,
        exist_ok=True
    )


    # ========================================================
    # 8. ROOT output file
    #
    # Every file deliberately contains the SAME histogram name:
    #
    #   h2_M01_vs_RpT
    #
    # Therefore later:
    #
    #   hadd ...
    #
    # automatically sums the same histogram across jobs.
    # ========================================================

    rootFileName = os.path.join(
        histDir,
        "M01_RpT_sample{0}_year{1}_job{2}.root".format(
            sampleNOW,
            year,
            whichJob
        )
    )


    outputFile = ROOT.TFile(
        rootFileName,
        "RECREATE"
    )


    h2.Write()


    # --------------------------------------------------------
    # Save useful metadata
    # --------------------------------------------------------

    ROOT.TNamed(
        "sample",
        str(sampleNOW)
    ).Write()

    ROOT.TNamed(
        "year",
        str(year)
    ).Write()

    ROOT.TNamed(
        "cutoff",
        str(cutOff)
    ).Write()

    ROOT.TNamed(
        "PDType",
        str(PDType)
    ).Write()


    outputFile.Close()


    # ========================================================
    # 9. Draw one plot for this job
    # ========================================================

    ROOT.gStyle.SetOptStat(0)

    canvas = ROOT.TCanvas(
        "canvas",
        "canvas",
        900,
        800
    )

    canvas.SetLeftMargin(0.12)
    canvas.SetRightMargin(0.16)
    canvas.SetBottomMargin(0.12)


    h2.SetTitle("")

    h2.GetXaxis().SetTitle(
        "M_{01} [GeV]"
    )

    h2.GetYaxis().SetTitle(
        "R_{pT}"
    )

    h2.GetZaxis().SetTitle(
        "Events"
    )

    h2.GetXaxis().SetTitleSize(0.045)
    h2.GetYaxis().SetTitleSize(0.045)
    h2.GetZaxis().SetTitleSize(0.045)

    h2.GetXaxis().SetLabelSize(0.038)
    h2.GetYaxis().SetLabelSize(0.038)
    h2.GetZaxis().SetLabelSize(0.038)


    h2.Draw("COLZ")


    # --------------------------------------------------------
    # Labels
    # --------------------------------------------------------

    latex = ROOT.TLatex()

    latex.SetNDC()

    latex.SetTextFont(62)
    latex.SetTextSize(0.045)

    latex.DrawLatex(
        0.13,
        0.94,
        "CMS"
    )


    latex.SetTextFont(42)
    latex.SetTextSize(0.035)

    latex.DrawLatex(
        0.23,
        0.94,
        "Simulation"
    )


    latex.SetTextSize(0.030)

    latex.DrawLatex(
        0.58,
        0.94,
        "sample {0}, {1}".format(
            sampleNOW,
            year
        )
    )


    latex.DrawLatex(
        0.58,
        0.90,
        "m_{WW} < {0} GeV".format(
            cutOff
        )
    )


    # ========================================================
    # 10. Save PNG
    # ========================================================

    plotName = os.path.join(
        plotDir,
        "M01_RpT_sample{0}_year{1}_job{2}.png".format(
            sampleNOW,
            year,
            whichJob
        )
    )


    canvas.SaveAs(
        plotName
    )


    print("")
    print("ROOT output:")
    print(rootFileName)

    print("")
    print("PNG output:")
    print(plotName)

    print("")
    print("Done.")
    print("========================================================")


# ============================================================
# READ MC SAMPLE
# ============================================================

def readMCSample(
    sampleNOW,
    year,
    whichJob,
    cutOff
):

    # ========================================================
    # Get the files EXACTLY as your normal analysis does
    # ========================================================

    files = getMClist(
        sampleNOW,
        skimType
    )


    print("")
    print("Sample:", sampleNOW)
    print("Total files:", len(files))


    if len(files) == 0:

        print(
            "ERROR: no files found for sample {0}".format(
                sampleNOW
            )
        )

        return


    # ========================================================
    # Same 15-way grouping used by your normal workflow
    # ========================================================

    if whichJob != -1:

        groupedFiles = groupFiles(
            files,
            group
        )


        if whichJob < 0 or whichJob >= len(groupedFiles):

            print(
                "ERROR: whichJob={0}, but only {1} groups exist".format(
                    whichJob,
                    len(groupedFiles)
                )
            )

            return


        files = groupedFiles[
            whichJob
        ]


        if len(files) == 0:

            print(
                "No files in job/group: {0} / {1}".format(
                    whichJob,
                    group
                )
            )

            return


    print(
        "Used files:",
        len(files)
    )


    # ========================================================
    # Build RDataFrame
    # ========================================================

    df = ROOT.RDataFrame(
        "Events",
        files
    )


    # ========================================================
    # PDType exactly as in the normal analysis
    # ========================================================

    sampleInfo = SwitchSample(
        sampleNOW,
        skimType
    )


    print("")
    print("SwitchSample:")
    print("  path     :", sampleInfo[0])
    print("  xsec     :", sampleInfo[1])
    print("  category :", sampleInfo[2])


    PDType = os.path.basename(
        sampleInfo[0]
    ).split("+")[0]


    # ========================================================
    # Make histogram
    # ========================================================

    make2DHistogram(
        df,
        sampleNOW,
        year,
        PDType,
        whichJob,
        cutOff
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    year = 20220
    process = -1
    whichJob = -1
    cutOff = "1000"


    valid = [
        "year=",
        "process=",
        "whichJob=",
        "cutOff=",
        "help"
    ]


    usage = (
        "Usage:\n"
        "python3 ssww_M01_RpT_2D.py "
        "--year=<year> "
        "--process=<process> "
        "--whichJob=<job> "
        "--cutOff=<cutoff>\n"
    )


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


        elif opt == "--year":

            year = int(arg)


        elif opt == "--process":

            process = int(arg)


        elif opt == "--whichJob":

            whichJob = int(arg)


        elif opt == "--cutOff":

            cutOff = str(arg).zfill(4)


    # ========================================================
    # Sanity checks
    # ========================================================

    if process < 0:

        print(
            "ERROR: process must be specified."
        )

        print(usage)

        sys.exit(1)


    print("")
    print("========================================================")
    print("Running:")
    print(" year      =", year)
    print(" process   =", process)
    print(" whichJob  =", whichJob)
    print(" cutOff    =", cutOff)
    print("========================================================")


    readMCSample(
        process,
        year,
        whichJob,
        cutOff
    )
