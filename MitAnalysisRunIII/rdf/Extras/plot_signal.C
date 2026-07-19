// plot_signal_growth.C
// Usage:
// root -l -b -q 'plot_signal_growth.C("input.root")'

#include "TFile.h"
#include "TH1.h"
#include "TCanvas.h"
#include "TPad.h"
#include "TLegend.h"
#include "TStyle.h"
#include "TLine.h"
#include "TString.h"
#include "iostream"

void plot_signal(
    const char* filename    = "/mnt/home/mghimiray/VBSStudies/Outputs_EFT/OriginalTT/1016/0000/datacards/output_sswwAnalysis1016_S0_20240_bin0.root",    const char* outname  = "signal_growth1016.png",
    bool logY = false,
    int rebin = 1
)
{
    gStyle->SetOptStat(0);
    gStyle->SetTitleFontSize(0.04);

    TFile* f = TFile::Open(filename, "READ");
    if (!f || f->IsZombie()) {
        std::cerr << "Error: cannot open file " << filename << std::endl;
        return;
    }

    TH1* histo_sm       = (TH1*) f->Get("histo_sm");
    TH1* histo_int      = (TH1*) f->Get("histo_quad_cS0");
    TH1* histo_lin_quad = (TH1*) f->Get("histo_sm_lin_quad_cS0");
//    TH1* histo_QCDSSWW  = (TH1*) f->Get("histo_QCDSSWW");
//    TH1* histo_EWKSSWW  = (TH1*) f->Get("histo_EWKSSWW");
//    TH1* histo_EWKWZ    = (TH1*) f->Get("histo_EWKWZ ");
//    TH1* histo_WZ       = (TH1*) f->Get("histo_WZ");
//    TH1* histo_ZZ       = (TH1*) f->Get("histo_ZZ");
//    TH1* histo_NonPrompt = (TH1*) f->Get("histo_NonPrompt");
//    TH1* histo_VVV      = (TH1*) f->Get("histo_VVV");
//    TH1* histo_TVX      = (TH1*) f->Get("histo_TVX");
//    TH1* histo_VG       = (TH1*) f->Get("histo_VG");
//    TH1* histo_WSM      = (TH1*) f->Get("histo_WSM");


    if (!histo_sm || !histo_int || !histo_lin_quad) {
        std::cerr << "Error: missing one or more histograms." << std::endl;
        std::cerr << "Need: histo_sm, histo_int, histo_lin_quad" << std::endl;
        return;
    }

    histo_sm       = (TH1*) histo_sm->Clone("h_sm_clone");
    histo_int      = (TH1*) histo_int->Clone("h_int_clone");
    histo_lin_quad = (TH1*) histo_lin_quad->Clone("h_lin_quad_clone");

    histo_sm->SetDirectory(0);
    histo_int->SetDirectory(0);
    histo_lin_quad->SetDirectory(0);

    if (rebin > 1) {
        histo_sm->Rebin(rebin);
        histo_int->Rebin(rebin);
        histo_lin_quad->Rebin(rebin);
    }

    // Styling
    histo_sm->SetLineColor(kBlack);
    histo_sm->SetLineWidth(3);
    histo_sm->SetTitle(" ");

    histo_int->SetLineColor(kBlue + 1);
    histo_int->SetLineWidth(3);
    histo_int->SetLineStyle(2);

    histo_lin_quad->SetLineColor(kRed + 1);
    histo_lin_quad->SetLineWidth(3);

    histo_sm->SetMarkerColor(kBlack);
    histo_int->SetMarkerColor(kBlue + 1);
    histo_lin_quad->SetMarkerColor(kRed + 1);

    histo_sm->SetMarkerStyle(20);
    histo_int->SetMarkerStyle(24);
    histo_lin_quad->SetMarkerStyle(21);

    // Canvas with two pads
    TCanvas* c = new TCanvas("c", "SM vs INT vs LIN+QUAD", 800, 800);

    TPad* pad1 = new TPad("pad1", "Upper pad", 0.0, 0.30, 1.0, 1.0);
    TPad* pad2 = new TPad("pad2", "Ratio pad", 0.0, 0.00, 1.0, 0.30);

    pad1->SetBottomMargin(0.02);
    pad1->SetLeftMargin(0.12);
    pad1->SetRightMargin(0.05);

    pad2->SetTopMargin(0.04);
    pad2->SetBottomMargin(0.35);
    pad2->SetLeftMargin(0.12);
    pad2->SetRightMargin(0.05);

    pad1->Draw();
    pad2->Draw();

    // -----------------------
    // Upper panel
    // -----------------------
    pad1->cd();
    if (logY) pad1->SetLogy();

    double maxY = std::max({
        histo_sm->GetMaximum(),
        histo_int->GetMaximum(),
        histo_lin_quad->GetMaximum()
    });

    histo_sm->SetMaximum(logY ? maxY * 20.0 : maxY * 1.5);
    histo_sm->SetMinimum(logY ? 0.1 : 0.0);

    histo_sm->GetYaxis()->SetTitle("Events");
    histo_sm->GetYaxis()->SetTitleSize(0.055);
    histo_sm->GetYaxis()->SetLabelSize(0.045);
    histo_sm->GetYaxis()->SetTitleOffset(1.05);

    histo_sm->GetXaxis()->SetLabelSize(0.0);

    histo_sm->Draw("HIST E");
    histo_int->Draw("HIST E SAME");
    histo_lin_quad->Draw("HIST E SAME");

    TLegend* leg = new TLegend(0.60, 0.68, 0.90, 0.88);
    leg->SetBorderSize(0);
    leg->SetFillStyle(0);
    leg->SetTextSize(0.04);
    leg->AddEntry(histo_sm, "SM", "l");
    leg->AddEntry(histo_int, "Quadratic", "l");
    leg->AddEntry(histo_lin_quad, "SM + INT + QUAD", "l");
    
    leg->Draw();

    // -----------------------
    // Lower ratio panel
    // -----------------------
    pad2->cd();

    TH1* ratio = (TH1*) histo_lin_quad->Clone("ratio_signal_growth");

    // Recommended ratio for signal growth:
    ratio->Divide(histo_sm);  // (SM + INT + QUAD) / SM

    // If you instead want SM / (SM + INT + QUAD), use this:
    // ratio = (TH1*) histo_sm->Clone("ratio_signal_growth");
    // ratio->Divide(histo_lin_quad);

    ratio->SetLineColor(kRed + 1);
    ratio->SetMarkerColor(kRed + 1);
    ratio->SetMarkerStyle(20);
    ratio->SetLineWidth(2);

    ratio->GetYaxis()->SetTitle("#frac{SM+INT+QUAD}{SM}");
    ratio->GetXaxis()->SetTitle(histo_sm->GetXaxis()->GetTitle());

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

    TLine* line = new TLine(
        ratio->GetXaxis()->GetXmin(), 1.0,
        ratio->GetXaxis()->GetXmax(), 1.0
    );
    line->SetLineColor(kBlack);
    line->SetLineStyle(2);
    line->SetLineWidth(2);
    line->Draw("SAME");

    c->SaveAs(outname);

    std::cout << "Saved plot: " << outname << std::endl;
}
