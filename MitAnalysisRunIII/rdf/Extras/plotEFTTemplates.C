#include <TFile.h>
#include <TH1.h>
#include <TCanvas.h>
#include <TLegend.h>
#include <TString.h>
#include <TStyle.h>
#include <TMath.h>
#include <iostream>
#include <algorithm>

void plotEFTTemplates(TString inputFileName,
                      TString op = "cM0",
                      bool normalize = false,
                      bool logy = false)
{
    gStyle->SetOptStat(0);

    TFile *f = TFile::Open(inputFileName, "READ");

    if (!f || f->IsZombie()) {
        std::cerr << "ERROR: cannot open file " << inputFileName << std::endl;
        return;
    }

    TH1 *h_sm   = (TH1*) f->Get("histo_sm");
    TH1 *h_slq  = (TH1*) f->Get(Form("histo_sm_lin_quad_%s", op.Data()));
    TH1 *h_quad = (TH1*) f->Get(Form("histo_quad_%s", op.Data()));

    if (!h_sm) {
        std::cerr << "ERROR: missing histo_sm" << std::endl;
        return;
    }

    if (!h_slq) {
        std::cerr << "ERROR: missing histo_sm_lin_quad_" << op << std::endl;
        return;
    }

    if (!h_quad) {
        std::cerr << "ERROR: missing histo_quad_" << op << std::endl;
        return;
    }

    h_sm   = (TH1*) h_sm->Clone("sm_clone");
    h_slq  = (TH1*) h_slq->Clone("slq_clone");
    h_quad = (TH1*) h_quad->Clone("quad_clone");

    h_sm->SetDirectory(0);
    h_slq->SetDirectory(0);
    h_quad->SetDirectory(0);

    f->Close();

    std::cout << "\n===== EFT TEMPLATE CHECK =====" << std::endl;
    std::cout << "File      = " << inputFileName << std::endl;
    std::cout << "Operator  = " << op << std::endl;
    std::cout << "SM        = " << h_sm->Integral() << std::endl;
    std::cout << "SM+L+Q    = " << h_slq->Integral() << std::endl;
    std::cout << "Quad      = " << h_quad->Integral() << std::endl;
    std::cout << "Linear    = " << h_slq->Integral() - h_sm->Integral() - h_quad->Integral() << std::endl;
    std::cout << "==============================\n" << std::endl;

    if (normalize) {
        if (h_sm->Integral() != 0)   h_sm->Scale(1.0 / h_sm->Integral());
        if (h_slq->Integral() != 0)  h_slq->Scale(1.0 / h_slq->Integral());
        if (h_quad->Integral() != 0) h_quad->Scale(1.0 / h_quad->Integral());
    }

    h_sm->SetLineColor(kBlack);
    h_sm->SetLineWidth(3);

    h_slq->SetLineColor(kRed);
    h_slq->SetLineWidth(3);

    h_quad->SetLineColor(kBlue);
    h_quad->SetLineWidth(3);

    h_sm->SetTitle("");
    h_sm->GetXaxis()->SetTitle("Bin");
    h_sm->GetYaxis()->SetTitle(normalize ? "Normalized yield" : "Events");

    double ymax = std::max({
        h_sm->GetMaximum(),
        h_slq->GetMaximum(),
        h_quad->GetMaximum()
    });

    double ymin = std::min({
        h_sm->GetMinimum(),
        h_slq->GetMinimum(),
        h_quad->GetMinimum()
    });

    if (logy) {
        h_sm->SetMinimum(1e-6);
        h_sm->SetMaximum(ymax * 10.0);
    } else {
        h_sm->SetMinimum(std::min(0.0, ymin * 1.2));
        h_sm->SetMaximum(ymax * 1.35);
    }

    TCanvas *c = new TCanvas("c", "c", 900, 800);
    c->SetTicks();

    if (logy) c->SetLogy();

    h_sm->Draw("hist");
    h_slq->Draw("hist same");
    h_quad->Draw("hist same");

    TLegend *leg = new TLegend(0.55, 0.70, 0.88, 0.88);
    leg->SetBorderSize(0);
    leg->SetFillStyle(0);
    leg->AddEntry(h_sm, "SM", "l");
    leg->AddEntry(h_slq, Form("SM + Lin + Quad %s", op.Data()), "l");
    leg->AddEntry(h_quad, Form("Quad %s", op.Data()), "l");
    leg->Draw();

    TString tag = normalize ? "normalized" : "raw";
    TString outname = Form("eft_templates_%s_%s.pdf", op.Data(), tag.Data());

    c->SaveAs(outname);

    TString outpng = Form("eft_templates_%s_%s.png", op.Data(), tag.Data());
    c->SaveAs(outpng);

    std::cout << "Saved: " << outname << std::endl;
    std::cout << "Saved: " << outpng << std::endl;
}
