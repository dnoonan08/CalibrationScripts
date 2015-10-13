from ROOT import *

def graphParamDist(paramFileName):
    if 'calibrationParams.txt' in paramFileName:
        outputDirectory = paramFileName.split('calibrationParams.txt')[0]
    else:
        outputDirectory = paramFileName + "/"
    outputParamFile = open(outputDirectory+"calibrationParams.txt",'r')

    hists = {0:{'all':[TH1F("Range0Slopes","Range0Slopes",50,3.,3.5), TH1F("Range0Offsets","Range0Offsetss",50,-20,-100)],
                0:[TH1F("Range0SlopesCapID0","Range0SlopesCapID0",50,3.,3.5), TH1F("Range0OffsetsCapID0","Range0OffsetsCapID0",50,-20,-100)],
                1:[TH1F("Range0SlopesCapID1","Range0SlopesCapID1",50,3.,3.5), TH1F("Range0OffsetsCapID1","Range0OffsetsCapID1",50,-20,-100)],
                2:[TH1F("Range0SlopesCapID2","Range0SlopesCapID2",50,3.,3.5), TH1F("Range0OffsetsCapID2","Range0OffsetsCapID2",50,-20,-100)],
                3:[TH1F("Range0SlopesCapID3","Range0SlopesCapID3",50,3.,3.5), TH1F("Range0OffsetsCapID3","Range0OffsetsCapID3",50,-20,-100)],
                },
             1:{'all':[TH1F("Range1Slopes","Range1Slopes",50,22.,28.), TH1F("Range1Offsets","Range1Offsetss",50,-20,-100)],
                0:[TH1F("Range1SlopesCapID0","Range1SlopesCapID0",50,22.,28.), TH1F("Range1OffsetsCapID0","Range1OffsetsCapID0",50,-20,-100)],
                1:[TH1F("Range1SlopesCapID1","Range1SlopesCapID1",50,22.,28.), TH1F("Range1OffsetsCapID1","Range1OffsetsCapID1",50,-20,-100)],
                2:[TH1F("Range1SlopesCapID2","Range1SlopesCapID2",50,22.,28.), TH1F("Range1OffsetsCapID2","Range1OffsetsCapID2",50,-20,-100)],
                3:[TH1F("Range1SlopesCapID3","Range1SlopesCapID3",50,22.,28.), TH1F("Range1OffsetsCapID3","Range1OffsetsCapID3",50,-20,-100)],
                },
             2:{'all':[TH1F("Range2Slopes","Range2Slopes",50,190.,210.), TH1F("Range2Offsets","Range2Offsetss",50,-20,-100)],
                0:[TH1F("Range2SlopesCapID0","Range2SlopesCapID0",50,190.,210.), TH1F("Range2OffsetsCapID0","Range2OffsetsCapID0",50,-20,-100)],
                1:[TH1F("Range2SlopesCapID1","Range2SlopesCapID1",50,190.,210.), TH1F("Range2OffsetsCapID1","Range2OffsetsCapID1",50,-20,-100)],
                2:[TH1F("Range2SlopesCapID2","Range2SlopesCapID2",50,190.,210.), TH1F("Range2OffsetsCapID2","Range2OffsetsCapID2",50,-20,-100)],
                3:[TH1F("Range2SlopesCapID3","Range2SlopesCapID3",50,190.,210.), TH1F("Range2OffsetsCapID3","Range2OffsetsCapID3",50,-20,-100)],
                },
             3:{'all':[TH1F("Range3Slopes","Range3Slopes",50,1840.,1890.), TH1F("Range3Offsets","Range3Offsetss",50,-20,-100)],
                0:[TH1F("Range3SlopesCapID0","Range3SlopesCapID0",50,1840.,1890.), TH1F("Range3OffsetsCapID0","Range3OffsetsCapID0",50,-20,-100)],
                1:[TH1F("Range3SlopesCapID1","Range3SlopesCapID1",50,1840.,1890.), TH1F("Range3OffsetsCapID1","Range3OffsetsCapID1",50,-20,-100)],
                2:[TH1F("Range3SlopesCapID2","Range3SlopesCapID2",50,1840.,1890.), TH1F("Range3OffsetsCapID2","Range3OffsetsCapID2",50,-20,-100)],
                3:[TH1F("Range3SlopesCapID3","Range3SlopesCapID3",50,1840.,1890.), TH1F("Range3OffsetsCapID3","Range3OffsetsCapID3",50,-20,-100)],
                },
             }
    
    for line in outputParamFile:
        qieID, qieNum, i_capID, qieRange, slope, offset = eval(line)
        hists[qieRange][i_capID][0].Fill(slope)
        hists[qieRange][i_capID][1].Fill(offset)
        hists[qieRange]['all'][0].Fill(slope)
        hists[qieRange]['all'][1].Fill(offset)

    outputParamRootFile = TFile(outputDirectory+"calibrationParams.root",'recreate')

    for r in hists:
        for c in hists[r]:
            hists[r][c][0].Write()
            hists[r][c][1].Write()
            
    outputParamRootFile.Close()

if __name__=="__main__":

    import sys
    
    if len(sys.argv)==2:
        outFile = sys.argv[1]

        graphParamDist(outFile)
