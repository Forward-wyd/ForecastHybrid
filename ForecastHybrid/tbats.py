import rpy2.robjects as ro
import ForecastHybrid.ForecastCurve as ForecastCurve
import logging
import time
from rpy2.robjects import pandas2ri
import numpy as np


class tbats(ForecastCurve.ForecastCurve):
    def __init__(self, timeseries):
        super().__init__(timeseries)

    def myname(self):
        return "tbats"

    def fitR(self, **kwargs):
        ro.r("rm(list=ls())")
        self.setTimeSeries(period=1)
        command = self.setREnv("tbats", **kwargs)
        return self.fitKernel(command)

    def fitKernel(self, command):
        try:
            # Fit the time series
            self.dumpRCommandEnv(command)
            start_time = time.time()
            self.r_forecastobject = ro.r(command)
            logging.info("[R]tbats ran in {} sec".format(time.time() - start_time))
            ro.globalenv['r_forecastobject'] = self.r_forecastobject
            # Fitted points
            self.extractFit(indices={'fidx':1, 'nbands':2, 'lower':6, 'upper':5})
            logging.info("tbats fit successful")
        except:
            logging.debug(self.rtracebackerror())
            logging.warning("Running tbats without any arguments except for the time series")
            try:
                command = 'tbats(r_timeseries)'
                self.r_forecastobject = ro.r(command)
                ro.globalenv['r_forecastobject'] = self.r_forecastobject
                # Fitted points
                self.extractFit(indices={'fidx': 1, 'nbands': 2, 'lower': 6, 'upper': 5})
            except:
                logging.error("Failure to fit data with tbats")

        return self.fitted


    def fit(self, use_box_cox = None, use_trend = None, use_damped_trend = None,
            seasonal_periods = None, use_arma_errors = True,
            use_parallel = None, num_cores = 2, bc_lower = 0,
            bc_upper = 1, biasadj = False):
        aargs = self.convertArgsToR(use_box_cox, use_trend, use_damped_trend,
                                    seasonal_periods, use_arma_errors,
                                    use_parallel, num_cores, bc_lower,
                                    bc_upper, biasadj)
        return self.fitR(**aargs)


    def convertArgsToR(self, use_box_cox=None, use_trend=None, use_damped_trend=None,
            seasonal_periods=None, use_arma_errors=True,
            use_parallel=None, num_cores=2, bc_lower=0,
            bc_upper=1, biasadj=False):

        aargs = {}
        if use_parallel is None:
            if len(self.ts) > 1000: use_parallel = True
            else: use_parallel = False

        if use_box_cox is not None: aargs['use.box.cox'] = use_box_cox
        if use_trend is not None: aargs['use.trend'] = use_trend
        if use_damped_trend is not None: aargs['use.damped.trend'] = use_damped_trend
        aargs['use.arma.errors'] = use_arma_errors
        aargs['use.parallel'] = use_parallel
        aargs['num.cores'] = num_cores
        aargs['bc.lower'] = bc_lower
        aargs['bc.upper'] = bc_upper
        aargs['biasadj'] = biasadj
        return aargs

    def forecast(self, h=5, level=[80,95], fan=False, robust=False, lambdav=None,
                 findfrequency=False):
        # Make the forecast
        fcst = self.rforecast(h, level, fan, robust, lambdav, findfrequency)
        self.forecasted = self.extractRFcst(fcst, indices={'fidx':1, 'nbands':2, 'lower':6, 'upper':5})
        return self.forecasted

    def refit(self, ts):
        # Go ahead and reset the data and the model
        rdf = pandas2ri.py2ri(ts)
        # Create a call string setting variables as necessary
        arr = np.array(self.r_forecastobject)
        ro.r("library(forecast)")
        ro.globalenv['rts'] = rdf
        ro.globalenv['tbatsmod'] = self.r_forecastobject
        refitR = ro.r("tbats(y=rts, model=tbatsmod)")
        self.r_forecastobject = refitR
        ro.globalenv['r_forecastobject'] = refitR
        self.fitted = ro.r('fitted(r_forecastobject)')
        return self.fitted