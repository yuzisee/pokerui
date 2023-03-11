#!/usr/bin/env python
# range_of_certainty_viz.py
"""Usage: $0 tracked_apps_history_*.csv"""

# https://stackoverflow.com/questions/4341746/how-do-i-disable-a-pylint-warning
#noqa: E266
# https://stackoverflow.com/questions/18444840/how-to-disable-a-pep8-error-in-a-specific-file

import collections
import csv
import enum
import itertools
import math
import sys

# import scipy.stats

# https://github.com/python-mode/python-mode/issues/699#issuecomment-286598349
# pylama:ignore=E201,E202


def scipy_stats_poisson_midpoint(n):
    """approx scipy.stats.poisson(n).median()"""
    # return scipy.stats.poisson(n).median()
    return (n + 1.0/3.0 - 0.02/n)
    # return n


def scipy_stats_norm_cdf(x):
    t = 1.0 / (1.0 + 0.33267 * x)
    a1 = 0.4361836
    a2 = -0.1201676
    a3 = 0.937298

    if x < 0:
        return 1.0 - (scipy_stats_norm_cdf(-x))
    else:
        return 1.0 - (scipy_stats_norm_pdf(x)) * t * (a1 + t * (a2 + t * a3))


def scipy_stats_vstpoisson_cdf(n, x):
    """approx scipy.stats.poisson(n).cdf(x)"""
    # return scipy.stats.poisson(n).cdf(x)

    # The variance stabilizing transformation is biased in a way that
    # encourages convergence at the tails (the derivative is never _flat_)
    mu = math.sqrt(n)
    std = 0.5
    # return scipy.stats.norm(0.0, 1.0).cdf((math.sqrt(max(x, 0.0)) - mu) / std)
    return scipy_stats_norm_cdf(((math.sqrt(max(x, 0.0))) - mu) / std)


def scipy_stats_vstpoisson_pmf(n, x):
    """approx scipy.stats.poisson(n).pmf(x)"""
    # print('{} {} = {} v {}'.format(n, x, scipy.stats.poisson(n).pmf(x), scipy_stats_poisson_cdf(n, x+0.5) - scipy_stats_poisson_cdf(n, x-0.5)))
    # return scipy.stats.poisson(n).pmf(round(x))

    return scipy_stats_vstpoisson_cdf(n, x+0.5) - scipy_stats_vstpoisson_cdf(n, x-0.5)


def scipy_stats_norm_pdf(x):
    # actual = scipy.stats.norm(0.0, 1.0).pdf(x)
    computed = math.exp(- 0.5 * x * x) / math.sqrt(2.0 * math.pi)
    # print(actual)
    # print(computed)
    # return actual
    return computed


def scipy_stats_norm_cdf_max(x):
    """http://www.jiem.org/index.php/jiem/article/viewFile/60/27

    doi:10.3926/jiem.2009.v2n1.p114-127
    A logistic approximation to the cumulative normal distribution

    """
    return 1.0 / (1.0 + math.exp(-x * (0.07056 * x * x + 1.5976)))


def scipy_stats_norm_cdf_mean(x):
    """https://en.wikipedia.org/wiki/Normal_distribution#Numerical_approximations_for_the_normal_CDF

    Zelen & Severo (1964) --> http://people.math.sfu.ca/~cbm/aands/page_932.htm

    """
    if x < 0:
        return 1 - scipy_stats_norm_cdf_mean(-x)
    t = 1 / (1 + 0.33267 * x)
    a1 = 0.4361836
    a2 = -0.1201676
    a3 = 0.937298
    return 1.0 - scipy_stats_norm_pdf(x) * t * (a1 + t * (a2 + t * a3))


class CountDataset(object):
    def __init__(self, n):
        self._n = n

    def poisson_process(self, guess_interval_width):
        # NOTE: Median = [lambda - ln(2), lambda + 1/3 - 0.02/lambda, lambda + 1/3)
        # interval_max_err = interval_width
        # confidence_pct = CDF(scipy.median + interval_width) - CDF(scipy.median - interval_width)
        interval_upper = scipy_stats_poisson_midpoint(self._n) + guess_interval_width
        interval_lower = scipy_stats_poisson_midpoint(self._n) - guess_interval_width
        # confidence_pct = scipy.stats.poisson(self._n).cdf(interval_upper) - scipy.stats.poisson(self._n).cdf(interval_lower)
        confidence_pct = scipy_stats_vstpoisson_cdf(self._n, interval_upper) - scipy_stats_vstpoisson_cdf(self._n, interval_lower)

        # confidence_pct := interval_max_err / lambda
        # fit_score = 1.0 - confidence_pct - interval_max_err / lambda
        #
        plus_minus = guess_interval_width

        # So that "90% statistically significant" means: you are within a +/- 5% confidence interval 90% of the time."
        # interval_width = 2.0 * plus_minus

        # So that "90% statistically significant" means: you are within a +/- 10% confidence interval 10% of the time."
        interval_max_err = plus_minus
        fit_score = 1.0 - confidence_pct - interval_max_err / self._n  # fit_score = 1.0 - confidence_pct - interval_width

        # d_fit_score = - d confidence_pct - d interval_max_err / lambda
        # d_interval_max_err = d_interval_width
        # d_confidence_pct = pdf(scipy.median + interval_width) d{scipy.median + interval_width) - pdf(scipy.median - interval_width) d{scipy.median - interval_width)
        #                  = pdf(scipy.median + interval_width) d{               interval_width) - pdf(scipy.median - interval_width) d{             - interval_width)
        #                  = pdf(scipy.median + interval_width) d{               interval_width) + pdf(scipy.median - interval_width) d{             + interval_width)
        #                  = [pdf(scipy.median + interval_width) + pdf(scipy.median - interval_width)] d_interval_width

        # d_fit_score                  = - ([pdf(scipy.median + interval_width) + pdf(scipy.median - interval_width)] d_interval_width) - d interval_width / lambda
        # d_fit_score_d_interval_width = - ([pdf(scipy.median + interval_width) + pdf(scipy.median - interval_width)] ) - 1.0 / lambda

        # d_confidence_pct = scipy.stats.poisson(self._n).pmf(interval_upper) + scipy.stats.poisson(self._n).pmf(interval_lower)
        d_confidence_pct = scipy_stats_vstpoisson_pmf(self._n, interval_upper) + scipy_stats_vstpoisson_pmf(self._n, interval_lower)
        # print(scipy.stats.poisson(mu=self._n).pmf(interval_lower))
        # print(scipy_stats_vstpoisson_pmf(n=self._n, x=interval_lower))
        # print(scipy.stats.poisson(mu=self._n).pmf(self._n))
        # print(scipy_stats_vstpoisson_pmf(n=self._n, x=self._n))
        # print(scipy.stats.poisson(mu=self._n).pmf(interval_upper))
        # print(scipy_stats_vstpoisson_pmf(n=self._n, x=interval_upper))

        d_fit_score = - d_confidence_pct - 1.0 / self._n

        # print('[{} + {}dw] Poisson Event n={} ranges {:0.1f} .. {:0.1f} @ {:0.0f}ile'.format(fit_score, d_fit_score, self._n, interval_lower, interval_upper, 100 * confidence_pct))

        # Newton's Method
        # f(z) + delta_z * f'(z) = 0
        #        delta_z         = -f(z) / f'(z)
        proposed_adjustment = - fit_score / d_fit_score
        # proposed = guess_interval_width + proposed_adjustment

        return (fit_score, guess_interval_width + proposed_adjustment)

        # TODO(from joseph): Verify agresti_coull output against known values
        # TODO(from joseph): Verify d_fit_score against small-delta computation
        # TODO(from joseph): Need approximations to ... scipy.stats.norm().cdf

        # https://en.wikipedia.org/wiki/Poisson_distribution#Related_distributions
        #  [DONE: RAW] --> Try the exact CDF via Scipy
        #  [NOTE: messy algebra] --> Try the: an accurate approximation to this exact interval has been proposed (based on the Wilson-Hilferty transformation):[41]
        #  [DONE: VAR_TR] --> Try the CDF via:  Variance-stabilizing transformation ... its square root is approximately normally distributed with expected value of about
        #  --> Try the: normal distribution is a good approximation if an appropriate continuity correction is performed
        #  [DONE: ANSCOMBE] Try the https://en.wikipedia.org/wiki/Anscombe_transform


