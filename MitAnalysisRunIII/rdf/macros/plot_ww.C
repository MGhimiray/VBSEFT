#include <ROOT/RDataFrame.hxx>
#include <ROOT/RVec.hxx>
#include <TCanvas.h>
#include <TFile.h>
#include <TH1D.h>
#include <TLegend.h>
#include <TLatex.h>
#include <TROOT.h>
#include <TTree.h>
#include <TStyle.h>
#include <TSystem.h>
#include <TLine.h>

#include <algorithm>
#include <cmath>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

using Vec_f  = ROOT::VecOps::RVec<float>;
using Vec_i  = ROOT::VecOps::RVec<int>;
using Vec_uc = ROOT::VecOps::RVec<unsigned char>;

float Get_mww(const Vec_f& lepton_pt,
              const Vec_f& lepton_eta,
              const Vec_f& lepton_phi,
              const Vec_f& lepton_mass,
              const Vec_f& lepton_pz,
              const float metpT,
              const float metphi) {
  if (lepton_pt.size() != 2) return 0.0f;

  float px1 = lepton_pt[0] * std::cos(lepton_phi[0]);
  float py1 = lepton_pt[0] * std::sin(lepton_phi[0]);
  float px2 = lepton_pt[1] * std::cos(lepton_phi[1]);
  float py2 = lepton_pt[1] * std::sin(lepton_phi[1]);

  (void)px1; (void)py1; (void)px2; (void)py2; (void)metphi;

  float pztot = lepton_pz[0] + lepton_pz[1];

  float E1 = std::sqrt(lepton_pt[0]*lepton_pt[0] +
                       lepton_pz[0]*lepton_pz[0] +
                       lepton_mass[0]*lepton_mass[0]);

  float E2 = std::sqrt(lepton_pt[1]*lepton_pt[1] +
                       lepton_pz[1]*lepton_pz[1] +
                       lepton_mass[1]*lepton_mass[1]);

  float MTfirst  = E1 + E2 + metpT;
  float MTsecond = pztot;

  float mww2 = MTfirst*MTfirst - MTsecond*MTsecond;
  return sqrt(mww2);
}

float DeltaPhi(float phi1, float phi2) {
  float dphi = std::fmod(phi1 - phi2, 2.0f * static_cast<float>(M_PI));
  if (dphi >  static_cast<float>(M_PI)) dphi -= 2.0f * static_cast<float>(M_PI);
  if (dphi <= -static_cast<float>(M_PI)) dphi += 2.0f * static_cast<float>(M_PI);
  return dphi;
}

float DeltaR(float eta1, float phi1, float eta2, float phi2) {
  const float dphi = DeltaPhi(phi1, phi2);
  const float deta = eta1 - eta2;
  return std::sqrt(deta*deta + dphi*dphi);
}

Vec_i cleaningJetFromLepton(const Vec_f& jet_eta,
                            const Vec_f& jet_phi,
                            const Vec_f& lep_eta,
                            const Vec_f& lep_phi,
                            const float drcut = 0.4f) {
  Vec_i mask(jet_eta.size(), 1);
  for (size_t j = 0; j < jet_eta.size(); ++j) {
    for (size_t l = 0; l < lep_eta.size(); ++l) {
      if (DeltaR(jet_eta[j], jet_phi[j], lep_eta[l], lep_phi[l]) < drcut) {
        mask[j] = 0;
        break;
      }
    }
  }
  return mask;
}

std::vector<std::string> SplitLines(const std::string& text) {
  std::vector<std::string> out;
  std::stringstream ss(text);
  std::string line;
  while (std::getline(ss, line)) {
    if (!line.empty()) out.push_back(line);
  }
  return out;
}

std::vector<std::string> GetRootFiles(const TString& dir) {
  TString cmd = Form("find %s -type f -name '*.root' 2>/dev/null", dir.Data());
  auto files = SplitLines(gSystem->GetFromPipe(cmd.Data()).Data());
  std::sort(files.begin(), files.end());
  return files;
}

