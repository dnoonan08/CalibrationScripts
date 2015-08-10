from ROOT import *
import sys
import numpy

gROOT.SetBatch()
ROOT.gStyle.SetCanvasColor(0)



def doFit(graph, qieRange, saveGraph = False, qieNumber = 0, qieUniqueID = ""):
    
    vOffset = 64*qieRange

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

    combined = TF1("fullrange",subrangeFit,1+vOffset,62+vOffset,5)
    combined.SetParameters(1,-1,-1,-1,-1)
    graph.Fit(combined,"","",1+vOffset,62+vOffset)

    if saveGraph:
        qieInfo = ""
        saveName = "plots/ADCvsfC"
        if qieUniqueID != "": 
            qieInfo += ", Card ID "+qieUniqueID
            saveName += "_"+qieUniqueID
        if qieNumber != 0: 
            qieInfo += ", QIE " + str(qieNumber)
            saveName += "_"+str(qieNumber)
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
        xmin = graph.GetXaxis().GetXmin()
        xmax = graph.GetXaxis().GetXmax()
        ymin = graph.GetYaxis().GetXmin()
        ymax = graph.GetYaxis().GetXmax()

        doSub0 =xmin < 15+vOffset
        doSub1 =xmin < 35+vOffset and xmax > 16+vOffset
        doSub2 =xmin < 56+vOffset and xmax > 36+vOffset
        doSub3 =xmax > 57+vOffset
        
        countsubranges = 0
        if doSub0: countsubranges += 1
        if doSub1: countsubranges += 1
        if doSub2: countsubranges += 1
        if doSub3: countsubranges += 1

        text = TPaveText(xmin + (xmax-xmin)*.1, ymax - (ymax-ymin)*(.1+.1*countsubranges),xmin + (xmax-xmin)*.6,ymax-(ymax-ymin)*.1)
        text.SetFillColor(kWhite)
        text.SetFillStyle(4000)
        text.AddText("Constrained slope =  %.2f fC/ADC" % (combined.GetParameter(0)))
        text.Draw("same")

        c1.SaveAs(saveName)

    params = []
    params = combined.GetParameters()
    return params
