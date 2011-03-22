'''
These classes cache non-existant metadata from TheMovieDB and TVDB.
It uses sqlite databases.

Currently supports only TheMovieDB, but is scheduled to support TVDB.

It uses themoviedb JSON api class and TVDB XML api class.
For TVDB it currently uses a modified version of 
Python API by James Smith (http://loopj.com)
They can both be found in the same folder.

*Metahandlers created for Icefilms addon Release v1.0.0

*Credits: Daledude / Anarchintosh / WestCoast13 

*Last Updated: 19th/March/2011
    
*To-Do:
- write a clean database function (correct imgs_prepacked by checking if the images actually exist)
  for pre-packed container creator. also retry any downloads that failed.
  also, if  database has just been created for pre-packed container, purge all images are not referenced in database.
- split into two files; containerhandlers.py and metadata.py


'''

import os
from pprint import pprint
import re
import sys
import urllib
import urllib2
import cStringIO
import string
import shutil
import clean_dirs

try:
    import xbmc
except:
    print 'Not running under xbmc; install container function unavaliable.'
    xbmc_imported=False
else:
    xbmc_imported=True
            

from TMDB import TMDB
#necessary to make it work on python 2.4 and 2.7
try:
    from pysqlite2 import dbapi2 as sqlite
except:
    from sqlite3 import dbapi2 as sqlite



def get_dir(mypath, dirname):
    #...creates sub-directories if they are not found.
    subpath = os.path.join(mypath, dirname)
    if not os.path.exists(subpath):
        os.makedirs(subpath)
    return subpath

def bool2string(myinput):
    #neatens up usage of preparezip flag.
    if myinput is False:
        myoutput = 'false'
        return myoutput
    elif myinput is True:
        myoutput = 'true'
        return myoutput

def Movie_URL_List():
        iceurl='http://www.icefilms.info/'
        mvurl=iceurl+'movies/a-z/'

        finallist=[]

        #Generate A-Z icefilms movie url list and return it
        AZ=list([chr(i) for i in xrange(ord('A'), ord('Z')+1)])
        AZ.append('1')
        for theletter in AZ:
                myurl=mvurl+theletter
                finallist.append(myurl)

        #append the urls of the other categories
        finallist.append(iceurl+'music/a-z/1')
        finallist.append(iceurl+'standup/a-z/1')
        finallist.append(iceurl+'other/a-z/1')

        return finallist

def GetURL(url):
    #print 'processing url: '+url
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')       
    response = urllib2.urlopen(req)
    link=response.read()
    response.close()
    return link

def cleanUnicode(string):   
    try:
        #string = string.replace('\\xc3', '?') 
        #fixed_string = string.replace("'","").replace(unicode(u'\u201c'), '"').replace(unicode(u'\u201d'), '"').replace(unicode(u'\u2019'),'').replace(unicode(u'\u2026'),'...').replace(unicode(u'\u2018'),'').replace(unicode(u'\u2013'),'-')
        
        #to-check if we need only this to solve unicode problems
        fixed_string = unicodedata.normalize('NFKD', string).encode('ascii','ignore')
        #print 'THE STRING:',fixed_string
        return fixed_string
    except:
        return string