bool HasBranch(const std::string& fileName, const char* treeName, const char* branchName) {
  TFile f(fileName.c_str(), "READ");
  if (f.IsZombie()) return false;
  auto *tree = dynamic_cast<TTree*>(f.Get(treeName));
  if (!tree) return false;
  return tree->GetBranch(branchName) != nullptr;
}

double GetSumW(const std::vector<std::string>& files) {
  if (files.empty()) return 0.0;

  if (HasBranch(files[0], "Runs", "genEventSumw")) {
    ROOT::RDataFrame rdfRuns("Runs", files);
    return *rdfRuns.Sum<double>("genEventSumw");
  }

  if (HasBranch(files[0], "Events", "genWeight")) {
    ROOT::RDataFrame rdfEv("Events", files);
    return *rdfEv.Sum<double>("genWeight");
  }

  ROOT::RDataFrame rdfEv("Events", files);
  return static_cast<double>(*rdfEv.Count());
}

ROOT::RDF::RNode DefineGenObjects(ROOT::RDF::RNode df,
                                  float ptlcut = 20.f,
                                  float ptjcut = 30.f,
                                  float etajcut = 5.f) {
  auto dftag = df
    .Define("good_GenDressedLepton", Form("abs(GenDressedLepton_eta) < 2.5 && GenDressedLepton_pt > %g", ptlcut))
    .Define("good_GenDressedLepton_hasTauAnc", "GenDressedLepton_hasTauAnc[good_GenDressedLepton]")
    .Define("good_GenDressedLepton_pt", "GenDressedLepton_pt[good_GenDressedLepton]")
    .Define("good_GenDressedLepton_eta", "GenDressedLepton_eta[good_GenDressedLepton]")
    .Define("good_GenDressedLepton_phi", "GenDressedLepton_phi[good_GenDressedLepton]")
    .Define("good_GenDressedLepton_mass", "GenDressedLepton_mass[good_GenDressedLepton]")
    .Define("good_GenDressedLepton_pdgId", "GenDressedLepton_pdgId[good_GenDressedLepton]")
    .Define("good_GenDressedLepton_pz", "good_GenDressedLepton_pt * sinh(good_GenDressedLepton_eta)")
    .Define("ngood_GenDressedLeptons", "Sum(good_GenDressedLepton)*1.0f")
    .Define("GenJet_mask", "cleaningJetFromLepton(GenJet_eta, GenJet_phi, good_GenDressedLepton_eta, good_GenDressedLepton_phi)")
    .Define("good_GenJet", Form("GenJet_pt > %g && abs(GenJet_eta) < %g && GenJet_mask > 0", ptjcut, etajcut))
    .Define("ngood_GenJets", "Sum(good_GenJet)*1.0f")
    .Define("good_GenJet_pt", "GenJet_pt[good_GenJet]")
    .Define("good_GenJet_eta", "GenJet_eta[good_GenJet]")
    .Define("good_GenJet_phi", "GenJet_phi[good_GenJet]")
    .Define("good_GenJet_mass", "GenJet_mass[good_GenJet]")
    .Define("good_GenJet_hadronFlavour", "GenJet_hadronFlavour[good_GenJet]")
    .Define("good_GenJet_partonFlavour", "GenJet_partonFlavour[good_GenJet]");

  return dftag;
}

