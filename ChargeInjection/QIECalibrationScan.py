from datetime import date, datetime
from time import sleep
import os
from optparse import OptionParser
import subprocess
import sys

from numpy import std
from ROOT import *

#script to control DAC
from DAC import *

from scans import *

# from adcTofC import *
# from fitGraphs import *
from adcTofC_linearized import *
from fitGraphs_linearized import *
from GraphParamDist import *


slotDict = {1:[2,5,7,8,10],
	    }

sys.path.insert(0, '/home/hep/ChargeInjector/hcal_teststand_scripts_HE')

from hcal_teststand.uhtr import *
#from hcal_teststand import *
from hcal_teststand.hcal_teststand import *
#from hcal_teststand.qie import *

from ngccmEmulatorCommands import *
from simpleLinkMap import getSimpleLinkMap

import sqlite3 as lite

from TDC_scan import *

from read_histo import read_histo

from checkLinks_Old import *

#from SerialNumberMap import *

gROOT.SetBatch(kTRUE)

orbitDelay = 30
GTXreset = 1
CDRreset = 1

### Which slot number contains which injection card {slot:card}
### slots are numbered 1 to 8 (slot 10 contains the DAC, slot 9 has an extra injection card)
### The purpose of this dictionary is to allow for swapping out a nonfunctional card
injectionCardSlotMapping = {1:1,
			    2:2,
			    3:3,
			    4:4,
			    5:5,
			    6:6,
			    7:7,
			    8:8,
			    }

## Which histogram does DAC channel 00 fill on each injection board slot ( { histogram : injectionslot} )
## check this mapping with new injection card (inject one channel at a time, see which histogram is filled)

dac13Mapping = { 1  : 1 ,
		 2  : 2 ,
		 3  : 3 ,
		 4  : 4 ,
		 5  : 5 ,
		 6  : 6 ,
		 7  : 7 ,
		 8  : 8 ,
		 9  : 9 ,
		 10 : 10 ,
		 11 : 11 ,
		 12 : 12,
		 }

fakesimpleCardMap = {1  : 1 , 2  : 2 , 3  : 3 , 4  : 4 , 5  : 5 , 6  : 6 , 7  : 7 , 8  : 8 , 9  : 9 , 10 : 10, 11 : 11, 12 : 12, 13 : 13, 14 : 14, 15 : 15, 16 : 16, 17 : 17, 18 : 18, 19 : 19, 20 : 20, 21 : 21, 22 : 22, 23 : 23, 24 : 24, 25 : 25, 26 : 26, 27 : 27, 28 : 28, 29 : 29, 30 : 30, 31 : 31, 32 : 32, 
                     }                     
		
#Scans over a number of DAC settings, getting the uHTR histogram and read out the mean and RMS for each scan point
#Returns a dictionary with the ADC values at each DAC LSB
#setFixRangeModeOff(ts,slotDict)
def doScan(ts, scanRange = range(30), qieRange=0, sepCapID = True, SkipScan = False, outputDirectory = ""):

	print 'SepCap', sepCapID
        setFixRangeModeOn(ts,slotDict,qieRange)

	print orbitDelay
	getGoodLinks(ts, orbitDelay=orbitDelay, GTXreset = GTXreset, CDRreset = CDRreset, forceInit=True)

        relayOn = False
        if qieRange==0: relayOn = True

	results = {}
	for i in scanRange:

		histName = ""
		histName = "Calibration_LSB_{0}".format( i )
		if not SkipScan:
			print 'LSB', i, relayOn
			setDAC(i,relayOn=relayOn)
			getGoodLinks(ts, orbitDelay=orbitDelay, GTXreset = GTXreset, CDRreset = CDRreset)
			print 'GettingHist'
			fName = outputDirectory+histName

			while not os.path.exists(fName):
				if sepCapID:
					fName = uhtr.get_histos(ts,n_orbits=4000, sepCapID=1, file_out_base=outputDirectory+histName)
				else:
					fName = uhtr.get_histos(ts,n_orbits=4000, sepCapID=0, file_out_base=outputDirectory+histName)
		else:
			fName = outputDirectory+histName
		print 'ReadingHist'
		vals = read_histo(fName,sepCapID,int(qieRange))
		results[i] = vals