def do_all_steps_poisson_events(a_impl, accuracy_decimal_points):
    # smallest_guess = 0.0
    # largest_guess = None
    # best_guess = math.sqrt(a_impl._n_s) * 0.5
    # best_guess = math.sqrt(a_impl._n_s) * 0.8948929172
    # best_guess = a_impl._n_s * 0.5166666667
    # best_guess = (math.pow(a_impl._n_s, 0.6504) + math.log(a_impl._n_s, 2.0)) * 0.533055627112
    # best_guess = (math.pow(a_impl._n_s, 0.618) + math.log(a_impl._n_s, 2.7)) * 0.681923512977
    ## best_guess = math.pow(a_impl._n_s, 0.575) * 1.03269558402
    # best_guess = math.pow(a_impl._n_s, 0.61) * 0.780202633034
    best_guess = math.pow(a_impl._n, 0.582)

    while True:
        a_fit_score, proposed_interval_width = a_impl.poisson_process(best_guess)

        if a_fit_score == 0:
            return (proposed_interval_width)
        else:
            correct_to_x_decimal_places = -math.log(math.fabs(proposed_interval_width - best_guess), 10) + math.log(a_impl._n, 10)
            if correct_to_x_decimal_places > accuracy_decimal_points:
                # We have converged
                return (proposed_interval_width)

            best_guess = proposed_interval_width

        # print('{} {} {}'.format(smallest_guess, best_guess, largest_guess))


StatisticallySignificant = collections.namedtuple('StatisticallySignificant', ['conservative', 'optimistic', 'nominal', 'display_str', 'confidence_pct', 'accuracy_decimal_points'])


def new_PoissonEvents(accuracy_decimal_points, n):
    """Computed bounds & results"""
    plus_minus = do_all_steps_poisson_events(CountDataset(n=n), accuracy_decimal_points)
    confidence_pct = 1.0 - plus_minus / n
    # print('>>> new_PoissonEvents  n={} --> {} +/- {}'.format(n, scipy_stats_poisson_midpoint(n), plus_minus))
    conservative_count = max(scipy_stats_poisson_midpoint(n) - plus_minus, 0.0)
    optimistic_count = (scipy_stats_poisson_midpoint(n) + plus_minus)
    display_str = '{:0.1f}..{:0.1f} ({})'.format(conservative_count, optimistic_count, n)
    return StatisticallySignificant(conservative=conservative_count, optimistic=optimistic_count, nominal=n, display_str=display_str, confidence_pct=confidence_pct, accuracy_decimal_points=accuracy_decimal_points)


class PercentageDataset(object):
    def __init__(self, n_s, n_f):
        self._n_s = n_s
        self._n_f = n_f
        self._n = n_s + n_f

    def print_basic_stats(self):
        pct = self._n_s / float(self._n)
        unbiased_pct = (self._n_s + 0.5) / (self._n + 1)
        print('Observed percentage: {:0.1f}% = {} out of {}'.format(pct*100, self._n_s, self._n))
        print('After Laplace Smoothing w/ Jeffreys Prior: {:0.1f}%'.format(unbiased_pct * 100))

    def add_s(self):
        self._n_s += 1
        self._n += 1

    def add_f(self):
        self._n_f += 1
        self._n += 1

    def n(self):
        return self._n

    def raw_pct(self):
        return self._n_s / self._n

    def fancy_stats(self, accuracy_decimal_points):
        return new_AgrestiCoull(accuracy_decimal_points=accuracy_decimal_points, n_s=self._n_s, n=self._n)

    def print_basic_stats(self):
        pct = self._n_s / float(self._n)
        unbiased_pct = (self._n_s + 0.5) / (self._n + 1)
        print('Observed percentage: {:0.1f}% = {} out of {}'.format(pct*100, self._n_s, self._n))
        print('After Laplace Smoothing w/ Jeffreys Prior: {:0.1f}%'.format(unbiased_pct * 100))

    # def agresti_coull(self, confidence_pct):
    #     """For a confidence interval of 90%, z = -normcdfinv(0.05) = 1.96
    #                                          z = -normcdfinv(0.5-0.5*conf)
    #     """
    #     vv = 1.0
    #     gaussian_impl = scipy.stats.norm(0.0, math.sqrt(vv))
    #     z = -gaussian_impl.ppf(0.5 - 0.5*confidence_pct)
    #     fit_score, proposed_z, center_pct = self.agresti_coull_z(z)

    #     proposed_confidence_pct = confidence_pct = 1 - 2 * gaussian_impl.cdf(-proposed_z)
    #     return (fit_score, proposed_confidence_pct, center_pct)

    def agresti_coull_z(self, z):
        # confidence_pct = 1 - 2 * scipy.stats.norm(0.0, 1.0).cdf(-z)
        confidence_pct = 1.0 - (2.0 * (scipy_stats_norm_cdf(-z)))
        # plus_minus = z * sqrt(p_hat * (1-p_hat) / n_hat)
        #            = z * sqrt(n_s_hat/n_hat * n_f_hat/n_hat / n_hat)
        #            = z * sqrt(n_s_hat * n_f_hat / n_hat^3)
        #     n_hat = (n + z^2)

        #     p_hat = (n_s + z^2 / 2) / n_hat
        #     n_s_hat = (n_s + z^2 / 2)
        #   1-p_hat = 1 - (n_s + z^2 / 2) / n_hat
        #           = (n_hat - (n_s + z^2 / 2)) / n_hat
        #           = (n + z^2 - n_s - z^2 / 2) / n_hat
        #           = (n_f + z^2 / 2 ) / n_hat
        #     n_f_hat = (n_f + z^2 / 2)
        n_s_hat = self._n_s + z*z/2
        n_f_hat = self._n_f + z*z/2
        n_hat = n_s_hat + n_f_hat
        plus_minus = z * math.sqrt(n_s_hat * n_f_hat / n_hat / n_hat / n_hat)
        # print('Agresti-Coull percentages {:0.1f}% .. {:0.1f}% @ {:0.0f}ile'.format(100 * ((n_s_hat / n_hat) - plus_minus), 100 * ((n_s_hat / n_hat) + plus_minus), 100 * confidence_pct))

        # So that "90% statistically significant" means: you are within a +/- 5% confidence interval 90% of the time."
        # interval_width = 2.0 * plus_minus

        # So that "90% statistically significant" means: you are within a +/- 10% confidence interval 10% of the time."
        interval_max_err = plus_minus
        fit_score = 1.0 - confidence_pct - interval_max_err  # fit_score = 1.0 - confidence_pct - interval_width

        # d_fit_score_d_z = - d confidence_pct - d interval_width
        # d confidence_pct = d { 1 - 2 * scipy.stats.norm().cdf(-z) }
        #                  =   {   - 2 * scipy.stats.norm().pdf(-z) * -1 }
        #                  =         2 * scipy.stats.norm().pdf(-z)
        # d interval_width = interval_width * d log interval_width
        # d log interval_width = d log { 2.0 * z * math.sqrt(n_s_hat * n_f_hat / n_hat / n_hat / n_hat) }
        #                      = d log { 2.0 * z * math.sqrt(n_s_hat * n_f_hat / n_hat / n_hat / n_hat) }
        #                      = d log { 2.0 * z * math.sqrt(n_s_hat) * math.sqrt(n_f_hat) * math.pow(n_hat, -1.5) }
        #                      = d { log 2.0 + log z + log math.sqrt(n_s_hat) + log math.sqrt(n_f_hat) + log math.pow(n_hat, -1.5) }
        #                      =                 1/z + d {  0.5 log (n_s_hat) +      0.5 log (n_f_hat) - 1.5 log (n_hat) }
        #                      =                 1/z +   {  0.5 (d n_s_hat) / n_s_hat + 0.5 (d n_f_hat) / n_f_hat - 1.5 (d n_hat) / n_hat }
        # d n_hat / dz = d/dz (n + z^2) = 2z
        # d n_s_hat / dz = d/dz (n_s + z^2/2) = z
        # d n_f_hat / dz = d/dz (n_f + z^2/2) = z
        # d log interval_width =                 1/z +   {  0.5 z / n_s_hat + 0.5 z / n_f_hat - 1.5 * 2z / n_hat }
        # d log interval_width =  1/z +  {  0.5 z / n_s_hat + 0.5 z / n_f_hat - 3.0 z / n_hat }
        d_log_interval_width = 1.0 / z + 0.5 * z / n_s_hat + 0.5 * z / n_f_hat - 3.0 * z / n_hat
        d_interval_max_err = interval_max_err * d_log_interval_width  # d_interval_width = interval_width * d_log_interval_width
        d_confidence_pct = 2.0 * scipy_stats_norm_pdf(-z)

        d_fit_score = - d_confidence_pct - d_interval_max_err  # d_fit_score = - d_confidence_pct - d_interval_width

        # Newton's Method
        # f(z) + delta_z * f'(z) = 0
        #        delta_z         = -f(z) / f'(z)
        proposed_z_adjustment = - fit_score / d_fit_score
        proposed_z = z + proposed_z_adjustment
        proposed_confidence_pct = confidence_pct + d_confidence_pct * proposed_z_adjustment

        return (fit_score, proposed_z, proposed_confidence_pct, n_s_hat / n_hat)

        # TODO(from joseph): Verify agresti_coull output against known values
        # TODO(from joseph): Verify d_fit_score against small-delta computation
        # TODO(from joseph): Need approximations to ... scipy.stats.norm().cdf
        # ---- You need to know z AND confidence_pct to calulate fit_score.

        #    If you have z,
        ##      https://www.omicsonline.org/open-access/a-new-approximation-to-standard-normal-distribution-function-2168-9679-1000351.php?aid=91676&view=mobile
        ##        2.232e-004 error MEAN
        ##      http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.654.1560&rep=rep1&type=pdf
        ##        ~3E-5 error MAX (for 10 terms)
        ##      http://mathworld.wolfram.com/NormalDistributionFunction.html
        ##        ~3E-5 error MAX (Bagby's approximation)
        ##      http://web2.uwindsor.ca/math/hlynka/zogheibhlynka.pdf
        ##        ~4.73E~5 error MEAN (Waissi and Rossin's approximation)
        ##        ~9E-4 error MAX (F3)
        ##        ~1.4E-3 error MAX (F4)
        ##        ~1.1E-2 error MAX (F5)
        ##      http://www.hrpub.org/download/20140305/MS7-13401470.pdf
        ##        ~1.9E-4 error MAX
        ##        ~5.5E-5 error MEAN
        ##        (for 4 terms)
        ##      https://en.wikipedia.org/wiki/Normal_distribution#Numerical_approximations_for_the_normal_CDF
        ##      https://en.wikipedia.org/wiki/Error_function#Approximation_with_elementary_functions
        ##      http://people.math.sfu.ca/~cbm/aands/page_932.htm
        ##        7.5E-8 error MEAN (for 6 terms)
        ##        1.15E-5 error MEAN (for 4 terms)
        ##      http://www.jiem.org/index.php/jiem/article/viewFile/60/27
        ##        ~1.4E-4 error MAX (for 2 terms)
        ##      http://m-hikari.com/ams/ams-2014/ams-85-88-2014/epureAMS85-88-2014.pdf
        ##        ~1.3E-4 error MAX (for a bunch of terms and kinda weird)
        ##      http://www.codeplanet.eu/files/download/accuratecumnorm.pdf
        ##        Hart 86 is perfect
        ##      https://github.com/scipy/scipy/blob/master/scipy/special/cephes/ndtr.c
        #       confidence_pct = 1 - 2 * scipy.stats.norm(0.0, 1.0).cdf(-z)

        #    If you have confidence_pct,
        ##      https://www.johndcook.com/blog/normal_cdf_inverse/
        ##        ~4E-4 error
        ##      https://stackedboxes.org/2017/05/01/acklams-normal-quantile-function/
        ##        ~1.15E-9 error
        ##      http://m-hikari.com/ams/ams-2014/ams-85-88-2014/epureAMS85-88-2014.pdf
        ##      http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.654.1560&rep=rep1&type=pdf
        ##        ~3E-4 error
        ##      https://github.com/scipy/scipy/blob/master/scipy/special/cephes/ndtri.c
        ##   ... but it will give you Z back so having the probit (quantile function) alone doesn't avoid having to do the other approximation above.
        #       z = -gaussian_impl.ppf(0.5 - 0.5*confidence_pct)


