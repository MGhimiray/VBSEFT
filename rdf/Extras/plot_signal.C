// plot_signal.C
//
// Usage example:
//
// root -l -b -q \
// 'plot_signal.C("input.root","output.png","S0",1016,109.0,false,false,1)'

#include "TFile.h"
#include "TH1.h"
#include "TCanvas.h"
#include "TPad.h"
#include "TLegend.h"
#include "TStyle.h"
#include "TLine.h"
#include "TLatex.h"
#include "TString.h"
#include "TSystem.h"

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>

void plot_signal(
    const char* filename =
        "/mnt/home/mghimiray/VBSStudies/Outputs_EFT/fakerrate/"
        "1023/0000/datacards/"
        "output_sswwAnalysis1023_S0_20240_bin0.root",

    const char* outname = "signal_growth.png",

    const char* operatorName = "S0",

    int variable = 1023,

    double luminosity = 280.0,

    bool drawRatio = false,

    bool logY = false,

    int rebin = 1
)
{
    gStyle->SetOptStat(0);
    gStyle->SetTitleFontSize(0.04);

    // =========================================================
    // Open input ROOT file
    // =========================================================

    TFile* f = TFile::Open(filename, "READ");

    if (!f || f->IsZombie()) {

        std::cerr
            << "Error: cannot open file: "
            << filename
            << std::endl;

        return;
    }

    // =========================================================
    // Histogram names
    // =========================================================

    TString quadraticName =
        Form("histo_quad_c%s", operatorName);

    TString fullName =
        Form("histo_sm_lin_quad_c%s", operatorName);

    std::cout << "Reading:" << std::endl;
    std::cout << "  histo_sm" << std::endl;
    std::cout << "  " << quadraticName << std::endl;
    std::cout << "  " << fullName << std::endl;

    // =========================================================
    // Read histograms
    // =========================================================

    TH1* histo_sm_original =
        dynamic_cast<TH1*>(
            f->Get("histo_sm")
        );

    TH1* histo_quad_original =
        dynamic_cast<TH1*>(
            f->Get(quadraticName.Data())
        );

    TH1* histo_lin_quad_original =
        dynamic_cast<TH1*>(
            f->Get(fullName.Data())
        );

    if (
        !histo_sm_original ||
        !histo_quad_original ||
        !histo_lin_quad_original
    ) {
        std::cerr
            << "Error: missing histogram(s)."
            << std::endl;

        if (!histo_sm_original) {
            std::cerr
                << "Missing: histo_sm"
                << std::endl;
        }

        if (!histo_quad_original) {
            std::cerr
                << "Missing: "
                << quadraticName
                << std::endl;
        }

        if (!histo_lin_quad_original) {
            std::cerr
                << "Missing: "
                << fullName
                << std::endl;
        }

        f->Close();
        delete f;

        return;
    }

    // =========================================================
    // Clone histograms
    // =========================================================

    TH1* histo_sm =
        dynamic_cast<TH1*>(
            histo_sm_original->Clone("h_sm_clone")
        );

    TH1* histo_quad =
        dynamic_cast<TH1*>(
            histo_quad_original->Clone("h_quad_clone")
        );

    TH1* histo_lin_quad =
        dynamic_cast<TH1*>(
            histo_lin_quad_original->Clone(
                "h_lin_quad_clone"
            )
        );

    histo_sm->SetDirectory(nullptr);
    histo_quad->SetDirectory(nullptr);
    histo_lin_quad->SetDirectory(nullptr);

    f->Close();
    delete f;

    // =========================================================
    // Optional rebinning
    // =========================================================

    if (rebin > 1) {

        histo_sm->Rebin(rebin);
        histo_quad->Rebin(rebin);
        histo_lin_quad->Rebin(rebin);
    }

    // =========================================================
    // Print SM content in every bin
    // =========================================================

    // Values with absolute size below this threshold are marked
    // as "VERY SMALL".
    const double smallThreshold = 1.0e-6;

    const int nBins =
        histo_sm->GetNbinsX();

    std::cout
        << "\n============================================================\n"
        << "SM BIN CONTENTS\n"
        << "============================================================\n"
        << "File      : " << filename << "\n"
        << "Variable  : " << variable << "\n"
        << "Operator  : " << operatorName << "\n"
        << "Rebin     : " << rebin << "\n"
        << "N bins    : " << nBins << "\n"
        << "Threshold : " << smallThreshold << "\n"
        << "============================================================"
        << std::endl;

    std::cout
        << std::scientific
        << std::setprecision(10);

    for (int iBin = 1; iBin <= nBins; ++iBin) {

        const double lowEdge =
            histo_sm->GetXaxis()->GetBinLowEdge(iBin);

        const double upperEdge =
            histo_sm->GetXaxis()->GetBinUpEdge(iBin);

        const double binCenter =
            histo_sm->GetXaxis()->GetBinCenter(iBin);

        const double content =
            histo_sm->GetBinContent(iBin);

        const double error =
            histo_sm->GetBinError(iBin);

        std::cout
            << "Bin "
            << std::setw(3)
            << iBin
            << "  range = ["
            << lowEdge
            << ", "
            << upperEdge
            << "]"
            << "  center = "
            << binCenter
            << "  SM = "
            << content
            << "  error = "
            << error;

        if (content == 0.0) {

            std::cout
                << "  <-- EXACTLY ZERO";
        }
        else if (std::abs(content) < smallThreshold) {

            std::cout
                << "  <-- VERY SMALL";
        }

        std::cout << std::endl;
    }

    const double underflowContent = histo_sm->GetBinContent(0);

    const double underflowError =
        histo_sm->GetBinError(0);

    const double overflowContent =
        histo_sm->GetBinContent(nBins + 1);

    const double overflowError =
        histo_sm->GetBinError(nBins + 1);

    const double regularIntegral =
        histo_sm->Integral(1, nBins);

    const double completeIntegral =
        histo_sm->Integral(0, nBins + 1);

    std::cout
        << "------------------------------------------------------------\n"
        << "Underflow : SM = "
        << underflowContent
        << "  error = "
        << underflowError
        << "\n"
        << "Overflow  : SM = "
        << overflowContent
        << "  error = "
        << overflowError
        << "\n"
        << "------------------------------------------------------------\n"
        << "Integral excluding underflow/overflow = "
        << regularIntegral
        << "\n"
        << "Integral including underflow/overflow = "
        << completeIntegral
        << "\n"
        << "============================================================\n"
        << std::endl;

    // Restore a normal output format for later terminal messages.
    std::cout
        << std::defaultfloat
        << std::setprecision(6);

    // =========================================================
    // Select x-axis title
    // =========================================================

    TString xAxisTitle =
        histo_sm->GetXaxis()->GetTitle();

    if (variable == 1010) {

        xAxisTitle = "m_{01}";
    }
    else if (variable == 1014) {

        xAxisTitle = "m_{jj} #times m_{01}";
    }
    else if (variable == 1016) {

        xAxisTitle = "R_{p_{T}}";
    }
    else if (variable == 1013) {

        xAxisTitle = "m_{jj} #times m_{T}";
    }
    else if (variable == 1022) {

        xAxisTitle = "m_{01} #times R_{p_{T}}";
    }
    else if (variable == 1023) {

        xAxisTitle = "m_{01} #times #Delta#eta_{jj}";
    }

    // Variable 1013 retains the x-axis title already stored
    // inside the ROOT histogram.

    // =========================================================
    // Histogram styling
    // =========================================================

    // SM
    histo_sm->SetLineColor(kBlack);
    histo_sm->SetLineWidth(3);
    histo_sm->SetTitle("");

    histo_sm->SetMarkerColor(kBlack);
    histo_sm->SetMarkerStyle(20);

    // Quadratic
    histo_quad->SetLineColor(kBlue + 1);
    histo_quad->SetLineWidth(3);
    histo_quad->SetLineStyle(2);

    histo_quad->SetMarkerColor(kBlue + 1);
    histo_quad->SetMarkerStyle(24);

    // SM + interference + quadratic
    histo_lin_quad->SetLineColor(kRed + 1);
    histo_lin_quad->SetLineWidth(3);

    histo_lin_quad->SetMarkerColor(kRed + 1);
    histo_lin_quad->SetMarkerStyle(21);

    // =========================================================
    // Canvas and pads
    // =========================================================

    TCanvas* c =
        new TCanvas(
            "c",
            "SM vs QUAD vs FULL",
            800,
            800
        );

    TPad* pad1 = nullptr;
    TPad* pad2 = nullptr;

    /*
       drawRatio = false:
           Only the main plot is drawn.

       drawRatio = true:
           The ratio panel is also drawn.
    */

    if (drawRatio) {

        pad1 =
            new TPad(
                "pad1",
                "Upper pad",
                0.0,
                0.30,
                1.0,
                1.0
            );

        pad2 =
            new TPad(
                "pad2",
                "Ratio pad",
                0.0,
                0.00,
                1.0,
                0.30
            );

        pad1->SetBottomMargin(0.02);
        pad1->SetTopMargin(0.10);
        pad1->SetLeftMargin(0.12);
        pad1->SetRightMargin(0.05);

        pad2->SetTopMargin(0.04);
        pad2->SetBottomMargin(0.35);
        pad2->SetLeftMargin(0.12);
        pad2->SetRightMargin(0.05);

        pad1->Draw();
        pad2->Draw();
    }
    else {

        pad1 =
            new TPad(
                "pad1",
                "Main pad",
                0.0,
                0.0,
                1.0,
                1.0
            );

        pad1->SetBottomMargin(0.13);
        pad1->SetTopMargin(0.10);
        pad1->SetLeftMargin(0.12);
        pad1->SetRightMargin(0.05);

        pad1->Draw();
    }

    // =========================================================
    // Main panel
    // =========================================================

    pad1->cd();

    if (logY) {

        pad1->SetLogy();
    }

    const double maxY =
        std::max(
            {
                histo_sm->GetMaximum(),
                histo_quad->GetMaximum(),
                histo_lin_quad->GetMaximum()
            }
        );

    if (logY) {

        histo_sm->SetMaximum(maxY * 20.0);
        histo_sm->SetMinimum(0.1);
    }
    else {

        histo_sm->SetMaximum(maxY * 1.50);
        histo_sm->SetMinimum(0.0);
    }

    // Y axis
    histo_sm->GetYaxis()->SetTitle("Events");
    histo_sm->GetYaxis()->SetTitleSize(0.055);
    histo_sm->GetYaxis()->SetLabelSize(0.045);
    histo_sm->GetYaxis()->SetTitleOffset(1.05);

    // X axis
    histo_sm->GetXaxis()->SetTitle(
        xAxisTitle.Data()
    );

    if (drawRatio) {

        // Hide main-panel x axis when ratio panel is present.
        histo_sm->GetXaxis()->SetLabelSize(0.0);
        histo_sm->GetXaxis()->SetTitleSize(0.0);
    }
    else {

        histo_sm->GetXaxis()->SetLabelSize(0.045);
        histo_sm->GetXaxis()->SetTitleSize(0.050);
        histo_sm->GetXaxis()->SetTitleOffset(1.05);
    }

    // =========================================================
    // Draw histograms
    // =========================================================

    histo_sm->Draw("HIST E");

    histo_quad->Draw(
        "HIST E SAME"
    );

    histo_lin_quad->Draw(
        "HIST E SAME"
    );

    // =========================================================
    // Legend
    // =========================================================

    TLegend* leg =
        new TLegend(
            0.58,
            0.68,
            0.90,
            0.88
        );

    leg->SetBorderSize(0);
    leg->SetFillStyle(0);
    leg->SetTextSize(0.04);

    leg->AddEntry(
        histo_sm,
        "SM",
        "l"
    );

    leg->AddEntry(
        histo_quad,
        "Quadratic",
        "l"
    );

    leg->AddEntry(
        histo_lin_quad,
        "SM + INT + QUAD",
        "l"
    );

    leg->Draw();

    // =========================================================
    // CMS and EFT information
    // =========================================================

    TLatex latex;
    latex.SetNDC();

    // CMS
    latex.SetTextAlign(13);
    latex.SetTextFont(62);
    latex.SetTextSize(0.050);

    latex.DrawLatex(
        0.16,
        0.88,
        "CMS"
    );

    // Work in progress
    latex.SetTextFont(52);
    latex.SetTextSize(0.036);

    latex.DrawLatex(
        0.16,
        0.825,
        "Work in progress"
    );

    // EFT coefficient
    latex.SetTextFont(42);
    latex.SetTextSize(0.036);

    latex.DrawLatex(
        0.16,
        0.755,
        Form(
            "f_{%s} = 10 TeV^{-4}",
            operatorName
        )
    );

    // Integrated luminosity
    latex.SetTextAlign(31);
    latex.SetTextFont(42);
    latex.SetTextSize(0.034);

    latex.DrawLatex(
        0.96,
        0.905,
        Form(
            "%.1f fb^{-1} (13.6 TeV)",
            luminosity
        )
    );

    // =========================================================
    // Optional ratio panel
    // =========================================================

    if (drawRatio && pad2) {

        pad2->cd();

        TH1* ratio =
            dynamic_cast<TH1*>(
                histo_lin_quad->Clone(
                    "ratio_signal_growth"
                )
            );

        ratio->SetDirectory(nullptr);

        // (SM + INT + QUAD) / SM
        ratio->Divide(histo_sm);

        ratio->SetLineColor(kRed + 1);
        ratio->SetMarkerColor(kRed + 1);
        ratio->SetMarkerStyle(20);
        ratio->SetLineWidth(2);

        ratio->GetYaxis()->SetTitle(
            "#frac{SM+INT+QUAD}{SM}"
        );

        ratio->GetXaxis()->SetTitle(
            xAxisTitle.Data()
        );

        ratio->GetYaxis()->SetNdivisions(505);
        ratio->GetYaxis()->SetTitleSize(0.11);
        ratio->GetYaxis()->SetLabelSize(0.09);
        ratio->GetYaxis()->SetTitleOffset(0.50);

        ratio->GetXaxis()->SetTitleSize(0.12);
        ratio->GetXaxis()->SetLabelSize(0.10);
        ratio->GetXaxis()->SetTitleOffset(1.05);

        ratio->SetMinimum(0.0);
        ratio->SetMaximum(3.0);

        ratio->Draw("E");

        TLine* line =
            new TLine(
                ratio->GetXaxis()->GetXmin(),
                1.0,
                ratio->GetXaxis()->GetXmax(),
                1.0
            );

        line->SetLineColor(kBlack);
        line->SetLineStyle(2);
        line->SetLineWidth(2);
        line->Draw("SAME");
    }

    // =========================================================
    // Save plot
    // =========================================================

    c->cd();
    c->Update();

    gSystem->mkdir(
        "plots",
        true
    );

    TString outputPath =
        Form(
            "plots/%s",
            outname
        );

    c->SaveAs(
        outputPath.Data()
    );

    std::cout
        << "Saved plot: "
        << outputPath
        << std::endl;
}
