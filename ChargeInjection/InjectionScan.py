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

def setup(ts, range=0, useFixRange=True, useCalibrationMode=True):
	commands = [
		"get HF1-bkp_pwr_bad",
		"put HF1-bkp_reset 1",
		"put HF1-bkp_reset 0",
		"get HF1-adc56_f",
		"put HF1-2-QIE[1-24]_RangeSet 24*x",
		"get HF1-2-QIE[1-24]_RangeSet",
		"put HF1-2-QIE[1-24]_FixRange 24*1",
		"get HF1-2-QIE[1-24]_FixRange",
		"put HF1-2-QIE[1-24]_CalMode 24*1",
		"get HF1-2-QIE[1-24]_CalMode",
		"get HF1-2-iBot_StatusReg_QieDLLNoLock",
		"get HF1-2-iBot_StatusReg_PLL320MHzLock",
		"quit",
		]
	
	commands[4] = commands[4].replace('x',str(range))
	if not useFixRange:
		commands[6] = commands[6].replace('24*1','24*0')
	if not useCalibrationMode:
		commands[8] = commands[8].replace('24*1','24*0')

	output = ngccm.send_commands_parsed(ts, commands)
	for line in output['output']:
		print line['cmd'], line['result']

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
		'quit',
		'exit',
		'exit'
		]
	uhtr.send_commands_script(ts, ts.uhtr_slots[0], cmds)
#	for line in output['output']:
#		print line
#		print line['cmd'], line['result']


def read_histo(file_in="", sepCapID=True, qierange = 0):
	result = []
	tf = TFile(file_in, "READ")
	tc = TCanvas("tc", "tc", 500, 500)
	if sepCapID:
		for i_link in range(24):
			for i_ch in range(4):
				th = tf.Get("h{0}".format(4*i_link + i_ch))
				info = {}
				info["link"] = i_link
				info["channel"] = i_ch
				info["mean"] = []
				info["meanerr"] = []
				info["rms"] = []
				for i_capID in range(4):
					offset = 64*(i_capID)
					th.GetXaxis().SetRangeUser(offset, offset+63)
					info["mean"].append(th.GetMean()-offset)
					info["meanerr"].append(th.GetMeanError())
					info["rms"].append(th.GetRMS())
					#                               info["stddev"] = th.GetStdDev()
				result.append(info)
		
	else:
		for i_link in range(24):
			for i_ch in range(4):
				th = tf.Get("h{0}".format(4*i_link + i_ch))
				info = {}
				info["link"] = i_link
				info["channel"] = i_ch
				info["mean"] = th.GetMean()
				info["meanerr"] = th.GetMeanError()
				info["rms"] = th.GetRMS()
				#                               info["stddev"] = th.GetStdDev()
				result.append(info)
	return result
		
																																						


def doScan(ts, injCardNumber = 1, dacNumber = 1, scanRange = range(30), qieRange=0, useFixRange=True, useCalibrationMode=True, saveHistograms = True, sepCapID = True, SkipScan = False):

	print 'SepCap', sepCapID

	if saveHistograms:
		outputDirectory = "injector_card_{0}_DAC_{1}/Cal_range_{2}_mode/{3}/".format(injCardNumber, dacNumber, qieRange, str(date.today() ) )
		if not os.path.exists(outputDirectory):
			os.system( "mkdir -pv "+outputDirectory )


	if useFixRange:
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
			setDAC( i)
			# setup("{0}".format(options.scan))
			sleep(5)
			if sepCapID:
				fName = uhtr.get_histo(ts,uhtr_slot=ts.uhtr_slots[0],n_orbits=4000, sepCapID=1, file_out=outputDirectory+histName)
			else:
				fName = uhtr.get_histo(ts,uhtr_slot=ts.uhtr_slots[0],n_orbits=4000, sepCapID=0, file_out=outputDirectory+histName)
			setDAC(0)
			setup("{0}".format(qieRange))            
		else:
			fName = outputDirectory+histName
		vals = read_histo(fName,sepCapID,int(qieRange))
		results[i] = vals
	
	return results


def main(options):
	ts = teststand("904")

	scanRange = scans[options.range]
	if not options.scan == []:
		scanRange = eval(options.scan)

	print scanRange

	sepCapID = options.sepCapID
	print sepCapID

	if not options.SkipScan:
		print ts.fe_crates
		print ts.qie_slots
		uniqueID = {}
		for i_crate in ts.fe_crates:
			uniqueID[i_crate] = {}
			for i_slot in ts.qie_slots[0]:
				uniqueID[i_crate][i_slot] = get_unique_id(ts, i_crate, i_slot)
				print i_crate, i_slot, get_unique_id(ts, i_crate, i_slot)

		qieCardID = get_unique_id(ts,1,2)

#### Find which injection board is hooked up to which range of QIE's

	qieCardID = ['0x8d000000', '0xaa24da70']

	results = doScan(ts, options.cardnumber, options.dacnumber, scanRange, options.range, options.useFixRange, options.useCalibrationMode, options.saveHistograms,sepCapID=sepCapID, SkipScan=options.SkipScan)

	histoList = eval(options.histoList)

	qieParams = lite.connect("qieParameters.db")
	cursor = qieParams.cursor()

	cursor.execute("create table if not exists qieparams(id STRING, qie INT, capID INT, range INT, slope REAL, offset REAL)")
		

	print qieCardID
	qieID = "%s %s" %(qieCardID[0], qieCardID[1])

	#Will need to find a way of updating the mapping between injection boards and qie boards

	if sepCapID:
		graphs = makeADCvsfCgraphSepCapID(scanRange,results, histoList)

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
		graphs = makeADCvsfCgraph(scanRange,results, histoList, sepCapID)

		for ih in histoList:
			graph = graphs[ih]
			print ih
			qieNum = ih%24 + 1

			params = doFit(graph,int(options.range), True, qieNum, qieID.replace(' ', '_'))
			
			values = (qieID, qieNum, i_capID, options.range, params[0], params[1])
			cursor.execute("insert or replace into qieparams values (?, ?, ?, ?, ?, ?)",values)

	cursor.close()
	qieParams.commit()
	qieParams.close()

		
if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-c", "--card", dest="cardnumber", default="2" ,
			  help="qie card number" )
	parser.add_option("-d", "--dac", dest="dacnumber", default="2" ,
			  help="DAC used" )
	parser.add_option("-r", "--range", dest="range",default=0 ,
			  help="choose which range you would like to scan: 0, 1, 2, 3" )
	parser.add_option("-s", "--scan", dest="scan", default=[] ,
			  help="set a range of DAC values you want to scan over" )
	parser.add_option("--nofixed", action="store_false", dest="useFixRange", default=True ,
			  help="do not use fixed range mode")
	parser.add_option("--nocalmode", action="store_false", dest="useCalibrationMode", default=True ,
			  help="do not use calibration mode" )
	parser.add_option("--save","--savehistos",action="store_true",dest="saveHistograms", default=False,
			  help="save the histogram output files")
	parser.add_option("--histoList", dest="histoList",default='range(96)',
			  help="choose histogram range to look at")
	parser.add_option("--NoSepCapID", action="store_false",dest="sepCapID",default=True,
			  help="don't separate the different capID histograms")
	parser.add_option("--SkipScan", action="store_true",dest="SkipScan",default=False,
			  help="Skip the scan, using presaved scan")

	(options, args) = parser.parse_args()
	
	main(options)
