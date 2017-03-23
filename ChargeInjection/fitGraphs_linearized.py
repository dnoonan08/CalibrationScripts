from ROOT import *
import sys
import numpy
from array import array
import os

from linearADC import *

####Change the fit to return slopes/offsets in terms of range 0 values for all ranges

gROOT.SetBatch(kTRUE)
ROOT.gStyle.SetCanvasColor(kWhite)
gStyle.SetStatStyle(kWhite)
gStyle.SetTitleStyle(kWhite)

graphOffset = [100,500,3000,8000]

startVal = [[3.2,-15],
	    [3.2,-20],
	    [3.2,-20],
	    [3.2,-20]]


Varlimits = [[[2.5,4.0],[-50,100]],
	     [[2.5,4.0],[-50,1000]],
	     [[2.5,4.0],[-500,1000]],
	     [[2.5,4.0],[-5000,10000]]]



lineColors = [kRed, kBlue, kGreen+2, kCyan] 

def doFit_combined(graphList, qieRange, saveGraph = False, qieNumber = 0, qieUniqueID = "", useCalibrationMode = True, outputDir = '',saveOnlyComb = False):

	fitLines = []
	slopes = []
	offsets = []

	pedestal = [-13.33]*4
	linearizedGraphList = []

	print graphList

        for i_range in range(4):
		vOffset = i_range*64
		graphs = graphList[i_range]
		if graphs==None: 
			fitLines.append(None)
			continue
		else:			
			fitLines.append([])

		for i_capID in range(4):
			nominalgraph = graphs[i_capID]
			nominalgraph.SetNameTitle('%s_range_%i'%(nominalgraph.GetName(),i_range),'%s_range_%i'%(nominalgraph.GetName(),i_range))
			graph = nominalgraph.Clone("%s_linearized"%nominalgraph.GetName())
			graph.SetNameTitle("%s_linearized"%nominalgraph.GetName(),"%s_linearized"%nominalgraph.GetName())

			if i_range==0:
				for n in range(graph.GetN()):
					if graph.GetX()[n]>0.5:
						x1 = graph.GetX()[n+1]
						y1 = graph.GetY()[n+1]
						x2 = graph.GetX()[n+2]
						y2 = graph.GetY()[n+2]
						m = (y2-y1)/(x2-x1)
						pedestal[i_capID] = y1 - m*x1
						break

			points = range(graph.GetN())
			points.reverse()
			maxCharge = -9e9
			minCharge = 9e9
			for n in points:
				x = graph.GetX()[n]-vOffset
				nominalgraph.GetY()[n] -= pedestal[i_capID]
				graph.GetY()[n] -= pedestal[i_capID]
				if x<1 or x>62:
					graph.RemovePoint(n)
					continue
				y = graph.GetY()[n]
				if y > maxCharge: maxCharge = y
				if y < minCharge: minCharge = y
				_x, _ex = linADC(graph.GetX()[n],graph.GetEX()[n])
# 				graph.GetX()[n] = _x
# 				graph.GetEX()[n] = _ex

# 				x = graph.GetX()[n]
# 				ex = graph.GetEX()[n]
				_y = graph.GetY()[n]
				_ey = graph.GetEY()[n]
				graph.GetX()[n] = _y
				graph.GetEX()[n] = _ey
				graph.GetY()[n] = _x
				graph.GetEY()[n] = _ex
			graph.GetXaxis().SetTitle("Charge (fC)")
			graph.GetYaxis().SetTitle("Linearized ADC")

			
			graph.Fit("pol1","0")
			linearizedGraphList.append(graph)
			fitLine = graph.GetFunction("pol1")
			fitLine.SetNameTitle("fit_%s"%graph.GetName(),"fit_%s"%graph.GetName())
			fitLines[-1].append(fitLine)

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
					
				xmin = graph.GetXaxis().GetXmin()
				xmax = graph.GetXaxis().GetXmax()
				ymin = graph.GetYaxis().GetXmin()
				ymax = graph.GetYaxis().GetXmax()

				saveName += "/ADCvsfC"
				if qieNumber != 0: 
					qieInfo += ", QIE " + str(qieNumber)
					saveName += "_qie"+str(qieNumber)
				qieInfo += ", CapID " + str(i_capID)
				saveName += "_range"+str(i_range)
				saveName += "_capID"+str(i_capID)
				if not useCalibrationMode: saveName += "_NotCalMode"
				saveName += ".pdf"
				graph.SetTitle("ADC vs Charge, Range %i%s" % (i_range,qieInfo))
				graph.GetYaxis().SetTitle("Charge (fC)")
				graph.GetYaxis().SetTitleOffset(1.2)
				graph.GetXaxis().SetTitle("ADC")

			if saveGraph and not saveOnlyComb:

				xVals = graph.GetX()
				exVals = graph.GetEX()
				yVals = graph.GetY()
				eyVals = graph.GetEY()
				residuals = []
				residualErrors = []
# 				residualsY = []
# 				residualErrorsY = []
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


				resArray = array('d',residuals)
				resErrArray = array('d',residualErrors)
				resErrUpArray = array('d',eUp)
				resErrDownArray = array('d',eDown)
				xArray = array('d',x)
				xErrorsArray = array('d',[0]*len(x))

				
#				print i_range, i_capID, N, xArray, resArray
				residualGraphX = TGraphErrors(N,xArray,resArray, xErrorsArray, resErrArray)

				residualGraphX.SetTitle("")
				c1 = TCanvas()
				p1 = TPad("","",0,.2,.9,1)
				p2 = TPad("","",0,0,.9,.2)
				p1.Draw()
				p2.Draw()
				p1.SetFillColor(kWhite)
				p2.SetFillColor(kWhite)
