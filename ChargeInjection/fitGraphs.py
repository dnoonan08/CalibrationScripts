from ROOT import *
import sys
import numpy
from array import array
import os

gROOT.SetBatch(True)
ROOT.gStyle.SetCanvasColor(kWhite)
gStyle.SetStatStyle(kWhite)
gStyle.SetTitleStyle(kWhite)

graphOffset = [100,500,3000,8000]

startVal = [[3.2,-15],
	    [2.5e+01,-1.0e+03],
	    [2.1e+02,-2.2e+04],
	    [1.6e+03,-2.6e+05]
	    ]

Varlimits = [[[2.5,4.0],[-40,0]],
	     [[20.,30.],[-2000,-500]],
	     [[0.75*2.1e+02,1.25*2.1e+02],[1.25*-2.2e+04,0.75*-2.2e+04]],
	     [[0.75*1.6e+03,1.25*1.6e+03],[1.25*-2.6e+05,0.75*-2.6e+05]],
	     ]
	       
def invertFunction(x,y,p0,p1, vOffset):
        if x - vOffset < 16:
            m = p0
            b = p1
        elif x - vOffset < 36:
            m = 2*p0
            b = - p0*(16+vOffset) + p1
        elif x - vOffset < 57:
            m = 4*p0
            b = -2*p0*(vOffset+36) - p0*(16+vOffset) + p1
        elif x - vOffset < 63:
            m = 8*p0
            b = -4*p0*(vOffset+57) -2*p0*(vOffset+36) - p0*(16+vOffset) + p1
	else:
		return 0
        return (y-b)/m


def fit_graph(graph, qieRange, vOffset):
    vOffset = qieRange*64
    x1 = 16
    x2 = 36
    x3 = 57

    def subrangeFit_continuous(x,p):
        if x[0] - vOffset < x1:
            return p[0]*x[0] + p[1]
        elif x[0] - vOffset < x2:
            return 2*p[0]*x[0] - p[0]*(x1+vOffset) + p[1]
        elif x[0] - vOffset < x3:
            return 4*p[0]*x[0] -2*p[0]*(vOffset+x2) - p[0]*(x1+vOffset) + p[1]
        elif x[0] - vOffset < 63:
            return 8*p[0]*x[0] -4*p[0]*(vOffset+x3) -2*p[0]*(vOffset+x2) - p[0]*(x1+vOffset) + p[1]
        else: return 0
    
    xVals = graph.GetX()
    yVals = graph.GetY()
    N = graph.GetN()
    xVals_list = []
    yVals_list = []
    for i in range(N):
        xVals_list.append(xVals[i])
        yVals_list.append(yVals[i])


    xVals_list.sort()
    max_x = xVals_list[-1]
    min_x = xVals_list[0]
#    print min_x, max_x
    # print xVals_list
    # print yVals_list
    # print max(1+vOffset,min_x+1),min(max_x-1,62+vOffset)
    
    combined = TF1("fit_"+graph.GetName(),subrangeFit_continuous,max(1+vOffset,min_x+1),min(max_x-1,62+vOffset),2)

    combined.SetParameters(0,startVal[qieRange][0])
    combined.SetParameters(1,startVal[qieRange][1])
    combined.SetParLimits(0,Varlimits[qieRange][0][0],Varlimits[qieRange][0][1])
    combined.SetParLimits(1,Varlimits[qieRange][1][0],Varlimits[qieRange][1][1])
    combined.SetLineWidth(0)
#    graph.Fit(combined,"N","",max(1+vOffset,min_x+1),min(max_x-1,62+vOffset))
    graph.Fit(combined,"N","",1+vOffset,62+vOffset)

    print graph.GetName()
    print 1+vOffset,62+vOffset
    print combined.GetChisquare()

    return combined


lineColors = [kRed, kBlue, kGreen+2, kCyan] 

