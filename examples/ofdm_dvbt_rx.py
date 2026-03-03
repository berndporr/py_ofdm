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
# Transmits a test grey scale image. 

import numpy as np
import scipy.io.wavfile as wav
import matplotlib.pyplot as plt
import pyofdm.codec
import pyofdm.nyquistmodem
from PIL import Image

# expected image for size and ber determination
tx_im = Image.open("Gilbert Scott Building 098.pgm")
tx_byte = np.array(tx_im, dtype='uint8')
Npixels = tx_im.size[1]*tx_im.size[0]

# We do DVB-T 2k
# https://www.etsi.org/deliver/etsi_en/300700_300799/300744/01.06.01_60/en_300744v010601p.pdf

# Number of total frequency camples
totalFreqSamples = 2048

# Number of useful data carriers / frequency samples
sym_slots = 1512

# QAM Order 
QAMorder = 2

# Total number of bytes per OFDM symbol
nbytes = sym_slots*QAMorder//8

# Distance of the evenly spaced pilots
distanceOfPilots = 12
pilotlist = pyofdm.codec.setpilotindex(nbytes,QAMorder,distanceOfPilots)

ofdm = pyofdm.codec.OFDM(pilotAmplitude = 16/9,
                         nData=nbytes,
                         pilotIndices = pilotlist,
                         mQAM = QAMorder,
                         nFreqSamples = totalFreqSamples)

# OFDM reception as audio file
samp_rate, base_signal = wav.read('ofdm44100.wav')
# Number of expected OFDM symbols in signal
sig_sym = (Npixels-1+nbytes)//nbytes
# append extra zeros so that the search algorithm is happy
base_signal = np.append(base_signal,np.zeros(ofdm.nIFFT*2))
complex_signal = pyofdm.nyquistmodem.demod(base_signal)

print("sample rate=",samp_rate)

searchRangeForPilotPeak = 8
cc, sumofimag, offset = ofdm.findSymbolStartIndex(complex_signal, 
    searchrangefine = searchRangeForPilotPeak)

plt.figure()
plt.title("Cross correlation @ nIFFT to locate cyclic prefix")
plt.xlabel("Sample index")
plt.ylabel("Cross correlation @ nIFFT")
plt.plot(cc)
plt.axvline(x=offset,color='g')

plt.figure()
plt.title("Sum of the square of the imaginary parts of the pilots")
plt.xlabel("Relative sample index")
plt.ylabel("Sum(imag(pilots)^2)")
plt.plot(np.arange(-searchRangeForPilotPeak,searchRangeForPilotPeak),sumofimag)
print("Symbol start sample index =",offset)

ofdm.initDecode(complex_signal,offset)
            
rx_byte = np.uint8([ofdm.decode()[0] for i in range(sig_sym)]).ravel()

rx_im = rx_byte[0:Npixels].reshape(tx_im.size[1],tx_im.size[0])

plt.figure()
plt.title("Decoded image")
plt.imshow(rx_im, cmap='gray')

tx_bin = np.unpackbits(tx_byte.ravel())
rx_bin = np.unpackbits(rx_byte[0:Npixels])
ber = (rx_bin ^ tx_bin).sum()/tx_bin.size
print('ber= ', ber)

plt.show()