#!/usr/bin/env python

from ROOT import *
import sys

fName = sys.argv[1]

rootFile = TFile(fName,'r')

gROOT.SetBatch()

histoList = range(60,72)
for ih in histoList:
    histo = rootFile.Get("fCvsADC_"+str(ih))

    stepHist = TH1F("step"+str(ih),"step"+str(ih),200,0,30)

    low1, high1 = 0,0
    low2, high2 = 0,0
    low3, high3 = 0,0

    histo.SetTitle("Charge vs ADC, Channel 0")
    fC = histo.GetX()
    ADC = histo.GetY()
    low1 = fC[0]
    for n in range(1,histo.GetN()-1):
        if ADC[n]<35: high1 = fC[n] 
        if ADC[n]<37: low2 = fC[n] 
        if ADC[n]<55: high2 = fC[n] 
        if ADC[n]<57: low3 = fC[n] 
        if ADC[n]<62.5: high3 = fC[n] 
        binDiff = ADC[n+1]-ADC[n-1]
        if binDiff > 0:
            step = (fC[n+1]-fC[n-1])/binDiff
            stepHist.Fill(step)

#    sub0_0 = TF1("pol1")
    sub0_0 = TF1("sub0_0","pol1",low0,high0)
    sub0_1 = TF1("sub0_1","pol1",low1,high1)
    sub0_2 = TF1("sub0_2","pol1",low2,high2)
    sub0_3 = TF1("sub0_3","pol1",low3,high3)
    
    c1 = TCanvas()
    histo.Draw("ap")
    histo.Fit("sub0_0","","",low0,high0)
    histo.Fit("sub0_1","","",low1,high1)
    histo.Fit("sub0_2","","",low2,high2)
    histo.Fit("sub0_3","","",low3,high3)
    sub0_0.Draw("same")
    sub0_1.Draw("same")
    sub0_2.Draw("same")
    sub0_3.Draw("same")

    histo.GetXaxis().SetRangeUser(0,800)
    histo.GetYaxis().SetRangeUser(0,70)
    histo.GetXaxis().SetTitle("Charge (fC)")
    histo.GetYaxis().SetTitle("ADC")

    text = TPaveText(400,15,700,35)
    text.SetFillColor(kWhite)
    text.AddText("subrange0 = %.2f fC/ADC" % (1./sub0_0.GetParameter(1)))
    text.AddText("subrange1 = %.2f fC/ADC" % (1./sub0_1.GetParameter(1)))
    text.AddText("subrange2 = %.2f fC/ADC" % (1./sub0_2.GetParameter(1)))
    text.AddText("subrange3 = %.2f fC/ADC" % (1./sub0_3.GetParameter(1)))
    text.Draw("same")

    c1.SaveAs("plots/fCvsADC_"+str(ih)+".png")

    stepHist.Draw()
    c1.SaveAs("plots/stepHist_"+str(ih)+".png")
