from sqlite3 import *
from datetime import *
import sys

if len(sys.argv) != 2:
    print 'specify directory'
    sys.exit()
directory = sys.argv[1]

#qieParams = connect('qieCalibrationParameters.db')
qieParams = connect(directory+'/qieCalibrationParameters.db')

cursor = qieParams.cursor()

QIE_ID_list = list(set(cursor.execute("select id from qieparams").fetchall()))

sample1Type = open("partialInstallationQIEs_1.xml",'w')

versionNumber = 1

outputline =  '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
outputline += '<ROOT xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n'
outputline += '<PARTS>\n'
outputline += '\n'
outputline += '\n'

sample1Type.write(outputline)

from SerialNumberMap import *

for qieID in QIE_ID_list:
    print qieID
    serialNum = mapUIDtoSerial[qieID[0]]
    serialNum += 3040000000000500000
    print serialNum
#    qieID = qieID[0].replace(' ','')
    outputline =  '<PART mode="auto">\n'
    outputline += '        <KIND_OF_PART>HCAL QIE10 Card</KIND_OF_PART>\n'
    outputline += '        <BARCODE>%s</BARCODE>\n'%serialNum
    outputline += '        <SERIALNUMBER>%s</SERIALNUMBER>\n'%qieID    
    outputline += '        <COMMENT_DESCRIPTION>QIE10-ADC Relationship</COMMENT_DESCRIPTION>\n'
    outputline += '    <CHILDREN>\n'
    for i_qie in range(24):
        outputline += '        <PART mode="auto">\n'
        outputline += '            <KIND_OF_PART>HCAL QIE10 ADC</KIND_OF_PART>\n'
        outputline += '            <NAME_LABEL>%s-%i</NAME_LABEL>\n'%(serialNum, i_qie)
        outputline += '            <PREDEFINED_ATTRIBUTES>\n'
        outputline += '                <ATTRIBUTE>\n'
        outputline += '                    <NAME>QIE10 ADC Channel Number</NAME>\n'
        outputline += '                    <VALUE>%i</VALUE>\n'%i_qie
        outputline += '                </ATTRIBUTE>\n'
        outputline += '            </PREDEFINED_ATTRIBUTES>\n'
        outputline += '        </PART>\n'
    outputline += '    </CHILDREN>\n'
    outputline += '</PART>\n\n\n'
    sample1Type.write(outputline)    

outputline =  '</PARTS>\n'
outputline += '</ROOT>\n'
sample1Type.write(outputline)    

sample2Type = open("partialInstallationQIEs_2.xml",'w')

outputline = ''
outputline += '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
outputline += '<ROOT xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n'
outputline += '\n'
outputline += '  <HEADER>\n'
outputline += '    <TYPE>\n'
outputline += '      <EXTENSION_TABLE_NAME>QIE10_ADC_NORMMODE</EXTENSION_TABLE_NAME>\n'
outputline += '      <NAME>QIE10 Normal Mode Calibration Constants</NAME>\n'
outputline += '    </TYPE>\n'
outputline += '\n'
outputline += '    <RUN>\n'
outputline += '    <RUN_NAME>QIE10 Normal Mode Calib Consts</RUN_NAME>\n'
outputline += '    <RUN_BEGIN_TIMESTAMP>%s</RUN_BEGIN_TIMESTAMP>\n'%str(datetime.now())
outputline += '    <INITIATED_BY_USER>dnoonan</INITIATED_BY_USER>\n'
outputline += '    <LOCATION>CERN 904</LOCATION>\n'
outputline += '    <COMMENT_DESCRIPTION>Corrected QIE Channel NORM Constants</COMMENT_DESCRIPTION>\n'
outputline += '    </RUN>\n'
outputline += '  </HEADER>\n'
outputline += '\n'
sample2Type.write(outputline)
#QIE_ID_list = [(u'0x8d000000 0xaa24da70',)]
print QIE_ID_list
for qieID in QIE_ID_list:
    unique_id = str(qieID[0])
    serialNum = mapUIDtoSerial[qieID[0]]
    serialNum += 3040000000000500000
#    qieID = qieID[0].replace(' ','')
    for i_qie in range(24):
        outputline = ''
        outputline += '    <DATA_SET>\n'
        outputline += '        <VERSION>V%i</VERSION>\n'%versionNumber
        outputline += '        <COMMENT_DESCRIPTION>NORM Calib Constants of QIE10</COMMENT_DESCRIPTION>\n'
        outputline += '        <PART>\n'
        outputline += '            <KIND_OF_PART>HCAL QIE10 ADC</KIND_OF_PART>\n'
        outputline += '            <NAME_LABEL>%s-%i</NAME_LABEL>\n'%(serialNum, i_qie)
        outputline += '        </PART>\n'
        outputline += '        <DATA>\n'
        for i_capID in range(4):
            for i_range in range(4):
                query = (unique_id, i_qie+1, i_capID, i_range)