def do_one_step(a_impl, confidence_pct_impl):
    a_fit_score, proposed_confidence_pct, _ = a_impl.agresti_coull(confidence_pct_impl)
    if a_fit_score > 0.0:
        assert proposed_confidence_pct > confidence_pct_impl, "should be expanding"
        print('--> correct to {:0.1f} decimal places, please expand confidence/interval to {}'.format(-math.log(a_fit_score, 10), proposed_confidence_pct))
    if a_fit_score < 0.0:
        assert proposed_confidence_pct < confidence_pct_impl, "should be reducing"
        print('--> correct to {:0.1f} decimal places, please reduce confidence/interval to {}'.format(-math.log(-a_fit_score, 10), proposed_confidence_pct))
    print('')


def do_all_steps_agresti_coull(a_impl, accuracy_decimal_points):
    # best_guess = (1.0 + 0.689981619447) / 2.0  # 0.8449908097
    # z = 1.42205877113  # print(-scipy.stats.norm(0.0, 1.0).ppf(0.5 - 0.5*best_guess))
    best_guess_z = 1.42205877113
    while True:
        # a_fit_score, proposed_confidence_pct, center_pct = a_impl.agresti_coull(best_guess)
        a_fit_score, proposed_z, proposed_confidence_pct, center_pct = a_impl.agresti_coull_z(best_guess_z)
        correct_to_x_decimal_places = -math.log(math.fabs(a_fit_score), 10)
        if correct_to_x_decimal_places > accuracy_decimal_points:
            return (proposed_confidence_pct, center_pct)
        else:
            # best_guess = proposed_confidence_pct
            best_guess_z = proposed_z


def new_AgrestiCoull(accuracy_decimal_points, n_s, n):
    """Computed bounds & results"""
    if n == 0:
        return StatisticallySignificant(conservative=0.0, optimistic=1.0, nominal=0.5, display_str='n/a', confidence_pct=0, accuracy_decimal_points=0)
    else:
        n_f = n - n_s
        confidence_pct, center_pct = do_all_steps_agresti_coull(PercentageDataset(n_s=n_s, n_f=n_f), accuracy_decimal_points)
        plus_minus = 1.0 - confidence_pct
        # print('>>> new_AgrestiCoull  {} {} --> {} +/- {}'.format(n_s, n_f, center_pct, plus_minus))
        conservative_pct = max(center_pct - plus_minus, 0.0)
        optimistic_pct = min(center_pct + plus_minus, 1.0)
        display_str = '{:0.2f}..{:0.2f} ({}/{})'.format(conservative_pct, optimistic_pct, n_s, n)
        return StatisticallySignificant(conservative=conservative_pct, optimistic=optimistic_pct, nominal=(float(n_s) / float(n_s + n_f)), display_str=display_str, confidence_pct=confidence_pct, accuracy_decimal_points=accuracy_decimal_points)


def check_outlier(a, b):
    """Compare two AgrestiCoull objects

       Returns:
         (string) Either '        ' or 'notable ' or 'OUTLIER!' depending on the level of separation
    """
    if a.conservative > b.optimistic:
        return 'OUTLIER!'
    if a.optimistic < b.conservative:
        return 'OUTLIER!'

    if (a.nominal < b.conservative) and (a.optimistic < b.nominal):
        return ' notable'
    if (b.nominal < a.conservative) and (b.optimistic < a.nominal):
        return ' notable'

    return '        '


# ====================================================


EARLY_STAGE = {
    'Pre Funding': True,
    'Raised Seed': True,
    'Raised A': False,
    'Raised B': False,
    'Raised C': False,
}

