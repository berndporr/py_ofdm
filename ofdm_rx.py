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

# geometry of the expected image
ymax = 100
xmax= 256

# let's instantiate the OFDM codec
ofdm = ofdm_codec.OFDM()

# OFDM reception as audio file
fs,signal = wavfile.read('ofdm8000.wav')
print("fs =",fs)


# Let find the starting index with the cyclic prefix
crosscorr = np.array([])
# let's find the offset
for i in range(ofdm.nIFFT*5):
    s1 = signal[i:i+ofdm.nCyclic]
    s2 = signal[i+ofdm.nIFFT*2:i+ofdm.nIFFT*2+ofdm.nCyclic]
    cc = np.correlate(s1,s2)
    crosscorr = np.append(crosscorr,cc)

o1 = np.argmax(crosscorr)
print("1st guess for max index =",o1)
plt.figure(1)
plt.plot(crosscorr)

offset = o1

# Now let's fine tune it by looking at the imaginary parts

imagpilots = np.array([])
searchrange = 25
for i in range(o1-searchrange,o1+searchrange):
    ofdm.initDecode(signal,i)
    row,im = ofdm.decode(xmax)
    imagpilots = np.append(imagpilots,im)

o2 = o1 + np.argmin(imagpilots) - searchrange
print("Final offset corrected for errors =",o2)
plt.figure(2)
plt.plot(imagpilots)

ofdm.initDecode(signal,offset)

# our image
rx_image = np.empty((ymax,xmax))

# loop for the y coordinate
for y in range(ymax):
    row,i = ofdm.decode(xmax)
    rx_image[y,:] = row

plt.figure(3)
plt.imshow(rx_image, cmap='gray')
plt.show()
