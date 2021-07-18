#	Copyright (C) 2020 Bernd Porr <mail@berndporr.me.uk>
#                 2021 David Hutchings <david.hutchings@glasgow.ac.uk>

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

import numpy as np
import matplotlib.pyplot as plt
import ofdm_codec

ofdm = ofdm_codec.OFDM(pilotAmplitude = 1,nData=12,mQAM=2)
signal = np.empty(0)

row = np.random.randint(256,size=12,dtype='uint8')
print(row)
signal = np.append(signal,ofdm.encode(row))

plt.figure()
plt.title("Symbol")
plt.plot(np.abs(signal))
plt.show()

# Show negative frequency components as negative, rather than upper half
myfreqs = (np.arange(ofdm.nIFFT)+ofdm.nIFFT//2)%ofdm.nIFFT-ofdm.nIFFT//2
fig, axs = plt.subplots(2,1)
axs[0].bar(myfreqs,ofdm.spectrum.real)
axs[0].axhline()
axs[0].set_title("Re")
axs[1].bar(myfreqs,ofdm.spectrum.imag)
axs[1].axhline()
axs[1].set_title("Im")
plt.show()

#######################################################################
# reception

# Let's add some dummy zero data to the signal

dummy = np.zeros(np.random.randint(low=1*ofdm.nIFFT,high=2*ofdm.nIFFT),dtype=complex)
signal = np.append(dummy, signal)
dummy = np.zeros(2*ofdm.nIFFT,dtype=complex)
signal = np.append(signal, dummy)

searchRangeForPilotPeak = 8
cc, sumofimag, offset = ofdm.findSymbolStartIndex(signal,
    searchrangefine = searchRangeForPilotPeak)

print("Symbol start sample index =",offset)

plt.figure()
plt.title("Cross correlation @ nIFFT to locate cyclic prefix")
plt.xlabel("Sample index")
plt.ylabel("Cross correlation @ nIFFT")
plt.plot(cc)
plt.axvline(x=offset,color='g')
plt.show()

plt.figure()
plt.title("Sum of the square of the imaginary parts of the pilots")
plt.xlabel("Relative sample index")
plt.ylabel("Sum(imag(pilots)^2)")
plt.plot(np.arange(-searchRangeForPilotPeak,searchRangeForPilotPeak),sumofimag)
plt.show()

ofdm.initDecode(signal,offset)

rx_enc = ofdm.decode()[0]
print(rx_enc)