#                print query
                slope_offset = cursor.execute("select slope, offset from qieparams where id = ? and qie = ? and capID = ? and range = ?", query).fetchall()
                if len(slope_offset)>0:
#                    print slope_offset[0]
                    outputline += '            <CAP%i_RANGE%i_OFFSET>%.6f</CAP%i_RANGE%i_OFFSET>\n' %(i_capID, i_range, slope_offset[0][1], i_capID, i_range)
                    outputline += '            <CAP%i_RANGE%i_SLOPE>%.6f</CAP%i_RANGE%i_SLOPE>\n' %(i_capID, i_range, slope_offset[0][0], i_capID, i_range)
        outputline += '        </DATA>\n'
        outputline += '    </DATA_SET>\n'
        sample2Type.write(outputline)
sample2Type.write('</ROOT>\n')


sample3Type = open("partialInstallationQIEs_3.xml",'w')

qieTestParams = connect(directory+'/qieTestParameters.db')
cursorTest = qieTestParams.cursor()

outputline = ''
outputline += '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
outputline += '<ROOT xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n'
outputline += '\n'
outputline += '  <HEADER>\n'
outputline += '    <TYPE>\n'
outputline += '      <EXTENSION_TABLE_NAME>QIE10_ADC_PROPERTIES</EXTENSION_TABLE_NAME>\n'
outputline += '      <NAME>QIE10 Properties</NAME>\n'
outputline += '    </TYPE>\n'
outputline += '\n'
outputline += '\n'
outputline += '    <RUN>\n'
outputline += '      <RUN_NAME>QIE10 Properties</RUN_NAME>\n'
outputline += '      <RUN_BEGIN_TIMESTAMP>%s</RUN_BEGIN_TIMESTAMP>\n'%str(datetime.now())
outputline += '      <INITIATED_BY_USER>dnoonan</INITIATED_BY_USER>\n'
outputline += '      <LOCATION>CERN 904</LOCATION>\n'
outputline += '      <COMMENT_DESCRIPTION>QIE10 ADC Properties</COMMENT_DESCRIPTION>\n'
outputline += '    </RUN>\n'
outputline += '  </HEADER>\n'
outputline += '\n'
sample3Type.write(outputline)
for qieID in QIE_ID_list:
    unique_id = str(qieID[0])
    serialNum = mapUIDtoSerial[qieID[0]]
    serialNum += 3040000000000500000
#    qieID = qieID[0].replace(' ','')
    for i_qie in range(24):
        outputline = ''
        outputline += '    <DATA_SET>\n'
        outputline += '        <VERSION>V%i</VERSION>\n'%versionNumber
        outputline += '        <COMMENT_DESCRIPTION>QIE10 Properties</COMMENT_DESCRIPTION>\n'
        outputline += '        <PART>\n'
        outputline += '            <KIND_OF_PART>HCAL QIE10 ADC</KIND_OF_PART>\n'
        outputline += '            <NAME_LABEL>%s-%i</NAME_LABEL>\n'%(serialNum, i_qie)
        outputline += '        </PART>\n'
        outputline += '        <DATA>\n'
        query = (unique_id, i_qie+1)
                
        params = cursorTest.execute("select type1_r0, type2_r0, type1_r1, type2_r1, type3_r1, type1_r2, type2_r2, tdcstart from qietestparams where id = ? and qie = ?", query).fetchall()
        #print params
        if len(params) > 0:
            type1_r0, type2_r0, type1_r1, type2_r1, type3_r1, type1_r2, type2_r2, tdcstart = params[0]
            outputline += '            <RNG0TO1_ERR_RATE_TYP1>%.6f</RNG0TO1_ERR_RATE_TYP1>\n'%(type1_r0)
            outputline += '            <RNG0TO1_ERR_RATE_TYP2>%.6f</RNG0TO1_ERR_RATE_TYP2>\n'%(type2_r0)
            outputline += '            <RNG1TO2_ERR_RATE_TYP1>%.6f</RNG1TO2_ERR_RATE_TYP1>\n'%(type1_r1)
            outputline += '            <RNG1TO2_ERR_RATE_TYP2>%.6f</RNG1TO2_ERR_RATE_TYP2>\n'%(type2_r1)
            outputline += '            <RNG1TO2_ERR_RATE_TYP3>%.6f</RNG1TO2_ERR_RATE_TYP3>\n'%(type3_r1)
            outputline += '            <RNG2TO3_ERR_RATE_TYP1>%.6f</RNG2TO3_ERR_RATE_TYP1>\n'%(type1_r1)
            outputline += '            <RNG2TO3_ERR_RATE_TYP2>%.6f</RNG2TO3_ERR_RATE_TYP2>\n'%(type2_r1)
            outputline += '            <TDC_THSHLD_CALIB>%.6f</TDC_THSHLD_CALIB>\n'%(tdcstart)
        outputline += '        </DATA>\n'
        outputline += '    </DATA_SET>\n'
        sample3Type.write(outputline)
sample3Type.write('</ROOT>\n')
