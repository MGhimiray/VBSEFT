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
  kPlotEFTM1Int    , //28
  kPlotEFTM1Quad   , //29
  kPlotEFTM7Int    , //30
  kPlotEFTM7Quad   , //31
  kPlotEFTS0Int    , //32
  kPlotEFTS0Quad   , //33
  kPlotEFTT0Int    , //34
  kPlotEFTT0Quad   , //35
  kPlotEFTT1Int    , //36
  kPlotEFTT1Quad   , //37
  kPlotEFTT2Int    , //38
  kPlotEFTT2Quad   , //39

  kPlotEFTM2QuadWZ , //40
  kPlotEFTM3QuadWZ , //41
  kPlotEFTM4QuadWZ , //42
  kPlotEFTM5QuadWZ , //43
  kPlotEFTT5QuadWZ , //44
  kPlotEFTT6QuadWZ , //45
  kPlotEFTT7QuadWZ , //46

  kPlotEFTM2IntWZ  , //47
  kPlotEFTM3IntWZ  , //48
  kPlotEFTM4IntWZ  , //49
  kPlotEFTM5IntWZ  , //50
  kPlotEFTT5IntWZ  , //51
  kPlotEFTT6IntWZ  , //52
  kPlotEFTT7IntWZ  , //53

  nPlotCategories
};


std::map<int, TString> plotBaseNames={

  { kPlotData      , "Data" },
  { kPlotqqWW      , "qqWW" },
  { kPlotggWW      , "ggWW" },
  { kPlotTT        , "TT" },
  { kPlotTW        , "TW" },
  { kPlotDY        , "DY" },
  { kPlotEWKSSWW   , "EWKSSWW" },
  { kPlotQCDSSWW   , "QCDSSWW" },
  { kPlotEWKWZ     , "EWKWZ" },
  { kPlotWZ        , "WZ" },
  { kPlotZZ        , "ZZ" },
  { kPlotNonPrompt , "NonPrompt" },
  { kPlotVVV       , "VVV" },
  { kPlotTVX       , "TVX" },
  { kPlotVG        , "VG" },
  { kPlotHiggs     , "Higgs" },
  { kPlotWS        , "WS" },
  { kPlotOther     , "Other" },
  { kPlotEM        , "EM" },
  { kPlotBSM       , "BSM" },

  { kPlotSignal0   , "Signal0" },
  { kPlotSignal1   , "Signal1" },
  { kPlotSignal2   , "Signal2" },
  { kPlotSignal3   , "Signal3" },
  { kPlotSignal4   , "Signal4" },
  { kPlotSignal5   , "Signal5" },

  { kPlotEFTM0Int    , "EFTM0Int" },
  { kPlotEFTM0Quad   , "EFTM0Quad" },
  { kPlotEFTM1Int    , "EFTM1Int" },
  { kPlotEFTM1Quad   , "EFTM1Quad" },
  { kPlotEFTM7Int    , "EFTM7Int" },
  { kPlotEFTM7Quad   , "EFTM7Quad" },
  { kPlotEFTS0Int    , "EFTS0Int" },
  { kPlotEFTS0Quad   , "EFTS0Quad" },
  { kPlotEFTT0Int    , "EFTT0Int" },
  { kPlotEFTT0Quad   , "EFTT0Quad" },
  { kPlotEFTT1Int    , "EFTT1Int" },
  { kPlotEFTT1Quad   , "EFTT1Quad" },
  { kPlotEFTT2Int    , "EFTT2Int" },
  { kPlotEFTT2Quad   , "EFTT2Quad" },

  { kPlotEFTM2QuadWZ , "EFTM2QuadWZ" },
  { kPlotEFTM3QuadWZ , "EFTM3QuadWZ" },
  { kPlotEFTM4QuadWZ , "EFTM4QuadWZ" },
  { kPlotEFTM5QuadWZ , "EFTM5QuadWZ" },
  { kPlotEFTT5QuadWZ , "EFTT5QuadWZ" },
  { kPlotEFTT6QuadWZ , "EFTT6QuadWZ" },
  { kPlotEFTT7QuadWZ , "EFTT7QuadWZ" },

  { kPlotEFTM2IntWZ  , "EFTM2IntWZ" },
  { kPlotEFTM3IntWZ  , "EFTM3IntWZ" },
  { kPlotEFTM4IntWZ  , "EFTM4IntWZ" },
  { kPlotEFTM5IntWZ  , "EFTM5IntWZ" },
  { kPlotEFTT5IntWZ  , "EFTT5IntWZ" },
  { kPlotEFTT6IntWZ  , "EFTT6IntWZ" },
  { kPlotEFTT7IntWZ  , "EFTT7IntWZ" }

};


