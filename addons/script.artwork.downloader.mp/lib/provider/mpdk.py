#import modules
import sys
import urllib
import base64
import hashlib
### import libraries
from lib.language import *
from lib.script_exceptions import NoFanartError
from lib.utils import *
from operator import itemgetter

### get addon 
__localize__    = ( sys.modules[ '__main__' ].__localize__ )
__addon__    = ( sys.modules[ '__main__' ].__addon__ )

API_KEY = 'd03eb128a68aa8516355eb054e47a29a'
API_URL_MOVIE = 'http://passion-xbmc.org/scraper/API/1/Movie.GetArtworks/%s/%s/IMDB/fr/JSON/%s/%s'

IMAGE_TYPES = ['HDLogos',
               'Posters',
               'Fanarts',
               'CDarts',
               'HDClearArts']

class MP_MovieProvider():

    def __init__(self):
        self.name = 'Media-Passion - Movie API'

    def get_image_list(self, media_id, mode):
        username = base64.b64encode( __addon__.getSetting("provider_mpdk_user") )
        password = hashlib.sha1( __addon__.getSetting("provider_mpdk_user").lower() + __addon__.getSetting("provider_mpdk_password") ).hexdigest()
        log(API_URL_MOVIE%(username,password,API_KEY, media_id))
        data = get_data(API_URL_MOVIE%(username,password,API_KEY, media_id), 'json')
        image_list = []
        if data == 'Empty' or not data:
            return image_list
        else:
            # split 'name' and 'data'
            for title, value in data.iteritems():
                for art in IMAGE_TYPES:
                    if value.has_key(art):
                        for item in value[art]:
                            # Check on what type and use the general tag
                            arttypes = {'HDLogos': 'clearlogo',
                                        'Posters': 'poster',
                                        'Fanarts': 'fanart',
                                        'CDarts': 'discart',
                                        'HDClearArts': 'clearart'}
                            if art in ['HDLogos', 'HDClearArts']:
                                size = 'HD'
                            else:
                                size = ''
                            if art == 'Fanarts':
                                type = ['fanart','extrafanart']
                            else:
                                type = [arttypes[art]]
                            if item.get('Lang','') == '':
                                lang = 'n/a'
                            else:
                                lang = item.get('Lang')[:2]
                            # Fill list
                            if (art != "CDarts" or(art == "CDarts" and mode == "gui")):
                                image_list.append({'url': urllib.quote(item.get('URLOriginal'), ':/'),
                                                   'preview': item.get('URLOriginal').replace('main','preview'),
                                                   'id': item.get('IDMedia'),
                                                   'art_type': type,
                                                   'size': size,
                                                   'language': lang,
                                                   'height': int(item.get('Hauteur')),
                                                   'width': int(item.get('Largeur')),
                                                   'rating': item.get('Note',0),
                                                   'votes': item.get('Votes',0),
                                                   'discnumber': '1',
                                                   'disctype': 'n/r',
                                                   'generalinfo': ('%s: %s  |  %s: %sx%s - %s' 
                                                           %( __localize__(32141), get_language(item.get('Lang','n/a')[:2]).capitalize(),
                                                              __localize__(32145), item.get('Largeur'), item.get('Hauteur'),item.get('PoidsNice','')))})
                            else:
                                image_list.append({'url': urllib.quote(item.get('URLOriginal'), ':/'),
                                                   'preview': item.get('URLOriginal').replace('main','preview'),
                                                   'id': item.get('IDMedia'),
                                                   'art_type': type,
                                                   'size': size,
                                                   'language': lang,
                                                   'height': int(item.get('Hauteur')),
                                                   'width': int(item.get('Largeur')),
                                                   'rating': item.get('Note',0),
                                                   'votes': item.get('Votes',0),
                                                   'discnumber': '1',
                                                   'disctype': 'dvd',
                                                   'generalinfo': ('%s: %s  |  %s: %sx%s - %s' 
                                                           %( __localize__(32141), get_language(item.get('Lang','n/a')[:2]).capitalize(),
                                                              __localize__(32145), item.get('Largeur'), item.get('Hauteur'),item.get('PoidsNice','')))})
                                image_list.append({'url': urllib.quote(item.get('URLOriginal'), ':/'),
                                                   'preview': item.get('URLOriginal').replace('main','preview'),
                                                   'id': item.get('IDMedia'),
                                                   'art_type': type,
                                                   'size': size,
                                                   'language': lang,
                                                   'height': int(item.get('Hauteur')),
                                                   'width': int(item.get('Largeur')),
                                                   'rating': item.get('Note',0),
                                                   'votes': item.get('Votes',0),
                                                   'discnumber': '1',
                                                   'disctype': 'bluray',
                                                   'generalinfo': ('%s: %s  |  %s: %sx%s - %s' 
                                                           %( __localize__(32141), get_language(item.get('Lang','n/a')[:2]).capitalize(),
                                                              __localize__(32145), item.get('Largeur'), item.get('Hauteur'),item.get('PoidsNice','')))})
            if image_list == []:
                raise NoFanartError(media_id)
            else:
                # Sort the list before return. Last sort method is primary
                # image_list = sorted(image_list, key=itemgetter('votes'), reverse=True)
                # image_list = sorted(image_list, key=itemgetter('size'), reverse=False)
                # image_list = sorted(image_list, key=itemgetter('language'))
                return image_list