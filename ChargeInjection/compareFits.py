import sqlite3

from ROOT import *

import sys

from optparse import OptionParser
parser = OptionParser()
parser.add_option("--dir1", dest="fileName_1", default="temp")
parser.add_option("--dir2", dest="fileName_2", default="temp")
parser.add_option("--noTop", action="store_false", dest="useTop",default=True)
parser.add_option("--noBot", action="store_false", dest="useBottom",default=True)


(options, args) = parser.parse_args()

useTop = options.useTop
useBottom = options.useBottom
fileName_1 = options.fileName_1
fileName_2 = options.fileName_2

qieList = []
if useTop:
    qieList += range(1,13)
if useBottom:
    qieList += range(13,25)

if not '.db' in fileName_1:
    print "Wrong file type:", fileName_1
if not '.db' in fileName_2:
    print "Wrong file type:", fileName_2

uniqueIDs = ['0x46000000 0xb9fbd770',
             '0x35000000 0xba1e0670',
             '0xb2000000 0xba274170',
             '0x20000000 0xba09fb70',
             ]


DB_1 = sqlite3.connect(fileName_1)
DB_2 = sqlite3.connect(fileName_2)

cursor_1 = DB_1.cursor()
cursor_2 = DB_2.cursor()

params_1 = cursor_1.execute("select * from qieparams where id = ?",(uniqueIDs[0],)).fetchall()
params_2 = cursor_2.execute("select * from qieparams where id = ?",(uniqueIDs[0],)).fetchall()

slopes_1  = [[],[],[],[]]
offsets_1 = [[],[],[],[]]

slopes_2  = [[],[],[],[]]
offsets_2 = [[],[],[],[]]

for iqie in qieList:
#    print iqie
    slopes_1[0].append([0,0,0,0])
    slopes_1[1].append([0,0,0,0])
    slopes_1[2].append([0,0,0,0])
    slopes_1[3].append([0,0,0,0])
    offsets_1[0].append([0,0,0,0])
    offsets_1[1].append([0,0,0,0])
    offsets_1[2].append([0,0,0,0])
    offsets_1[3].append([0,0,0,0])
    for param in params_1:
        if param[1]==iqie:        
            slopes_1[param[3]][-1][param[2]]=param[-2]
            offsets_1[param[3]][-1][param[2]]=param[-1]

    slopes_2[0].append([0,0,0,0])
    slopes_2[1].append([0,0,0,0])
    slopes_2[2].append([0,0,0,0])
    slopes_2[3].append([0,0,0,0])
    offsets_2[0].append([0,0,0,0])
    offsets_2[1].append([0,0,0,0])
    offsets_2[2].append([0,0,0,0])
    offsets_2[3].append([0,0,0,0])
    for param in params_2:
        if param[1]==iqie:
            slopes_2[param[3]][-1][param[2]]=param[-2]
            offsets_2[param[3]][-1][param[2]]=param[-1]

#print slopes_1

from array import array
            
slope_DB1_0 = array('d',[b[0] for b in slopes_1[0]] + [b[1] for b in slopes_1[0]] + [b[2] for b in slopes_1[0]] + [b[3] for b in slopes_1[0]])
slope_DB2_0 = array('d',[b[0] for b in slopes_2[0]] + [b[1] for b in slopes_2[0]] + [b[2] for b in slopes_2[0]] + [b[3] for b in slopes_2[0]])
slope_DB1_1 = array('d',[b[0] for b in slopes_1[1]] + [b[1] for b in slopes_1[1]] + [b[2] for b in slopes_1[1]] + [b[3] for b in slopes_1[1]])
slope_DB2_1 = array('d',[b[0] for b in slopes_2[1]] + [b[1] for b in slopes_2[1]] + [b[2] for b in slopes_2[1]] + [b[3] for b in slopes_2[1]])
slope_DB1_2 = array('d',[b[0] for b in slopes_1[2]] + [b[1] for b in slopes_1[2]] + [b[2] for b in slopes_1[2]] + [b[3] for b in slopes_1[2]])
slope_DB2_2 = array('d',[b[0] for b in slopes_2[2]] + [b[1] for b in slopes_2[2]] + [b[2] for b in slopes_2[2]] + [b[3] for b in slopes_2[2]])
slope_DB1_3 = array('d',[b[0] for b in slopes_1[3]] + [b[1] for b in slopes_1[3]] + [b[2] for b in slopes_1[3]] + [b[3] for b in slopes_1[3]])
slope_DB2_3 = array('d',[b[0] for b in slopes_2[3]] + [b[1] for b in slopes_2[3]] + [b[2] for b in slopes_2[3]] + [b[3] for b in slopes_2[3]])

