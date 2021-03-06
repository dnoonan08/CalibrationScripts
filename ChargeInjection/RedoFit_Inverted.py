from time import sleep
from datetime import date, datetime
import os
from optparse import OptionParser
import subprocess
import sys

from scans import *
from adcTofC_Inverted import *
from fitGraphs_Inverted import *
from ROOT import *
#from DAC import *

# sys.path.insert(0, '../../hcal_teststand_scripts')

# from hcal_teststand.uhtr import *
# from hcal_teststand import *
# from hcal_teststand.hcal_teststand import *
# from hcal_teststand.qie import *
# from checkLinks import *

from GraphParamDist import *

import sqlite3 as lite

from SerialNumberMap import *

# from RangeTransitionErrors import *

orbitDelay = 3507
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
			    9:9,
			    }

## Which histogram does DAC channel 00 fill on each injection board slot ( { histogram : injectionslot} )
## check this mapping with new injection card (inject one channel at a time, see which histogram is filled)

dac13Mapping = { 1  : 2 ,
		 2  : 4 ,
		 3  : 6 ,
		 4  : 8 ,
		 5  : 10,
		 6  : 12,
		 7  : 1 ,
		 8  : 3 ,
		 9  : 5 ,
		 10 : 7 ,
		 11 : 9 ,
		 12 : 11,
		 }

# def print_links(ts):
# 	linksGood, linkOutput, problemLinks = checkLinkStatus(ts)
# 	if not linksGood:
# 		print linkOutput
# 		print "Problem with Links:",problemLinks
# 	else:
# 		print 'Links Good'


def print_qie_range(ts, crate, slot):
	commands = []
	for i_qie in range(1, 25):
#		commands.append("get HF{0}-{1}-QIE{2}_FixRange".format(crate, slot, i_qie))
		commands.append("get HF{0}-{1}-QIE{2}_RangeSet".format(crate, slot, i_qie))
	raw_output = ngccm.send_commands_parsed(ts, commands)['output']
	for val in raw_output:
		if 'RangeSet' in val['cmd']:
			print val['cmd'], val['result']




def read_histo(file_in="", sepCapID=True, qieRange = 0):
	result = {}
	tf = TFile(file_in, "READ")
	tc = TCanvas("tc", "tc", 500, 500)
	rangeADCoffset = qieRange*64.
	if sepCapID:
		for i_link in range(24):
			for i_ch in range(4):
				histNum = 4*i_link + i_ch
				th = tf.Get("h{0}".format(histNum))
#				th.SetBinContent(1,0)
				info = {}
				info["link"] = i_link
				info["channel"] = i_ch
				info["mean"] = []
				info["rms"] = []
				for i_capID in range(4):
					offset = 64*(i_capID)
					if th.GetBinContent(2)==0 and th.GetBinContent(3)==0 and th.GetBinContent(4)==0: th.SetBinContent(1,0)
					th.GetXaxis().SetRangeUser(offset, offset+63)
					info["mean"].append(th.GetMean()-offset+rangeADCoffset)
					info["rms"].append(max(0.2, th.GetRMS()))
#					info["rms"].append(th.GetRMS())
				result[histNum] = info
		
	else:
		for i_link in range(24):
			for i_ch in range(4):
				histNum = 4*i_link + i_ch
				th = tf.Get("h{0}".format(histNum))
				info = {}
				info["link"] = i_link
				info["channel"] = i_ch
				info["mean"] = th.GetMean()
				info["rms"] = th.GetRMS()

				result[histNum] = info

	return result
		

def doScan(ts, scanRange = range(30), qieRange=0, useFixRange=True, useCalibrationMode=True, sepCapID = True, SkipScan = False, outputDirectory = ""):

	print 'SepCap', sepCapID


	results = {}
	for i in scanRange:
		histName = ""
		histName = "Calibration_LSB_{0}.root".format( i )
		fName = outputDirectory+histName
		vals = read_histo(fName,sepCapID,int(qieRange))
		results[i] = vals

	return results

# def getSimpleLinkMap(ts, outputDirectory):
# 	print 'Start Get Mapping'
# 	linkMap = {}

# 	setDAC(0)

# 	print_links(ts)
# 	for crate in ts.fe_crates:
# 		for slot in ts.qie_slots[0]:
# 			print slot
# 			print crate
# 			unique_ID_parsed = qie.get_unique_id(ts,crate,slot)
# 			print unique_ID_parsed
# 			unique_ID = "%s %s"%(unique_ID_parsed[0], unique_ID_parsed[1])
# 			print 'Set Fixed Range'
# 			set_fix_range_all(ts, crate, slot, True, 2)
# 			sleep(3)
# #			print_qie_range(ts,crate,slot)
# 			getGoodLinks(ts, orbitDelay=orbitDelay, GTXreset = 1, CDRreset = 1, forceInit=True)
# 			print_links(ts)
# 			fName = uhtr.get_histo(ts,uhtr_slot=ts.uhtr_slots[0],n_orbits=1000, sepCapID=0, file_out = outputDirectory+"mappingHist.root")
# 			vals = read_histo(fName,False)
# 			for i in range(0,96,4):
# 				link = int(i/4)
# 				if vals[i]['mean'] > 100:
# 					linkMap[link] = unique_ID

