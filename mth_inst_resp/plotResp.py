
from libInst import read_sacpz_file, getResponse
from libPlotResp import plotResponse
from libNominals import getPoleZero
from mth_utils.liblog import getLogger

from sys import exit
import sys
import getopt
import numpy as np

logger = getLogger()

fname = 'plotResp.py'

# Most polezero files - e.g, from FetchData -sd - are actually Displacement, 
#      even though they (still) say unitsIn = M/S
# By default, we will attempt to remove a zero at the origin so that the
#      reponse plots flat (to velocity)
# If polezero file really is Velocity, then use the '--vel' flag on the cmd line
#      and all zeros will be used
pzVelocity = False 

def processCmdLine():
    usage  = "Usage: %s -f sacpz_filename [also --f or --file] [--vel = This really is a velocity pz resp]" % fname
    pzFile = None
    global pzVelocity

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'f:h', ['help', 'f=', 'file=', 'vel'])
        if len(args) > 0:
            exit_now(usage)
    except getopt.GetoptError:   # Throw error if opt not in list above
        exit_now(usage)
    for opt, arg in opts:
        #print ">> opt=[%s] arg=[%s]" % (opt,arg)
        if opt in ('-f', '--f', '--file'):
            pzFile = arg
        elif opt in ('--vel'):
            pzVelocity = True
        else:
            print("Error: unknown opt=[%s]" % opt)
            exit_now(usage)
    if pzFile is None:
        exit_now(usage)

    return pzFile

def exit_now(usage):
    print(usage)
    exit(2)

def main():
    pzFilename = processCmdLine()
    pzs = read_sacpz_file(pzFilename)

    logger.info("%s: pzVelocity=[%s]" % (fname, pzVelocity))

    if pzVelocity:
        pass
    else:
        success = pzs.removeZero()
        if not success == 1:
            logger.error("%s: Error stripping zero at origin from pz" % (fname))

    freqs = np.logspace(-5, 2., num=200)
    resp  = getResponse(pzs, freqs, useSensitivity=False)
    if 1:
        title = "Type:%s [%s] [a0=%12.6e]" % ('Vel', pzs.name, pzs.a0)
    plotResponse(resp, freqs, title, xmin=.001, xmax=100.)
    exit()

## end main

if __name__=="__main__":
    main()