class MetaContainer:       

    def Create_Icefilms_Container(self,outpath):

        #create container working directory
        workdir=os.path.join(outpath,'Generated Icefilms Container')
        if not os.path.exists(workdir):
            os.makedirs(workdir)
        print 'BUILDING CONTAINER IN:',workdir

        #Initialise meta class, set it to download images.
        meta=MovieMetaData(workdir, preparezip=True)

        #code to scrape A-Z of all movies on icefilms.
        mvinks=Movie_URL_List()
        for myaz in mvinks:
            print 'GETTING METADATA FOR ALL ENTRIES ON: '+myaz
            link=GetURL(myaz)
            match=re.compile('<a name=i id=(.+?)></a><img class=star><a href=/(.+?)>(.+?)<br>').findall(link)

            #For all results run the class
            for imdb_id,url,name in match:
                meta.get_movie_meta(imdb_id)

        print 'Container Making is Finished'

        print 'Cleaning image directory of empty sub-directories [Running clean_dirs.py]'
        cd=clean_dirs.DirCleaner()
        mvcovers=os.path.join(workdir,'meta_caches','themoviedb','covers')
        cd.DelEmptyFolders(mvcovers)

    def _del_metadir(self,path):
        #pass me the path the meta_caches is in

        meta_caches=os.path.join(path,'meta_caches')
        
        #Nuke the old meta_caches folder (if it exists) and install this meta_caches folder.
        #Will only ever delete a meta_caches folder, so is farly safe (won't delete anything it is fed)

        if os.path.exists(meta_caches):
                try:
                    shutil.rmtree(meta_caches)
                except:
                    print 'Failed to delete old meta'
                    return False
                else:
                    print 'deleted old meta'
                    return True

    def _del_path(self,path):

        if os.path.exists(path):
                try:
                    shutil.rmtree(path)
                except:
                    print 'Failed to delete old meta'
                    return False
                else:
                    print 'deleted old meta'
                    return True

    def _extract_zip(self,src,dest):
            try:
                print 'Extracting '+str(src)+' to '+str(dest)
                #make sure there are no double slashes in paths
                src=os.path.normpath(src)
                dest=os.path.normpath(dest) 

                #Unzip
                xbmc.executebuiltin("XBMC.Extract("+src+","+dest+")")

            except:
                print 'Extraction failed!'

            else:                
                print 'Extraction success!'
                    
                

        
    def Install_Icefilms_Container(self,workingdir,containerpath,dbtype,installtype):

        #NOTE: This function is handled by higher level functions in the Default.py
        
        if xbmc_imported==True:

            if dbtype=='tvdb' or dbtype=='themoviedb':

                if installtype == 'database' or installtype == 'covers' or installtype == 'backdrops':

                    meta_caches=os.path.join(workingdir,'meta_caches')
                    cachepath=os.path.join(meta_caches,dbtype)

                    if not os.path.exists(meta_caches):
                        #create the meta folders if they do not exist
                        make_dirs(workingdir)

                    if installtype=='database':
                        #delete old db files
                        if dbtype=='themoviedb':
                            try:
                                os.remove(os.path.join(cachepath,'movie_cache.db'))
                            except:
                                pass

                        #extract the db zip to 'themoviedb' or 'TVDB'
                        self._extract_zip(containerpath,cachepath)

                    if installtype=='covers' or installtype=='backdrops':
                        #delete old folders
                        deleted=self._del_path(os.path.join(cachepath,installtype))

                        #extract the covers or backdrops folder zip to 'themoviedb' or 'TVDB'
                        if deleted == True:
                                self._extract_zip(containerpath,cachepath)

                else:
                    print 'not a valid installtype:',installtype
                    return False

            else:
                print 'not a valid dbtype:',dbtype
                return False
        else:                          
            print 'Not running under xbmc :( install container function unavaliable.'







    def oldInstall_Icefilms_Container(self,containerpath,installpath,installtype):

        #old code
        
        #NOTE: This function is handled by higher level functions in the Default.py
        #      ie. will be called several times, as a meta *update* involves updating databases and images.
        #      (this is not the case for first metacontainer, which is just one zip file) 

        try:
            import xbmc
        except:
            print 'Not running under xbmc; install container function unavaliable.'
            return False
        else:
            try:
                #Unzip container to temp folder
                tempdir=os.path.normpath(os.path.join(installpath,'temp'))
                if not os.path.exists(tempdir):
                    os.makedirs(tempdir)
                containerpath=os.path.normpath(containerpath)

                xbmc.executebuiltin("XBMC.Extract("+containerpath+","+tempdir+")")
            except:
                print 'Extraction failed!'
                return False
            else:                
                #If extraction is successful;
                temp_meta=os.path.join(tempdir,'meta_caches')
                dest_meta=os.path.join(installpath,'meta_caches')

                if installtype == 'initial':                   
                    #Nuke the old meta_caches folder (if it exists) and install this meta_caches folder.
                    #Will only ever delete a meta_caches folder, so is farly safe (won't delete anything it is fed)
                    if os.path.exists(dest_meta):
                        try:
                            shutil.rmtree(dest_meta)
                        except:
                            print 'Failed to delete old meta'
                            return False
                        else:
                            try:
                                time.sleep(1)
                                SetPermissions(tempdir)
                                
                                shutil.move(temp_meta,installpath)
                            except:
                                print 'failed to move the meta to destination'
                                return False
                    elif not os.path.exists(dest_meta):
                            try:
                                time.sleep(1)
                                
                                SetPermissions(tempdir)
                                
                                shutil.move(temp_meta,installpath)
                            except:
                                print 'failed to move the meta to destination...'
                                return False

                elif installtype == 'images':
                #Merge the images from container with the user's current image folder.
                #THIS WILL BE ADDED IN A FUTURE RELEASE
                    pass

                elif installtype == 'databases':
                #Nuke old database files and install the container's database files, leave images untouched.
                #THIS WILL BE ADDED IN A FUTURE RELEASE
                    pass

def make_dirs(path):
        # make the necessary directories, without having to initialise the class (and connect to db etc)
        mainpath = get_dir(path, 'meta_caches')

        tvpath = get_dir(mainpath, 'tvdb')
        tvcovers = get_dir(tvpath, 'covers')
        tvbackdrops = get_dir(tvpath, 'backdrops')

        mvpath = get_dir(mainpath, 'themoviedb')
        mvcovers = get_dir(mvpath, 'covers')
        mvbackdrops = get_dir(mvpath, 'backdrops')