GOT_INTERVIEWED = {
    'application': False,
    'round_1': True,
    'round_2': True,
    'round_rc': True,
    'reference_check': True,
    'StartX': True,
}

IS_URM_ETHNICITY = {
    'Latinx': True,
    'African American': True,
    'Native American': True,
    'Native Hawaiian / Pacific Islander': True,
    'Middle Eastern / North African': True,

    'White': False,
    'East Asian': False,
    # https://secure.helpscout.net/conversation/1777571589/70877
    # https://secure.helpscout.net/conversation/1778607501/70979/
    'South Asian': False,
    'Southeast Asian': False,
    # OLD: https://docs.google.com/document/d/1onXS2Ls1-HbnYZIXizQxDxqr8Qy62JyJUeRNEtaXYoA/edit#bookmark=id.eqjuhba8w8lo
    'Asian': False,
    'Latino/a': True,
    'Other Hispanic': True,
}

MIGRATE_ETHNICITY = {
    'Latino/a': 'Latinx',
    'Other Hispanic': 'Latinx',
}


def session_integer(session_str):
    # """Convert 'Summer 2012' to 201250 so that it's easier to sort, etc."""
    # a, b = session_str.strip().split()
    # return int(b) * 100 + {'Spring': 25, 'Summer': 50, 'Fall': 75}[a]
    """Convert '2012.75 StartX (F12) to 201275 so that it's easier to sort, etc."""
    # print(session_str)
    return int(100 * float(session_str.strip().split()[0]))


def session_name(session_int):
    session_year = int(session_int / 100)
    if session_int - session_year * 100 == 25:
        return 'Spring {}'.format(session_year)
    if session_int - session_year * 100 == 50:
        return 'Summer {}'.format(session_year)
    if session_int - session_year * 100 == 75:
        return 'Fall {}'.format(session_year)
    return repr(session_int) + ' ' + repr(session_year)  # To help debug in case of problems.


def is_series_a_plus(stage_funding):
    return (len(stage_funding.strip().split()) == 2) and (stage_funding.strip().split()[0] == 'Raised') and (len(stage_funding.strip().split()[1]) == 1) and (stage_funding.strip().split()[1].upper() == stage_funding.strip().split()[1])


def clean_data_impl(all_data):
    """Remove invalid data (not all fields populated, spam applications, etc."""
    result = []
    for r in all_data:
        if r['cohort'].startswith('Testing '):
            continue

        if r['is_complete'] == 'false':
            continue

        if r['is_spam'] == 'true':
            continue

        if r['id'] in frozenset(['10517', '10518', '10519']):
            # These were some hacky incomplete application stuffed into the system just so they could schedule an interview...?
            continue

        if r['id'] in frozenset(['10812']):
            # This is an "add a founder" applicant who was forced into the system with incomplete founder apps...
            continue

        session = session_integer(r['cohort'])

        if session < 201650:
            # Didn't have "stage_funding" before F15
            # Didn't have "ethnicity" before S16
            continue

        result.append(r)

    return result


def acceptance_rejection_data():
    Applicants = collections.namedtuple('Applicants', ['accepted', 'rejected'])
    return collections.defaultdict(lambda: Applicants(accepted=list(), rejected=list()))


def filter_ix_experienced(x):
    ### Based on https://github.com/StartXstaff/startx-web/blob/1ef6806f6708bee1a4c03f8cb3c52592ccb60d7d/app/models/application.rb#L679
    if (x['has_professor'] == 'true') or (x['program'] == 'professor_in_residence'):
        return True

    if x['program'].endswith('_industry'):
        return True

    if x['program'].endswith('_serial'):
        return True

    if is_series_a_plus(x['stage_funding']):
        return True

    return False


def filter_has_urm_ethnicity(x):
    return x['ethnicities'].strip() and (any(IS_URM_ETHNICITY[a.strip()] for a in x['ethnicities'].split('|')))


def filter_has_urm_gender(x):
    return not all((a.strip() == 'Male') for a in x['genders'].split('|'))


def filter_demographic_data(clean_data, demographic_filters, success_criteria, subset_criteria):
    """Filter the data to count demographics stats. This is used to determine & measure bias among different groups."""
    # This loop initializes and populates demographic_data[] by session
    # keys are session, values are lists of applicants
    demographic_data = acceptance_rejection_data()
    for r in clean_data:
        session = session_integer(r['cohort'])

        if not subset_criteria(r):
            # For now, we are looking for bias in our INTERVIEW process.
            continue

        new_entry = {}
        for demographic_name, demographic_criteria in demographic_filters.items():  # TODO(from joseph): Python2 support prefers iteritems or viewitems?
            try:
                new_entry[demographic_name] = demographic_criteria(r)
            except KeyError as e:
                sys.stderr.write(repr(e) + ' ERROR: ' + repr(r))
                sys.stderr.write('\n')
                sys.stderr.write("Please check the data to see if it's suspicious. If there is no bug in the code, consider marking these ids in clean_data_impl")
                sys.stderr.write('\n')
                raise
        # new_entry = {demographic_name, demographic_criteria(r)}  # 'has_urm_ethnicity': has_urm_ethnicity, 'has_urm_gender': not is_all_male}

    print('  ' + title_str)
    print('  TARGET  {}..{} ({}/{})'.format(overall_data.conservative_pct, overall_data.optimistic_pct, overall_data.n_s, overall_data.n))

    for category_str, comp_result in zip(iter_order, results):
        is_outlier = check_outlier(per_category_data[category_str], comp_result)

        print('  {} {}..{} ({}/{})'.format(category_str + ' ' + is_outlier, per_category_data[category_str].conservative_pct, per_category_data[category_str].optimistic_pct, per_category_data[category_str].n_s, per_category_data[category_str].n))

