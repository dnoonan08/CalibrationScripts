from ROOT import *
import sqlite3

gROOT.SetBatch(kTRUE)

def fillHistos(values):
    maxslopes = [max([x[-2] for x in values if x[3]==0]+[-1]),
                 max([x[-2] for x in values if x[3]==1]+[-1]),
                 max([x[-2] for x in values if x[3]==2]+[-1]),
                 max([x[-2] for x in values if x[3]==3]+[-1]),
                 ]

    minslopes = [min([x[-2] for x in values if x[3]==0]+[99999.]),
                 min([x[-2] for x in values if x[3]==1]+[99999.]),
                 min([x[-2] for x in values if x[3]==2]+[99999.]),
                 min([x[-2] for x in values if x[3]==3]+[99999.]),
                 ]

    maxoffsets = [max([x[-1] for x in values if x[3]==0]+[-9.99e+10]),
                  max([x[-1] for x in values if x[3]==1]+[-9.99e+10]),
                  max([x[-1] for x in values if x[3]==2]+[-9.99e+10]),
                  max([x[-1] for x in values if x[3]==3]+[-9.99e+10]),
                  ]
    
    minoffsets = [min([x[-1] for x in values if x[3]==0]+[99999.]),
                  min([x[-1] for x in values if x[3]==1]+[99999.]),
                  min([x[-1] for x in values if x[3]==2]+[99999.]),
                  min([x[-1] for x in values if x[3]==3]+[99999.]),
                  ]


    print minslopes
    print maxslopes

    print minoffsets
    print maxoffsets

    hists = {0:{'all':[TH1F("Range0Slopes","Range0Slopes",50,minslopes[0]-.1, maxslopes[0]+.1), TH1F("Range0Offsets","Range0Offsetss",50,-20,-100)],
                0:[TH1F("Range0SlopesCapID0","Range0SlopesCapID0",50,minslopes[0]-.1, maxslopes[0]+.1), TH1F("Range0OffsetsCapID0","Range0OffsetsCapID0",50,-20,-100)],
                1:[TH1F("Range0SlopesCapID1","Range0SlopesCapID1",50,minslopes[0]-.1, maxslopes[0]+.1), TH1F("Range0OffsetsCapID1","Range0OffsetsCapID1",50,-20,-100)],
                2:[TH1F("Range0SlopesCapID2","Range0SlopesCapID2",50,minslopes[0]-.1, maxslopes[0]+.1), TH1F("Range0OffsetsCapID2","Range0OffsetsCapID2",50,-20,-100)],
                3:[TH1F("Range0SlopesCapID3","Range0SlopesCapID3",50,minslopes[0]-.1, maxslopes[0]+.1), TH1F("Range0OffsetsCapID3","Range0OffsetsCapID3",50,-20,-100)],
                },
             1:{'all':[TH1F("Range1Slopes","Range1Slopes",50,minslopes[1]-.5, maxslopes[1]+.5), TH1F("Range1Offsets","Range1Offsetss",50,-20,-100)],
                0:[TH1F("Range1SlopesCapID0","Range1SlopesCapID0",50,minslopes[1]-.5, maxslopes[1]+.5), TH1F("Range1OffsetsCapID0","Range1OffsetsCapID0",50,-20,-100)],
                1:[TH1F("Range1SlopesCapID1","Range1SlopesCapID1",50,minslopes[1]-.5, maxslopes[1]+.5), TH1F("Range1OffsetsCapID1","Range1OffsetsCapID1",50,-20,-100)],
                2:[TH1F("Range1SlopesCapID2","Range1SlopesCapID2",50,minslopes[1]-.5, maxslopes[1]+.5), TH1F("Range1OffsetsCapID2","Range1OffsetsCapID2",50,-20,-100)],
                3:[TH1F("Range1SlopesCapID3","Range1SlopesCapID3",50,minslopes[1]-.5, maxslopes[1]+.5), TH1F("Range1OffsetsCapID3","Range1OffsetsCapID3",50,-20,-100)],
                },
             2:{'all':[TH1F("Range2Slopes","Range2Slopes",50,minslopes[2]-5., maxslopes[2]+5.), TH1F("Range2Offsets","Range2Offsetss",50,-20,-100)],
                0:[TH1F("Range2SlopesCapID0","Range2SlopesCapID0",50,minslopes[2]-5., maxslopes[2]+5.), TH1F("Range2OffsetsCapID0","Range2OffsetsCapID0",50,-20,-100)],
                1:[TH1F("Range2SlopesCapID1","Range2SlopesCapID1",50,minslopes[2]-5., maxslopes[2]+5.), TH1F("Range2OffsetsCapID1","Range2OffsetsCapID1",50,-20,-100)],
                2:[TH1F("Range2SlopesCapID2","Range2SlopesCapID2",50,minslopes[2]-5., maxslopes[2]+5.), TH1F("Range2OffsetsCapID2","Range2OffsetsCapID2",50,-20,-100)],
                3:[TH1F("Range2SlopesCapID3","Range2SlopesCapID3",50,minslopes[2]-5., maxslopes[2]+5.), TH1F("Range2OffsetsCapID3","Range2OffsetsCapID3",50,-20,-100)],
                },
             3:{'all':[TH1F("Range3Slopes","Range3Slopes",50,minslopes[3]-5., maxslopes[3]+5.), TH1F("Range3Offsets","Range3Offsetss",50,-20,-100)],
                0:[TH1F("Range3SlopesCapID0","Range3SlopesCapID0",50,minslopes[3]-5., maxslopes[3]+5.), TH1F("Range3OffsetsCapID0","Range3OffsetsCapID0",50,-20,-100)],
                1:[TH1F("Range3SlopesCapID1","Range3SlopesCapID1",50,minslopes[3]-5., maxslopes[3]+5.), TH1F("Range3OffsetsCapID1","Range3OffsetsCapID1",50,-20,-100)],
                2:[TH1F("Range3SlopesCapID2","Range3SlopesCapID2",50,minslopes[3]-5., maxslopes[3]+5.), TH1F("Range3OffsetsCapID2","Range3OffsetsCapID2",50,-20,-100)],
                3:[TH1F("Range3SlopesCapID3","Range3SlopesCapID3",50,minslopes[3]-5., maxslopes[3]+5.), TH1F("Range3OffsetsCapID3","Range3OffsetsCapID3",50,-20,-100)],
                },
             }    
    
    for entry in values:
        qieID, serial,  qieNum, i_capID, qieRange, directory, timestamp, slope, offset = entry
        hists[qieRange][i_capID][0].Fill(slope)
        hists[qieRange][i_capID][1].Fill(offset)
        hists[qieRange]['all'][0].Fill(slope)
        hists[qieRange]['all'][1].Fill(offset)

    return hists