class MovieMetaData:
    def __init__(self, path, preparezip=False):
        #this init auto-constructs necessary folder hierarchies.

        self.mainpath = get_dir(path, 'meta_caches')

        # control whether class is being used to prepare pre-packaged .zip
        self.classmode = bool2string(preparezip)
        self.videocache = os.path.join(self.mainpath, 'video_cache.db')

        self.tvpath = get_dir(self.mainpath, 'tvdb')
        self.tvcache = os.path.join(self.tvpath, 'tv_cache.db')
        self.tvcovers = get_dir(self.tvpath, 'covers')
        self.tvbackdrops = get_dir(self.tvpath, 'backdrops')

        self.mvpath = get_dir(self.mainpath, 'themoviedb')
        self.mvcache = os.path.join(self.mvpath, 'movie_cache.db')
        self.mvcovers = get_dir(self.mvpath, 'covers')
        self.mvbackdrops = get_dir(self.mvpath, 'backdrops')

        # connect to db at class init and use it globally
        self.dbcon = sqlite.connect(self.videocache)
        self.dbcon.row_factory = sqlite.Row # return results indexed by field names and not numbers so we can convert to dict
        self.dbcur = self.dbcon.cursor()

        # create cache db if it dont exist
        self._cache_create_movie_db()

    # cleanup db when object destroyed
    def __del__(self):
        self.dbcur.close()
        self.dbcon.close()

    def _downloadimages(self,meta,mediatype,imdb_id):
          
          if mediatype=='movies':
               cover_folder=os.path.join(self.mvcovers,imdb_id)

               if not os.path.exists(cover_folder):
                   os.makedirs(cover_folder)

               cover_name=self._picname(meta['cover_url'])
               cover_path = os.path.join(cover_folder, cover_name)

               self._dl_code(meta['cover_url'],cover_path)
               

               #backdrop_name=self._picname(meta['backdrop_url'])
               #backdrop_path = os.path.join(self.mvbackdrops, backdrop_name)

               
               #self._dl_code(meta['backdrop_url'],backdrop_path)
               
          if mediatype=='tvshow':
               outpath = os.path.join(self.tvimgpath, 'hi')
          if mediatype=='episode':
               pass
   
    def _picformat(self,url):
        #get image format from url (ie .jpg)
        picformat = re.split('\.+', url)
        return picformat[-1]

    def _picname(self,url):
        #get image name from url (ie my_movie_poster.jpg)
        picname = re.split('\/+', url)
        return picname[-1]
         
        
    def _dl_code(self,url,mypath):
        if url.startswith('http://'):
          try:
               req = urllib2.Request(url)
               response = urllib2.urlopen(req)
               data=response.read()
               response.close()
               fh = open(mypath, 'wb')
               fh.write(data)  
               fh.close()
               #return True
          except:
              print 'image download failed: ',url
              #return False
        else:
            if url is not None:
                print 'not a valid url: ',url
            #return False