def doFit_combined(graphs, qieRange, saveGraph = False, qieNumber = 0, qieUniqueID = "", useCalibrationMode = True, outputDir = ''):

    fitLines = []
    slopes = []
    offsets = []

    for i_capID in range(4):
        graph = graphs[i_capID]
        fitLine = fit_graph(graph, qieRange, 0)
        fitLines.append(fitLine)
        if saveGraph:
            qieInfo = ""
	    
            saveName = outputDir
	    if saveName[-1]!='/':
		    saveName += '/'
	    saveName += "plots/"
            if qieUniqueID != "": 
                qieInfo += ", Card ID "+qieUniqueID
            else:
                qieUniqueID = "UnknownID"
            saveName += qieUniqueID
            if not os.path.exists(saveName):
                os.system("mkdir -p %s"%saveName)
            saveName += "/ADCvsfC"
            if qieNumber != 0: 
                qieInfo += ", QIE " + str(qieNumber)
                saveName += "_qie"+str(qieNumber)
            qieInfo += ", CapID " + str(i_capID)
            saveName += "_range"+str(qieRange)
            saveName += "_capID"+str(i_capID)
            if not useCalibrationMode: saveName += "_NotCalMode"
            saveName += ".pdf"
            graph.SetTitle("ADC vs Charge, Range %i%s" % (qieRange,qieInfo))
            graph.GetYaxis().SetTitle("Charge (fC)")
            graph.GetYaxis().SetTitleOffset(1.2)
            graph.GetXaxis().SetTitle("ADC")

            xVals = graph.GetX()
            exVals = graph.GetEX()
            yVals = graph.GetY()
            eyVals = graph.GetEY()
            residuals = []
            residualErrors = []
            residualsY = []
            residualErrorsY = []
            eUp = []
            eDown = []
            N = graph.GetN()
            x = []
            y = []

            for i in range(N):
		#    if yVals[i] != 0:
		residuals.append((yVals[i]-fitLine.Eval(xVals[i]))/max(yVals[i],0.001))
		xLow = (xVals[i]-exVals[i])
		xHigh = (xVals[i]+exVals[i])
		eUp.append((yVals[i]-fitLine(xLow))/max(yVals[i],0.001))
		eDown.append((yVals[i]-fitLine(xLow))/max(yVals[i],0.001))
		residualErrors.append(eyVals[i]/max(yVals[i],0.001))
		x.append(xVals[i])

                #if xVals[i] != 0:
		xFit = invertFunction(xVals[i], yVals[i],fitLine.GetParameter(0),fitLine.GetParameter(1), qieRange*64)
#		    print xFit, xVals[i], yVals[i],fitLine.GetParameter(0),fitLine.GetParameter(1), qieRange*64
		residualsY.append((xVals[i]-xFit)/max(xVals[i],0.001))
		residualErrorsY.append(exVals[i]/max(xVals[i],0.001))
		y.append(yVals[i])
            
            resArray = array('d',residuals)
            resErrArray = array('d',residualErrors)
            resErrUpArray = array('d',eUp)
            resErrDownArray = array('d',eDown)
            resArrayY = array('d',residualsY)
            resErrArrayY = array('d',residualErrorsY)
            xArray = array('d',x)
            xErrorsArray = array('d',[0]*len(x))
            yArray = array('d',y)
            yErrorsArray = array('d',[0]*len(y))

	    # print yArray
	    # print resArrayY
	    # print xVals[1]
	    # print len(yArray)
	    # print len(resArrayY)

            residualGraphX = TGraphErrors(len(x),xArray,resArray, xErrorsArray, resErrArray)
