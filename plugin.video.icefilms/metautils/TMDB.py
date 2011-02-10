# Credits: Daledude
# Awesome efficient lightweight code.

import simplejson
import urllib
#from pprint import pprint


class TMDB(object):
    def __init__(self, api_key='b91e899ce561dd19695340c3b26e0a02', view='json', lang='en'):
        #view = yaml json xml
        self.view = view
        self.lang = lang
        self.api_key = api_key
        self.url_prefix = 'http://api.themoviedb.org/2.1'


    def _do_request(self, method, values):
        url = "%s/%s/%s/%s/%s/%s" % (self.url_prefix, method, self.lang, self.view, self.api_key, values)
        try:
            meta = simplejson.load(urllib.urlopen(url))[0]
        except:
            print "utter failure. probably connection issue"
            return None

        if meta == 'Nothing found.':
            return None
        else:
            return meta


    # video_id is either tmdb or imdb id
    def getVersion(self, video_id):
        return self._do_request('Movie.getVersion', video_id)

    def getInfo(self, tmdb_id):
        return self._do_request('Movie.getInfo', tmdb_id)


    def imdbLookup(self, imdb_id):
        # Movie.imdbLookup doesnt return all the info that Movie.getInfo does like the cast.
        # So do a small lookup with getVersion just to get the tmdb id from the imdb id.
        # Then lookup by the tmdb id to get all the meta.
        try:
            tmdb_id = self.getVersion(imdb_id)['id']
        except:
            return None

        if tmdb_id:
            return self._do_request('Movie.getInfo', tmdb_id)
        else:
            return None


if __name__ == "__main__":
    print "=============="
    tmdb = TMDB('57983e31fb435df4df77afb854740ea9')
    video_meta = tmdb.imdbLookup('tt0499549')
    if not video_meta:
        raise Exception('No meta data found!')

    #pprint(video_meta)

    print "Posters:"
    for poster in video_meta['posters']:
        print "\t%s: %s" % (poster['image']['size'], poster['image']['url'])

    print "\n\n"

    print "Genres:"
    for genre in video_meta['genres']:
        print "\t%s: %s" % (genre['name'], genre['url'])

    print "\n\n"

    print "Cast:"
    for cast in video_meta['cast']:
        print "\t%s: %s" % (cast['name'], cast['job'])

    print "\n\n"

    print "Studios:"
    for studio in video_meta['studios']:
        print "\t%s" % studio['name']
