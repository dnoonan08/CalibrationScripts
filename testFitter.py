#!/usr/bin/env python

from ROOT import *
import sys
import numpy

fName = sys.argv[1]

rootFile = TFile(fName,'r')

gROOT.SetBatch()
ROOT.gStyle.SetCanvasColor(0)

offset = 64

histoList = range(60,68)
for ih in histoList:
    histo = rootFile.Get("fCvsADC_"+str(ih))

    stepHist = TH1F("step"+str(ih),"step"+str(ih),200,0,30)

    low0, high0 = 0,0
    low1, high1 = 0,0
    low2, high2 = 0,0
    low3, high3 = 0,0

    fC = histo.GetX()
    ADC = histo.GetY()
    N = histo.GetN()

    maxFC  = 0
    minFC  = 999999
    maxADC = 0
    minADC = 999999

    for n in range(1,N-1):
        if fC[n] > maxFC: maxFC = fC[n]
        if fC[n] < minFC: minFC = fC[n]
        if ADC[n] > maxADC: maxADC = ADC[n]
        if ADC[n] < minADC: minADC = ADC[n]


    print minFC, maxFC
    print minADC, maxADC

    low0 = minFC

    offset = 0
    UsedRange = -1
    if   maxADC < 70:  
        UsedRange = 0
        offset = 0
    elif maxADC < 140: 
        UsedRange = 1
        offset = 60
    elif maxADC < 205:
        UsedRange = 2
        offset = 120
    else: 
        UsedRange = 3
        offset = 180

    for n in range(1,N-1):
        adc = ADC[n]-offset
        if adc<15: high0 = fC[n] 
        if adc<16.5: low1 = fC[n] 
        if adc<35: high1 = fC[n] 
        if adc<36.5: low2 = fC[n] 
        if adc<56: high2 = fC[n] 
        if adc<57.5: low3 = fC[n] 
        if adc<62.5: high3 = fC[n] 
        binDiff = ADC[n+1]-ADC[n-1]
        if binDiff > 0:
            step = (fC[n+1]-fC[n-1])/binDiff
            stepHist.Fill(step)


    doSub0 = low0<high0
    doSub1 = low1<high1
    doSub2 = low2<high2
    doSub3 = low3<high3

    histo.SetTitle("Charge vs ADC, Range 0")


    sub0_0 = TF1("sub0_0","pol1",low0,high0)
    sub0_1 = TF1("sub0_1","pol1",low1,high1)
    sub0_2 = TF1("sub0_2","pol1",low2,high2)
    sub0_3 = TF1("sub0_3","pol1",low3,high3)
    
    c1 = TCanvas()
    histo.Draw("ap")
#    histo.GetXaxis().SetRangeUser(minFC*.85,maxFC*1.1)
#    histo.GetYaxis().SetRangeUser(minADC*.9, maxADC*1.1)
    histo.GetXaxis().SetTitle("Charge (fC)")
    histo.GetYaxis().SetTitle("ADC")
    histo.Fit("sub0_0","","",low0,high0)
    histo.Fit("sub0_1","","",low1,high1)
    histo.Fit("sub0_2","","",low2,high2)
    histo.Fit("sub0_3","","",low3,high3)
    sub0_0.SetLineColor(kRed)
    sub0_1.SetLineColor(kRed)
    sub0_2.SetLineColor(kRed)
    sub0_3.SetLineColor(kRed)
    if doSub0: sub0_0.Draw("same")
    if doSub1: sub0_1.Draw("same")
    if doSub2: sub0_2.Draw("same")
    if doSub3: sub0_3.Draw("same")


    med = (maxFC-minFC)/2.
    upper = (med+maxFC)/2.
    upperADC = (maxADC-minADC)*.3+minADC
    text = TPaveText(med,minADC,upper,upperADC)
    text.SetFillColor(kWhite)
    if doSub0: text.AddText("subrange0 = %.2f fC/ADC" % (1./sub0_0.GetParameter(1)))
    if doSub1: text.AddText("subrange1 = %.2f fC/ADC" % (1./sub0_1.GetParameter(1)))
    if doSub2: text.AddText("subrange2 = %.2f fC/ADC" % (1./sub0_2.GetParameter(1)))
    if doSub3: text.AddText("subrange3 = %.2f fC/ADC" % (1./sub0_3.GetParameter(1)))
    text.Draw("same")

    print minFC, maxFC
    print minADC, maxADC

    c1.SaveAs("plots/fCvsADC_"+str(ih)+".png")

    stepHist.Draw()
    c1.SaveAs("plots/stepHist_"+str(ih)+".png")