def graphParamDist(paramFileName):
    if 'qieCalibrationParameters.db' in paramFileName:
        outputDirectory = paramFileName.split('qieCalibrationParameters.db')[0]
    else:
        outputDirectory = paramFileName + "/"


    paramDB = sqlite3.connect(outputDirectory+'qieCalibrationParameters.db')
    cursor = paramDB.cursor()

    

    qieCards = [x[0] for x in list(set(cursor.execute("select id from qieparams").fetchall()))]
    print qieCards

    for uniqueID in qieCards:
        print uniqueID
        parameterValues = cursor.execute("select * from qieparams where id = ?", [str(uniqueID)]).fetchall()

        hists = fillHistos(parameterValues)

        outputParamRootFile = TFile(outputDirectory+"calibrationParams_%s.root"%str(uniqueID).replace(" ","_"),'recreate')

        # print hists
        for i_range in hists:
            for i_capID in hists[i_range]:
                hists[i_range][i_capID][0].Write()
                hists[i_range][i_capID][1].Write()
            
        outputParamRootFile.Close()
        c1 = TCanvas()
        c1.cd()
        c1.Divide(2,2)

        c1.cd(1)
        hists[0]['all'][0].Draw()
        c1.cd(2)
        hists[1]['all'][0].Draw()
        c1.cd(3)
        hists[2]['all'][0].Draw()
        c1.cd(4)
        hists[3]['all'][0].Draw()
        c1.SaveAs(outputDirectory+"Slopes_%s.pdf"%str(uniqueID).replace(" ","_"))

        c1.cd(1)
        hists[0]['all'][1].Draw()
        c1.cd(2)
        hists[1]['all'][1].Draw()
        c1.cd(3)
        hists[2]['all'][1].Draw()
        c1.cd(4)
        hists[3]['all'][1].Draw()
        c1.SaveAs(outputDirectory+"Offsets_%s.pdf"%str(uniqueID).replace(" ","_"))
    

if __name__=="__main__":

    import sys
    
    if len(sys.argv)==2:
        outFile = sys.argv[1]

        graphParamDist(outFile)
