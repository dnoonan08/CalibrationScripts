import os
import sys
import subprocess
from time import sleep

def setDAC( dacLSB = 0, dacChannel = -1,relayOn = False):
        if relayOn==True:
                os.system("export LD_LIBRARY_PATH=/usr/local/lib:/home/hep/ChargeInjector/DAC/mcc-libhid_multDACs:$LD_LIBRARY_PATH; /home/hep/ChargeInjector/DAC/mcc-libhid_multDACs/dacQinjector -dOn -o {0} -c {1}".format(dacLSB, dacChannel) )
        else:
                os.system("export LD_LIBRARY_PATH=/usr/local/lib:/home/hep/ChargeInjector/DAC/mcc-libhid_multDACs:$LD_LIBRARY_PATH; /home/hep/ChargeInjector/DAC/mcc-libhid_multDACs/dacQinjector  -dOff -o {0} -c {1}".format(dacLSB, dacChannel) )
	sleep(2)


def blinkDAC():
	os.system("export LD_LIBRARY_PATH=/usr/local/lib:/home/hep/ChargeInjector/DAC/mcc-libhid_multDACs:$LD_LIBRARY_PATH; /home/hep/ChargeInjector/DAC/mcc-libhid_multDACs/dacQinjector -b")
	
def getDACNumber():
	count = 0
	foundDevice = False
	while not foundDevice and count < 5:
		command = "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/hep/ChargeInjector/DAC/mcc-libhid_multDACs:/usr/local/lib; /home/hep/ChargeInjector/DAC/mcc-libhid_multDACs/dacQinjector -verbose"
		output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).communicate()[0]

		outLines = output.split('\n')
		foundDevice = False
		dacNums = []
		count += 1
		for line in outLines:
			print line
			if 'DAC Serial Number' in line:
				foundDevice = True

				number = line.split()[-1]
				if number == '00101659':
					dacNums.append('01')
				elif number == '00104076':
					dacNums.append('02')
                                elif number == '00108124':
					dacNums.append('03')
                                elif number == '00108645':
					dacNums.append('04')
                                elif number == '00108644':
					dacNums.append('05')
                                elif number == '00108646':
					dacNums.append('06')
                                elif number == 'Error':
					foundDevice = False
					print outLines
	if not foundDevice:
		print "!!! Unable to find USB DAC !!!"
		print "Exiting"
		print count
		#sys.exit()
	if len(dacNums)==0:
		print "Unknown DAC"
		print "Exiting"
		print outLines
		#sys.exit()

	print 'Using DAC %s' %dacNums
	return dacNums


if __name__=='__main__':
	if '-b' in sys.argv:
		blinkDAC()
		sys.exit()
		

	if len(sys.argv)==2:
		setDAC(sys.argv[1])

	if len(sys.argv)==3:
		setDAC(sys.argv[1],sys.argv[2])

	if len(sys.argv)==4:
		setDAC(sys.argv[1],sys.argv[2],eval(sys.argv[3]))
