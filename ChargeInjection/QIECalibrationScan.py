from time import sleep
from datetime import date
import os
from optparse import OptionParser
import subprocess
import sys

from scans import *
from adcTofC import *
from fitGraphs import *
from ROOT import *

sys.path.insert(0, '../../hcal_teststand_scripts')

from hcal_teststand.uhtr import *
from hcal_teststand import *
from hcal_teststand.hcal_teststand import *
from hcal_teststand.qie import *

import sqlite3 as lite

### Which slot number contains which injection card {slot:card}
### slots are numbered 1 to 8 (slot 0 contains the DAC, slot 9 has an extra injection card)
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

## Which histogram does DAC channel 13 fill on each injection board slot ( { histogram : injectionslot} )
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
			      

def setDAC( dacLSB = 0, dacChannel = -1):
	os.system("export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib; ~/../tiroy/mcc-libhid/dacQinjector  -o {0} -c {1}".format(dacLSB, dacChannel) )


def initLinks(ts):
	cmds = [
		'0',
		'link',
		'init',
		'1',
		'92',
		'0',
		'0',
		'0',
		'quit',
		'exit',
		'-1'
		]
	output = uhtr.send_commands_script(ts, ts.uhtr_slots[0], cmds)

	sleep(2)



def read_histo(file_in="", sepCapID=True, qierange = 0):
	result = {}
	tf = TFile(file_in, "READ")
	tc = TCanvas("tc", "tc", 500, 500)
	if sepCapID:
		for i_link in range(24):
			for i_ch in range(4):
				histNum = 4*i_link + i_ch
				th = tf.Get("h{0}".format(histNum))
				th.SetBinContent(1,0)
				info = {}
				info["link"] = i_link
				info["channel"] = i_ch
				info["mean"] = []
				info["rms"] = []
				for i_capID in range(4):
					offset = 64*(i_capID)
					th.GetXaxis().SetRangeUser(offset, offset+63)
					info["mean"].append(th.GetMean()-offset)
					info["rms"].append(th.GetRMS())

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
		
																																						


def doScan(ts, injCardNumber = 1, dacNumber = 1, scanRange = range(30), qieRange=0, useFixRange=True, useCalibrationMode=True, saveHistograms = True, sepCapID = True, SkipScan = False, outputDirectory = ""):

	print 'SepCap', sepCapID

	if useFixRange:
		for i_crate in ts.fe_crates:
			for ts.qie_slots[0]:
		set_fix_range_all(ts, 1, 2, True, int(qieRange))
	if useCalibrationMode:
		set_cal_mode_all(ts, 1, 2, True)

	if not SkipScan:
		initLinks(ts)

	results = {}
	for i in scanRange:

		histName = ""
		if saveHistograms: histName = "Calibration_LSB_{0}.root".format( i )
		if not SkipScan:
			print 'LSB', i
			setDAC(i)
			sleep(5)
			if sepCapID:
				fName = uhtr.get_histo(ts,uhtr_slot=ts.uhtr_slots[0],n_orbits=4000, sepCapID=1, file_out=outputDirectory+histName)
			else:
				fName = uhtr.get_histo(ts,uhtr_slot=ts.uhtr_slots[0],n_orbits=4000, sepCapID=0, file_out=outputDirectory+histName)
		else:
			fName = outputDirectory+histName
		vals = read_histo(fName,sepCapID,int(qieRange))
		results[i] = vals
		
	if not SkipScan:
		setDAC(0)
		set_fix_range_all(ts, 1, 2, False, int(qieRange))
		set_cal_mode_all(ts, 1, 2, False)
	
	return results

def mapInjectorToQIE(ts):
	"""
	Finds the mapping of which injector card is connected to which QIE card (and which half)
	
	Sets all cards to fixed range 1
	Injects a charge using DAC 13 which max out range 1	
	"""

	links = ts.get_links()

	for i_crate in ts.fe_crates:
		for i_slots in ts.qie_slots[0]:
			set_fix_range_all(ts, i_crate, i_slot, True, 1)

	setDAC(dacLSB = 0)
	sleep(5)
	setDAC(dacLSB = 10000, dacChannel = 13)
	sleep(5)
	fName = uhtr.get_histo(ts,uhtr_slot=ts.uhtr_slots[0],n_orbits=4000, sepCapID=0, file_out = outputDirectory+"mappingHist.root")
	vals = read_histo(fName,False)

	mapping = {}
	simpleMap = {}
	for i in vals:
		# set to fixed range, not sep capID
		# setting to fixed range 1, injecting at a range 3 value
		# filled histograms should be at 127, empty histograms should at 64
		if vals[i]['mean'] > 96:
			histNum = i
			filledQIE = histNum%12 + 1
			injectionCardSlot = dac13Mapping[filledQIE]
			link = vals[i]['link']
			qieSlot = links[11][link].slot   #does this make sense????
			mapping[injectionCardSlot] = {'link' : link,
						      'id'   : links[11][link].qie_unique_id,
						      'half' : links[11][link].qie_half,
						      'slot' : qieSlot,
						      'connector' : int(histNum/12)
						      }
			simpleCardMap[int(histNum/12)] = injectionCardSlotMapping[injectionCardSlot]

			
	for i_crate in ts.fe_crates:
		for i_slots in ts.qie_slots[0]:
			set_fix_range_all(ts, i_crate, i_slot, False)

	return mapping, simpleCardMap



