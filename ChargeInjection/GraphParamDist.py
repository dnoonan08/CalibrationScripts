from ROOT import *
import sqlite3

gROOT.SetBatch(True)

def fillHistos(values):

    hists = {0:[TH1F("Range0Slopes","Range0Slopes",50,.25,.35), TH1F("Range0Offsets","Range0Offsets",50,-10,10)],
             1:[TH1F("Range1Slopes","Range1Slopes",50,.25,.35), TH1F("Range1Offsets","Range1Offsets",50,-10,10)],
             2:[TH1F("Range2Slopes","Range2Slopes",50,.25,.35), TH1F("Range2Offsets","Range2Offsets",50,-10,10)],
             3:[TH1F("Range3Slopes","Range3Slopes",50,.25,.35), TH1F("Range3Offsets","Range3Offsets",50,-10,10)],
             }    
    
    for entry in values:
        qieID, serial,  qieNum, i_capID, qieRange, directory, timestamp, slope, offset = entry
#         print slope, offset
        hists[qieRange][i_capID][0].Fill(slope)
        hists[qieRange][i_capID][1].Fill(offset)
        hists[qieRange]['all'][0].Fill(slope)
        hists[qieRange]['all'][1].Fill(offset)

    return hists

def graphParamDist(paramFileName):

    outputDirectory = paramFileName.split('qieCalibrationParam')[0]

    paramDB = sqlite3.connect(paramFileName)
    cursor = paramDB.cursor()

    

    qieCards = [x[0] for x in list(set(cursor.execute("select id from qieparams").fetchall()))]
    print qieCards

    for uniqueID in qieCards:
        print uniqueID
        parameterValues = cursor.execute("select * from qieparams where id = ?", [str(uniqueID)]).fetchall()

        range0MinMax = cursor.execute("select min(slope), max(slope), min(offset), max(offset) from qieparams where id = ? and range=?", [str(uniqueID),0]).fetchone()
        range1MinMax = cursor.execute("select min(slope), max(slope), min(offset), max(offset) from qieparams where id = ? and range=?", [str(uniqueID),1]).fetchone()
        range2MinMax = cursor.execute("select min(slope), max(slope), min(offset), max(offset) from qieparams where id = ? and range=?", [str(uniqueID),2]).fetchone()
        range3MinMax = cursor.execute("select min(slope), max(slope), min(offset), max(offset) from qieparams where id = ? and range=?", [str(uniqueID),3]).fetchone()

        hists = {0:[TH1F("Range0Slopes","Range0Slopes",50,range0MinMax[0]*0.8,range0MinMax[1]*1.2), TH1F("Range0Offsets","Range0Offsets",50,range0MinMax[2]*1.2, range0MinMax[3]*1.2)],
                 1:[TH1F("Range1Slopes","Range1Slopes",50,range1MinMax[0]*0.8,range1MinMax[1]*1.2), TH1F("Range1Offsets","Range1Offsets",50,range1MinMax[2]*1.2, range1MinMax[3]*1.2)],
                 2:[TH1F("Range2Slopes","Range2Slopes",50,range2MinMax[0]*0.8,range2MinMax[1]*1.2), TH1F("Range2Offsets","Range2Offsets",50,range2MinMax[2]*1.2, range2MinMax[3]*1.2)],
                 3:[TH1F("Range3Slopes","Range3Slopes",50,range3MinMax[0]*0.8,range3MinMax[1]*1.2), TH1F("Range3Offsets","Range3Offsets",50,range3MinMax[2]*1.2, range3MinMax[3]*1.2)],
                 }    
    
        for entry in parameterValues:
            qieID, serial,  qieNum, i_capID, qieRange, directory, timestamp, slope, offset = entry
            hists[qieRange][0].Fill(slope)
            hists[qieRange][1].Fill(offset)
            hists[qieRange][0].Fill(slope)
            hists[qieRange][1].Fill(offset)


        outputParamRootFile = TFile("%s/fitResults_%s.root"%(outputDirectory, uniqueID.replace(" ","_")),"update")

        outputParamRootFile.cd("SummaryPlots")

        # print hists
        for i_range in hists:
            hists[i_range][0].Write()
            hists[i_range][1].Write()
            
        outputParamRootFile.Close()
        c1 = TCanvas()
        c1.cd()
        c1.Divide(2,2)

        c1.cd(1)
        hists[0][0].Draw()
        c1.cd(2)
        hists[1][0].Draw()
        c1.cd(3)
        hists[2][0].Draw()
        c1.cd(4)
        hists[3][0].Draw()
        c1.SaveAs(outputDirectory+"Slopes_%s.pdf"%str(uniqueID).replace(" ","_"))

        c1.cd(1)
        hists[0][1].Draw()
        c1.cd(2)
        hists[1][1].Draw()
        c1.cd(3)
        hists[2][1].Draw()
        c1.cd(4)
        hists[3][1].Draw()
        c1.SaveAs(outputDirectory+"Offsets_%s.pdf"%str(uniqueID).replace(" ","_"))
    

if __name__=="__main__":

    import sys
    
    if len(sys.argv)==2:
        outFile = sys.argv[1]

        graphParamDist(outFile)
