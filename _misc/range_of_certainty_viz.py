#!/usr/bin/env python3
"""range_of_certainty_viz.py

Scroll down to `def read_args():` to see usage instructions
"""

import argparse
import collections
import math

import matplotlib.pyplot
import matplotlib.patches

# import scipy.stats


def scipy_stats_norm_cdf(x):
    t = 1.0 / (1.0 + 0.33267 * x)
    a1 = 0.4361836
    a2 = -0.1201676
    a3 = 0.937298

    if x < 0:
        return 1.0 - (scipy_stats_norm_cdf(-x))
    else:
        return 1.0 - (scipy_stats_norm_pdf(x)) * t * (a1 + t * (a2 + t * a3))


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


StatisticallySignificant = collections.namedtuple('StatisticallySignificant', ['conservative', 'optimistic', 'nominal', 'display_str', 'confidence_pct', 'accuracy_decimal_points'])


class PercentageDataset(object):
    def __init__(self, n_s, n_f):
        self._n_s = n_s
        self._n_f = n_f
        self._n = n_s + n_f

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

    def log_prob(self, true_success_rate : float) -> float:
        """What is the the ln(probability) of seeing the given observations, if the true "success rate" is as given?
          → the probability of seeing `count_successes` successes is x^count_successes
          → the probability of seeing `count_failures` falures is (1.0-x)^count_failures

        :param true_success_rate: value between 0.0 and 1.0
        :return: ln(probability_of_seeing_events)
          ln(probability_of_seeing_events) = ln(x^count_successes   *   (1.0-x)^count_failures)
                                           = ln(x^count_successes) + ln((1.0-x)^count_failures)
                                           = count_successes*ln(x) + count_failures*ln((1.0-x))
        """
        if (true_success_rate <= 0.0) and (self._n_s > 0):
            return -math.inf
        if (true_success_rate >= 1.0) and (self._n_f > 0):
            return -math.inf

        return self._n_s * math.log(true_success_rate) + self._n_f * math.log1p(-true_success_rate)

    def fancy_stats(self, accuracy_decimal_points) -> StatisticallySignificant:
        return new_AgrestiCoull(accuracy_decimal_points=accuracy_decimal_points, n_s=self._n_s, n=self._n)

    def basic_stats(self) -> str:
        raw_stats_str = self.raw_stats()

        pct = self._n_s / float(self._n)
        unbiased_pct = (self._n_s + 0.5) / (self._n + 1)

        return "\r\n".join([
            'Observed percentage: {:0.1f}% = {}'.format(pct * 100, raw_stats_str),
            'After Laplace Smoothing w/ Jeffreys Prior: {:0.1f}%'.format(unbiased_pct * 100)
        ])

    def raw_stats(self) -> str:
        return '{:.0f} failures and {:.0f} successes, out of {} total events'.format(self._n_f, self._n_s, self._n)

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


def new_AgrestiCoull(accuracy_decimal_points, n_s, n) -> StatisticallySignificant:
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
        display_str = '{:0.2f}..{:0.2f} ({} out of {})'.format(conservative_pct, optimistic_pct, n_s, n)
        return StatisticallySignificant(conservative=conservative_pct, optimistic=optimistic_pct, nominal=(float(n_s) / float(n_s + n_f)), display_str=display_str, confidence_pct=confidence_pct, accuracy_decimal_points=accuracy_decimal_points)


