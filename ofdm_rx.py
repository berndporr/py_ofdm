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
import matplotlib.colors as mcolors
import ofdm_codec

# geometry of the expected image
ymax = 100
xmax= 256

# let's instantiate the OFDM codec
ofdm = ofdm_codec.OFDM()

# OFDM reception as audio file
fs,signal = wavfile.read('ofdm8000.wav')
# so that the search algorithm is happy
signal = np.append(signal,np.zeros(ofdm.nIFFT*2))

print("fs =",fs)

searchRangeForPilotPeak = 25
cc,sumofimag,offset = ofdm.findSymbolStartIndex(signal, searchrangefine = searchRangeForPilotPeak)

print("Symbol start sample index =",offset)

plt.subplot(131)
plt.title("Cross correlation to find the cyclic prefix")
plt.xlabel("Sample index")
plt.ylabel("Cross correlation")
plt.plot(cc)
plt.axvline(x=offset,color=mcolors.BASE_COLORS['g'])

plt.subplot(132)
plt.title("Sum of the abs of the imaginary parts of the pilots")
plt.xlabel("Relative sample index")
plt.ylabel("Sum(abs(imag(pilots)))")
plt.plot(np.arange(-searchRangeForPilotPeak,searchRangeForPilotPeak),sumofimag)

ofdm.initDecode(signal,offset)

# our image
rx_image = np.empty((ymax,xmax))

# loop for the y coordinate
for y in range(ymax):
    row,i = ofdm.decode()
    rx_image[y,:] = row

plt.subplot(133)
plt.title("Decoded image")
plt.imshow(rx_image, cmap='gray')
plt.show()
