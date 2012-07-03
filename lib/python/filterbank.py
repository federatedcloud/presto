"""
A module for reading filterbank files.

Patrick Lazarus, June 26, 2012
(Minor modification from file originally from June 6th, 2009)
"""

import sys
import warnings
import os.path
import numpy as np
import sigproc


DEBUG = False

def create_filterbank_file(outfn, header, spectra=None, verbose=False):
    """Write filterbank header and spectra to file.

        Input:
            outfn: The outfile filterbank file's name.
            header: A dictionary of header paramters and values.
            spectra: Spectra to write to file. (Default: don't write
                any spectra - i.e. write out header only)
            verbose: If True, be verbose (Default: be quiet)

        Output:
            None
    """
    outfile = open(outfn, 'wb')
    outfile.write(sigproc.addto_hdr("HEADER_START", None))
    for paramname in self.header.keys():
        if verbose:
            print "Writing header param (%s)" % paramname
        value = self.header[paramname]
        outfile.write(sigproc.addto_hdr(paramname, value))
    outfile.write(sigproc.addto_hdr("HEADER_END", None))
    if spectra:
        self.spectra.flatten().astype(self.dtype).tofile(outfile)
    outfile.close()


def get_dtype(nbits):
    """For a given number of bits per sample return
        a numpy-recognized dtype.

        Input:
            nbits: Number of bits per sample, as recorded in the filterbank
                file's header.

        Output:
            dtype: A numpy-recognized dtype string.
    """
    if nbits not in [32, 16, 8]:
        raise NotImplementedError("'filterbank.py' only supports " \
                                    "files with 8- or 16-bit " \
                                    "integers, or 32-bit floats " \
                                    "(nbits provided: %g)!" % nbits)
    if nbits == 32:
        dtype = 'float32'
    else:
        dtype = 'uint%d' % nbits
    return dtype


def read_header(filename, verbose=False):
    """Read the header of a filterbank file, and return
        a dictionary of header paramters and the header's
        size in bytes.

        Inputs:
            filename: Name of the filterbank file.
            verbose: If True, be verbose. (Default: be quiet)

        Outputs:
            header: A dictionary of header paramters.
            header_size: The size of the header in bytes.
    """
    header = {}
    filfile = open(filename, 'rb')
    filfile.seek(0)
    paramname = ""
    while (paramname != 'HEADER_END'):
        if verbose:
            print "File location: %d" % filfile.tell()
        paramname, val = sigproc.read_hdr_val(filfile, stdout=verbose)
        if verbose:
            print "Read param %s (value: %s)" % (paramname, val)
        if paramname not in ["HEADER_START", "HEADER_END"]:
            header[paramname] = val
    header_size = filfile.tell()
    filfile.close()
    return header, header_size


class FilterbankFile(object):
    def __init__(self, filfn, read_only=True):
        if not os.path.isfile(filfn):
            raise ValueError("ERROR: File does not exist!\n\t(%s)" % filfn)
        self.filename = filfn
        self.read_only = read_only
        self.header, self.header_size = read_header(self.filename)
        self.frequencies = self.fch1 + self.foff*np.arange(self.nchans)
        self.is_hifreq_first = (self.foff < 0)
        self.data_size = os.stat(self.filename)[6] - self.header_size
        self.bytes_per_spectrum = self.nchans*self.nbits / 8
        self.nspec = self.data_size / self.bytes_per_spectrum

        if self.data_size % self.bytes_per_spectrum:
            warnings.warn("Not an integer number of spectra in file.")

        mode = (self.read_only and 'r') or 'r+'
        self.spectra = np.memmap(self.filename, dtype=get_dtype(self.nbits), \
                                    mode=mode, offset=self.header_size, \
                                    shape=(self.nspec, self.nchans))

    def get_timeslice(self, start, stop):
        startbins = int(np.round(start/self.tsamp))
        stopbins = int(np.round(stop/self.tsamp))
        return self.get_spectra(startbins, stopbins)

    def get_spectra(self, start, stop):
        return self.spectra[start:stop]

    def __getattr__(self, name):
        if DEBUG:
            print "Fetching header param (%s)" % name
        return self.header[name]

    def print_header(self):
        """Print header parameters and values.
        """
        for param in sorted(self.header.keys()):
            if param in ("HEADER_START", "HEADER_END"):
                continue
            print "%s: %s" % (param, self.header[param])


def main():
    fil = FilterbankFile(sys.argv[1])
    fil.print_header()


if __name__ == '__main__':
    main()