std::map<int, int> plotColors={

  { kPlotData      , kBlack},

  { kPlotqqWW      , cmsstyle::p10::kBlue},
  { kPlotggWW      , cmsstyle::p10::kBlue-3},
  { kPlotTT        , cmsstyle::p10::kYellow},
  { kPlotTW        , cmsstyle::p10::kYellow-3},
  { kPlotDY        , kYellow},

  { kPlotEWKSSWW   , cmsstyle::p10::kBlue},
  { kPlotQCDSSWW   , cmsstyle::p10::kBlue-3},
  { kPlotEWKWZ     , cmsstyle::p10::kYellow},

  { kPlotWZ        , cmsstyle::p10::kRed},
  { kPlotZZ        , cmsstyle::p10::kCyan},
  { kPlotNonPrompt , cmsstyle::p10::kViolet},
  { kPlotVVV       , cmsstyle::p10::kGray},
  { kPlotTVX       , cmsstyle::p10::kOrange},
  { kPlotVG        , cmsstyle::p10::kBrown},
  { kPlotHiggs     , cmsstyle::p10::kGreen},
  { kPlotWS        , cmsstyle::p10::kAsh},
  { kPlotOther     , cmsstyle::p10::kAsh},
  { kPlotEM        , cmsstyle::p10::kBlue},

  { kPlotBSM       , kAzure+1},
  { kPlotSignal0   , kAzure+2},
  { kPlotSignal1   , kAzure+3},
  { kPlotSignal2   , kAzure+4},
  { kPlotSignal3   , kAzure+5},
  { kPlotSignal4   , kAzure+6},
  { kPlotSignal5   , kAzure+7},

  { kPlotEFTM0Int    , kMagenta},
  { kPlotEFTM0Quad   , kPink},

  { kPlotEFTM1Int    , kMagenta-3},
  { kPlotEFTM1Quad   , kPink-3},

  { kPlotEFTM7Int    , kMagenta-6},
  { kPlotEFTM7Quad   , kPink-6},

  { kPlotEFTS0Int    , kMagenta-9},
  { kPlotEFTS0Quad   , kPink-9},

  { kPlotEFTT0Int    , kMagenta-12},
  { kPlotEFTT0Quad   , kPink-12},

  { kPlotEFTT1Int    , kMagenta-15},
  { kPlotEFTT1Quad   , kPink-15},

  { kPlotEFTT2Int    , kMagenta-18},
  { kPlotEFTT2Quad   , kPink-18},

  { kPlotEFTM2QuadWZ , kPink-20},
  { kPlotEFTM3QuadWZ , kPink-21},
  { kPlotEFTM4QuadWZ , kPink-22},
  { kPlotEFTM5QuadWZ , kPink-23},

  { kPlotEFTT5QuadWZ , kPink-24},
  { kPlotEFTT6QuadWZ , kPink-25},
  { kPlotEFTT7QuadWZ , kPink-26},

  { kPlotEFTM2IntWZ  , kMagenta-20},
  { kPlotEFTM3IntWZ  , kMagenta-21},
  { kPlotEFTM4IntWZ  , kMagenta-22},
  { kPlotEFTM5IntWZ  , kMagenta-23},

  { kPlotEFTT5IntWZ  , kMagenta-24},
  { kPlotEFTT6IntWZ  , kMagenta-25},
  { kPlotEFTT7IntWZ  , kMagenta-26}

};


