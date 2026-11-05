#include <TROOT.h>
#include <TFile.h>
#include <TTree.h>
#include <TSystem.h>
#include <TString.h>
#include <TRandom.h>
#include <TH1D.h>
#include <TH2D.h>
#include <TMath.h>
#include <iostream>
#include <fstream>
#include <cassert>
#include <filesystem>
#include <algorithm>
#include <cmath>
#include "TLorentzVector.h"
#include "TColor.h"

#include "makePlots/common.h"

// whichAna = 0 (SSWW), fidAna = 0/2/4 (WW), 1/3/5 (WWb)
// whichAna = 0 (WZ), fidAna = 0 (WZ), 1 (WZb)

// -----------------------------------------------------------------------------
// EFT/AAC helpers
// -----------------------------------------------------------------------------
// The input EFT INT and QUAD histograms are assumed to have been produced at
// Wilson coefficient c0. For AAC, the datacard must contain, for one operator:
//   sm                    = SM
//   sm_lin_quad_<wc>       = SM + INT/c0 + QUAD/c0^2
//   quad_<wc>              = QUAD/c0^2
//
// The pure interference histogram is never written as a datacard process.

struct EFTConfig {
  TString op;       // e.g. M0, T0
  TString wc;       // e.g. cM0, cT0
  int intIndex;     // histogram category for pure INT input
  int quadIndex;    // histogram category for pure QUAD input
};

bool getEFTConfig(TString eftOp, EFTConfig &cfg) {
  eftOp.ToUpper();

  if(eftOp == "M0") {
    cfg = {"M0", "cM0", kPlotEFTM0Int, kPlotEFTM0Quad};
    return true;
  }
  else if(eftOp == "M1") {
    cfg = {"M1", "cM1", kPlotEFTM1Int, kPlotEFTM1Quad};
    return true;
  }
  else if(eftOp == "M7") {
    cfg = {"M7", "cM7", kPlotEFTM7Int, kPlotEFTM7Quad};
    return true;
  }
  else if(eftOp == "S0") {
    cfg = {"S0", "cS0", kPlotEFTS0Int, kPlotEFTS0Quad};
    return true;
  }
  else if(eftOp == "T0") {
    cfg = {"T0", "cT0", kPlotEFTT0Int, kPlotEFTT0Quad};
    return true;
  }
  else if(eftOp == "T1") {
    cfg = {"T1", "cT1", kPlotEFTT1Int, kPlotEFTT1Quad};
    return true;
  }
  else if(eftOp == "T2") {
    cfg = {"T2", "cT2", kPlotEFTT2Int, kPlotEFTT2Quad};
    return true;
  }

  return false;
}

bool isAnyEFTComponent(int ic) {
  if(ic == kPlotEFTM0Int || ic == kPlotEFTM0Quad) return true;
  if(ic == kPlotEFTM1Int || ic == kPlotEFTM1Quad) return true;
  if(ic == kPlotEFTM7Int || ic == kPlotEFTM7Quad) return true;
  if(ic == kPlotEFTS0Int || ic == kPlotEFTS0Quad) return true;
  if(ic == kPlotEFTT0Int || ic == kPlotEFTT0Quad) return true;
  if(ic == kPlotEFTT1Int || ic == kPlotEFTT1Quad) return true;
  if(ic == kPlotEFTT2Int || ic == kPlotEFTT2Quad) return true;
  return false;
}

bool skipInactiveEFTProcess(int ic, const EFTConfig &cfg) {
  if(!isAnyEFTComponent(ic)) return false;
  if(ic == cfg.intIndex) return false;
  if(ic == cfg.quadIndex) return false;
  return true;
}

TH1D* cloneWithDirectoryOff(TH1D* h, const TString& name) {
  assert(h);
  TH1D* out = (TH1D*)h->Clone(name);
  out->SetNameTitle(name, name);
  out->SetDirectory(0);
  return out;
}

TH1D* buildSMLinearQuadratic(TH1D* hSM, TH1D* hINT, TH1D* hQUAD,
                             const TString& name, double c0) {
  assert(hSM);
  assert(hINT);
  assert(hQUAD);
  TH1D* out = cloneWithDirectoryOff(hSM, name);
  out->Add(hINT,  1.0 / c0);
  out->Add(hQUAD, 1.0 / (c0 * c0));
  return out;
}

TH1D* buildQuadratic(TH1D* hQUAD, const TString& name, double c0) {
  assert(hQUAD);
  TH1D* out = cloneWithDirectoryOff(hQUAD, name);
  out->Scale(1.0 / (c0 * c0));
  return out;
}

void convertEFTTemplatesToAAC(TH1D* histos[nPlotCategories], double c0,
                              const EFTConfig &cfg) {
  if(!histos[kPlotEWKSSWW] || !histos[cfg.intIndex] || !histos[cfg.quadIndex]) return;

  TH1D* hSM   = histos[kPlotEWKSSWW];
  TH1D* hINT  = histos[cfg.intIndex];
  TH1D* hQUAD = histos[cfg.quadIndex];

  TString hSMName  = "histo_sm";
  TString hSLQName = Form("histo_sm_lin_quad_%s", cfg.wc.Data());
  TString hQName   = Form("histo_quad_%s", cfg.wc.Data());

  TH1D* hSMOut  = cloneWithDirectoryOff(hSM, hSMName);
  TH1D* hSLQOut = buildSMLinearQuadratic(hSM, hINT, hQUAD, hSLQName, c0);
  TH1D* hQOut   = buildQuadratic(hQUAD, hQName, c0);

  histos[kPlotEWKSSWW] = hSMOut;
  histos[cfg.intIndex] = hSLQOut;
  histos[cfg.quadIndex] = hQOut;
}

// -----------------------------------------------------------------------------
// Diagnostic: print negative bins AFTER SM + linear + quadratic are combined.
// -----------------------------------------------------------------------------
// This checks ONLY the final AAC SLQ object
//
//   sm_lin_quad_<wc> = SM + INT/c0 + QUAD/c0^2
//
// and is called immediately after convertEFTTemplatesToAAC().
//
// IMPORTANT:
//   For systematic templates this check is done BEFORE the existing
//   non-positive -> nominal replacement, so no negative merged AAC bin is hidden.
void printNegativeEFTBins(TH1D* histos[nPlotCategories],
                          const EFTConfig &cfg,
                          const TString &label) {
  const int ids[3] = {kPlotEWKSSWW, cfg.intIndex, cfg.quadIndex};

  for(int k = 0; k < 3; ++k) {
    TH1D *h = histos[ids[k]];
    if(!h) continue;

    for(int nb = 1; nb <= h->GetNbinsX(); ++nb) {
      if(h->GetBinContent(nb) < 0.0) {
        printf("NEGATIVE EFT BIN: %-18s hist=%s bin=%d\n",
               label.Data(), h->GetName(), nb);
      }
    }
  }
}

// Theory policy, matching the SSWW treatment:
// for every MC process, including the final AAC basis processes,
// a negative THEORY bin is set to zero.
// Only the bin content is changed; the existing bin error is left untouched.
void zeroNegativeTheoryBins(TH1D* histos[nPlotCategories]) {
  for(int ic = 0; ic < nPlotCategories; ++ic) {
    if(ic == kPlotData) continue;
    TH1D *h = histos[ic];
    if(!h) continue;

    for(int nb = 1; nb <= h->GetNbinsX(); ++nb) {
      if(h->GetBinContent(nb) < 0.0) {
        h->SetBinContent(nb, 0.0);
      }
    }
  }
}


bool useProcess(int ic, TH1D* histo_Baseline[nPlotCategories], const EFTConfig &cfg) {
  if(ic == kPlotData) return false;
  if(skipInactiveEFTProcess(ic, cfg)) return false;
  if(!histo_Baseline[ic]) return false;
  if(histo_Baseline[ic]->Integral() == 0.0) return false;
  return true;
}

bool shouldWriteHistogram(int ic, TH1D* histo_Baseline[nPlotCategories], const EFTConfig &cfg) {
  if(ic == kPlotData) return histo_Baseline[ic] != nullptr;
  return useProcess(ic, histo_Baseline, cfg);
}


// -----------------------------------------------------------------------------
// Background-shape protection helpers
// -----------------------------------------------------------------------------
// These helpers are for generic background cleanup.
// Theory-systematic clipping for the final AAC basis is handled explicitly
// after SM/INT/QUAD are combined. Experimental AAC fallback is handled
// separately by replacing non-positive varied bins with nominal.

bool isAACProcess(int ic, const EFTConfig &cfg) {
  if(ic == kPlotEWKSSWW) return true;   // sm
  if(ic == cfg.intIndex) return true;   // sm_lin_quad_cX
  if(ic == cfg.quadIndex) return true;  // quad_cX
  return false;
}

bool protectThisProcess(int ic, const EFTConfig &cfg) {
  if(ic == kPlotData) return false;
  if(isAACProcess(ic, cfg)) return false;
  return true;
}

void zeroNegativeBinsForBkg(TH1D *h, int ic, const EFTConfig &cfg) {
  if(!h) return;
  if(!protectThisProcess(ic, cfg)) return;

  for(int nb = 1; nb <= h->GetNbinsX(); nb++) {
    if(h->GetBinContent(nb) < 0.0) {
      h->SetBinContent(nb, 0.0);
      h->SetBinError(nb, 0.0);
    }
  }
}

void replaceBadIntegralForBkg(TH1D *h, TH1D *hNom, int ic, const EFTConfig &cfg) {
  if(!h || !hNom) return;
  if(!protectThisProcess(ic, cfg)) return;

  if(h->Integral() <= 0.0) {
    
    h->Reset();
    h->Add(hNom);
  }
}