#            residualGraphX = TGraphAsymmErrors(len(x),xArray,resArray, xErrorsArray, xErrorsArray, resErrDownArray, resErrUpArray)
            residualGraphY = TGraphErrors(len(y),resArrayY, yArray, resErrArrayY, yErrorsArray)

            residualGraphX.SetTitle("")
            c1 = TCanvas()
            p1 = TPad("","",0,.2,.8,1)
            p2 = TPad("","",0,0,.8,.2)
            p3 = TPad("","",.8,0,1,1)
            p1.Draw()
            p2.Draw()
            p3.Draw()
            p1.SetFillColor(kWhite)
            p2.SetFillColor(kWhite)
            p3.SetFillColor(kWhite)
            p1.cd()
            p1.SetBottomMargin(0)
            p1.SetRightMargin(0)
            graph.Draw("ap")
            fitLine.SetLineColor(kRed)
            fitLine.SetLineWidth(2)
            fitLine.Draw("same")

            xmin = graph.GetXaxis().GetXmin()
            xmax = graph.GetXaxis().GetXmax()
            ymin = graph.GetYaxis().GetXmin()
            ymax = graph.GetYaxis().GetXmax()

            text = TPaveText(xmin + (xmax-xmin)*.2, ymax - (ymax-ymin)*(.3),xmin + (xmax-xmin)*.6,ymax-(ymax-ymin)*.1)
            text.SetFillColor(kWhite)
            text.SetFillStyle(4000)
	    slopes.append( (fitLine.GetParameter(0), fitLine.GetParError(0) ) )
	    offsets.append( (fitLine.GetParameter(1), fitLine.GetParError(1) ) )
            text.AddText("Slope =  %.2f +- %.2f fC/ADC" % (fitLine.GetParameter(0), fitLine.GetParError(0)))
            text.AddText("Offset =  %.2f +- %.2f fC" % (fitLine.GetParameter(1), fitLine.GetParError(1)))
            text.Draw("same")


            p2.cd()
            p2.SetTopMargin(0)
            p2.SetRightMargin(0)
            p2.SetBottomMargin(0.35)
            residualGraphX.Draw("ap")
            zeroLine = TLine(fitLine.GetMinimumX(), 0,fitLine.GetMaximumX(),0)
            zeroLine.Draw("same")

            p3.cd()
	    p3.SetTopMargin(0.8*p3.GetTopMargin() )
            p3.SetLeftMargin(0)
            p3.SetBottomMargin(0.2)
            residualGraphY.Draw("ap")
            zeroLineY = TLine(0,ymin,0,ymax)
            zeroLineY.Draw("same")


            residualGraphX.GetXaxis().SetLabelSize(0.15)
            residualGraphX.GetYaxis().SetLabelSize(0.15)
            residualGraphX.GetYaxis().SetTitle("Residuals")
            residualGraphX.GetXaxis().SetTitle("ADC")
            residualGraphX.GetXaxis().SetTitleSize(0.15)
            residualGraphX.GetYaxis().SetTitleSize(0.15)
            residualGraphX.GetYaxis().SetTitleOffset(0.33)

            residualGraphY.GetXaxis().SetTitle("Residuals")
            residualGraphY.GetXaxis().SetLabelSize(0.1)
            residualGraphY.GetYaxis().SetLabelSize(0.1)
            residualGraphY.GetXaxis().SetTitleSize(0.1)

            residualGraphY.GetXaxis().SetTitleOffset(0.3)
            residualGraphY.GetXaxis().SetLabelOffset(-0.05)


            residualGraphX.GetYaxis().CenterTitle()
            residualGraphY.GetXaxis().CenterTitle()
	   

            # xmin = xmin-10
            # xmax = xmax+10

#            graph.GetXaxis().SetLimits(xmin-10,xmax+10)
	    graph.GetXaxis().SetLimits(qieRange*64-10,(1+qieRange)*64+10)
            graph.GetYaxis().SetLimits(ymin*.9,ymax*1.1)

            residualGraphX.GetXaxis().SetLimits(qieRange*64-10,(1+qieRange)*64+10)
            residualGraphX.GetYaxis().SetRangeUser(-0.03,0.03)
            residualGraphX.SetMarkerStyle(7)
            residualGraphX.GetYaxis().SetNdivisions(3,5,0)

            residualGraphY.GetXaxis().SetLimits(-0.03,0.03)
            residualGraphY.GetYaxis().SetLimits(ymin*.9, ymax*1.1)
	    residualGraphY.SetMarkerStyle(7)
            residualGraphY.GetXaxis().SetNdivisions(3,5,0)
	    residualGraphY.SetTitle("")