offset_DB1_0 = array('d',[b[0] for b in offsets_1[0]] + [b[1] for b in offsets_1[0]] + [b[2] for b in offsets_1[0]] + [b[3] for b in offsets_1[0]])
offset_DB2_0 = array('d',[b[0] for b in offsets_2[0]] + [b[1] for b in offsets_2[0]] + [b[2] for b in offsets_2[0]] + [b[3] for b in offsets_2[0]])
offset_DB1_1 = array('d',[b[0] for b in offsets_1[1]] + [b[1] for b in offsets_1[1]] + [b[2] for b in offsets_1[1]] + [b[3] for b in offsets_1[1]])
offset_DB2_1 = array('d',[b[0] for b in offsets_2[1]] + [b[1] for b in offsets_2[1]] + [b[2] for b in offsets_2[1]] + [b[3] for b in offsets_2[1]])
offset_DB1_2 = array('d',[b[0] for b in offsets_1[2]] + [b[1] for b in offsets_1[2]] + [b[2] for b in offsets_1[2]] + [b[3] for b in offsets_1[2]])
offset_DB2_2 = array('d',[b[0] for b in offsets_2[2]] + [b[1] for b in offsets_2[2]] + [b[2] for b in offsets_2[2]] + [b[3] for b in offsets_2[2]])
offset_DB1_3 = array('d',[b[0] for b in offsets_1[3]] + [b[1] for b in offsets_1[3]] + [b[2] for b in offsets_1[3]] + [b[3] for b in offsets_1[3]])
offset_DB2_3 = array('d',[b[0] for b in offsets_2[3]] + [b[1] for b in offsets_2[3]] + [b[2] for b in offsets_2[3]] + [b[3] for b in offsets_2[3]])


from numpy import *

axisTitle1 = fileName_1
axisTitle2 = fileName_2

if 'Data_CalibrationScans' in axisTitle1:
    split = axisTitle1.split('/')
    axisTitle1 = split[1] + '/' + split[2]
if 'Data_CalibrationScans' in axisTitle2:
    split = axisTitle2.split('/')
    axisTitle2 = split[1] + '/' + split[2]
    

line = TF1("line","x",-1e6,1e6)
slopegraph0 = TGraph(len(slope_DB1_0),slope_DB1_0, slope_DB2_0)
slopegraph0.SetMarkerStyle(2)
slopegraph0.GetXaxis().SetTitle("Slope (%s)" %axisTitle1)
slopegraph0.GetYaxis().SetTitle("Slope (%s)" %axisTitle2)
slopegraph0.GetXaxis().SetLimits(0.995*min(slope_DB1_0 + slope_DB2_0), 1.005*max(slope_DB1_0 + slope_DB2_0))
slopegraph0.GetYaxis().SetRangeUser(0.995*min(slope_DB1_0 + slope_DB2_0), 1.005*max(slope_DB1_0 + slope_DB2_0))
slopegraph1 = TGraph(len(slope_DB1_1),slope_DB1_1, slope_DB2_1)
slopegraph1.SetMarkerStyle(2)
slopegraph1.GetXaxis().SetTitle("Slope (%s)" %axisTitle1)
slopegraph1.GetYaxis().SetTitle("Slope (%s)" %axisTitle2)
slopegraph1.GetXaxis().SetLimits(0.995*min(slope_DB1_1 + slope_DB2_1), 1.005*max(slope_DB1_1 + slope_DB2_1))
slopegraph1.GetYaxis().SetRangeUser(0.995*min(slope_DB1_1 + slope_DB2_1), 1.005*max(slope_DB1_1 + slope_DB2_1))
slopegraph2 = TGraph(len(slope_DB1_1),slope_DB1_2, slope_DB2_2)
slopegraph2.SetMarkerStyle(2)
slopegraph2.GetXaxis().SetTitle("Slope (%s)" %axisTitle1)
slopegraph2.GetYaxis().SetTitle("Slope (%s)" %axisTitle2)
slopegraph2.GetXaxis().SetLimits(0.995*min(slope_DB1_2 + slope_DB2_2), 1.005*max(slope_DB1_2 + slope_DB2_2))
slopegraph2.GetYaxis().SetRangeUser(0.995*min(slope_DB1_2 + slope_DB2_2), 1.005*max(slope_DB1_2 + slope_DB2_2))
slopegraph3 = TGraph(len(slope_DB1_1),slope_DB1_3, slope_DB2_3)
slopegraph3.SetMarkerStyle(2)
slopegraph3.GetXaxis().SetTitle("Slope (%s)" %axisTitle1)
slopegraph3.GetYaxis().SetTitle("Slope (%s)" %axisTitle2)
slopegraph3.GetXaxis().SetLimits(0.995*min(slope_DB1_3 + slope_DB2_3), 1.005*max(slope_DB1_3 + slope_DB2_3))
slopegraph3.GetYaxis().SetRangeUser(0.995*min(slope_DB1_3 + slope_DB2_3), 1.005*max(slope_DB1_3 + slope_DB2_3))

