# Python OFDM transmitter and receiver

Features: Nyquist quadrature modulator, pilot tones and cyclic prefix.

## OFDM class

The module `ofdm_codec` contains methods to encode, decode
and to find the start of the symbol.

## Tx/Rx-Demo

A grey value image is transmitted encoded as OFDM.

### Transmission

Run `ofdm_ex1_tx.py`. This creates a wav file with the whole
image as OFDM encoded. You can listen to it!

### Reception

Run `ofdm_ex1_rx.py`. This then detects the start of the 1st symbol
1st with the cyclic prefix and then fine tunes it with the pilots.
Then it decodes the image.

### Various modifications and updates to initial version released by Bernd Porr 

- QAM modulation and demodulation is now performed using Roberto Nobrega komm library [pypi.org.project/komm](https://pypi.org.project/komm) which allows the modulation order to be extended to square modulations beyond QPSK/4QAM

- pilots can be inserted at any user selected indices and not just regularly spaced. DC subcarrier is unmodulated by default.

- default example corresponds to 802.11a standard, [rfmw.em.keysight.com//wireless/helpfiles/89600b/webhelp/subsystems/wlan-ofdm/Content/ofdm_basicprinciplesoverview.htm](https://rfmw.em.keysight.com//wireless/helpfiles/89600b/webhelp/subsystems/wlan-ofdm/Content/ofdm_basicprinciplesoverview.htm) with 48 data carriers and 4 pilot tones. In practice the carrier separation is 312.5kHz

- encode() and decode() operate with a complex signal, suitable for quadrature modulation of a carrier. nyquistmod() and nyquistdemod() convert between a complex signal and a double-sampled real signal for basedband modulation.

- crosscorrelation now finds just the cross-correlation value at a fixed sample (nIFFT) for a sliding window of width nCyclic

- imPilots now returns the sum of the squares of the imaginary part of the pilots

- rewritten examples:

1. ofdm_wifi.py 
self contained, generates one random symbol and shows the absolute value of the signal, the real and imaginary parts of the ofdm spectrum, the cross-correction value @nIFFT, the sum of the squares of the imaginary part of the pilots, and compares output bytes to input bytes.

2. ofdm_ex1_tx.py
reads in a pgm image 'DC4_300x200.pgm' and saves ofdm baseband to a WAV file 'ofdm44100.wav'

3. ofdm_ex1_rx.py
reads in ofdm baseband from a WAV file 'ofdm44100.wav', displays image and reports bit error ratio (ber).