def report_pipeline_demographics(demographic_data, clean_data, str_prefix):

    categories = set()
    for y in sorted(demographic_data.keys()):
        candidates = demographic_data[y]

    """Spot checks
    a = Dataset(n_s=3, n_f=5)
    a.print_basic_stats()
    do_one_step(a, 0.9)
    do_one_step(a, 0.76493165631)
    do_one_step(a, 0.797260633123)
    do_one_step(a, 0.79864299296)
    # do_one_step(a, 0.67785)

    print('VERIFY')
    # https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm
    a = Dataset(n_s=4, n_f=16)
    a.print_basic_stats()
    a.agresti_coull(0.9)
        print('')
        print(' === {}PIPELINE HEALTH for {} === '.format(str_prefix, c))

        total_n =     sum(len(            candidates.accepted         ) for candidates in demographic_data.values())
        total_n_s   = sum(len([x for x in candidates.accepted if x[c]]) for candidates in demographic_data.values())
        overall_n_s = total_n_s / float(len(demographic_data.values()))

        overall_count = new_PoissonEvents(accuracy_decimal_points=3, n=overall_n_s)
        overall_rate = new_AgrestiCoull(accuracy_decimal_points=3, n_s=total_n_s, n=total_n)
        print('  AVERAGE: {}'.format(overall_count.display_str))

        for y in sorted(demographic_data.keys()):
            candidates = demographic_data[y]

            n_s = len([x for x in candidates.accepted if x[c]])
            n_f = len([x for x in candidates.rejected if x[c]])
            assert n_f == 0, 'This is a pipeline test, so the "success criteria" is True for all rows.'

            if n_s > 0:
                y_count = new_PoissonEvents(accuracy_decimal_points=3, n=n_s)
                a.print_basic_stats()
    print('{} {} {}'.format(check_outlier(y_count, overall_count), y_count.display_str, session_name(y)))
            else:
                print('     (n/a)            -- {}'.format(session_name(y)))
        print('')
        print('  OVERALL: {}'.format(overall_rate.display_str))

        for y in sorted(demographic_data.keys()):
            candidates = demographic_data[y]

            n_s = len([x for x in candidates.accepted if x[c]])
            baseline_n = len(     candidates.accepted )
            assert len(candidates.rejected) == 0, 'This is a pipeline test, so the "success criteria" is True for all rows.'

            y_rate = new_AgrestiCoull(accuracy_decimal_points=3, n_s=n_s, n=baseline_n)

            print('  {} {} {}'.format(check_outlier(y_rate, overall_rate), y_rate.display_str, session_name(y)))


def print_demographic_data(overall_s, overall_f, demographic_s, demographic_f, category_str):
    baseline_s = overall_s - demographic_s
    baseline_f = overall_f - demographic_f

    experiment_group = new_AgrestiCoull(accuracy_decimal_points=3, n_s=demographic_s, n=(demographic_s+demographic_f))
    control_group = new_AgrestiCoull(accuracy_decimal_points=3, n_s=baseline_s, n=(baseline_s+baseline_f))

    print('  {} {} {}'.format(check_outlier(experiment_group, control_group), experiment_group.display_str, category_str))


def report_demographic_data(demographic_data, title_str):
    """Look for demographic bias for a given subset (subset_criteria), and defining success using success_criteria"""
    #
    #    Demographic data (Post-seed or earlier // interviewed only?)
    #      Med
    #      URM ethnicity
    #      Gender
    #      TODO(Social Science)

    all_categories = set()

    # Show statistics
    for y in sorted(demographic_data.keys()):
        candidates = demographic_data[y]

        print(' === BIAS DETECTION for {} {} === '.format(session_name(y), title_str))

        categories = frozenset.union(frozenset(itertools.chain(*[x.keys() for x in candidates.accepted])), frozenset(itertools.chain(*[x.keys() for x in candidates.rejected])))
        all_categories.update(categories)

        overall_s = len([x for x in candidates.accepted])
        overall_f = len([x for x in candidates.rejected])

        overall_group = new_AgrestiCoull(accuracy_decimal_points=3, n_s=overall_s, n=(overall_s+overall_f))
        a.print_basic_stats()
    print('TARGET: {}'.format(overall_group.display_str))

        for c in categories:
            n_s = len([x for x in candidates.accepted if x[c]])
            n_f = len([x for x in candidates.rejected if x[c]])

            # baseline_s = len([x for x in candidates.accepted if not x[c]])
            # baseline_f = len([x for x in candidates.rejected if not x[c]])

            print_demographic_data(overall_s, overall_f, n_s, n_f, c)
    print('')
    print(' === BIAS DETECTION for all data {} === '.format(title_str))

    overall_s = sum(len([x for x in candidates.accepted      ]) for candidates in demographic_data.values())
    overall_f = sum(len([x for x in candidates.rejected      ]) for candidates in demographic_data.values())
    overall_group = new_AgrestiCoull(accuracy_decimal_points=3, n_s=overall_s, n=(overall_s+overall_f))
    print('  TARGET: {}'.format(overall_group.display_str))

    for c in all_categories:
        n_s = sum(len([x for x in candidates.accepted if x[c]]) for candidates in demographic_data.values())
        n_f = sum(len([x for x in candidates.rejected if x[c]]) for candidates in demographic_data.values())
        print_demographic_data(overall_s, overall_f, n_s, n_f, c)


    a = Dataset(n_s=3, n_f=5)
    a.print_basic_stats()
    print('Accurate to {}+ decimal points: confidence_pct = {}'.format(ACCURACY_DECIMAL_POINTS, do_all_steps(a, ACCURACY_DECIMAL_POINTS)[0]))
        print('')
        print(' === OUTLIER DETECTION FOR ({}) {} === '.format(title_str.strip(), divider_str.strip()))

        # TODO(from joseph): More extreme outlier detection can take the lowest
        # conservative & highest optimistic and see if they mismatch.

        print('   TARGET: {}'.format(overall_group.display_str))
        for y in sorted(demographic_data.keys()):
            c = demographic_data[y]

            n_s = len(c.accepted)
            n_f = len(c.rejected)
            y_group = new_AgrestiCoull(accuracy_decimal_points=3, n_s=n_s, n=(n_s+n_f))

    a = Dataset(n_s=7, n_f=(42-7))
    a.print_basic_stats()
    print('Accurate to {}+ decimal points: confidence_pct = {}'.format(ACCURACY_DECIMAL_POINTS, do_all_steps(a, ACCURACY_DECIMAL_POINTS)[0]))
        print('')
        print('  AVERAGE: {}'.format(overall_count.display_str))
        for y in sorted(demographic_data.keys()):
            c = demographic_data[y]

            n_s = len(c.accepted)
            n_f = len(c.rejected)
            y_count = new_PoissonEvents(accuracy_decimal_points=3, n=(n_s+n_f))

            print('  {} {} {}'.format(check_outlier(y_count, overall_count), y_count.display_str, session_name(y)))


def report_timeseries_data(clean_data, divider_labels, iteration_mode):
    """iteration_mode is either 'exhaustive_complementary' or 'nested_compound'

    Example of exhaustive_complementary
    #    Timeseries data (only allowing for separation of things that SHOULD
    #    have a different acceptance rate -- which means we can only detect
    #    anomalies across time)
    #      applied before
    #      fresh applicant
    #       +- affiliated student teams
    #       +- remaining (mostly likely non-student) teams
    #         +- Series A+
    #         +- Post-seed or earlier


    a = Dataset(n_s=29, n_f=49)
    a.print_basic_stats()
    print('Accurate to {}+ decimal points: confidence_pct = {}'.format(ACCURACY_DECIMAL_POINTS, do_all_steps(a, ACCURACY_DECIMAL_POINTS)[0]))
    print('')

    a = Dataset(n_s=58/2, n_f=58/2)
    a.print_basic_stats()
    print('Accurate to {}+ decimal points: confidence_pct = {}'.format(ACCURACY_DECIMAL_POINTS, do_all_steps(a, ACCURACY_DECIMAL_POINTS)[0]))
    print('')

    a = Dataset(n_s=302/2, n_f=302/2)
    a.print_basic_stats()
    print('Accurate to {}+ decimal points: confidence_pct = {}'.format(ACCURACY_DECIMAL_POINTS, do_all_steps(a, ACCURACY_DECIMAL_POINTS)[0]))
    print('')
    print_outliers(divider_strs, overall_timeseries_data, 'END-TO-END')


def incr_accepted(pct_dat):
    pct_dat.add_s()


def incr_rejected(pct_dat):
    pct_dat.add_f()


    report_outliers(
      '=== VFPs (invite-only) ===',
      {
        "2017.75": new_AgrestiCoull(accuracy_decimal_points=3, n_s=6, n=(216-154)),
        "2018.25": new_AgrestiCoull(accuracy_decimal_points=3, n_s=3, n=(231-197)),
        "2018.50": new_AgrestiCoull(accuracy_decimal_points=3, n_s=8, n=(246-200)),
        "2018.75": new_AgrestiCoull(accuracy_decimal_points=3, n_s=3, n=(163-138)),
      }
    )
    report_bias(
      "2017.25 overall (we had open VFPs this year)",
      new_AgrestiCoull(accuracy_decimal_points=3, n_s=22,  n=301),
      {
        "Med Companies ": new_AgrestiCoull(accuracy_decimal_points=3, n_s=3,  n=58),
        "Social Science": new_AgrestiCoull(accuracy_decimal_points=3, n_s=4,  n=53),
        "URM ethnicites": new_AgrestiCoull(accuracy_decimal_points=3, n_s=3,  n=40),
        "Teams w/ women": new_AgrestiCoull(accuracy_decimal_points=3, n_s=5,  n=67),
      }
    )


DIVERSITY_ANALYSIS_CSV_DATA = ['Teams w/ any Women', 'teams_w_all_women', 'mixed_gender_teams_w_female_ceo', 'mixed_gender_teams_w_male_ceo', 'Teams w/ any URM Ethnicities']
DIVERSITY_ANALYSIS_CSV_DEMOGRAPHICS = ['African American', 'Native American', 'Native Hawaiian / Pacific Islander', 'Latinx']
DIVERSITY_ANALYSIS_CSV_COLUMNS = DIVERSITY_ANALYSIS_CSV_DATA + [("teams w/ " + s1) for s1 in DIVERSITY_ANALYSIS_CSV_DEMOGRAPHICS] + [("teams w/ ONLY " + s1) for s1 in DIVERSITY_ANALYSIS_CSV_DEMOGRAPHICS]