# 	print 'Done with Getting Mapping'
# 	return linkMap

		
# def mapInjectorToQIE(ts, outputDirectory = ''):
# 	"""
# 	Finds the mapping of which injector card is connected to which QIE card (and which half)
	
# 	Sets all cards to fixed range 1
# 	Injects a charge using DAC 13 which max out range 1	
# 	"""

# 	print 'get links'


# 	##### CHANGE THIS
# 	##### Test without injectors
# 	# linkMap = {12:'0x8d000000 0xaa24da70',
# 	# 	   13:'0x8d000000 0xaa24da70',
# 	# 	   14:'0x8d000000 0xaa24da70',
# 	# 	   15:'0x8d000000 0xaa24da70',
# 	# 	   16:'0x8d000000 0xaa24da70',
# 	# 	   17:'0x8d000000 0xaa24da70',
# 	# 	   }
# 	linkMap = getSimpleLinkMap(ts,outputDirectory)	
# 	print 'got links'
# #	print linkMap

	
# 	print_links(ts)

# 	for i_crate in ts.fe_crates:
# 		for i_slot in ts.qie_slots[0]:
# 			print 'Set Fixed Range'
# 			set_fix_range_all(ts, i_crate, i_slot, True, 1)
# 			sleep(3)
			
# 	print 'Set DAC, get hist'
# 	setDAC(dacLSB = 10000, dacChannel = 0)
# 	getGoodLinks(ts, orbitDelay=orbitDelay, GTXreset = 1, CDRreset = 1, forceInit=True)


# 	print 'Read Histos'
# 	fName = uhtr.get_histo(ts,uhtr_slot=ts.uhtr_slots[0],n_orbits=3000, sepCapID=0, file_out = outputDirectory+"mappingHist.root")
# 	vals = read_histo(fName,False)

# 	print_links(ts)

# 	setDAC(dacLSB = 0)

# 	for i_crate in ts.fe_crates:
# 		for i_slots in ts.qie_slots[0]:
# 			print 'Set Fixed Range off'
# 			set_fix_range_all(ts, i_crate, i_slot, False)
# 	sleep(3)
# 	getGoodLinks(ts, orbitDelay=orbitDelay, GTXreset = 1, CDRreset = 1, forceInit=True)
	
# 	print_links(ts)

# 	mapping = {}
# 	simpleCardMap = {}
# 	for i in vals:
# 		# set to fixed range, not sep capID
# 		# setting to fixed range 1, injecting at a range 3 value
# 		# filled histograms should be at 127, empty histograms should at 64
# 		if vals[i]['mean'] > 96:
# 			histNum = i
# 			filledQIE = histNum%12 + 1
# 			injectionCardSlot = dac13Mapping[filledQIE]
# 			link = vals[i]['link']
# 			if link%6 < 3: half = 'TOP'
# 			else: half = 'BOTTOM'
# 			mapping[injectionCardSlot] = {'link' : link,
# 						      'id'   : linkMap[link],
# 						      'half' : half,
# 						      'connector' : int(histNum/12)
# 						      }
# 			print int(histNum/12), injectionCardSlot
# 			simpleCardMap[int(histNum/12)] = injectionCardSlotMapping[injectionCardSlot]

			
# 	print_links(ts)

# 	return mapping, simpleCardMap

def getValuesFromFile(outputDir):
	"""
	Gets data from the cardData text file from the previous run
	Gets things like the injection mapping, QIE ranges used, etc.
	"""

	dataFile = open(outputDir+"/cardData.txt",'r')
	for line in dataFile:
		if 'DAC' in line and 'Used' in line:
			dacNumber = line.split()[1]
		if 'simpleCardMap' in line:
			simpleCardMap = eval(line.split('simpleCardMap ')[-1])
		if 'injectionMapping' in line:
			injectionMapping = eval(line.split('injectionMapping ')[-1])
		if 'minRange' in line:
			minRange = int(line.split('minRange ')[-1])
		if 'maxRange' in line:
			maxRange = int(line.split('maxRange ')[-1])

	return injectionMapping, simpleCardMap, minRange, maxRange, dacNumber

def QIECalibrationScan(options):
	##load teststand 904, will this be the correcto configuration for 
#	ts = teststand("904")
	ts = None
	## take data separated by capID
	sepCapID = options.sepCapID
	print "Separate capID =",sepCapID

