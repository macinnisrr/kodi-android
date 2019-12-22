#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2011-2014 Martijn Kaijser
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

### import libraries
import lib.common

from tvdb import TVDBProvider
from tmdb import TMDBProvider
from fanarttv import FTV_TVProvider
from fanarttv import FTV_MovieProvider
from mpdk import MP_MovieProvider

__addon__        = lib.common.__addon__

def get_providers():
    movie_providers = []
    tv_providers = []
    musicvideo_providers = []
    providers = {}

    tv_providers.append(TVDBProvider())
    tv_providers.append(FTV_TVProvider())
    
    if __addon__.getSetting("provider_tmdb") == 'true':
        movie_providers.append(TMDBProvider())
    if __addon__.getSetting("provider_fanarttv") == 'true':
        movie_providers.append(FTV_MovieProvider())
    if __addon__.getSetting("provider_mpdk") == 'true':
        movie_providers.append(MP_MovieProvider())
    
    musicvideo_providers.append(TMDBProvider())

    providers['movie_providers'] = movie_providers
    providers['tv_providers'] = tv_providers
    providers['musicvideo_providers'] = musicvideo_providers

    return providers