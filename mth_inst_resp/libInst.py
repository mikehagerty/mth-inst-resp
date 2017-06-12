from __future__ import absolute_import
import numpy as np
import sys

# MTH: This is because, from within a package, source filenames are preceded by "." for
#      relative path, so from .polezero means to look in ./polezero.py
#      But this does *not* work for running the code from the cmd line (outside the pkg struct)
modulename = 'mth_inst_resp'
if modulename not in sys.modules:
    #print 'You have not imported the {} module'.format(modulename)
    from polezero import polezero
else:
    #print 'You HAVE imported the {} module'.format(modulename)
    from .polezero import polezero
    

def evalResp(pz, f):
    '''
    Expand the polezero into response at a single frequency, I(f)
    :param pz: instance of class polezero
    :param f:  single frequency
    '''
    s = 0.000 + 1.000j
    numerator   = 1.000 + 0.000j
    denominator = 1.000 + 0.000j

    if pz.AorB == 'A':
        s *= 2.*np.pi*f
    elif pz.AorB == 'B':
        s *= f
    else:
        print("Unknown pz response type=[%s]" % pz.AorB)

    for j in range(pz.nzeros):
        numerator *= (s - pz.zeros[j])

    for j in range(pz.npoles):
        denominator *= (s - pz.poles[j])

    Gf = numerator * pz.a0   # Make sure this is complex
    Gf /= denominator 
    return Gf;



def getResponse(pz, freqs, velocity=False, useSensitivity=True):
    '''
        We're expecting a standard IRIS polezero file for displacement,
            so if velocity=True try to shed one zero at origin
    '''

# This can be used if you know you are passing a Disp response but want a Vel response:
    if velocity:
        success = pz.removeZero()
        if not success == 1:
            logger.error("%s: Error stripping zero at origin from pz" % (fname))

    resp = np.zeros((len(freqs),), dtype=np.complex128)
    for i, f in enumerate(freqs):
        resp[i] = evalResp(pz, f)
        if useSensitivity:
            resp[i] *= pz.sensitivity
    return resp

def read_sacpz_file(filename):
    '''
* **********************************
* NETWORK   (KNETWK): AU
* STATION    (KSTNM): WR1
* LOCATION   (KHOLE):
* CHANNEL   (KCMPNM): BHZ
* CREATED           : 2017-02-02T01:23:27
* START             : 2005-01-31T00:00:00
* END               : 2599-12-31T23:59:59
* DESCRIPTION       : Warramunga Array, Australia
* LATITUDE          : -19.942600
* LONGITUDE         : 134.339500
* ELEVATION         : 389.0
* DEPTH             : 0.0
* DIP               : 0.0
* AZIMUTH           : 0.0
* SAMPLE RATE       : 40.0
* INPUT UNIT        : M
* OUTPUT UNIT       : COUNTS
* INSTTYPE          : Guralp CMG3ESP_30sec_ims/Guralp DM24-MK3 Datalogge
* INSTGAIN          : 4.000290e+03 (M/S)
* COMMENT           : V3180 A3242
* SENSITIVITY       : 2.797400e+09 (M/S)
* A0                : 8.883050e-02
* **********************************
ZEROS   5
    +0.000000e+00   +0.000000e+00
    +0.000000e+00   +0.000000e+00
    +0.000000e+00   +0.000000e+00
    +8.670000e+02   +9.050000e+02
    +8.670000e+02   -9.050000e+02
POLES   4
    -1.486000e-01   +1.486000e-01
    -1.486000e-01   -1.486000e-01
    -3.140000e+02   +2.023000e+02
    -3.140000e+02   -2.023000e+02
CONSTANT    2.484944e+08
    '''
    fname = 'read_sacpz_file'

    with open(filename, 'r') as f:
        lines = f.readlines()

    zeros = None
    poles = None
    sensitivity = None
    a0 = None
    unitsIn = None
    unitsOut = None
    knet = ""
    ksta = ""
    kloc = ""
    kchan = ""

    for i in range(len(lines)):
        line = lines[i]
        #print "i=[%d] line=[%s]" % (i, line)

        if line[0] == '*':
            if line[2] != '*':
                split_list = line.split(':')
                field = split_list[0][1:]
                val   = split_list[1]
                # could have val = "" or val = 2.79E9 (M/S)
                val_list = val.split()
                nsplit=len(val_list)
                #print "field=", field, " val=", val

                if 'SENSITIVITY' in field:
                    sensitivity = float(val_list[0])
                elif 'A0' in field:
                    a0 = float(val_list[0])
                elif 'INPUT UNIT' in field:
                    unitsIn = val.strip()
                elif 'OUTPUT UNIT' in field:
                    unitsOut = val.strip()
                elif 'NETWORK' in field:
                    knet = val.strip()
                elif 'STATION' in field:
                    ksta = val.strip()
                elif 'LOCATION' in field:
                    kloc = val.strip()
                elif 'CHANNEL' in field:
                    kchan = val.strip()

        elif line[0:5] == 'ZEROS':
            try:
                nzeros = int(line[6:len(line)])
            except:
                print("%s.%s Error: can't read nzeros from line=[%s]" % (__name__, fname, line))
                exit(1)
            #zeros = np.zeros((nzeros,), dtype=np.complex128)
            zeros = np.zeros(nzeros, dtype=np.complex128)
            for j in range(nzeros):
                i += 1
                line = lines[i]
                (z_re, z_im) = line.split()
                zeros[j] = complex( float(z_re), float(z_im) )
        elif line[0:5] == 'POLES':
            try:
                npoles = int(line[6:len(line)])
            except:
                print("%s.%s Error: can't read npoles from line=[%s]" % (__name__, fname, line))
                exit(1)
            poles = np.zeros(npoles, dtype=np.complex128)
            for j in range(npoles):
                i += 1
                line = lines[i]
                (p_re, p_im) = line.split()
                poles[j] = complex( float(p_re), float(p_im) )

    name = "%s.%s %s.%s" % (knet, ksta, kloc, kchan)

    pz_ = polezero(name = name,
                         AorB = 'A', #type = 'A[Laplace Transform (Rad/sec)]',
                         unitsIn  = unitsIn,
                         unitsOut = unitsOut,
                         a0 = a0,
                         sensitivity = sensitivity,
                         sensitivity_f = 1.0,
                         poles = poles,
                         zeros = zeros)
    return pz_


