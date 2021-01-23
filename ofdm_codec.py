"""
OFDM transmitter and receiver with energy dispersal, pilot tones and cyclic prefix
"""
#	OFDM transmission and reception with energy dispersal
#
#	Copyright (C) 2020 Bernd Porr <mail@berndporr.me.uk>

#	This program is free software; you can redistribute it and/or modify
#	it under the terms of the GNU Lesser General Public License as published by
#	the Free Software Foundation; either version 2 of the License, or
#	(at your option) any later version.

#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.

#	You should have received a copy of the GNU Lesser General Public License
#	along with this program; if not, write to the Free Software
#	Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import numpy as np
import random
import scipy.signal

class OFDM:
    """
    OFDM encoder and decoder. The data is encoded as 4-QAM so two bits per frequency sample. Energy
    dispersal is done with a pre-seeded random number generator. Both pilot tones
    and the cyclic prefix are added so that the start of the symbol can be detected at the receiver. 
    The complex time series after the inverse Fourier Transform is modulated into a real valued stream 
    with a Nyquist quadrature modulator. On the receiver side the start of the symbol is detected by
    first doing a coarse search with the cyclic prefix and then a precision alignment with the pilots.
    """
    def __init__(self, nFreqSamples = 2048, pilotDistanceInSamples = 16, pilotAmplitude = 2, nData = 256, nCyclic = None):
        """
        nFreqSamples sets the number of frequency coefficients of the FFT. Pilot tones are injected
        every pilotDistanceInSamples-th frequency sample. The real valued pilot amplitude is pilotAmplitude.
        For transmission nData bytes are expected in an array. The length of the Cyclic prefix is the number
        of the real valued transmission samples.
        """
        # the total number of frequency samples
        self.nIFFT = nFreqSamples

        # number of data samples in bytes (coded/decoded)
        self.nData = nData

        if nCyclic:
            self.nCyclic = nCyclic
        else:
            # the default cyclic prefix is a 1/4 of the length of the symbol
            self.nCyclic = int(self.nIFFT * 2 / 4)

        # distance between pilots	
        self.pilot_distance = pilotDistanceInSamples

        # amplitudes of the pilot carrier at the beginning
        self.pilot_amplitude = pilotAmplitude

        # First frequency coefficient index used
        # We assume that the spectrum is centred symmetrically around DC and depends on nData
        self.k_start = int(self.nIFFT - self.nIFFT / self.pilot_distance / 2 - nData * 4 / 2)

    def encode(self,signal,data,randomSeed = 1):
        """
        Creates an OFDM symbol as QAM = 2 bits per frequency sample. 
        The signal is a real valued numpy array where the
        encoded data-stream is appended. The data is an array of bytes.
        The random seed sets the pseudo random number generator for the
        engergy dispersal.
        """
        # create an empty spectrum with all complex frequency values set to zero
        self.spectrum = np.zeros(self.nIFFT,dtype=complex)

        # we start with a negative frequency and then
        # work ourselves up to positive ones
        k = self.k_start
        
        # set the random number generator to a known start value
        # will generate always the same sequence from this start value
        # We xor its value with the grey values from the image to
        # generate a pseudo random sequence which is called "engery dispersal".
        random.seed(randomSeed)
        
        # counter for the pilots
        pilot_counter = self.pilot_distance/2
        
        # we loop through the data
        for x in range(self.nData):

            # get one byte
            databyte = int(data[x])

            # Energy dispersal
            # Generate the random number
            r = int(random.randint(0,255))
            # xor the grey value with the random number
            databyte = int(databyte ^ r)

            # Create the bitstream from the byte
            bitstream = np.zeros(8)
            for bit in range(8):
                m = 1 << bit
                testbit = m & databyte
                if testbit > 0:
                    bitstream[bit] = 1
                else:
                    bitstream[bit] = -1

            # now we have 8 bits which we distribute over four frequency samples
            # with 4-QAM / QPSK coding
            for cnum in range(4):
                # Let's check if we need to insert a pilot
                pilot_counter = pilot_counter - 1
                if pilot_counter == 0:
                    pilot_counter = self.pilot_distance
                    self.spectrum[k] = self.pilot_amplitude
                    k = k + 1
                    if not (k < self.nIFFT):
                        k = 0
                self.spectrum[k] = complex(bitstream[int(cnum*2)],
                                           bitstream[int(cnum*2+1)])
                # increase the frequency index
                k = k + 1
                # wrap to positive frequencies once we have reached the last index
                if not (k < self.nIFFT):
                    k = 0

        # Create one symbol by transforming our frequency samples into
        # complex timedomain samples
        complex_symbol = np.fft.ifft(self.spectrum)

        # Create an empty real valued symbol with twice the samples
        # because we need to interleave real and complex values
        tx_symbol = np.zeros(len(complex_symbol)*2)

        # Now we upsample at factor 2 and interleave
        # the I and Q signals
        # This is a digital quadrature modulator where we
        # interleave the complex signal c(n) as:
        # +Real(c(n)), +Imag(c(n)), -Real(c(n+1), -Imag(c(n+1))
        # and then repeat it until we have created our sequence
        # with twice the number of samples.
        s = 1
        txindex = 0
        for smpl in complex_symbol:
            tx_symbol[txindex] = s * np.real(smpl)
            txindex = txindex + 1
            tx_symbol[txindex] = s * np.imag(smpl)
            txindex = txindex + 1
            s = s * -1

        # Generate cyclic prefix taken from the end of the signal
        # This is now twice the length because we have two times
        # more samples, effectively transmitting at twice the
        # sampling rate
        cyclicPrefix = tx_symbol[-self.nCyclic:]

        # Add the cyclic prefix to the signal
        signal = np.concatenate((signal,cyclicPrefix))
        # Add the real valued symbol to the signal
        signal = np.concatenate((signal,tx_symbol))
        return signal


    def initDecode(self,signal,offset):
        """
        Starts a decoding process. The signal is the real valued received
        signal and the decoding start at the index specified by offset.
        """
        self.s = 1
        self.rxindex = offset
        self.signal = signal

    def decode(self, randomSeed = 1):
        """
        Decodes one symbol and returns a byte array of the
        data and the absolute values of the imaginary parts
        of the pilot tones. The smaller that value the better
        the symbol start detection, the reception and the jitter 
        (theoretically zero at perfect reception).
        """
        # Skip cyclic prefix
        self.rxindex = self.rxindex + self.nCyclic

        # The complex symbol in the time domain
        rx_symbol = np.zeros(self.nIFFT,dtype=complex)
        
        # Demodulate the signal with the Nyquist quadrature demodulator
        for a in range(self.nIFFT):
            realpart = self.s * self.signal[self.rxindex]
            self.rxindex = self.rxindex + 1
            imagpart = self.s * self.signal[self.rxindex]
            self.rxindex = self.rxindex + 1
            rx_symbol[a] = complex(realpart,imagpart)
            self.s = self.s * -1

        # Perform an FFT to get the frequency samples which code our signal as QPSK pairs
        isymbol = np.fft.fft(rx_symbol)

        # set the random number generator to the same value as in the transmitter so that
        # we have exactly the same sequence
        random.seed(randomSeed)

        # we start at frequency index k_start
        k = self.k_start

        # counter for the pilots
        pilot_counter = self.pilot_distance/2

        # the byte array storing the received data
        data = np.zeros(self.nData)

        # sum of the imaginary parts of the pilot tones
        imPilots = 0

        # we loop through one line in the image
        for x in range(self.nData):

            # decode one byte from 4 bytes in the FFT
            # we first create an array which contains the bits in separate rows
            bitstream = np.zeros(8)
            # loop through four bytes in the fft 
            for cnum in range(4):
                # test for pilots and ignore
                pilot_counter = pilot_counter - 1
                if pilot_counter == 0:
                    pilot_counter = self.pilot_distance
                    imPilots = imPilots + np.abs(np.imag(isymbol[k]))
                    k = k + 1
                    if not (k < self.nIFFT):
                        k = 0
                # first bit is in the real part of the coefficient
                bitstream[int(cnum*2)] = np.heaviside(np.real(isymbol[k]),0)
                # second bit is in the imag part of the coefficient
                bitstream[int(cnum*2+1)] = np.heaviside(np.imag(isymbol[k]),0)
                # get the next FFT coefficient
                k = k + 1
                # we wrap to positive frequencies
                if not (k < self.nIFFT):
                    k = 0

            # now let's assemble the bits into into a proper byte by
            # using bit-wise or
            databyte = 0

            # let's loop through the bits
            for bit in range(8):
                mask = 1 << bit
                if (bitstream[bit] > 0):
                    databyte = int(mask | int(databyte))

            # de-scramble the byte
            r = int(random.randint(0,255))
            databyte = databyte ^ r

            # store it in the image
            data[x] = databyte
        return data,imPilots


    def findSymbolStartIndex(self, signal, searchrangecoarse=None, searchrangefine = 25):
        """
        Finds the start of the symbol by 1st doing a cross correlation
        with the cyclic prefix and then it uses the pilot tones.
        Arguments: the real valued reception signal, the coarse searchrange for
        the cyclic prefix and the fine one for the pilots.
        Returns the cross correlation array from the cyclic prefix,
        the abs values of the imaginary parts of the pilots and the index
        of the symbol start relative to the signal.
        """
        # Set it to some default
        if not searchrangecoarse:
            searchrangecoarse = self.nIFFT*10
            
        # Let find the starting index with the cyclic prefix
        crosscorr = np.array([])
        for i in range(searchrangecoarse):
            s1 = signal[i:i+self.nCyclic]
            s2 = signal[i+self.nIFFT*2:i+self.nIFFT*2+self.nCyclic]
            cc = np.correlate(s1,s2)
            crosscorr = np.append(crosscorr,cc)

        pks,_ = scipy.signal.find_peaks(crosscorr,distance=self.nIFFT*2)
        o1 = pks[0]

        # Now let's fine tune it by looking at the imaginary parts
        imagpilots = np.array([])
        for i in range(o1-searchrangefine,o1+searchrangefine):
            self.initDecode(signal,i)
            _,im = self.decode()
            imagpilots = np.append(imagpilots,im)

        # Correct it with the pilots
        o2 = o1 + np.argmin(imagpilots) - searchrangefine
        return crosscorr,imagpilots,o2