DIVERSITY_COUNT_CSV_COLUMNS = (['Men', 'Women', 'gender unknown'] + DIVERSITY_ANALYSIS_CSV_DEMOGRAPHICS + ['ethnicity unknown/not specified'] + ['ethnicity Asian/White'])
DIVERSITY_COUNT_CSV_ADMISSIONS_COLUMNS = ['# founders\r\naccepted:\r\n' + s for s in DIVERSITY_COUNT_CSV_COLUMNS]
DIVERSITY_COUNT_CSV_MARKETING_COLUMNS = ['# founders\r\napplied:\r\n' + s for s in DIVERSITY_COUNT_CSV_COLUMNS]


class DiversityAnalysis(object):
    def __init__(self):
        self._data = collections.defaultdict(lambda: PercentageDataset(n_s=0.0, n_f=0.0))
        # self._data['overall']
        # self._data['teams_w_all_women']
        # self._data['mixed_gender_teams_w_female_ceo']
        # self._data['mixed_gender_teams_w_male_ceo']

        self._with = collections.defaultdict(lambda: PercentageDataset(0.0, 0.0))
        # self._with['African American']
        # self._with['Native American']
        # self._with['Native Hawaiian / Pacific Islander']
        # self._with['Latinx']  # and previously 'Latino/a' + 'Other Hispanic'

        self._only = collections.defaultdict(lambda: PercentageDataset(0.0, 0.0))

        self.count_admitted_founders = 0

        self.count_admitted_founder_men = 0
        self.count_admitted_founder_women = 0
        self.count_admitted_founder_gender_unknown = 0

        self.count_admitted_founder_african_american = 0
        self.count_admitted_founder_native_american = 0
        self.count_admitted_founder_native_hawaiian_pacific_islander = 0
        self.count_admitted_founder_latinx = 0
        self.count_admitted_founder_ethnicity_asianwhite = 0
        self.count_admitted_founder_ethnicity_unknown = 0

    def count_admitted(self, x, tally_mode, b_admitted):
        assert type(tally_mode) == TallyMode

        if b_admitted:
            incr_f = incr_accepted
        else:
            incr_f = incr_rejected

        genders = [s.lower().strip() for s in x['genders'].split('|')]
        if len(genders) > 0:
            if any((g == 'female') for g in genders):
                incr_f(self._data['Teams w/ any Women'])

            if all((g == 'female') for g in genders):
                incr_f(self._data['teams_w_all_women'])
            elif genders[0] == 'female':  # NOTE: We should check CEO rather than F1, but this is a simplification for now. In the future we'll add Founder Role to the export.
                incr_f(self._data['mixed_gender_teams_w_female_ceo'])
            elif any((g == 'female') for g in genders):
                incr_f(self._data['mixed_gender_teams_w_male_ceo'])

        ethnicities_gen = map((lambda s: MIGRATE_ETHNICITY.get(s, s)), (s.strip() for s in x['ethnicities'].split('|')))  # Split by '|' so that we get a list of each ethnicity, and then migrate ethnicity so that the 'Latino/a' becomes 'Latinx' etc.
        ethnicities = list(ethnicities_gen)

        if len(ethnicities) > 0:

            if any(IS_URM_ETHNICITY.get(g, False) for g in ethnicities):  # TODO(from joseph): What if ethnicity is blank?
                incr_f(self._data['Teams w/ any URM Ethnicities'])

            for eth in DIVERSITY_ANALYSIS_CSV_DEMOGRAPHICS:

                if all((g == eth) for g in ethnicities):
                    incr_f(self._only[eth])
                elif any((g == eth) for g in ethnicities):
                    incr_f(self._with[eth])

        if (len(genders) > 0) and (len(ethnicities) > 0):
            incr_f(self._data['overall'])

        if b_admitted or (tally_mode == TallyMode.count_all_founders):
            count_founders = max(len(x['applicants_name_and_emails'].split(';')), len(x['field_of_study'].split('|')))  # Sometimes founders are missing emails???
            self.count_admitted_founders += count_founders

            missing_genders = count_founders - len(genders)
            self.count_admitted_founder_gender_unknown += missing_genders

            scale_ethnicities = float(count_founders) / len(ethnicities)  # You can "check all that apply" in the Ethnicities question

            # DEBUG: We are incrementing genders too much and incrementing ethnicities not enough
            if missing_genders > 0:
                print('Missing genders')
                print(repr(x['id']) + ' ' + repr(x['cohort']) + ': {} vs {}'.format(len(genders), count_founders))
            if missing_genders < 0:
                print('More genders than founders')
                print(repr(x['id']) + ' ' + repr(x['cohort']) + ': {} vs {}'.format(len(genders), count_founders))

            # if scale_ethnicities < 1.0:
            #     print('Missing ethnicities')
            #     print(repr(x['id']) + ' ' + repr(x['cohort']) + ': {} @ {}'.format(len(ethnicities), scale_ethnicities))
            # if scale_ethnicities > 1.0:
            #     print('More ethnicities than founders')
            #     print(repr(x['id']) + ' ' + repr(x['cohort']) + ': {} @ {}'.format(len(ethnicities), scale_ethnicities))

            for g in genders:
                if g == 'female':
                    self.count_admitted_founder_women += 1
                elif g == 'male':
                    self.count_admitted_founder_men += 1
                else:
                    self.count_admitted_founder_gender_unknown += 1

            for g in ethnicities:
                if g == 'African American':
                    self.count_admitted_founder_african_american += scale_ethnicities
                elif g == 'Native American':
                    self.count_admitted_founder_native_american += scale_ethnicities
                elif g == 'Native Hawaiian / Pacific Islander':
                    self.count_admitted_founder_native_hawaiian_pacific_islander += scale_ethnicities
                elif g == 'Latinx':
                    self.count_admitted_founder_latinx += scale_ethnicities
                elif (g == 'Asian') or (g == 'East Asian') or (g == 'Southeast Asian') or (g == 'White'):
                    self.count_admitted_founder_ethnicity_asianwhite += scale_ethnicities
                else:
                    print('UNKNOWN: ' + g)
                    self.count_admitted_founder_ethnicity_unknown += scale_ethnicities

    @staticmethod
    def roc_as_str(baseline_roc, demographic_dat):
        demographic_admitted = demographic_dat.fancy_stats(accuracy_decimal_points=3)
        outlier_detect = check_outlier(baseline_roc, demographic_admitted).strip()
        if outlier_detect == 'OUTLIER!':
            # Leading newline if notable
            # Leading & training newline if anomaly
            return "\r\n" + demographic_admitted.display_str + "\r\n"
        elif outlier_detect == 'notable':
            return "\r\n" + demographic_admitted.display_str
        else:
            return demographic_admitted.display_str

    def n(self):
        return self._data['overall']._n

    # def pipeline_as_str(self, baseline):
    def pipeline_as_str(self):
        # TODO(from joseph): Baseline can be "all cohorts" and skip the outlier_detect if baseline == self
        # assert type(baseline) == DiversityAnalysis
        denominator = self._data['overall'].n()
        result = list()

        for d in DIVERSITY_ANALYSIS_CSV_DATA:
            num_applied = self._data[d].n()
            result.append(PercentageDataset(n_s=num_applied, n_f=(denominator - num_applied)).fancy_stats(accuracy_decimal_points=3).display_str)

        for d in DIVERSITY_ANALYSIS_CSV_DEMOGRAPHICS:
            num_applied = self._with[d].n()
            result.append(PercentageDataset(n_s=num_applied, n_f=(denominator - num_applied)).fancy_stats(accuracy_decimal_points=3).display_str)

        for d in DIVERSITY_ANALYSIS_CSV_DEMOGRAPHICS:
            num_applied = self._only[d].n()
            result.append(PercentageDataset(n_s=num_applied, n_f=(denominator - num_applied)).fancy_stats(accuracy_decimal_points=3).display_str)

        return result

    def pct_as_str(self):
        baseline = self._data['overall'].fancy_stats(accuracy_decimal_points=3)

        overall_admitted = self._data['overall'].raw_pct()

        result = ['{:0.1f}%'.format(overall_admitted * 100)]
        for d in DIVERSITY_ANALYSIS_CSV_DATA:
            result.append(DiversityAnalysis.roc_as_str(baseline, self._data[d]))

        for d in DIVERSITY_ANALYSIS_CSV_DEMOGRAPHICS:
            result.append(DiversityAnalysis.roc_as_str(baseline, self._with[d]))

        for d in DIVERSITY_ANALYSIS_CSV_DEMOGRAPHICS:
            result.append(DiversityAnalysis.roc_as_str(baseline, self._only[d]))

        return result

    def num_as_str(self):
        return [
            self.count_admitted_founder_men,
            self.count_admitted_founder_women,
            self.count_admitted_founder_gender_unknown,

            self.count_admitted_founder_african_american,
            self.count_admitted_founder_native_american,
            self.count_admitted_founder_native_hawaiian_pacific_islander,
            self.count_admitted_founder_latinx,
            self.count_admitted_founder_ethnicity_unknown,

            self.count_admitted_founder_ethnicity_asianwhite,
        ]