#            print xmin, xmax

            p1.cd()

            c1.SaveAs(saveName)

    params = []
    for i in range(4):
        params.append(fitLines[i].GetParameters())
    outputTGraphs = TFile(outputDir+"/adcVSfc_graphs.root","update")

    for graph in graphs:
	    graph.Write()
    for fitLine in fitLines:
	    fitLine.SetNpx(4000)
	    fitLine.Write()

    if saveGraph:
        saveName = saveName.replace("_capID"+str(i_capID),"")
        c1 = TCanvas()
	for i_capID in range(4):
            graph = graphs[i_capID]
	    fitLine = fitLines[i_capID]
#            graph.SetMarkerStyle(20+i_capID)
	 #   print graph
            fitLine.SetLineColor(lineColors[i_capID])
            fitLine.SetLineWidth(2)

	    print xmin, xmax
	    print ymin, ymax
	    if not qieRange==3:
		    text = TPaveText(xmin +5, ymax + 3*graphOffset[qieRange] - (ymax-ymin)*(.7) ,xmin + 50 ,ymax+3.75*graphOffset[qieRange])
	    else:
		    text = TPaveText(xmin +25, ymax + 2*graphOffset[qieRange] - (ymax-ymin)*(.7) ,xmin + 75 ,ymax+3.75*graphOffset[qieRange])

	    text.SetFillColor(kWhite)
	    text.SetFillStyle(4000)
	    text.SetTextAlign(11)
	    text.AddText("CapID 0:")
	    text.AddText("    Slope =  %.2f +- %.2f fC/ADC" % slopes[0])
            text.AddText("    Offset =  %.2f +- %.2f fC" % offsets[0])
	    text.AddText("CapID 1:")
            text.AddText("    Slope =  %.2f +- %.2f fC/ADC" % slopes[1])
            text.AddText("    Offset =  %.2f +- %.2f fC" % offsets[1])
	    text.AddText("CapID 2:")
            text.AddText("    Slope =  %.2f +- %.2f fC/ADC" % slopes[2])
            text.AddText("    Offset =  %.2f +- %.2f fC" % offsets[2])
	    text.AddText("CapID 3:")
            text.AddText("    Slope =  %.2f +- %.2f fC/ADC" % slopes[3])
            text.AddText("    Offset =  %.2f +- %.2f fC" % offsets[3])
            text.Draw("same")

            if i_capID==0:
                graph.Draw("ap")
                graph.SetTitle("ADC vs Charge, Range %i, %s, QIE %i" % (qieRange,qieUniqueID,qieNumber))
		graph.GetYaxis().SetRangeUser(ymin-graphOffset[qieRange],graph.GetYaxis().GetXmax()+graphOffset[qieRange]*4)
            else:
                N_ = graph.GetN()
                x_ = graph.GetX()
                y_ = graph.GetY()
                for i in range(N_):
                    graph.SetPoint(i,x_[i],y_[i]+(graphOffset[qieRange]*i_capID))
                graph.Draw("p, same")
                fitLine.SetParameter(1,fitLine.GetParameter(1)+(graphOffset[qieRange]*i_capID))
            fitLine.Draw("same")
        c1.SaveAs(saveName)
        for i_capID in range(4):
		fitLine = fitLines[i_capID]
		fitLine.SetParameter(1,fitLine.GetParameter(1)-(graphOffset[qieRange]*i_capID))
		N_ = graph.GetN()
		x_ = graph.GetX()
                y_ = graph.GetY()
                for i in range(N_):
			graph.SetPoint(i,x_[i],y_[i]+(graphOffset[qieRange]*i_capID))

    return params


def doFit(graph, qieRange, saveGraph = False, qieNumber = 0, qieUniqueID = "", capID = -1, useCalibrationMode = True):
    
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
    
    xVals = graph.GetX()
    N = graph.GetN()
    xVals_list = []
    for i in range(N):
        xVals_list.append(xVals[i])

    xVals_list.sort()
    max_x = xVals_list[-1]
    min_x = xVals_list[0]
    print min_x, max_x
    
    combined = TF1("fullrange",subrangeFit_continuous,max(2,min_x+1)+vOffset,min(max_x-1,62)+vOffset,2)
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
        saveName += "_range"+str(qieRange)
        if not useCalibrationMode: saveName += "_NotCalMode"
        saveName += ".pdf"
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



