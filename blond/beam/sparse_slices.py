# coding: utf-8
# Copyright 2016 CERN. This software is distributed under the
# terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file LICENCE.md.
# In applying this licence, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization or
# submit itself to any jurisdiction.
# Project website: http://blond.web.cern.ch/

'''
**Module to compute beam slicing for a sparse beam**
**Only valid for cases with constant revolution and RF frequencies**

:Authors: **Juan F. Esteban Mueller**
'''

from __future__ import division, print_function
from builtins import range, object
import numpy as np
import ctypes
# from ..setup_cpp import libblond
from .. import libblond
from ..utils import bmath as bm
from ..beam.profile import Profile, CutOptions



class SparseSlices(object):
    '''
    *This class instantiates a Slice object for each filled bucket according
    to the provided filling pattern. Each slice object will be of the size of 
    an RF bucket and will have the same number of slices.*
    '''
    
    def __init__(self, RFStation, Beam, n_slices, filling_pattern, tracker='C',
                 direct_slicing=False):
        
        #: *Import (reference) Beam*
        self.Beam = Beam
        
        #: *Import (reference) RFStation*
        self.RFParams = RFStation
        
        #: *Number of slices per bucket*
        self.n_slices = n_slices
        
        #: *Filling pattern as a boolean array where True (1) means filled
        # bucket*
        self.filling_pattern = filling_pattern
        
        # Bunch index for each filled bucket (-1 if empty). Only for C++ track
        self.bunch_indexes = np.cumsum(filling_pattern) * filling_pattern - 1
        
        #: *Number of buckets to be sliced*
        self.n_filled_buckets = int(np.sum(filling_pattern))
        
        # Pre-processing the slicing edges
        self.set_cuts()
        
        # Initialize individual slicing objects
        self.slices_array = []
        # Group n_macroparticles from all objects in a single array
        # (for C++ track).
        self.n_macroparticles_array = np.zeros((self.n_filled_buckets, 
                                                n_slices), dtype=bm.precision.real_t)
        # Group bin_centers from all objects in a single array (for impedance)
        self.bin_centers_array = np.zeros((self.n_filled_buckets, n_slices), dtype=bm.precision.real_t)
        for i in range(self.n_filled_buckets):
            # Only valid for cut_edges='edges'
                
            self.slices_array.append(Profile(Beam, CutOptions(cut_left= self.cut_left_array[i], 
                    cut_right=self.cut_right_array[i], n_slices=n_slices))   )
                 
            self.slices_array[i].n_macroparticles = \
                                               self.n_macroparticles_array[i,:]
            self.bin_centers_array[i,:] = self.slices_array[i].bin_centers
            self.slices_array[i].bin_centers = self.bin_centers_array[i,:]
        
        # Select the tracker
        if tracker is 'C':
            self.track = self._histrogram_C
        elif tracker is 'onebyone':
            self.track = self._histrogram_one_by_one
            
        # Track at initialisation
        if direct_slicing:
            self.track()


    def set_cuts(self):
        '''
        *Method to set the self.cut_left_array and self.cut_right_array 
        properties, with the limits being an RF period.
        This is done as a pre-processing.*
        '''
        # RF period
        Trf = 2.0 * np.pi / self.RFParams.omega_rf[0,self.RFParams.counter[0]]
        
        self.cut_left_array = np.zeros(self.n_filled_buckets, dtype=bm.precision.real_t)
        self.cut_right_array = np.zeros(self.n_filled_buckets, dtype=bm.precision.real_t)
        for i in range(self.n_filled_buckets):
            bucket_index = np.where(self.filling_pattern)[0][i]
            self.cut_left_array[i] = bucket_index * Trf
            self.cut_right_array[i] = (bucket_index + 1) * Trf


    def _histrogram_C(self):
        '''
        *Histrogram generated by calling an optimized C++ function that 
        calculates all the profile at once.*
        '''
               
        libblond.sparse_histogram(self.Beam.dt.ctypes.data_as(ctypes.c_void_p), 
                 self.n_macroparticles_array.ctypes.data_as(ctypes.c_void_p),
                 self.cut_left_array.ctypes.data_as(ctypes.c_void_p), 
                 self.cut_right_array.ctypes.data_as(ctypes.c_void_p),
                 self.bunch_indexes.ctypes.data_as(ctypes.c_void_p),
                 ctypes.c_int(self.n_slices), 
                 ctypes.c_int(self.n_filled_buckets), 
                 ctypes.c_int(self.Beam.n_macroparticles))
                 
                         
    def _histrogram_one_by_one(self):
        '''
        *Histrogram generated by calling the tack() method of each Profile 
        object*
        '''
        
        for i in range(self.n_filled_buckets):
            self.slices_array[i].track()
