import sys
import os
import re
import mmap
#import numpy as np
from bitstring import  ConstBitStream #BitArray, BitStream, pack, Bits,
from datetime import datetime, timedelta
#import gc

import argparse

parser = argparse.ArgumentParser(description='Extracts realtime meta-data from XAVC files and put to SRT (subtitle) file',)
parser.add_argument('infile',help='First file or filepath should be the source')
args = parser.parse_args()

def getfn():
    k=0
    j=0
    k= 8*52
    j = k + 8*2
    fn = sub[k:j].read('uint:16')
    fn= 2**((1-float(fn)/65536)*8)
    fn=round(fn,1)
    return str(fn)

def getss():
    k=0
    j=0
    k= 8*109 + delta1
    j= k + 4*8
    ss1 = sub[k:j].read('int:32')
    ss2 = sub[k+4*8:j+4*8].read('int:32')
    ss = str(ss1) + '/' +str(ss2)
    return str(ss)

def getiso():
    k=0
    j=0
    k= 8*127 + delta1
    j= k + 2*8
    iso = sub[k:j].read('uint:16')
    return str(iso)

def getdist():
    k=0
    j=0
    k= 8*52 + delta1
    j= k + 2*8
    diste = sub[k:j].read('int:4')
    distm = sub[k+4:j].read('uint:12')
    dist = float(distm*(10**diste))
    return str(dist)+'m'

def getdb():
    k=0
    j=0
    k= 8*121 + delta1
    j= k + 2*8
    db = sub[k:j].read('uint:16')/100
    return str(db)

def getsdur():
    if ffps == '59.94p':
        sdur = 1001.0/60000.0
    elif ffps == '29.97p':
        sdur = 1001.0/30000.0
    elif ffps == '50p':
        sdur = 1.0/50.0
    elif ffps == '25p':
        sdur = 1.0/25.0
    elif ffps == '24p':
        sdur = 100.0/24000.0
    elif ffps == '100p':
        sdur = 1.0/100.0
    elif ffps == '120p':
        sdur = 1.0/120.0
    return sdur

def getpasm():
    k = 78*8+delta1
    j = k+16*8
    if sub[k:j] == '0x060E2B340401010B0510010101010000' : ae = 'Exp. mode: M '
    elif sub[k:j] == '0x060E2B340401010B0510010101020000' : ae = 'Exp. mode: AUTO'
    elif sub[k:j] == '0x060E2B340401010B0510010101030000' : ae = 'Exp. mode: GAIN'
    elif sub[k:j] == '0x060E2B340401010B0510010101040000' : ae = 'Exp. mode: A'
    elif sub[k:j] == '0x060E2B340401010B0510010101050000' : ae = 'Exp. mode: S'
    else : ae = 'N/A'
    return ae

def sampletime (ssec,sdur):
    sec = timedelta(seconds=float(ssec))
    delta = timedelta(seconds=float(sdur))
    d = datetime(1,1,1) + sec
    de = d+delta
    d=str(d).split(' ',1)[1]
    d=d.replace('.',',')
    de=str(de).split(' ',1)[1]
    de=de.replace('.',',')
    result =  d[:-3] + ' --> ' + de[:-3]
    return result

delta1 = 0

if not os.path.exists(args.infile) :
    print ('Error! Given input file name not found! Please check path given in CMD or set in script code!')
    sys.exit()

#F = "C:/Users/ruskugaa/Downloads/C0275.mp4"
#F = "D:/Temp/rtmd/C0002.MP4"
#F = "D:/Temp/rtmd/C0078.MP4"
F = args.infile

print 'Opened file ' + F
print 'Analyzing...'
s = ConstBitStream(filename=F)

### NRT_Acquire START ###
filesize = os.path.getsize(F)

all_the_data = open(F,'r+')
offset = (filesize/mmap.ALLOCATIONGRANULARITY-1)* mmap.ALLOCATIONGRANULARITY
m = mmap.mmap(all_the_data.fileno(),0,access=mmap.ACCESS_READ, offset = offset)

pattern = 'Duration value="(.*?)".*?formatFps="(.*?)".*?Device manufacturer="(.*?)".*?modelName="(.*?)"'
rx = re.compile(pattern, re.IGNORECASE|re.MULTILINE|re.DOTALL)
result = rx.findall(m)

for duration,ffps, vendor, modelname in result:
    print 'Model Name:', vendor, modelname
    print 'Video duration (frames):',duration
    print 'Video framerate:',ffps
all_the_data.close()
### NRT_Acquire END ###
    

samples = s.findall('0x001c0100', bytealigned=True) 
print 'Processing...'

sdur = getsdur()

ssec = 0
k=0
offset = 0
with open(F[:-3]+'srt', 'w') as f:

    for c in range(int(duration)):
        s = ConstBitStream(filename=F)
        #Debug# print s
        samples = (s.find('0x001c0100', start = offset, bytealigned=True))
        #Debug# print 'Samples:', len(samples)
        #Debug# if samples [0]
        i = samples[0]
        #Debug# print i
        sub = s[i:(i+1024*8)]
        if sub[54*8:55*8] != '0x06' and sub[134*8:135*8] !='0x06':
            delta1 = 48

        fn = getfn()
        ss=getss()
        iso=getiso()
        db = getdb()
        ae=getpasm()
        if sub[54*8:55*8] != '0x06': 
            dist=getdist()
        else: dist = 'N/A'
        c+=1
        
        #Debug# print c

        f.write (str(c) +'\n')
        f.write (str(sampletime(ssec,sdur)) + '\n')
        
        f.write ('FPS: ' + ffps + '  Frame: ' + str(c) + '/' + duration + '\n') #removed ('Model: ' + vendor + ' ' + modelname + ' |)
        f.write (ae +'  ISO: ' + str(iso) + '  Gain: ' + str(db) +'db' + '  F' + str(fn) + '  Shutter: ' + str(ss) + '\n')
        f.write ('Focus Distance: ' + dist + '\n')
        f.write ('\n')
        ssec=ssec+sdur
        offset = s.pos + 1024*8 - 8
        #Debug# print offset



    #Debug" print 'Last pos', i
    print 'Last frame processed:', c
    #Debug# print("type error: " + str(e))
print 'Success! SRT file created: ' + F[:-3]+'srt'

#Debug# gc.collect()