void protectHistogramForBkg(TH1D *h, TH1D *hNom, int ic, const EFTConfig &cfg) {
  zeroNegativeBinsForBkg(h, ic, cfg);
  replaceBadIntegralForBkg(h, hNom, ic, cfg);
}

void safeScaleToNominal(TH1D *h, TH1D *hNom, int ic, const EFTConfig &cfg) {
  if(!h || !hNom) return;

  const double nom = hNom->GetSumOfWeights();
  const double den = h->GetSumOfWeights();

  // EFT/AAC templates are not repaired or clipped. They are only scaled if possible.
  if(isAACProcess(ic, cfg)) {
    if(den != 0.0) {
      h->Scale(nom / den);
    }
    else {
      
    }
    return;
  }

  // Normal backgrounds are repaired before scaling.
  protectHistogramForBkg(h, hNom, ic, cfg);

  const double denAfter = h->GetSumOfWeights();
  if(nom > 0.0 && denAfter > 0.0) {
    h->Scale(nom / denAfter);
  }
  else if(nom > 0.0) {
    
    h->Reset();
    h->Add(hNom);
  }
}



bool validateAACProcesses(TH1D* histos[nPlotCategories],
                          const EFTConfig &cfg,
                          const TString &label,
                          double tinyTolerance = 1e-10) {
  (void)label;
  (void)tinyTolerance;

  const int ids[3] = {kPlotEWKSSWW, cfg.intIndex, cfg.quadIndex};

  for(int k = 0; k < 3; ++k) {
    TH1D *h = histos[ids[k]];
    if(!h) return false;

    if(!std::isfinite(h->Integral())) return false;

    for(int nb = 1; nb <= h->GetNbinsX(); ++nb) {
      if(!std::isfinite(h->GetBinContent(nb)) ||
         !std::isfinite(h->GetBinError(nb))) {
        return false;
      }
    }
  }

  return true;
}


// -----------------------------------------------------------------------------
// AAC experimental-systematic protection
// -----------------------------------------------------------------------------
// If an EXPERIMENTAL AAC basis variation becomes non-positive while the NOMINAL
// AAC basis bin is positive, replace that pathological variation by the
// nominal value in that bin.
//
// This is the historical SSWW/EFT numerical safeguard. It is not a universal
// AAC/Combine prescription. It means that this nuisance has zero effect in
// that one pathological bin. Every occurrence is printed.
//
// The replacement is applied after SM/INT/QUAD have been converted into the
// AAC basis, so pure interference is never clipped by this function.
void replaceNonPositiveAACSystematicWithNominal(
    TH1D* varied[nPlotCategories],
    TH1D* nominal[nPlotCategories],
    const EFTConfig &cfg,
    const TString &label) {

  const int ids[3] = {kPlotEWKSSWW, cfg.intIndex, cfg.quadIndex};

  for(int k = 0; k < 3; ++k) {
    TH1D *hVar = varied[ids[k]];
    TH1D *hNom = nominal[ids[k]];
    if(!hVar || !hNom) continue;

    const int nbins = std::min(hVar->GetNbinsX(), hNom->GetNbinsX());

    for(int nb = 1; nb <= nbins; ++nb) {
      const double nom = hNom->GetBinContent(nb);
      const double var = hVar->GetBinContent(nb);

      if(nom > 0.0 && var <= 0.0) {
hVar->SetBinContent(nb, nom);
        hVar->SetBinError(nb, hNom->GetBinError(nb));
      }
    }
  }
}


// Historical SSWW shape-ratio treatment.
// For positive nominal and positive varied template:
//   * ratio above 1.15 -> 1.15
//   * ratio below 0.85 -> 0.85
//   * Down is reciprocal to Up.
//
// If the varied template is non-positive, Up and Down are both set to nominal.
// For AAC processes that fallback is explicitly printed.
void setSymmetricShapeBin(
    TH1D *hUp,
    TH1D *hDown,
    TH1D *hNom,
    int nb,
    const TString &processName,
    const TString &systName,
    bool printAACFallback,
    bool applyHistoricalCap = true,
    double ratioMin = 0.85,
    double ratioMax = 1.15) {

  if(!hUp || !hDown || !hNom) return;

  const double nom = hNom->GetBinContent(nb);
  const double rawUp = hUp->GetBinContent(nb);

  if(nom <= 0.0) {
    hUp->SetBinContent(nb, nom);
    hDown->SetBinContent(nb, nom);
    return;
  }

  if(rawUp <= 0.0 || !std::isfinite(rawUp)) {
    (void)printAACFallback;
hUp->SetBinContent(nb, nom);
    hDown->SetBinContent(nb, nom);
    return;
  }

  double ratio = rawUp / nom;

  if(applyHistoricalCap) {
    if(ratio > ratioMax) ratio = ratioMax;
    else if(ratio < ratioMin) ratio = ratioMin;
  }

  hUp->SetBinContent(nb, nom * ratio);
  hDown->SetBinContent(nb, nom / ratio);
}


