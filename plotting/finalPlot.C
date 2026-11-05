#include "TROOT.h"
#include "Math/ProbFuncMathCore.h"
#include "TInterpreter.h"
#include "TFile.h"
#include "TCanvas.h"
#include "TH1F.h"
#include "TStyle.h"
#include "TPad.h"
#include "TGaxis.h"
#include "TLine.h"
#include "Math/QuantFuncMathCore.h"
#include "TMath.h"
#include "TGraphAsymmErrors.h"
#include "TSystem.h"
#include "TRandom.h"
#include "common.h"
#include "StandardPlot.C"


#include <cassert>
#include <iostream>
#include <cmath>
#include <algorithm>

using namespace std;

double gEFTLegendCoeff = 1.0;
bool gUseEFTLegendCoeff = false;
double scaling[8] = {1,1,1,1,1,1,1,1};
//double scaling[8] = {73.496/69.913,1.2,168.114/157.695,404.402/361.347,2.583/2.537,1,1,1};
//double scaling[8] = {0.94,1.04,1.04,1.01,1.00,1.02,1.01,1.05};

bool isLogSpecial = false;
bool isLogX = false;
bool printRatios = false;
bool printYieldsBinByBin = false;


bool histHasAnyContent(TH1F *h){
  if(!h) return false;

  for(int i=0; i<=h->GetNbinsX()+1; i++){
    if(std::fabs(h->GetBinContent(i)) > 0.0) return true;
    if(std::fabs(h->GetBinError(i))   > 0.0) return true;
  }

  return false;
}

void eraselabel(TPad *p, Double_t h){
  p->cd();
  TPad *pe = new TPad("pe","pe",0.02,0,p->GetLeftMargin()-0.007,h);
  pe->Draw();
  pe->SetFillColor(p->GetFillColor());
  pe->SetBorderMode(0);
}

void atributes(TH1D *histo, TString xtitle = "", TString ytitle = "Fraction", TString units = ""){

  histo->SetTitle("");

  if(strcmp(units.Data(),"")==0){
    histo->GetXaxis()->SetTitle(xtitle.Data());
  }
  else {
    units = units.ReplaceAll("BIN","");

    if(strcmp(units.Data(),"")==0){
      histo->GetXaxis()->SetTitle(Form("%s",xtitle.Data()));
    }
    else {
      histo->GetXaxis()->SetTitle(Form("%s [%s]",xtitle.Data(),units.Data()));
    }
  }

  histo->GetXaxis()->SetLabelFont  (42);
  histo->GetXaxis()->SetLabelOffset(0.015);
  histo->GetXaxis()->SetLabelSize  (0.135);
  histo->GetXaxis()->SetNdivisions (505);
  histo->GetXaxis()->SetTitleFont  (42);
  histo->GetXaxis()->SetTitleOffset(1.00);
  histo->GetXaxis()->SetTitleSize  (0.120);

  histo->GetYaxis()->SetTitle(ytitle.Data());
  histo->GetYaxis()->SetLabelFont  (42);
  histo->GetYaxis()->SetLabelOffset(0.015);
  histo->GetYaxis()->SetLabelSize  (0.150);
  histo->GetYaxis()->SetNdivisions (505);
  histo->GetYaxis()->SetTitleFont  (42);
  histo->GetYaxis()->SetTitleOffset(0.43);
  histo->GetYaxis()->SetTitleSize  (0.120);

  histo->SetLineColor(kBlack);
  histo->SetMarkerSize(0.8);
  histo->SetMarkerStyle(kFullCircle);
}

bool shouldFlipEFTInterference(TString op)
{
  op.ToUpper();

  return (
    op == "T0" ||
    op == "T1" ||
    op == "T2" ||
    op == "S0" ||
    op == "M1" 
  );
}


int findPlotIndexLike(TString key1 = "", TString key2 = "", TString key3 = ""){

  TString k1 = key1; k1.ToLower();
  TString k2 = key2; k2.ToLower();
  TString k3 = key3; k3.ToLower();

  for(int i = 0; i < nPlotCategories; i++){

    TString name = plotBaseNames[i];
    TString lname = name;
    lname.ToLower();

    bool match = false;

    if(k1 != "" && lname.Contains(k1)) match = true;
    if(k2 != "" && lname.Contains(k2)) match = true;
    if(k3 != "" && lname.Contains(k3)) match = true;

    if(match) return i;
  }

  return -1;
}

void setAutoRatioRange(TH1D* hBand, TH1D* hRatio, bool forcePositive = true)
{
  double yMin =  1e30;
  double yMax = -1e30;

  for(int i=1; i<=hRatio->GetNbinsX(); i++){

    double y  = hRatio->GetBinContent(i);
    double ey = hRatio->GetBinError(i);

    if(!std::isfinite(y))  continue;
    if(!std::isfinite(ey)) ey = 0.0;

    // Ignore exactly empty bins
    if(y == 0.0 && ey == 0.0) continue;

    yMin = std::min(yMin, y - ey);
    yMax = std::max(yMax, y + ey);
  }

  // fallback
  if(yMin == 1e30 || yMax == -1e30){
    yMin = 0.0;
    yMax = 1.0;
  }

  double padding = 0.20 * (yMax - yMin);
  if(padding <= 0.0) padding = 0.20 * std::fabs(yMax);
  if(padding <= 0.0) padding = 1.0;

  yMin -= padding;
  yMax += padding;

  if(forcePositive){
    yMin = 0.0;
    if(yMax <= 0.0) yMax = 1.0;
  }

  // Use SetMinimum/SetMaximum because this histogram is used as the drawn frame.
  hBand->SetMinimum(yMin);
  hBand->SetMaximum(yMax);

  printf("AUTO LINEAR RANGE: ymin = %.4e, ymax = %.4e\n", yMin, yMax);
}

