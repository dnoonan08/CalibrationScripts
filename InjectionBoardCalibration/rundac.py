import subprocess
import time
import sys
import os
from optparse import OptionParser


parser = OptionParser()
parser.add_option("-d", "--dac", dest="dac",
                default="",
                help="The dac being used (default is -1)", metavar="STR")
parser.add_option("-c", "--card", dest="card",
                default="",
                help="The card being used (default is -1)", metavar="STR")
parser.add_option("-p", "--pigtail", dest="pigtail",
                default="",
                help="The pigtail being used (default is -1)", metavar="STR")
parser.add_option("-v", "--version", dest="version",
                default="",
                help="The pigtail being used (default is -1)", metavar="STR")
parser.add_option("-o","--overwrite",action="store_false", dest="doCheck",default = True)

(options, args) = parser.parse_args()

pigtail = options.pigtail
card = options.card
dac = options.dac
version = options.version
doCheck = options.doCheck

if not version == "":
	version = "_v"+version

outTextFileName = "/afs/cern.ch/user/d/dnoonan/HCAL_Testing/Calibration/calibration_output/calibration_output_card_%s_dac_%s_pigtail_%s%s.txt"%(card,dac,pigtail,version)

if doCheck:
	if os.path.exists(outTextFileName):
		print 'File', outTextFileName, 'exists already'
		print 'To replace this file, use the options -o or --overwrite'
		sys.exit()


#hostname = '128.141.168.19'
hostname = 'dnoonan@pb-d-128-141-168-45.cern.ch'
filename_dac_exe  = '/afs/cern.ch/user/d/dnoonan/HCAL_Testing/mcc-libhid/dacQinjector'
filename_keithley = '/Users/dnoonan/Work/CMS/HCAL/CalibrationScripts/Keithley/run_Keithley.py'

R0_s0 = [i for i in range(35)] #[0, 1, 2, 3, 0]
R0_s1_2_3 = [i for i in range(35,135,5)]
R1 = [ i for i in range(140, 4000, 60)]

logFullRange = [2**16-1] + [0]  + [2**x for x in range(16)]  + [2**x+2**(x-1) for x in range(1,16)] + [2**x+2**(x-2) for x in range(2,16)] + [2**x+2**(x-1)+2**(x-2) for x in range(2,16)]

FullRange = range(0,130) + range(130,200,5) + range(200,1000,50) + range(1000,10000, 500) + range(10000, 45500, 5000)


def calibration(range):
	for i in range:
    		command = '{0} -o {1}'.format(filename_dac_exe, i )
    		subprocess.call([command], shell=True)
    		time.sleep(5)
    
    		command = 'ssh {0} \'python {1} {2}\''.format(hostname, filename_keithley, i)
		
    		subprocess.call([command], shell=True)
		
def calibration_saveToTextFile(range,outFileName = 'calibration_output.txt'):
	outFile = open(outFileName,'w')

	for i in range:
    		command = '{0} -o {1}'.format(filename_dac_exe, i )
    		subprocess.call([command], shell=True)
    		time.sleep(5)
		outFail = 1
    		command = 'ssh {0} python {1} {2}'.format(hostname, filename_keithley, i)
		while outFail != 0:
			outFail = subprocess.call(command.split(), stdout=outFile)
		

def calibration_saveTGraph(range, outFileName = 'calibration_tgraph.root',cardNum = 0, pigtail = 0):
	from ROOT import TGraphErrors, TFile
	from array import array
	current_mean = []
	current_stddev = []

	for i in range:
		command = '{0} -o {1}'.format(filename_dac_exe, i )
		subprocess.call([command], shell=True)
		time.sleep(5)
		
		command = 'ssh {0} \'python {1} {2}\''.format(hostname, filename_keithley, i)
        
		output = subprocess.Popen(command.split(), stdout=PIPE).communicate().split(',')
	if len(output)==4:
		current_mean.append(float(output[0]))
		current_stddev.append(float(output[1]))
	elif len(output)==5:
		current_mean.append(float(output[1]))
		current_stddev.append(float(output[2]))
    			
    
	xRange = array('d',range)
	xRangeErr = array('d',[0.]*len(range))
	yCurrent = array('d',current_mean)
	yCurrentErr = array('d',current_stddev)

	graph = TGraphErrors(len(xRange),xRange,yCurrent,xRangeErr,yCurrentErr)
	graphName ="calibration_card_%i_pigtail_%i_LSB_%i_%i" %(cardNum, pigtail, range[0],range[-1])
	graph.SetNameTitle(graphName, graphName)

	roo_outfile = TFile(outFileName,'recreate')
	graph.Write()
	roo_outfile.Close()
	print 'done'

#calibration(R1)

calibration_saveToTextFile(FullRange,outTextFileName)

command = '{0} -o {1}'.format(filename_dac_exe, 0 )
subprocess.call([command], shell=True)
