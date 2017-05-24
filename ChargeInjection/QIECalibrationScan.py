from time import sleep
from datetime import date, datetime
import os
from optparse import OptionParser
import subprocess
import sys

from numpy import std

from scans import *
from adcTofC import *
from fitGraphs_linearized import *
from ROOT import *
from DAC import *

sys.path.insert(0, '../../AcceptanceTests/hcal_teststand_scripts')

from hcal_teststand.uhtr import *
from hcal_teststand import *
from hcal_teststand.hcal_teststand import *
from hcal_teststand.qie import *
from checkLinks import *

from GraphParamDist import *

import sqlite3 as lite

from RangeTransitionErrors import *
from TDC_scan import *
#from read_histo import *

from SerialNumberMap import *
from FitUncertaintyPlots import *

removeExtraBinContent = True  #### added into the read_histo function to subtract content from ADC 60 in capID0, this seems to be here because of bug in uHTR (extra signal once per orbit???)  flag is here to easily remove it later for testing

gROOT.SetBatch(True)

UID_SN_DB = sqlite3.connect("/nfshome0/dnoonan/serialNumberToUIDmap.db")
serialNumcursor = UID_SN_DB.cursor()


orbitDelay = 160
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


def print_qie_range(ts, crate, slot):
	commands = []
	for i_qie in range(1, 25):
		commands.append("get HF{0}-{1}-QIE{2}_RangeSet".format(crate, slot, i_qie))
	raw_output = ngfec.send_commands(ts, cmds=commands, script=True)#['output']
	# raw_output = ngccm.send_commands_parsed(ts, commands)['output']
	for val in raw_output:
		if 'RangeSet' in val['cmd']:
			print val['cmd'], val['result']

def print_qie_status(ts, crate, slot):
	commands = []
	commands.append("get HF{0}-{1}-QIE[1-24]_FixRange".format(crate,slot))
	commands.append("get HF{0}-{1}-QIE[1-24]_RangeSet".format(crate,slot))
	commands.append("get HF{0}-{1}-QIE[1-24]_CalMode".format(crate,slot))
	raw_output = ngfec.send_commands(ts, cmds=commands,script=True)#['output']	
	# raw_output = ngccm.send_commands_parsed(ts, commands)['output']	
	for val in raw_output:
		for setting in ['RangeSet','FixRange','CalMode']:
			if setting in val['cmd']:
				print setting, val['cmd'], val['result']


# from checkQIEStatus import *	

def check_qie_status(ts, crate, slot):
	commands = []
	commands.append("get HF{0}-{1}-QIE[1-24]_FixRange".format(crate,slot))
	commands.append("get HF{0}-{1}-QIE[1-24]_RangeSet".format(crate,slot))
	commands.append("get HF{0}-{1}-QIE[1-24]_CalMode".format(crate,slot))
	raw_output = ngfec.send_commands(ts, cmds=commands, script=True)#['output']	
	# raw_output = ngccm.send_commands_parsed(ts, commands)['output']	

	results = {}
	goodValues = True
	problems = []
	for val in raw_output:
		for setting in ['RangeSet','FixRange','CalMode']:
			if setting in val['cmd']:
				results[val['cmd']] = val['result']
			values = [float(x) for x in val['result'].split()]
			if not std(values)==0:
				goodValues = False
				problems.append([val['cmd'],val['result']])
	
	return goodValues, results, problems


def getGoodQIESetting(ts,fe_crates, qie_slots, qieRange=0, useFixRange= False, useCalibrationMode = False):

	cmds = []
	for i_crate in fe_crates:
		for i_slot in qie_slots:
			print 'Set Fixed Range and Calibration mode Crate %i Slot %i' %(i_crate,i_slot)
			cmds += ['put HF%i-%i-QIE[1-24]_FixRange 24*%i'%(int(i_crate),int(i_slot),int(useFixRange)),
				 'put HF%i-%i-QIE[1-24]_RangeSet 24*%i'%(int(i_crate),int(i_slot),int(qieRange)),
				 'put HF%i-%i-QIE[1-24]_CalMode 24*%i'%(int(i_crate),int(i_slot),int(useCalibrationMode))
				 ]
			raw_output = ngfec.send_commands(ts, cmds=cmds, script=True)
			sleep(1)


