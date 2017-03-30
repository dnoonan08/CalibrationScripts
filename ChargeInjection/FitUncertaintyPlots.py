from ROOT import *

def fillFitUncertaintyHists(summaryFile):
    range0Unc = TH1F("SlopeUncertainty_Range0","SlopeUncertainty_Range0",100,0,.05)
    range1Unc = TH1F("SlopeUncertainty_Range1","SlopeUncertainty_Range1",100,0,.05)
    range2Unc = TH1F("SlopeUncertainty_Range2","SlopeUncertainty_Range2",100,0,.05)
    range3Unc = TH1F("SlopeUncertainty_Range3","SlopeUncertainty_Range3",100,0,.05)


    _file = TFile(summaryFile,"update")

    keys = _file.GetDirectory("fitLines").GetListOfKeys()

    badfits = []

    for k in keys:
        fitline = k.ReadObj()
        slopeUnc = 1
        if fitline.GetParameter(1)>0:
            slopeUnc = fitline.GetParError(1)/fitline.GetParameter(1)

#        print slopeUnc
        if slopeUnc > 0.05:
#            print 'HERE', slopeUnc
#            print k
            slopeUnc = 0.0499
        if (slopeUnc > 0.01 and not 'range_3' in fitline.GetName()) or slopeUnc > 0.02:
            print '*'*40
            print '*'*40
            print '*'*40
            print 'Bad Fit Result'
            print fitline.GetName()
            print '*'*40
            print '*'*40
            print '*'*40
            channelNum = int(fitline.GetName().split('_')[2])%24+1
            badfits.append(channelNum)

            
        if 'range_0' in fitline.GetName():
            range0Unc.Fill(slopeUnc)
        if 'range_1' in fitline.GetName():
            range1Unc.Fill(slopeUnc)
        if 'range_2' in fitline.GetName():
            range2Unc.Fill(slopeUnc)
        if 'range_3' in fitline.GetName():
            range3Unc.Fill(slopeUnc)

    
    _file.cd("SummaryPlots")
    range0Unc.Write()
    range1Unc.Write()
    range2Unc.Write()
    range3Unc.Write()

    return badfits
                    