#		print_links(ts)
	if not SkipScan:
		setDAC(0,relayOn=relayOn)
                setFixRangeModeOff(ts,slotDict)

	getGoodLinks(ts, orbitDelay=orbitDelay, GTXreset = GTXreset, CDRreset = CDRreset, forceInit=True)

	# for i_crate in ts.fe_crates:
	# 	for i_slot in ts.qie_slots[0]:
	# 		print '-'*20
	# 		print 'Crate %i Slot %i Status'%(i_crate,i_slot)
	# 		print_qie_status(ts,i_crate,i_slot)


	return results

# def ShuntScan(ts, shuntSettings = range(12)):
	


#Provides the mapping of card slot to uHTR link
#Sets the QIE card in one slot to fixed range mode in range 2, injects charge equivalent to ADC 0, and looks for which links read 128 (bottom of range 2)

#NEEDS TO BE REWRITTEN WITH NEW MAPPING SCHEME
		
def mapInjectorToQIE(ts, linkMap, outputDirectory = ''):
	"""
	Finds the mapping of which injector card is connected to which QIE card (and which half)
	
        Inject with one channel and see which QIE is read out (injects at a very high value, all other channels will be pedestals)
	"""
	print 'Set DAC, get good links'
	setDAC(dacLSB = 30000, dacChannel = 0,relayOn=False)
	getGoodLinks(ts, orbitDelay=orbitDelay, GTXreset = GTXreset, CDRreset = CDRreset, forceInit=True)


	print 'Get/Read Histos'
	fName = uhtr.get_histos(ts,n_orbits=300, sepCapID=0, file_out_base = outputDirectory+"mappingHist")
	vals = read_histo(fName,False)

	setDAC(dacLSB = 0,relayOn=False)

	getGoodLinks(ts, orbitDelay=orbitDelay, GTXreset = GTXreset, CDRreset = CDRreset, forceInit=True)

	mapping = {}

	simpleCardMap = {}
	for i in vals:
		# set to fixed range, not sep capID
		# setting to fixed range 1, injecting at a range 3 value
		# filled histograms should be at 127, empty histograms should at 64
		if vals[i]['mean'] > 96:
			histNum = i
			filledQIE = histNum%12 + 1
			injectionCardSlot = dac13Mapping[filledQIE]
			link = vals[i]['link']
			if link%6 < 3: half = 'TOP'
			else: half = 'BOTTOM'
			mapping[injectionCardSlot] = {'link' : link,
						      'id'   : linkMap[link],
						      'half' : half,
						      'connector' : int(histNum/12)
						      }
			print int(histNum/12), injectionCardSlot
			simpleCardMap[int(histNum/12)] = injectionCardSlotMapping[injectionCardSlot]

			
#	print_links(ts)

	return mapping, simpleCardMap

def QIECalibrationScan(options):
	##load teststand 904, will this be the correcto configuration for 
	ts = teststand("HEfnal",'/home/hep/ChargeInjector/hcal_teststand_scripts_HE/configuration/teststands.txt')

	global orbitDelay
