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
import ofdm_codec
from PIL import Image

# expected image for size and ber determination
tx_im = Image.open('DC4_300x200.pgm')
tx_byte = np.array(tx_im, dtype='uint8')
Npixels = tx_im.size[1]*tx_im.size[0]

# let's initiate the OFDM codec
sym_slots, QAMorder = 48, 2
nbytes = sym_slots*QAMorder//8
ofdm = ofdm_codec.OFDM(pilotAmplitude = 1, nData=nbytes, mQAM=QAMorder)

# OFDM reception as audio file
samp_rate, base_signal = wav.read('ofdm44100.wav')
# append extra zeros so that the search algorithm is happy
base_signal = np.append(base_signal,np.zeros(ofdm.nIFFT*2))
complex_signal = ofdm.nyquistdemod(base_signal)

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
plt.show()

plt.figure()
plt.title("Sum of the square of the imaginary parts of the pilots")
plt.xlabel("Relative sample index")
plt.ylabel("Sum(imag(pilots)^2)")
plt.plot(np.arange(-searchRangeForPilotPeak,searchRangeForPilotPeak),sumofimag)
plt.show()
print("Symbol start sample index =",offset)

ofdm.initDecode(complex_signal,offset)
sig_sym = (Npixels-1+nbytes)//nbytes
            
rx_byte = np.empty(0, dtype='uint8')

for i in range(sig_sym):
    row = ofdm.decode()[0]
    rx_byte = np.append(rx_byte, np.uint8(row))

rx_im = rx_byte[0:Npixels].reshape(tx_im.size[1],tx_im.size[0])

plt.figure()
plt.title("Decoded image")
plt.imshow(rx_im, cmap='gray')
plt.show()

tx_bin = np.unpackbits(tx_byte.flatten())
rx_bin = np.unpackbits(rx_byte[0:Npixels])
ber = (rx_bin ^ tx_bin).sum()/tx_bin.size
print('ber= ', ber)


