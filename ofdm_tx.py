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

# Transmitter and test receiver on the same data
# Transmits a test grey scale image. Every horizontal line turns into a symbol

import cv2
import numpy as np
import scipy.io.wavfile as wavfile
import matplotlib.pyplot as plt
import ofdm_codec

# load the cheesy image
a = cv2.imread('greytee.png',cv2.IMREAD_GRAYSCALE)

# the number of lines in the image
ymax,xmax= np.shape(a)
print(xmax,ymax)

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

plt.figure(1)
plt.title("TX OFDM spectrum")
plt.xlabel("Normalised frequencies")
plt.ylabel("Freq-amplitudes")
plt.plot(np.linspace(0,1,len(signal)),np.abs(np.fft.fft(signal))/len(signal))

plt.figure(2)
plt.title("OFDM complex sprectrum")
plt.plot(np.abs(ofdm.spectrum))
#plt.show()

#######################################################################
# reception

# our image
rx_image = np.empty((ymax,xmax))

# Let's do a sanity check. We cheat here as we know the index of the symbol start.
ofdm.initDecode(signal,offset)

# loop for the y coordinate
for y in range(ymax):
    row,i = ofdm.decode()
    rx_image[y,:] = row

plt.figure(3)
plt.imshow(rx_image, cmap='gray')
plt.show()
