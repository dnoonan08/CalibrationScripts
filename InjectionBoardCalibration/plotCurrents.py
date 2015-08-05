from ROOT import *
import sys
import os
from array import array
import sqlite3 as lite


gROOT.SetBatch()

min = -1
max = 99999
if '-min' in sys.argv:
    i = sys.argv.index('-min')
    min = sys.argv[i+1]
    sys.argv.remove('-min')
    sys.argv.remove(min)
if '-max' in sys.argv:
    i = sys.argv.index('-max')
    max = sys.argv[i+1]
    sys.argv.remove('-max')
    sys.argv.remove(max)

print min, max

min = float(min)
max = float(max)

if len(sys.argv) < 2:
    print 'Requires a file (or list of files) for which the plots should be made'
    sys.exit()

rangeOut = ''
if min > -1:
    rangeOut += '_min'+str(int(min))
if max < 99999:
    rangeOut += '_max'+str(int(max))

fList = []

outFile = TFile("currentTGraphs.root",'recreate')

for fName in sys.argv[1:]:
    if not os.path.exists(fName):
        print 'File', fName,'does not exist'
    else:
        fList.append(fName)

outputText = open('slopeOffset.csv','w')

outputDB = lite.connect("SlopesOffsets.db")
cursor = outputDB.cursor()

cursor.execute("create table if not exists cardcal(card INT, dac INT, pigtail INT, rangelow REAL, rangehigh REAL, offset REAL, slope REAL)")


for fName in fList:
    values = fName.split('/')[-1].split('.txt')[0].split('_')
    card= int(values[3])
    dac = int(values[5])
    pigtail = int(values[7])

    lsb_list = []
    currentMean_list = []
    currentStdev_list = []
    calFile = open(fName,'read')
    for line in calFile:
        values = line.split(',')
        if len(values) != 5:
            continue
        if float(values[0]) < min or float(values[0]) > max:
            continue
        lsb_list.append(float(values[0]))
        currentMean_list.append(float(values[1]))
        currentStdev_list.append(float(values[2]))
    lsb = array('d',lsb_list)
    lsbErr = array('d',[0]*len(lsb_list))
    current = array('d',currentMean_list)
    currentErr = array('d',currentStdev_list)

    graph = TGraphErrors(len(lsb),lsb,current,lsbErr,currentErr)
    graph.SetNameTitle("currentCalibration_card%i_dac%i_pigtail%i%s"%(card,dac,pigtail,rangeOut),"currentCalibration_card%i_dac%i_pigtail%i%s"%(card,dac,pigtail,rangeOut))

    jumpLSBs = []
    changes = []
    for i in range(1,len(currentMean_list)):
        change = currentMean_list[i] - currentMean_list[i-1]
        lsbChange = lsb_list[i] - lsb_list[i-1]
        minSlope = -3e-8
        if change > lsbChange*minSlope:
            jumpLSBs.append(lsb[i])
            changes.append(change)
    print jumpLSBs
    print changes

    fitRanges = []
    lastJump = 0
    for i in jumpLSBs:
        fitRanges.append( (lastJump, i-1) )
        lastJump = i
    fitRanges.append( (lastJump,lsb[-1]) )

    print fitRanges
    lines = []

    for i in range( len(fitRanges) ):
        lines.append(TF1('line'+str(i),'pol1',fitRanges[i][0],fitRanges[i][1] ) )
        graph.Fit('line'+str(i),"","",fitRanges[i][0],fitRanges[i][1] )


    c1 = TCanvas()
    graph.Draw("ap")
    for l in lines: l.Draw("same")
    c1.SaveAs("plots/"+graph.GetName()+".pdf")

    cursor.execute("delete from cardcal where card=? and dac=? and pigtail=?",(card, dac, pigtail))
    for line in lines:
        print '%i,%i,%i,%f,%f,%.12f,%.12f\n'%(card, dac, pigtail,line.GetXmin(),line.GetXmax(),line.GetParameter(0), line.GetParameter(1))

        output = '%i,%i,%i,%f,%f,%.12f,%.12f\n'%(card, dac, pigtail,line.GetXmin(),line.GetXmax(),line.GetParameter(0), line.GetParameter(1))
        outputText.write(output)


        cursor.execute("insert into cardcal values(?,?,?,?,?,?,?)",(card, dac, pigtail,line.GetXmin(),line.GetXmax(),line.GetParameter(0), line.GetParameter(1)))

    outFile.cd()
    graph.Write()


cursor.close()
outputDB.commit()
outputDB.close()
