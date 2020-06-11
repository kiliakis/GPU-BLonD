# coding: utf-8
# Copyright 2017 CERN. This software is distributed under the
# terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file LICENCE.md.
# In applying this licence, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization or
# submit itself to any jurisdiction.
# Project website: http://blond.web.cern.ch/

"""Module containing the fundamental beam class with methods to compute beam
statistics

:Authors: **Danilo Quartullo**, **Helga Timko**, **ALexandre Lasheen**

"""

from __future__ import division
from builtins import object
import numpy as np
import itertools as itl
from scipy.constants import m_p, m_e, e, c
from ..trackers.utilities import is_in_separatrix
from ..utils import exceptions as blExcept
from ..utils import bmath as bm
from time import sleep

class Particle(object):

    def __init__(self, user_mass, user_charge):

        if user_mass > 0.:
            self.mass = float(user_mass)
            self.charge = float(user_charge)
        else:
            # MassError
            raise RuntimeError('ERROR: Particle mass not recognized!')


class Proton(Particle):

    def __init__(self):

        Particle.__init__(self, float(m_p*c**2/e), np.float(1))


class Electron(Particle):

    def __init__(self):
        self.mass = float(m_e*c**2/e)
        self.charge = float(-1)


class Beam(object):
    """Class containing the beam properties.
    This class containes the beam coordinates (dt, dE) and the beam properties.

    The beam coordinate 'dt' is defined as the particle arrival time to the RF
    station w.r.t. the reference time that is the sum of turns. The beam
    coordiate 'dE' is defined as the particle energy offset w.r.t. the
    energy of the synchronous particle.

    The class creates a beam with zero dt and dE, see distributions to match
    a beam with respect to the RF and intensity effects.

    Parameters
    ----------
    Ring : Ring
        Used to import different quantities such as the mass and the energy.
    n_macroparticles : int
        total number of macroparticles.
    intensity : float
        total intensity of the beam (in number of charge).

    Attributes
    ----------
    mass : float
        mass of the particle [eV].
    charge : int
        integer charge of the particle [e].
    beta : float
        relativistic velocity factor [].
    gamma : float
        relativistic mass factor [].
    energy : float
        energy of the synchronous particle [eV].
    momentum : float
        momentum of the synchronous particle [eV].
    dt : numpy_array, float
        beam arrival times with respect to synchronous time [s].
    dE : numpy_array, float
        beam energy offset with respect to the synchronous particle [eV].
    mean_dt : float
        average beam arrival time [s].
    mean_dE : float
        average beam energy offset [eV].
    sigma_dt : float
        standard deviation of beam arrival time [s].
    sigma_dE : float
        standard deviation of beam energy offset [eV].
    intensity : float
        total intensity of the beam in number of charges [].
    n_macroparticles : int
        total number of macroparticles in the beam [].
    ratio : float
        ratio intensity per macroparticle [].
    n_macroparticles_lost : int
        number of macro-particles marked as 'lost' [].
    id : numpy_array, int
        unique macro-particle ID number; zero if particle is 'lost'.

    See Also
    ---------
    distributions.matched_from_line_density:
        match a beam with a given bunch profile.
    distributions.matched_from_distribution_function:
        match a beam with a given distribution function in phase space.

    Examples
    --------
    >>> from input_parameters.ring import Ring
    >>> from beam.beam import Beam
    >>>
    >>> n_turns = 10
    >>> C = 100
    >>> eta = 0.03
    >>> momentum = 26e9
    >>> ring = Ring(n_turns, C, eta, momentum, 'proton')
    >>> n_macroparticle = 1e6
    >>> intensity = 1e11
    >>>
    >>> my_beam = Beam(ring, n_macroparticle, intensity)
    """

    def __init__(self, Ring, n_macroparticles, intensity):

        self.Particle = Ring.Particle
        self.beta = Ring.beta[0][0]
        self.gamma = Ring.gamma[0][0]
        self.energy = Ring.energy[0][0]
        self.momentum = Ring.momentum[0][0]
        self._dt = np.zeros([int(n_macroparticles)])
        self._dE = np.zeros([int(n_macroparticles)])
        self.mean_dt = 0.
        self.mean_dE = 0.
        self.sigma_dt = 0.
        self.sigma_dE = 0.
        self.intensity = float(intensity)
        self.n_macroparticles = int(n_macroparticles)
        self.ratio = self.intensity/self.n_macroparticles
        self.id = np.arange(1, self.n_macroparticles + 1, dtype=int)
        # For MPI
        self.n_total_macroparticles_lost = 0

        self.dev_beam_dt = None
        self.dev_beam_dE = None
        self.dev_id     = None


        self.gpu_valid = False
        self.cpu_valid = True

        self.total_transfers = 0


    def use_gpu(self):
        global drv,gpuarray,gb
        import blond.gpu.gpu_beam as gb
        from pycuda import gpuarray, driver as drv, tools
        import atexit      
        from blond.utils.bmath import gpu_num

        drv.init()
        drv.Device(gpu_num)

        gb.funcs_update(self)


    def cpu_validate(self):
        if (not self.cpu_valid):
            self._dt = self.dev_beam_dt.get()
            self._dE = self.dev_beam_dE.get()
            #self.id = self.dev_id.get()*self.id
            self.cpu_valid = True
            self.total_transfers += 1


    def gpu_validate(self):
        if (not self.gpu_valid):
            self.dev_beam_dE = gpuarray.to_gpu(self._dE)
            self.dev_beam_dt = gpuarray.to_gpu(self._dt)
            self.dev_id    = gpuarray.to_gpu((self.id !=0).astype(np.float64))
            self.gpu_valid = True


    @property
    def dt(self):
        self.cpu_validate()
        return self._dt


    @dt.setter
    def dt(self, value):
        self.cpu_valid = True
        self.gpu_valid = False
        self._dt = value


    @property
    def dE(self):
        self.cpu_validate()
        return self._dE


    @dE.setter
    def dE(self, value):
        self.cpu_valid = True
        self.gpu_valid = False
        self._dE = value


    @property
    def dev_dE(self):
        self.gpu_validate()
        return self.dev_beam_dE


    @dev_dE.setter
    def dev_dE(self, value):
        self.gpu_validate()
        self.cpu_valid = False
        self.dev_beam_dE = value


    @property
    def dev_dt(self):
        self.gpu_validate()
        return self.dev_beam_dt


    @dev_dt.setter
    def dev_dt(self, value):
        self.gpu_validate()
        self.cpu_valid = False
        self.dev_beam_dt = value

    @property
    def n_macroparticles_lost(self):
        '''Number of lost macro-particles, defined as @property.

        Returns
        -------
        n_macroparticles_lost : int
            number of macroparticles lost.

        '''
        if (bm.get_exec_mode()=='GPU'):
            return self.n_macroparticles - int(gpuarray.sum(self.dev_id).get())
        else:
            return len(np.where(self.id == 0)[0])

    @property
    def n_macroparticles_alive(self):
        '''Number of transmitted macro-particles, defined as @property.

        Returns
        -------
        n_macroparticles_alive : int
            number of macroparticles not lost.

        '''
        return self.n_macroparticles - self.n_macroparticles_lost


    def eliminate_lost_particles(self):
        """Eliminate lost particles from the beam coordinate arrays
        """
        indexalive = np.where(self.id == 0)[0]
        if len(indexalive) < self.n_macroparticles:
            self.dt = np.ascontiguousarray(self._beam.dt[indexalive])
            self.dE = np.ascontiguousarray(self._beam.dE[indexalive])
            self.n_macroparticles = len(self.beam.dt)
        else:
            # AllParticlesLost
            raise RuntimeError("ERROR in Beams: all particles lost and" +
                               " eliminated!")


    def statistics(self):
        '''
        Calculation of the mean and standard deviation of beam coordinates,
        as well as beam emittance using different definitions.
        Take no arguments, statistics stored in

        - mean_dt
        - mean_dE
        - sigma_dt
        - sigma_dE
        '''

        # Statistics only for particles that are not flagged as lost
        itemindex = np.where(self.id != 0)[0]
        self.mean_dt = np.mean(self.dt[itemindex])
        self.mean_dE = np.mean(self.dE[itemindex])
        self.sigma_dt = np.std(self.dt[itemindex])
        self.sigma_dE = np.std(self.dE[itemindex])

        # R.m.s. emittance in Gaussian approximation
        self.epsn_rms_l = np.pi*self.sigma_dE*self.sigma_dt  # in eVs


    def losses_separatrix(self, Ring, RFStation):
        '''Beam losses based on separatrix.

        Set to 0 all the particle's id not in the separatrix anymore.

        Parameters
        ----------
        Ring : Ring
            Used to call the function is_in_separatrix.
        RFStation : RFStation
            Used to call the function is_in_separatrix.
        '''

        itemindex = np.where(is_in_separatrix(Ring, RFStation, self,
                                              self.dt, self.dE) == False)[0]

        if itemindex.size != 0:
            self.id[itemindex] = 0
            self.gpu_valid = False

    def losses_longitudinal_cut(self, dt_min, dt_max):
        '''Beam losses based on longitudinal cuts.

        Set to 0 all the particle's id with dt not in the interval
        (dt_min, dt_max).

        Parameters
        ----------
        dt_min : float
            minimum dt.
        dt_max : float
            maximum dt.
        '''
        itemindex = np.where((self.dt - dt_min)*(dt_max - self.dt) < 0)[0]

        if itemindex.size != 0:
            self.id[itemindex] = 0


    def losses_energy_cut(self, dE_min, dE_max):
        '''Beam losses based on energy cuts, e.g. on collimators.

        Set to 0 all the particle's id with dE not in the interval (dE_min, dE_max).

        Parameters
        ----------
        dE_min : float
            minimum dE.
        dE_max : float
            maximum dE.
        '''

        itemindex = np.where((self.dE - dE_min)*(dE_max - self.dE) < 0)[0]

        if itemindex.size != 0:
            self.id[itemindex] = 0


    def losses_below_energy(self, dE_min):
        '''Beam losses based on lower energy cut.

        Set to 0 all the particle's id with dE below dE_min.

        Parameters
        ----------
        dE_min : float
            minimum dE.
        '''

        itemindex = np.where((self.dE - dE_min) < 0)[0]

        if itemindex.size != 0:
            self.id[itemindex] = 0


    def add_particles(self, new_particles):
        '''
        Method to add array of new particles to beam object
        New particles are given id numbers sequential from last id of this beam

        Parameters
        ----------
        new_particles : array-like
            (2, n) array of (dt, dE) for new particles
        '''

        try:
            new_dt = new_particles[0]
            newdE = new_particles[1]
            if len(new_dt) != len(newdE):
                raise blExcept.ParticleAdditionError(
                    "new_particles must have equal number of time and energy coordinates")
        except TypeError:
            raise blExcept.ParticleAdditionError(
                "new_particles shape must be (2, n)")

        nNew = len(new_dt)

        self.id = np.concatenate((self.id, np.arange(self.n_macroparticles + 1,
                                                     self.n_macroparticles
                                                     + nNew + 1, dtype=int)))
        self.n_macroparticles += nNew

        self.dt = np.concatenate((self.dt, new_dt))
        self.dE = np.concatenate((self.dE, newdE))


    def add_beam(self, other_beam):
        '''
        Method to add the particles from another beam to this beam
        New particles are given id numbers sequential from last id of this beam
        Particles with id == 0 keep id == 0 and are included in addition

        Parameters
        ----------
        other_beam : blond beam object
        '''

        if not isinstance(other_beam, type(self)):
            raise TypeError("add_beam method requires a beam object as input")

        self.dt = np.concatenate((self.dt, other_beam.dt))
        self.dE = np.concatenate((self.dE, other_beam.dE))

        counter = itl.count(self.n_macroparticles + 1)
        newids = np.zeros(other_beam.n_macroparticles)

        for i in range(other_beam.n_macroparticles):
            if other_beam.id[i]:
                newids[i] = next(counter)
            else:
                next(counter)

        self.id = np.concatenate((self.id, newids))
        self.n_macroparticles += other_beam.n_macroparticles


    def __iadd__(self, other):
        '''
        Initialisation of in place addition calls add_beam(other) if other
        is a blond beam object, calls add_particles(other) otherwise

        Parameters
        ----------
        other : blond beam object or (2, n) array
        '''

        if isinstance(other, type(self)):
            self.add_beam(other)
            return self
        else:
            self.add_particles(other)
            return self


    def split(self):
        from ..utils.mpi_config import worker
        
        if len(worker.indices) == 0 or worker.isMaster:
            start, size = worker.split(self.n_macroparticles)
            self.dt = self.dt[start: start + size]
            self.dE = self.dE[start: start + size]
            self.id = self.id[start: start + size]
            worker.indices['beam'] = {'start': start,
                                      'size': size,
                                      'stride': 1,
                                      'total_size': self.n_macroparticles}
            self.n_macroparticles = size


    def gather(self):
        from ..utils.mpi_config import worker

        total_size = worker.indices['beam']['total_size']
        self.dt = worker.gather(self.dt, total_size)
        self.dE = worker.gather(self.dE, total_size)
        self.id = worker.gather(self.id, total_size)
        self.n_macroparticles = total_size


    def gather_statistics(self, all=False):
        '''
        MPI ONLY ROUTINE: Gather beam statistics.
        Parameters
        ----------
        all : boolean
            if true, all workers will gather the beam stats.
            If false, only the master will get the beam stats.
        '''
        if not bm.mpiMode():
            raise RuntimeError(
                'ERROR: Cannot use this routine unless in MPI Mode')

        from ..utils.mpi_config import worker

        if all:
            temp = worker.allgather(np.array([self.mean_dt]))
            self.mean_dt = np.mean(temp)
            temp = worker.allgather(np.array([self.mean_dE]))
            self.mean_dE = np.mean(temp)
            temp = worker.allgather(np.array([self.n_macroparticles_lost]))
            self.n_total_macroparticles_lost = np.sum(temp)
        else:
            temp = worker.gather(np.array([self.mean_dt]))
            self.mean_dt = np.mean(temp)
            temp = worker.gather(np.array([self.mean_dE]))
            self.mean_dE = np.mean(temp)
            temp = worker.gather(np.array([self.n_macroparticles_lost]))
            self.n_total_macroparticles_lost = np.sum(temp)


    def gather_losses(self, all=False):
        '''
        MPI ONLY ROUTINE: Gather beam losses.
        Parameters
        ----------
        all : boolean
            if true, all workers will gather the beam stats.
            If false, only the master will get the beam stats.
        '''
        if not bm.mpiMode():
            raise RuntimeError(
                'ERROR: Cannot use this routine unless in MPI Mode')

        from ..utils.mpi_config import worker

        if all:
            temp = worker.allgather(np.array([self.n_macroparticles_lost]))
            self.n_total_macroparticles_lost = np.sum(temp)
        else:
            temp = worker.gather(np.array([self.n_macroparticles_lost]))
            self.n_total_macroparticles_lost = np.sum(temp)




