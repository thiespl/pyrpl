import logging
logger = logging.getLogger(name=__name__)
from ...attributes import *
from ... import CurveDB
from ..test_base import TestPyrpl


class TestPidNaIqIir(TestPyrpl):
    def setup(self):
        self.extradelay = 0.6 * 8e-9  # no idea where this delay comes from
        # shortcuts
        self.pyrpl.na = self.pyrpl.networkanalyzer
        self.na = self.pyrpl.networkanalyzer

    def test_iirsimple_na_generator(self):
        # this test defines a simple transfer function that occupies 2
        # biquads in the iir filter. It then shifts the coefficients through
        # all available biquad spots and verifies that the transfer
        # function, as obtained from a na measurement, is in agreement with
        # the expected one. If something fails, the curves are saved to
        # CurveDB.
        extradelay = 0
        error_threshold = 0.25  # this value is mainly so high because of
        # ringing effects since we sweep over a resonance of the IIR filter
        # over a timescale comparable to its bandwidth. We should implement
        # another filter with very slow scan to test for model accuracy.
        # This test is only to confirm that all of the biquads are working.
        # setup na
        na = self.pyrpl.networkanalyzer
        iir = self.pyrpl.rp.iir
        na.setup(start_freq=3e3,
                 stop_freq=1e6,
                 points=301,
                 rbw=[500, 500],
                 avg=1,
                 amplitude=0.005,
                 input=iir,
                 output_direct='off',
                 logscale=True)

        # setup a simple iir transfer function
        zeros = [1e5j - 3e3]
        poles = [5e4j - 3e3]
        gain = 1.0
        iir.setup(zeros=zeros, poles=poles, gain=gain,
                  loops=35,
                  input=na.iq,
                  output_direct='off')

        for setting in range(iir._IIRSTAGES):
            iir.on = False
            # shift coefficients into next pair of biquads (each biquad has
            # 6 coefficients)
            iir.coefficients = np.roll(iir.coefficients, 6)
            iir.iirfilter._fcoefficients = iir.coefficients
            iir.on = True
            # self.na_assertion(setting=setting,
            #                  module=iir,
            #                  error_threshold=error_threshold,
            #                  extradelay=extradelay,
            #                  relative=True)
            yield self.na_assertion, \
                  setting, iir, error_threshold, extradelay, True

    def test_iircomplicated_na_generator(self):
        """
        This test defines a number of complicated IIR transfer functions
        and tests whether the NA response of the filter corresponds to what's
        expected.

        sorry for the ugly code - the test works though
        if there is a problem, no need to try to understand what the code
        does at first (rather read the iir module code):
        Just check the latest new CurveDB curves and for each failed test
        you should find a set of curves whose names indicate the failed
        test, whose parameters show the error between measurement and
        theory, and by comparing the measurement and theory curve you
        should be able to figure out what went wrong in the iir filter...
        """

        extradelay = 0
        error_threshold = 0.005  # mean relative error over the whole curve,
        # values will be redifined individually
        if self.r is None:
            return
        else:
            pyrpl = self.pyrpl
        # setup na
        na = self.pyrpl.networkanalyzer
        self.pyrpl.na = na
        iir = pyrpl.rp.iir

        params = []
        # setting 1
        z, p, g, loops = (np.array([-1510.0000001 - 10101.36145285j, -1510.0000001 +
                                    10101.36145285j,
                                    -2100.0000001 - 21828.90817759j, -2100.0000001 + 21828.90817759j,
                                    -1000.0000001 - 30156.73583005j, -1000.0000001 + 30156.73583005j,
                                    -1000.0000001 - 32063.2533145j, -1000.0000001 + 32063.2533145j,
                                    -6100.0000001 - 44654.63524562j, -6100.0000001 + 44654.63524562j]),
                          np.array([-151.00000010 - 16271.51686739j,
                                    -151.00000010 + 16271.51686739j, -51.00000010 - 22342.54324816j,
                                    -51.00000010 + 22342.54324816j, -10.00000010 - 30884.30406145j,
                                    -10.00000010 + 30884.30406145j, -41.00000010 - 32732.52445066j,
                                    -41.00000010 + 32732.52445066j, -51.00000010 - 46953.00496993j,
                                    -51.00000010 + 46953.00496993j]),
                          0.03,
                          400)
        naset = dict(start_freq=3e3,
                     stop_freq=50e3,
                     points=2001,
                     rbw=[500, 500],
                     avg=1,
                     amplitude=0.05,
                     input=iir,
                     output_direct='off',
                     logscale=True)
        error_threshold = 0.05  # [0.01, 0.03] works if avg=10 in naset
        params.append((z, p, g, loops, naset, "low_sampling", error_threshold,
                       ['final', 'continuous']))

        # setting 2 - minimum number of loops
        z = [1e5j - 3e3]
        p = [5e4j - 3e3]
        g = 0.5
        loops = None
        naset = dict(start_freq=3e3,
                     stop_freq=10e6,
                     points=1001,
                     rbw=[500, 500],
                     avg=1,
                     amplitude=0.05,
                     input=iir,
                     output_direct='off',
                     logscale=True)
        error_threshold = 0.05  # large because of phase error at high freq
        params.append((z, p, g, loops, naset, "loops_None", error_threshold,
                       ['final', 'continuous']))

        # setting 3 - complicated with well-defined loops (similar to 1)
        z, p, g = (
            np.array([-151.0000001 - 10101.36145285j, -151.0000001 +
                      10101.36145285j,
                      -210.0000001 - 21828.90817759j, -210.0000001 + 21828.90817759j,
                      -100.0000001 - 30156.73583005j, -100.0000001 + 30156.73583005j,
                      -100.0000001 - 32063.2533145j, -100.0000001 + 32063.2533145j,
                      -610.0000001 - 44654.63524562j, -610.0000001 + 44654.63524562j]),
            np.array([-151.00000010 - 16271.51686739j,
                      -151.00000010 + 16271.51686739j, -51.00000010 - 22342.54324816j,
                      -51.00000010 + 22342.54324816j, -50.00000010 - 30884.30406145j,
                      -50.00000010 + 30884.30406145j, -41.00000010 - 32732.52445066j,
                      -41.00000010 + 32732.52445066j, -51.00000010 - 46953.00496993j,
                      -51.00000010 + 46953.00496993j]),
            0.5)
        loops = 80
        naset = dict(start_freq=3e3,
                     stop_freq=50e3,
                     points=2501,
                     rbw=[1000, 1000],
                     avg=5,
                     amplitude=0.02,
                     input=iir,
                     output_direct='off',
                     logscale=True)
        error_threshold = 0.03
        params.append((z, p, g, loops, naset, "loops=80", error_threshold,
                       ['final', 'continuous']))

        # setting 4, medium complex transfer function
        z = [-4e4j - 300, +4e4j - 300, -2e5j - 3000, +2e5j - 3000]
        p = [-5e4j - 300, +5e4j - 300, -1e5j - 3000, +1e5j - 3000, -1e6j - 30000,
             +1e6j - 30000, -5e5]
        g = 1.0
        loops = None
        naset = dict(start_freq=1e4,
                     stop_freq=500e3,
                     points=301,
                     rbw=1000,
                     avg=1,
                     amplitude=0.01,
                     input='iir',
                     output_direct='off',
                     logscale=True)
        error_threshold = [0.03, 0.04]
        params.append((z, p, g, loops, naset, "4 - medium", error_threshold,
                       ['final', 'continuous']))

        # config na and iir and launch the na assertions
        for param in params[2:3]:
            z, p, g, loops, naset, name, maxerror, kinds = param
            self.pyrpl.na.setup(**naset)
            iir.setup(zeros=z, poles=p, gain=g, loops=loops, input=na.iq, output_direct='off')
            yield self.na_assertion, name, iir, maxerror, 0, True, True, kinds
            # default arguments of na_assertion:
            # setting, module, error_threshold=0.1,
            # extradelay=0, relative=False, mean=False, kinds=[]

    def na_assertion(self, setting, module, error_threshold=0.1,
                     extradelay=0, relative=False, mean=False, kinds=None):
        """
        helper function: tests if module.transfer_function is within
        error_threshold of the measured transfer function of the module
        """
        na = self.pyrpl.na
        na.input = module
        data = na.curve()
        f = na.data_x

        extrastring = str(setting)
        if not kinds:
            kinds = [None]
        for kind in kinds:
            if kind is None:
                theory = module.transfer_function(f, extradelay=extradelay)
                eth = error_threshold
            else:
                extrastring += '_' + kind + '_'
                theory = module.transfer_function(f, extradelay=extradelay,
                                                  kind=kind)
                try:
                    eth = error_threshold[kinds.index(kind)]
                except:
                    eth = error_threshold
            if relative:
                error = np.abs((data - theory) / theory)
            else:
                error = np.abs(data - theory)
            if mean:
                maxerror = np.mean(error)
            else:
                maxerror = np.max(error)
            if maxerror > eth:
                c = CurveDB.create(f, data, name='test_' + module.name
                                                 + '_' + extrastring
                                                 + '_na-failed-data')
                c.params["unittest_relative"] = relative
                c.params["unittest_maxerror"] = maxerror
                c.params["unittest_error_threshold"] = eth
                c.params["unittest_setting"] = setting
                c.save()
                c.add_child(CurveDB.create(f, theory,
                                           name='test_' + module.name + '_na-failed-theory'))
                c.add_child(CurveDB.create(f, error,
                                           name='test_' + module.name + '_na-failed-error'))
                assert False, (maxerror, setting)