void setAutoChi2LogRange(TH1D* hBand, TH1D* hRatio)
{
  double yMin =  1e30;
  double yMax = -1e30;

  for(int i=1; i<=hRatio->GetNbinsX(); i++){

    double y = hRatio->GetBinContent(i);

    if(!std::isfinite(y)) continue;
    if(y <= 0.0) continue;

    yMin = std::min(yMin, y);
    yMax = std::max(yMax, y);
  }

  // fallback
  if(yMin == 1e30 || yMax == -1e30){
    yMin = 1e-4;
    yMax = 1.0;
  }

  // Pad the range by about half a decade on both sides
  yMin = std::pow(10.0, std::floor(std::log10(yMin)) - 0.5);
  yMax = std::pow(10.0, std::ceil (std::log10(yMax)) + 0.5);

  if(yMin <= 0.0) yMin = 1e-6;
  if(yMax <= yMin) yMax = 10.0*yMin;

  // Use SetMinimum/SetMaximum because this histogram is used as the drawn frame.
  hBand->SetMinimum(yMin);
  hBand->SetMaximum(yMax);

  printf("AUTO CHI2 LOG RANGE: ymin = %.4e, ymax = %.4e\n", yMin, yMax);
}


void setOverlayStyle(TH1F *h, int color, int style, int width = 3){

  if(!h) return;

  h->SetFillStyle(0);
  h->SetFillColor(0);
  h->SetLineColor(color);
  h->SetLineStyle(style);
  h->SetLineWidth(width);
}

TString getEFTOperatorFromUnits(TString units)
  {
    TString u = units;
    u.ToUpper();
  
    if(u.Contains("EFTM0")) return "M0";
    if(u.Contains("EFTM1")) return "M1";
    if(u.Contains("EFTM7")) return "M7";
    if(u.Contains("EFTS0")) return "S0";
    if(u.Contains("EFTT0")) return "T0";
    if(u.Contains("EFTT1")) return "T1";
    if(u.Contains("EFTT2")) return "T2";
    if(u.Contains("EFTM2")) return "M2";
    if(u.Contains("EFTM3")) return "M3";
    if(u.Contains("EFTM4")) return "M4";
    if(u.Contains("EFTM5")) return "M5";
    if(u.Contains("EFTT5")) return "T5";
    if(u.Contains("EFTT6")) return "T6";
    if(u.Contains("EFTT7")) return "T7";
  
    return "";
  }
  
  TString getAxisUnits(TString units)
  {
    TString u = units;
    u.ToUpper();
  
    // If the original units contain GeV anywhere, show only GeV
    if(u.Contains("GEV")) return "GeV";
  
    // If no physical unit is present, show no unit
    return "";
  }


  bool isAnyEFTCategory(int ic)
  {
    return (
      ic == kPlotEFTM0Int  || ic == kPlotEFTM0Quad ||
      ic == kPlotEFTM1Int  || ic == kPlotEFTM1Quad ||
      ic == kPlotEFTM7Int  || ic == kPlotEFTM7Quad ||
      ic == kPlotEFTS0Int  || ic == kPlotEFTS0Quad ||
      ic == kPlotEFTT0Int  || ic == kPlotEFTT0Quad ||
      ic == kPlotEFTT1Int  || ic == kPlotEFTT1Quad ||
      ic == kPlotEFTT2Int  || ic == kPlotEFTT2Quad ||
      ic == kPlotEFTM2QuadWZ || ic == kPlotEFTM3QuadWZ ||
      ic == kPlotEFTM4QuadWZ || ic == kPlotEFTM5QuadWZ ||
      ic == kPlotEFTT5QuadWZ || ic == kPlotEFTT6QuadWZ ||
      ic == kPlotEFTT7QuadWZ || ic == kPlotEFTM2IntWZ  ||
      ic == kPlotEFTM3IntWZ  || ic == kPlotEFTM4IntWZ  ||
      ic == kPlotEFTM5IntWZ  || ic == kPlotEFTT5IntWZ  ||
      ic == kPlotEFTT6IntWZ  || ic == kPlotEFTT7IntWZ  
    );
  }
  
  int getEFTIntCategory(TString op)
    {
        op.ToUpper();
    
        if(op == "M0") return kPlotEFTM0Int;
        if(op == "M1") return kPlotEFTM1Int;
        if(op == "M7") return kPlotEFTM7Int;
        if(op == "S0") return kPlotEFTS0Int;
        if(op == "T0") return kPlotEFTT0Int;
        if(op == "T1") return kPlotEFTT1Int;
        if(op == "T2") return kPlotEFTT2Int;
        if(op == "M2") return kPlotEFTM2IntWZ;
        if(op == "M3") return kPlotEFTM3IntWZ;
        if(op == "M4") return kPlotEFTM4IntWZ;
        if(op == "M5") return kPlotEFTM5IntWZ;
        if(op == "T5") return kPlotEFTT5IntWZ;
        if(op == "T6") return kPlotEFTT6IntWZ;
        if(op == "T7") return kPlotEFTT7IntWZ;
    
        return -1;
    }
    
    
    int getEFTQuadCategory(TString op)
    {
        op.ToUpper();
    
        if(op == "M0") return kPlotEFTM0Quad;
        if(op == "M1") return kPlotEFTM1Quad;
        if(op == "M7") return kPlotEFTM7Quad;
        if(op == "S0") return kPlotEFTS0Quad;
        if(op == "T0") return kPlotEFTT0Quad;
        if(op == "T1") return kPlotEFTT1Quad;
        if(op == "T2") return kPlotEFTT2Quad;
        if(op == "M2") return kPlotEFTM2QuadWZ;
        if(op == "M3") return kPlotEFTM3QuadWZ;
        if(op == "M4") return kPlotEFTM4QuadWZ;
        if(op == "M5") return kPlotEFTM5QuadWZ;
        if(op == "T5") return kPlotEFTT5QuadWZ;
        if(op == "T6") return kPlotEFTT6QuadWZ;
        if(op == "T7") return kPlotEFTT7QuadWZ;

        return -1;
    }


