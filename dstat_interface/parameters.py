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

from errors import ErrorLogger
_logger = ErrorLogger(sender="dstat-interface-parameters")

class ParametersGroup(object):
    """A set of parameters with associated dict keys and methods
    for setting and reading.
    
    Parameters:
    keys -- ordered list of parameter dict keys
    getters -- ordered list of getter method instances
    setters -- ordered list of setter method instances
    """
    def __init__(self, keys, getters, setters):
        self.dict = zip(keys, getters, setters)

    @property
    def parameters(self):
        self._parameters = {}
        try:
            for i in self.dict:
                key, getter, setter = i
                self._parameters[key] = getter()
            return self._parameters
        except IndexError as e:
            _logger.error("Invalid parameter key: %s" % e, "WAR")
    
    @parameters.setter
    def parameters(self, params):
        try:
            for i in self.dict:
                key, getter, setter = i
                setter(params[key])
        except IndexError as e:
            _logger.error("Invalid parameter key: %s" % e, "WAR")
        

# def load_params(obj_list, params):
#     """Loads parameters into gtk widgets.
#
#     Arguments:
#     obj_list -- List of 2-tuples of key, instance method pairs.
#     params -- dict of parameters
#     """
#     try:
#         for i in obj_list:
#             key, method = i
#             method(params[key])
#     except IndexError as e:
#         _logger.error("Invalid parameter key: %s" % e, "WAR")
#
# def save_params(obj_list):
#     """Saves params to dict.
#
#     Arguments:
#     obj_list
#     """
#     pass
        