std::map<int, TString> plotNames={

  { kPlotData      , "Data"},
  { kPlotqqWW      , "WW"},
  { kPlotggWW      , "gg #rightarrow WW"},
  { kPlotTT        , "Top quark"},
  { kPlotTW        , "tW"},
  { kPlotDY        , "Drell-Yan"},

  { kPlotEWKSSWW   , "W^{#pm}W^{#pm}"},
  { kPlotQCDSSWW   , "QCD W^{#pm}W^{#pm}"},
  { kPlotEWKWZ     , "EWK WZ"},

  { kPlotWZ        , "WZ"},
  { kPlotZZ        , "ZZ"},
  { kPlotNonPrompt , "Nonprompt"},
  { kPlotVVV       , "VVV"},
  { kPlotTVX       , "tVx"},
  { kPlotVG        , "V#gamma"},
  { kPlotHiggs     , "Higgs boson"},
  { kPlotWS        , "Wrong sign"},
  { kPlotOther     , "Other bkg."},
  { kPlotEM        , "Nonresonant"},
  { kPlotBSM       , "BSM"},

  { kPlotSignal0   , "Signal 0"},
  { kPlotSignal1   , "Signal 1"},
  { kPlotSignal2   , "Signal 2"},
  { kPlotSignal3   , "Signal 3"},
  { kPlotSignal4   , "Signal 4"},
  { kPlotSignal5   , "Signal 5"},

  { kPlotEFTM0Int    , "EFT M0 Int"},
  { kPlotEFTM0Quad   , "EFT M0 Quad"},

  { kPlotEFTM1Int    , "EFT M1 Int"},
  { kPlotEFTM1Quad   , "EFT M1 Quad"},

  { kPlotEFTM7Int    , "EFT M7 Int"},
  { kPlotEFTM7Quad   , "EFT M7 Quad"},

  { kPlotEFTS0Int    , "EFT S0 Int"},
  { kPlotEFTS0Quad   , "EFT S0 Quad"},

  { kPlotEFTT0Int    , "EFT T0 Int"},
  { kPlotEFTT0Quad   , "EFT T0 Quad"},

  { kPlotEFTT1Int    , "EFT T1 Int"},
  { kPlotEFTT1Quad   , "EFT T1 Quad"},

  { kPlotEFTT2Int    , "EFT T2 Int"},
  { kPlotEFTT2Quad   , "EFT T2 Quad"},

  { kPlotEFTM2QuadWZ , "EFT M2 Quad WZ"},
  { kPlotEFTM3QuadWZ , "EFT M3 Quad WZ"},
  { kPlotEFTM4QuadWZ , "EFT M4 Quad WZ"},
  { kPlotEFTM5QuadWZ , "EFT M5 Quad WZ"},

  { kPlotEFTT5QuadWZ , "EFT T5 Quad WZ"},
  { kPlotEFTT6QuadWZ , "EFT T6 Quad WZ"},
  { kPlotEFTT7QuadWZ , "EFT T7 Quad WZ"},

  { kPlotEFTM2IntWZ  , "EFT M2 Int WZ"},
  { kPlotEFTM3IntWZ  , "EFT M3 Int WZ"},
  { kPlotEFTM4IntWZ  , "EFT M4 Int WZ"},
  { kPlotEFTM5IntWZ  , "EFT M5 Int WZ"},

  { kPlotEFTT5IntWZ  , "EFT T5 Int WZ"},
  { kPlotEFTT6IntWZ  , "EFT T6 Int WZ"},
  { kPlotEFTT7IntWZ  , "EFT T7 Int WZ"}

};