####################################################################
# MTH: 09/2014
# This file contains the following obspy helper functions:
#
# sacpzToDictionary(sacpzString, '\n', ":") will convert the single
#	string (sacpzString) returned from obspy.iris.client.sacpz()
#   (e.g., the obspy interface to iris polezero web service)
#	into a dictionary similar to what is returned by the other
#	2 polezero get methods in obspy:
#		1. obspy.xseed.Parser.getPAZ()
#		2. obspy.arclink.Client.getPAZ()
#
# sacpzGetCoords(sacpzString, '\n', ":") - returns dictionary
#	of station coordinates pulled from sacpzString
#   ** This is needed because obspy polezero return methods above
#      do NOT include station lat,lon
#
####################################################################

import os.path

def getpzString(net, stn, loc, chn, path):
    '''
        Use path to form file name like: some/path/SACPZ.IW.DLMT.00.BHZ
        Read file in and return as single string
    '''
    pzfile = path + '/SACPZ.' + net + '.' + stn + '.' + loc + '.' + chn
    if not os.path.isfile(pzfile):
        print 'Error: pzfile=[%s] does NOT exist' % pzfile
        return None
    f = open(pzfile, 'r')
    pzstring = f.read()
    if len(pzstring) == 0:
        print 'Error reading pzfile=[%s]' % pzfile
        return None
    return pzstring

def sacpzGetCoords(s, pairSeparator, keyValueSeparator):
	dict={}
	pairs = s.split(pairSeparator)
	while pairs:
		pair = pairs.pop(0)
		#print 'pair=', pair
		if pair.find("LATITUDE") > 0:
			dict[u'latitude']=float(pair.split(keyValueSeparator)[1])
		if pair.find("LONGITUDE") > 0:
			dict[u'longitude']=float(pair.split(keyValueSeparator)[1])
		if pair.find("ELEVATION") > 0:
			dict[u'elevation']=float(pair.split(keyValueSeparator)[1])
	return dict

# sacpzToDictionary() - convert
# Note:
# - The polezero responses returned by IRIS web services all appear to be
#   in a standardized format:
#	+ input_units='M' (i.e., they have an added zero)
#	+ analog stage type = 'A' [rad/s]
#		- e.g., II stations have analog stage type = 'B' [Hz], but these are
#			    converted to 'A' by scaling the poles/zeros by 2pi and by
#				scaling the normalization factor A0 by 2pi
# - The conversion between SEED format and obspy paz dictionary is:
#			SEED convention			   --> obspy paz dictionary
#	+ polezero normalization factor A0 --> 'gain'
#	+ sensor gain = Stage 1 Gain       --> 'seisometer_gain'
#	+ Sensitivity = Stage 0 Gain	   --> 'sensitivity'
#   + digitizer gain = Stage 2 Gain    --> 'digitizer_gain'
#                                      *** IRIS pz does NOT contain this, though 
#								           obspy.xseed.Parser.getPAZ() does
def sacpzToDictionary(s, pairSeparator, keyValueSeparator):
    # e.g., s=1 huge string, pairSeparator='\n', keyValueSeparator=':'
    dict={}
    pairs = s.split(pairSeparator)
    while pairs:
        #try:
            line = pairs.pop(0)
            #print 'line=', line
            #if line.find("NETWORK") > 0:
            if line[0:9] == "* NETWORK":
                dict[u'network']=line.split(keyValueSeparator)[1].strip()
            elif line[0:9] == "* STATION":
                dict[u'station']=line.split(keyValueSeparator)[1].strip()
            elif line[0:10] == "* LOCATION":
                dict[u'location']=line.split(keyValueSeparator)[1].strip()
            elif line[0:9] == "* CHANNEL":
                dict[u'channel']=line.split(keyValueSeparator)[1].strip()