#				p3.SetFillColor(kWhite)
				p1.cd()
				p1.SetBottomMargin(0)
				p1.SetRightMargin(0)
				graph.Draw("ap")
				fitLine.SetLineColor(kRed)
				fitLine.SetLineWidth(2)
				fitLine.Draw("same")

				# xmin = graph.GetXaxis().GetXmin()
				# xmax = graph.GetXaxis().GetXmax()
				# ymin = graph.GetYaxis().GetXmin()
				# ymax = graph.GetYaxis().GetXmax()

				text = TPaveText(xmin + (xmax-xmin)*.2, ymax - (ymax-ymin)*(.3),xmin + (xmax-xmin)*.6,ymax-(ymax-ymin)*.1)
				text.SetFillColor(kWhite)
				text.SetFillStyle(8000)
				text.AddText("Slope =  %.4f +- %.4f ADC/fC" % (fitLine.GetParameter(1), fitLine.GetParError(1)))
				text.AddText("Offset =  %.2f +- %.2f ADC" % (fitLine.GetParameter(0), fitLine.GetParError(0)))
				text.Draw("same")


				p2.cd()
				p2.SetTopMargin(0)
				p2.SetRightMargin(0)
				p2.SetBottomMargin(0.35)
				residualGraphX.Draw("ap")
				zeroLine = TF1("zero","0",-9e9,9e9)
				zeroLine.SetLineColor(kBlack)
				zeroLine.SetLineWidth(1)
				zeroLine.Draw("same")

				# xmin = xmin-10
				# xmax = xmax+10
				if minCharge < 10: minCharge = -10
			# graph.GetXaxis().SetLimits(xmin-10,xmax+10)
				graph.GetXaxis().SetLimits(minCharge*0.9, maxCharge*1.1)
				graph.GetYaxis().SetLimits(ymin*.9,ymax*1.1)

				residualGraphX.GetXaxis().SetLimits(minCharge*0.9, maxCharge*1.1)
				residualGraphX.GetYaxis().SetRangeUser(-0.03,0.03)
				residualGraphX.SetMarkerStyle(7)
				residualGraphX.GetYaxis().SetNdivisions(3,5,0)

				residualGraphX.GetXaxis().SetLabelSize(0.15)
				residualGraphX.GetYaxis().SetLabelSize(0.15)
				residualGraphX.GetYaxis().SetTitle("Residuals")
				residualGraphX.GetXaxis().SetTitle("ADC")
				residualGraphX.GetXaxis().SetTitleSize(0.15)
				residualGraphX.GetYaxis().SetTitleSize(0.15)
				residualGraphX.GetYaxis().SetTitleOffset(0.33)

				p1.cd()

				c1.SaveAs(saveName)

	params = [[],[],[],[]]
	for irange in range(4):
		if fitLines[irange]==None:
			for icapID in range(4):
				params[irange].append([-1,-1])
			continue
		for icapID in range(4):
			offset = fitLines[irange][icapID].GetParameter(0)
			slope = fitLines[irange][icapID].GetParameter(1)
			params[irange].append([slope,offset])


	outputTGraphs = TFile(outputDir.replace("outputPlots","")+"/fitResults_%s.root"%qieUniqueID,"update")

	for graph in linearizedGraphList:
		outputTGraphs.cd("LinadcVsCharge")
		graph.Write()
	for i_range in range(4):
		if graphList[i_range]==None: continue
		print 'Writing'
		for graph in graphList[i_range]:
			outputTGraphs.cd("adcVsCharge")
			graph.Write()
		for fitLine in fitLines[i_range]:
			fitLine.SetNpx(1000)
			outputTGraphs.cd("fitLines")
			fitLine.Write()

		if saveGraph:
			saveName = saveName.replace("_capID"+str(i_capID),"")
			c1 = TCanvas()
			slopes = []
			offsets = []

			for i_capID in range(4):
				graph = graphList[i_range][i_capID]
				fitLine = fitLines[i_range][i_capID]
				#            graph.SetMarkerStyle(20+i_capID)
				fitLine.SetLineColor(lineColors[i_capID])
				fitLine.SetLineWidth(2)

				slopes.append( (fitLine.GetParameter(0), fitLine.GetParError(0) ) )
				offsets.append( (fitLine.GetParameter(1), fitLine.GetParError(1) ) )
				if i_capID==0:
					graph.Draw("ap")
					graph.SetTitle("ADC vs Charge, Range %i, %s, QIE %i" % (i_range,qieUniqueID,qieNumber))
					graph.GetYaxis().SetRangeUser(ymin-graphOffset[i_range],graph.GetYaxis().GetXmax()+graphOffset[i_range]*4)
				else:
					N_ = graph.GetN()
					x_ = graph.GetX()
					y_ = graph.GetY()
					for n in range(N_):
						graph.SetPoint(n,x_[n],y_[n]+(graphOffset[i_range]*i_capID))
						fitLine.SetParameter(1,fitLine.GetParameter(1)+(graphOffset[i_range]*i_capID))
				graph.Draw("p, same")
				fitLine.Draw("same")
				if not i_range==3:
					text = TPaveText(xmin +5, ymax + 3*graphOffset[i_range] - (ymax-ymin)*(.7) ,xmin + 50 ,ymax+3.75*graphOffset[i_range])
				else:
					text = TPaveText(xmin +25, ymax + 2*graphOffset[i_range] - (ymax-ymin)*(.7) ,xmin + 75 ,ymax+3.75*graphOffset[i_range])

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
				
			c1.SaveAs(saveName)

	return params