ALL_COHORTS_SENTINEL_KEY = 0


def session_name_impl(si):
    if si == ALL_COHORTS_SENTINEL_KEY:
        return '(all cohorts)'
    else:
        return session_name(si)


class CsvOutputCalculator(object):
    def __init__(self):
        # keys are cohorts
        self.written_stage = collections.defaultdict(DiversityAnalysis)
        self.interview_stage = collections.defaultdict(DiversityAnalysis)

        self.qualifying = collections.defaultdict(DiversityAnalysis)
        self.nonqualifying = collections.defaultdict(DiversityAnalysis)

    def count(self, r, n):
        """Usually ``n``==1, unless you are counting weighted averages for some reason (e.g. if we don't know VFP status we could 50%-50% both, or something)"""

        assert n == 1, "we're using incr_accepted and incr_rejected for now, but if we accept other values of ``n`` we can update this code accordingly"

        si = session_integer(r['cohort'])
        self.count_impl(r, si)
        self.count_impl(r, ALL_COHORTS_SENTINEL_KEY)

    def count_impl(self, r, si):
        b_admitted_to_startx = (r['admissions'] == 'StartX')

        if b_admitted_to_startx:
            self.interview_stage[si].count_admitted(r, tally_mode=TallyMode.count_admitted_founders_only, b_admitted=True)
            self.written_stage[  si].count_admitted(r, tally_mode=TallyMode.count_admitted_founders_only, b_admitted=True)
        elif GOT_INTERVIEWED[r['admissions']]:
            self.interview_stage[si].count_admitted(r, tally_mode=TallyMode.count_admitted_founders_only, b_admitted=False)
            self.written_stage[  si].count_admitted(r, tally_mode=TallyMode.count_admitted_founders_only, b_admitted=True)
        elif r['admissions']:
            self.written_stage[  si].count_admitted(r, tally_mode=TallyMode.count_admitted_founders_only, b_admitted=False)

        # FORCE b_admitted == TRUE  so that it counts founders
        # TODO(we need an enum)
        if r['is_qualifying'] == 'true':
            self.qualifying[   si].count_admitted(r, tally_mode=TallyMode.count_all_founders, b_admitted=True)
        else:
            self.nonqualifying[si].count_admitted(r, tally_mode=TallyMode.count_all_founders, b_admitted=True)


class DemographicsAnalysis(object):
    def __init__(self):
        self.categories = ['SIR summer program', 'SIR school-year scholarship', '(StartX) Stanford professors', '(StartX) "maybe Stanford" early-stage', '(StartX) NON-Stanford early-stage', 'Series A+', '(StartX) other unknown']
        self.subgroups = dict()
        for c in self.categories:
            self.subgroups[c] = CsvOutputCalculator()

    def count_application(self, x):
        # Compare to ``filter_steps`` above
        if x['program'] == 'student_in_residence':
            if session_name(session_integer(x['cohort'].strip())).strip().startswith('Summer'):
                self.subgroups['SIR summer program'].count(x, 1.0)
            else:
                self.subgroups['SIR school-year scholarship'].count(x, 1.0)
        else:
            # Not a student. Check professor next
            if ((x['has_professor'] == 'true') or (x['program'] == 'professor_in_residence')) and (x['is_maybe_stanford'] == 'probably_stanford'):
                self.subgroups['(StartX) Stanford professors'].count(x, 1.0)
            elif is_series_a_plus(x['stage_funding']):
                self.subgroups['Series A+'].count(x, 1.0)
            else:
                # Early-stage. So count whether it's Stanford or not-Stanford!
                if x['is_maybe_stanford'] == 'probably_stanford':
                    self.subgroups['(StartX) "maybe Stanford" early-stage'].count(x, 1.0)
                elif x['is_maybe_stanford'] == 'VFP':
                    self.subgroups['(StartX) NON-Stanford early-stage'].count(x, 1.0)
                else:
                    self.subgroups['(StartX) other unknown'].count(x, 1.0)

    # Per cohort
    # Interview vs. written
    # SIR vs. (StartX) Stanford professors vs. (StartX) "maybe Stanford" early-stage vs. (StartX) non-Stanford early-stage vs. Series A+
    # .. overall % admitted
    # .. range of certainty % admitted for: "teams w/ female co-founder", "teams w/ XYZ ethnicity", ...
    # .. total # of founders admitted vs. total # of each ethnicity, total # of each gender


CsvNames = collections.namedtuple('CsvNames', ['admissions', 'marketing'])


def create_csvs(admissions_data, csv_fname):
    assert type(csv_fname) == CsvNames

    reapplications = DemographicsAnalysis()
    firsttime_applications = DemographicsAnalysis()

    for x in admissions_data:
        if x['is_reapplicant'] == 'true':
            reapplications.count_application(x)
        else:
            firsttime_applications.count_application(x)

    csv_headers = ['Evaluation Tier', 'Admissions Category']
    csv_shared_headers = ['Cohort/Date', 'n']

    # In python3, csv.writer doesn't work with 'bytes' and ONLY works with 'strings'
    # https://stackoverflow.com/questions/33054527/typeerror-a-bytes-like-object-is-required-not-str-when-writing-to-a-file-in
    with open(csv_fname.admissions, 'w') as f:

        f_out = csv.writer(f)
        header_str = csv_headers + ['Application Medium'] + csv_shared_headers + ['Overall % acceptance'] + [("% acceptance\r\n(Statistical Significance range of certainty)\r\n" + s) for s in DIVERSITY_ANALYSIS_CSV_COLUMNS] + DIVERSITY_COUNT_CSV_ADMISSIONS_COLUMNS
        # print(repr(header_str))
        f_out.writerow(header_str)
        # f_out.writerow([b'abc'])

        # _bias_detector_main.admissions.csv
        # COLUMN 0 = New App vs. Re-app
        # COLUMN 1 = Admissions category
        # COLUMN 2 = Written vs. Interview
        # COLUMN 3 = Cohort
        # COLUMN 4 = Overall n admitted
        # COLUMN 5 = Overall % admitted
        # COLUMN 6+ = Range of certainty teams w/ all women, Mixed teams w/ female CEO, Mixed team w/ male CEO, Range of certainty teams w/ XYZ ethnicity, ..., Range of certainty teams w/ ONLY XYZ ethnicity,
        # COLUMN ... = Range of certainty teams w/ ONLY URM ethnicity
        # COLUMN n-2 = Total # of founders admitted, total # each ethnicity admitted, total # each gender admitted

        for rf, tier_dat in [('New Applications', firsttime_applications), ('Reapplications', reapplications)]:
            for admissions_category in tier_dat.categories:
                for evaluation_medium, em_dat in [('Written Application', tier_dat.subgroups[admissions_category].written_stage), ('Interview Stage', tier_dat.subgroups[admissions_category].interview_stage)]:
                    for si in sorted(em_dat.keys()):
                        da_dat = em_dat[si]
                        row_list = [rf, admissions_category, evaluation_medium, session_name_impl(si), int(da_dat.n())] + da_dat.pct_as_str() + da_dat.num_as_str()
                        f_out.writerow(row_list)

    with open(csv_fname.marketing, 'w') as f:
        f_out = csv.writer(f)
        header_str = csv_headers + ['Lead Qualification'] + csv_shared_headers + DIVERSITY_COUNT_CSV_MARKETING_COLUMNS + [("% of applicants \r\n(Statistical Significance range of certainty)\r\n" + s) for s in DIVERSITY_ANALYSIS_CSV_COLUMNS]

        f_out.writerow(header_str)

        # _bias_detector_main.marketing.csv
        # COLUMN 0 = New App vs. Re-app
        # COLUMN 1 = Admissions category
        # COLUMN 2 = Qualifying vs non-qualifying
        # COLUMN 3 = Cohort
        # COLUMN 4 = Overall n applied (closed, not spam)
        # COLUMN 5+ = Range of certainty teams w/ all women, Mixed teams w/ female CEO, Mixed team w/ male CEO, Range of certainty teams w/ XYZ ethnicity, ..., Range of certainty teams w/ ONLY XYZ ethnicity,
        # COLUMN ... = Range of certainty teams w/ ONLY URM ethnicity
        # COLUMN n-2 = Total # of founders applied, total # each ethnicity applied, total # each gender applied
        for rf, tier_dat in [('New Applications', firsttime_applications), ('Reapplications', reapplications)]:
            for admissions_category in tier_dat.categories:
                for qualifying_vs_nonqualifying, qn_dat in [('Qualifying as Outbound', tier_dat.subgroups[admissions_category].qualifying), ('inbound', tier_dat.subgroups[admissions_category].nonqualifying)]:
                    for si in sorted(qn_dat.keys()):
                        da_dat = qn_dat[si]
                        row_list = [rf, admissions_category, qualifying_vs_nonqualifying, session_name_impl(si), int(da_dat.n())] + da_dat.num_as_str() + da_dat.pipeline_as_str()
                        f_out.writerow(row_list)


