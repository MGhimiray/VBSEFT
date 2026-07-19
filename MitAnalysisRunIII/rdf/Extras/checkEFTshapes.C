#include <TFile.h>
#include <TH1.h>
#include <TCanvas.h>
#include <TLegend.h>
#include <TStyle.h>
#include <TSystem.h>
#include <TString.h>
#include <TLatex.h>
#include <iostream>
#include <map>

struct VarInfo {
    TString name;
    TString xTitle;

    bool useXRange;
    double xMin;
    double xMax;

    bool useYRange;
    double yMin;
    double yMax;
};

VarInfo getVariableInfo(int plotNumber)
{
    std::map<int, VarInfo> varMap;

    // -------------------------------------------------
    // Define here what each number means
    // -------------------------------------------------

    varMap[99] = {
        "mjj",
        "m_{jj} [GeV]"
    };

    varMap[115] = {
        "MT",
        "m_{T} [GeV]"
    };

    varMap[24] = {
       "detajj",
       "#Delta #eta_{jj}"
    };

    // -------------------------------------------------
    // If number is not listed above
    // -------------------------------------------------
    if (varMap.find(plotNumber) == varMap.end()) {
        std::cerr << "Warning: plot number " << plotNumber
                  << " not found in variable map. Using generic name." << std::endl;

        return {
            Form("var%d", plotNumber),
            Form("Variable %d", plotNumber),
            false, 0, 0,
            true, -3, 30
        };
    }

    return varMap[plotNumber];
}

void checkEFTshapes(TString opName = "T2", double cValue = 2.0, double coefficient = 1.0, int plotNumber = 99, int intHistoNumber = 38, int quadHistoNumber = 39)
{
    // -------------------------------------------------
    // Base directory
    // -------------------------------------------------
    TString baseDir = "/mnt/home/mghimiray/VBSStudies/Outputs_EFT/OriginalTT/1013/0000/merge2";

    TString filename = Form("%s/fillhisto_sswwAnalysis1013_2027_%d.root",
                            baseDir.Data(), plotNumber);

    std::cout << "Reading file: " << filename << std::endl;
    std::cout << "Operator    : " << opName << std::endl;
    std::cout << "c value     : " << cValue << std::endl;
    std::cout << "Coefficient : " << coefficient << std::endl;
    std::cout << "Plot number : " << plotNumber << std::endl;

    VarInfo var = getVariableInfo(plotNumber);

    TFile *file = TFile::Open(filename, "READ");

    if (!file || file->IsZombie()) {
        std::cerr << "Error: cannot open file: " << filename << std::endl;
        return;
    }

    // -------------------------------------------------
    // Histogram names
    // -------------------------------------------------
    TH1 *hsm   = (TH1*)file->Get("histo6");
    TH1 *hint  = (TH1*)file->Get(Form("histo%d", intHistoNumber));
    TH1 *hquad = (TH1*)file->Get(Form("histo%d", quadHistoNumber));

    if (!hsm || !hint || !hquad) {
        std::cerr << "Error: one or more histograms not found." << std::endl;
        file->ls();
        file->Close();
        return;
    }

    hsm->SetDirectory(0);
    hint->SetDirectory(0);
    hquad->SetDirectory(0);

    file->Close();

    // -------------------------------------------------
    // Scale EFT shapes
    // -------------------------------------------------
    // Interference scales as c
    // Quadratic scales as c^2
    double coeff = coefficient / cValue;
    hint->Scale(1.0 / cValue);
    hquad->Scale(1.0 / (cValue * cValue));

    TH1 *hsum = (TH1*)hsm->Clone("hsum");
    hsum->SetDirectory(0);
    hsum->Add(hint);
    hsum->Add(hquad);

    // -------------------------------------------------
    // Style
    // -------------------------------------------------
    gStyle->SetOptStat(0);

    hsm->SetLineColor(kBlack);
    hsm->SetLineWidth(2);

    hint->SetLineColor(kRed);
    hint->SetLineWidth(2);

    hquad->SetLineColor(kBlue);
    hquad->SetLineWidth(2);

    hsum->SetLineColor(kGreen + 2);
    hsum->SetLineWidth(3);
    hsum->SetLineStyle(2);

    hsm->SetTitle(Form(" "));

    hsm->GetXaxis()->SetTitle(var.xTitle);
    hsm->GetYaxis()->SetTitle("Events");

    // -------------------------------------------------
    // Axis ranges
    // -------------------------------------------------
    if (var.useXRange) {
        hsm->GetXaxis()->SetRangeUser(var.xMin, var.xMax);
    }
    
    hsm->SetMinimum(hint->GetMinimum()*1.2); // Set a small minimum to better see differences
    hsm->SetMaximum(hsum->GetMaximum() * 1.5); // Add some headroom

    TCanvas *c = new TCanvas("c", "EFT Shapes", 800, 700);

    hsm->Draw("HIST");
    hint->Draw("HIST SAME");
    hquad->Draw("HIST SAME");
    hsum->Draw("HIST SAME");

    // -------------------------------------------------
    // Horizontal line at y = 0
    // -------------------------------------------------
    TLine *zeroLine = new TLine(
        hsm->GetXaxis()->GetXmin(), 0.0,
        hsm->GetXaxis()->GetXmax(), 0.0
    );
    zeroLine->SetLineStyle(2);   // dotted
    zeroLine->SetLineWidth(2);
    zeroLine->SetLineColor(kGray+2);
    zeroLine->Draw("SAME");

    // Do not use log scale because interference can be negative
    // c->SetLogy();

    // -------------------------------------------------
    // Labels on the upper-left side
    // -------------------------------------------------
    TLatex latex;
    latex.SetNDC();
    latex.SetTextFont(42);
    latex.SetTextAlign(13);
    
    // Work-in-progress label
    latex.SetTextSize(0.045);
    latex.DrawLatex(0.15, 0.88, "#bf{CMS}");

    latex.SetTextSize(0.03);
    latex.DrawLatex(0.15, 0.83, "#it{Work in progress}");
    
    // Wilson-coefficient value
    latex.SetTextSize(0.035);
    latex.DrawLatex(
        0.15,
        0.78,
        Form("f_{%s} = %.1f TeV^{-4}", opName.Data(), coeff)
    );


    TLegend *leg = new TLegend(0.60, 0.70, 0.88, 0.88);
    leg->AddEntry(hsm,   "SM", "l");
    leg->AddEntry(hint,  "Interference", "l");
    leg->AddEntry(hquad, "Quadratic", "l");
    leg->AddEntry(hsum,  "Interference+Quadratic", "l");
    leg->Draw();

    // -------------------------------------------------
    // Save plots
    // -------------------------------------------------
    gSystem->mkdir("plots", kTRUE);

    TString outname = Form("plots/%s_%s_%d_scaledC%.2f",
                           var.name.Data(),
                           opName.Data(),
                           plotNumber,
                           coeff);

    c->SaveAs(outname + ".png");
    c->SaveAs(outname + ".pdf");

    std::cout << "Saved: " << outname << ".png" << std::endl;
    std::cout << "Saved: " << outname << ".pdf" << std::endl;
}