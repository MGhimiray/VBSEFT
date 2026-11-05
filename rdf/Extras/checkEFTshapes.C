#include <algorithm>
#include <cmath>
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


struct LimitData {
    std::vector<double> cutoff;

    std::vector<double> expMTMjjLow;
    std::vector<double> expMTMjjHigh;
    std::vector<double> obsMTMjjLow;
    std::vector<double> obsMTMjjHigh;

    std::vector<double> expM01MjjLow;
    std::vector<double> expM01MjjHigh;
    std::vector<double> obsM01MjjLow;
    std::vector<double> obsM01MjjHigh;
};


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

        // Zero is used as the unavailable-value marker.
        if (std::abs(y[i]) < 1.0e-12)
            continue;

        graph->SetPoint(point, x[i], y[i]);
        point++;
    }

    return graph;
}


bool readLimitFile(const TString &inputFile,
                   LimitData &data)
{
    std::ifstream file(inputFile.Data());

    if (!file.is_open()) {
        std::cerr
            << "ERROR: Cannot open "
            << inputFile
            << std::endl;

        return false;
    }

    std::string line;

    while (std::getline(file, line)) {

        if (line.empty() || line[0] == '#')
            continue;

        std::stringstream ss(line);

        double cutoff;

        double expMTLow;
        double expMTHigh;
        double obsMTLow;
        double obsMTHigh;

        double expM01Low;
        double expM01High;
        double obsM01Low;
        double obsM01High;

        if (!(ss >> cutoff
                 >> expMTLow
                 >> expMTHigh
                 >> obsMTLow
                 >> obsMTHigh
                 >> expM01Low
                 >> expM01High
                 >> obsM01Low
                 >> obsM01High)) {

            std::cerr
                << "WARNING: Cannot read line:\n"
                << line
                << std::endl;

            continue;
        }

        data.cutoff.push_back(cutoff);

        data.expMTMjjLow.push_back(expMTLow);
        data.expMTMjjHigh.push_back(expMTHigh);

        data.obsMTMjjLow.push_back(obsMTLow);
        data.obsMTMjjHigh.push_back(obsMTHigh);

        data.expM01MjjLow.push_back(expM01Low);
        data.expM01MjjHigh.push_back(expM01High);

        data.obsM01MjjLow.push_back(obsM01Low);
        data.obsM01MjjHigh.push_back(obsM01High);
    }

    file.close();

    if (data.cutoff.empty()) {
        std::cerr
            << "ERROR: No valid points were found in "
            << inputFile
            << std::endl;

        return false;
    }

    return true;
}


void drawCMSLabels()
{
    TLatex latex;
    latex.SetNDC();

    latex.SetTextAlign(11);
    latex.SetTextFont(62);
    latex.SetTextSize(0.042);

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

    latex.SetTextAlign(31);
    latex.SetTextFont(42);
    latex.SetTextSize(0.033);

    latex.DrawLatex(
        0.96,
        0.905,
        "280 fb^{-1} (13.6 TeV)"
    );
}


