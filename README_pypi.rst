Python OFDM transmitter and receiver
====================================

Features: Nyquist quadrature modulator, pilot tones and cyclic prefix.

The module `codec` contains the class `OFDM` to encode, decode, modulate
demodualte and to find the start of the symbol.


OFDM class
----------

Constructor: `OFDM(nFreqSamples=64, pilotIndices=[-21, -7, 7, 21], pilotAmplitude=1, nData=12, fracCyclic=0.25, mQAM=2)`

     OFDM encoder and decoder. The data is encoded as QAM using the komm package. 
     Energy dispersal is done with a pre-seeded random number generator. Both pilot 
     tones and the cyclic prefix are added so that the start of the symbol can be 
     detected at the receiver. 
     The complex time series after the inverse Fourier Transform can be modulated 
     into a real valued stream with a Nyquist quadrature modulator for baseband. 
     On the receiver side the start of the symbol is detected by first doing a 
     coarse search with the cyclic prefix and then a precision alignment with the 
     pilots.
     
     nFreqSamples sets the number of frequency coefficients of the FFT. Pilot 
     tones are injected at pilotIndices. The real valued pilot amplitude is 
     pilotAmplitude. For transmission nData bytes are expected in an array. 
     The relative length of the Cyclic prefix is fracCyclic. 
     Number of QAM symbols = 2**mQAM, giving mQAM bits per QAM symbol. Average 
     power is normalised to unity. Default example correspond to 802.11a wifi 
     modulation.
     
`decode(self, randomSeed=1)`
     Decodes one symbol and returns a byte array of the
     data and the sum of the squares of the imaginary parts
     of the pilot tones. The smaller that value the better
     the symbol start detection, the reception and the jitter 
     (theoretically zero at perfect reception).
     
`encode(self, data, randomSeed=1)`
     Creates an OFDM symbol using QAM. 
     The signal is a complex valued numpy array where the
     encoded data-stream is appended. 
     The data is an array of bytes.
     The random seed sets the pseudo random number generator for the
     energy dispersal.

`findSymbolStartIndex(self, signal, searchrangecoarse=None, searchrangefine=25)`
     Finds the start of the symbol by 1st doing a cross correlation @nIFFT
     with the cyclic prefix and then it uses the pilot tones.
     Arguments: the real valued reception signal, the coarse searchrange for
     the cyclic prefix and the fine one for the pilots.
     Returns the cross correlation value array from the cyclic prefix,
     the squared values of the imaginary parts of the pilots and the 
     index of the symbol start relative to the signal.
     
`initDecode(self, signal, offset)`
     Starts a decoding process. The signal is the real valued received
     signal and the decoding start at the index specified by offset.


Periodic pilots
---------------

The module `codec` contains a function which generates evenly spaced pilots.
Call the function with the same values for `nData` and `mQAM`::

  setpilotindex(nData, mQAM, pilotspacing)
     

Nyquist modulator and demodulator
---------------------------------

These are in the module `nyquistmodem` which convert between complex
and real valued signals. The modulation is at nyquist rate which means
that its a quadrature modulator operating at a period of 4 samples for
the sine and cosine waves.
     
`nyquistdemod(base_signal)`
     Nyqist demodulator which turns the received real valued signal into a
     complex valued sequence for the OFDM decoder.
     
`nyquistmod(complex_signal)`
     Nyqist modulator which turns the complex valued base signal into a
     real valued sequence to be transmitted.


     

Examples
--------

See https://github.com/dchutchings/py_ofdm for examples.

