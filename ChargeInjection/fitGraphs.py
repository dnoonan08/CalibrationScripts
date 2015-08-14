from ROOT import *
import sys
import numpy

import os

gROOT.SetBatch()
ROOT.gStyle.SetCanvasColor(0)



def doFit(graph, qieRange, saveGraph = False, qieNumber = 0, qieUniqueID = "", capID = -1):
    
    vOffset = 64*int(qieRange)
    if capID != -1: vOffset = 0


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

    def subrangeFit_sep(x,p):
        if x[0] - vOffset < 16:
            return p[0]*x[0] + p[1]
        elif x[0] - vOffset < 35:
            return p[2]*x[0] + p[3]
        elif x[0] - vOffset < 57:
            return p[4]*x[0] + p[5]
        elif x[0] - vOffset < 63:
            return p[6]*x[0] + p[7]
        else: return 0

    def subrangeFit_continuous(x,p):
        if x[0] - vOffset < 16:
            return p[0]*x[0] + p[1]
        elif x[0] - vOffset < 36:
            return 2*p[0]*x[0] - p[0]*(16+vOffset) + p[1]
        elif x[0] - vOffset < 57:
            return 4*p[0]*x[0] -2*p[0]*(vOffset+36) - p[0]*(16+vOffset) + p[1]
        elif x[0] - vOffset < 63:
            return 8*p[0]*x[0] -4*p[0]*(vOffset+57) -2*p[0]*(vOffset+36) - p[0]*(16+vOffset) + p[1]
        else: return 0

    def subrangeFit_continuous_ratio(x,p):
        if x[0] - vOffset < 16:
            return p[0]*x[0] + p[1]
        elif x[0] - vOffset < 36:
            return p[2]*p[0]*x[0] - p[0]*(16+vOffset) + p[1]
        elif x[0] - vOffset < 57:
            return p[2]**2*p[0]*x[0] -p[2]*p[0]*(vOffset+36) - p[0]*(16+vOffset) + p[1]
        elif x[0] - vOffset < 63:
            return p[2]**3*p[0]*x[0] -p[2]**2*p[0]*(vOffset+57) -p[2]*p[0]*(vOffset+36) - p[0]*(16+vOffset) + p[1]
        else: return 0

    xmin = graph.GetXaxis().GetXmin()
    xmax = graph.GetXaxis().GetXmax()
    ymin = graph.GetYaxis().GetXmin()
    ymax = graph.GetYaxis().GetXmax()

    
    combined = TF1("fullrange",subrangeFit_continuous,1+vOffset,xmax-1+vOffset,2)
    combined.SetParameters(1,-1)
    combined.SetLineWidth(2)
    graph.Fit(combined,"","",1+vOffset,62+vOffset)


    if saveGraph:
        qieInfo = ""
        saveName = "plots/"
        if qieUniqueID != "": 
            qieInfo += ", Card ID "+qieUniqueID
        else:
            qieUniqueID = "UnknownID"
        if not os.path.exists("plots/%s"%qieUniqueID):
            os.system("mkdir plots/%s"%qieUniqueID)
        saveName += qieUniqueID
        saveName += "/ADCvsfC"
        if qieNumber != 0: 
            qieInfo += ", QIE " + str(qieNumber)
            saveName += "_qie"+str(qieNumber)
        if capID != -1:
            qieInfo += ", CapID " + str(capID)
            saveName += "_capID"+str(capID)
        saveName += "_range"+str(qieRange)+".png"
        graph.SetTitle("ADC vs Charge, Range %i%s" % (qieRange,qieInfo))
        graph.GetYaxis().SetTitle("Charge (fC)")
        graph.GetYaxis().SetTitleOffset(1.2)
        graph.GetXaxis().SetTitle("ADC")

        c1 = TCanvas()
#        graph.SetMarkerStyle(2)
        graph.Draw("ap")
        combined.SetLineColor(kRed)
        combined.Draw("same")

        graph.GetXaxis().SetRangeUser(vOffset-10,vOffset+74)
        graph.GetYaxis().SetRangeUser(ymin*.9,ymax*1.1)
        

        # doSub0 =xmin < 15+vOffset
        # doSub1 =xmin < 35+vOffset and xmax > 16+vOffset
        # doSub2 =xmin < 56+vOffset and xmax > 36+vOffset
        # doSub3 =xmax > 57+vOffset

        xmin = max(vOffset,xmin)-10
        xmax = vOffset+74
        
        # countsubranges = 0
        # if doSub0: countsubranges += 1
        # if doSub1: countsubranges += 1
        # if doSub2: countsubranges += 1
        # if doSub3: countsubranges += 1

        text = TPaveText(xmin + (xmax-xmin)*.2, ymax - (ymax-ymin)*(.3),xmin + (xmax-xmin)*.6,ymax-(ymax-ymin)*.1)
        text.SetFillColor(kWhite)
        text.SetFillStyle(4000)
        text.AddText("Slope =  %.2f +- %.2f fC/ADC" % (combined.GetParameter(0), combined.GetParError(0)))
        text.AddText("Offset =  %.2f +- %.2f fC" % (combined.GetParameter(1), combined.GetParError(1)))
        text.Draw("same")

        c1.SaveAs(saveName)

    params = []
    params = combined.GetParameters()
    return params
