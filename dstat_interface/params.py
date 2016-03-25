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

from errors import ErrorLogger, InputError
_logger = ErrorLogger(sender="dstat-interface-params")

def get_params(window):
    """Fetches and returns dict of all parameters for saving."""
    
    selection = window.exp_window.select_to_key[window.expcombobox.get_active()]
    
    parameters = {}
    parameters['version'] = window.version
    parameters.update(window.adc_pot.params)
    parameters.update(window.exp_window.get_params(selection))
    
    return parameters