TH1D* BuildHist(const TString& label,
                const TString& sampleDir,
                double xsec_fb,
                double lumi_fb,
                int nbins,
                double xmin,
                double xmax,
                float ptlcut,
                float ptjcut,
                float etajcut) {
  auto files = GetRootFiles(sampleDir);
  if (files.empty()) {
    std::cerr << "No ROOT files found in: " << sampleDir << std::endl;
    return nullptr;
  }

  std::cout << "[" << label << "] files = " << files.size() << std::endl;
  const double sumw = GetSumW(files);
  std::cout << "[" << label << "] sumW = " << sumw << std::endl;
  if (sumw == 0.0) {
    std::cerr << "Sum of weights is zero for " << label << std::endl;
    return nullptr;
  }

  ROOT::RDataFrame df("Events", files);
  auto df1 = DefineGenObjects(df, ptlcut, ptjcut, etajcut)
    .Filter("ngood_GenDressedLeptons == 2", "exactly two dressed leptons after selection")
    .Define("invariant_mass",
            "Get_mww(good_GenDressedLepton_pt, good_GenDressedLepton_eta, "
            "good_GenDressedLepton_phi, good_GenDressedLepton_mass, "
            "good_GenDressedLepton_pz, GenMET_pt, GenMET_phi)");

  TString wexpr;
  if (HasBranch(files[0], "Events", "genWeight")) {
    wexpr = Form("(%f * %f / %f) * genWeight", lumi_fb, xsec_fb, sumw);
  } else {
    wexpr = Form("(%f * %f / %f)", lumi_fb, xsec_fb, sumw);
  }

  auto df2 = df1.Define("plotWeight", wexpr.Data());

  TString hname = "h_" + label;
  hname.ReplaceAll("+", "plus");
  hname.ReplaceAll(" ", "_");

  ROOT::RDF::TH1DModel model(hname.Data(), "", nbins, xmin, xmax);
  auto hptr = df2.Histo1D(model, "invariant_mass", "plotWeight");

  TH1D* h = static_cast<TH1D*>(hptr->Clone(hname + "_clone"));
  h->SetDirectory(nullptr);
  return h;
}

void NormalizeIfRequested(TH1D* h, bool shape_norm) {
  if (!h || !shape_norm) return;
  const double integral = h->Integral();
  if (integral != 0.0) h->Scale(1.0 / integral);
}

void StyleHist(TH1D* h, int color, const TString& ytitle) {
  if (!h) return;
  h->SetLineColor(color);
  h->SetLineWidth(3);
  h->SetMarkerStyle(0);
  h->SetStats(0);
  h->GetXaxis()->SetTitle("m_{WW} [GeV]");
  h->GetYaxis()->SetTitle(ytitle);
  h->GetXaxis()->SetTitleSize(0.045);
  h->GetYaxis()->SetTitleSize(0.045);
  h->GetXaxis()->SetLabelSize(0.04);
  h->GetYaxis()->SetLabelSize(0.04);
}

