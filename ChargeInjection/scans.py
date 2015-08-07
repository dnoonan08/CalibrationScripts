#DACscan = [ 0.0001 , 0.0002 , 0.0003 , 0.0004 , 0.0005 , 0.0006 , 0.0007 , 0.0008 , 0.0009 ,
 #           0.0010 , 0.0020 , 0.0030 , 0.0040 , 0.0050 , 0.0060 , 0.0070 , 0.0080 , 0.0090 ,
  #          0.0100 , 0.0200 , 0.0300 , 0.0400 , 0.0500 , 0.0600 , 0.0700 , 0.0800 , 0.0900 ,
   #         0.1000 , 0.2000 , 0.3000 , 0.4000 , 0.5000 , 0.6000 , 0.7000 , 0.8000 , 0.9000 ,
    #        1.0000 , 2.0000 , 3.0000 , 4.0000 , 5.0000 ]
DACscan = []
for i in range(30000):
	DACscan.append(i)

DACscan_range0 = range(160)
DACscan_range1 = range(100,240, 5)+ range(240,500,10) + range(500,1000,20) + range(1000,1600,50)
DACscan_range2 = range(1200,2100, 75)+range(2100,4200,150) + range(4200,9000,300) + range(9000,12000,500)
DACscan_range3 = range(12000,14000,1000)

# for i in range(0, 130, 1):
#     DACscan_range0.append(i)
# for i in range(130,480,10):
#     DACscan_range0.append(i)
# DACscan_range1 = []
# for i in range(125, 4000 , 30): # run scan from 125
#     DACscan_range1.append(i)
# DACscan_range3 = []
# DACscan_range2 = []
# for i in range(4000, 6200 , 100 ):
#     DACscan_range2.append(i)
# for i in range(6200, 34000, 2000):
#     DACscan_range3.append(i)


scans = { "0" : DACscan_range0 ,
          "1" : DACscan_range1 ,
          "2" : DACscan_range2 ,
          "3" : DACscan_range3 ,
          "custom" : DACscan }

