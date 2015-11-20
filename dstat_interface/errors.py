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

class Error(Exception):
    """Copies Exception class"""
    pass

class InputError(Error):
    """Exception raised for errors in the input. Extends Error class.
        
    Attributes:
        expr -- input expression in which the error occurred
        msg  -- error message
    """
    
    def __init__(self, expr, msg):
        self.expr = expr
        self.msg = msg

class VarError(Error):
    """Exception raised for internal variable errors. Extends Error class.
        
    Attributes:
        var -- var in which the error occurred
        msg  -- error message
    """
    
    def __init__(self, var, msg):
        self.var = var
        self.msg = msg