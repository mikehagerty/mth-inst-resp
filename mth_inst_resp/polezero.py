
import numpy as np

class polezero:
    '''
    This class holds a standard polezero response
    '''
    def __init__(self, name, AorB, unitsIn, unitsOut, a0, sensitivity, sensitivity_f, poles, zeros):
        '''
        :param name: name it
        :type  name: str
        :param AorB: type: {'A'=Laplace transform (rad/s); 'B'=Analog response (Hz); 'D'=Digital (Z-transform)}
        :type  AorB: str
        :param unitsIn: e.g., 'M' or 'M/S' **Warning these are often incorrect in the pzfile!
        :type  unitsIn:  str
        :param unitsOut: e.g., 'COUNTS'
        :type  unitsOut: str
        :param a0: polezero normalization factor (normalize response amp=1 in midband)
        :type  a0: float
        :param sensitivity:
        :type  sensitivity: float
        :type  sensitivity_f: float
        :type  poles: numpy complex array
        :type  zeros: numpy complex array
        '''
        self.name         = name
        self.AorB         = AorB 
        self.unitsIn      = unitsIn
        self.unitsOut     = unitsOut
        self.npoles       = poles.size
        if zeros is not None:
            self.nzeros   = zeros.size
        else:
            self.nzeros   = 0
        self.poles        = poles
        self.zeros        = zeros
        self.a0           = a0
        self.sensitivity  = sensitivity
        self.sensitivity_f= sensitivity_f
        #self.constant     = constant

    def removeZero(self):

        hasZeroAtOrigin = False
        ii=-1
        for i in range(self.zeros.size):
            if self.zeros[i].real == 0 and self.zeros[i].imag == 0:
                #print "Found origin at i=%d" % i
                hasZeroAtOrigin = True
                ii=i
                break

        if hasZeroAtOrigin:
            zeros = np.delete(self.zeros, ii)
            self.zeros  = zeros
            self.nzeros = zeros.size
            return 1
        else:
            return -1


    def __str__(self):

        string = "\n"
        string += "name:\t%s\n" % self.name
        string += "type:\t%s\n" % self.AorB
        string += "In:\t%s\n" % self.unitsIn
        string += "Out:\t%s\n" % self.unitsOut
        string += "a0:\t%e\n" % self.a0
        string += "sensitivity:  %e\n" % self.sensitivity
        string += "npoles:\t%d\n" % self.npoles
        for i in range(self.npoles):
            string += "  %d: %14.12e  %14.12e\n" % (i, self.poles[i].real, self.poles[i].imag)
        string += "nzeros:\t%d\n" % self.nzeros
        for i in range(self.nzeros):
            string += "  %d: %14.12e  %14.12e\n" % (i, self.zeros[i].real, self.zeros[i].imag)
        
        return string