def read_histo(file_in="", sepCapID=True, qieRange = 0):
	result = {}
	tf = TFile(file_in, "READ")
	tc = TCanvas("tc", "tc", 500, 500)
	if sepCapID:
		rangeADCoffset = qieRange*64.
		for i_link in range(24):
			for i_ch in range(4):
				histNum = 4*i_link + i_ch
				th = tf.Get("h{0}".format(histNum))
				if removeExtraBinContent:
					extraBinContent = th.GetBinContent(61)
					extraCountEstimate = int(th.Integral()/3560.)
					th.SetBinContent(61,extraBinContent-extraCountEstimate)

				th.GetXaxis().SetRangeUser(0,63)
				if th.GetMean() > 2.5:
					th.SetBinContent(1,0)
				th.GetXaxis().SetRangeUser(0,255)				
				info = {}
				info["link"] = i_link
				info["channel"] = i_ch
				info["mean"] = []
				info["rms"] = []
				for i_capID in range(4):
					offset = 64*(i_capID)
					th.GetXaxis().SetRangeUser(offset, offset+63)
					info["mean"].append(th.GetMean()-offset+rangeADCoffset)
					info["rms"].append(max(th.GetRMS(), 0.01))

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

	tf.Close()
	return result
		
#Scans over a number of DAC settings, getting the uHTR histogram and read out the mean and RMS for each scan point
#Returns a dictionary with the ADC values at each DAC LSB

def doScan(ts, scanRange = range(30), qieRange=0, useFixRange=True, useCalibrationMode=True, sepCapID = True, SkipScan = False, outputDirectory = ""):

	print 'SepCap', sepCapID

	getGoodQIESetting(ts, ts.fe_crates, ts.qie_slots[0], int(qieRange), useFixRange=True, useCalibrationMode=True)

			
	getGoodLinks(ts, orbitDelay=orbitDelay, GTXreset = GTXreset, CDRreset = CDRreset, forceInit=True)

	results = {}
	for i in scanRange:

		histName = ""
		histName = "Calibration_LSB_{0}.root".format( i )
		if not SkipScan:
			print 'LSB', i
			setDAC(i)
			getGoodLinks(ts, orbitDelay=orbitDelay, GTXreset = GTXreset, CDRreset = CDRreset)
			print 'GettingHist'
			fName = outputDirectory+histName
			attempts = 0

			while not os.path.exists(fName):
				if attempts > 10:
					continue
				fName = uhtr.get_histo(ts,crate=ts.be_crates[0],uhtr_slot=ts.uhtr_slots[0],n_orbits=4000, sepCapID=1, file_out=outputDirectory+histName)
		else:
			fName = outputDirectory+histName
		print 'ReadingHist'
		vals = read_histo(fName,sepCapID,int(qieRange))
		results[i] = vals

#		print_links(ts)
	if not SkipScan:
		setDAC(0)
		getGoodQIESetting(ts, ts.fe_crates, ts.qie_slots[0], int(qieRange), useFixRange=False, useCalibrationMode=False)

	getGoodLinks(ts, orbitDelay=orbitDelay, GTXreset = GTXreset, CDRreset = CDRreset, forceInit=True)

	for i_crate in ts.fe_crates:
		for i_slot in ts.qie_slots[0]:
			print '-'*20
			print 'Crate %i Slot %i Status'%(i_crate,i_slot)
			print_qie_status(ts,i_crate,i_slot)


	return results


