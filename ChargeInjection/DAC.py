import os
import sys
import subprocess
from time import sleep

def setDAC( dacLSB = 0, dacChannel = -1):
	os.system("export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib; /nfshome0/dnoonan/mcc-libhid/dacQinjector  -o {0} -c {1}".format(dacLSB, dacChannel) )
	sleep(2)


def getDACNumber():
	count = 0
	foundDevice = False
	while not foundDevice and count < 5:
		command = "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib; /nfshome0/dnoonan/mcc-libhid/dacQinjector  -o 0"
		output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).communicate()[0]

		outLines = output.split('\n')
		foundDevice = False
		dacNum = '00'
		for line in outLines:
			if 'USB 3105 Device is found' in line:
				foundDevice = True
			if 'DAC Serial Number' in line:
				number = line.split()[-1]
				if number == '00101659':
					dacNum = '01'
				if number == '00104076':
					dacNum = '02'				
				if number == 'Error':
					foundDevice = False
					count += 1
					print outLines
	if not foundDevice:
		print "!!! Unable to find USB DAC !!!"
		print "Exiting"
		print count
		#sys.exit()
	if dacNum == '00':
		print "Unknown DAC"
		print "Exiting"
		print outLines
		#sys.exit()

	print 'Using DAC %s' %dacNum
	return dacNum


if __name__=='__main__':
	if len(sys.argv)==2:
		setDAC(sys.argv[1])

	if len(sys.argv)==3:
		setDAC(sys.argv[1],sys.argv[2])