#	orbitDelay = findMagicNumber(ts)
	orbitDelay = 22
	print orbitDelay

	## take data separated by capID
	sepCapID = options.sepCapID
	print "Separate capID =",sepCapID

	dacNum = getDACNumber()[0]

	## create directory structure:
	## in the end, it will be /InjectionData/date/Run_XX/CalMode_FixedRangeY/
	outputDirectory = "Data_CalibrationScans/%s/"%( str(date.today()) )

	if not os.path.exists(outputDirectory):
		os.system( "mkdir -pv "+outputDirectory )
		fileVersion = "Run_01/"
	else:
		tempfiles = os.listdir(outputDirectory)
		files = []
		for fName in tempfiles:
			if not 'Run_' in fName: continue
			if '.tgz' in fName: continue
			files.append(fName)
		files.sort()
		lastNum = int(files[-1].split("_")[-1])
		fileVersion = "Run_%02i/"%(lastNum+1)

	outputDirectory += fileVersion
	os.system( "mkdir -pv "+outputDirectory )

        print '-'*30
	print 'Start Mapping'
        print '-'*30
	## run mapping of injection cards to qie cards

        setDAC(0)

	linkMap = getSimpleLinkMap(ts,orbitDelay,outputDirectory, slotDict)	
	#linkMap = {12: {'slot': 10, 'side': 'Top', 'unique_ID': '0x00000001 0x00000010', 'rbx': 1}, 13: {'slot': 10, 'side': 'Bottom', 'unique_ID': '0x00000001 0x00000010', 'rbx': 1}, 14: {'slot': 7, 'side': 'Top', 'unique_ID': '0x00000001 0x00000007', 'rbx': 1}, 15: {'slot': 7, 'side': 'Bottom', 'unique_ID': '0x00000001 0x00000007', 'rbx': 1}, 16: {'slot': 8, 'side': 'Top', 'unique_ID': '0x00000001 0x00000008', 'rbx': 1}, 17: {'slot': 8, 'side': 'Bottom', 'unique_ID': '0x00000001 0x00000008', 'rbx': 1}, 18: {'slot': 5, 'side': 'Top', 'unique_ID': '0x00000001 0x00000005', 'rbx': 1}, 19: {'slot': 5, 'side': 'Bottom', 'unique_ID': '0x00000001 0x00000005', 'rbx': 1}, 20: {'slot': 2, 'side': 'Top', 'unique_ID': '0x00000001 0x00000002', 'rbx': 1}, 21: {'slot': 2, 'side': 'Bottom', 'unique_ID': '0x00000001 0x00000002', 'rbx': 1}}

	# linkMap = {14: {'slot': 4, 'rm': 4, 'side': 'Bottom', 'unique_ID': '0x73000000 0xd7a5c370', 'rbx': 1}, 15: {'slot': 4, 'rm': 4, 'side': 'Top', 'unique_ID': '0x73000000 0xd7a5c370', 'rbx': 1}, 16: {'slot': 3, 'rm': 4, 'side': 'Bottom', 'unique_ID': '0xcc000000 0xd7a98670', 'rbx': 1}, 17: {'slot': 3, 'rm': 4, 'side': 'Top', 'unique_ID': '0xcc000000 0xd7a98670', 'rbx': 1}, 18: {'slot': 2, 'rm': 4, 'side': 'Bottom', 'unique_ID': '0x86000000 0xd7a14370', 'rbx': 1}, 19: {'slot': 2, 'rm': 4, 'side': 'Top', 'unique_ID': '0x86000000 0xd7a14370', 'rbx': 1}, 20: {'slot': 1, 'rm': 4, 'side': 'Top', 'unique_ID': '0x70000000 0xd7b1b870', 'rbx': 1}, 21: {'slot': 1, 'rm': 4, 'side': 'Bottom', 'unique_ID': '0x70000000 0xd7b1b870', 'rbx': 1}}
	


	print 'got links'
	print linkMap

        simpleCardMap = fakesimpleCardMap
	###CHANGE THIS
	# injectionMapping, simpleCardMap = mapInjectorToQIE(ts, linkMap, outputDirectory)
	
	# print injectionMapping
	# print simpleCardMap



	qieParamsLocal = lite.connect(outputDirectory+"qieCalibrationParameters.db")
	cursorLocal = qieParamsLocal.cursor()
	cursorLocal.execute("create table if not exists qieparams(id STRING, serial INT, qie INT, capID INT, range INT, directoryname STRING, date STRING, slope REAL, offset REAL)")


	print_links(ts)

	### Get list of histograms (QIE channels) from injeciton mapping
	histoList1 = []
	
        ### linkMap, each key is a link number, there are 6 channels per link
	linkList = linkMap.keys()
	linkList.sort()
	for i_link in linkList:
		for ih in range(6):
			histoList1.append(ih+i_link*6)



        ###THIS NEEDS TO CHANGE WHEN THE MAPPING IS FIXED
	# histoList2 = []
	# linkGroups = simpleCardMap.keys()
	# linkGroups.sort()
	# for i_link in linkGroups:
	# 	for ih in range(12):
	# 		histoList2.append(ih+i_link*12)

        # ### what was my logic here????
        # ### Was it that it needs to appear in both lists????
	# histoList = list(set(histoList1) & set(histoList2))
        histoList = histoList1

        print '-'*30
        print 'Histograms List'
        print '-'*30
	print histoList

	minRange = 0
	maxRange = 4

	if not int(options.range) == -1:
		minRange = int(options.range)
		maxRange = int(options.range)+1		


	## creates a 'cardData.txt' file in the output directory, containing the list of injection cards used, the mapping between 
	dataFile = open(outputDirectory+"cardData.txt",'w')
	
	line = '%s\n'%str(datetime.now())
	line += "DAC %s Used\n\n" %dacNum

        ### THIS NEEDS TO CHANGE WHEN THE MAPPING IS FIGURED OUT