##---- these things are non-standard for obspy paz[] but are found in SAC Polzero string/file ----#
            elif line[0:9] == "* CREATED":
                dict[u'created']=line.split(keyValueSeparator)[1].strip()
            elif line[0:7] == "* START":
                dict[u'start']=line.split(keyValueSeparator)[1].strip()
            elif line[0:5] == "* END":
                dict[u'end']=line.split(keyValueSeparator)[1].strip()
            elif line[0:13] == "* DESCRIPTION":
                dict[u'description']=line.split(keyValueSeparator)[1].strip()
            elif line.find("LATITUDE") > 0:
                dict[u'latitude']=float(line.split(keyValueSeparator)[1])
            elif line.find("LONGITUDE") > 0:
                dict[u'longitude']=float(line.split(keyValueSeparator)[1])
            elif line.find("ELEVATION") > 0:
                dict[u'elevation']=float(line.split(keyValueSeparator)[1])
            elif line.find("DEPTH") > 0:
                dict[u'depth']=float(line.split(keyValueSeparator)[1])
            elif line.find("DIP") > 0:
                dict[u'dip']=float(line.split(keyValueSeparator)[1])
            elif line.find("AZIMUTH") > 0:
                dict[u'azimuth']=float(line.split(keyValueSeparator)[1])
            elif line.find("SAMPLE RATE") > 0:
                dict[u'sampleRate']=float(line.split(keyValueSeparator)[1])
##-----------------------------------------------------------------------------------------------#
            elif line[0:4]=="* A0" > 0:
                gain=float(line.split(keyValueSeparator)[1])
                if (gain <= 0):
                    #print 'Error: gain <= 0'
                    raise Exception('sacpzToDictionary: gain <= 0')
                    return None
                else:
                    dict['gain']=gain
            elif line[0:10] == "* INSTGAIN":
                try:
                    dict['seismometer_gain']=float((line.split(keyValueSeparator)[1].lstrip()).split()[0])
                except Exception as e:
                    #print 'sacpzToDictionary: Warning: while setting seismometer_gain [%s]' % e
                    dict['seismometer_gain']=0.0
            elif line[0:13] == "* SENSITIVITY":
                sensitivity=float((line.split(keyValueSeparator)[1].lstrip()).split()[0])
                if (sensitivity == 0):
                    raise Exception('sacpzToDictionary: SENSITIVITY == 0')
                    return None
                elif (sensitivity < 0):
                    iDummyDoSomething = 1
                    #MTH: This appears to be used to indicate flipped polarity (?)
                    #print 'sacpzToDictionary: Warning: sensitivity <= 0'
                    #raise Exception('sacpzToDictionary: sensitivity <= 0')
                    #return None
                else:
                    iDummyDoSomething = 0
                    #dict['sensitivity']=sensitivity
                dict['sensitivity']=sensitivity
            elif line[0:10] == "* INSTTYPE":
                dict['instrument']=line.split(keyValueSeparator)[1].lstrip().rstrip()
            elif line[0:12] == "* INPUT UNIT":
                dict['input_unit']=line.split(keyValueSeparator)[1].strip()
            elif line[0:13] == "* OUTPUT UNIT":
                dict['output_unit']=(line.split(keyValueSeparator)[1]).strip()
		    #This does not work since there is no space before ZEROS on the line=pair
		    #elif pair.find("ZEROS") > 0:
            elif line[0:5] == "ZEROS":
                nzeros=int(line.split()[1])
                if nzeros < 1:
                    #print 'Error: nzeros < 1'
                    raise Exception('sacpzToDictionary: nzeros < 1')
                    return None
                else:
                    list=[]
                    for i in range(0,nzeros):
                        zero = pairs.pop(0)
                        zero = zero.lstrip()
                        zero = zero.rstrip()
                        zero = zero.split('\t')	        # zero is now a list ['+0.0000', '+0.0000j']
                        zero = complex(float(zero[0]), float(zero[1]))
                        list.append(zero)
                    dict['zeros'] = list
            elif line[0:5] == "POLES":
                npoles=int(line.split()[1])
                if npoles < 1:
                    #print 'Error: npoles < 1'
                    raise Exception('sacpzToDictionary: npoles < 1')
                    return None
                else:
                    list=[]
                    for i in range(0,npoles):
                        pole = pairs.pop(0)
                        pole = pole.lstrip()
                        pole = pole.rstrip()
                        pole = pole.split('\t')	# pole is a list ['+0.0000', '+0.0000j']
                        pole = complex(float(pole[0]), float(pole[1]))
                        list.append(pole)
                    dict['poles'] = list

        #except Exception as e:
            #print 'sacpzToDictionary: Caught e=' , e
            #return None

    return dict