offsetgraph0 = TGraph(len(offset_DB1_0),offset_DB1_0, offset_DB2_0)
offsetgraph0.SetMarkerStyle(2)
offsetgraph0.GetXaxis().SetTitle("Offset (%s)" %axisTitle1)
offsetgraph0.GetYaxis().SetTitle("Offset (%s)" %axisTitle2)
offsetgraph0.GetXaxis().SetLimits(0.995*min(offset_DB1_0 + offset_DB2_0), 1.005*max(offset_DB1_0 + offset_DB2_0))
offsetgraph0.GetYaxis().SetRangeUser(0.995*min(offset_DB1_0 + offset_DB2_0), 1.005*max(offset_DB1_0 + offset_DB2_0))
offsetgraph1 = TGraph(len(offset_DB1_1),offset_DB1_1, offset_DB2_1)
offsetgraph1.SetMarkerStyle(2)
offsetgraph1.GetXaxis().SetTitle("Offset (%s)" %axisTitle1)
offsetgraph1.GetYaxis().SetTitle("Offset (%s)" %axisTitle2)
offsetgraph1.GetXaxis().SetLimits(0.995*min(offset_DB1_1 + offset_DB2_1), 1.005*max(offset_DB1_1 + offset_DB2_1))
offsetgraph1.GetYaxis().SetRangeUser(0.995*min(offset_DB1_1 + offset_DB2_1), 1.005*max(offset_DB1_1 + offset_DB2_1))
offsetgraph2 = TGraph(len(offset_DB1_1),offset_DB1_2, offset_DB2_2)
offsetgraph2.SetMarkerStyle(2)
offsetgraph2.GetXaxis().SetTitle("Offset (%s)" %axisTitle1)
offsetgraph2.GetYaxis().SetTitle("Offset (%s)" %axisTitle2)
offsetgraph2.GetXaxis().SetLimits(0.995*min(offset_DB1_2 + offset_DB2_2), 1.005*max(offset_DB1_2 + offset_DB2_2))
offsetgraph2.GetYaxis().SetRangeUser(0.995*min(offset_DB1_2 + offset_DB2_2), 1.005*max(offset_DB1_2 + offset_DB2_2))
offsetgraph3 = TGraph(len(offset_DB1_1),offset_DB1_3, offset_DB2_3)
offsetgraph3.SetMarkerStyle(2)
offsetgraph3.GetXaxis().SetTitle("Offset (%s)" %axisTitle1)
offsetgraph3.GetYaxis().SetTitle("Offset (%s)" %axisTitle2)
offsetgraph3.GetXaxis().SetLimits(0.995*min(offset_DB1_3 + offset_DB2_3), 1.005*max(offset_DB1_3 + offset_DB2_3))
offsetgraph3.GetYaxis().SetRangeUser(0.995*min(offset_DB1_3 + offset_DB2_3), 1.005*max(offset_DB1_3 + offset_DB2_3))
    
    


c1 = TCanvas("c1","c1",1200,1200)
oneLine = TF1("oneLine","x",-1e6,1e6)
oneLineUp = TF1("oneLineUp","1.02*x",-1e6,1e6)
oneLineDown = TF1("oneLineDown","0.98*x",-1e6,1e6)
oneLine.SetLineColor(kRed)
oneLineDown.SetLineColor(kRed)
oneLineUp.SetLineColor(kRed)
oneLineDown.SetLineStyle(2)
oneLineUp.SetLineStyle(2)

c1.Divide(2,2)
c1.cd(1)
slopegraph0.Draw("ap")
oneLine.Draw("same")
c1.cd(2)
slopegraph1.Draw("ap")
oneLine.Draw("same")
c1.cd(3)
slopegraph2.Draw("ap")
oneLine.Draw("same")
c1.cd(4)
slopegraph3.Draw("ap")
oneLine.Draw("same")

# def savePlots(plotNames):
    
