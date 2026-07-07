import ROOT
from ROOT import TFile
import os, sys, getopt

sys.path.append('/mnt/home/mghimiray/VBSStudies/VBSStudies03/MitAnalysisRunIII/rdf/macrosTT')
from utilsCategory import plotCategory


def get_available_histo_indices(root_file):
    indices = []
    for key in root_file.GetListOfKeys():
        name = key.GetName()
        if name.startswith("histo"):
            suffix = name[5:]
            if suffix.isdigit():
                indices.append(int(suffix))
    return sorted(indices)


if __name__ == "__main__":
    path = "fillhisto_sswwAnalysis1014"
    year = 20220
    output = "/mnt/home/mghimiray/VBSStudies/Outputs_EFT/OriginalTT/1014/0000/merge1"
    showUnc = 0

    valid = ['path=', 'year=', 'output=', 'unc=', 'help']
    usage  = f"Usage: computeYields.py --path=<{path}>\n"
    usage += f"                       --year=<{year}>\n"
    usage += f"                       --output=<{output}>\n"
    usage += f"                       --unc=<{showUnc}>"

    try:
        opts, args = getopt.getopt(sys.argv[1:], "", valid)
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
            output = str(arg).rstrip("/")
        elif opt == "--unc":
            showUnc = int(arg)

    histo = []
    signalDict0 = []
    signalDict1 = []

    if 'sswwAnalysis' in path:
        histo.append(18)
        signalDict0.append(plotCategory("kPlotEWKSSWW"))
        signalDict1.append(plotCategory("kPlotEWKSSWW"))

        histo.append(19)
        signalDict0.append(plotCategory("kPlotEWKSSWW"))
        signalDict1.append(plotCategory("kPlotEWKSSWW"))

    elif 'zzAna' in path:
        histo.append(8)
        signalDict0.append(plotCategory("kPlotZZ"))
        signalDict1.append(plotCategory("kPlotZZ"))

        histo.append(16)
        signalDict0.append(plotCategory("kPlotZZ"))
        signalDict1.append(plotCategory("kPlotZZ"))

    elif 'wzAna' in path:
        histo.append(11)
        signalDict0.append(plotCategory("kPlotWZ"))
        signalDict1.append(plotCategory("kPlotWZ"))

        histo.append(12)
        signalDict0.append(plotCategory("kPlotWZ"))
        signalDict1.append(plotCategory("kPlotWZ"))

        histo.append(17)
        signalDict0.append(plotCategory("kPlotWZ"))
        signalDict1.append(plotCategory("kPlotWZ"))

        histo.append(18)
        signalDict0.append(plotCategory("kPlotWZ"))
        signalDict1.append(plotCategory("kPlotWZ"))

        histo.append(27)
        signalDict0.append(plotCategory("kPlotEWKWZ"))
        signalDict1.append(plotCategory("kPlotEWKWZ"))

        histo.append(28)
        signalDict0.append(plotCategory("kPlotEWKWZ"))
        signalDict1.append(plotCategory("kPlotEWKWZ"))

    elif 'zmetAna' in path:
        histo.append(34)
        signalDict0.append(plotCategory("kPlotZZ"))
        signalDict1.append(plotCategory("kPlotZZ"))

        histo.append(35)
        signalDict0.append(plotCategory("kPlotZZ"))
        signalDict1.append(plotCategory("kPlotZZ"))

    elif 'wwAna' in path:
        histo.append(42)
        signalDict0.append(plotCategory("kPlotNonPrompt"))
        signalDict1.append(plotCategory("kPlotNonPrompt"))

        histo.append(71)
        signalDict0.append(plotCategory("kPlotNonPrompt"))
        signalDict1.append(plotCategory("kPlotNonPrompt"))

        histo.append(72)
        signalDict0.append(plotCategory("kPlotNonPrompt"))
        signalDict1.append(plotCategory("kPlotNonPrompt"))

        histo.append(43)
        signalDict0.append(plotCategory("kPlotqqWW"))
        signalDict1.append(plotCategory("kPlotggWW"))

        histo.append(44)
        signalDict0.append(plotCategory("kPlotDY"))
        signalDict1.append(plotCategory("kPlotDY"))

        histo.append(45)
        signalDict0.append(plotCategory("kPlotTT"))
        signalDict1.append(plotCategory("kPlotTW"))

        histo.append(57)
        signalDict0.append(plotCategory("kPlotHiggs"))
        signalDict1.append(plotCategory("kPlotHiggs"))

    elif 'zAna' in path:
        histo.append(27)
        signalDict0.append(plotCategory("kPlotDY"))
        signalDict1.append(plotCategory("kPlotDY"))

        histo.append(28)
        signalDict0.append(plotCategory("kPlotDY"))
        signalDict1.append(plotCategory("kPlotDY"))

        histo.append(29)
        signalDict0.append(plotCategory("kPlotDY"))
        signalDict1.append(plotCategory("kPlotDY"))

    else:
        print(f"ERROR: unknown analysis path '{path}'")
        sys.exit(1)

    nCat = plotCategory("kPlotCategories")
    dataCat = plotCategory("kPlotData")

    print(f"Using output directory: {output}")
    print(f"Using path basename   : {os.path.basename(path)}")
    print(f"Using year            : {year}")
    print(f"Expected categories   : {nCat}")

    for nh in range(len(histo)):
        print(f"**********HISTO: {histo[nh]} **********")

        filename = f"{output}/{os.path.basename(path)}_{year}_{histo[nh]}.root"
        print(f"Opening file: {filename}")

        inputFile = TFile.Open(filename, "READ")
        if not inputFile or inputFile.IsZombie():
            print(f"ERROR: cannot open file {filename}")
            continue

        available = get_available_histo_indices(inputFile)
        if len(available) == 0:
            print(f"ERROR: no histo* objects found in {filename}")
            inputFile.Close()
            continue

        print(f"Available histograms: histo{available[0]} ... histo{available[-1]}  (total {len(available)})")

        histoSel = [None for _ in range(nCat)]

        for i in available:
            if i >= nCat:
                continue
            h = inputFile.Get(f"histo{i}")
            if not h:
                print(f"WARNING: histo{i} listed but could not be read from {filename}")
                continue
            histoSel[i] = h.Clone(f"histo{i}_clone")
            histoSel[i].SetDirectory(0)

        inputFile.Close()

        refHist = None
        for h in histoSel:
            if h is not None:
                refHist = h
                break

        if refHist is None:
            print(f"ERROR: no usable histograms loaded from {filename}")
            continue

        theYields  = [0.0, 0.0, 0.0]   # data, signal, background
        theYieldsE2 = [0.0, 0.0, 0.0]  # store squared uncertainties

        theYieldsProcess = [0.0 for _ in range(nCat)]
        theYieldsProcessUnc2 = [0.0 for _ in range(nCat)]

        for nb in range(1, refHist.GetNbinsX() + 1):
            streamYield = ""
            mcYield = 0.0
            processesWithEvents = []

            for i in range(nCat):
                if histoSel[i] is None:
                    continue

                bc = histoSel[i].GetBinContent(nb)
                be = histoSel[i].GetBinError(nb)

                if histoSel[i].GetSumOfWeights() > 0 or i == dataCat:
                    if showUnc == 0:
                        streamYield += f" {bc:7.1f}"
                    else:
                        streamYield += f" {bc:7.1f} +/- {be:5.1f}"
                    processesWithEvents.append(i)

                theYieldsProcess[i] += bc
                theYieldsProcessUnc2[i] += be * be

                if i == dataCat:
                    theYields[0] += bc
                    theYieldsE2[0] += be * be
                elif i == signalDict0[nh] or i == signalDict1[nh]:
                    theYields[1] += bc
                    theYieldsE2[1] += be * be
                    mcYield += bc
                else:
                    theYields[2] += bc
                    theYieldsE2[2] += be * be
                    mcYield += bc

            streamYield = f"({nb:2d}) {mcYield:7.1f}" + streamYield

            if nb == 1 and len(processesWithEvents) > 0:
                streamProcess = "         "
                for pr in processesWithEvents:
                    streamProcess += f" {pr:7d}"
                print(streamProcess)

            print(streamYield)

        streamYield = ""
        for i in range(nCat):
            if histoSel[i] is None:
                continue
            if histoSel[i].GetSumOfWeights() > 0 or i == dataCat:
                procUnc = theYieldsProcessUnc2[i] ** 0.5
                if showUnc == 0:
                    streamYield += f" {theYieldsProcess[i]:7.1f}"
                else:
                    streamYield += f" {theYieldsProcess[i]:7.1f} +/- {procUnc:5.1f}"

        theYieldsE = [x ** 0.5 for x in theYieldsE2]

        streamYield = f"(xx) {theYields[1] + theYields[2]:7.1f}" + streamYield
        print(streamYield)

        print(
            "DA: {0:7.1f} +/- {1:4.1f} / SIG: {2:7.1f} +/- {3:4.1f} / BG: {4:7.1f} +/- {5:4.1f}".format(
                theYields[0], theYieldsE[0],
                theYields[1], theYieldsE[1],
                theYields[2], theYieldsE[2]
            )
        )

        SB = theYields[1] / theYields[2] if theYields[2] != 0 else 0.0

        pred = theYields[1] + theYields[2]
        if pred != 0 and theYields[0] != 0:
            DataVsPred = theYields[0] / pred
            DataVsPredE = DataVsPred * (
                (theYieldsE[0] / theYields[0]) ** 2 +
                (theYieldsE[1] / pred) ** 2 +
                (theYieldsE[2] / pred) ** 2
            ) ** 0.5
        else:
            DataVsPred = 0.0
            DataVsPredE = 0.0

        print(f"SB: {SB:.2f} / DataVsPred: {DataVsPred:.2f} +/- {DataVsPredE:.2f}")