def main(options):

	##load teststand 904, will this be the correcto configuration for 
	ts = teststand("904")


	## load qie parameters db
	qieParams = lite.connect("qieParameters.db")
	cursor = qieParams.cursor()
	cursor.execute("create table if not exists qieparams(id STRING, qie INT, capID INT, range INT, slope REAL, offset REAL)")
		
	## take data separated by capID
	sepCapID = options.sepCapID
	print "Separate capID =",sepCapID


	## create directory structure:
	## in the end, it will be /InjectionData/date/Run_XX/CalMode_FixedRangeY/
	outputDirectory = "InjectionData/%s/"%( str(date.today()) )
	if not os.path.exists(outputDirectory):
		os.system( "mkdir -pv "+outputDirectory )
		fileVersion = "Run_01/"
	else:
		files = os.listDir(outputDirectory)
		files.sort()
		lastNum = int(files[-1].split("_")[-1])
		fileVersion = "Run_%02i/"%lastNum+1
	outputDirectory += fileVersion
	os.system( "mkdir -pv "+outputDirectory )
	

	## run mapping of injection cards to qie cards
	injectionMapping, simpleCardMap = mapInjectorToQIE(ts)

	## creates a 'cardData.txt' file in the output directory, containing the list of injection cards used, the mapping between 
	dataFile = open(outputDirectory+"cardData.txt",'w')
	line = "Injection Cards Used\n"
	line += str(qieInjectionCardsUsed)+"\n\n"
	
	line += '\n\n'
	for i_injCard in injectionMapping:
		line += "Injection Card %i\n"%i_injCard
		line += "  slot: %s\n"%injectionMapping[i_injCard]['slot']
		line += "  id: %s\n"%injectionMapping[i_injCard]['id']
		line += "  half: %s\n"%injectionMapping[i_injCard]['half']

	dataFile.write(line)
	dataFile.close()	
	

	for qieRange in range(3):
	
		scanRange = scans[qieRange]

		print scanRange


		if useCalibrationMode:
			CalMode = "CaliMode"
		else:
			CalMode = "NotCaliMode"
		if useFixRange:
			rangeMode = "FixRange_%i"%qieRange
		else:
			rangeMode = "VariableRange"

		outputDirectory += "%s_%s"%(CalMode,rangeMode)
		os.system( "mkdir -pv "+outputDirectory )
		
		results = doScan(ts, options.cardnumber, options.dacnumber, scanRange, options.range, options.useFixRange, options.useCalibrationMode, options.saveHistograms,sepCapID=sepCapID, SkipScan=options.SkipScan)

		histoList = range(96)

		if sepCapID:
			graphs = makeADCvsfCgraphSepCapID(scanRange,results, histoList, mapping = simpleCardMap)

			for ih in histoList:
				for i_capID in range(4):
					graph = graphs[ih][i_capID]
					print ih, i_capID
					print graph
					qieNum = ih%24 + 1
					params = doFit(graph,int(options.range), True, qieNum, qieID.replace(' ', '_'),i_capID)
					
					values = (qieID, qieNum, i_capID, options.range, params[0], params[1])
					
					cursor.execute("insert or replace into qieparams values (?, ?, ?, ?, ?, ?)",values)
				
		else:
			capID = -1
			graphs = makeADCvsfCgraph(scanRange,results, histoList, sepCapID, mapping = simpleCardMap)

			for ih in histoList:
				graph = graphs[ih]
				print ih
				qieNum = ih%24 + 1
				
				params = doFit(graph,int(options.range), True, qieNum, qieID.replace(' ', '_'))
				
				cursor.execute("remove from qieparams where qieID=? and qieNum=? and i_capID=? and range=?",(qieID, qieNum, i_capID, options.range))
				
				values = (qieID, qieNum, i_capID, options.range, params[0], params[1])
				
				cursor.execute("insert into qieparams values (?, ?, ?, ?, ?, ?)",values)

	cursor.close()
	qieParams.commit()
	qieParams.close()

		
if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-d", "--dac", dest="dacnumber", default="2" ,
			  help="DAC used" )
	parser.add_option("--nofixed", action="store_false", dest="useFixRange", default=True ,
			  help="do not use fixed range mode")
	parser.add_option("--nocalmode", action="store_false", dest="useCalibrationMode", default=True ,
			  help="do not use calibration mode" )
	parser.add_option("--NoSepCapID", action="store_false",dest="sepCapID",default=True,
			  help="don't separate the different capID histograms")
	parser.add_option("--SkipScan", action="store_true",dest="SkipScan",default=False,
			  help="Skip the scan, using presaved scan")

	(options, args) = parser.parse_args()
	
	main(options)
