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
		'3499',
		'0',
		'0',
		'0',
		'quit',
		'exit',
		'-1'
		]
	output = uhtr.send_commands_script(ts, ts.uhtr_slots[0], cmds)
#	print output['output']
	sleep(2)
#	for line in output['output']:
#		print line
#		print line['cmd'], line['result']

from linearizeHists import *

newOutTest = TFile("testingNew.root",'recreate')

def read_histoLinearized(file_in="", sepCapID=True, qieRange = 0,lsb=0,histoList = range(96)):
	result = {}
	tf = TFile(file_in, "READ")
	tc = TCanvas("tc", "tc", 500, 500)
	if sepCapID:
		for i_link in range(24):
			for i_ch in range(4):
				hNum = 4*i_link + i_ch
				if hNum in histoList:
					th = tf.Get("h{0}".format(hNum))
				
					info = {}
					info["link"] = i_link
					info["channel"] = i_ch
					info["mean"] = []
					info["meanerr"] = []
					info["rms"] = []
					for i_capID in range(4):
						offset = 64*(i_capID)
						newHist = linearizeHist(th,qieRange,offset,hNum,i_capID,lsb)
						newOutTest.cd()
						newHist.Write()
						info['mean'].append(newHist.GetMean())
						info["meanerr"].append(newHist.GetMeanError())
						info["rms"].append(newHist.GetRMS())

					result[hNum] = info
				
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
		
																																						


def read_histo(file_in="", sepCapID=True, qieRange = 0):
	result = []
	tf = TFile(file_in, "READ")
	tc = TCanvas("tc", "tc", 500, 500)
	if sepCapID:
		for i_link in range(24):
			for i_ch in range(4):
				th = tf.Get("h{0}".format(4*i_link + i_ch))
				th.GetXaxis().SetRangeUser(0,63)
				if th.GetMaximumBin() > 2:
					th.SetBinContent(1,0)
				info = {}
				info["link"] = i_link
				info["channel"] = i_ch
				info["mean"] = []
				info["meanerr"] = []
				info["rms"] = []
				for i_capID in range(4):
					offset = 64*(i_capID)
					th.GetXaxis().SetRangeUser(offset, offset+63)
					info["mean"].append(th.GetMean() - offset + qieRange*64)
					info["meanerr"].append(th.GetMeanError())
					info["rms"].append(th.GetRMS())
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
				result.append(info)
	return result
		
																																						


def doScan(ts, injCardNumber = 1, dacNumber = 1, scanRange = range(30), qieRange=0, useFixRange=True, useCalibrationMode=True, saveHistograms = True, sepCapID = True, SkipScan = False,histoList=range(96), testDir = False):

	print 'SepCap', sepCapID

	if saveHistograms and not SkipScan:
		if sepCapID:
			outputDirectory = "injector_card_{0}_DAC_{1}/Cal_range_{2}_mode/{3}/".format(injCardNumber, dacNumber, qieRange, str(date.today() ) )
		else:
			outputDirectory = "injector_card_{0}_DAC_{1}/Cal_range_{2}_mode_NoSepCapID/{3}/".format(injCardNumber, dacNumber, qieRange, str(date.today() ) )

		if not useCalibrationMode:
			outputDirectory = outputDirectory.replace('/Cal_','/NoCal_')
		if not useFixRange:
			outputDirectory = outputDirectory.replace('_range_','_NotFixedRange_')

		if not os.path.exists(outputDirectory):
			os.system( "mkdir -pv "+outputDirectory )

	if SkipScan:
		if sepCapID:
			outputDirectory = "injector_card_{0}_DAC_{1}/Cal_range_{2}_mode/".format( injCardNumber, dacNumber, qieRange )
		else:
			outputDirectory = "injector_card_{0}_DAC_{1}/Cal_range_{2}_mode_NoSepCapID/".format( injCardNumber, dacNumber, qieRange )
		dirs = os.listdir(outputDirectory)
		dirs.sort()
		outputDirectory += dirs[-1]+'/'
		print outputDirectory

	if testDir:
		outputDirectory = 'TestDir/'

	if useFixRange:
		set_fix_range_all(ts, 1, 2, True, int(qieRange))
	else:
		set_fix_range_all(ts, 1, 2, False)
	if useCalibrationMode:
		set_cal_mode_all(ts, 1, 2, True)
	else:
		set_cal_mode_all(ts, 1, 2, False)
	if not SkipScan:
		initLinks(ts)

	results = {}
	for i in scanRange:

		histName = ""
		if saveHistograms: histName = "Calibration_LSB_{0}.root".format( i )
		if not SkipScan:
			print 'LSB', i
			setDAC(i)
			# setup("{0}".format(options.scan))
			sleep(3)
			if sepCapID:
				fName = uhtr.get_histo(ts,uhtr_slot=ts.uhtr_slots[0],n_orbits=4000, sepCapID=1, file_out=outputDirectory+histName)
			else:
				fName = uhtr.get_histo(ts,uhtr_slot=ts.uhtr_slots[0],n_orbits=4000, sepCapID=0, file_out=outputDirectory+histName)
		else:
			fName = outputDirectory+histName
		vals = read_histo(fName,sepCapID,int(qieRange))