void drawLimitPlot(const TString &operatorName,
                   const std::vector<double> &cutoff,
                   const std::vector<double> &expMT,
                   const std::vector<double> &obsMT,
                   const std::vector<double> &expM01,
                   const std::vector<double> &obsM01,
                   bool upperLimit)
{
    TGraph *gExpMT =
        makeGraphIgnoringZero(cutoff, expMT);

    TGraph *gObsMT =
        makeGraphIgnoringZero(cutoff, obsMT);

    TGraph *gExpM01 =
        makeGraphIgnoringZero(cutoff, expM01);

    TGraph *gObsM01 =
        makeGraphIgnoringZero(cutoff, obsM01);


    // m_jj × m_T: red
    setStyle(gExpMT, kRed + 1, 2, 20);
    setStyle(gObsMT, kRed + 1, 1, 20);

    // m_jj × m_01: blue
    setStyle(gExpM01, kBlue + 1, 2, 21);
    setStyle(gObsM01, kBlue + 1, 1, 21);


    double minimum = 0.0;
    double maximum = 0.0;

    auto updateRange =
        [&](const std::vector<double> &values)
    {
        for (double value : values) {

            if (std::abs(value) < 1.0e-12)
                continue;

            minimum = std::min(minimum, value);
            maximum = std::max(maximum, value);
        }
    };

    updateRange(expMT);
    updateRange(obsMT);
    updateRange(expM01);
    updateRange(obsM01);


    TString limitType =
        upperLimit ? "upper" : "lower";

    TString canvasName =
        "canvas_" + operatorName + "_" + limitType;

    TCanvas *canvas =
        new TCanvas(
            canvasName,
            "Limits versus cutoff",
            900,
            700
        );

    canvas->SetLeftMargin(0.14);
    canvas->SetRightMargin(0.04);
    canvas->SetBottomMargin(0.13);
    canvas->SetTopMargin(0.11);


    gExpMT->SetTitle("");

    gExpMT->GetXaxis()->SetTitle(
        "Clipping cutoff #Lambda_{cut} [GeV]"
    );

    if (upperLimit) {

        gExpMT->GetYaxis()->SetTitle(
            Form(
                "Upper 95%% CL limit on f_{%s} [TeV^{-4}]",
                operatorName.Data()
            )
        );

        gExpMT->SetMinimum(0.0);
        gExpMT->SetMaximum(maximum * 1.25);

    } else {

        gExpMT->GetYaxis()->SetTitle(
            Form(
                "Lower 95%% CL limit on f_{%s} [TeV^{-4}]",
                operatorName.Data()
            )
        );

        /*
           minimum is negative.

           Multiplying by 1.25 extends the lower part of the axis:
           -1.0 becomes -1.25.
        */
        gExpMT->SetMinimum(minimum * 1.25);
        gExpMT->SetMaximum(0.0);
    }


    gExpMT->GetXaxis()->SetLimits(
        cutoff.front(),
        cutoff.back()
    );

    // Labels at 1000, 2000 and 3000.
    gExpMT->GetXaxis()->SetNdivisions(2, kFALSE);

    gExpMT->GetXaxis()->SetTitleSize(0.045);
    gExpMT->GetYaxis()->SetTitleSize(0.045);

    gExpMT->GetXaxis()->SetLabelSize(0.040);
    gExpMT->GetYaxis()->SetLabelSize(0.040);

    gExpMT->GetXaxis()->SetTitleOffset(1.15);
    gExpMT->GetYaxis()->SetTitleOffset(1.45);

    gExpMT->GetXaxis()->SetTickLength(0.025);


    /*
       Straight lines are used because the limits are calculated
       only at the listed clipping-cutoff values.

       A = axes
       L = straight lines
       P = calculated points
    */
    gExpMT->Draw("ALP");
    gObsMT->Draw("LP SAME");

    gExpM01->Draw("LP SAME");
    gObsM01->Draw("LP SAME");


    TLegend *legend =
        new TLegend(
            0.50,
            0.66,
            0.92,
            0.87
        );

    legend->SetBorderSize(0);
    legend->SetFillStyle(0);
    legend->SetTextSize(0.032);

    legend->AddEntry(
        gExpMT,
        "Expected, m_{jj} #times m_{T}",
        "lp"
    );

    legend->AddEntry(
        gObsMT,
        "Observed, m_{jj} #times m_{T}",
        "lp"
    );

    legend->AddEntry(
        gExpM01,
        "Expected, m_{jj} #times m_{01}",
        "lp"
    );

    legend->AddEntry(
        gObsM01,
        "Observed, m_{jj} #times m_{01}",
        "lp"
    );

    legend->Draw();

    drawCMSLabels();

    canvas->RedrawAxis();


    TString outputName =
        "limits_" +
        operatorName +
        "_" +
        limitType +
        "_vs_cutoff";

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


void plotlimits(TString operatorName = "T0")
{
    gStyle->SetOptStat(0);

    TString inputFile =
        "limits_" + operatorName + ".txt";

    LimitData data;

    if (!readLimitFile(inputFile, data))
        return;


    // Positive or upper interval endpoints
    drawLimitPlot(
        operatorName,
        data.cutoff,

        data.expMTMjjHigh,
        data.obsMTMjjHigh,

        data.expM01MjjHigh,
        data.obsM01MjjHigh,

        true
    );


    // Negative or lower interval endpoints
    drawLimitPlot(
        operatorName,
        data.cutoff,

        data.expMTMjjLow,
        data.obsMTMjjLow,

        data.expM01MjjLow,
        data.obsM01MjjLow,

        false
    );
}