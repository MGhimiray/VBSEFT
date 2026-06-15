#include "TH1D.h"
#include "TH2D.h"
#include "cmsstyle.C"

enum plotCategory {
  kPlotData      , // 0
  kPlotqqWW      , // 1
  kPlotggWW      , // 2
  kPlotTT        , // 3
  kPlotTW        , // 4
  kPlotDY        , // 5
  kPlotEWKSSWW   , // 6
  kPlotQCDSSWW   , // 7
  kPlotEWKWZ     , // 8
  kPlotWZ        , // 9
  kPlotZZ        , //10
  kPlotNonPrompt , //11
  kPlotVVV       , //12
  kPlotTVX       , //13
  kPlotVG        , //14
  kPlotHiggs     , //15
  kPlotWS        , //16
  kPlotOther     , //17
  kPlotEM        , //18
  kPlotBSM       , //19
  kPlotSignal0   , //20
  kPlotSignal1   , //21
  kPlotSignal2   , //22
  kPlotSignal3   , //23
  kPlotSignal4   , //24
  kPlotSignal5   , //25
  kPlotEFTM0Int    , //26
  kPlotEFTM0Quad   , //27
  kPlotEFTM1Int   , //28
  kPlotEFTM1Quad   , //29
  kPlotEFTM7Int   , //30
  kPlotEFTM7Quad   , //31
  kPlotEFTS0Int   , //32
  kPlotEFTS0Quad   , //33
  kPlotEFTT0Int   , //34
  kPlotEFTT0Quad   , //35
  kPlotEFTT1Int   , //36
  kPlotEFTT1Quad   , //37
  kPlotEFTT2Int   , //38
  kPlotEFTT2Quad   , //39
  nPlotCategories
};

std::map<int, TString> plotBaseNames={
  { kPlotData	   , "Data" },
  { kPlotqqWW	   , "qqWW" },
  { kPlotggWW	   , "ggWW" },
  { kPlotTT	   , "TT" },
  { kPlotTW	   , "TW" },
  { kPlotDY	   , "DY" },
  { kPlotEWKSSWW   , "EWKSSWW" },
  { kPlotQCDSSWW   , "QCDSSWW" },
  { kPlotEWKWZ     , "EWKWZ" },
  { kPlotWZ	   , "WZ" },
  { kPlotZZ	   , "ZZ" },
  { kPlotNonPrompt , "NonPrompt" },
  { kPlotVVV	   , "VVV" },
  { kPlotTVX	   , "TVX" },
  { kPlotVG	   , "VG" },
  { kPlotHiggs     , "Higgs" },
  { kPlotWS	   , "WS" },
  { kPlotOther     , "Other" },
  { kPlotEM	   , "EM" },
  { kPlotBSM	   , "BSM" },
  { kPlotSignal0   , "Signal0" },
  { kPlotSignal1   , "Signal1" },
  { kPlotSignal2   , "Signal2" },
  { kPlotSignal3   , "Signal3" },
  { kPlotSignal4   , "Signal4" },
  { kPlotSignal5   , "Signal5" },
  { kPlotEFTM0Int    , "EFTM0Int" },
  { kPlotEFTM0Quad   , "EFTM0Quad" },
  { kPlotEFTM1Int   , "EFTM1Int" },
  { kPlotEFTM1Quad   , "EFTM1Quad" },
  { kPlotEFTM7Int   , "EFTM7Int" },
  { kPlotEFTM7Quad   , "EFTM7Quad" },
  { kPlotEFTS0Int   , "EFTS0Int" },
  { kPlotEFTS0Quad   , "EFTS0Quad" },
  { kPlotEFTT0Int   , "EFTT0Int" },
  { kPlotEFTT0Quad   , "EFTT0Quad" },
  { kPlotEFTT1Int   , "EFTT1Int" },
  { kPlotEFTT1Quad   , "EFTT1Quad" },
  { kPlotEFTT2Int   , "EFTT2Int" },
  { kPlotEFTT2Quad   , "EFTT2Quad" }
}; 