# 	for i_injCard in injectionMapping:
# 		line += "Injection Card %i\n"%i_injCard
# #		line += "  slot: %s\n"%injectionMapping[i_injCard]['slot']
# 		line += "  Connected to QIE:\n"
# 		line += "    id: %s\n"%injectionMapping[i_injCard]['id']
# 		line += "    half: %s\n"%injectionMapping[i_injCard]['half']
# 		connector = int(injectionMapping[i_injCard]['connector'])
# 		line += "    links: %i%i%i\n"%(connector*3, connector*3+1, connector*3+2)
# 		line += "    histss: %i-%i\n"%(connector*12, connector*12+11)

# 	line += '*'*80 + '\n'
# 	line += 'Parameters that can be pulled for redoing the fit \n'
# 	line += '*'*80 + '\n'

# 	line += 'simpleCardMap '
# 	line += str(simpleCardMap)
# 	line += '\n'
# 	line += 'injectionMapping '
# 	line += str(injectionMapping)
# 	line += '\n'
# 	line += 'minRange '
# 	line += str(minRange)
# 	line += '\n'
# 	line += 'maxRange '
# 	line += str(maxRange)
# 	line += '\n'
	dataFile.write(line)
	dataFile.close()	

	outputParamFile = open(outputDirectory+"calibrationParams.txt",'w')
	outputParamFile.write('(qieID, serialNum, qieNum, capID, qieRange, outputDirectory, timeStamp, slope, offset)\n')

        graphs = {}
        for qieRange in range(minRange, maxRange):

		scanRange = scanValues[qieRange]
                print scanValues
                print 'List of scan DAC points range %i'%qieRange
		print scanRange


		getGoodLinks(ts, orbitDelay=orbitDelay, GTXreset = GTXreset, CDRreset = CDRreset)
				
                rangeMode = "FixRange_%i"%qieRange

		rangeOutputDirectory = outputDirectory + "Data_%s/"%(rangeMode)
		os.system( "mkdir -pv "+rangeOutputDirectory )
		results = doScan(ts, scanRange, qieRange, sepCapID=sepCapID, SkipScan=options.SkipScan, outputDirectory = rangeOutputDirectory)
		graphs[qieRange] = makeADCvsfCgraphSepCapID(scanRange,results, histoList, cardMap = simpleCardMap, dac=dacNum)

        for ih in histoList:
                if options.SkipFit: continue

                qieID = injectionMapping[simpleCardMap[int(ih/12)]]['id']
                serial = mapUIDtoSerial[qieID]
                qieNum = ih%24 + 1

                graphList = []

		if 0 in graphs:
                        graphList.append(graphs[0][ih])
		else:
                        graphList.append(None)
                if 1 in graphs:
                        graphList.append(graphs[1][ih])
                else:
                        graphList.append(None)
                if 2 in graphs:
                        graphList.append(graphs[2][ih])
                else:
                        graphList.append(None)
                if 3 in graphs:
                        graphList.append(graphs[3][ih])
                else:
                        graphList.append(None)

                rangeOutputDirectory = outputDirectory+'/outputPlots/'
                os.system( "mkdir -pv "+rangeOutputDirectory )

                params = doFit_combined(graphList,int(qieRange), True, qieNum, qieID.replace(' ', '_'),options.useCalibrationMode, rangeOutputDirectory)

                print params
                for i_range in graphs:
                        for i_capID in range(4):
                                print i_range, i_capID
                                print params[i_range]
                                print params[i_range][i_capID]