def main():
    b_csv_step = False
    # print(repr(sys.argv))
    # print(repr(sys.argv[1]))
    # print(repr(' '.join(sys.argv[2:])))

    if (len(sys.argv) > 2) and (sys.argv[1] == '--csv'):
        fname = ' '.join(sys.argv[2:])
        b_csv_step = True
    elif len(sys.argv) > 1:
        fname = ' '.join(sys.argv[1:])
    else:
        # https://startx.com/dumps/7813
        fname = 'tracked_apps_history_200528205134.csv'

    try:
        with open(fname, 'r', encoding='utf8') as f:
            raw_data = list(csv.DictReader(f))
    except TypeError as exc:
        # python3 vs python2
        # https://stackoverflow.com/questions/10971033/backporting-python-3-openencoding-utf-8-to-python-2
        # TypeError: 'encoding' is an invalid keyword argument for this function
        if 'encoding' in exc.message:
            with open(fname, 'rb') as f:
                raw_data = list(csv.DictReader(f))
        else:
            raise exc

    clean_data = clean_data_impl(raw_data)

    # Strategy:

    # divider_labels = ['applied before', 'fresh applicant SIR', 'fresh applicant non-SIR Series A+', 'fresh applicant non-SIR early-stage interviewed', 'fresh applicant non-SIR early-stage written-application VFP', 'fresh applicant non-SIR early-stage written-application Affiliated team']

    # To show the split across S17 -> F17 and the change in VFP, use this...
    # divider_labels = ['applied before', 'student', 'VFP', 'Series A+', 'all']

    print('################################')
    print('   Part 1: Trends across time')
    print('   [Instructions]')
    print('     * Focus on percentages, not overall counts')
    print('     * Results are shown as Written Phase > Interview Phase > Both (end-to-end) ')
    print('################################')

    # Assuming all VFPs are invite-required (and therefore a higher quality) but not noticably so starting at Series A, use this:
    report_timeseries_data(clean_data, ['applied before', 'Summer-SIR', 'SIR', 'Series A+', 'VFP', 'stanfordprofessor', 'all'], 'exhaustive_complementary')
    # We also have the added benefit of quickly counting "SIR" starting in P19 applications
    #
    #      TODO(actual VFP tests)
    #           +- interviewed
    #           +- not interviewed
    #             +- Definitely VFP
    #             +- Definitely affiliated

    print('')
    print('')
    print('########################################')
    print('   Part 2: Applicant Mixer statistics')
    print('########################################')

    report_timeseries_data(clean_data, ['positive_referral', 'new Stanford'], 'nested_compound')  # (What is the acceptance rate of: referral companies?)  (How many new Stanford apps had referrals?)
    report_timeseries_data(clean_data, ['stanfordprofessor', 'Stanford', 'first application'], 'nested_compound')  # What is the acceptance rate of: Stanford professors overall? Stanford professors on their first application?
    report_timeseries_data(clean_data, ['SIR', 'applied before'], 'nested_compound')  # What is the acceptance rate of: SIR overall? SIR re-applicants?

    #
    # QUESTION --> do we use "is_eventually_admitted" instead???
    #   If yes, it indicates anomalies in the applicant pool...
    #   If no, it clearly answers the above question: applied before needs to
    #   be the first Yule-Simpson separation.
    #

    bBonus = {}
    bBonus['Series_A+'] = lambda x: is_series_a_plus(x['stage_funding'])
    bBonus['stanford_professor'] = lambda x: (x['has_professor'] == 'true') and (x['is_maybe_stanford'] == 'probably_stanford')
    bBonus['new_team_positive_referral'] = lambda x: (x['founder_referrals'].strip() != '') and (x['is_reapplicant'] == 'false')  # How many new applications with referrals did we have?
    print('')
    report_pipeline_demographics(filter_demographic_data(clean_data, bBonus, lambda x: True, lambda x: True), clean_data, '')

    # What percentage of Stanford applications have a referral?
    # What percentage of VFP applications had a referral?
    # What percentage of applications have "is_maybe_stanford" unclear?
    print('')
    report_pipeline_demographics(filter_demographic_data(clean_data, {'has_referral': lambda x: (x['founder_referrals'].strip() != '')}, lambda x: True, lambda x: (x['is_maybe_stanford'] == 'VFP')), clean_data, '*VFP* ')
    print('')
    report_pipeline_demographics(filter_demographic_data(clean_data, {'has_referral': lambda x: (x['founder_referrals'].strip() != '')}, lambda x: True, lambda x: (x['is_maybe_stanford'] == 'probably_stanford')), clean_data, '*Stanford* ')
    print('')
    report_pipeline_demographics(filter_demographic_data(clean_data, {'ambiguous_Stanford': lambda x: (x['is_maybe_stanford'] != 'VFP') and (x['is_maybe_stanford'] != 'probably_stanford')}, lambda x: True, lambda x: True), clean_data, '')

    print('')
    print('')
    print('###########################################')
    print('   Part 3: Treatment of different groups')
    print('###########################################')

    def got_interviewed(x):
        return GOT_INTERVIEWED[x['admissions']]

    def got_accepted(x):
        return (x['admissions'] == 'StartX')

    def is_sir(x):
        return x['program'] == 'student_in_residence'

    """Confirming approximations
    print('CDF ,  Bowling (2009) ,  Zelen & Severo (1964)')
    g = scipy.stats.norm(0.0, 1.0)
    err_max = []
    err_mean = []

    STEP_START_END = 5.0
    STEPS = 500
    for i in range(STEPS):
        x = -STEP_START_END + (STEP_START_END * 2) * i / STEPS

        actual = g.cdf(x)
        candidate_max = scipy_stats_norm_cdf_max(x)
        candidate_mean = scipy_stats_norm_cdf_mean(x)
        print('x = {}; \t {} \t {} \t {}'.format(x, actual, candidate_max, candidate_mean))

        err_max.append(math.fabs(candidate_max - actual))
        err_mean.append(math.fabs(candidate_mean - actual))

    print('\t MAX ERROR \t {} \t {}'.format(max(err_max), max(err_mean)))
    print('\t MEAN ERROR \t {} \t {}'.format(math.fsum(err_max) / STEPS, math.fsum(err_mean) / STEPS))
    """

    # write_reference_chart()


if __name__ == '__main__':
    main()