#		vals = read_histoLinearized(fName,sepCapID,int(qieRange),i,histoList)
		results[i] = vals
		
	if not SkipScan:
		setDAC(0)
		set_fix_range_all(ts, 1, 2, False)
		set_cal_mode_all(ts, 1, 2, False)
	
	return results


def main(options):
	ts = teststand("904")

	scanRange = scans5k[options.range]
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

	histoList = eval(options.histoList)

	results = doScan(ts, options.cardnumber, options.dacnumber, scanRange, options.range, options.useFixRange, options.useCalibrationMode, options.saveHistograms,sepCapID=sepCapID, SkipScan=options.SkipScan, histoList = histoList)

	qieParams = lite.connect("qieParameters.db")
	cursor = qieParams.cursor()

	cursor.execute("create table if not exists qieparams(id STRING, qie INT, capID INT, range INT, slope REAL, offset REAL)")
		

	print qieCardID
	qieID = "%s %s" %(qieCardID[0], qieCardID[1])

	#Will need to find a way of updating the mapping between injection boards and qie boards
	
	if not options.useFixRange:
		return

	outFile = TFile('testOutGraphs.root','recreate')

	if sepCapID:
		graphs = makeADCvsfCgraphSepCapID(scanRange,results, histoList)

		for ih in histoList:
			for g in graphs[ih]:
				print g
				outFile.cd()
				g.Write()

			if options.SkipFit:
				continue

			qieNum = ih%24 + 1
			params = doFit_combined(graphs[ih],int(options.range), True, qieNum, qieID.replace(' ', '_'), options.useCalibrationMode)
			if not options.useCalibrationMode:
				continue

			for i_capID in range(4):
				values = (qieID, qieNum, i_capID, options.range, params[i_capID][0], params[i_capID][1])
				
				cursor.execute("insert or replace into qieparams values (?, ?, ?, ?, ?, ?)",values)


			# for i_capID in range(4):
			# 	graph = graphs[ih][i_capID]
			# 	print ih, i_capID
			# 	qieNum = ih%24 + 1
				
			# 	params = doFit(graph,int(options.range), True, qieNum, qieID.replace(' ', '_'),i_capID, options.useCalibrationMode)

			# 	if not options.useCalibrationMode:
			# 		continue

			# 	values = (qieID, qieNum, i_capID, options.range, params[0], params[1])
				
			# 	cursor.execute("insert or replace into qieparams values (?, ?, ?, ?, ?, ?)",values)
				
	else:
		i_capID = -1
		graphs = makeADCvsfCgraph(scanRange,results, histoList)

		for ih in histoList:
			graph = graphs[ih]
			print ih
			qieNum = ih%24 + 1



			params = doFit(graph,int(options.range), True, qieNum, qieID.replace(' ', '_'), capID = -1, useCalibrationMode = options.useCalibrationMode)
			
			if not options.useCalibrationMode:
				continue

			cursor.execute("delete from qieparams where id=? and qie=? and capID=? and range=?",(qieID, qieNum, i_capID, options.range))
			
			values = (qieID, qieNum, i_capID, options.range, params[0], params[1])

			cursor.execute("insert into qieparams values (?, ?, ?, ?, ?, ?)",values)

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
	parser.add_option("--notsave","--notsavehistos",action="store_false",dest="saveHistograms", default=True,
			  help="save the histogram output files")
	parser.add_option("--histoList", dest="histoList",default='range(48,72)',
			  help="choose histogram range to look at")
	parser.add_option("--NoSepCapID", action="store_false",dest="sepCapID",default=True,
			  help="don't separate the different capID histograms")
	parser.add_option("--SkipScan", action="store_true",dest="SkipScan",default=False,
			  help="Skip the scan, using presaved scan")
	parser.add_option("--SkipFit", action="store_true",dest="SkipFit",default=False,
			  help="Skip the parameter fit")
	parser.add_option("--Test", action="store_true",dest="testDir",default=False,
			  help="Store output in TestDir")

	(options, args) = parser.parse_args()
	
	main(options)