#Provides the mapping of card slot to uHTR link
#Sets the QIE card in one slot to fixed range mode in range 2, injects charge equivalent to ADC 0, and looks for which links read 128 (bottom of range 2)
def getSimpleLinkMap(ts, outputDirectory):

	print 'Start Get Mapping'
	linkMap = {}

	setDAC(0)

	print_links(ts)
 	for crate in ts.fe_crates:
		for slot in ts.qie_slots[0]:
			print slot
			print crate
			unique_ID_parsed = qie.get_unique_id(ts,crate,slot)[(crate,slot)]
			print unique_ID_parsed
			unique_ID = "%s %s"%(unique_ID_parsed[0], unique_ID_parsed[1])
			print 'Set Fixed Range'
			getGoodQIESetting(ts, [crate], [slot], 2, useFixRange=True, useCalibrationMode=False)
#			set_fix_range_all(ts, crate, slot, True, 2)

			sleep(3)
			# This is here just to test in case where it is thought the card may not be getting set to fixed range
			#print_qie_range(ts,crate,slot)

			getGoodLinks(ts, orbitDelay=orbitDelay, GTXreset = GTXreset, CDRreset = GTXreset, forceInit=True)
			
			fName = uhtr.get_histo(ts,crate=ts.be_crates[0],uhtr_slot=ts.uhtr_slots[0],n_orbits=1000, sepCapID=0, file_out = outputDirectory+"mappingHist.root")
			vals = read_histo(fName,False)
			for i in range(0,96,4):
				link = int(i/4)
				if vals[i]['mean'] > 100:
					linkMap[link] = [unique_ID,slot]
			print_links(ts)
			print 'Set Fixed Range Off'
			getGoodQIESetting(ts, [crate], [slot], 2, useFixRange=False, useCalibrationMode=False)
#			set_fix_range_all(ts, crate, slot, False)
			getGoodLinks(ts, orbitDelay=orbitDelay, GTXreset = GTXreset, CDRreset = CDRreset, forceInit=True)

	print 'Done with Getting Mapping'
	return linkMap

		
def mapInjectorToQIE(ts, linkMap, outputDirectory = ''):
	"""
	Finds the mapping of which injector card is connected to which QIE card (and which half)
	
	Sets all cards to fixed range 1
	Injects a charge using DAC 13 which max out range 1	
	"""

	print 'get links'

	getGoodQIESetting(ts, ts.fe_crates, ts.qie_slots[0], 1, useFixRange=True, useCalibrationMode=False)

	# for i_crate in ts.fe_crates:
	# 	for i_slot in ts.qie_slots[0]:
	# 		print 'Set Fixed Range'
	# 		set_fix_range_all(ts, i_crate, i_slot, True, 1)
	# 		sleep(3)
			
	print 'Set DAC, get hist'
	setDAC(dacLSB = 10000, dacChannel = 0)
	getGoodLinks(ts, orbitDelay=orbitDelay, GTXreset = GTXreset, CDRreset = CDRreset, forceInit=True)


	print 'Read Histos'
	fName = uhtr.get_histo(ts,crate=ts.be_crates[0],uhtr_slot=ts.uhtr_slots[0],n_orbits=3000, sepCapID=0, file_out = outputDirectory+"mappingHist2.root")
	vals = read_histo(fName,False)

#	print_links(ts)

	setDAC(dacLSB = 0)

	getGoodQIESetting(ts, ts.fe_crates, ts.qie_slots[0], 1, useFixRange=False, useCalibrationMode=False)
	# for i_crate in ts.fe_crates:
	# 	for i_slots in ts.qie_slots[0]:
	# 		print 'Set Fixed Range off'
	# 		set_fix_range_all(ts, i_crate, i_slot, False)
	# sleep(3)
	getGoodLinks(ts, orbitDelay=orbitDelay, GTXreset = GTXreset, CDRreset = CDRreset, forceInit=True)
	
