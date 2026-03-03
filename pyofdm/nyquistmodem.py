import numpy as np

"""
Nyquist modulator and demodulator
"""

def mod(complex_signal):
    """
    Takes a complex input signal and converts it to a
    real valued signal twice the length.
    """
        
    # Create an empty real valued symbol with twice the samples
    # because we need to interleave real and complex values
    len_signal = len(complex_signal)
    base_signal = np.zeros(2*len_signal)
    
    # Now we upsample at factor 2 and interleave
    # the I and Q signals
    # This is a digital quadrature modulator where we
    # interleave the complex signal c(n) as:
    # +Real(c(n)), +Imag(c(n)), -Real(c(n+1), -Imag(c(n+1))
    # and then repeat it until we have created our sequence
    # with twice the number of samples.
    s = 1
    for smpl in range(len_signal):
        base_signal[2*smpl] = s * np.real(complex_signal[smpl])
        base_signal[2*smpl+1] = s * np.imag(complex_signal[smpl])
        s = s * -1
        
    return base_signal
    
def demod(base_signal):
    """
    Takes a real valued input signal and converts it to a
    complex valued signal half the length.
    """
        
    len_signal = len(base_signal)//2
    complex_signal = np.zeros(len_signal,dtype=complex)
    
    # Demodulate the signal with the Nyquist quadrature demodulator
    s = 1
    for smpl in range(len_signal):
        realpart = s * base_signal[2*smpl]
        imagpart = s * base_signal[2*smpl+1]
        complex_signal[smpl] = complex(realpart,imagpart)
        s = s * -1
        
    return complex_signal
