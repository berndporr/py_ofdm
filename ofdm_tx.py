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
import scipy.io.wavfile as wavfile
import matplotlib.pyplot as plt
import ofdm_codec

# load the cheesy image
a = cv2.imread('greytee.png',cv2.IMREAD_GRAYSCALE)

# the number of lines in the image
ymax,xmax= np.shape(a)

ofdm = ofdm_codec.OFDM()

# to have some delay before it starts
offset = ofdm.nIFFT * 3

# some dummy bytes before we start transmission
signal = np.zeros(offset)

# loop for the y coordinate, line by line
for y in range(ymax):
    # get a line from the image
    row = a[y,:]
    signal = ofdm.encode(signal,row)

# save it as a wav file to listen to
wavfile.write('ofdm8000.wav',8000,signal)


#######################################################################
# reception
import random

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
for y in range(ymax):

    # skip cyclic prefix
    rxindex = rxindex + ofdm.nCyclic

    nIFFT = ofdm.nIFFT
    k_start = ofdm.k_start
    pilot_distance = ofdm.pilot_distance

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