#--------------------------------Start of Movie cache handling code ----------------#

        
    def get_movie_meta(self, imdb_id, type, name, ice_id, refresh=False):

        # add the tt if not found. integer aware.
        imdb_id=str(imdb_id)
        if not imdb_id.startswith('tt'):
                imdb_id = "tt%s" % imdb_id

        if refresh:
            meta=None
        else:
            self.check_video_for_url( ice_id, imdb_id, type )
            meta = self._cache_lookup_movie_by_imdb(imdb_id, type)

        if meta is None:
            #print "adding to cache and getting metadata from web"
            meta = self._get_tmdb_meta_data(imdb_id,type, name)
            meta['watched'] = self.get_watched( imdb_id, 'movie')
            #meta['plot']=cleanUnicode(str(meta['plot']))
            self._cache_save_movie_meta(meta, type)

            #if creating a metadata container, download the images.
            if self.classmode is 'true':
                self._downloadimages(meta,'movies',imdb_id)

        if meta is not None:

            #if cache row says there are pre-packed images,..
            if meta['imgs_prepacked'] == 'true':

                    #define the image paths
                    cover_path=os.path.join(self.mvcovers,imdb_id,self._picname(meta['cover_url']))
                    #backdrop_path=os.path.join(self.mvbackdrops,imdb_id,self._picname(meta['backdrop_url']))

                    #if paths exist, replace the urls with paths
                    if self.classmode is 'false':              
                        if os.path.exists(cover_path):
                            meta['cover_url'] = cover_path
                        #if os.path.exists(backdrop_path):
                        #    meta['backdrop_url'] = backdrop_path
                        
                    #try some image redownloads if building container
                    elif self.classmode is 'true':                                              
                        if not os.path.exists(cover_path):
                                self._downloadimages(meta,'movies',imdb_id)

                        #if not os.path.exists(backdrop_path):
                        #        self._downloadimages(meta,'movies',imdb_id)

        #Clean some unicode stuff
        try:
            meta['plot']=cleanUnicode(str(meta['plot']))
        except:
            print 'could not clean plot'

            
        #Return the values to XBMC
        return meta
    
    def _cache_create_movie_db(self):
        # split text across lines to make it easier to understand
        self.dbcur.execute("CREATE TABLE IF NOT EXISTS movie_meta ("
                           "imdb_id TEXT, tmdb_id TEXT, name TEXT,"
                           "rating FLOAT, duration INTEGER, plot TEXT,"
                           "mpaa TEXT, premiered TEXT, genres TEXT, studios TEXT,"
                           "thumb_url TEXT, cover_url TEXT,"
                           "trailer_url TEXT, backdrop_url TEXT,"
                           "imgs_prepacked TEXT," # 'true' or 'false'. added to determine whether to load imgs from path not url (ie. if they are included in pre-packaged metadata container).
                           "watched INTEGER,"
                           "UNIQUE(imdb_id)"
                           ");"
        )
        self.dbcur.execute('CREATE INDEX IF NOT EXISTS nameindex on movie_meta (name);')
        
        # split text across lines to make it easier to understand
        self.dbcur.execute("CREATE TABLE IF NOT EXISTS tvshow_meta ("
                           "imdb_id TEXT, tmdb_id TEXT, name TEXT,"
                           "rating FLOAT, duration INTEGER, plot TEXT,"
                           "mpaa TEXT, premiered TEXT, genres TEXT, studios TEXT,"
                           "thumb_url TEXT, cover_url TEXT,"
                           "trailer_url TEXT, backdrop_url TEXT,"
                           "imgs_prepacked TEXT," # 'true' or 'false'. added to determine whether to load imgs from path not url (ie. if they are included in pre-packaged metadata container).
                           "watched INTEGER,"
                           "UNIQUE(imdb_id)"
                           ");"
        )
        self.dbcur.execute('CREATE INDEX IF NOT EXISTS nameindex on tvshow_meta (name);')
        
        # split text across lines to make it easier to understand
        self.dbcur.execute("CREATE TABLE IF NOT EXISTS episode_meta ("
                           "imdb_id TEXT, "
                           "tvdb_id TEXT, "
                           "season TEXT, "
                           "season_num INTEGER, "
                           "episode TEXT, "
                           "episode_num INTEGER, "
                           "episode_id TEXT, "
                           "name TEXT, "
                           "tvdb_name TEXT, "
                           "plot TEXT, "
                           "rating FLOAT, "
                           "aired TEXT, "
                           "poster TEXT, "
                           "watched INTEGER, "
                           "UNIQUE(imdb_id, tvdb_id, season, name)"
                           ");"
        )
        # split text across lines to make it easier to understand
        self.dbcur.execute("CREATE TABLE IF NOT EXISTS season_meta ("
                           "imdb_id TEXT, tmdb_id TEXT, season TEXT,"
                           "cover_url TEXT,"
                           "watched INTEGER,"
                           "UNIQUE(imdb_id, season)"
                           ");"
        )
        
        # split text across lines to make it easier to understand
        self.dbcur.execute("CREATE TABLE  IF NOT EXISTS url"
                            "("
                            "url TEXT,"
                            "type TEXT,"
                            "imdb_id TEXT,"
                            "tvdb_id TEXT,"
                            "season TEXT,"
                            "name TEXT,"
                            "UNIQUE(url)"
                            ");"
        )
        
        #self.dbcur.execute('CREATE INDEX IF NOT EXISTS nameindex on tvshow_meta (name);')

    def _cache_lookup_movie_by_imdb(self, imdb_id, type):
        if type == 'movie':
            table='movie_meta'
        elif type == 'tvshow':
            table='tvshow_meta'
        # select * is easier since we return a dict but may not be efficient.
        self.dbcur.execute("SELECT * FROM " + table + " WHERE imdb_id = '%s'" % imdb_id) #select database row where imdb_id matches
        matchedrow = self.dbcur.fetchone()
        if matchedrow:
                return dict(matchedrow)
        else:
            return None
        
    def check_video_for_url(self, ice_id, imdb_id, type):
        if type == 'movie':
            table='movie_meta'
        elif type == 'tvshow':
            table='tvshow_meta'
        self.dbcur.execute("SELECT * FROM url WHERE url = '%s'" % ice_id )
        matchedrow = self.dbcur.fetchone()
        if matchedrow:
            if matchedrow['imdb_id'] != imdb_id:
                print 'There might be a problem here. We have to update url with the correct imdb_id'
                self.dbcur.execute("UPDATE url SET imdb_id = '%s', type = '%s' WHERE url = '%s' " % ( imdb_id, type, ice_id ) )
                
        else:
            self.dbcur.execute("INSERT INTO url VALUES "
                           "('%s', '%s', '%s', '%s', '%s', '%s' )" % ( ice_id, type, imdb_id, '', '', '' ))
            self.dbcon.commit()
            
    def _cache_save_movie_meta(self, meta, type):
        if type == 'movie':
            table='movie_meta'
        elif type == 'tvshow':
            table='tvshow_meta'
        self.dbcur.execute("SELECT * FROM " + table + " WHERE imdb_id = '%s'" % meta['imdb_id']) #select database row where imdb_id matches
        matchedrow = self.dbcur.fetchone()
        if matchedrow:
                self.dbcur.execute("DELETE FROM " + table + " WHERE imdb_id = '%s'" % meta['imdb_id']) #delete database row where imdb_id matches
        # use named-parameter binding for lazyness
        print meta
        self.dbcur.execute("INSERT INTO " + table + " VALUES "
                           "(:imdb_id, :tmdb_id, :name, :rating, :duration, :plot, :mpaa, :premiered, :genres, :studios, :thumb_url, :cover_url, :trailer_url, :backdrop_url, :imgs_prepacked, :watched)",
                           meta
                           #"('%s', '%s', '%s', %s, %s, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')"
                           #% ( meta['imdb_id'], meta['tmdb_id'],meta['name'],meta['rating'],meta['duration'],meta['plot'],meta['mpaa'],
                           #meta['premiered'],meta['genres'],meta['studios'],meta['thumb_url'],meta['cover_url'],meta['trailer_url'],meta['backdrop_url'],meta['imgs_prepacked'])
        )
        self.dbcon.commit()

    # this will return a dict. it must also return an empty dict when
    # no movie meta info was found from tmdb because we should cache
    # these "None found" entries otherwise we hit tmdb alot.
    
    def _get_tmdb_meta_data(self, imdb_id, type, name):
        #get metadata text using themoviedb api
        tmdb = TMDB()
        md = tmdb.imdbLookup(imdb_id,type,name)
        if md is None:
            # create an empty dict so below will at least populate empty data for the db insert.
            md = {}

        # copy tmdb to our own for conformity and eliminate KeyError.
        # we set a default value for those keys not returned by tmdb.
        meta = {}
        meta['watched'] = 6
        meta['imdb_id'] = imdb_id
        meta['tmdb_id'] = md.get('id', '')
        meta['name'] = name #md.get('name', '')
        meta['rating'] = md.get('rating', 0)
        meta['duration'] = md.get('runtime', 0)
        meta['plot'] = md.get('overview', '')
        meta['mpaa'] = md.get('certification', '')
        meta['premiered'] = md.get('released', '')
        meta['trailer_url'] = md.get('trailer', '')
        #print meta['plot']
        meta['genres'] = ''
        if md.has_key('imdb_genres'):
            meta['genres'] = md.get('imdb_genres', '')
        meta['studios'] = ''
        tmp_gen = []
        tmp_gen = md.get('genres', '')
        for temp in tmp_gen:
            if meta['genres'] == '':
                meta['genres'] = temp.get('name','')
            else:
                meta['genres'] = meta['genres'] + ' / ' + temp.get('name','')
        print "My genres are : **************  " + meta['genres']
        
        if md.has_key('tvdb_studios'):
            meta['studios'] = md.get('tvdb_studios', '')
        try:
            meta['studios'] = (md.get('studios', '')[0])['name']
        except:
            try:
                meta['studios'] = (md.get('studios', '')[1])['name']
            except:
                try:
                    meta['studios'] = (md.get('studios', '')[2])['name']
                except:
                    try:    
                        meta['studios'] = (md.get('studios', '')[3])['name']
                    except:
                        #print 'studios failed: ',md.get('studios', '')
                        pass
                        

        #meta['cast'] = md.get('cast', '')
        
        #set whether that database row will be accompanied by pre-packed images.
        meta['imgs_prepacked'] = self.classmode

        # define these early cuz they must exist whether posters do or not
        meta['thumb_url'] = ''
        meta['cover_url'] = ''
        if md.has_key('imdb_poster'):
            meta['cover_url'] = md.get('imdb_poster', '')
        if md.has_key('posters'):
            # find first thumb poster url
            for poster in md['posters']:
                if poster['image']['size'] == 'thumb':
                    meta['thumb_url'] = poster['image']['url']
                    break
            # find first cover poster url
            for poster in md['posters']:
                if poster['image']['size'] == 'cover':
                    meta['cover_url'] = poster['image']['url']
                    break

        meta['backdrop_url'] = ''
        if md.has_key('backdrops'):
            # find first original backdrop url
            for backdrop in md['backdrops']:
                if backdrop['image']['size'] == 'original':
                    meta['backdrop_url'] = backdrop['image']['url']
                    break

        return meta

    def get_episode_meta(self, imdb_id, season, episode, refresh=False):

        # add the tt if not found. integer aware.
        imdb_id=str(imdb_id)
        if not imdb_id.startswith('tt'):
                imdb_id = "tt%s" % imdb_id
        print "season is '" + season + "'"
        #clean episode to get episode number
        ep_num = ''
        season_num = ''
        dateSearch = False
        searchTVDB = True
        if season.startswith('Season '):
            season_num=season[7:(len(season)-1)]
            #print season[7:(len(season)-1)]+'x'
            if episode.startswith(season[7:(len(season)-1)]+'x'):
                ep_num=(episode[(len(season)-7):])[:2]
                if ep_num.startswith('0'):
                    ep_num=ep_num[1:]
            else:
                print '##** imdb=' + str(imdb_id) + ' ' + season + ' Episode ' + episode + ' ** Could not find episode number for pattern 1x01 Episode title **##'
                #return None
                ep_num = episode
                searchTVDB = False
        elif len(season) == 4 and episode[6] == ".":
            ep_num=episode[:6]
            season_num=season
            dateSearch=True
        else:
            print '##** imdb=' + str(imdb_id) + ' ' + season + ' Episode ' + episode + ' ** Could not find episode number for pattern MMM DD. Episode title **##'
            #return None
            season_num=season
            ep_num = episode
            searchTVDB = False
        
        print 'imdb=' + str(imdb_id) + ' ' + season + ' Episode ' + episode + ' Episode Num=' + ep_num
        
        if refresh:
            meta=None
        else:
            meta = self._cache_lookup_episode(imdb_id, season, episode)#ep_num)
        
        if meta is None:
            #Find tvdb_id for the TVshow
            tvdb_id = self._get_tvdb_id(imdb_id)
            if tvdb_id == '' or tvdb_id is None:
                print "Could not find TVshow with imdb " + imdb_id
                
                meta = {}
                meta['imdb_id']=imdb_id
                meta['tvdb_id']=''
                meta['season']=season
                meta['season_num'] = 0
                meta['episode']=ep_num
                meta['episode_num'] = 0
                meta['episode_id'] = ''
                meta['name']=episode
                meta['tvdb_name'] = ''
                meta['plot'] = ''
                meta['rating'] = 0
                meta['aired'] = ''
                meta['poster'] = ''
                meta['cover_url']=meta['poster']
                meta['trailer_url']=''
                meta['premiered']=meta['aired']
                meta = self._get_tv_extra(meta)
                meta['watched'] = self.get_watched_episode(meta)
                
                self._cache_save_episode_meta(meta)
                
                return meta
            print 'TVdb is ' + tvdb_id
            
            #print "adding to cache and getting metadata from web"
            if searchTVDB:
                meta = self._get_tvdb_episode_data(tvdb_id, season_num, ep_num, dateSearch)
                if meta is None:
                    meta = {}
                    meta['episode_id'] = ''
                    meta['tvdb_name'] = ''
                    meta['plot'] = ''
                    meta['rating'] = 0
                    meta['aired'] = ''
                    meta['poster'] = ''
                    meta['season_num'] = 0
                    meta['episode_num'] = 0
            else:
                meta = {}
                meta['episode_id'] = ''
                meta['tvdb_name'] = ''
                meta['plot'] = ''
                meta['rating'] = 0
                meta['aired'] = ''
                meta['poster'] = ''
                meta['season_num'] = 0
                meta['episode_num'] = 0
                
            #if meta is not None:
            meta['imdb_id']=imdb_id
            meta['tvdb_id']=tvdb_id
            meta['season']=season
            meta['episode']=ep_num
            meta['name']=episode
            meta['cover_url']=meta['poster']
            meta['trailer_url']=''
            meta['premiered']=meta['aired']
            meta = self._get_tv_extra(meta)
            meta['watched'] = self.get_watched_episode(meta)
            self._cache_save_episode_meta(meta)
            #Clean some unicode stuff
            try:
                meta['plot']=cleanUnicode(str(meta['plot']))
            except:
                print 'could not clean plot'
        
        else:
            print 'episode found on db, meta='+str(meta)
        #Return the values to XBMC
        return meta
    
    def _get_tv_extra(self, meta):
        # select * is easier since we return a dict but may not be efficient.
        self.dbcur.execute("SELECT * FROM tvshow_meta WHERE imdb_id = '%s'" % meta['imdb_id']) #select database row where imdb_id matches
        matchedrow = self.dbcur.fetchone()
        if matchedrow:
            temp = dict(matchedrow)
            meta['genres'] = temp['genres']
            meta['duration'] = temp['duration']
            meta['studios'] = temp['studios']
            meta['mpaa'] = temp['mpaa']
            
            return meta
        else:
            meta['genres'] = ''
            meta['duration'] = 0
            meta['studios'] = ''
            meta['mpaa'] = ''
            return None

    def _get_tvdb_id(self, imdb_id):
        # select * is easier since we return a dict but may not be efficient.
        self.dbcur.execute("SELECT * FROM tvshow_meta WHERE imdb_id = '%s'" % imdb_id) #select database row where imdb_id matches
        matchedrow = self.dbcur.fetchone()
        if matchedrow:
                return dict(matchedrow)['tmdb_id']
        else:
            return None
    
    def _cache_lookup_episode(self, imdb_id, season, episode):

        #sql = "SELECT episode_meta.plot as plot, tvshow_meta.genres as genres, tvshow_meta.duration as duration, episode_meta.aired as premiered, tvshow_meta.studios as studios, tvshow_meta.mpaa as mpaa, episode_meta.imdb_id as imdb_id, episode_meta.rating as rating, episode_meta.season_num as season_num, episode_meta.episode_num as episode_num, '' as trailer_url, episode_meta.season as season, episode_meta.watched as watched, episode_meta.poster as cover_url FROM episode_meta, tvshow_meta WHERE episode_meta.imdb_id = tvshow_meta.imdb_id AND episode_meta.tvdb_id = tvshow_meta.tmdb_id AND episode_meta.imdb_id = '%s' AND season = '%s' AND episode = '%s' " % (imdb_id, season, episode)
        #print sql
        self.dbcur.execute('SELECT '
                           'episode_meta.plot as plot, '
                           'tvshow_meta.genres as genres, '
                           'tvshow_meta.duration as duration, '
                           'episode_meta.aired as premiered, '
                           'tvshow_meta.studios as studios, '
                           'tvshow_meta.mpaa as mpaa, '
                           'episode_meta.imdb_id as imdb_id, '
                           'episode_meta.rating as rating, '
                           'episode_meta.season_num as season_num, '
                           'episode_meta.episode_num as episode_num, '
                           '"" as trailer_url, '
                           'episode_meta.season as season, '
                           'episode_meta.watched as watched, '
                           'episode_meta.poster as cover_url ' 
                           'FROM episode_meta, tvshow_meta WHERE '
                           'episode_meta.imdb_id = tvshow_meta.imdb_id AND '
                           'episode_meta.tvdb_id = tvshow_meta.tmdb_id AND '
                           'episode_meta.imdb_id = "%s" AND season = "%s" AND episode_meta.name = "%s" ' % (imdb_id, season, episode) )
        matchedrow = self.dbcur.fetchone()
        if matchedrow:
            return dict(matchedrow)
        else:
            return None
        
    def _get_tvdb_episode_data(self, tvdb_id, season, episode, dateSearch=False):
        #get metadata text using themoviedb api
        tmdb = TMDB()
        meta = tmdb.tvdbLookup(tvdb_id,season,episode, dateSearch)
        
        return meta
        
    def _cache_save_episode_meta(self, meta):
        #select database row where imdb_id matches
        self.dbcur.execute('SELECT * FROM episode_meta WHERE '
                           'imdb_id = "%s" AND tvdb_id = "%s" AND season = "%s" AND name = "%s"' 
                           % (meta['imdb_id'], meta['tvdb_id'], meta['season'], meta['name']) )
        matchedrow = self.dbcur.fetchone()
        #delete database row where imdb_id matches
        if matchedrow:
                self.dbcur.execute('DELETE FROM episode_meta WHERE '
                           'imdb_id = "%s" AND tvdb_id = "%s" AND season = "%s" AND name = "%s" ' 
                           % (meta['imdb_id'], meta['tvdb_id'], meta['season'], meta['name']) ) 
        # use named-parameter binding for lazyness
        print ' meta before insert ' + str(meta)
        self.dbcur.execute("INSERT INTO episode_meta VALUES "
                           "(:imdb_id, :tvdb_id, :season, :season_num, :episode, :episode_num, :episode_id, :name, :tvdb_name, :plot, :rating, :aired, :poster, :watched)",
                           meta
                           #"('%s', '%s', '%s', %s, %s, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')"
                           #% ( meta['imdb_id'], meta['tmdb_id'],meta['name'],meta['rating'],meta['duration'],meta['plot'],meta['mpaa'],
                           #meta['premiered'],meta['genres'],meta['studios'],meta['thumb_url'],meta['cover_url'],meta['trailer_url'],meta['backdrop_url'],meta['imgs_prepacked'])
        )
        print 'after insert'
        self.dbcon.commit()
        print 'after commit'

    def change_watched(self, imdb_id, videoType, name, season):
        # add the tt if not found. integer aware.
        imdb_id=str(imdb_id)
        if not imdb_id.startswith('tt'):
            imdb_id = "tt%s" % imdb_id
                
        if videoType == 'movie' or videoType == 'tvshow':
            watched = self.get_watched(imdb_id, videoType)
            if watched == 6:
                self.update_watched(imdb_id, videoType, 7)
            else:
                self.update_watched(imdb_id, videoType, 6)
        elif videoType == 'episode':
            tvdb_id = self._get_tvdb_id(imdb_id)
            if tvdb_id is None:
                tvdb_id = ''
            tmp_meta = {}
            tmp_meta['imdb_id'] = imdb_id
            tmp_meta['tvdb_id'] = tvdb_id 
            tmp_meta['season']  = season
            tmp_meta['name']    = name
            watched = self.get_watched_episode(tmp_meta)
            if watched == 6:
                self.update_watched(imdb_id, videoType, 7, name=name, season=season, tvdb_id=tvdb_id)
            else:
                self.update_watched(imdb_id, videoType, 6, name=name, season=season, tvdb_id=tvdb_id)
                
    
    def update_watched(self, imdb_id, videoType, new_value, name='', season='', tvdb_id=''):
        if videoType == 'movie':
            sql="UPDATE movie_meta SET watched = " + str(new_value) + " WHERE imdb_id = '" + imdb_id + "'" 
        elif videoType == 'tvshow':
            sql="UPDATE tvshow_meta SET watched = " + str(new_value) + " WHERE imdb_id = '" + imdb_id + "'"
        elif videoType == 'episode':
            sql='UPDATE episode_meta SET watched = ' + str(new_value) + ' WHERE imdb_id = "' + imdb_id + '" AND tvdb_id = "' + tvdb_id + '" AND season = "' + season + '" AND name = "' + name + '" '
            print sql
        else: # Something went really wrong
            return None
        
        self.dbcur.execute(sql)
        self.dbcon.commit()
    
    def update_trailer(self, imdb_id, type, trailer):
        if type == 'movie':
            table='movie_meta'
        elif type == 'tvshow':
            table='tvshow_meta'
        
        # add the tt if not found. integer aware.
        imdb_id=str(imdb_id)
        if not imdb_id.startswith('tt'):
                imdb_id = "tt%s" % imdb_id
                
        self.dbcur.execute("UPDATE " + table + " set trailer_url='" + trailer + "' "
                           " WHERE imdb_id = '" + imdb_id + "' " )
        self.dbcon.commit()
    
    def get_watched(self, imdb_id, type):
        if type == 'movie':
            table='movie_meta'
        elif type == 'tvshow':
            table='tvshow_meta'
        
        # select * is easier since we return a dict but may not be efficient.
        self.dbcur.execute("SELECT * FROM " + table + " WHERE imdb_id = '%s'" % imdb_id)
        matchedrow = self.dbcur.fetchone()
        if matchedrow:
                return dict(matchedrow)['watched']
        else:
            return 6
        
    def get_watched_episode(self, meta):
        # select * is easier since we return a dict but may not be efficient.
        self.dbcur.execute('SELECT * FROM episode_meta WHERE ' +
                           'imdb_id = "%s" AND tvdb_id = "%s" AND season = "%s" AND name = "%s" ' 
                           % (meta['imdb_id'], meta['tvdb_id'], meta['season'], meta['name']) )
        matchedrow = self.dbcur.fetchone()
        if matchedrow:
                return dict(matchedrow)['watched']
        else:
            return 6
    
    def findCover(self, season, images):
        cover_url = ''
        
        match=re.compile('Season (.+?) ').findall(season)
        if len(match) > 0:
            season_num = match[0]
        else:
            print 'Could not match pattern for Season'
            return cover_url
        
        for image in images:
            (banner_url, banner_type, banner_season) = image
            if banner_season == season_num and banner_type == 'season':
                cover_url = banner_url
                break
        
        return cover_url
    
    def getSeasonCover(self, imdb_id, seasons, refresh=False):
        # add the tt if not found. integer aware.
        imdb_id=str(imdb_id)
        if not imdb_id.startswith('tt'):
                imdb_id = "tt%s" % imdb_id
                
        coversList = []
        tvdb_id = self._get_tvdb_id(imdb_id)
        images  = None
        if refresh == False:
            for season in seasons:
                meta = self._cache_lookup_season(imdb_id, season)
                if meta is None:
                    meta = {}
                    if tvdb_id is None or tvdb_id == '':
                        meta['cover_url']=''
                    elif images:
                        meta['cover_url']=self.findCover( season, images )
                    else:
                        if len(season) == 4:
                            meta['cover_url']=''
                        else:
                            tmdb = TMDB()
                            images = tmdb.getSeasonPosters(tvdb_id, season)
                            print images
                            meta['cover_url']=self.findCover( season, images )
                            
                    meta['season']=season
                    meta['tvdb_id'] = tvdb_id
                    meta['imdb_id'] = imdb_id
                    meta['watched'] = 6
                    
                    self._cache_save_season_meta(meta)
                
                print meta['season'] + ' ' + meta['cover_url']        
                coversList.append(meta)
            
        return coversList
    
    def _cache_lookup_season(self, imdb_id, season):
        #select database row where imdb_id and season matches
        self.dbcur.execute("SELECT * FROM season_meta WHERE imdb_id = '%s' AND season ='%s' " 
                           % ( imdb_id, season ) )
        matchedrow = self.dbcur.fetchone()
        if matchedrow:
            return dict(matchedrow)
        else:
            return None
    
    def _cache_save_season_meta(self, meta):
        #select database row where imdb_id matches
        self.dbcur.execute("SELECT * FROM season_meta WHERE imdb_id = '%s' AND season ='%s' " 
                           % ( meta['imdb_id'], meta['season'] ) ) 
        matchedrow = self.dbcur.fetchone()
        if matchedrow:
            self.dbcur.execute("DELETE FROM season_meta WHERE imdb_id = '%s' AND season ='%s' " 
                               % ( meta['imdb_id'], meta['season'] ) )
        # use named-parameter binding for lazyness
        print meta
        self.dbcur.execute("INSERT INTO season_meta VALUES "
                           "(:imdb_id, :tvdb_id, :season, :cover_url, :watched)",
                           meta
                           )
        self.dbcon.commit()
    
    def get_movie_meta_by_url(self, ice_id, refresh=False):

        if refresh:
            meta=None
        else:
            meta = self._cache_lookup_by_url(ice_id)

        #Clean some unicode stuff
        try:
            meta['plot']=cleanUnicode(str(meta['plot']))
        except:
            print 'could not clean plot'
            
        #Return the values to XBMC
        return meta
    
    def _cache_lookup_by_url(self, ice_id):
        
        # select * is easier since we return a dict but may not be efficient.
        self.dbcur.execute("SELECT * FROM url WHERE url = '%s'" % ice_id)
        matchedrow = self.dbcur.fetchone()
        if matchedrow:
            print 'something found'
            type = dict(matchedrow)['type']
            print type
            imdb_id = dict(matchedrow)['imdb_id']
            print imdb_id
            if (type == 'movie' or type == 'tvshow') and imdb_id is not None:
                meta = self._cache_lookup_movie_by_imdb(imdb_id, type)
                return meta
            else:
                return None
        else:
            return None
    
    def refresh_movie_meta(self, imdb_id):
        #print 'Show Overview from TVDB is ' + show.poster_url
        # add the tt if not found. integer aware.
        imdb_id=str(imdb_id)
        if not imdb_id.startswith('tt'):
                imdb_id = "tt%s" % imdb_id

        meta = None #self._cache_lookup_movie_by_imdb(imdb_id)

        if meta is None:
            #print "adding to cache and getting metadata from web"
            meta = self._get_tmdb_meta_data(imdb_id)
            self._cache_save_movie_meta(meta)

            #if creating a metadata container, download the images.
            if self.classmode is 'true':
                self._downloadimages(meta,'movies',imdb_id)

        if meta is not None:

            #if cache row says there are pre-packed images,..
            if meta['imgs_prepacked'] == 'true':

                    #define the image paths
                    cover_path=os.path.join(self.mvcovers,imdb_id,self._picname(meta['cover_url']))
                    #backdrop_path=os.path.join(self.mvbackdrops,imdb_id,self._picname(meta['backdrop_url']))

                    #if paths exist, replace the urls with paths
                    if self.classmode is 'false':              
                        if os.path.exists(cover_path):
                            meta['cover_url'] = cover_path
                        #if os.path.exists(backdrop_path):
                        #    meta['backdrop_url'] = backdrop_path
                        
                    #try some image redownloads if building container
                    elif self.classmode is 'true':                                              
                        if not os.path.exists(cover_path):
                                self._downloadimages(meta,'movies',imdb_id)

                        #if not os.path.exists(backdrop_path):
                        #        self._downloadimages(meta,'movies',imdb_id)

        #Clean some unicode stuff
        try:
            meta['plot']=cleanUnicode(str(meta['plot']))
        except:
            print 'could not clean plot'

            
        #Return the values to XBMC
        return meta
       