#	dacNum = getDACNumber()

	## create directory structure:
	## in the end, it will be /InjectionData/date/Run_XX/CalMode_FixedRangeY/
	outputDirectory = options.outputDirectory+'/'

	injectionMapping, simpleCardMap, minRange, maxRange, dacNum = getValuesFromFile(outputDirectory)

	print injectionMapping
	print simpleCardMap

	allCardsHaveSerialNumber = True
	for i_slot in injectionMapping:
		uID = injectionMapping[i_slot]['id']		
		if not uID in mapUIDtoSerial:
			print 'Missing serial number for card %s' %uID
			print 'Please edit SerialNumberMap.py to include this card'
			allCardsHaveSerialNumber = False

	if not allCardsHaveSerialNumber:
		sys.exit()

	## load qie parameters db

	qieParamsLocal = lite.connect(outputDirectory+"qieCalibrationParameters.db")
	cursorLocal = qieParamsLocal.cursor()
	cursorLocal.execute("drop table if exists qieparams")
	cursorLocal.execute("create table if not exists qieparams(id STRING, serial INT, qie INT, capID INT, range INT, directoryname STRING, date STRING, slope REAL, offset REAL)")

	

#	print_links(ts)

	histoList = []
	
	linkGroups = simpleCardMap.keys()
	linkGroups.sort()
	for i_link in linkGroups:
		for ih in range(12):
			histoList.append(ih+i_link*12)
	print histoList
		
#	sys.exit()



	if not int(options.range) == -1:
		minRange = int(options.range)
		maxRange = int(options.range)+1

	outputParamFile = open(outputDirectory+"calibrationParams.txt",'w')
	outputParamFile.write('(qieID, serialNum, qieNum, capID, qieRange, outputDirectory, timeStamp, slope, offset)\n')


	for qieRange in range(minRange, maxRange):
	
		scanRange = scans5k[qieRange]

		print scanRange
				
		# status = linkStatus(ts)
		# print status['output']


		if options.useCalibrationMode:
			CalMode = "CalibrationMode"
		else:
			CalMode = "NormalMode"
		if options.useFixRange:
			rangeMode = "FixRange_%i"%qieRange
		else:
			rangeMode = "VariableRange"

		rangeOutputDirectory = outputDirectory + "%s_%s/"%(CalMode,rangeMode)
		os.system( "mkdir -pv "+rangeOutputDirectory )
		
		results = doScan(ts, scanRange, qieRange, options.useFixRange, options.useCalibrationMode, sepCapID=sepCapID, SkipScan=True, outputDirectory = rangeOutputDirectory)

		outputTGraphs = TFile(rangeOutputDirectory+"/adcVSfc_graphs.root","recreate")
		outputTGraphs.Close()

		# histoList = range(96)
		# histoList = range(48,72)

		if options.SkipFit: continue

		if sepCapID:
			graphs = makeADCvsfCgraphSepCapID(scanRange,results, histoList, cardMap = simpleCardMap, dac=dacNum)	

#			print graphs
			for ih in histoList:
				# outputTGraphs.cd()
				# for i_capID in range(4):
				# 	graphs[ih][i_capID].Write()
				qieID = injectionMapping[simpleCardMap[int(ih/12)]]['id']
				serial = mapUIDtoSerial[qieID]
				qieNum = ih%24 + 1
				params = doFit_combined(graphs[ih],int(qieRange), True, qieNum, qieID.replace(' ', '_'),options.useCalibrationMode, rangeOutputDirectory)
				for i_capID in range(4):

					values = (qieID, serial, qieNum, i_capID, qieRange, outputDirectory, str(datetime.now()), params[i_capID][0], params[i_capID][1])
					
					cursorLocal.execute("insert into qieparams values (?, ?, ?, ?, ?, ?, ? , ?, ?)",values)

					outputParamFile.write(str(values)+'\n')

		# outputTGraphs.Close()

	qieParamsLocal.commit()
	qieParamsLocal.close()
	outputParamFile.close()
	
	graphParamDist(outputDirectory+"qieCalibrationParameters.db")


		
if __name__ == "__main__":

	print 'Start'
	parser = OptionParser()
	parser.add_option("-r", "--range", dest="range", default=-1,type='int',
			  help="Specify range to be used in scan (default is -1, which does all 4 ranges)" )
	parser.add_option("-d", "--dir", dest="outputDirectory", default='Unknown',
			  help="Specify the directory to read from" )
	parser.add_option("--nofixed", action="store_false", dest="useFixRange", default=True ,
			  help="do not use fixed range mode")
	parser.add_option("--nocalmode", action="store_false", dest="useCalibrationMode", default=True ,
			  help="do not use calibration mode" )
	parser.add_option("--NoSepCapID", action="store_false",dest="sepCapID",default=True,
			  help="don't separate the different capID histograms")
	parser.add_option("--SkipScan", action="store_true",dest="SkipScan",default=False,
			  help="Skip the scan, using presaved scan")
	parser.add_option("--SkipFit", action="store_true",dest="SkipFit",default=False,
			  help="Skip the fitting step")
	parser.add_option("--NoLinkInit", action="store_true",dest="NoLinkInit",default=False,
			  help="Skip the scan, using presaved scan")
	parser.add_option("--SkipRangeTransition", action="store_false",dest="RunRangeTransitionScan",default=True,
			  help="Skip the range transition scans")

	(options, args) = parser.parse_args()

	if not options.range == -1:
		options.RunRangeTransitionScan=False
	if options.outputDirectory == 'Unknown':
		print 'Specify a directory to read from'
		sys.exit()
	print 'Start'
	QIECalibrationScan(options)


