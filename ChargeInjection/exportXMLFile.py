from sqlite3 import *
from datetime import *

# from barCodeMap import barCodeMap

# def getBarCode(uniqueID):
#     ibarCodeMap

qieParams = connect('qieCalibrationParameters.db')

cursor = qieParams.cursor()

QIE_ID_list = list(set(cursor.execute("select id from qieparams").fetchall()))

sample1Type = open("testSample1.xml",'w')

versionNumber = 1

outputline =  '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
outputline += '<ROOT xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n'
outputline += '<PARTS>\n'
outputline += '\n'
outputline += '\n'

sample1Type.write(outputline)

for qieID in QIE_ID_list:
    qieID = qieID[0].replace(' ','')
    outputline =  '<PART mode="auto">\n'
    outputline += '        <KIND_OF_PART>HCAL QIE10 Card</KIND_OF_PART>\n'
    outputline += '        <BARCODE>%s</BARCODE>\n'
    
    outputline += '        <COMMENT_DESCRIPTION>QIE10-ADC Relationship</COMMENT_DESCRIPTION>\n'
    outputline += '    <CHILDREN>\n'
    for i_qie in range(24):
        outputline += '        <PART mode="auto">\n'
        outputline += '            <KIND_OF_PART>HCAL QIE10 ADC</KIND_OF_PART>\n'
        outputline += '            <NAME_LABEL>%s-%i</NAME_LABEL>\n'%(qieID, i_qie)
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

sample2Type = open("testSample2.xml",'w')

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
QIE_ID_list = [(u'0x8d000000 0xaa24da70',)]
print QIE_ID_list
for qieID in QIE_ID_list:
    unique_id = str(qieID[0])
    qieID = qieID[0].replace(' ','')
    for i_qie in range(13,24):
        outputline = ''
        outputline += '    <DATA_SET>\n'
        outputline += '        <VERSION>V%i</VERSION>\n'%versionNumber
        outputline += '        <COMMENT_DESCRIPTION>NORM Calib Constants of QIE10</COMMENT_DESCRIPTION>\n'
        outputline += '        <PART>\n'
        outputline += '            <KIND_OF_PART>HCAL QIE ADC</KIND_OF_PART>\n'
        outputline += '            <NAME_LABEL>%s-%i</NAME_LABEL>\n'%(qieID, i_qie)
        outputline += '        </PART>\n'
        outputline += '        <DATA>\n'
        for i_capID in range(4):
            for i_range in range(4):
                query = (unique_id, i_qie, i_capID, i_range)
                print query
                slope_offset = cursor.execute("select slope, offset from qieparams where id = ? and qie = ? and capID = ? and range = ?", query).fetchall()
                print slope_offset
                outputline += '            <CAP%i_RANGE%i_OFFSET>%.6f</CAP%i_RANGE%i_OFFSET>\n' %(i_capID, i_range, slope_offset[1], i_capID, i_range)
                outputline += '            <CAP%i_RANGE%i_SLOPE>%.6f</CAP%i_RANGE%i_SLOPE>\n' %(i_capID, i_range, slope_offset[1], i_capID, i_range)
        outputline += '        </DATA>\n'
        outputline += '    </DATA_SET>\n'
        sample2Type.write(outputline)
