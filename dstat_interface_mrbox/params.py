#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import logging

import yaml

from errors import InputError

logger = logging.getLogger('dstat.params')

def get_params(window):
    """Fetches and returns dict of all parameters for saving."""

    parameters = {}

    selection = window.exp_window.select_to_key[window.expcombobox.get_active()]
    parameters['experiment_index'] = selection

    try:
        parameters['version'] = window.version
    except AttributeError: # Will be thrown if not connected to DStat
        pass

    try:
        parameters.update(window.adc_pot.params)
    except InputError:
        logger.info("No gain selected.")
    parameters.update(window.exp_window.get_params(selection))
    parameters.update(window.analysis_opt_window.params)
    parameters.update(window.db_window.persistent_params)
    
    return parameters

def save_params(window, path):
    """Fetches current params and saves to path."""
    logger.info("Save to: %s", path)
    params = get_params(window)

    with open(path, 'w') as f:
        yaml.dump(params, f)

def load_params(window, path):
    """Loads params from a path into UI elements."""
    
    try:
        get_params(window)
    except InputError:  # Will be thrown because no experiment will be selected
        pass

    with open(path, 'r') as f:
        params = yaml.load(f)
    set_params(window, params)

def set_params(window, params):
    window.adc_pot.params = params
    if 'experiment_index' in params:
        window.expcombobox.set_active(
            window.exp_window.classes[params['experiment_index']][0]
            )
        window.exp_window.set_params(params['experiment_index'], params)
        
    window.analysis_opt_window.params = params
    window.db_window.params = params

    window.params_loaded = True
