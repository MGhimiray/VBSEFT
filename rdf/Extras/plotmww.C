#include <iostream>

#include "TFile.h"
#include "TH1.h"
#include "TCanvas.h"
#include "TLegend.h"
#include "TStyle.h"
#include "TAxis.h"


void plotmww(

    const char* filename =
    "/mnt/home/mghimiray/VBSStudies/Outputs_EFT/fakerrate/1022/0000/merge2/fillhisto_sswwAnalysis1022_2027_126.root",

    const char* outname = "T2_mWW.png"

)

{

    gStyle->SetOptStat(0);


    TFile *f = TFile::Open(filename,"READ");

    if(!f || f->IsZombie()){
        std::cout<<"Cannot open file"<<std::endl;
        return;
    }


    TH1* h_SM =
        (TH1*)f->Get("histo6");

    TH1* h_Int =
        (TH1*)f->Get("histo38");

    TH1* h_Quad =
        (TH1*)f->Get("histo39");


    if(!h_SM || !h_Int || !h_Quad){

        std::cout<<"Missing histogram"<<std::endl;

        if(!h_SM)
            std::cout<<"Missing histo_6"<<std::endl;

        if(!h_Int)
            std::cout<<"Missing histo_38"<<std::endl;

        if(!h_Quad)
            std::cout<<"Missing histo_39"<<std::endl;

        return;
    }



    TH1* sm = (TH1*)h_SM->Clone("SM");

    TH1* sm_int = (TH1*)h_SM->Clone("SM_plus_T2_Int");
    sm_int->Add(h_Int);

    TH1* sm_quad = (TH1*)h_SM->Clone("SM_plus_T2_Quad");
    sm_quad->Add(h_Quad);



    TCanvas *c = new TCanvas("c","c",800,700);

    c->SetLogy();

    sm->SetLineColor(kBlack);
    sm_int->SetLineColor(kBlue);
    sm_quad->SetLineColor(kRed);


    sm->SetLineWidth(2);
    sm_int->SetLineWidth(2);
    sm_quad->SetLineWidth(2);


    sm->GetXaxis()->SetTitle("m_{WW} [GeV]");
    sm->GetYaxis()->SetTitle("Events");

    sm->SetTitle("");
 //   sm->SetMinimum(-3);


    sm->Draw("hist");
    sm_int->Draw("hist same");
    sm_quad->Draw("hist same");



    TLegend *leg =
        new TLegend(0.55,0.70,0.88,0.88);


    leg->AddEntry(sm,
                  "SM",
                  "l");


    leg->AddEntry(sm_int,
                  "SM + Int",
                  "l");


    leg->AddEntry(sm_quad,
                  "SM + Quad",
                  "l");


    leg->Draw();



    c->SaveAs(outname);
    c->SaveAs("plotmww.pdf");
    c->SaveAs("plotmww.png");



    TFile *fout =
        new TFile("plotmww.root","RECREATE");


    sm->Write();
    sm_int->Write();
    sm_quad->Write();


    fout->Close();

    f->Close();

}