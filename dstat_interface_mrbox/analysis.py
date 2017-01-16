#!/usr/bin/env python
#     DStat Interface - An interface for the open hardware DStat potentiostat
#     Copyright (C) 2014  Michael D. M. Dryden -
#     Wheeler Microfluidics Laboratory <http://microfluidics.utoronto.ca>
#
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Functions for analyzing data.
"""
import logging
import datetime as dt
import cStringIO as StringIO
import re
import types

import numpy as np
import pandas as pd
import arrow

logger = logging.getLogger('dstat.analysis')

class AnalysisOptions(object):
    """Analysis options window."""
    def __init__(self, builder):
        self.builder = builder
        self.builder.add_from_file('interface/analysis_options.glade')
        self.builder.connect_signals(self)

        self.window = self.builder.get_object('analysis_dialog')
        self.stats_button = self.builder.get_object('stats_button')
        self.stats_start = self.builder.get_object('stats_start_spin')
        self.stats_start_button = self.builder.get_object('stats_start_button')
        self.stats_stop = self.builder.get_object('stats_stop_spin')
        self.stats_stop_button = self.builder.get_object('stats_stop_button')

        self.stats_button.connect('toggled',
                                  self.on_button_toggled_hide,
                                      [self.stats_stop,
                                       self.stats_stop_button,
                                       self.stats_start,
                                       self.stats_start_button
                                       ]
                                  )

        self._params = {'stats_true':False,
                        'stats_start_true':False,
                        'stats_stop':0,
                        'stats_stop_true':False,
                        'stats_start':0
                        }

    def show(self):
        """Show options window."""
        self.window.run()
        self.window.hide()

    def on_button_toggled_hide(self, control, widgets):
        """Hide unchecked fields"""
        active = control.get_active()

        for widget in widgets:
            widget.set_sensitive(active)

    @property
    def params(self):
        """Getter for analysis params"""
        self._params['stats_true'] = self.stats_button.get_active()

        self._params['stats_start_true'] = self.stats_start_button.get_active()
        self._params['stats_start'] = self.stats_start.get_value()

        self._params['stats_stop_true'] = self.stats_stop_button.get_active()
        self._params['stats_stop'] = self.stats_stop.get_value()

        return self._params

    @params.setter
    def params(self, params):
        for key in self._params:
            if key in params:
                self._params[key] = params[key]

        self.stats_button.set_active(self._params['stats_true'])
        self.stats_start_button.set_active(self._params['stats_start_true'])
        self.stats_start.set_value(self._params['stats_start'])
        self.stats_stop_button.set_active(self._params['stats_stop_true'])
        self.stats_stop.set_value(self._params['stats_stop'])

def do_analysis(experiment):
    """Takes an experiment class instance and runs selected analysis."""

    experiment.analysis = {}

    if experiment.parameters['stats_true']:
        if (experiment.parameters['stats_start_true'] or
            experiment.parameters['stats_stop_true']):

            if experiment.parameters['stats_start_true']:
                start = experiment.parameters['stats_start']
            else:
                start = min(experiment.data['data'][0][0])

            if experiment.parameters['stats_stop_true']:
                stop = experiment.parameters['stats_stop']
            else:
                stop = min(experiment.data['data'][0][0])

            data = _data_slice(experiment.data['data'],
                               start,
                               stop
                               )
        else:
            data = experiment.data['data']

        experiment.analysis.update(_summary_stats(data))

    try:
        x, y = experiment.data['ft'][0]
        experiment.analysis['FT Integral'] = _integrateSpectrum(
                x,
                y,
                float(experiment.parameters['sync_freq']),
                float(experiment.parameters['fft_int'])
        )

    except KeyError:
        pass

def _data_slice(data, start, stop):
    """Accepts data (as list of tuples of lists) and returns copy of data
    between start and stop (in whatever x-axis units for the experiment type).
    """
    output = []

    for scan in range(len(data)):
        t = []
        for i in range(len(data[scan])):
            t.append([])
        output.append(tuple(t))

        for i in range(len(data[scan][0])): # x-axis column
            if data[scan][0][i] >= start or data[scan][0][i] <= stop:
                for d in range(len(output[scan])):
                    output[scan][d].append(data[scan][d][i])

    return output

def _summary_stats(data):
    """Takes data and returns summary statistics of first y variable as dict of
    name, (scan, values).
    """

    stats = {'min':[],'max':[], 'mean':[]}

    for scan in range(len(data)):
        stats['min'].append(
                            (scan, min(data[scan][1]))
                            )
        stats['max'].append(
                            (scan, max(data[scan][1]))
                            )
        stats['mean'].append(
                            (scan, np.mean(data[scan][1]))
                            )
    return stats

def _integrateSpectrum(x, y, target, bandwidth):
    """
    Returns integral of range of bandwidth centered on target.
    """
    j = 0
    k = len(x)

    for i in range(len(x)):
        if x[i] >= target-bandwidth/2:
            j = i
            break

    for i in range(j,len(x)):
        if x[i] >= target+bandwidth/2:
            k = i
            break

    return [(0, np.trapz(y=y[j:k], x=x[j:k]))]


def integrate_fft(df_fft, target_hz, bandwidth):
    '''
    Integrate a bandwidth around a target frequency in DStat FFT results.

    Args
    ----

        df_data (pandas.DataFrame) : DStat FFT results as returned by the
            `dstat_to_fft_frame` function, including the columns `frequency`
            and `amplitude`.
        target_hz (float) : Target frequency.
        bandwidth (float) : Bandwidth (centered at target frequency) to
            integrate within.

    Returns
    -------

        (float) : Integrated amplitude within bandwidth around target
            frequency (definite integral as approximated by trapezoidal
            rule).  See `numpy.trapz` for more information.
    '''
    df_bandpass = df_fft.loc[(df_fft.frequency >= target_hz - .5 * bandwidth) &
                             (df_fft.frequency <= target_hz + .5 * bandwidth)]

    # Definite integral as approximated by trapezoidal rule.
    return np.trapz(x=df_bandpass.frequency, y=df_bandpass.amplitude)


def dstat_to_fft_frame(df_data, sample_frequency_hz=60., settling_period_s=2.):
    '''
    Compute FFT for set of DStat measurements.

    Args
    ----

        df_data (pandas.DataFrame) : DStat experiment results with at least the
            columns `time_s`, and `current_amps`.
        settling_period_s (float) : Signal settling time (in seconds).  No
            measurements before specified time will be considered when
            computing the FFT.

    Returns
    -------

        df_data (pandas.DataFrame) : DStat FFT table with the columns
            `frequency` and `amplitude`.
    '''
    df_data_i = df_data.loc[(df_data.time_s > settling_period_s)].copy()
    df_data_i.reset_index(drop=True, inplace=True)

    avg = np.mean(df_data_i.current_amps.values)

    # Find first and last rising edge in synchronous signal.
    rising_edge_i = np.zeros(df_data_i.shape[0], dtype=bool)
    rising_edge_i[:-1] = ((df_data_i.current_amps <= avg)[:-1].values &
                          (df_data_i.current_amps > avg)[1:].values)
    df_data_i['rising_edge'] = rising_edge_i
    first_edge, last_edge = df_data_i.loc[df_data_i.rising_edge].index[[0, -1]]

    # Set start and end of FFT measurements range to mean.
    df_data_i.current_amps.values[[first_edge, last_edge]] = avg

    # Restrict FFT to measurements between first and last rising edge.
    df_edges_i = df_data_i.loc[first_edge:last_edge - 1, ['time_s',
                                                          'current_amps']]

    # Length of the signal.
    N = len(df_edges_i)

    # Compute frequencies based on sampling frequency.
    frequencies = np.fft.fftfreq(N, d=1. / sample_frequency_hz)[:N / 2]

    # FFT computing and normalization.
    Y = np.fft.fft(df_edges_i.current_amps.values) / N
    Y = abs(Y[:N / 2])

    # Create data frame from frequency and amplitude arrays.
    df_fft_i = pd.DataFrame(np.column_stack([frequencies, Y]),
                            columns=['frequency', 'amplitude'])
    return df_fft_i


def dstat_to_frame(data_path_i):
    '''
    Convert DStat text file results to ``pandas.DataFrame``.

    Parameters
    ----------
    data_path_i : str
        Path to DStat results text file.

    Returns
    -------
    pandas.DataFrame
        DStat measurements in a table with the column ``name`` and
        ``current_amps``, indexed by ``utc_timestamp`` and ``time_s``.

    Notes
    -----

    **TODO** Currently only works for experiments with current as the only
    measurement column (i.e., chronoamperometry, photodiode).
    '''
    with data_path_i.open('r') as input_i:
        diff = (dt.datetime.utcnow() - dt.datetime.now())
        utc_timestamp = arrow.get(input_i.readline().split(' ')[-1]) + diff

    str_data = StringIO.StringIO('\n'.join(l for l in data_path_i.lines()
                                           if not l.startswith('#')))
    df_data = pd.read_csv(str_data, sep='\s+', header=None)
    df_data.rename(columns={0: 'time_s', 1: 'current_amps'}, inplace=True)
    df_data.insert(0, 'name', re.sub(r'-data$', '', data_path_i.namebase))
    df_data.insert(0, 'utc_timestamp', utc_timestamp.datetime +
                   df_data.index.map(lambda v: dt.timedelta(seconds=v)))
    df_data.set_index(['utc_timestamp', 'time_s'], inplace=True)
    return df_data


def reduce_dstat_data(df_dstat, groupby, settling_period_s=2., bandwidth=1.,
                      summary_fields=[]):
    '''
    Reduce measurements for each DStat experiment in `df_dstat` to a single
    row with an aggregate signal value.

    For continuous detection, the aggregate signal column corresponds to the
    mean `current_amps`.

    For synchronous detection experiments (i.e., where `target_hz` is greater
    than 0), the aggregate signal corresponds to the integrated amplitude of
    the `current_amps` FFT within the bandwidth around target frequency.

    Args
    ----

        df_md_dstat (pandas.DataFrame) : DStat measurements table at least
            containing the columns `current_amps`, and `time_s`. For
            synchronous detection experiments the table must also include the
            columns `sample_frequency_hz`, `target_hz`.
        groupby (object, list) : Column(s) that identify distinct DStat
            experiments.  Each row of the output summary table directly
            corresponds to each distinct combination of the `groupby`
            column(s), where the first column(s) in the output table correspond
            to the respective `groupby` column(s).
        settling_period_s (float) : Measurement settling period in seconds.
            Measurements taken before start time will not be included in
            calculations.
        bandwidth (float) : Bandwidth (centered at synchronous detection
            frequency) to integrate within.
        summary_fields (list) : List of columns to extract first value in each
            group to include in each row of the output summary table.

    Returns
    -------

        (pd.DataFrame) : Table containing the `groupby` column(s), the
            `summary_fields` columns, and the column `signal` (i.e., the
            aggregate signal value).
    '''
    rows = []

    for index_i, df_i in df_dstat.groupby(groupby):
        # Get `pandas.Series` containing summary metadata fields (not including signal).
        summary_i = df_i.iloc[0][summary_fields].copy()
        summary_i.name = index_i

        if 'target_hz' in summary_i and summary_i['target_hz'] > 0:
            # Synchronous detection (e.g., shuttered).
            #
            # Use FFT to integrate signal at bandwidth surrounding target synchonization
            # frequency.
            df_fft_i = dstat_to_fft_frame(df_i, sample_frequency_hz=
                                          summary_i['sample_frequency_hz'],
                                          settling_period_s=settling_period_s)
            summary_i['signal'] = integrate_fft(df_fft_i,
                                                summary_i['target_hz'],
                                                bandwidth)
        else:
            # Continuous detection.
            #
            # Take mean measurement value (after settling period).
            summary_i['signal'] = (df_i.loc[df_i.time_s > settling_period_s]
                                   .current_amps.mean())
        if isinstance(index_i, types.StringTypes):
            index_i = [index_i]
        else:
            index_i = list(index_i)
        rows.append(index_i + summary_i.tolist())

    return pd.DataFrame(rows, columns=groupby + summary_i.keys().tolist())
