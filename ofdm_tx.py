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

#       using more than one pilots to eliminate ambiguities.

import cv2
import numpy as np
import random
import scipy.io.wavfile as wavfile
import matplotlib.pyplot as plt

# load the cheesy image
a = cv2.imread('greytee.png',cv2.IMREAD_GRAYSCALE)

# the number of lines in the image
ymax,xmax= np.shape(a)

# the plan is that we generate for every line of the image
# one symbol, thus, one IFFT

# our inverse FFT has 2048 frequencies
nIFFT = 2048

# the cyclic prefix is a 1/4 of the length of the symbol
nCyclic = int(nIFFT*2/4)

# distance between pilots
pilot_distance = 16

# amplitudes of the pilot carrier at the beginning
pilot_amplitude = 2

# to have some delay before it starts
offset = nIFFT*3

# total number of complex samples in the timedomain
nTotal = (nIFFT+nCyclic)*ymax+offset

# first k index used
k_start = int(nIFFT/2 + nIFFT/4 - nIFFT/pilot_distance/4)

ymin = 0
# ymax = 1


def ofdm_encode(signal,data):
    # create an empty spectrum with all complex frequency values set to zero
    spectrum = np.zeros(nIFFT,dtype=complex)

    # we start with a negative frequency and then 
    # work ourselves up to positive ones
    # we have 2048 frequency samples and 1024 frequencies we use for the
    # image
    k = k_start
    
    # set the random number generator to a known start value
    # will generate always the same sequence from this start value
    # We xor its value with the grey values from the image to
    # generate a pseudo random sequence which is called "engery dispersal".
    random.seed(1)
    
    # pilot signal, make it stronger than the payload data
    # so that it's easy to recognise
    # we can use it to fine tune the symbol start in the receiver
    # However, only one pilot won't be enough in a real receiver
    # because of its periodic nature. We need to scatter them
    # over the spectrum.
    
    # counter for the pilots
    pilot_counter = pilot_distance/2
    
    # we loop through one line in the image
    for x in range(xmax):

        # get the grey value
        greyvalue = int(data[x])
        # greyvalue = int(x % 255)
        # generate the random number
        r = int(random.randint(0,255))
        # xor the grey value with the random number
        greyvalue = int(greyvalue ^ r)

        # create the bitstream
        bitstream = np.zeros(8)
        for bit in range(8):
            m = 1 << bit
            testbit = m & greyvalue
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
                pilot_counter = pilot_distance;
                spectrum[k] = pilot_amplitude
                k = k + 1
                if not (k < nIFFT):
                    k = 0
            spectrum[k] = complex(bitstream[int(cnum*2)],
                                  bitstream[int(cnum*2+1)])
            # increase the frequency index
            k = k + 1
            # wrap to positive frequencies once we have reached the last index
            if not (k < nIFFT):
                k = 0

    # create one symbol by transforming our frequency samples into
    # complex timedomain samples
    complex_symbol = np.fft.ifft(spectrum);

    # create an empty real valued symbol with twice the samples
    # because we need to interleave real and complex values
    tx_symbol = np.zeros(len(complex_symbol)*2)

    # now we upsample at factor 2 and interleave
    # the I and Q signals
    # This is a digital quadrature modulator where we
    # interleave the complex signal c(n) as:
    # +Real(c(n)), +Imag(c(n)), -Real(c(n+1), -Imag(c(n+1))
    # and then repeat it until we have created our sequence
    # with twice the number of samples.
    s = 1;
    txindex = 0;
    for smpl in complex_symbol:
        tx_symbol[txindex] = s * np.real(smpl)
        txindex = txindex + 1
        tx_symbol[txindex] = s * np.imag(smpl)
        txindex = txindex + 1
        s = s * -1

    # generate cyclic prefix taken from the end of the signal
    # This is now twice the length because we have two times
    # more samples, effectively transmitting at twice the
    # sampling rate
    cyclicPrefix = tx_symbol[-nCyclic:]

    # add the cyclic prefix to the signal
    signal = np.concatenate((signal,cyclicPrefix));
    # add the real valued symbol to the signal
    signal = np.concatenate((signal,tx_symbol));
    return signal




# some dummy bytes before we start transmission
signal = np.zeros(offset)

# loop for the y coordinate, line by line
for y in range(ymin,ymax):
    # get a line from the image
    row = a[y,:]
    signal = ofdm_encode(signal,row)

# save it as a wav file to listen to
wavfile.write('ofdm8000.wav',8000,signal)


#######################################################################
# reception


# our image
rx_image = np.zeros((ymax,xmax))

# 4QAM/QPSK demodulator
# we split the signal again into real and imaginary parts
# In a real receiver the offset won't be known and had to be
# detected using the cyclic prefix and the pilot tones.
# However here we just assume we know the start and cheat.
s = 1
rxindex = offset

# loop for the y coordinate
for y in range(ymin,ymax):

    # skip cyclic prefix
    rxindex = rxindex + nCyclic

    rx_symbol = np.zeros(nIFFT,dtype=complex)
    # demodulate
    for a in range(nIFFT):
        realpart = s * signal[rxindex]
        rxindex = rxindex + 1;
        imagpart = s * signal[rxindex]
        rxindex = rxindex + 1
        rx_symbol[a] = complex(realpart,imagpart)
        s = s * -1

    # perform a FFT to get the frequency samples which code our signal as QPSK pairs
    isymbol = np.fft.fft(rx_symbol)

    # set the random number generator to the same value as in the transmitter so that
    # we have exactly the same sequence
    random.seed(1)

    # we start at frequency index k_start
    k = k_start;

    # counter for the pilots
    pilot_counter = pilot_distance/2

    # we loop through one line in the image
    for x in range(xmax):

        # decode one byte from 4 bytes in the FFT
        # we first create an array which contains the bits in separate rows
        bitstream = np.zeros(8)
        # loop through four bytes in the fft 
        for cnum in range(4):
            # test for pilots and ignore
            pilot_counter = pilot_counter - 1;
            if pilot_counter == 0:
                pilot_counter = pilot_distance;
                k = k + 1
                if not (k < nIFFT):
                    k = 0
            # first bit is in the real part of the coefficient
            bitstream[int(cnum*2)] = np.heaviside(np.real(isymbol[k]),0);
            # second bit is in the imag part of the coefficient
            bitstream[int(cnum*2+1)] = np.heaviside(np.imag(isymbol[k]),0);
            # get the next FFT coefficient
            k = k + 1
            # we wrap to positive frequencies
            if not (k < nIFFT):
                k = 0

        # now let's assemble the bits into into a proper byte by
        # using bit-wise or
        greyvalue = 0

        # let's loop through the bits
        for bit in range(8):
            mask = 1 << bit
            if (bitstream[bit] > 0):
                greyvalue = int(mask | int(greyvalue))

        # de-scramble the byte
        r = int(random.randint(0,255))
        greyvalue = greyvalue ^ r

        # store it in the image
        rx_image[y,x] = greyvalue

plt.imshow(rx_image, cmap='gray')
plt.show()
