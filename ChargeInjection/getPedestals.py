from ROOT import *
from linearADC import *
import os
from array import array

bin0startLevel = -0.5


def linearizeGraph(graph, i_range):
    vOffset = i_range*64
    points = range(graph.GetN())
    points.reverse()
    removeRest = False
    graph.SetNameTitle(graph.GetName().replace("ADC","linADC"),graph.GetName().replace("ADC","linADC"))

    for n in points:
        x = graph.GetX()[n]-vOffset
        if x>62:
            graph.RemovePoint(n)
            continue

        if n==0:
            graph.RemovePoint(n)
            continue

        if x < 1:
            removeRest=True

        if removeRest:
            graph.RemovePoint(n)
            continue

        _linADC, _linADCErr = linADC(graph.GetX()[n],graph.GetEX()[n])
        _charge = graph.GetY()[n]
        _chargeErr = graph.GetEY()[n]
        graph.GetX()[n] = _charge
        graph.GetEX()[n] = _chargeErr
        graph.GetY()[n] = _linADC
        graph.GetEY()[n] = _linADCErr
    return graph


def getPedestals(graphs, histoList,dirName, date, run):

    pedestalVals = {}

    if not os.path.exists("%s/PedestalPlots"%dirName):
        os.mkdir("%s/PedestalPlots"%dirName)
    
    _file = TFile("%s/PedestalPlots/pedestalMeasurement_%s_%s.root"%(dirName,date,run),"update")

    c1 = TCanvas()
    c1.Divide(2,2)

    for ih in histoList:
        _file.mkdir("h%i"%ih)
        _file.cd("h%i"%ih)
        print ih
        #get low current
        lowCurrentPeds = []
        for i_capID in range(4):
            #linearize the graph first 
            graph = linearizeGraph(graphs[ih][i_capID],0)
            graph.Fit("pol1","Q")
            line = graph.GetFunction("pol1")
            graph.Write()
            #pedestal is the x-intercept of the graph (-offset/slope)            
            lowCurrentPeds.append(-1*(line.GetParameter(0)+bin0startLevel)/line.GetParameter(1))

        pedestalVals[ih] = lowCurrentPeds

    _file.Close()

    return pedestalVals
