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

from PIL import Image
import numpy as np
import scipy.io.wavfile as wav
import ofdm_codec

# load the image
tx_im = Image.open('DC4_300x200.pgm')
Npixels = tx_im.size[0]*tx_im.size[1]
tx_enc = np.array(tx_im, dtype="uint8").flatten()

sym_slots, QAMorder = 48, 2
nbytes = sym_slots*QAMorder//8
ofdm = ofdm_codec.OFDM(pilotAmplitude = 1, nData=nbytes, mQAM=QAMorder)
# add zeros to make data a whole number of symbols
tx_enc = np.append(tx_enc,np.zeros((sym_slots-tx_enc.size)%sym_slots, dtype="uint8"))

# Let's add some dummy zero data to the signal
complex_signal = np.zeros(np.random.randint(low=1*ofdm.nIFFT,high=2*ofdm.nIFFT),dtype=complex)

for i in range(0,tx_enc.size,nbytes):
    complex_signal = np.append(complex_signal,ofdm.encode(tx_enc[i:i+nbytes])) 

base_signal = ofdm.nyquistmod(complex_signal)
# save it as a wav file
wav.write('ofdm44100.wav',44100,base_signal)
