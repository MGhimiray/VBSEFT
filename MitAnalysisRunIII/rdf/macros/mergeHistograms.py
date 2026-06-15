import ROOT
from ROOT import TFile, TH1D, TH2D
import os, sys, getopt, glob
from utilsCategory import plotCategory
ROOT.PyConfig.DisableRootLogon = True

if __name__ == "__main__":
    path = "/mnt/home/mghimiray/VBSStudies/Outputs_EFT/Fakerate/output/fillhisto_fakeAnalysis1001"
    year = 20240
    output = "/mnt/home/mghimiray/VBSStudies/Outputs_EFT/Fakerate/output/merge1"

    valid = ['path=', "year=", 'output=', 'help']
    usage  =  "Usage: ana.py --path=<{0}>\n".format(path)
    usage +=  "              --year=<{0}>\n".format(year)
    usage +=  "              --output=<{0}>".format(output)
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", valid)
    except getopt.GetoptError as ex:
        print(usage)
        print(str(ex))
        sys.exit(1)

    for opt, arg in opts:
        if opt == "--help":
            print(usage)
            sys.exit(1)
        if opt == "--path":
            path = str(arg)
        if opt == "--year":
            year = int(arg)
        if opt == "--output":
            output = str(arg)

    paths_to_watch = path + "_sample*_year" + str(year) + "_job*.root"
    print("paths_to_watch: {0}".format(paths_to_watch))
    inputDataFolders = glob.glob(paths_to_watch)
    print("Total found files: {0}".format(len(inputDataFolders)))
    if len(inputDataFolders) == 0:
        sys.exit(1)

    nCat, nHisto, nhistoNonPrompt, nhistoWS = plotCategory("kPlotCategories"), 1600, 50, 20

    myfile = [0 for x in range(len(inputDataFolders))]
    for nf in range(len(inputDataFolders)):
        myfile[nf] = TFile(inputDataFolders[nf])
        if not myfile[nf] or myfile[nf].IsZombie():
            print("Problem opening file:", inputDataFolders[nf])

    if not os.path.exists(output):
        os.makedirs(output)

    for nh in range(nHisto):

        # 1D
        histo = [0 for x in range(nCat)]
        for nc in range(nCat):
            histo[nc] = None
            for nf in range(len(inputDataFolders)):
                htmp = myfile[nf].Get("histo_{0}_{1}".format(nh, nc))
                if not htmp:
                    continue
                if histo[nc] is None:
                    histo[nc] = htmp.Clone("histo_tmp_{0}_{1}".format(nh, nc))
                    histo[nc].SetDirectory(0)
                else:
                    histo[nc].Add(htmp)

        if histo[0]:
            outputFileName = "{0}/{1}_{2}_{3}.root".format(output, os.path.basename(path), year, nh)
            print("Making 1D {0}".format(outputFileName))
            outputFile = TFile(outputFileName, "RECREATE")
            outputFile.cd()
            for nc in range(nCat):
                if not histo[nc]:
                    continue
                histo[nc].SetNameTitle("histo{0}".format(nc), "histo{0}".format(nc))
                histo[nc].SetBinContent(
                    histo[nc].GetNbinsX(),
                    histo[nc].GetBinContent(histo[nc].GetNbinsX()) + histo[nc].GetBinContent(histo[nc].GetNbinsX() + 1)
                )
                histo[nc].SetBinError(
                    histo[nc].GetNbinsX(),
                    pow(
                        pow(histo[nc].GetBinError(histo[nc].GetNbinsX()), 2) +
                        pow(histo[nc].GetBinError(histo[nc].GetNbinsX() + 1), 2),
                        0.5
                    )
                )
                histo[nc].SetBinContent(histo[nc].GetNbinsX() + 1, 0.0)
                histo[nc].SetBinError(histo[nc].GetNbinsX() + 1, 0.0)
                histo[nc].Write()
            outputFile.Close()

        # 1DMVA
        histoMVA = [0 for x in range(nCat)]
        for nc in range(nCat):
            histoMVA[nc] = None
            for nf in range(len(inputDataFolders)):
                htmp = myfile[nf].Get("histoMVA_{0}_{1}".format(nh, nc))
                if not htmp:
                    continue
                if histoMVA[nc] is None:
                    histoMVA[nc] = htmp.Clone("histoMVA_tmp_{0}_{1}".format(nh, nc))
                    histoMVA[nc].SetDirectory(0)
                else:
                    histoMVA[nc].Add(htmp)

        if histoMVA[0]:
            outputFileName = "{0}/{1}_{2}_{3}_mva.root".format(output, os.path.basename(path), year, nh)
            print("Making 1D {0}".format(outputFileName))
            outputFile = TFile(outputFileName, "RECREATE")
            outputFile.cd()
            for nc in range(nCat):
                if not histoMVA[nc]:
                    continue
                histoMVA[nc].SetNameTitle("histoMVA{0}".format(nc), "histoMVA{0}".format(nc))
                histoMVA[nc].SetBinContent(
                    histoMVA[nc].GetNbinsX(),
                    histoMVA[nc].GetBinContent(histoMVA[nc].GetNbinsX()) + histoMVA[nc].GetBinContent(histoMVA[nc].GetNbinsX() + 1)
                )
                histoMVA[nc].SetBinError(
                    histoMVA[nc].GetNbinsX(),
                    pow(
                        pow(histoMVA[nc].GetBinError(histoMVA[nc].GetNbinsX()), 2) +
                        pow(histoMVA[nc].GetBinError(histoMVA[nc].GetNbinsX() + 1), 2),
                        0.5
                    )
                )
                histoMVA[nc].SetBinContent(histoMVA[nc].GetNbinsX() + 1, 0.0)
                histoMVA[nc].SetBinError(histoMVA[nc].GetNbinsX() + 1, 0.0)
                histoMVA[nc].Write()
            outputFile.Close()

        # 2D
        histo2d = [0 for x in range(nCat)]
        for nc in range(nCat):
            histo2d[nc] = None
            for nf in range(len(inputDataFolders)):
                htmp = myfile[nf].Get("histo2d_{0}_{1}".format(nh, nc))
                if not htmp:
                    continue
                if histo2d[nc] is None:
                    histo2d[nc] = htmp.Clone("histo2d_tmp_{0}_{1}".format(nh, nc))
                    histo2d[nc].SetDirectory(0)
                else:
                    histo2d[nc].Add(htmp)

        if histo2d[0]:
            outputFileName = "{0}/{1}_{2}_{3}_2d.root".format(output, os.path.basename(path), year, nh)
            print("Making 2D {0}".format(outputFileName))
            outputFile = TFile(outputFileName, "RECREATE")
            outputFile.cd()
            for nc in range(nCat):
                if not histo2d[nc]:
                    continue
                histo2d[nc].SetNameTitle("histo2d{0}".format(nc), "histo2d{0}".format(nc))

                for i in range(histo2d[nc].GetNbinsX()):
                    histo2d[nc].SetBinContent(
                        i + 1, histo2d[nc].GetNbinsY(),
                        histo2d[nc].GetBinContent(i + 1, histo2d[nc].GetNbinsY()) +
                        histo2d[nc].GetBinContent(i + 1, histo2d[nc].GetNbinsY() + 1)
                    )
                    histo2d[nc].SetBinError(
                        i + 1, histo2d[nc].GetNbinsY(),
                        pow(
                            pow(histo2d[nc].GetBinError(i + 1, histo2d[nc].GetNbinsY()), 2) +
                            pow(histo2d[nc].GetBinError(i + 1, histo2d[nc].GetNbinsY() + 1), 2),
                            0.5
                        )
                    )
                    histo2d[nc].SetBinContent(i + 1, histo2d[nc].GetNbinsY() + 1, 0.0)
                    histo2d[nc].SetBinError(i + 1, histo2d[nc].GetNbinsY() + 1, 0.0)

                for i in range(histo2d[nc].GetNbinsY()):
                    histo2d[nc].SetBinContent(
                        histo2d[nc].GetNbinsX(), i + 1,
                        histo2d[nc].GetBinContent(histo2d[nc].GetNbinsX(), i + 1) +
                        histo2d[nc].GetBinContent(histo2d[nc].GetNbinsX() + 1, i + 1)
                    )
                    histo2d[nc].SetBinError(
                        histo2d[nc].GetNbinsX(), i + 1,
                        pow(
                            pow(histo2d[nc].GetBinError(histo2d[nc].GetNbinsX(), i + 1), 2) +
                            pow(histo2d[nc].GetBinError(histo2d[nc].GetNbinsX() + 1, i + 1), 2),
                            0.5
                        )
                    )
                    histo2d[nc].SetBinContent(histo2d[nc].GetNbinsX() + 1, i + 1, 0.0)
                    histo2d[nc].SetBinError(histo2d[nc].GetNbinsX() + 1, i + 1, 0.0)

                histo2d[nc].Write()
            outputFile.Close()

    for nf in range(len(inputDataFolders)):
        print("Closing file... {0}".format(nf))
        myfile[nf].Close()

    print("DONE")