def write_viz_to_images(primary_output_imagename: str, input_basicstats: PercentageDataset, input_fancystats: StatisticallySignificant) -> None:

    png_dpi = 1 / matplotlib.pyplot.rcParams['figure.dpi']  # pixel in inches
    # https://matplotlib.org/stable/gallery/subplots_axes_and_figures/figure_size_units.html#figure-size-in-pixel
    matplotlib.pyplot.figure(figsize=(1000.0 * png_dpi, 1100.0 * png_dpi))

    # === Viz 1: Describe the problem ===
    count_failures = input_basicstats.n() * (1.0 - input_basicstats.raw_pct())
    count_successes = input_basicstats.n() * input_basicstats.raw_pct()

    rect_width_radius = 1.0 / input_basicstats.n() / 2.0

    matplotlib.pyplot.clf()
    matplotlib.pyplot.suptitle('We observed a "{:.1f}% success rate"...'.format(input_basicstats.raw_pct() * 100.0), fontweight='bold')
    matplotlib.pyplot.title("...but is there a way to express a range of certainty, without getting into\nthe complexity of confidence intervals, p-values, etc.?\n")
    if count_failures > 0:
        matplotlib.pyplot.text(rect_width_radius, count_failures, ' {:.0f} failures'.format(count_failures), verticalalignment='top')
    if count_successes > 0:
        matplotlib.pyplot.text(1.0 - rect_width_radius, count_successes, '{:.0f} successes '.format(count_successes), verticalalignment='top', horizontalalignment='right')
    # https://math.stackexchange.com/questions/864606/difference-between-%E2%89%88-%E2%89%83-and-%E2%89%85
    matplotlib.pyplot.text(0.5, 0.0, '\n{} ≈ "{:.1f}%" success rate'.format(input_basicstats.raw_stats(), input_basicstats.raw_pct() * 100.0), horizontalalignment='center', verticalalignment='top', fontweight='bold')
    matplotlib.pyplot.xlim(-0.5, 1.5)
    matplotlib.pyplot.ylim(0.0, max(count_failures, count_successes))
    ax = matplotlib.pyplot.subplot()
    ax.add_patch(matplotlib.patches.Rectangle((-rect_width_radius, 0.0), height=count_failures, width=rect_width_radius * 2.0, color='orange'))
    ax.add_patch(matplotlib.patches.Rectangle((1.0 - rect_width_radius, 0.0), height=count_successes, width=rect_width_radius * 2.0, color='orange'))
    ax.xaxis.set_visible(False)
    ax.yaxis.set_tick_params(labelright=True)
    ax.spines['top'].set_visible(False)

    print('Writing 0000_' + primary_output_imagename)
    matplotlib.pyplot.savefig('0000_' + primary_output_imagename)

    # === Viz N: Illustrate a solution ===

    confidence_pct100 = 100.0 * input_fancystats.confidence_pct
    observed_success_rate = input_basicstats.raw_pct()

    x_resolution = math.ceil(0.5 / png_dpi)
    xs = [float(x) / x_resolution for x in range(int(x_resolution+1))]
    # print(repr(xs))

    # if `x` is the "true success rate",

    log_ys = [input_basicstats.log_prob(x) for x in xs]
    # print(repr(log_ys))
    ys = [math.exp(y) for y in log_ys]
    plot_ymax = max(ys)

    # Observed is X
    # If we choose to draw error bars at Y and Z, we can say
    # "..."
    # a.k.a. "80% range of certainty"
    matplotlib.pyplot.clf()
    matplotlib.pyplot.suptitle("Probability of observating " + input_basicstats.raw_stats().replace(", ", "\n") + ', if the "true success rate" is ... (see x-axis)')
    # matplotlib.pyplot.title('{0:0.1f}% of the time, the error on our estimated success rate is more than ±{0:0.1f}% a.k.a. "{1:0.1f}% range of certainty"'.format(100.0 - confidence_pct100, confidence_pct100))
    matplotlib.pyplot.plot([observed_success_rate, observed_success_rate], [0.0, plot_ymax], '--', label='"Observed" success rate, a.k.a. n_success ÷ n_total', color='blue')
    matplotlib.pyplot.plot(xs, ys,'-', color='green')
    matplotlib.pyplot.xlabel('"true success rate""')
    matplotlib.pyplot.ylabel('Probability')
    matplotlib.pyplot.legend()

    ax = matplotlib.pyplot.subplot()
    ax.set_ylim(bottom=0.0)

    print('Writing 0001_' + primary_output_imagename)
    matplotlib.pyplot.savefig('0001_' + primary_output_imagename)


def read_args() -> PercentageDataset:
    parser = argparse.ArgumentParser(
                    prog="range_of_certainty_viz.py",
                    description="Perhaps a more simplified way to express 'ranges of certainty'... for audiences that aren't as well versed in confidence intervals, probability, etc.",
                    epilog='Basic Usage: python3 ./range_of_certainty_viz.py --count-successes=5 --count-total=7')

    parser.add_argument('-t', '--count-total', type=int)
    parser.add_argument('-s', '--count-successes', type=int)
    parser.add_argument('-f', '--count-failures', type=int)

    args = parser.parse_args()

    if sum(x is None for x in [args.count_total, args.count_successes, args.count_failures]) != 1:
        # NOTE: Early return (panic)
        parser.error("""
***ERROR***
  Exactly two of
    (--count-total, --count-successes, --count-failures)
  must be provided.
Please try again!""")

    # INVARIANT: If we get this far, the correct command line arguments were provided.

    if args.count_total is None:
        return PercentageDataset(args.count_successes, args.count_failures)
    elif args.count_failures is None:
        return PercentageDataset(args.count_successes, args.count_total - args.count_successes)
    elif args.count_successes is None:
        return PercentageDataset(args.count_total - args.count_failures, args.count_failures)

    raise NotImplementedError("This should be impossible, but if you get here... maybe someone added a new type of command line argument we weren't ready for?")


def main() -> None:
    test_data = read_args()
    print(test_data.basic_stats())
    range_of_certainty_calculation = test_data.fancy_stats(accuracy_decimal_points=3)
    print(range_of_certainty_calculation.display_str)
    write_viz_to_images('range_of_certainty.png', test_data, range_of_certainty_calculation)


if __name__ == '__main__':
    main()


# https://github.com/python-mode/python-mode/issues/699#issuecomment-286598349
# pylama:ignore=E201,E202

# https://stackoverflow.com/questions/4341746/how-do-i-disable-a-pylint-warning
# https://stackoverflow.com/questions/18444840/how-to-disable-a-pep8-error-in-a-specific-file
# noqa: E266
# noqa: E501
