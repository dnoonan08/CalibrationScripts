#!/usr/bin/env python

from ROOT import *
import sys
import numpy

fName = sys.argv[1]

rootFile = TFile(fName,'r')

gROOT.SetBatch()
ROOT.gStyle.SetCanvasColor(0)


f = fName.split('_')
rValue = int(f[f.index('Range')+1])
vOffset = rValue*64

print rValue
print vOffset

def subrangeFit(x,p):
    if x[0] - vOffset < 16:
        return p[0]*x[0] + p[1]
    elif x[0] - vOffset < 36:
        return 2*p[0]*x[0] + p[2]
    elif x[0] - vOffset < 57:
        return 4*p[0]*x[0] + p[3]
    elif x[0] - vOffset < 63:
        return 8*p[0]*x[0] + p[4]
    else: return 0

def subrangeFit2(x,p):
    if 0.5 < x[0] - vOffset < 15:
        return p[0]*x[0] + p[1]
    elif 16 < x[0] - vOffset < 35:
        return 2*p[0]*x[0] + p[2]
    elif 36 < x[0] - vOffset < 56:
        return 4*p[0]*x[0] + p[3]
    elif 57 < x[0] - vOffset < 63:
        return 8*p[0]*x[0] + p[4]
    else:
        return 0

histoList = range(60,68)
for ih in histoList:
    histo = rootFile.Get("fCvsADC_"+str(ih))

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

    for n in range(1,N-1):
        adc = ADC[n]-vOffset
        if adc<1: low0 = fC[n]
        if adc<15: high0 = fC[n] 
        if adc<16.5: low1 = fC[n] 
        if adc<35: high1 = fC[n] 
        if adc<36.5: low2 = fC[n] 
        if adc<56: high2 = fC[n] 
        if adc<57.5: low3 = fC[n] 
        if adc<62.5: high3 = fC[n] 

    doSub0 = low0<high0
    doSub1 = low1<high1
    doSub2 = low2<high2
    doSub3 = low3<high3

    countsubranges = 0
    if doSub0: countsubranges+=1
    if doSub1: countsubranges+=1
    if doSub2: countsubranges+=1
    if doSub3: countsubranges+=1

    histo.SetTitle("Charge vs ADC, Range %i" % rValue)

    sub0_0 = TF1("sub0_0","pol1",low0,high0)
    sub0_1 = TF1("sub0_1","pol1",low1,high1)
    sub0_2 = TF1("sub0_2","pol1",low2,high2)
    sub0_3 = TF1("sub0_3","pol1",low3,high3)

    
    c1 = TCanvas()
    histo.Draw("ap")
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


    xmin = histo.GetXaxis().GetXmin()
    xmax = histo.GetXaxis().GetXmax()
    ymin = histo.GetYaxis().GetXmin()
    ymax = histo.GetYaxis().GetXmax()

    text = TPaveText(xmax - (xmax-xmin)*.5, ymin + (ymax-ymin)*.1,xmax - (xmax-xmin)*.1,ymin+(ymax-ymin)*(.1+.1*countsubranges))
    text.SetFillColor(kWhite)
    text.SetFillStyle(4000)
    if doSub0: text.AddText("subrange0 = %.2f fC/ADC" % (1./sub0_0.GetParameter(1)))
    if doSub1: text.AddText("subrange1 = %.2f fC/ADC" % (1./sub0_1.GetParameter(1)))
    if doSub2: text.AddText("subrange2 = %.2f fC/ADC" % (1./sub0_2.GetParameter(1)))
    if doSub3: text.AddText("subrange3 = %.2f fC/ADC" % (1./sub0_3.GetParameter(1)))
    text.Draw("same")
    c1.SaveAs("plots/fCvsADC_"+str(ih)+".png")



    sub0_0 = TF1("sub0_0","pol1",1 +vOffset,15+vOffset)
    sub0_1 = TF1("sub0_1","pol1",16+vOffset,36+vOffset)
    sub0_2 = TF1("sub0_2","pol1",36+vOffset,56+vOffset)
    sub0_3 = TF1("sub0_3","pol1",57+vOffset,61+vOffset)

    sub0_0.SetParameters(1,3)
    sub0_1.SetParameters(1,6)
    sub0_2.SetParameters(1,12)
    sub0_3.SetParameters(1,24)

    histo2 = rootFile.Get("ADCvsfC_"+str(ih))
    histo2.SetTitle("ADC vs Charge, Range %i" % rValue)
    histo2.GetYaxis().SetTitle("Charge (fC)")
    histo2.GetYaxis().SetTitleOffset(1.2)
    histo2.GetXaxis().SetTitle("ADC")
    histo2.Fit("sub0_0","","",1 +vOffset,15+vOffset)
    histo2.Fit("sub0_1","","",16+vOffset,36+vOffset)
    histo2.Fit("sub0_2","","",36+vOffset,56+vOffset)
    histo2.Fit("sub0_3","","",57+vOffset,61+vOffset)
    histo2.Draw('ap')
    if doSub0: sub0_0.Draw("same")
    if doSub1: sub0_1.Draw("same")
    if doSub2: sub0_2.Draw("same")
    if doSub3: sub0_3.Draw("same")    
    xmin = histo2.GetXaxis().GetXmin()
    xmax = histo2.GetXaxis().GetXmax()
    ymin = histo2.GetYaxis().GetXmin()
    ymax = histo2.GetYaxis().GetXmax()

    text = TPaveText(xmin + (xmax-xmin)*.1, ymax - (ymax-ymin)*(.1+.1*countsubranges),xmin + (xmax-xmin)*.5,ymax-(ymax-ymin)*.1)
    text.SetFillColor(kWhite)
    text.SetFillStyle(4000)
    if doSub0: text.AddText("subrange0 = %.2f fC/ADC" % (sub0_0.GetParameter(1)))
    if doSub1: text.AddText("subrange1 = %.2f fC/ADC" % (sub0_1.GetParameter(1)))
    if doSub2: text.AddText("subrange2 = %.2f fC/ADC" % (sub0_2.GetParameter(1)))
    if doSub3: text.AddText("subrange3 = %.2f fC/ADC" % (sub0_3.GetParameter(1)))
    text.Draw("same")
    
    c1.SaveAs("plots/ADCvsfC_"+str(ih)+".png")
    
 
    combined = TF1("fullrange",subrangeFit,1+vOffset,62+vOffset,5)
    combined.SetParameters(sub0_0.GetParameter(1), sub0_0.GetParameter(0), sub0_1.GetParameter(0), sub0_2.GetParameter(0), sub0_3.GetParameter(0))
    print combined
    histo2.Fit(combined,"","",1+vOffset,62+vOffset)
    print combined
    histo2.Draw('ap')
    combined.Draw("same")

    text = TPaveText(xmin + (xmax-xmin)*.1, ymax - (ymax-ymin)*(.1+.1*countsubranges),xmin + (xmax-xmin)*.6,ymax-(ymax-ymin)*.1)
    text.SetFillColor(kWhite)
    text.SetFillStyle(4000)
    text.AddText("Constrained slope =  %.2f fC/ADC" % (combined.GetParameter(0)))
    text.Draw("same")
    c1.SaveAs("plots/ADCvsfC_constrained_"+str(ih)+".png")
