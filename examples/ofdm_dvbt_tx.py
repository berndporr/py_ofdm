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
import pyofdm.codec
import pyofdm.nyquistmodem
import matplotlib.pyplot as plt

# load the image
tx_im = Image.open("Gilbert Scott Building 098.pgm")
Npixels = tx_im.size[0]*tx_im.size[1]
tx_enc = np.array(tx_im, dtype="uint8").ravel()

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

# add zeros to make data a whole number of symbols
tx_enc = np.append(tx_enc,np.zeros(nbytes-tx_enc.size%nbytes, dtype="uint8"))

complex_signal = np.array([ofdm.encode(tx_enc[i:i+nbytes]) for i in range(0,tx_enc.size,nbytes)])

complex_signal = complex_signal.ravel()

rng1 = np.random.default_rng()

plt.figure()
plt.title('OFDM output')
plt.plot(complex_signal.real, label="real")
plt.plot(complex_signal.imag, label="imag")
plt.legend()

# plot single symbol spectrum with cyclic prefix removed
# the spectrum is shifted so that the zero frequency component is at the centre 
plt.figure()
plt.title("single symbol OFDM complex spectrum")
plt.xlabel("Normalised frequency")
plt.ylabel("Signal amplitude")
xlength = len(complex_signal)
plt.plot(np.abs(np.roll(np.fft.fft(complex_signal[-totalFreqSamples:]),
totalFreqSamples//2)/totalFreqSamples))

# Call Nyquist modulator. Note that number of samples is doubled, and output is real.
base_signal = pyofdm.nyquistmodem.mod(complex_signal)

# plot modulated signal spectrum (positive frequencies only)
xlength = len(complex_signal)
plt.figure()
plt.title("OFDM spectrum after Nyquist modulation")
plt.xlabel("Frequency/Nyquist frequency")
plt.ylabel("Signal amplitude")
plt.plot(np.linspace(0,2,xlength),1/xlength*np.abs(np.fft.fft(base_signal)[xlength:]))
plt.show()

# add some random length dummy data to the start of the signal here
# this example copies data from the end of the modulated signal
# this example selects a length between 1/4 and 1 times the raw OFDM symbol
# for Nyquist modulator, make this a multiple of 4 to ensure carrier phase syncronisation

npre = rng1.integers(low=totalFreqSamples//8,high=totalFreqSamples//2)*4
base_signal = np.concatenate((base_signal[-npre:],base_signal))

# save it as a wav file
wav.write('ofdm44100.wav',44100,base_signal)