// compare_bins.C
//
// Compare an old and a new EFT ROOT file.
//
// Example:
//
// root -l -b -q \
// 'compare_bins.C("old.root","new.root","S0")'
//
// It compares:
//
//   histo_sm
//   histo_quad_cS0
//   histo_sm_lin_quad_cS0
//
// and prints:
//   - number of bins
//   - every regular bin
//   - underflow
//   - overflow
//   - regular/full integrals
//   - last-bin comparison
//   - test whether:
//         OLD last bin ~= NEW penultimate + NEW last bin
//

#include "TFile.h"
#include "TH1.h"
#include "TString.h"

#include <iostream>
#include <iomanip>
#include <cmath>
#include <algorithm>


// ============================================================
// Small helper structure
// ============================================================

struct HistSet
{
    TH1* sm   = nullptr;
    TH1* quad = nullptr;
    TH1* full = nullptr;
};


// ============================================================
// Read histograms from one ROOT file
// ============================================================

HistSet readHistograms(
    const char* filename,
    const char* operatorName,
    const char* tag
)
{
    HistSet h;

    TFile* f = TFile::Open(filename, "READ");

    if (!f || f->IsZombie()) {
        std::cerr
            << "\nERROR: Cannot open file:\n"
            << filename
            << std::endl;

        return h;
    }

    TString quadName =
        Form("histo_quad_c%s", operatorName);

    TString fullName =
        Form("histo_sm_lin_quad_c%s", operatorName);


    TH1* hsm =
        dynamic_cast<TH1*>(f->Get("histo_sm"));

    TH1* hquad =
        dynamic_cast<TH1*>(f->Get(quadName.Data()));

    TH1* hfull =
        dynamic_cast<TH1*>(f->Get(fullName.Data()));


    if (!hsm) {
        std::cerr
            << "Missing histo_sm in "
            << filename << std::endl;
    }

    if (!hquad) {
        std::cerr
            << "Missing "
            << quadName
            << " in "
            << filename << std::endl;
    }

    if (!hfull) {
        std::cerr
            << "Missing "
            << fullName
            << " in "
            << filename << std::endl;
    }


    if (hsm) {
        h.sm = dynamic_cast<TH1*>(
            hsm->Clone(Form("sm_%s",tag))
        );
        h.sm->SetDirectory(nullptr);
    }

    if (hquad) {
        h.quad = dynamic_cast<TH1*>(
            hquad->Clone(Form("quad_%s",tag))
        );
        h.quad->SetDirectory(nullptr);
    }

    if (hfull) {
        h.full = dynamic_cast<TH1*>(
            hfull->Clone(Form("full_%s",tag))
        );
        h.full->SetDirectory(nullptr);
    }


    f->Close();
    delete f;

    return h;
}


// ============================================================
// Print one histogram completely
// ============================================================

void printHistogram(
    TH1* h,
    const char* name
)
{
    if (!h) return;

    const int nBins = h->GetNbinsX();

    std::cout
        << "\n------------------------------------------------------------\n"
        << name
        << "\n"
        << "N regular bins = "
        << nBins
        << "\n"
        << "------------------------------------------------------------\n";

    std::cout
        << std::scientific
        << std::setprecision(8);


    // Underflow
    std::cout
        << "UF"
        << "   content = "
        << std::setw(15)
        << h->GetBinContent(0)
        << "   error = "
        << std::setw(15)
        << h->GetBinError(0)
        << "\n";


    // Regular bins
    for (int i = 1; i <= nBins; ++i) {

        const double low =
            h->GetXaxis()->GetBinLowEdge(i);

        const double high =
            h->GetXaxis()->GetBinUpEdge(i);

        std::cout
            << "Bin "
            << std::setw(3)
            << i
            << "   x=["
            << std::setw(10)
            << low
            << ","
            << std::setw(10)
            << high
            << "]"
            << "   content = "
            << std::setw(15)
            << h->GetBinContent(i)
            << "   error = "
            << std::setw(15)
            << h->GetBinError(i)
            << "\n";
    }


    // Overflow
    std::cout
        << "OF"
        << "   content = "
        << std::setw(15)
        << h->GetBinContent(nBins + 1)
        << "   error = "
        << std::setw(15)
        << h->GetBinError(nBins + 1)
        << "\n";


    std::cout
        << "------------------------------------------------------------\n"
        << "Integral regular bins = "
        << h->Integral(1,nBins)
        << "\n"
        << "Integral incl. UF/OF  = "
        << h->Integral(0,nBins+1)
        << "\n"
        << "------------------------------------------------------------\n";

    std::cout
        << std::defaultfloat
        << std::setprecision(6);
}