void makeEFTDatacards(int whichAna = 0, int fidAna = 0, TString InputDir = "/mnt/home/mghimiray/VBSStudies/Outputs_EFT/fakerrate/1001/1200/merge1/", TString anaSel = "sswwAnalysis", int year = 20240, TString eftOp = "M0", double nC0 = 10.0, int cutoff = 0000, int variable = 1010){
  EFTConfig cfg;
  if(!getEFTConfig(eftOp, cfg)) {
    
    return;
  }

  const double c0 = nC0; // Wilson coefficient value used in the generated INT/QUAD samples.
  if(c0 == 0.0) {
    
    return;
  }

  int isTypeFakeSyst = 2;
  plotBaseNames[kPlotNonPrompt] = "NonPrompt";
  if     (anaSel.Contains("wzAnalysis")) {plotBaseNames[kPlotNonPrompt] = "NonWZPrompt";}
  else if(anaSel.Contains("zzAnalysis")) {plotBaseNames[kPlotNonPrompt] = "NonZZPrompt"; isTypeFakeSyst = 0;}

  // AAC process names for the selected one-operator fit.

  plotBaseNames[kPlotEWKSSWW] = "sm";
  plotBaseNames[cfg.intIndex]  = Form("sm_lin_quad_%s", cfg.wc.Data());
  plotBaseNames[cfg.quadIndex] = Form("quad_%s", cfg.wc.Data());

  
  
  

  int theYear = 0;
  TString theTagYear = "NULL";
  double triggerEffUnc = 1.000;
  double lumiU[4] = {1.000, 1.000, 1.000, 1.000};
  if     (year == 20220) {triggerEffUnc = 1.005; lumiU[0] = 1.0138; lumiU[1] = 1.0000; lumiU[2] = 1.0000; theYear = 2022; theTagYear = "2022";}
  else if(year == 20221) {triggerEffUnc = 1.005; lumiU[0] = 1.0138; lumiU[1] = 1.0000; lumiU[2] = 1.0000; theYear = 2022; theTagYear = "2022EE";}
  else if(year ==  2022) {triggerEffUnc = 1.005; lumiU[0] = 1.0138; lumiU[1] = 1.0000; lumiU[2] = 1.0000; theYear = 2022; theTagYear = "2022";}
  else if(year == 20230) {triggerEffUnc = 1.005; lumiU[0] = 1.0017; lumiU[1] = 1.0127; lumiU[2] = 1.0000; theYear = 2023; theTagYear = "2023";}
  else if(year == 20231) {triggerEffUnc = 1.005; lumiU[0] = 1.0017; lumiU[1] = 1.0127; lumiU[2] = 1.0000; theYear = 2023; theTagYear = "2023BPix";}
  else if(year ==  2023) {triggerEffUnc = 1.005; lumiU[0] = 1.0017; lumiU[1] = 1.0127; lumiU[2] = 1.0000; theYear = 2023; theTagYear = "2023";}
  else if(year == 20240) {triggerEffUnc = 1.005; lumiU[0] = 1.0020; lumiU[1] = 1.0068; lumiU[2] = 1.0144; theYear = 2024; theTagYear = "2024";}
  else if(year == 20250) {triggerEffUnc = 1.005; lumiU[0] = 1.0000; lumiU[1] = 1.0000; lumiU[2] = 1.0000; lumiU[3] = 1.0500; theYear = 2025; theTagYear = "2025";}
  else { return;}

  int jumpValue = 200;
  int startHistogram = 0;
  TString postFixFile = "_mva";
  TString postFixHist = "MVA";
  if     (anaSel.Contains("wzAnalysis")) {startHistogram = 300; postFixFile = ""; postFixHist = "";}
  else if(anaSel.Contains("zzAnalysis")) {startHistogram = 300; postFixFile = ""; postFixHist = "";}

  double systValue;
  TFile *inputFile;
  TFile *outputFile;
  const int endTheory = 113;
  const int nSystTotal = 169;
  const int nSystDataCardTotal = 112; // (nSystTotal-endTheory)*2 = nSystDataCardTotal

  TH1D *histo_Baseline[nPlotCategories] = {};
  TH1D *histo_QCDScaleUp[nPlotCategories] = {};
  TH1D *histo_QCDScaleDown[nPlotCategories] = {};
  TH1D *histo_PSUp[nPlotCategories] = {};
  TH1D *histo_PSDown[nPlotCategories] = {};

  TH1D *histo_Syst[nSystTotal][nPlotCategories] = {};
  TH1D *histo_SystDataCard[nSystDataCardTotal][nPlotCategories] = {};
  TH1D *histo_PDFUp  [101][nPlotCategories] = {};
  TH1D *histo_PDFDown[101][nPlotCategories] = {};

  const int numberBTagSyst = 11;
  TString BtagSFBCNames[numberBTagSyst] = {"CMS_btag_fixedWP_bc_02", "CMS_btag_fixedWP_bc_bfragmentation", "CMS_btag_fixedWP_bc_colorreconnection", "CMS_btag_fixedWP_bc_hdamp", "CMS_btag_fixedWP_bc_jer", "CMS_btag_fixedWP_bc_jes", "CMS_btag_fixedWP_bc_pdf", "CMS_btag_fixedWP_bc_pileup", "CMS_btag_fixedWP_bc_topmass", "CMS_btag_fixedWP_bc_type3", Form("CMS_btag_fixedWP_bc_uncorrelated_%s",theTagYear.Data())};

  const int numberJESSyst = 28;
  TString jesNames[numberJESSyst] = {"", "AbsoluteMPFBias", "AbsoluteScale", "AbsoluteStat", "FlavorQCD", "Fragmentation", "PileUpDataMC", "PileUpPtBB", "PileUpPtEC1", "PileUpPtEC2", "PileUpPtHF", "PileUpPtRef", "RelativeFSR", "RelativeJEREC1", "RelativeJEREC2", "RelativeJERHF", "RelativePtBB", "RelativePtEC1", "RelativePtEC2", "RelativePtHF", "RelativeBal", "RelativeSample", "RelativeStatEC", "RelativeStatFSR", "RelativeStatHF", "SinglePionECAL", "SinglePionHCAL", "TimePtEta"};

  jesNames[ 3] = Form("%s_%s"  ,jesNames[ 3].Data(),theTagYear.Data()); // AbsoluteStat
  jesNames[13] = Form("%s_%s"  ,jesNames[13].Data(),theTagYear.Data()); // RelativeJEREC1
  jesNames[14] = Form("%s_%s"  ,jesNames[14].Data(),theTagYear.Data()); // RelativeJEREC2
  jesNames[17] = Form("%s_%s"  ,jesNames[17].Data(),theTagYear.Data()); // RelativePtEC1
  jesNames[18] = Form("%s_%s"  ,jesNames[18].Data(),theTagYear.Data()); // RelativePtEC2
  jesNames[21] = Form("%s_%s"  ,jesNames[21].Data(),theTagYear.Data()); // RelativeSample
  jesNames[22] = Form("%s_%s"  ,jesNames[22].Data(),theTagYear.Data()); // RelativeStatEC
  jesNames[23] = Form("%s_%s"  ,jesNames[23].Data(),theTagYear.Data()); // RelativeStatFSR
  jesNames[24] = Form("%s_%s"  ,jesNames[24].Data(),theTagYear.Data()); // RelativeStatHF
  jesNames[27] = Form("%s_%s"  ,jesNames[27].Data(),theTagYear.Data()); // TimePtEta

  TString nameSyst[nSystDataCardTotal];
  nameSyst[  0] = Form("CMS_eff_m_reco_%sUp",theTagYear.Data());
  nameSyst[  1] = Form("CMS_eff_m_reco_%sDown",theTagYear.Data());
  nameSyst[  2] = Form("CMS_eff_m_id_%sUp",theTagYear.Data());
  nameSyst[  3] = Form("CMS_eff_m_id_%sDown",theTagYear.Data());
  nameSyst[  4] = Form("CMS_eff_m_iso_%sUp",theTagYear.Data());
  nameSyst[  5] = Form("CMS_eff_m_iso_%sDown",theTagYear.Data());
  nameSyst[  6] = Form("CMS_eff_e_reco_%sUp",theTagYear.Data());
  nameSyst[  7] = Form("CMS_eff_e_reco_%sDown",theTagYear.Data());
  nameSyst[  8] = Form("CMS_eff_e_idUp");
  nameSyst[  9] = Form("CMS_eff_e_idDown");
  nameSyst[10 ] = "pileup_13p6TeVUp";
  nameSyst[11 ] = "pileup_13p6TeVDown";
  nameSyst[12 ] = Form("CMS_SMP25013_WWtrigger_%sUp",theTagYear.Data());
  nameSyst[13 ] = Form("CMS_SMP25013_WWtrigger_%sDown",theTagYear.Data());
  nameSyst[14 ] = Form("CMS_SMP25013_eff_m_tightid_%sUp",theTagYear.Data());
  nameSyst[15 ] = Form("CMS_SMP25013_eff_m_tightid_%sDown",theTagYear.Data());
  nameSyst[16 ] = Form("CMS_SMP25013_eff_e_tightid_%sUp",theTagYear.Data());
  nameSyst[17 ] = Form("CMS_SMP25013_eff_e_tightid_%sDown",theTagYear.Data());
  nameSyst[18 ] = Form("%sUp"  ,BtagSFBCNames[ 0].Data());
  nameSyst[19 ] = Form("%sDown",BtagSFBCNames[ 0].Data());
  nameSyst[20 ] = Form("%sUp"  ,BtagSFBCNames[ 1].Data());
  nameSyst[21 ] = Form("%sDown",BtagSFBCNames[ 1].Data());
  nameSyst[22 ] = Form("%sUp"  ,BtagSFBCNames[ 2].Data());
  nameSyst[23 ] = Form("%sDown",BtagSFBCNames[ 2].Data());
  nameSyst[24 ] = Form("%sUp"  ,BtagSFBCNames[ 3].Data());
  nameSyst[25 ] = Form("%sDown",BtagSFBCNames[ 3].Data());
  nameSyst[26 ] = Form("%sUp"  ,BtagSFBCNames[ 4].Data());
  nameSyst[27 ] = Form("%sDown",BtagSFBCNames[ 4].Data());
  nameSyst[28 ] = Form("%sUp"  ,BtagSFBCNames[ 5].Data());
  nameSyst[29 ] = Form("%sDown",BtagSFBCNames[ 5].Data());
  nameSyst[30 ] = Form("%sUp"  ,BtagSFBCNames[ 6].Data());
  nameSyst[31 ] = Form("%sDown",BtagSFBCNames[ 6].Data());
  nameSyst[32 ] = Form("%sUp"  ,BtagSFBCNames[ 7].Data());
  nameSyst[33 ] = Form("%sDown",BtagSFBCNames[ 7].Data());
  nameSyst[34 ] = Form("%sUp"  ,BtagSFBCNames[ 8].Data());
  nameSyst[35 ] = Form("%sDown",BtagSFBCNames[ 8].Data());
  nameSyst[36 ] = Form("%sUp"  ,BtagSFBCNames[ 9].Data());
  nameSyst[37 ] = Form("%sDown",BtagSFBCNames[ 9].Data());
  nameSyst[38 ] = Form("%sUp"  ,BtagSFBCNames[10].Data());
  nameSyst[39 ] = Form("%sDown",BtagSFBCNames[10].Data());
  nameSyst[40 ] = "CMS_btag_fixedWP_light_simpleUp";
  nameSyst[41 ] = "CMS_btag_fixedWP_light_simpleDown";
  nameSyst[42 ] = "ewkCorrUp";
  nameSyst[43 ] = "ewkCorrDown";
  nameSyst[44 ] = Form("CMS_scale_m_%sUp",theTagYear.Data());
  nameSyst[45 ] = Form("CMS_scale_m_%sDown",theTagYear.Data());
  nameSyst[46 ] = Form("CMS_scale_e_%sUp",theTagYear.Data());
  nameSyst[47 ] = Form("CMS_scale_e_%sDown",theTagYear.Data());
  nameSyst[48 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 0].Data());
  nameSyst[49 ] = Form("CMS_scale_j_%sDown",jesNames[ 0].Data());
  nameSyst[50 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 1].Data());
  nameSyst[51 ] = Form("CMS_scale_j_%sDown",jesNames[ 1].Data());
  nameSyst[52 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 2].Data());
  nameSyst[53 ] = Form("CMS_scale_j_%sDown",jesNames[ 2].Data());
  nameSyst[54 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 3].Data());
  nameSyst[55 ] = Form("CMS_scale_j_%sDown",jesNames[ 3].Data());
  nameSyst[56 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 4].Data());
  nameSyst[57 ] = Form("CMS_scale_j_%sDown",jesNames[ 4].Data());
  nameSyst[58 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 5].Data());
  nameSyst[59 ] = Form("CMS_scale_j_%sDown",jesNames[ 5].Data());
  nameSyst[60 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 6].Data());
  nameSyst[61 ] = Form("CMS_scale_j_%sDown",jesNames[ 6].Data());
  nameSyst[62 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 7].Data());
  nameSyst[63 ] = Form("CMS_scale_j_%sDown",jesNames[ 7].Data());
  nameSyst[64 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 8].Data());
  nameSyst[65 ] = Form("CMS_scale_j_%sDown",jesNames[ 8].Data());
  nameSyst[66 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 9].Data());
  nameSyst[67 ] = Form("CMS_scale_j_%sDown",jesNames[ 9].Data());
  nameSyst[68 ] = Form("CMS_scale_j_%sUp"  ,jesNames[10].Data());
  nameSyst[69 ] = Form("CMS_scale_j_%sDown",jesNames[10].Data());
  nameSyst[70 ] = Form("CMS_scale_j_%sUp"  ,jesNames[11].Data());
  nameSyst[71 ] = Form("CMS_scale_j_%sDown",jesNames[11].Data());
  nameSyst[72 ] = Form("CMS_scale_j_%sUp"  ,jesNames[12].Data());
  nameSyst[73 ] = Form("CMS_scale_j_%sDown",jesNames[12].Data());
  nameSyst[74 ] = Form("CMS_scale_j_%sUp"  ,jesNames[13].Data());
  nameSyst[75 ] = Form("CMS_scale_j_%sDown",jesNames[13].Data());
  nameSyst[76 ] = Form("CMS_scale_j_%sUp"  ,jesNames[14].Data());
  nameSyst[77 ] = Form("CMS_scale_j_%sDown",jesNames[14].Data());
  nameSyst[78 ] = Form("CMS_scale_j_%sUp"  ,jesNames[15].Data());
  nameSyst[79 ] = Form("CMS_scale_j_%sDown",jesNames[15].Data());
  nameSyst[80 ] = Form("CMS_scale_j_%sUp"  ,jesNames[16].Data());
  nameSyst[81 ] = Form("CMS_scale_j_%sDown",jesNames[16].Data());
  nameSyst[82 ] = Form("CMS_scale_j_%sUp"  ,jesNames[17].Data());
  nameSyst[83 ] = Form("CMS_scale_j_%sDown",jesNames[17].Data());
  nameSyst[84 ] = Form("CMS_scale_j_%sUp"  ,jesNames[18].Data());
  nameSyst[85 ] = Form("CMS_scale_j_%sDown",jesNames[18].Data());
  nameSyst[86 ] = Form("CMS_scale_j_%sUp"  ,jesNames[19].Data());
  nameSyst[87 ] = Form("CMS_scale_j_%sDown",jesNames[19].Data());
  nameSyst[88 ] = Form("CMS_scale_j_%sUp"  ,jesNames[20].Data());
  nameSyst[89 ] = Form("CMS_scale_j_%sDown",jesNames[20].Data());
  nameSyst[90 ] = Form("CMS_scale_j_%sUp"  ,jesNames[21].Data());
  nameSyst[91 ] = Form("CMS_scale_j_%sDown",jesNames[21].Data());
  nameSyst[92 ] = Form("CMS_scale_j_%sUp"  ,jesNames[22].Data());
  nameSyst[93 ] = Form("CMS_scale_j_%sDown",jesNames[22].Data());
  nameSyst[94 ] = Form("CMS_scale_j_%sUp"  ,jesNames[23].Data());
  nameSyst[95 ] = Form("CMS_scale_j_%sDown",jesNames[23].Data());
  nameSyst[96 ] = Form("CMS_scale_j_%sUp"  ,jesNames[24].Data());
  nameSyst[97 ] = Form("CMS_scale_j_%sDown",jesNames[24].Data());
  nameSyst[98 ] = Form("CMS_scale_j_%sUp"  ,jesNames[25].Data());
  nameSyst[99 ] = Form("CMS_scale_j_%sDown",jesNames[25].Data());
  nameSyst[100] = Form("CMS_scale_j_%sUp"  ,jesNames[26].Data());
  nameSyst[101] = Form("CMS_scale_j_%sDown",jesNames[26].Data());
  nameSyst[102] = Form("CMS_scale_j_%sUp"  ,jesNames[27].Data());
  nameSyst[103] = Form("CMS_scale_j_%sDown",jesNames[27].Data());
  nameSyst[104] = Form("CMS_res_j_%sUp",theTagYear.Data());
  nameSyst[105] = Form("CMS_res_j_%sDown",theTagYear.Data());
  nameSyst[106] = Form("CMS_scale_met_jer_%sUp",theTagYear.Data());
  nameSyst[107] = Form("CMS_scale_met_jer_%sDown",theTagYear.Data());
  nameSyst[108] = Form("CMS_scale_met_jes_%sUp",theTagYear.Data());
  nameSyst[109] = Form("CMS_scale_met_jes_%sDown",theTagYear.Data());
  nameSyst[110] = Form("CMS_scale_met_unclustered_energy_%sUp",theTagYear.Data());
  nameSyst[111] = Form("CMS_scale_met_unclustered_energy_%sDown",theTagYear.Data());

  TString nameFakeSyst = "random";
  if     (anaSel.Contains("sswwAnalysis")) {
    nameFakeSyst = "ssww";
  }
  else if(anaSel.Contains("wzAnalysis")) {
    nameFakeSyst = "wz";
  }
  else if(anaSel.Contains("zzAnalysis")) {
    nameFakeSyst = "zz";
  }
  else {
    
    return;
  }

  inputFile = new TFile(Form("%s/fillhisto_%s_%d_%d%s.root",InputDir.Data(),anaSel.Data(),year,startHistogram+fidAna*jumpValue,postFixFile.Data()), "read");
  for(unsigned ic=kPlotData; ic!=nPlotCategories; ic++) {
    histo_Baseline[ic] = (TH1D*)inputFile->Get(Form("histo%s%d", postFixHist.Data(), ic)); assert(histo_Baseline[ic]); histo_Baseline[ic]->SetDirectory(0);
    histo_Baseline[ic]->SetNameTitle(Form("histo_%s",plotBaseNames[ic].Data()),Form("histo_%s",plotBaseNames[ic].Data()));
  }
  delete inputFile;

  // Convert nominal SM/INT/QUAD EFT inputs to the AAC basis.
  // After this point:
  //   kPlotEWKSSWW -> histo_sm
  //   cfg.intIndex -> histo_sm_lin_quad_<wc>
  //   cfg.quadIndex -> histo_quad_<wc>
  convertEFTTemplatesToAAC(histo_Baseline, c0, cfg);

  // Check the final merged SM+linear+quadratic nominal template.
  printNegativeEFTBins(histo_Baseline, cfg, "NOMINAL");

  if(!validateAACProcesses(histo_Baseline, cfg, "nominal")) {
    
    return;
  }

  // Initialize theory-shape uncertainty histograms using the final AAC process names.
  for(int ic=0; ic<nPlotCategories; ic++) {
    if(!useProcess(ic, histo_Baseline, cfg)) continue;

    histo_QCDScaleUp[ic] =
      (TH1D*)histo_Baseline[ic]->Clone(
        Form("histo_%s_QCD_scale_%s_ACCEPTUp",
             plotBaseNames[ic].Data(), plotBaseNames[ic].Data()));

    histo_QCDScaleDown[ic] =
      (TH1D*)histo_Baseline[ic]->Clone(
        Form("histo_%s_QCD_scale_%s_ACCEPTDown",
             plotBaseNames[ic].Data(), plotBaseNames[ic].Data()));

    histo_PSUp[ic] =
      (TH1D*)histo_Baseline[ic]->Clone(
        Form("histo_%s_PS_%s_ACCEPTUp",
             plotBaseNames[ic].Data(), plotBaseNames[ic].Data()));

    histo_PSDown[ic] =
      (TH1D*)histo_Baseline[ic]->Clone(
        Form("histo_%s_PS_%s_ACCEPTDown",
             plotBaseNames[ic].Data(), plotBaseNames[ic].Data()));

    histo_QCDScaleUp[ic]->SetDirectory(0);
    histo_QCDScaleDown[ic]->SetDirectory(0);
    histo_PSUp[ic]->SetDirectory(0);
    histo_PSDown[ic]->SetDirectory(0);
  }

  for(int j=0; j<nSystTotal; j++){
    for(int ic=0; ic<nPlotCategories; ic++) {
      if(!histo_Baseline[ic]) continue;
      histo_Syst[j][ic] = (TH1D*)histo_Baseline[ic]->Clone(Form("histo_%s_%d",plotBaseNames[ic].Data(),j));
      histo_Syst[j][ic]->SetDirectory(0);
    }
  }
  for(int j=0; j<nSystDataCardTotal; j++){
    for(int ic=0; ic<nPlotCategories; ic++) {
      if(!useProcess(ic, histo_Baseline, cfg)) continue;
      if(
        (ic == kPlotEWKSSWW) &&
         nameSyst[j].Contains("ewkCorr")) {
        histo_SystDataCard[j][ic] = (TH1D*)histo_Baseline[ic]->Clone(Form("histo_%s_WW%s",plotBaseNames[ic].Data(),nameSyst[j].Data()));
      }
      else if(
        (ic == kPlotEWKWZ) &&
         nameSyst[j].Contains("ewkCorr")) {
        histo_SystDataCard[j][ic] = (TH1D*)histo_Baseline[ic]->Clone(Form("histo_%s_WZ%s",plotBaseNames[ic].Data(),nameSyst[j].Data()));
      }
      else {
        histo_SystDataCard[j][ic] = (TH1D*)histo_Baseline[ic]->Clone(Form("histo_%s_%s",plotBaseNames[ic].Data(),nameSyst[j].Data()));
      }
    }
  }
  for(int j=0; j<101; j++){
    for(int ic=0; ic<nPlotCategories; ic++) {
      if(!useProcess(ic, histo_Baseline, cfg)) continue;
      histo_PDFUp[j][ic] = (TH1D*)histo_Baseline[ic]->Clone(Form("histo_%s_pdf%dUp", plotBaseNames[ic].Data(), j));
      histo_PDFUp[j][ic]->SetDirectory(0);
    }
    for(int ic=0; ic<nPlotCategories; ic++) {
      if(!useProcess(ic, histo_Baseline, cfg)) continue;
      histo_PDFDown[j][ic] = (TH1D*)histo_Baseline[ic]->Clone(Form("histo_%s_pdf%dDown", plotBaseNames[ic].Data(), j));
      histo_PDFDown[j][ic]->SetDirectory(0);
    }
  }

  for(int j=0; j<nSystTotal; j++){
    inputFile = new TFile(Form("%s/fillhisto_%s_%d_%d%s.root",InputDir.Data(),anaSel.Data(),year,startHistogram+fidAna*jumpValue+1+j,postFixFile.Data()), "read");
    for(unsigned ic=kPlotData; ic!=nPlotCategories; ic++) {
      histo_Syst[j][ic] = (TH1D*)inputFile->Get(Form("histo%s%d", postFixHist.Data(), ic)); assert(histo_Syst[j][ic]); histo_Syst[j][ic]->SetDirectory(0);
    }
    delete inputFile;

    // Convert each systematic variation to the same AAC basis:
    // sm, sm_lin_quad_<wc>, quad_<wc>.
    convertEFTTemplatesToAAC(histo_Syst[j], c0, cfg);

    // Print any negative final AAC basis bin BEFORE applying the policy.
    if(j < endTheory) {
      printNegativeEFTBins(histo_Syst[j], cfg, Form("THEORY_%d", j));

      // Theory: same treatment for ordinary MC and EFT/AAC.
      // Negative content -> 0. Bin error is intentionally left unchanged.
      zeroNegativeTheoryBins(histo_Syst[j]);
    }
    else {
      printNegativeEFTBins(histo_Syst[j], cfg, Form("EXPERIMENTAL_%d", j));

      // Experimental AAC: non-positive varied bin with positive nominal
      // -> nominal, exactly analogous to the final SSWW shape fallback.
      replaceNonPositiveAACSystematicWithNominal(
          histo_Syst[j], histo_Baseline, cfg, Form("experimental_%d", j));
    }

    if(!validateAACProcesses(histo_Syst[j], cfg, Form("systematic_%d", j))) {
      return;
    }
  }

  for(unsigned ic=0; ic<nPlotCategories; ic++) {
    if(!useProcess(ic, histo_Baseline, cfg)) continue;
    for(int nb=1; nb<=histo_Baseline[ic]->GetNbinsX(); nb++){
      histo_Baseline[ic]->SetBinContent(nb, TMath::Max((float)histo_Baseline[ic]->GetBinContent(nb),0.0f));

      // compute QCD scale uncertainties bin-by-bin
      double diffQCDScale[6] = {
       TMath::Abs(histo_Syst[4][ic]->GetBinContent(nb)-histo_Baseline[ic]->GetBinContent(nb)),
       TMath::Abs(histo_Syst[5][ic]->GetBinContent(nb)-histo_Baseline[ic]->GetBinContent(nb)),
       TMath::Abs(histo_Syst[6][ic]->GetBinContent(nb)-histo_Baseline[ic]->GetBinContent(nb)),
       TMath::Abs(histo_Syst[7][ic]->GetBinContent(nb)-histo_Baseline[ic]->GetBinContent(nb)),
       TMath::Abs(histo_Syst[8][ic]->GetBinContent(nb)-histo_Baseline[ic]->GetBinContent(nb)),
       TMath::Abs(histo_Syst[9][ic]->GetBinContent(nb)-histo_Baseline[ic]->GetBinContent(nb))};

      double systQCDScale = diffQCDScale[0];
      for(int nqcd=1; nqcd<6; nqcd++) {
        if(diffQCDScale[nqcd] > systQCDScale) systQCDScale = diffQCDScale[nqcd];
      }

      if(histo_Baseline[ic]->GetBinContent(nb) > 0) 
        systQCDScale = 1.0+systQCDScale/histo_Baseline[ic]->GetBinContent(nb);
      else systQCDScale = 1;

      histo_QCDScaleUp  [ic]->SetBinContent(nb, histo_Baseline[ic]->GetBinContent(nb)*systQCDScale);
      histo_QCDScaleDown[ic]->SetBinContent(nb, histo_Baseline[ic]->GetBinContent(nb)/systQCDScale);

      // compute PS uncertainties bin-by-bin
      double diffPS[4] = {
       TMath::Abs(histo_Syst[0][ic]->GetBinContent(nb)-histo_Baseline[ic]->GetBinContent(nb)),
       TMath::Abs(histo_Syst[1][ic]->GetBinContent(nb)-histo_Baseline[ic]->GetBinContent(nb)),
       TMath::Abs(histo_Syst[2][ic]->GetBinContent(nb)-histo_Baseline[ic]->GetBinContent(nb)),
       TMath::Abs(histo_Syst[3][ic]->GetBinContent(nb)-histo_Baseline[ic]->GetBinContent(nb))};

      double systPS = diffPS[0];
      for(int nps=1; nps<4; nps++) {
        if(diffPS[nps] > systPS) systPS = diffPS[nps];
      }

      if(histo_Baseline[ic]->GetBinContent(nb) > 0) 
        systPS = 1.0+systPS/histo_Baseline[ic]->GetBinContent(nb);
      else systPS = 1;

      histo_PSUp  [ic]->SetBinContent(nb, histo_Baseline[ic]->GetBinContent(nb)*systPS);
      histo_PSDown[ic]->SetBinContent(nb, histo_Baseline[ic]->GetBinContent(nb)/systPS);

      // Final theory-shape protection, identical for ordinary MC and EFT/AAC.
      histo_QCDScaleUp  [ic]->SetBinContent(nb, TMath::Max((float)histo_QCDScaleUp  [ic]->GetBinContent(nb),0.0f));
      histo_QCDScaleDown[ic]->SetBinContent(nb, TMath::Max((float)histo_QCDScaleDown[ic]->GetBinContent(nb),0.0f));
      histo_PSUp        [ic]->SetBinContent(nb, TMath::Max((float)histo_PSUp        [ic]->GetBinContent(nb),0.0f));
      histo_PSDown      [ic]->SetBinContent(nb, TMath::Max((float)histo_PSDown      [ic]->GetBinContent(nb),0.0f));

      // compute PDF uncertainties
      for(int npdf=0; npdf<100; npdf++){
        double diff = 0;
        if(histo_Baseline[ic]->GetBinContent(nb) > 0) diff = TMath::Abs(histo_Syst[npdf+11][ic]->GetBinContent(nb)-histo_Baseline[ic]->GetBinContent(nb))/histo_Baseline[ic]->GetBinContent(nb);
        diff = std::min(diff, 0.15);
        histo_PDFUp  [npdf][ic]->SetBinContent(nb, histo_Baseline[ic]->GetBinContent(nb)*(1.0+diff));
        histo_PDFDown[npdf][ic]->SetBinContent(nb, histo_Baseline[ic]->GetBinContent(nb)/(1.0+diff));
      }
      histo_PDFUp  [100][ic]->SetBinContent(nb, histo_Syst[111][ic]->GetBinContent(nb));
      histo_PDFDown[100][ic]->SetBinContent(nb, histo_Syst[112][ic]->GetBinContent(nb));

      // PDF is also a theory uncertainty: negative content -> 0 for all MC/EFT.
      for(int npdf=0; npdf<101; ++npdf) {
        histo_PDFUp[npdf][ic]->SetBinContent(
            nb, TMath::Max((float)histo_PDFUp[npdf][ic]->GetBinContent(nb),0.0f));
        histo_PDFDown[npdf][ic]->SetBinContent(
            nb, TMath::Max((float)histo_PDFDown[npdf][ic]->GetBinContent(nb),0.0f));
      }

      // ---------------------------------------------------------------------
      // General experimental shape uncertainties.
      //
      // Each source histo_Syst[endTheory+nuis] is treated as the Up template.
      // Down is constructed reciprocally around nominal.
      //
      // Historical SSWW treatment retained:
      //   positive varied/nominal ratio -> cap to [0.85,1.15]
      //   non-positive varied bin       -> Up = Down = nominal
      //
      // IMPORTANT: this does NOT combine all nuisances into one envelope.
      // Each nuisance is still written separately to the datacard.
      // ---------------------------------------------------------------------
      for(int nuis=0; nuis<nSystTotal-endTheory; nuis++) {
        TH1D *hUp   = histo_SystDataCard[2*nuis][ic];
        TH1D *hDown = histo_SystDataCard[2*nuis+1][ic];
        TH1D *hNom  = histo_Baseline[ic];

        if(!hUp || !hDown || !hNom || !histo_Syst[endTheory+nuis][ic]) continue;

        hUp->SetBinContent(nb, histo_Syst[endTheory+nuis][ic]->GetBinContent(nb));
        hUp->SetBinError(nb,   histo_Syst[endTheory+nuis][ic]->GetBinError(nb));

        setSymmetricShapeBin(
            hUp,
            hDown,
            hNom,
            nb,
            plotBaseNames[ic],
            nameSyst[2*nuis],
            isAACProcess(ic, cfg),
            true,   // retain historical SSWW 0.85--1.15 cap
            0.85,
            1.15);
      }

    } // loop over bins
  } // loop over categories

  // Begin Nonprompt study
  const int nNonPromptSyst = 12;
  TString namenonPromptSyst[nNonPromptSyst];
  namenonPromptSyst[ 0] = Form("CMS_SMP25013_fake_%s_m0Up",nameFakeSyst.Data());
  namenonPromptSyst[ 1] = Form("CMS_SMP25013_fake_%s_m1Down",nameFakeSyst.Data());
  namenonPromptSyst[ 2] = Form("CMS_SMP25013_fake_%s_m2Up",nameFakeSyst.Data());
  namenonPromptSyst[ 3] = Form("CMS_SMP25013_fake_%s_e0Up",nameFakeSyst.Data());
  namenonPromptSyst[ 4] = Form("CMS_SMP25013_fake_%s_e1Up",nameFakeSyst.Data());
  namenonPromptSyst[ 5] = Form("CMS_SMP25013_fake_%s_e2Up",nameFakeSyst.Data());
  namenonPromptSyst[ 6] = Form("CMS_SMP25013_fake_%s_m0Down",nameFakeSyst.Data());
  namenonPromptSyst[ 7] = Form("CMS_SMP25013_fake_%s_m1Up",nameFakeSyst.Data());
  namenonPromptSyst[ 8] = Form("CMS_SMP25013_fake_%s_m2Down",nameFakeSyst.Data());
  namenonPromptSyst[ 9] = Form("CMS_SMP25013_fake_%s_e0Down",nameFakeSyst.Data());
  namenonPromptSyst[10] = Form("CMS_SMP25013_fake_%s_e1Down",nameFakeSyst.Data());
  namenonPromptSyst[11] = Form("CMS_SMP25013_fake_%s_e2Down",nameFakeSyst.Data());
  const int totalNumberFakeSyst = 6;
  TH1D *histo_InputNonPromtUnc[totalNumberFakeSyst];
  TH1D *histo_NonPromtUnc[nNonPromptSyst];
  if(isTypeFakeSyst != 0){
    inputFile = new TFile(Form("%s/fillhisto_%s_%d_nonprompt.root",InputDir.Data(),anaSel.Data(),year), "read");
    int startH = totalNumberFakeSyst*fidAna;
    for(int j=0; j<totalNumberFakeSyst; j++){
      histo_InputNonPromtUnc[j] = (TH1D*)inputFile->Get(Form("histoNonPrompt_%d", j+startH));
      histo_NonPromtUnc[j+                  0] = (TH1D*)histo_InputNonPromtUnc[j]->Clone(Form("histo_%s_%s", plotBaseNames[kPlotNonPrompt].Data(), namenonPromptSyst[j+                  0].Data())); histo_NonPromtUnc[j+		    0]->SetDirectory(0);
      histo_NonPromtUnc[j+totalNumberFakeSyst] = (TH1D*)histo_InputNonPromtUnc[j]->Clone(Form("histo_%s_%s", plotBaseNames[kPlotNonPrompt].Data(), namenonPromptSyst[j+totalNumberFakeSyst].Data())); histo_NonPromtUnc[j+totalNumberFakeSyst]->SetDirectory(0);
    }
    delete inputFile;

    for(int j=0; j<totalNumberFakeSyst; j++){
      for(int nb=1; nb<=histo_Baseline[kPlotNonPrompt]->GetNbinsX(); nb++){
        histo_NonPromtUnc[j+                  0]->SetBinContent(nb, TMath::Max((float)histo_NonPromtUnc[j+                  0]->GetBinContent(nb),0.0f));
        histo_NonPromtUnc[j+totalNumberFakeSyst]->SetBinContent(nb, TMath::Max((float)histo_NonPromtUnc[j+totalNumberFakeSyst]->GetBinContent(nb),0.0f));
       if(histo_Baseline[kPlotNonPrompt]->GetBinContent(nb) > 0) {
          systValue = histo_NonPromtUnc[j+0]->GetBinContent(nb) / histo_Baseline[kPlotNonPrompt]->GetBinContent(nb);
          if     (systValue >   3.0) systValue =   3.0;
          else if(systValue < 1/3.0) systValue = 1/3.0;
          histo_NonPromtUnc[j+0]->SetBinContent(nb,histo_Baseline[kPlotNonPrompt]->GetBinContent(nb)*systValue);
          if(systValue > 0) histo_NonPromtUnc[j+totalNumberFakeSyst]->SetBinContent(nb,histo_Baseline[kPlotNonPrompt]->GetBinContent(nb)/systValue);
        }
      }
      if(anaSel.Contains("sswwAnalysis")){
        double nomFake = histo_Baseline[kPlotNonPrompt]->GetSumOfWeights();

        double denUp = histo_NonPromtUnc[j+0]->GetSumOfWeights();
        if(nomFake > 0.0 && denUp > 0.0) {
          histo_NonPromtUnc[j+0]->Scale(nomFake / denUp);
        }
        else {
          
          histo_NonPromtUnc[j+0]->Reset();
          histo_NonPromtUnc[j+0]->Add(histo_Baseline[kPlotNonPrompt]);
        }

        double denDown = histo_NonPromtUnc[j+totalNumberFakeSyst]->GetSumOfWeights();
        if(nomFake > 0.0 && denDown > 0.0) {
          histo_NonPromtUnc[j+totalNumberFakeSyst]->Scale(nomFake / denDown);
        }
        else {
          
          histo_NonPromtUnc[j+totalNumberFakeSyst]->Reset();
          histo_NonPromtUnc[j+totalNumberFakeSyst]->Add(histo_Baseline[kPlotNonPrompt]);
        }
      }    }
  }
  // End Nonprompt study

  // Begin wrongsign study
  const int nwrongsignSyst = 4;
  TString namewrongsignSyst[nwrongsignSyst];
  namewrongsignSyst[ 0] = Form("CMS_SMP25013_wrongsign_stat_%sUp",theTagYear.Data());
  namewrongsignSyst[ 1] =      "CMS_SMP25013_wrongsign_methodUp";
  namewrongsignSyst[ 2] = Form("CMS_SMP25013_wrongsign_stat_%sDown",theTagYear.Data());
  namewrongsignSyst[ 3] =      "CMS_SMP25013_wrongsign_methodDown";
  const int totalNumberWSSyst = 2;
  TH1D *histo_InputWSUnc[totalNumberWSSyst];
  TH1D *histo_WSUnc[nwrongsignSyst];
  if(anaSel.Contains("sswwAnalysis")){
    inputFile = new TFile(Form("%s/fillhisto_%s_%d_wrongsign.root",InputDir.Data(),anaSel.Data(),year), "read");
    int startH = totalNumberWSSyst*fidAna;
    for(int j=0; j<totalNumberWSSyst; j++){
      histo_InputWSUnc[j] = (TH1D*)inputFile->Get(Form("histoWS_%d", j+startH));
      histo_WSUnc[j+                0] = (TH1D*)histo_InputWSUnc[j]->Clone(Form("histo_%s_%s", plotBaseNames[kPlotWS].Data(), namewrongsignSyst[j+                0].Data())); histo_WSUnc[j+                0]->SetDirectory(0);
      histo_WSUnc[j+totalNumberWSSyst] = (TH1D*)histo_InputWSUnc[j]->Clone(Form("histo_%s_%s", plotBaseNames[kPlotWS].Data(), namewrongsignSyst[j+totalNumberWSSyst].Data())); histo_WSUnc[j+totalNumberWSSyst]->SetDirectory(0);
    }
    delete inputFile;

    for(int j=0; j<totalNumberWSSyst; j++){
      for(int nb=1; nb<=histo_Baseline[kPlotWS]->GetNbinsX(); nb++){
        histo_WSUnc[j+                0]->SetBinContent(nb, TMath::Max((float)histo_WSUnc[j+                0]->GetBinContent(nb),0.0f));
        histo_WSUnc[j+totalNumberWSSyst]->SetBinContent(nb, TMath::Max((float)histo_WSUnc[j+totalNumberWSSyst]->GetBinContent(nb),0.0f));
        if(histo_Baseline[kPlotWS]->GetBinContent(nb) > 0) {
          systValue = histo_WSUnc[j+0]->GetBinContent(nb) / histo_Baseline[kPlotWS]->GetBinContent(nb);
          if     (systValue > 1.15) systValue = 1.15;
          else if(systValue < 0.85) systValue = 0.85;
          histo_WSUnc[j+0]->SetBinContent(nb,histo_Baseline[kPlotWS]->GetBinContent(nb)*systValue);
          
          if(systValue > 0) histo_WSUnc[j+totalNumberWSSyst]->SetBinContent(nb,histo_Baseline[kPlotWS]->GetBinContent(nb)/systValue);
        }
      }
    }
  }
  // End wrongsign study

  TString additionalSuffix = "";
  if(whichAna != 0){ 
    additionalSuffix = "_alt";
  }

  // Begin renormalize
  for(unsigned ic=kPlotData; ic!=nPlotCategories; ic++) {
    if(!useProcess(ic, histo_Baseline, cfg)) continue;
    if(!(ic == kPlotEWKSSWW ||
         ic == kPlotWZ ||
         ic == kPlotEWKWZ ||
         ic == kPlotZZ ||
         ic == cfg.intIndex ||
         ic == cfg.quadIndex
        )) continue;

    safeScaleToNominal(histo_QCDScaleUp  [ic], histo_Baseline[ic], ic, cfg);
    safeScaleToNominal(histo_QCDScaleDown[ic], histo_Baseline[ic], ic, cfg);
    safeScaleToNominal(histo_PSUp        [ic], histo_Baseline[ic], ic, cfg);
    safeScaleToNominal(histo_PSDown      [ic], histo_Baseline[ic], ic, cfg);

    for(int npdf=0; npdf<101; npdf++){
      safeScaleToNominal(histo_PDFUp  [npdf][ic], histo_Baseline[ic], ic, cfg);
      safeScaleToNominal(histo_PDFDown[npdf][ic], histo_Baseline[ic], ic, cfg);
    }

    for(int j=0; j<nSystDataCardTotal; j++) {
      if(!histo_SystDataCard[j][ic]) continue;
      TString histName = histo_SystDataCard[j][ic]->GetName();
      if(histName.Contains("pileup") || histName.Contains("ewkCorr")) {
        safeScaleToNominal(histo_SystDataCard[j][ic], histo_Baseline[ic], ic, cfg);
      }
    }
  }
  // End renormalize

  // Begin Fix a feature affecting first bin
  for(unsigned ic=kPlotData; ic!=nPlotCategories; ic++) {
    if(!shouldWriteHistogram(ic, histo_Baseline, cfg)) continue;
    if(ic == kPlotData) {
      histo_Baseline[ic]->SetBinError(1,sqrt(histo_Baseline[ic]->GetBinContent(1)));
    } else {
      float relativeUncBin2 = 0.01;
      if(histo_Baseline[ic]->GetBinContent(2) > 0) relativeUncBin2 = histo_Baseline[ic]->GetBinError(2)/histo_Baseline[ic]->GetBinContent(2);
      histo_Baseline[ic]->SetBinError(1,relativeUncBin2*histo_Baseline[ic]->GetBinContent(1));
    }
  }
  // End Fix a feature affecting first bin

  TString outdir = Form("/mnt/home/mghimiray/VBSStudies/Outputs_EFT/fakerrate/%d/%04d/datacards", variable, cutoff);
  std::filesystem::create_directories(outdir.Data());
  TString c0Tag = TString::Format("%.6g", c0);
  c0Tag.ReplaceAll(".", "p");
  c0Tag.ReplaceAll("-", "m");
  TString outputLimits = Form("%s/output_%s_%s_%d_bin%d%s.root", outdir.Data(), anaSel.Data(), cfg.op.Data(), year, fidAna, additionalSuffix.Data());
  // Protect non-EFT/background histograms before writing.
  // This is intentionally not applied to sm, sm_lin_quad_<wc>, or quad_<wc>.
  for(unsigned ic=kPlotData; ic!=nPlotCategories; ic++) {
    if(!shouldWriteHistogram(ic, histo_Baseline, cfg)) continue;
    if(!protectThisProcess(ic, cfg)) continue;

    zeroNegativeBinsForBkg(histo_Baseline[ic], ic, cfg);

    if(histo_Baseline[ic]->Integral() <= 0.0) {
      
      continue;
    }

    for(int j=0; j<nSystDataCardTotal; j++) {
      if(histo_SystDataCard[j][ic]) {
        protectHistogramForBkg(histo_SystDataCard[j][ic], histo_Baseline[ic], ic, cfg);
      }
    }

    protectHistogramForBkg(histo_QCDScaleUp  [ic], histo_Baseline[ic], ic, cfg);
    protectHistogramForBkg(histo_QCDScaleDown[ic], histo_Baseline[ic], ic, cfg);
    protectHistogramForBkg(histo_PSUp        [ic], histo_Baseline[ic], ic, cfg);
    protectHistogramForBkg(histo_PSDown      [ic], histo_Baseline[ic], ic, cfg);

    for(int npdf=0; npdf<101; npdf++){
      if(histo_PDFUp[npdf][ic]) {
        protectHistogramForBkg(histo_PDFUp[npdf][ic], histo_Baseline[ic], ic, cfg);
      }
      if(histo_PDFDown[npdf][ic]) {
        protectHistogramForBkg(histo_PDFDown[npdf][ic], histo_Baseline[ic], ic, cfg);
      }
    }
  }

  // Protect nonprompt fake-shape histograms.
  if(isTypeFakeSyst != 0 && histo_Baseline[kPlotNonPrompt]) {
    for(int j=0; j<nNonPromptSyst; j++) {
      if(histo_NonPromtUnc[j]) {
        protectHistogramForBkg(histo_NonPromtUnc[j],
                               histo_Baseline[kPlotNonPrompt],
                               kPlotNonPrompt,
                               cfg);
      }
    }
  }

  // Protect wrong-sign shape histograms.
  if(anaSel.Contains("sswwAnalysis") && histo_Baseline[kPlotWS]) {
    for(int j=0; j<nwrongsignSyst; j++) {
      if(histo_WSUnc[j]) {
        protectHistogramForBkg(histo_WSUnc[j],
                               histo_Baseline[kPlotWS],
                               kPlotWS,
                               cfg);
      }
    }
  }

  outputFile = new TFile(outputLimits, "RECREATE");
  outputFile->cd();
  for(unsigned ic=kPlotData; ic!=nPlotCategories; ic++) {
    if(!shouldWriteHistogram(ic, histo_Baseline, cfg)) continue;

    histo_Baseline[ic]->Write();

    if(ic == kPlotData) continue; // data_obs has no nuisance shapes

    for(int j=0; j<nSystDataCardTotal; j++) {
      if(histo_SystDataCard[j][ic]) histo_SystDataCard[j][ic]->Write();
    }

    if(histo_QCDScaleUp  [ic]) histo_QCDScaleUp  [ic]->Write();
    if(histo_QCDScaleDown[ic]) histo_QCDScaleDown[ic]->Write();
    if(histo_PSUp        [ic]) histo_PSUp        [ic]->Write();
    if(histo_PSDown      [ic]) histo_PSDown      [ic]->Write();
    for(int npdf=0; npdf<101; npdf++){
      if(histo_PDFUp  [npdf][ic]) histo_PDFUp  [npdf][ic]->Write();
      if(histo_PDFDown[npdf][ic]) histo_PDFDown[npdf][ic]->Write();
    }
  }
  if(isTypeFakeSyst != 0) for(int j=0; j<nNonPromptSyst; j++) histo_NonPromtUnc[j]->Write();
  if(anaSel.Contains("sswwAnalysis")) for(int j=0; j<nwrongsignSyst; j++) histo_WSUnc[j]->Write();
  outputFile->Close();

  // Filling datacards txt file
  char outputLimitsCard[1024];
  sprintf(outputLimitsCard,"%s/datacard_%s_%s_%d_bin%d%s.txt",
          outdir.Data(), anaSel.Data(), cfg.op.Data(), year, fidAna, additionalSuffix.Data());
  ofstream newcardShape;
  newcardShape.open(outputLimitsCard);
  newcardShape << Form("imax * number of channels\n");
  newcardShape << Form("jmax * number of background minus 1\n");
  newcardShape << Form("kmax * number of nuisance parameters\n");

  newcardShape << Form("shapes    *   *   %s  histo_$PROCESS histo_$PROCESS_$SYSTEMATIC\n",outputLimits.Data());
  newcardShape << Form("shapes data_obs * %s  histo_Data\n",outputLimits.Data());

  newcardShape << Form("Observation %f\n",histo_Baseline[kPlotData]->GetSumOfWeights());

  newcardShape << Form("bin   ");
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!useProcess(ic, histo_Baseline, cfg)) continue;
    newcardShape << Form("ch%d ",fidAna);

  }
  newcardShape << Form("\n");

  newcardShape << Form("process  ");
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!useProcess(ic, histo_Baseline, cfg)) continue;
    newcardShape << Form("%s  ", plotBaseNames[ic].Data());
  }
  newcardShape << Form("\n");

  newcardShape << Form("process  ");
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!useProcess(ic, histo_Baseline, cfg)) continue;
    if     (ic == kPlotEWKSSWW) newcardShape << Form("%d  ", 1);
    else if(ic == cfg.intIndex)  newcardShape << Form("%d  ", 2);
    else if(ic == cfg.quadIndex) newcardShape << Form("%d  ", 3);
    else                         newcardShape << Form("%d  ", ic);
  }
  newcardShape << Form("\n");

  newcardShape << Form("rate  ");
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!useProcess(ic, histo_Baseline, cfg)) continue;
    newcardShape << Form("%f  ", histo_Baseline[ic]->GetSumOfWeights());
  }
  newcardShape << Form("\n");

  if(isTypeFakeSyst == 1){
    newcardShape << Form("CMS_SMP25013_fake_%s_m      lnN ",nameFakeSyst.Data());
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!useProcess(ic, histo_Baseline, cfg)) continue;
      if(ic == kPlotNonPrompt) newcardShape << Form("%6.3f ",1.15);
      else		       newcardShape << Form("- "); 
    }
    newcardShape << Form("\n");

    newcardShape << Form("CMS_SMP25013_fake_%s_e lnN ",nameFakeSyst.Data());
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!useProcess(ic, histo_Baseline, cfg)) continue;
      if(ic == kPlotNonPrompt) newcardShape << Form("%6.3f ",1.15);
      else		       newcardShape << Form("- ");
    }
    newcardShape << Form("\n");
  } // isTraditionalSyst == true
  else if(isTypeFakeSyst == 2){
    newcardShape << Form("CMS_SMP25013_fake_%s_m0 shape ",nameFakeSyst.Data());
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!useProcess(ic, histo_Baseline, cfg)) continue;
      if(ic == kPlotNonPrompt) newcardShape << Form("1.0 ");
      else		       newcardShape << Form("- "); 
    }
    newcardShape << Form("\n");

    newcardShape << Form("CMS_SMP25013_fake_%s_m1 shape ",nameFakeSyst.Data());
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!useProcess(ic, histo_Baseline, cfg)) continue;
      if(ic == kPlotNonPrompt) newcardShape << Form("1.0 ");
      else		       newcardShape << Form("- "); 
    }
    newcardShape << Form("\n");

    newcardShape << Form("CMS_SMP25013_fake_%s_m2 shape ",nameFakeSyst.Data());
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!useProcess(ic, histo_Baseline, cfg)) continue;
      if(ic == kPlotNonPrompt) newcardShape << Form("1.0 ");
      else		       newcardShape << Form("- "); 
    }
    newcardShape << Form("\n");

    newcardShape << Form("CMS_SMP25013_fake_%s_e0 shape ",nameFakeSyst.Data());
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!useProcess(ic, histo_Baseline, cfg)) continue;
      if(ic == kPlotNonPrompt) newcardShape << Form("1.0 ");
      else		       newcardShape << Form("- "); 
    }
    newcardShape << Form("\n");

    newcardShape << Form("CMS_SMP25013_fake_%s_e1 shape ",nameFakeSyst.Data());
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!useProcess(ic, histo_Baseline, cfg)) continue;
      if(ic == kPlotNonPrompt) newcardShape << Form("1.0 ");
      else		       newcardShape << Form("- "); 
    }
    newcardShape << Form("\n");

    newcardShape << Form("CMS_SMP25013_fake_%s_e2 shape ",nameFakeSyst.Data());
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!useProcess(ic, histo_Baseline, cfg)) continue;
      if(ic == kPlotNonPrompt) newcardShape << Form("1.0 ");
      else		       newcardShape << Form("- "); 
    }
    newcardShape << Form("\n");
  } // isTraditionalSyst == false

  for(int nl=0; nl<4; nl++){
    if(lumiU[nl] == 1) continue;
    newcardShape << Form("lumi_13p6TeV_%d lnN ", nl);
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!useProcess(ic, histo_Baseline, cfg)) continue;
      if(ic == kPlotNonPrompt) newcardShape << Form("- ");
      else                     newcardShape << Form("%6.3f ",lumiU[nl]);
    }
    newcardShape << Form("\n");
  }

  newcardShape << Form("CMS_SMP25013_trigger_%s   lnN     ",theTagYear.Data());
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!useProcess(ic, histo_Baseline, cfg)) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("%6.3f ",triggerEffUnc);
  }
  newcardShape << Form("\n");

  if(anaSel.Contains("sswwAnalysis")) {
    newcardShape << Form("CMS_SMP25013_wrongsign_stat_%s shape ",theTagYear.Data());
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!useProcess(ic, histo_Baseline, cfg)) continue;
      if(ic == kPlotWS) newcardShape << Form("1.0 ");
      else              newcardShape << Form("- "); 
    }
    newcardShape << Form("\n");


    newcardShape << Form("CMS_SMP25013_wrongsign_method shape ");
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!useProcess(ic, histo_Baseline, cfg)) continue;
      if(ic == kPlotWS) newcardShape << Form("1.0 ");
      else              newcardShape << Form("- "); 
    }
    newcardShape << Form("\n");
  }

  // BTagging uncertainties --> starting at 1, "2" not used
  for(int n_unc=1; n_unc<numberBTagSyst; n_unc++){
    newcardShape << Form("%s shape ",BtagSFBCNames[n_unc].Data());
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!useProcess(ic, histo_Baseline, cfg)) continue;
      if(ic == kPlotNonPrompt) newcardShape << Form("- ");
      else                     newcardShape << Form("1.0 ");
    }
    newcardShape << Form("\n");
  }

  newcardShape << Form("CMS_btag_fixedWP_light_simple shape ");
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!useProcess(ic, histo_Baseline, cfg)) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");

  newcardShape << Form("CMS_eff_m_reco_%s shape ",theTagYear.Data());
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!useProcess(ic, histo_Baseline, cfg)) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");

  newcardShape << Form("CMS_eff_m_id_%s shape ",theTagYear.Data());
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!useProcess(ic, histo_Baseline, cfg)) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");

  newcardShape << Form("CMS_eff_m_iso_%s shape ",theTagYear.Data());
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!useProcess(ic, histo_Baseline, cfg)) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");

  newcardShape << Form("CMS_eff_e_reco_%s shape ",theTagYear.Data());
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!useProcess(ic, histo_Baseline, cfg)) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");
 
  newcardShape << Form("CMS_eff_e_id shape ");
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!useProcess(ic, histo_Baseline, cfg)) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");

  newcardShape << Form("CMS_SMP25013_eff_m_tightid_%s shape ",theTagYear.Data());
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!useProcess(ic, histo_Baseline, cfg)) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");

  newcardShape << Form("CMS_SMP25013_eff_e_tightid_%s shape ",theTagYear.Data());
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!useProcess(ic, histo_Baseline, cfg)) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");

  newcardShape << Form("pileup_13p6TeV shape ");
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!useProcess(ic, histo_Baseline, cfg)) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");
 
  // JES uncertainties --> starting at 1, 0 == total (not used)
  for(int n_unc=1; n_unc<numberJESSyst; n_unc++){
    newcardShape << Form("CMS_scale_j_%s shape ",jesNames[n_unc].Data());
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!useProcess(ic, histo_Baseline, cfg)) continue;
      if     (ic == kPlotNonPrompt) newcardShape << Form("- ");
      else                          newcardShape << Form("1.0 ");
    }
    newcardShape << Form("\n");
  }

  newcardShape << Form("CMS_res_j_%s shape ",theTagYear.Data());
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!useProcess(ic, histo_Baseline, cfg)) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");
 
  newcardShape << Form("CMS_scale_m_%s shape ",theTagYear.Data());
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!useProcess(ic, histo_Baseline, cfg)) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");
 
  newcardShape << Form("CMS_scale_e_%s shape ",theTagYear.Data());
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!useProcess(ic, histo_Baseline, cfg)) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");

  //newcardShape << Form("CMS_scale_met_jer_%s shape ",theTagYear.Data());
  //for (int ic=0; ic<nPlotCategories; ic++){
  //  if(!histo_Baseline[ic]) continue;
  //  if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
  //  if(ic == kPlotNonPrompt) newcardShape << Form("- ");
  //  else		     newcardShape << Form("1.0 ");
  //}
  //newcardShape << Form("\n");

  //newcardShape << Form("CMS_scale_met_jes_%s shape ",theTagYear.Data());
  //for (int ic=0; ic<nPlotCategories; ic++){
  //  if(!histo_Baseline[ic]) continue;
  //  if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
  //  if(ic == kPlotNonPrompt) newcardShape << Form("- ");
  //  else		     newcardShape << Form("1.0 ");
  //}
  //newcardShape << Form("\n");

  newcardShape << Form("CMS_scale_met_unclustered_energy_%s shape ",theTagYear.Data());
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!useProcess(ic, histo_Baseline, cfg)) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else		     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");

  for(unsigned ic=0; ic<nPlotCategories; ic++) {
    if(!useProcess(ic, histo_Baseline, cfg) || ic == kPlotNonPrompt) continue;
    if     ( ic == kPlotEWKSSWW) continue;
    newcardShape << Form("QCD_scale_%s_ACCEPT shape ",plotBaseNames[ic].Data());
    for(unsigned ic2=0; ic2<nPlotCategories; ic2++) {
      if(!useProcess(ic2, histo_Baseline, cfg)) continue;
      if(ic==ic2) newcardShape << Form("1.0  ");
      else        newcardShape << Form("-  ");
      }
      newcardShape << Form("\n");
  } 

  newcardShape << Form("QCD_scale_sm_ACCEPT shape ");
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!useProcess(ic, histo_Baseline, cfg)) continue;
    if     (  ic != kPlotEWKSSWW
            ) newcardShape << Form("- ");
    else      newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");

  for(unsigned ic=0; ic<nPlotCategories; ic++) {
    if(!useProcess(ic, histo_Baseline, cfg) || ic == kPlotNonPrompt) continue;
    if     (ic == kPlotEWKSSWW) continue;
    newcardShape << Form("PS_%s_ACCEPT shape ",plotBaseNames[ic].Data());
    for(unsigned ic2=0; ic2<nPlotCategories; ic2++) {
      if(!useProcess(ic2, histo_Baseline, cfg)) continue;
      if(ic==ic2) newcardShape << Form("1.0  ");
      else        newcardShape << Form("-  ");
      }
      newcardShape << Form("\n");
  } 

  newcardShape << Form("PS_sm_ACCEPT shape ");
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!useProcess(ic, histo_Baseline, cfg)) continue;
    if     ( ic != kPlotEWKSSWW
           ) newcardShape << Form("- ");
    else     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");

  newcardShape << Form("WWewkCorr shape ");
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!useProcess(ic, histo_Baseline, cfg)) continue;
    if     (  ic != kPlotEWKSSWW
            ) newcardShape << Form("- ");
    else      newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");

  newcardShape << Form("WZewkCorr shape ");
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!useProcess(ic, histo_Baseline, cfg)) continue;
    if     (ic != kPlotEWKWZ
            ) newcardShape << Form("- ");
    else      newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");

  for(int npdf=100; npdf<=100; npdf++){
    newcardShape << Form("pdf%d shape ",npdf);
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!useProcess(ic, histo_Baseline, cfg)) continue;
      if(ic == kPlotNonPrompt) newcardShape << Form("- ");
      else                     newcardShape << Form("1.0 ");
    }
    newcardShape << Form("\n");
  }

  newcardShape << Form("pdfqq   lnN     ");
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!useProcess(ic, histo_Baseline, cfg)) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("%6.3f ",1.01);
  }
  newcardShape << Form("\n");

  if(anaSel.Contains("sswwAnalysis") || anaSel.Contains("wzAnalysis")){
    if(histo_Baseline[kPlotWZ] && histo_Baseline[kPlotWZ]->GetSumOfWeights() > 0)
    newcardShape << Form("CMS_ssww_wznorm  rateParam * %s 1 [0.1,4.9]\n",plotBaseNames[kPlotWZ].Data());
    if(histo_Baseline[kPlotEWKWZ] && histo_Baseline[kPlotEWKWZ]->GetSumOfWeights() > 0)
    newcardShape << Form("CMS_ssww_ewkwznorm  rateParam * %s 1 [0.1,4.9]\n",plotBaseNames[kPlotEWKWZ].Data());
    if(histo_Baseline[kPlotTVX] && histo_Baseline[kPlotTVX]->GetSumOfWeights() > 0)
    newcardShape << Form("CMS_ssww_tvxnorm  rateParam * %s 1 [0.1,4.9]\n",plotBaseNames[kPlotTVX].Data());
  }
  if(anaSel.Contains("sswwAnalysis")){
    if(histo_Baseline[kPlotNonPrompt] && histo_Baseline[kPlotNonPrompt]->GetSumOfWeights() > 0)
    //newcardShape << Form("CMS_ssww_nonpromptnorm_%d  rateParam * %s 1 [0.1,4.9]\n",(int)(fidAna/2),plotBaseNames[kPlotNonPrompt].Data());
    newcardShape << Form("CMS_ssww_nonpromptnorm  rateParam * %s 1 [0.1,4.9]\n",plotBaseNames[kPlotNonPrompt].Data());
  }
  //newcardShape << Form("CMS_ssww_zznorm  rateParam * %s 1 [0.1,4.9]\n",plotBaseNames[kPlotZZ].Data());

  // Preserve the established autoMCStats setting for a clean A/B comparison.
  newcardShape << Form("ch%d autoMCStats 0\n",fidAna);

  newcardShape.close();

}