#                               print params, i_range, i_capID                                                                       
#                               print params[i_range]                                                                
                                values = (qieID, serial, qieNum, i_capID, i_range, outputDirectory, str(datetime.now()), params[i_range][i_capID][0], params[i_range][i_capID][1])

                                cursorLocal.execute("insert into qieparams values (?, ?, ?, ?, ?, ?, ?, ? , ?)",values)

                                outputParamFile.write(str(values)+'\n')


	cursorLocal.close()
	qieParamsLocal.commit()
	qieParamsLocal.close()
	outputParamFile.close()
	
	graphParamDist(outputDirectory+"qieCalibrationParameters.db")

	### Graph parameters

	### Range Transition Errors

	
	qieTestParamsLocal = lite.connect(outputDirectory+"qieTestParameters.db")
	cursorLocal = qieTestParamsLocal.cursor()
	cursorLocal.execute("create table if not exists qietestparams(id STRING, qie INT, tdcstart REAL)") 



	if options.RunExtraTests:
		
		tdc_start_current = runTDCScan(mapping=simpleCardMap, dac=dacNum, orbitDelay=orbitDelay, outputDir = outputDirectory)

		for ih in histoList:
			tdcstart = tdc_start_current[ih]

			qieID = injectionMapping[simpleCardMap[int(ih/12)]]['id']
			qieNum = ih%24 + 1

			values = (qieID, qieNum, tdcstart)
			
			cursorLocal.execute("insert into qietestparams values (?, ?, ?)",values)

	cursorLocal.close()
	qieTestParamsLocal.commit()
	qieTestParamsLocal.close()
		
if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-r", "--range", dest="range", default=-1,type='int',
			  help="Specify range to be used in scan (default is -1, which does all 4 ranges)" )
	parser.add_option("--NoSepCapID", action="store_false",dest="sepCapID",default=False,
			  help="don't separate the different capID histograms")
	parser.add_option("--SkipScan", action="store_true",dest="SkipScan",default=False,
			  help="Skip the scan, using presaved scan")
	parser.add_option("--SkipFit", action="store_true",dest="SkipFit",default=False,
			  help="Skip the fitting step")
	parser.add_option("--NoLinkInit", action="store_true",dest="NoLinkInit",default=False,
			  help="Skip the scan, using presaved scan")
	parser.add_option("--SkipTDC", action="store_false",dest="RunTDCScan",default=True,
			  help="Skip the TDC scans")
	parser.add_option("--SkipExtraTests", action="store_false",dest="RunExtraTests",default=True,
			  help="Skip the Range Transistion and TDC tests")

	(options, args) = parser.parse_args()
        print 'start'
	if not options.range == -1:
		options.RunTDCScan=False
	if not options.RunTDCScan:
		options.RunExtraTests = False

        options.RunExtraTests = False

	QIECalibrationScan(options)