void plot_ww(TString skimType = "2l",
             bool shape_norm = false,
             TString outName = "mww_overlay_shape_2022_M0",
             TString operatorName = "M0",
             double lumi_fb = 170,
             int nbins = 40,
             double xmin = 0.0,
             double xmax = 6000.0,
             float ptlcut = 20.f,
             float ptjcut = 30.f,
             float etajcut = 5.f) {
  ROOT::EnableImplicitMT();
  gROOT->SetBatch(kTRUE);
  gStyle->SetOptStat(0);

  const TString dirT2 = "/mnt/home/mghimiray/VBSStudies/DATA/Monte_Carlo/";
  const TString dirT3 = "/mnt/home/mghimiray/VBSStudies/DATA/Monte_Carlo/Unskimmed/";

  const TString smDir   = dirT3 + "2024/SM";
  const TString intDir  = dirT2 + "2024/" + skimType + "/VBS-SSWW-" + operatorName + "-Interference_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM";
  const TString quadDir = dirT2 + "2024/" + skimType + "/VBS-SSWW-" + operatorName + "-Quadratic_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM";

  const double xsec_sm_fb   = 0.0295255 * 1000.0;
  const double xsec_quad_fb = 0.007333  * 1000.0;
  const double xsec_int_fb =  0.000297  * 1000.0;


  std::cout << "SM   dir: " << smDir << std::endl;
  std::cout << "INT  dir: " << intDir << std::endl;
  std::cout << "QUAD dir: " << quadDir << std::endl;
  std::cout << "Cuts: pTl > " << ptlcut << ", pTj > " << ptjcut << ", |eta_j| < " << etajcut << std::endl;

  TH1D* h_sm_raw   = BuildHist("SM_raw",   smDir,   xsec_sm_fb,   lumi_fb, nbins, xmin, xmax, ptlcut, ptjcut, etajcut);
  TH1D* h_int_raw  = BuildHist("Int_raw",  intDir,  xsec_int_fb,  lumi_fb, nbins, xmin, xmax, ptlcut, ptjcut, etajcut);
  TH1D* h_quad_raw = BuildHist("Quad_raw", quadDir, xsec_quad_fb, lumi_fb, nbins, xmin, xmax, ptlcut, ptjcut, etajcut);

  if (!h_sm_raw || !h_int_raw || !h_quad_raw) {
    std::cerr << "At least one histogram could not be created." << std::endl;
    return;
  }

  TH1D* h_sm     = static_cast<TH1D*>(h_sm_raw->Clone("h_mww_sm"));
  TH1D* h_smint  = static_cast<TH1D*>(h_sm_raw->Clone("h_mww_smint"));
  TH1D* h_smquad = static_cast<TH1D*>(h_sm_raw->Clone("h_mww_smquad"));

  h_sm->SetDirectory(nullptr);
  h_smint->SetDirectory(nullptr);
  h_smquad->SetDirectory(nullptr);

  h_smint->Add(h_int_raw);    // SM + Int
  h_smquad->Add(h_quad_raw);  // SM + Quad

  NormalizeIfRequested(h_sm, shape_norm);
  NormalizeIfRequested(h_smint, shape_norm);
  NormalizeIfRequested(h_smquad, shape_norm);

  const TString ytitle = shape_norm ? "A.U." : "Events";
  StyleHist(h_sm,     kBlack,    ytitle);
  StyleHist(h_smint,  kRed + 1,  ytitle);
  StyleHist(h_smquad, kBlue + 1, ytitle);

  const double ymax = std::max({h_sm->GetMaximum(), h_smint->GetMaximum(), h_smquad->GetMaximum()});
  h_sm->SetMaximum(ymax > 0.0 ? 1.25 * ymax : 1.0);
  h_sm->SetMinimum(1e-4);

  TCanvas* c = new TCanvas("c_mww", "c_mww", 900, 700);
  c->SetLeftMargin(0.12);
  c->SetBottomMargin(0.12);
  c->SetTicks(1, 1);
  c->SetLogy();

  h_sm->Draw("HIST");
  h_smint->Draw("HIST SAME");
  h_smquad->Draw("HIST SAME");

 // TLine* zeroLine = new TLine(xmin, 0.0, xmax, 0.0);
 // zeroLine->SetLineStyle(2);
 // zeroLine->SetLineWidth(2);
 // zeroLine->SetLineColor(kGray + 2);
 // zeroLine->Draw("SAME");

  h_sm->Draw("HIST SAME");
  h_smint->Draw("HIST SAME");
  h_smquad->Draw("HIST SAME");

  TLegend* leg = new TLegend(0.62, 0.72, 0.88, 0.88);
  leg->SetBorderSize(0);
  leg->SetFillStyle(0);
  leg->SetTextSize(0.04);
  leg->AddEntry(h_sm, "SM", "l");
  leg->AddEntry(h_smint, "SM+Int", "l");
  leg->AddEntry(h_smquad, "SM+Quad", "l");
  leg->Draw();

  c->SaveAs(outName + ".png");
  c->SaveAs(outName + ".pdf");

  TFile fout(outName + ".root", "RECREATE");
  h_sm->Write("h_mww_sm");
  h_smint->Write("h_mww_smint");
  h_smquad->Write("h_mww_smquad");
  h_sm_raw->Write("h_mww_sm_raw");
  h_int_raw->Write("h_mww_int_raw");
  h_quad_raw->Write("h_mww_quad_raw");
  fout.Close();

  std::cout << "Saved: " << outName << ".png, " << outName << ".pdf, " << outName << ".root" << std::endl;
}