std::map<int, int> plotColors={
  { kPlotData	   , kBlack},
  { kPlotqqWW	   , cmsstyle::p10::kBlue},     // 1
  { kPlotggWW	   , cmsstyle::p10::kBlue-3},   // not shown
  { kPlotTT	   , cmsstyle::p10::kYellow},   // 2
  { kPlotTW	   , cmsstyle::p10::kYellow-3}, // not shown
  { kPlotDY	   , kYellow},                  // 3 cmsstyle::p10::kAsh
  { kPlotEWKSSWW   , cmsstyle::p10::kBlue},     // 01
  { kPlotQCDSSWW   , cmsstyle::p10::kBlue-3},   // not shown
  { kPlotEWKWZ     , cmsstyle::p10::kYellow},   // 02
  { kPlotWZ	   , cmsstyle::p10::kRed},      // 4
  { kPlotZZ	   , cmsstyle::p10::kCyan},     // 5
  { kPlotNonPrompt , cmsstyle::p10::kViolet},   // 6
  { kPlotVVV	   , cmsstyle::p10::kGray},     // 7
  { kPlotTVX	   , cmsstyle::p10::kOrange},   // 8
  { kPlotVG	   , cmsstyle::p10::kBrown},    // 9
  { kPlotHiggs     , cmsstyle::p10::kGreen},    // 10
  { kPlotWS	   , cmsstyle::p10::kAsh},      // 03
  { kPlotOther     , cmsstyle::p10::kAsh},
  { kPlotEM	   , cmsstyle::p10::kBlue},     // 11
  { kPlotBSM	   , kAzure+1},
  { kPlotSignal0   , kAzure+2},
  { kPlotSignal1   , kAzure+3},
  { kPlotSignal2   , kAzure+4},
  { kPlotSignal3   , kAzure+5},
  { kPlotSignal4   , kAzure+6},
  { kPlotSignal5   , kAzure+7},
  { kPlotEFTM0Int  , kMagenta},
  { kPlotEFTM0Quad   , kPink},
  { kPlotEFTM1Int   , kMagenta-3},
  { kPlotEFTM1Quad   , kPink-3},
  { kPlotEFTM7Int   , kMagenta-6},
  { kPlotEFTM7Quad   , kPink-6},
  { kPlotEFTS0Int   , kMagenta-9},
  { kPlotEFTS0Quad   , kPink-9},
  { kPlotEFTT0Int   , kMagenta-12},
  { kPlotEFTT0Quad   , kPink-12},
  { kPlotEFTT1Int   , kMagenta-15},
  { kPlotEFTT1Quad   , kPink-15},
  { kPlotEFTT2Int   , kMagenta-18},
  { kPlotEFTT2Quad   , kPink-18}
}; 

std::map<int, TString> plotNames={
    { kPlotData      , "Data"},
    { kPlotqqWW      , "WW"},
    { kPlotggWW      , "gg #rightarrow WW"},
    { kPlotTT	     , "Top quark"},
    { kPlotTW	     , "tW"},
    { kPlotDY	     , "Drell-Yan"},
    { kPlotEWKSSWW   , "W^{#pm}W^{#pm}"},
    { kPlotQCDSSWW   , "QCD W^{#pm}W^{#pm}"},
    { kPlotEWKWZ     , "EWK WZ"},
    { kPlotWZ	     , "WZ"},
    { kPlotZZ	     , "ZZ"},
    { kPlotNonPrompt , "Nonprompt"},
    { kPlotVVV       , "VVV"},
    { kPlotTVX       , "tVx"},
    { kPlotVG	     , "V#gamma" },
    { kPlotHiggs     , "Higgs boson"},
    { kPlotWS	     , "Wrong sign"},
    { kPlotOther     , "Other bkg."},
    { kPlotEM	     , "Nonresonant"},
    { kPlotBSM       , "BSM"},
    { kPlotSignal0   , "Signal 0"},
    { kPlotSignal1   , "Signal 1"},
    { kPlotSignal2   , "Signal 2"},
    { kPlotSignal3   , "Signal 3"},
    { kPlotSignal4   , "Signal 4"},
    { kPlotSignal5   , "Signal 5"},
    { kPlotEFTM0Int    , "EFT M0 Int"},
    { kPlotEFTM0Quad   , "EFT M0 Quad"},
    { kPlotEFTM1Int   , "EFT M1 Int"},
    { kPlotEFTM1Quad   , "EFT M1 Quad"},
    { kPlotEFTM7Int   , "EFT M7 Int"},
    { kPlotEFTM7Quad   , "EFT M7 Quad"},
    { kPlotEFTS0Int   , "EFT S0 Int"},
    { kPlotEFTS0Quad   , "EFT S0 Quad"},
    { kPlotEFTT0Int   , "EFT T0 Int"},
    { kPlotEFTT0Quad   , "EFT T0 Quad"},
    { kPlotEFTT1Int   , "EFT T1 Int"},
    { kPlotEFTT1Quad   , "EFT T1 Quad"},
    { kPlotEFTT2Int   , "EFT T2 Int"},
    { kPlotEFTT2Quad   , "EFT T2 Quad"}
};
