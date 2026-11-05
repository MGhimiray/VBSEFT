#include <TFile.h>
#include <TH1.h>
#include <TCanvas.h>
#include <TPad.h>
#include <TLegend.h>
#include <TLine.h>
#include <TString.h>

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <memory>

void checkMETVariation(
    TString inputDir,
    TString anaSel = "sswwAnalysis1010",
    int year = 20240,
    int fidAna = 0,
    int category = 6)
{
    // Index mapping from your makeEFTDatacards macro.
    // Unclustered MET: endTheory(113) + nuis(55) = 168.
    // Input filename index: region offset + 1 + 168.
    const bool isWZ = anaSel.BeginsWith("wzAnalysis");
    const int regionOffset = (isWZ ? 300 : 0) + fidAna * 200;

    const TString fileSuffix = isWZ ? "" : "_mva";
    const TString histName =
        Form("histo%s%d", isWZ ? "" : "MVA", category);

    const TString nominalPath = Form(
        "%s/fillhisto_%s_%d_%d%s.root",
        inputDir.Data(), anaSel.Data(), year,
        regionOffset, fileSuffix.Data());

    const TString variedPath = Form(
        "%s/fillhisto_%s_%d_%d%s.root",
        inputDir.Data(), anaSel.Data(), year,
        regionOffset + 169, fileSuffix.Data());

    std::cout << "\nNominal: " << nominalPath
              << "\nMET input: " << variedPath
              << "\nHistogram: " << histName << "\n";

    std::unique_ptr<TFile> fNom(TFile::Open(nominalPath));
    std::unique_ptr<TFile> fVar(TFile::Open(variedPath));

    if (!fNom || fNom->IsZombie() ||
        !fVar || fVar->IsZombie()) {
        std::cerr << "ERROR: could not open input files.\n";
        return;
    }

    TH1 *sourceNom = nullptr, *sourceVar = nullptr;
    fNom->GetObject(histName.Data(), sourceNom);
    fVar->GetObject(histName.Data(), sourceVar);

    if (!sourceNom || !sourceVar) {
        std::cerr << "ERROR: histogram missing.\n";
        return;
    }

    const int nBins = sourceNom->GetNbinsX();

    if (sourceVar->GetNbinsX() != nBins) {
        std::cerr << "ERROR: different numbers of bins.\n";
        return;
    }

    for (int i = 1; i <= nBins + 1; ++i) {
        if (sourceNom->GetXaxis()->GetBinLowEdge(i) !=
            sourceVar->GetXaxis()->GetBinLowEdge(i)) {
            std::cerr << "ERROR: different bin edges.\n";
            return;
        }
    }

    static int serial = 0;
    ++serial;

    auto clone = [&](TH1 *source, const char *label) {
        TH1 *h = static_cast<TH1*>(
            source->Clone(Form("%s_%d", label, serial)));
        h->SetDirectory(nullptr);
        h->SetStats(false);
        return h;
    };

    TH1 *hNom  = clone(sourceNom, "met_nominal");
    TH1 *hRaw  = clone(sourceVar, "met_raw");
    TH1 *hUp   = clone(sourceNom, "met_processed_up");
    TH1 *hDown = clone(sourceNom, "met_processed_down");

    TH1 *rRaw  = clone(sourceNom, "met_ratio_raw");
    TH1 *rUp   = clone(sourceNom, "met_ratio_up");
    TH1 *rDown = clone(sourceNom, "met_ratio_down");

    rRaw->Reset();
    rUp->Reset();
    rDown->Reset();

    int cappedBins = 0;
    int fallbackBins = 0;
    int undefinedBins = 0;

    std::cout << std::fixed << std::setprecision(4)
              << "\nBin   [low, high]       Nominal       Raw"
              << "       Raw/Nom     Up/Nom    Down/Nom   Note\n";

    double ratioMin = 0.8;
    double ratioMax = 1.2;

    for (int i = 1; i <= nBins; ++i) {
        const double nom = hNom->GetBinContent(i);
        const double raw = hRaw->GetBinContent(i);

        if (!std::isfinite(nom) || !std::isfinite(raw)) {
            std::cerr << "ERROR: non-finite content in bin "
                      << i << ".\n";
            return;
        }

        double ratio = 1.0;
        TString note = "";

        // Reproduce your setSymmetricShapeBin content treatment.
        if (nom <= 0.0) {
            ++undefinedBins;
            note = "ratio undefined";
        }
        else if (raw <= 0.0) {
            ++fallbackBins;
            note = "replaced by nominal";
        }
        else {
            const double rawRatio = raw / nom;
            ratio = std::max(0.85, std::min(1.15, rawRatio));

            if (rawRatio < 0.85 || rawRatio > 1.15) {
                ++cappedBins;
                note = "CAPPED";
            }
        }

        hUp->SetBinContent(i, nom * ratio);
        hDown->SetBinContent(i, nom / ratio);

        std::cout << std::setw(3) << i << "  ["
                  << hNom->GetXaxis()->GetBinLowEdge(i) << ", "
                  << hNom->GetXaxis()->GetBinUpEdge(i) << "]  "
                  << std::setw(11) << nom << " "
                  << std::setw(11) << raw << " ";

        if (nom > 0.0) {
            const double rawRatio = raw / nom;

            rRaw->SetBinContent(i, rawRatio);
            rUp->SetBinContent(i, ratio);
            rDown->SetBinContent(i, 1.0 / ratio);

            ratioMin = std::min(
                ratioMin, std::min(rawRatio, std::min(ratio, 1.0/ratio)));
            ratioMax = std::max(
                ratioMax, std::max(rawRatio, std::max(ratio, 1.0/ratio)));

            std::cout << std::setw(11) << rawRatio << " "
                      << std::setw(10) << ratio << " "
                      << std::setw(10) << 1.0/ratio;
        }
        else {
            // NaN prevents undefined ratios being presented as zero.
            const double nan = std::nan("");
            rRaw->SetBinContent(i, nan);
            rUp->SetBinContent(i, nan);
            rDown->SetBinContent(i, nan);
            std::cout << "        N/A        N/A        N/A";
        }

        std::cout << "   " << note << "\n";
    }

    const double nominalYield = hNom->Integral();

    auto printYield = [&](const char *label, TH1 *h) {
        std::cout << std::setw(20) << label
                  << ": " << h->Integral();

        if (nominalYield > 0.0)
            std::cout << "   change = "
                      << 100.0 * (h->Integral()/nominalYield - 1.0)
                      << "%";

        std::cout << "\n";
    };

    std::cout << "\nVisible-bin yields (excluding under/overflow):\n";
    printYield("Nominal", hNom);
    printYield("Raw MET input", hRaw);
    printYield("Processed Up", hUp);
    printYield("Processed Down", hDown);

    std::cout << "\nCapped bins: " << cappedBins
              << "\nFallback bins: " << fallbackBins
              << "\nUndefined-ratio bins: " << undefinedBins
              << "\n\n";

    // Raw ratios are shown without ratio error bars:
    // nominal and varied templates contain correlated MC events.
    auto style = [](TH1 *h, int colour, int lineStyle) {
        h->SetLineColor(colour);
        h->SetLineStyle(lineStyle);
        h->SetLineWidth(2);
    };

    style(hNom,  kBlack, 1);
    style(hRaw,  kRed+1, 1);
    style(hUp,   kBlue+1, 2);
    style(hDown, kGreen+2, 3);

    style(rRaw,  kRed+1, 1);
    style(rUp,   kBlue+1, 2);
    style(rDown, kGreen+2, 3);

    TCanvas *canvas = new TCanvas(
        Form("checkMET_%d", serial), "MET variation check", 1000, 850);

    TPad *top = new TPad(
        Form("met_top_%d", serial), "", 0, 0.32, 1, 1);
    TPad *bottom = new TPad(
        Form("met_bottom_%d", serial), "", 0, 0, 1, 0.32);

    top->SetBottomMargin(0.025);
    bottom->SetTopMargin(0.035);
    bottom->SetBottomMargin(0.30);

    top->Draw();
    bottom->Draw();

    top->cd();

    hNom->SetTitle(Form(
        "%s, year %d, region %d, category %d",
        anaSel.Data(), year, fidAna, category));
    hNom->GetYaxis()->SetTitle("Events / bin");
    hNom->GetXaxis()->SetLabelSize(0);
    hNom->GetXaxis()->SetTitle("");

    double ymax = std::max(
        std::max(hNom->GetMaximum(), hRaw->GetMaximum()),
        std::max(hUp->GetMaximum(), hDown->GetMaximum()));

    double ymin = std::min(
        std::min(hNom->GetMinimum(), hRaw->GetMinimum()),
        std::min(hUp->GetMinimum(), hDown->GetMinimum()));

    hNom->SetMaximum(ymax > 0 ? 1.4*ymax : 1);
    hNom->SetMinimum(ymin < 0 ? 1.2*ymin : 0);

    hNom->Draw("HIST");
    hRaw->Draw("HIST SAME");
    hUp->Draw("HIST SAME");
    hDown->Draw("HIST SAME");

    TLegend *legend = new TLegend(0.53, 0.65, 0.89, 0.88);
    legend->SetBorderSize(0);
    legend->AddEntry(hNom, "Nominal", "l");
    legend->AddEntry(hRaw, "Original MET input", "l");
    legend->AddEntry(hUp, "After treatment: Up", "l");
    legend->AddEntry(hDown, "After treatment: Down", "l");
    legend->Draw();

    bottom->cd();

    rRaw->SetTitle("");
    rRaw->GetYaxis()->SetTitle("Variation / nominal");
    rRaw->GetXaxis()->SetTitle(
        sourceNom->GetXaxis()->GetTitle()[0]
        ? sourceNom->GetXaxis()->GetTitle()
        : "Analysis bin / observable");

    const double padding = 0.12 * (ratioMax - ratioMin);
    rRaw->SetMinimum(ratioMin - padding);
    rRaw->SetMaximum(ratioMax + padding);
    rRaw->GetYaxis()->SetNdivisions(505);
    rRaw->GetYaxis()->SetTitleSize(0.085);
    rRaw->GetYaxis()->SetTitleOffset(0.52);
    rRaw->GetYaxis()->SetLabelSize(0.075);
    rRaw->GetXaxis()->SetTitleSize(0.10);
    rRaw->GetXaxis()->SetLabelSize(0.085);

    rRaw->Draw("HIST");
    rUp->Draw("HIST SAME");
    rDown->Draw("HIST SAME");

    TLine *unity = new TLine(
        hNom->GetXaxis()->GetXmin(), 1.0,
        hNom->GetXaxis()->GetXmax(), 1.0);
    unity->SetLineStyle(2);
    unity->Draw();

    canvas->cd();
    canvas->Update();
}