void finalPlot(int nsel = 0,
               int ReBin = 1,
               TString XTitle = "N_{jets}",
               TString units = "",
               TString plotName = "histoWW_56.root",
               TString outputName = "njets",
               bool isLogY = false,
               int year = 2017,
               TString higgsLabel = "",
               double lumi = 1.0,
               bool isBlind = false,
               TString extraLabel = "",
               bool show2D = true,
               bool applyScaling = false,
               TString mlfitResult = "",
               TString channelName = "",
               bool doEFTScale = false,
               double oldvalue = 1.0,
               double newvalue = 1.0,
               int whichCondorJob = 1001,
               TString cutoff = "5000",
               bool applyBBBBSF = false,
               TString plotExtraName = "",
               TString higgs2Label = "",
               bool applySmoothing = false) {
  bool requestEFTRatio = units.Contains("EFTSB");
  if(isBlind && !requestEFTRatio) show2D = false;

  TString OUTPUT_DIR =Form("/mnt/home/mghimiray/VBSStudies/Outputs_EFT/fakerrate/50GeV/%d/%s/plots/",whichCondorJob,cutoff.Data());
  gSystem->mkdir(OUTPUT_DIR, kTRUE);
  
  bool makeRootFile = false;

  if(!plotName.Contains("2019") && plotName.Contains("VBFG"))
    makeRootFile = true;

  if(units.Contains("ROOT")) {
    makeRootFile = true;
    units = units.ReplaceAll("ROOT","");
  }

  bool isSignalStack = false;

  if(units.Contains("Stack")) {
    isSignalStack = true;
    units = units.ReplaceAll("Stack","");
  }

  bool isRemoveBSM = false;

  if(units.Contains("NoBSM")) {
    isRemoveBSM = true;
    units = units.ReplaceAll("NoBSM","");
  }

  bool doApplyBinWidth = false;

  if(units.Contains("BinWidth")) {
    doApplyBinWidth = true;
    units = units.ReplaceAll("BinWidth","");
  }


  TString axisUnits = getAxisUnits(units);

  gStyle->SetOptStat(0);

  TGaxis::SetMaxDigits(3);
  TGaxis::SetExponentOffset(-0.00, 0.00, "x");
  TGaxis::SetExponentOffset(-0.08, 0.01, "y");

  double eftScaleInt  = 1.0;
  double eftScaleQuad = 1.0;
  
  // Always tell the legend which coefficient is being plotted
  gUseEFTLegendCoeff = true;
  gEFTLegendCoeff = oldvalue;
  
  if(doEFTScale == true){
  
      double r = newvalue / oldvalue;
  
      eftScaleInt  = r;
      eftScaleQuad = r*r;
  
      // After rescaling, curves correspond to the target value
      gEFTLegendCoeff = newvalue;
  
      printf("\n");
      printf("EFT Wilson coefficient rescaling\n");
      printf("  old/generated value = %.6f\n", oldvalue);
      printf("  new/target value    = %.6f\n", newvalue);
      printf("  INT scale           = %.6f\n", eftScaleInt);
      printf("  QUAD scale          = %.6f\n", eftScaleQuad);
      printf("\n");
  }

  TH1F* _hist[nPlotCategories];

  for(int ic=0; ic<nPlotCategories; ic++)
    _hist[ic] = 0;

  TH1F* _histo_total = 0;

  StandardPlot myPlot;

  myPlot.setDoApplyBinWidth(doApplyBinWidth);
  myPlot.setLumi(lumi);
  myPlot.setLabel(XTitle);
  myPlot.addLabel(extraLabel.Data());
  myPlot.setHiggsLabel(higgsLabel.Data());
  myPlot.setHiggs2Label(higgs2Label.Data());
  myPlot.setUnits(axisUnits);

  TFile* file = new TFile(plotName, "read");

  if(!file || file->IsZombie()) {
    printf("File %s does not exist\n",plotName.Data());
    return;
  }

  double totalSystUnc = 0.0;
  double totalStatUnc = 0.0;

  double SF_yield[nPlotCategories];
  double SF_yield_unc[nPlotCategories];

  TFile *mlfit = 0;

  if(mlfitResult!="") {
    mlfit = TFile::Open(mlfitResult);
    assert(mlfit);
  }

  TH1F* hData = 0;
  TH1F* hBck  = 0;

  for(int ic=0; ic<nPlotCategories; ic++){
    _hist[ic] = (TH1F*)file->Get(Form("histo%d",ic));
  }

  _histo_total = (TH1F*)file->Get("histo_total");

  TString eftOperator = getEFTOperatorFromUnits(units);

    int idxEFTInt = -1;
    int idxQuad   = -1;
    
    if(eftOperator != ""){
      idxEFTInt = getEFTIntCategory(eftOperator);
      idxQuad   = getEFTQuadCategory(eftOperator);
    
      printf("\n");
      printf("Selected EFT operator from units = %s\n", eftOperator.Data());
      printf("  INT  category = %d : %s\n", idxEFTInt, plotBaseNames[idxEFTInt].Data());
      printf("  QUAD category = %d : %s\n", idxQuad,   plotBaseNames[idxQuad].Data());
      printf("\n");
    }
    else if(units.Contains("EFTSB")){
      printf("\n");
      printf("No EFT Int/Quad histogram will be used.\n");
      printf("\n");
    }

  if(idxEFTInt >= 0)
    printf("Found EFT interference histogram: %s (index %d)\n",
           plotBaseNames[idxEFTInt].Data(), idxEFTInt);
  else
    printf("Did not find EFT interference histogram\n");

  if(idxQuad >= 0)
    printf("Found EFT quadratic histogram: %s (index %d)\n",
           plotBaseNames[idxQuad].Data(), idxQuad);
  else
    printf("Did not find EFT quadratic histogram\n");

  int isVBS[2] = {0, 0};

  if     (plotName.Contains("fiducial6"))                                    isVBS[0] = 2;
  else if(plotName.Contains("ww_output"))                                    isVBS[0] = 3;
  else if(_hist[kPlotEWKSSWW] && _hist[kPlotEWKSSWW]->GetSumOfWeights() > 0) isVBS[0] = 1;
  else if(_hist[kPlotSignal0] && _hist[kPlotSignal0]->GetSumOfWeights() > 0) isVBS[0] = 1;
  else if(_hist[kPlotSignal1] && _hist[kPlotSignal1]->GetSumOfWeights() > 0) isVBS[0] = 1;
  else if(_hist[kPlotSignal2] && _hist[kPlotSignal2]->GetSumOfWeights() > 0) isVBS[0] = 1;
  else if(_hist[kPlotSignal3] && _hist[kPlotSignal3]->GetSumOfWeights() > 0) isVBS[0] = 1;

  if(_hist[kPlotEWKWZ] && _hist[kPlotEWKWZ]->GetSumOfWeights() > 0)
    isVBS[1] = 1;

  if(idxEFTInt >= 0)
    setOverlayStyle(_hist[idxEFTInt], kRed+1, 2, 3);

  if(idxQuad >= 0)
    setOverlayStyle(_hist[idxQuad], kBlue+1, 1, 3);

  bool hasOverlayEFT = false;

  if((idxEFTInt >= 0 && histHasAnyContent(_hist[idxEFTInt])) ||
     (idxQuad   >= 0 && histHasAnyContent(_hist[idxQuad]))) {
    hasOverlayEFT = true;
  }

  for(int ic=0; ic<nPlotCategories; ic++){

    if(!_hist[ic]) continue;

     bool isSelectedEFT = ((idxEFTInt >= 0 && ic == idxEFTInt) ||
                        (idxQuad   >= 0 && ic == idxQuad));
        bool isOtherEFT = isAnyEFTCategory(ic) && !isSelectedEFT;
        if(isOtherEFT) continue;   
        bool isOverlayHist = isSelectedEFT;

    bool keepNegativeBins = isOverlayHist;

    if(!keepNegativeBins){

      for(int i=1; i<=_hist[ic]->GetNbinsX(); i++){

        if(_hist[ic]->GetBinContent(i)<0) {
          _hist[ic]->SetBinContent(i,0);
          _hist[ic]->SetBinError(i,0);
        }
      }
    }

    if(ic == kPlotData) {

      hData = (TH1F*)_hist[ic]->Clone();

      hBck  = (TH1F*)_hist[ic]->Clone("hBck");
      hBck->Scale(0);
    }

    else if(applySmoothing &&
            _hist[ic]->GetSumOfWeights() > 0 &&
            ic != kPlotBSM &&
            ic != kPlotVG &&
            ic != kPlotSignal0 &&
            ic != kPlotSignal1 &&
            ic != kPlotSignal2 &&
            ic != kPlotSignal3 &&
            !isOverlayHist) {

      double smoothNorm = _hist[ic]->GetSumOfWeights();

      _hist[ic]->Smooth();

      if(_hist[ic]->GetSumOfWeights() > 0)
        _hist[ic]->Scale(smoothNorm/_hist[ic]->GetSumOfWeights());
    }

    if(isBlind == true && ic == kPlotData)
      continue;

    if(!(mlfitResult=="" ||
         ic == kPlotData ||
         ic == kPlotBSM ||
         isOverlayHist ||
         (ic == kPlotSignal1 && isVBS[0] == 2))) {

      SF_yield[ic]     = 1.0;
      SF_yield_unc[ic] = 0.0;

      if((TH1F*)mlfit->Get(Form("shapes_prefit/%s/%s",
                                channelName.Data(),
                                plotBaseNames[ic].Data()))) {

        double sum[3] = {0, 0, 0};

        TH1F* hFit = (TH1F*)mlfit->Get(Form("shapes_fit_s/%s/%s",
                                            channelName.Data(),
                                            plotBaseNames[ic].Data()));

        TH1F* hPreFit = (TH1F*)mlfit->Get(Form("shapes_prefit/%s/%s",
                                               channelName.Data(),
                                               plotBaseNames[ic].Data()));

        for(int i=1; i<=hFit->GetNbinsX(); i++){

          sum[2] += hFit->GetBinError(i);

          if(hFit->GetNbinsX() == _hist[ic]->GetNbinsX() &&
             applyBBBBSF == true){

            _hist[ic]->SetBinContent(i, hFit->GetBinContent(i));
            _hist[ic]->SetBinError(i,   hFit->GetBinError(i));
          }
        }

        sum[0] = hFit->GetSumOfWeights();
        sum[1] = hPreFit->GetSumOfWeights();

        if(hFit->GetNbinsX() == _hist[ic]->GetNbinsX() &&
           applyBBBBSF == true){
          // do nothing
        }
        else {
          SF_yield[ic]     = sum[0] / sum[1];
          SF_yield_unc[ic] = sum[2] / sum[0];
        }

        printf("POST FIT SFs: SF[%s] = %.3f +/- %.3f | %.3f\n",
               plotBaseNames[ic].Data(),
               SF_yield[ic],
               SF_yield_unc[ic],
               hFit->GetSumOfWeights()/hPreFit->GetSumOfWeights());
      }

      _hist[ic]->Scale(SF_yield[ic]);

      totalSystUnc += TMath::Power(_hist[ic]->GetSumOfWeights()*SF_yield_unc[ic],2);

      for(int i=1; i<=_hist[ic]->GetNbinsX(); i++){

        double theStat = _hist[ic]->GetBinError(i);
        double theSyst = _hist[ic]->GetBinContent(i)*SF_yield_unc[ic];

        totalStatUnc += TMath::Power(theStat,2);

        _hist[ic]->SetBinError(i,
          TMath::Min(TMath::Sqrt(TMath::Power(theStat,2)+TMath::Power(theSyst,2)),
                     _hist[ic]->GetBinContent(i)));
      }
    }

    if(ic != kPlotData)
      _hist[ic]->Scale(lumi);

    if(idxEFTInt >= 0 && ic == idxEFTInt){

          _hist[ic]->Scale(eftScaleInt);
        
          // Flip only T0/T1/T2 interference histograms
          if(shouldFlipEFTInterference(eftOperator)){
            _hist[ic]->Scale(-1.0);
        
            printf("Flipped EFT INT sign for %s: %s\n",
                   eftOperator.Data(),
                   plotBaseNames[ic].Data());
          }
        
          printf("Applied EFT INT scaling to %s: %.6f\n",
                 plotBaseNames[ic].Data(),
                 eftScaleInt);
        }

    if(idxQuad >= 0 && ic == idxQuad){
      _hist[ic]->Scale(eftScaleQuad);

      printf("Applied EFT QUAD scaling to %s: %.6f\n",
             plotBaseNames[ic].Data(),
             eftScaleQuad);
    }

    if(printYieldsBinByBin && histHasAnyContent(_hist[ic])){

      printf("Yields(%s) = %.3f\n",
             plotBaseNames[ic].Data(),
             _hist[ic]->GetSumOfWeights());

      for(int i=1; i<=_hist[ic]->GetNbinsX(); i++){
        printf("%7.3f +/- %.3f\n",
               _hist[ic]->GetBinContent(i),
               _hist[ic]->GetBinError(i));
      }
    }

    if(isRemoveBSM && ic == kPlotBSM)
      _hist[ic]->Scale(0);

    if(!isOverlayHist){

      if(ic == kPlotggWW && _hist[ic]) {
        _hist[kPlotqqWW]->Add(_hist[ic]);
        _hist[ic]->Scale(0);
      }

      if(ic == kPlotTW && _hist[ic]) {
        _hist[kPlotTT]->Add(_hist[ic]);
        _hist[ic]->Scale(0);
      }

      else if(isVBS[0] == 2 && ic == kPlotSignal1) {
        _hist[kPlotBSM]->Add(_hist[ic]);
        _hist[ic]->Scale(0);
      }


      else if(isVBS[0] == 1 && ic == kPlotSignal0 && !makeRootFile) {
        _hist[kPlotEWKSSWW]->Add(_hist[ic]);
        _hist[ic]->Scale(0);
      }

      else if(isVBS[0] == 1 && ic == kPlotSignal1 && !makeRootFile) {
        _hist[kPlotEWKSSWW]->Add(_hist[ic]);
        _hist[ic]->Scale(0);
      }

      else if(isVBS[0] == 1 && ic == kPlotSignal2 && !makeRootFile) {
        _hist[kPlotEWKSSWW]->Add(_hist[ic]);
        _hist[ic]->Scale(0);
      }

      else if(isVBS[0] == 1 && ic == kPlotSignal3 && !makeRootFile) {
        _hist[kPlotEWKSSWW]->Add(_hist[ic]);
        _hist[ic]->Scale(0);
      }

      else if(isVBS[1] == 1 && ic == kPlotggWW) {
        _hist[kPlotEWKWZ]->Add(_hist[ic]);
        _hist[ic]->Scale(0);
      }

      else if(isVBS[0] == 3 && ic == kPlotSignal0 && _hist[ic]) {
        _hist[kPlotqqWW]->Add(_hist[ic]);
        _hist[ic]->Scale(0);
      }

      else if(isVBS[0] == 3 && ic == kPlotSignal1 && _hist[ic]) {
        _hist[kPlotqqWW]->Add(_hist[ic]);
        _hist[ic]->Scale(0);
      }

      else if(isVBS[0] == 3 && ic == kPlotSignal2 && _hist[ic]) {
        _hist[kPlotqqWW]->Add(_hist[ic]);
        _hist[ic]->Scale(0);
      }

      else if(isVBS[0] == 3 && ic == kPlotSignal3 && _hist[ic]) {
        _hist[kPlotqqWW]->Add(_hist[ic]);
        _hist[ic]->Scale(0);
      }

      else if(isVBS[0] == 3 && ic == kPlotSignal4 && _hist[ic]) {
        _hist[kPlotqqWW]->Add(_hist[ic]);
        _hist[ic]->Scale(0);
      }

      else if(isVBS[0] == 3 && ic == kPlotSignal5 && _hist[ic]) {
        _hist[kPlotqqWW]->Add(_hist[ic]);
        _hist[ic]->Scale(0);
      }
    }
  }

  hasOverlayEFT = false;

  if((idxEFTInt >= 0 && histHasAnyContent(_hist[idxEFTInt])) ||
     (idxQuad   >= 0 && histHasAnyContent(_hist[idxQuad]))) {
    hasOverlayEFT = true;
  }

  for(int ic=0; ic<nPlotCategories; ic++){

    if(!_hist[ic]) continue;

    bool isSelectedEFT = ((idxEFTInt >= 0 && ic == idxEFTInt) ||
                        (idxQuad   >= 0 && ic == idxQuad));
        bool isOtherEFT = isAnyEFTCategory(ic) && !isSelectedEFT;
        if(isOtherEFT) continue;   
        bool isOverlayHist = isSelectedEFT;

    if(ic != kPlotData &&
       ic != kPlotBSM &&
       ic != kPlotSignal0 &&
       ic != kPlotSignal1 &&
       ic != kPlotSignal2 &&
       ic != kPlotSignal3 &&
       !isOverlayHist) {

      hBck->Add(_hist[ic]);

      if(mlfitResult==""){
        for(int i=1; i<=_hist[ic]->GetNbinsX(); i++){
          totalStatUnc += TMath::Power(_hist[ic]->GetBinError(i),2);
        }
      }
    }
  }

  if(_histo_total && !hasOverlayEFT){

    for(int i=1; i<=hBck->GetNbinsX(); i++){

      printf("(%2d) %7.1f +/- %5.1f | %7.1f +/- %5.1f\n",
             i,
             hBck->GetBinContent(i),
             hBck->GetBinError(i),
             _histo_total->GetBinContent(i),
             _histo_total->GetBinError(i));

      if(hBck->GetBinContent(i) > 0 &&
         TMath::Abs(hBck->GetBinContent(i)-_histo_total->GetBinContent(i))/
         hBck->GetBinContent(i) > 0.01) {
        printf("Big difference!\n");
      }

      hBck->SetBinError(i,_histo_total->GetBinError(i));
    }
  }

  if(printYieldsBinByBin && hBck->GetSumOfWeights() > 0){

    printf("Yields(Bck) = %.3f\n",hBck->GetSumOfWeights());

    for(int i=1; i<=hBck->GetNbinsX(); i++){
      printf("%7.3f +/- %.3f\n",
             hBck->GetBinContent(i),
             hBck->GetBinError(i));
    }
  }

  TFile* fileExtra = 0;

  if(plotExtraName != ""){

    fileExtra = new TFile(plotExtraName, "read");

    _hist[kPlotSignal0] = (TH1F*)fileExtra->Get(Form("histo%d",kPlotBSM));
    _hist[kPlotSignal0]->SetNameTitle(Form("histo%d",kPlotSignal0),
                                      Form("histo%d",kPlotSignal0));

    for(int i=1; i<=_hist[kPlotSignal0]->GetNbinsX(); i++){
      if(_hist[kPlotSignal0]->GetBinContent(i)<0)
        _hist[kPlotSignal0]->SetBinContent(i,0);
    }

    if(isVBS[0] == 2){

      _hist[kPlotSignal1] = (TH1F*)fileExtra->Get(Form("histo%d",kPlotSignal1));

      for(int i=1; i<=_hist[kPlotSignal1]->GetNbinsX(); i++){
        if(_hist[kPlotSignal1]->GetBinContent(i)<0)
          _hist[kPlotSignal1]->SetBinContent(i,0);
      }

      _hist[kPlotSignal0]->Add(_hist[kPlotSignal1]);
    }

    myPlot.setMCHist(kPlotSignal0, _hist[kPlotSignal0]);
  }

  if(!hBck || !hData) return;

  if(hBck->GetSumOfWeights() <= 0 ||
     (isBlind == false && hData->GetSumOfWeights() <= 0))
    return;

  double dataBkgScale = hData->GetSumOfWeights()/hBck->GetSumOfWeights();

  double daUnc = 1.0;

  if(hData->GetSumOfWeights() > 0)
    daUnc = 1/hData->GetSumOfWeights();

  double mcUnc = (totalStatUnc+totalSystUnc)/
                 hBck->GetSumOfWeights()/
                 hBck->GetSumOfWeights();

  printf("%s data/bck: %f / %f +/- %f/%f/%f = %f +/- %f\n",
         plotName.Data(),
         hData->GetSumOfWeights(),
         hBck->GetSumOfWeights(),
         TMath::Sqrt(totalStatUnc),
         TMath::Sqrt(totalSystUnc),
         TMath::Sqrt(totalStatUnc+totalSystUnc),
         dataBkgScale,
         TMath::Sqrt(daUnc+mcUnc)*dataBkgScale);

  if(applyScaling == true)
    hBck->Scale(dataBkgScale);

  for(int ic=0; ic<nPlotCategories; ic++){

    if(!_hist[ic]) continue;

    if(isBlind == true && ic == kPlotData)
      continue;

    bool isSelectedEFT = ((idxEFTInt >= 0 && ic == idxEFTInt) ||
                        (idxQuad   >= 0 && ic == idxQuad));
        bool isOtherEFT = isAnyEFTCategory(ic) && !isSelectedEFT;
        if(isOtherEFT) continue;   
        bool isOverlayHist = isSelectedEFT;

    if(applyScaling == true &&
       ic != kPlotData &&
       ic != kPlotBSM &&
       !isOverlayHist)
      _hist[ic]->Scale(dataBkgScale);

    if(ic == kPlotBSM && higgsLabel == "W_{L}W_{L}") {
      _hist[ic]->Scale(10.0);
      myPlot.setHiggsLabel("W_{L}W_{L} x 10");
    }

    if(isOverlayHist){
      if(histHasAnyContent(_hist[ic]))
        myPlot.setMCHist(ic, _hist[ic]);
    }
    else {
      if(_hist[ic]->GetSumOfWeights() > 0)
        myPlot.setMCHist(ic, _hist[ic]);
    }
  }

  myPlot.setAllHist(hBck);

  if(hasOverlayEFT)
    myPlot.setOverlaid(true);
  else
    myPlot.setOverlaid(false);

  if(isSignalStack == true){

    if(_hist[kPlotSignal0] && _hist[kPlotSignal0]->GetSumOfWeights() > 0) {
      _hist[kPlotSignal0]->Add(hBck);
      myPlot.setMCHist(kPlotSignal0, _hist[kPlotSignal0]);
    }

    if(_hist[kPlotBSM] && _hist[kPlotBSM]->GetSumOfWeights() > 0) {
      _hist[kPlotBSM]->Add(hBck);
      myPlot.setMCHist(kPlotBSM, _hist[kPlotBSM]);
    }
  }

  TCanvas* c1 = new TCanvas("c1", "c1", 5, 5, 500, 500);

  double maxRatio = 0.0;
  double minRatio = 1.0;

  if(show2D==false){

    if(isLogY == true) c1->SetLogy();
    if(isLogX == true) c1->SetLogx();

    myPlot.Draw(ReBin);
    cmsstyle::CMS_lumi(c1, 11);
  }
  else {

    c1->SetBottomMargin(0.1);
    c1->cd();

    TPad *pad1 = new TPad("pad1", "pad1",0.00,0.30,1.00,1.00);
    TPad *pad2 = new TPad("pad2", "pad2",0.00,0.00,1.00,0.29);

    pad1->SetBottomMargin(0);
    pad2->SetTopMargin(0);
    pad2->SetBottomMargin(0.3);

    pad1->Draw();
    pad2->Draw();

    pad1->cd();
    pad1->RedrawAxis();

    if(isLogY == true) c1->SetLogy();
    if(isLogY == true) pad1->SetLogy();

    if(isLogX == true) c1->SetLogx();
    if(isLogX == true) pad1->SetLogx();

    if(isLogSpecial) {
      c1->SetLogx();
      pad1->SetLogx();
      pad2->SetLogx();
    }

    float theLumi = 999;
    TString theYear = Form("%d",year);

    if     (year == 2022)  {theLumi = 34.8; theYear = Form("%d",2022);}
    else if(year == 20220) {theLumi = 8.1;}
    else if(year == 20221) {theLumi = 26.7;}

    if     (year == 2023)  {theLumi = 27.1; theYear = Form("%d",2023);}
    else if(year == 20230) {theLumi = 17.6;}
    else if(year == 20231) {theLumi = 9.5;}
    else if(year == 2027)  {theLumi = 308; theYear = Form("Run 3");}
    else if(year == 2024) {theLumi = 109; theYear = Form("%d",2024);}
    else if(year == 20250) {theLumi = 107; theYear = Form("%d",2025);}

    myPlot.Draw(ReBin);

    cmsstyle::SetExtraText("");
    cmsstyle::SetLumi(theLumi, "fb", theYear.Data(), 0);
    cmsstyle::SetEnergy(13.6);
    cmsstyle::CMS_lumi(pad1, 11);

    pad2->cd();
    pad2->RedrawAxis();

    hBck->Rebin(ReBin);
    hData->Rebin(ReBin);

    TH1D* hTotalDivision = (TH1D*) hData->Clone();
    hTotalDivision->Reset();

    TH1D* hDataDivision = (TH1D*) hData->Clone();
    hDataDivision->Reset();

    TH1D* hRatio = (TH1D*) hData->Clone();
    hRatio->Reset();

    TH1D* hBand = (TH1D*) hData->Clone();
    hBand->Reset();

    hDataDivision->Add(hData);
    hTotalDivision->Add(hBck);

    hRatio->Add(hDataDivision);
    hRatio->Divide(hTotalDivision);

    bool showPulls = false;
    bool useGarwood = false;

    if(showPulls) atributes(hRatio,XTitle.Data(),"Pull",units.Data());
    else          atributes(hRatio,XTitle.Data(),"Data/SM",units.Data());

    if(showPulls) atributes(hBand,XTitle.Data(),"Pull",units.Data());
    else          atributes(hBand,XTitle.Data(),"Data/SM",units.Data());


    bool doEFTRatio = units.Contains("EFTSB");

    if(doEFTRatio){
    
      TH1D* hBSM = (TH1D*) hData->Clone("hBSM_ratio");
      hBSM->Reset();
    
      if(idxEFTInt >= 0 && _hist[idxEFTInt]){

          TH1F* hIntAbs = (TH1F*) _hist[idxEFTInt]->Clone("hIntAbs_ratio");
          hIntAbs->SetDirectory(0);
        
          for(int ib=1; ib<=hIntAbs->GetNbinsX(); ib++){
            double c = hIntAbs->GetBinContent(ib);
            hIntAbs->SetBinContent(ib, std::fabs(c));
          }
        
          hBSM->Add(hIntAbs);
        }
    
      if(idxQuad >= 0 && _hist[idxQuad]){
        hBSM->Add(_hist[idxQuad]);
      }
    
      hDataDivision->Reset();
      hTotalDivision->Reset();
      hRatio->Reset();
      hBand->Reset();
    
      // numerator = (|INT| + QUAD)^2
      hDataDivision->Add(hBSM);
      hDataDivision->Multiply(hBSM);

      // denominator = SM + all normal backgrounds
      hTotalDivision->Add(hBck);
    
      hRatio->Add(hDataDivision);
      hRatio->Divide(hTotalDivision);

      for(int ib=1; ib<=hRatio->GetNbinsX(); ib++){

          double chi2bin = hRatio->GetBinContent(ib);
        
          double zbin = 0.0;
        
          if(chi2bin > 0.0)
            zbin = std::sqrt(chi2bin);
        
          hRatio->SetBinContent(ib, zbin);
          hRatio->SetBinError(ib, 0.0);
        }

        
    
      if(showPulls) atributes(hRatio,XTitle.Data(),"Pull",axisUnits.Data());
      else          atributes(hRatio,XTitle.Data(),"Sig.",axisUnits.Data());
    
      if(showPulls) atributes(hBand,XTitle.Data(),"Pull",axisUnits.Data());
      else          atributes(hBand,XTitle.Data(),"Sig.",axisUnits.Data());
    }


    TGraphAsymmErrors *gStatic = new TGraphAsymmErrors(hDataDivision);
    TGraphAsymmErrors *g = new TGraphAsymmErrors(hRatio);

    for(int i=1; i<=hDataDivision->GetNbinsX(); i++){

        if(doEFTRatio){
      
          double zbin = hRatio->GetBinContent(i);
      
          hBand->SetBinContent(i, 0.0);
          hBand->SetBinError(i, 0.0);
      
          hRatio->SetBinError(i, 0.0);
      
          g->SetPoint(i-1, hRatio->GetBinCenter(i), zbin);
          g->SetPointEYlow(i-1, 0.0);
          g->SetPointEYhigh(i-1, 0.0);
          g->SetPointEXlow(i-1, 0.0);
          g->SetPointEXhigh(i-1, 0.0);
      
          if(zbin > maxRatio) maxRatio = zbin;
          if(zbin < minRatio) minRatio = zbin;
      
          printf("EFT Z %-20s bin %2d x=[%8.2f,%8.2f]  "
              "S=%10.4e  B=%10.4e  Z=%10.4e\n",
              outputName.Data(),
              i,
              hRatio->GetXaxis()->GetBinLowEdge(i),
              hRatio->GetXaxis()->GetBinUpEdge(i),
              std::sqrt(hDataDivision->GetBinContent(i)),
              hTotalDivision->GetBinContent(i),
              zbin);
      
          continue;
        }
      
      if(showPulls){

        double pull = 0.0;

        if(useGarwood == false){

          if((hDataDivision->GetBinError(i) > 0 ||
              hTotalDivision->GetBinError(i) > 0) &&
             hDataDivision->GetBinContent(i) > 0){

            pull = (hDataDivision->GetBinContent(i)-hTotalDivision->GetBinContent(i))/
                   sqrt(hDataDivision->GetBinError(i)*hDataDivision->GetBinError(i)+
                        hTotalDivision->GetBinError(i)*hTotalDivision->GetBinError(i));
          }
        }
        else {

          pull = TMath::Sqrt(2)*
                 TMath::ErfInverse(-1+2*ROOT::Math::poisson_cdf(hDataDivision->GetBinContent(i),
                                                                hTotalDivision->GetBinContent(i)));
        }

        hRatio->SetBinContent(i,pull);
        hRatio->SetBinError(i,1.0);

        if(printRatios)
          printf("pull(%3d): da: %f pred: %f --> %f\n",
                 i,
                 hDataDivision->GetBinContent(i),
                 hTotalDivision->GetBinContent(i),
                 pull);
      }
      else {

        hBand->SetBinContent(i,1);

        if(hTotalDivision->GetBinContent(i) > 0)
          hBand->SetBinError(i,hTotalDivision->GetBinError(i)/hTotalDivision->GetBinContent(i));
        else
          hBand->SetBinError(i,0);

        hTotalDivision->SetBinError(i,0);

        double N = gStatic->GetY()[i-1];
        double alpha = (1-0.6827);

        double L = (N==0) ? 0 : (ROOT::Math::gamma_quantile(alpha/2,N,1.));
        double U = ROOT::Math::gamma_quantile_c(alpha/2,N+1,1);

        if(N != hDataDivision->GetBinContent(i))
          cout << "PROBLEM" << endl;

        double diffUp   = U-double(N);
        double diffDown = double(N)-L;

        double pull = 1.0;
        double pullerr = 0.0;

        if(hDataDivision->GetBinContent(i) &&
           hTotalDivision->GetBinContent(i) > 0){

          pull = hDataDivision->GetBinContent(i)/
                 hTotalDivision->GetBinContent(i);

          pullerr = pull*(diffUp+diffDown)/2/
                    hDataDivision->GetBinContent(i);

          g->SetPointEYlow (i-1, pull*diffDown/hDataDivision->GetBinContent(i));
          g->SetPointEYhigh(i-1, pull*diffUp  /hDataDivision->GetBinContent(i));
        }

        else if(hTotalDivision->GetBinContent(i) > 0){

          pull = hDataDivision->GetBinContent(i)/
                 hTotalDivision->GetBinContent(i);

          pullerr = diffUp/hTotalDivision->GetBinContent(i);

          g->SetPointEYlow (i-1, 0);
          g->SetPointEYhigh(i-1, diffUp/hTotalDivision->GetBinContent(i));
        }

        else {

          g->SetPointEYlow (i-1, 0);
          g->SetPointEYhigh(i-1, 0);
        }

        g->SetPointEXlow (i-1, 0);
        g->SetPointEXhigh(i-1, 0);

        if(pull+pullerr > maxRatio) maxRatio = pull+pullerr;
        if(pull-pullerr < minRatio) minRatio = pull-pullerr;

        if(printRatios) {
          printf("ratio(%3d): %f +/- %f --> da: %f +/- %f (%f) pred: %f +/- %f\n",
                 i,
                 pull,
                 pullerr,
                 hDataDivision->GetBinContent(i),
                 hDataDivision->GetBinError(i),
                 (diffUp+diffDown)/2,
                 hTotalDivision->GetBinContent(i),
                 hTotalDivision->GetBinError(i));
        }
      }
    }


        double theLines[2] = {1.0, 0.5};

        if(showPulls) {
          theLines[0] = 0.0;
          theLines[1] = 1.5;
        }

        Double_t dy = TMath::Max(TMath::Abs(hRatio->GetMaximum()),
                                 TMath::Abs(hRatio->GetMinimum())) + theLines[1];

        // --------------------------------------------------
        // Set lower-panel y range BEFORE drawing hBand
        // --------------------------------------------------
        if(doEFTRatio){

            pad2->SetLogy(false);
            setAutoRatioRange(hBand, hRatio, true);
          
            printf("DEBUG Z RANGE %s : hRatio min = %.4e, hRatio max = %.4e\n",
                   outputName.Data(),
                   hRatio->GetMinimum(),
                   hRatio->GetMaximum());
          }
        else {

          minRatio = TMath::Min(TMath::Max(minRatio-0.03,0.000),0.810);
          maxRatio = TMath::Min(TMath::Max(maxRatio+0.03,1.190),2.999);

          if(showPulls){
            hBand->SetMinimum(-dy);
            hBand->SetMaximum(+dy);
          }
          else {
            hBand->SetMinimum(minRatio);
            hBand->SetMaximum(maxRatio);
          }
        }

        hBand->SetFillColor(12);
        hBand->SetFillStyle(3345);
        hBand->SetMarkerSize(0);
        hBand->SetLineWidth(0);
        hBand->Draw("E2");

        g->Draw("P,same,z");

        // Do not draw a y=0 baseline for the EFT chi2 log panel.
        // A log-y axis cannot draw zero.
        if(!doEFTRatio){

          TLine* baseline = new TLine(hRatio->GetXaxis()->GetXmin(),
                                      theLines[0],
                                      hRatio->GetXaxis()->GetXmax(),
                                      theLines[0]);

          baseline->SetLineStyle(kDashed);
          baseline->Draw();
        }

        hBand->GetYaxis()->CenterTitle();

        pad2->Modified();
        pad2->Update();

    eraselabel(pad1,hData->GetXaxis()->GetLabelSize());
  }

  char CommandToExec[300];
  sprintf(CommandToExec,"mkdir -p plots");
  gSystem->Exec(CommandToExec);

  if(strcmp(outputName.Data(),"") != 0){

    TString myOutputFile;

    outputName = Form("%s_%d",outputName.Data(),year);

    myOutputFile = TString(OUTPUT_DIR) + "/" + outputName + ".eps";
    c1->SaveAs(myOutputFile.Data());

    myOutputFile = TString(OUTPUT_DIR) + "/" + outputName + ".png";
    c1->SaveAs(myOutputFile.Data());

    myOutputFile = TString(OUTPUT_DIR) + "/" + outputName + ".pdf";
    c1->SaveAs(myOutputFile.Data());

    if(makeRootFile) {

      for(int i=1; i<=_hist[kPlotData]->GetNbinsX(); i++) {
        if(_hist[kPlotData]->GetBinContent(i)<0) {
          _hist[kPlotData]->SetBinContent(i,0);
          _hist[kPlotData]->SetBinError(i,0);
        }
      }

      TFile output(Form("plots/%s.root",outputName.Data()),"RECREATE");

      hBck->Scale(0.0);

      for(int ic=0; ic<nPlotCategories; ic++){

        if(!_hist[ic]) continue;

        bool isSelectedEFT = ((idxEFTInt >= 0 && ic == idxEFTInt) ||
                        (idxQuad   >= 0 && ic == idxQuad));
        bool isOtherEFT = isAnyEFTCategory(ic) && !isSelectedEFT;
        if(isOtherEFT) continue;   
        bool isOverlayHist = isSelectedEFT;

        _hist[ic]->Write();

        if(ic != kPlotData &&
           ic != kPlotBSM &&
           !isOverlayHist) {
          hBck->Add(_hist[ic]);
        }
      }

      hBck->Write();
      output.Close();
    }
  }

  bool computePU = false;

  if(computePU || plotName.Contains("_npv.root") == true){

    hBck->Scale(hData->GetSumOfWeights()/hBck->GetSumOfWeights());

    TH1D *npvWeights = (TH1D*)hData->Clone("npvWeights");
    npvWeights->Sumw2();
    npvWeights->Divide(hBck);

    for(int i=1; i<=npvWeights->GetNbinsX(); i++){

      if(npvWeights->GetBinContent(i) > 3) {

        printf("Big number in (%d): %f, set to 3\n",
               i,
               npvWeights->GetBinContent(i));

        npvWeights->SetBinContent(i,3);
      }
    }

    TFile output(Form("npvWeights_%d.root",year),"RECREATE");
    npvWeights->Write();
    output.Close();
  }
}