#	print_links(ts)

	print vals

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
						      'id'   : linkMap[link][0],
						      'half' : half,
						      'connector' : int(histNum/12)
						      }
			print int(histNum/12), injectionCardSlot
			simpleCardMap[int(histNum/12)] = injectionCardSlotMapping[injectionCardSlot]

			
#	print_links(ts)

	return mapping, simpleCardMap

def QIECalibrationScan(options):
	print 'Start'

	##load teststand 904, will this be the correcto configuration for 
	ts = teststand("904cal",f="/nfshome0/dnoonan/AcceptanceTests/hcal_teststand_scripts/configuration/teststands.txt")

	# global orbitDelay
	# print 
	# orbitDelay = findMagicNumber(ts)
	## take data separated by capID

	sepCapID = options.sepCapID
	print "Separate capID =",sepCapID

	dacNum = getDACNumber()

	# if not checkLinksPluggedIn(ts):
	# 	print "Links do not seem to be plugged in"
	# 	sys.exit()

	getGoodLinks(ts, orbitDelay=orbitDelay, GTXreset = GTXreset, CDRreset = CDRreset, forceInit=True)


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

	print 'Start Mapping'


	## run mapping of injection cards to qie cards

	linkMap = getSimpleLinkMap(ts,outputDirectory)	
	print 'got links'
	print linkMap

	###CHANGE THIS
	injectionMapping, simpleCardMap = mapInjectorToQIE(ts, linkMap, outputDirectory)	

	print injectionMapping
	print simpleCardMap

	allCardsHaveSerialNumber = True
	for i_slot in injectionMapping:
		uID = injectionMapping[i_slot]['id']		
		sernumber = serialNumcursor.execute("select serial from UIDtoSerialNumber where uid=?",(uID,)).fetchone()
		if not type(sernumber)==type(tuple()):
			print 'Missing serial number for card %s' %uID
			print 'Rerun mapping routine on this crate'
			allCardsHaveSerialNumber = False

	if not allCardsHaveSerialNumber:
		sys.exit()



	print_links(ts)

	### Get list of histograms (QIE channels) from injeciton mapping
	histoList1 = []
	
	linkList = linkMap.keys()
	linkList.sort()
	for i_link in linkList:
		for ih in range(4):
			histoList1.append(ih+i_link*4)

	histoList2 = []

	linkGroups = simpleCardMap.keys()
	linkGroups.sort()
	for i_link in linkGroups:
		for ih in range(12):
			histoList2.append(ih+i_link*12)

	histoList = list(set(histoList1) & set(histoList2))

	print histoList

#	sys.exit()

	minRange = 0
	maxRange = 4

	if not int(options.range) == -1:
		minRange = int(options.range)
		maxRange = int(options.range)+1		


	## creates a 'cardData.txt' file in the output directory, containing the list of injection cards used, the mapping between 
	dataFile = open(outputDirectory+"cardData.txt",'w')
	
	line = '%s\n'%str(datetime.now())
	line += "DAC %s Used\n\n" %dacNum
	for i_injCard in injectionMapping:
		line += "Injection Card %i\n"%i_injCard
