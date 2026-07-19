#include <algorithm>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "TAxis.h"
#include "TCanvas.h"
#include "TGraph.h"
#include "TLatex.h"
#include "TLegend.h"
#include "TString.h"
#include "TStyle.h"


void setStyle(TGraph *graph,
              int color,
              int lineStyle,
              int markerStyle)
{
    graph->SetLineColor(color);
    graph->SetMarkerColor(color);

    graph->SetLineStyle(lineStyle);
    graph->SetLineWidth(3);

    graph->SetMarkerStyle(markerStyle);
    graph->SetMarkerSize(1.0);
}


TGraph *makeGraphIgnoringZero(const std::vector<double> &x,
                              const std::vector<double> &y)
{
    TGraph *graph = new TGraph();

    int point = 0;

    for (size_t i = 0; i < x.size(); ++i) {

        // Zero means that the limit was not available.
        if (y[i] == 0.0)
            continue;

        graph->SetPoint(point, x[i], y[i]);
        point++;
    }

    return graph;
}


void plotlimits(TString operatorName = "T0")
{
    gStyle->SetOptStat(0);

    TString inputFile =
        "limits_" + operatorName + ".txt";

    std::ifstream file(inputFile.Data());


    std::vector<double> cutoff;

    // m_jj * m_T
    std::vector<double> expMTMjj;
//    std::vector<double> obsMTMjj;

    // m_jj * m_01
    std::vector<double> expM01Mjj;
//    std::vector<double> obsM01Mjj;

    std::string line;

    while (std::getline(file, line)) {

        if (line.empty() || line[0] == '#')
            continue;

        std::stringstream ss(line);

        double x;
        double expectedMTMjj;
        double observedMTMjj;
        double expectedM01Mjj;
        double observedM01Mjj;

        if (!(ss >> x
                 >> expectedMTMjj
                 >> observedMTMjj
                 >> expectedM01Mjj
                 >> observedM01Mjj)) {

            std::cerr
                << "WARNING: Cannot read line:\n"
                << line
                << std::endl;

            continue;
        }

        cutoff.push_back(x);

        expMTMjj.push_back(expectedMTMjj);
//        obsMTMjj.push_back(observedMTMjj);

        expM01Mjj.push_back(expectedM01Mjj);
//        obsM01Mjj.push_back(observedM01Mjj);
    }

    file.close();

    if (cutoff.empty()) {
        std::cerr
            << "ERROR: No valid points found."
            << std::endl;

        return;
    }

    TGraph *gExpMTMjj =
        makeGraphIgnoringZero(cutoff, expMTMjj);

//    TGraph *gObsMTMjj =
//        makeGraphIgnoringZero(cutoff, obsMTMjj);

    TGraph *gExpM01Mjj =
        makeGraphIgnoringZero(cutoff, expM01Mjj);

//    TGraph *gObsM01Mjj =
//        makeGraphIgnoringZero(cutoff, obsM01Mjj);


    // m_jj * m_T: red
    setStyle(gExpMTMjj, kRed + 1, 2, 20);
//    setStyle(gObsMTMjj, kRed + 1, 1, 20);

    // m_jj * m_01: blue
    setStyle(gExpM01Mjj, kBlue + 1, 2, 21);
//    setStyle(gObsM01Mjj, kBlue + 1, 1, 21);


    double maximum = 0.0;

    auto updateMaximum =
        [&](const std::vector<double> &values)
    {
        for (double value : values) {

            if (value == 0.0)
                continue;

            maximum = std::max(maximum, value);
        }
    };

    updateMaximum(expMTMjj);
//    updateMaximum(obsMTMjj);
    updateMaximum(expM01Mjj);
//    updateMaximum(obsM01Mjj);

    if (maximum <= 0.0) {
        std::cerr
            << "ERROR: No positive limit values found."
            << std::endl;

        return;
    }


    TCanvas *canvas =
        new TCanvas(
            "canvas",
            "Limits versus cutoff",
            900,
            700
        );

    canvas->SetLeftMargin(0.14);
    canvas->SetRightMargin(0.04);
    canvas->SetBottomMargin(0.13);
    canvas->SetTopMargin(0.11);


    gExpMTMjj->SetTitle("");

    gExpMTMjj->GetXaxis()->SetTitle(
        " cutoff [GeV]"
    );

    gExpMTMjj->GetYaxis()->SetTitle(
        Form(
            "f_{%s} [TeV^{-4}]",
            operatorName.Data()
        )
    );

    gExpMTMjj->GetXaxis()->SetLimits(
        cutoff.front(),
        cutoff.back()
    );

    /*
       Two divisions give three labels:

       1000      2000      3000

       kFALSE prevents ROOT from optimizing the division number.
    */
    gExpMTMjj->GetXaxis()->SetNdivisions(2, kFALSE);

    gExpMTMjj->SetMinimum(0.0);
    gExpMTMjj->SetMaximum(maximum * 1.25);


    gExpMTMjj->GetXaxis()->SetTitleSize(0.045);
    gExpMTMjj->GetYaxis()->SetTitleSize(0.045);

    gExpMTMjj->GetXaxis()->SetLabelSize(0.040);
    gExpMTMjj->GetYaxis()->SetLabelSize(0.040);

    gExpMTMjj->GetXaxis()->SetTitleOffset(1.15);
    gExpMTMjj->GetYaxis()->SetTitleOffset(1.35);

    gExpMTMjj->GetXaxis()->SetTickLength(0.025);


    /*
       A = axes
       C = smooth curve
       P = markers
    */

    gExpMTMjj->Draw("AC");
//    gObsMTMjj->Draw("CP SAME");

    gExpM01Mjj->Draw("C SAME");
//    gObsM01Mjj->Draw("CP SAME");


    TLegend *legend =
        new TLegend(0.51, 0.66, 0.92, 0.87);

    legend->SetBorderSize(0);
    legend->SetFillStyle(0);
    legend->SetTextSize(0.033);

    legend->AddEntry(
        gExpMTMjj,
        "Expected, m_{jj} #times m_{T}",
        "lp"
    );

//    legend->AddEntry(
//        gObsMTMjj,
//        "Observed, m_{jj} #times m_{T}",
//        "lp"
//    );

    legend->AddEntry(
        gExpM01Mjj,
        "Expected, m_{jj} #times m_{01}",
        "lp"
    );

//    legend->AddEntry(
//        gObsM01Mjj,
//        "Observed, m_{jj} #times m_{01}",
//        "lp"
//    );

    legend->Draw();


    TLatex latex;
    latex.SetNDC();

    // CMS label moved slightly downward
    latex.SetTextFont(62);
    latex.SetTextSize(0.042);
    latex.SetTextAlign(11);
    latex.DrawLatex(
        0.14,
        0.905,
        "CMS"
    );

    latex.SetTextFont(52);
    latex.SetTextSize(0.033);
    latex.DrawLatex(
        0.21,
        0.905,
        "Work in progress"
    );

    // Luminosity moved slightly downward
    latex.SetTextFont(42);
    latex.SetTextSize(0.033);
    latex.SetTextAlign(31);
    latex.DrawLatex(
        0.96,
        0.905,
        "280 fb^{-1} (13.6 TeV)"
    );


    canvas->RedrawAxis();

    TString outputName =
        "limits_" + operatorName + "_vs_cutoff";

    canvas->SaveAs(outputName + ".pdf");
    canvas->SaveAs(outputName + ".png");

    std::cout
        << "Created: "
        << outputName
        << ".pdf"
        << std::endl;

    std::cout
        << "Created: "
        << outputName
        << ".png"
        << std::endl;
}