// ============================================================
// Print only tail information
// ============================================================

void printTail(
    TH1* h,
    const char* label
)
{
    if (!h) return;

    const int n = h->GetNbinsX();

    std::cout
        << std::scientific
        << std::setprecision(8);

    std::cout
        << "\n"
        << label
        << "\n";

    // Last three regular bins if available
    const int first =
        std::max(1,n-2);

    for (int i = first; i <= n; ++i) {

        std::cout
            << "  bin "
            << i
            << " = "
            << h->GetBinContent(i)
            << " +/- "
            << h->GetBinError(i)
            << "\n";
    }

    std::cout
        << "  overflow = "
        << h->GetBinContent(n+1)
        << " +/- "
        << h->GetBinError(n+1)
        << "\n";

    std::cout
        << std::defaultfloat;
}


// ============================================================
// Compare old last bin with new last two bins
// ============================================================

void compareLastBins(
    TH1* oldH,
    TH1* newH,
    const char* label
)
{
    if (!oldH || !newH) return;

    const int nOld =
        oldH->GetNbinsX();

    const int nNew =
        newH->GetNbinsX();


    std::cout
        << "\n============================================================\n"
        << "TAIL TEST : "
        << label
        << "\n"
        << "============================================================\n";


    std::cout
        << std::scientific
        << std::setprecision(10);


    const double oldLast =
        oldH->GetBinContent(nOld);

    const double oldOverflow =
        oldH->GetBinContent(nOld+1);

    const double newLast =
        newH->GetBinContent(nNew);

    const double newPenultimate =
        (nNew >= 2)
        ? newH->GetBinContent(nNew-1)
        : 0.0;

    const double newOverflow =
        newH->GetBinContent(nNew+1);

    const double newLastTwo =
        newPenultimate + newLast;


    std::cout
        << "OLD number of bins       = "
        << nOld << "\n"
        << "NEW number of bins       = "
        << nNew << "\n\n";

    std::cout
        << "OLD last visible         = "
        << oldLast << "\n";

    std::cout
        << "OLD overflow             = "
        << oldOverflow << "\n\n";

    std::cout
        << "NEW penultimate          = "
        << newPenultimate << "\n";

    std::cout
        << "NEW last visible         = "
        << newLast << "\n";

    std::cout
        << "NEW penultimate + last   = "
        << newLastTwo << "\n";

    std::cout
        << "NEW overflow             = "
        << newOverflow << "\n\n";


    const double difference =
        oldLast - newLastTwo;

    std::cout
        << "OLD last - NEW last two  = "
        << difference
        << "\n";


    if (std::abs(oldLast) > 0.0) {

        const double relativeDifference =
            difference / oldLast * 100.0;

        std::cout
            << "Relative difference      = "
            << relativeDifference
            << " %\n";
    }


    // --------------------------------------------------------
    // Also compare old last + overflow against new last two
    // + overflow
    // --------------------------------------------------------

    const double oldTailTotal =
        oldLast + oldOverflow;

    const double newTailTotal =
        newPenultimate
        + newLast
        + newOverflow;


    std::cout
        << "\nOLD last + overflow      = "
        << oldTailTotal
        << "\n";

    std::cout
        << "NEW last2 + overflow     = "
        << newTailTotal
        << "\n";

    std::cout
        << "Difference               = "
        << oldTailTotal - newTailTotal
        << "\n";


    std::cout
        << "============================================================\n";

    std::cout
        << std::defaultfloat
        << std::setprecision(6);
}


// ============================================================
// Main function
// ============================================================