#		line += "  slot: %s\n"%injectionMapping[i_injCard]['slot']
		line += "  Connected to QIE:\n"
		line += "    id: %s\n"%injectionMapping[i_injCard]['id']
		line += "    half: %s\n"%injectionMapping[i_injCard]['half']
		connector = int(injectionMapping[i_injCard]['connector'])
		line += "    links: %i%i%i\n"%(connector*3, connector*3+1, connector*3+2)
		line += "    histss: %i-%i\n"%(connector*12, connector*12+11)

	line += '*'*80 + '\n'
	line += 'Parameters that can be pulled for redoing the fit \n'
	line += '*'*80 + '\n'

	line += 'simpleCardMap '
	line += str(simpleCardMap)
	line += '\n'
	line += 'injectionMapping '
	line += str(injectionMapping)
	line += '\n'
	line += 'minRange '
	line += str(minRange)
	line += '\n'
	line += 'maxRange '
	line += str(maxRange)
	line += '\n'
	dataFile.write(line)
	dataFile.close()	

	outputParamFile = open(outputDirectory+"calibrationParams.txt",'w')
	outputParamFile.write('(qieID, serialNum, qieNum, capID, qieRange, outputDirectory, timeStamp, slope, offset)\n')


	results = {}
	graphs = {}
	for qieRange in range(minRange, maxRange):
	
		scanRange = scans5k[qieRange]

		print scanRange

		getGoodLinks(ts, orbitDelay=orbitDelay, GTXreset = GTXreset, CDRreset = CDRreset)
				
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
		
		results = doScan(ts, scanRange, qieRange, options.useFixRange, options.useCalibrationMode, sepCapID=sepCapID, SkipScan=options.SkipScan, outputDirectory = rangeOutputDirectory)
		graphs[qieRange] = makeADCvsfCgraphSepCapID(scanRange,results, histoList, cardMap = simpleCardMap, dac=dacNum)


	rangeOutputDirectory = outputDirectory+'/outputPlots/'
	os.system( "mkdir -pv "+rangeOutputDirectory )

	linkToUIDMap = {}
	uID_list = []
	for i in injectionMapping:
		tempLinkVal = injectionMapping[i]['link']
		linkVal = tempLinkVal-(tempLinkVal%3)
		uID = injectionMapping[i]['id'].replace(' ','_')
		if not uID in uID_list:
			uID_list.append(uID)
		linkToUIDMap[linkVal]=uID

	print '-'*20
	print '-'*20
	print '-'*20
	print '-'*20
	print 'linkToUIDMap'
	print linkToUIDMap
	print '-'*20
	print '-'*20
	print '-'*20
	print '-'*20

	qieParams = {}
	cursor = {}
	for uID in uID_list:
		outputGraphFile = TFile("%s/fitResults_%s.root"%(outputDirectory, uID),"recreate")
		DataOutputDirName = TNamed("DataFilesLocation",os.path.abspath(outputDirectory))
		DataOutputDirName.Write()
		outputGraphFile.mkdir("adcVsCharge")
		outputGraphFile.mkdir("LinadcVsCharge")
		outputGraphFile.mkdir("TDC")
		outputGraphFile.mkdir("fitLines")
		outputGraphFile.mkdir("SummaryPlots")
		outputGraphFile.Close()
		
		qieParams[uID] = lite.connect(outputDirectory+"qieCalibrationParameters_%s.db"%(uID))
		cursor[uID] = qieParams[uID].cursor()
		cursor[uID].execute("create table if not exists qieparams(id STRING, serial INT, qie INT, capID INT, range INT, directoryname STRING, date STRING, slope REAL, offset REAL)")

	for ih in histoList:
		if options.SkipFit: continue
	
		qieID = injectionMapping[simpleCardMap[int(ih/12)]]['id']
		serial = serialNumcursor.execute("select serial from UIDtoSerialNumber where uid=?",(qieID,)).fetchone()[0]#mapUIDtoSerial[qieID]
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

		
		params = doFit_combined(graphList=graphList, qieRange=int(qieRange), saveGraph=True, qieNumber=qieNum, qieUniqueID=qieID.replace(' ', '_'), useCalibrationMode=options.useCalibrationMode, outputDir=rangeOutputDirectory, saveOnlyComb=True)

		uID = qieID.replace(' ', '_')
		for i_range in graphs:
			for i_capID in range(4):
				values = (qieID, serial, qieNum, i_capID, i_range, outputDirectory, str(datetime.now()), params[i_range][i_capID][0], params[i_range][i_capID][1])
				cursor[uID].execute("insert into qieparams values (?, ?, ?, ?, ?, ?, ?, ? , ?)",values)

				outputParamFile.write(str(values)+'\n')

	### Save calibration condition db files and graph parameters

	for uID in uID_list:
		cursor[uID].close()
		qieParams[uID].commit()
		qieParams[uID].close()
		graphParamDist(outputDirectory+"qieCalibrationParameters_%s.db"%uID)

	outputParamFile.close()
	

	### Range Transition Errors

	qieTestParams = {}
	cursor = {}
	for uID in uID_list:
		qieTestParams[uID] = lite.connect(outputDirectory+"qieTestParameters_%s.db"%uID)
		cursor[uID] = qieTestParams[uID].cursor()
		cursor[uID].execute("create table if not exists qietestparams(id STRING, qie INT, type1_r0 REAL, type2_r0 REAL, type1_r1 REAL, type2_r1 REAL, type3_r1 REAL, type1_r2 REAL, type2_r2 REAL, tdcstart REAL)") 

	if options.RunExtraTests:		
		# errorRate = runTransitionErrorScans(outDir = outputDirectory, transitionRanges = [0,1,2], mapping = simpleCardMap, orbitDelay=orbitDelay)
		tdc_start_current = runTDCScan(mapping=simpleCardMap, dac=dacNum, orbitDelay=orbitDelay, linkToUIDMap=linkToUIDMap, outputDir = outputDirectory)

		for ih in histoList:
			type1_r0 = 0 #errorRate[0][ih][1][0]
			type2_r0 = 0 #errorRate[0][ih][2][0]
			type1_r1 = 0 #errorRate[1][ih][1][0]
			type2_r1 = 0 #errorRate[1][ih][2][0]
			type3_r1 = 0 #errorRate[1][ih][3][0]
			type1_r2 = 0 #errorRate[2][ih][1][0]
			type2_r2 = 0 #errorRate[2][ih][2][0]

			tdcstart = tdc_start_current[ih]

			qieID = injectionMapping[simpleCardMap[int(ih/12)]]['id']
			qieNum = ih%24 + 1

			values = (qieID, qieNum, type1_r0, type2_r0, type1_r1, type2_r1, type2_r1, type1_r2, type2_r2, tdcstart)
			uID = qieID.replace(' ','_')
			cursor[uID].execute("insert into qietestparams values (?, ?, ?, ?, ?, ?, ? , ?, ?, ?)",values)

	for uID in uID_list:
		cursor[uID].close()
		qieTestParams[uID].commit()
		qieTestParams[uID].close()


        problemCards = []
	for uID in uID_list:
		outputFileName = "%s/fitResults_%s.root"%(outputDirectory, uID)
                badChannels = fillFitUncertaintyHists(outputFileName)
		if len(badChannels) > 0:
			slot=-1
			for link in linkMap:
				if linkMap[link][0]==uID.replace('_',' '):
					slot = linkMap[link][1]
			problemCards.append([uID.replace('_',' '), slot, badChannels])

        for card in problemCards:
		print '*'*40
		print 'PROBLEM WITH FIT IN QIE CARD'
		print '    UnID: ',card[0]
		print '    Slot: ',card[1]
		print '    BadChannels: ', card[2]
	if len(problemCards)==0:
		print 'All cards calibrated with no problems'

 	
if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-r", "--range", dest="range", default=-1,type='int',
			  help="Specify range to be used in scan (default is -1, which does all 4 ranges)" )
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
	parser.add_option("--SkipTDC", action="store_false",dest="RunTDCScan",default=True,
			  help="Skip the TDC scans")
	parser.add_option("--SkipExtraTests", action="store_false",dest="RunExtraTests",default=True,
			  help="Skip the Range Transistion and TDC tests")

	(options, args) = parser.parse_args()

	if not options.range == -1:
		options.RunRangeTransitionScan=False
		options.RunTDCScan=False
	if not options.RunRangeTransitionScan or not options.RunTDCScan:
		options.RunExtraTests = False

	QIECalibrationScan(options)