void comparebins(

    const char* oldFile =
        "old.root",

    const char* newFile =
        "new.root",

    const char* operatorName =
        "S0"
)
{
    std::cout
        << "\n\n"
        << "############################################################\n"
        << "#                                                          #\n"
        << "#          EFT OLD vs NEW BINNING COMPARISON               #\n"
        << "#                                                          #\n"
        << "############################################################\n\n";

    std::cout
        << "Operator : "
        << operatorName
        << "\n\n";

    std::cout
        << "OLD FILE:\n"
        << oldFile
        << "\n\n";

    std::cout
        << "NEW FILE:\n"
        << newFile
        << "\n";


    // ========================================================
    // Load files
    // ========================================================

    HistSet oldHist =
        readHistograms(
            oldFile,
            operatorName,
            "old"
        );

    HistSet newHist =
        readHistograms(
            newFile,
            operatorName,
            "new"
        );


    if (
        !oldHist.sm ||
        !oldHist.quad ||
        !oldHist.full ||
        !newHist.sm ||
        !newHist.quad ||
        !newHist.full
    ) {
        std::cerr
            << "\nERROR: Could not load all required histograms.\n";

        return;
    }


    // ========================================================
    // Number of bins
    // ========================================================

    std::cout
        << "\n============================================================\n"
        << "BIN COUNT\n"
        << "============================================================\n";

    std::cout
        << "OLD : "
        << oldHist.sm->GetNbinsX()
        << " bins\n";

    std::cout
        << "NEW : "
        << newHist.sm->GetNbinsX()
        << " bins\n";

    std::cout
        << "============================================================\n";


    // ========================================================
    // Print complete OLD histograms
    // ========================================================

    std::cout
        << "\n\n############################################################\n"
        << "#                         OLD FILE                         #\n"
        << "############################################################\n";

    printHistogram(
        oldHist.sm,
        "OLD : SM"
    );

    printHistogram(
        oldHist.quad,
        "OLD : QUADRATIC"
    );

    printHistogram(
        oldHist.full,
        "OLD : SM + INT + QUAD"
    );


    // ========================================================
    // Print complete NEW histograms
    // ========================================================

    std::cout
        << "\n\n############################################################\n"
        << "#                         NEW FILE                         #\n"
        << "############################################################\n";

    printHistogram(
        newHist.sm,
        "NEW : SM"
    );

    printHistogram(
        newHist.quad,
        "NEW : QUADRATIC"
    );

    printHistogram(
        newHist.full,
        "NEW : SM + INT + QUAD"
    );


    // ========================================================
    // Compact tail view
    // ========================================================

    std::cout
        << "\n\n############################################################\n"
        << "#                     TAIL SUMMARY                         #\n"
        << "############################################################\n";

    printTail(
        oldHist.sm,
        "OLD SM"
    );

    printTail(
        newHist.sm,
        "NEW SM"
    );

    printTail(
        oldHist.quad,
        "OLD QUAD"
    );

    printTail(
        newHist.quad,
        "NEW QUAD"
    );

    printTail(
        oldHist.full,
        "OLD FULL"
    );

    printTail(
        newHist.full,
        "NEW FULL"
    );


    // ========================================================
    // Main diagnostic
    // ========================================================

    compareLastBins(
        oldHist.sm,
        newHist.sm,
        "SM"
    );

    compareLastBins(
        oldHist.quad,
        newHist.quad,
        "QUADRATIC"
    );

    compareLastBins(
        oldHist.full,
        newHist.full,
        "SM + INT + QUAD"
    );


    // ========================================================
    // Global integrals
    // ========================================================

    std::cout
        << "\n\n============================================================\n"
        << "GLOBAL INTEGRAL COMPARISON\n"
        << "============================================================\n";

    std::cout
        << std::scientific
        << std::setprecision(10);


    std::cout
        << "\nSM\n";

    std::cout
        << " OLD regular = "
        << oldHist.sm->Integral(
               1,
               oldHist.sm->GetNbinsX()
           )
        << "\n";

    std::cout
        << " NEW regular = "
        << newHist.sm->Integral(
               1,
               newHist.sm->GetNbinsX()
           )
        << "\n";


    std::cout
        << "\nQUADRATIC\n";

    std::cout
        << " OLD regular = "
        << oldHist.quad->Integral(
               1,
               oldHist.quad->GetNbinsX()
           )
        << "\n";

    std::cout
        << " NEW regular = "
        << newHist.quad->Integral(
               1,
               newHist.quad->GetNbinsX()
           )
        << "\n";


    std::cout
        << "\nSM + INT + QUAD\n";

    std::cout
        << " OLD regular = "
        << oldHist.full->Integral(
               1,
               oldHist.full->GetNbinsX()
           )
        << "\n";

    std::cout
        << " NEW regular = "
        << newHist.full->Integral(
               1,
               newHist.full->GetNbinsX()
           )
        << "\n";


    std::cout
        << "\n============================================================\n";

    std::cout
        << std::defaultfloat
        << std::setprecision(6);


    // ========================================================
    // Cleanup
    // ========================================================

    delete oldHist.sm;
    delete oldHist.quad;
    delete oldHist.full;

    delete newHist.sm;
    delete newHist.quad;
    delete newHist.full;


    std::cout
        << "\nComparison finished.\n"
        << std::endl;
}
