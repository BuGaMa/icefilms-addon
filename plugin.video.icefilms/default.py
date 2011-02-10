#!/usr/bin/python

#Icefilms.info v1.0.0 - anarchintosh / daledude 7/2/2011
# quite convoluted code. needs a good clean for v1.1.0

import sys,os,time
import re
import urllib,urllib2,cookielib,html2text
import xbmc,xbmcplugin,xbmcgui,xbmcaddon
from pysqlite2 import dbapi2 as sqlite

from xgoogle.BeautifulSoup import BeautifulSoup,BeautifulStoneSoup
from xgoogle.search import GoogleSearch
from mega import megaroutines
import clean_dirs
from metautils import metahandlers

def xbmcpath(path,filename):
     translatedpath = os.path.join(xbmc.translatePath( path ), ''+filename+'')
     return translatedpath

       
def Notify(typeq,title,message,times):
     #simplified way to call notifications. common notifications here.
     if title is '':
          title='Icefilms Notification'
     if typeq == 'small':
          if times is '':
               times='5000'
          smallicon=handle_file('smallicon')
          xbmc.executebuiltin("XBMC.Notification("+title+","+message+","+times+","+smallicon+")")
     if typeq == 'big':
          dialog = xbmcgui.Dialog()
          dialog.ok(' '+title+' ', ' '+message+' ')
     if typeq == 'megaalert1':
          ip = xbmc.getIPAddress()
          title='Megaupload Alert for IP '+ip
          message="Either you've reached your daily download limit\n or your IP is already downloading a file."
          dialog = xbmcgui.Dialog()
          dialog.ok(' '+title+' ', ' '+message+' ')
     if typeq == 'megaalert2':
          ip = xbmc.getIPAddress()
          title='Megaupload Info for IP '+ip
          message="No problems! You have not reached your limit."
          dialog = xbmcgui.Dialog()
          dialog.ok(' '+title+' ', ' '+message+' ')


#get path to me
icepath=os.getcwd()

#paths etc need sorting out. do for v1.1.0
icedatapath = 'special://profile/addon_data/plugin.video.icefilms'
metapath = icedatapath+'/mirror_page_meta_cache'
downinfopath = icedatapath+'/downloadinfologs'
transdowninfopath = xbmcpath(downinfopath,'')
transmetapath = xbmcpath(metapath,'')
translatedicedatapath = xbmcpath(icedatapath,'')
art = icepath+'/resources/art'


def handle_file(filename,getmode=''):
     #bad python code to add a get file routine.
     if filename is 'captcha':
          return_file = xbmcpath(icedatapath,'CaptchaChallenge.txt')
     elif filename is 'mirror':
          return_file = xbmcpath(icedatapath,'MirrorPageSource.txt')
     elif filename is 'episodesrc':
          return_file = xbmcpath(icedatapath,'EpisodePageSource.txt')
     elif filename is 'pageurl':
          return_file = xbmcpath(icedatapath,'PageURL.txt')

     elif filename is 'mediapath':
          return_file = xbmcpath(downinfopath,'MediaPath.txt')
     #extra thing to provide show name with year if going via episode list.
     elif filename is 'mediatvshowname':
          return_file = xbmcpath(downinfopath,'TVShowName.txt')
     #extra thing to provide season name.
     elif filename is 'mediatvseasonname':
          return_file = xbmcpath(downinfopath,'TVSeasonName.txt')

     elif filename is 'videoname':
          return_file = xbmcpath(metapath,'VideoName.txt')
     elif filename is 'sourcename':
          return_file = xbmcpath(metapath,'SourceName.txt')
     elif filename is 'description':
          return_file = xbmcpath(metapath,'Description.txt')
     elif filename is 'poster':
          return_file = xbmcpath(metapath,'Poster.txt')
     elif filename is 'mpaa':
          return_file = xbmcpath(metapath,'mpaa.txt')
     elif filename is 'listpic':
          return_file = xbmcpath(metapath,'listpic.txt')

     elif filename is 'smallicon':
          return_file = xbmcpath(art,'smalltransparent2.png')
     elif filename is 'homepage':
          return_file = xbmcpath(art,'homepage.png')
     elif filename is 'movies':
          return_file = xbmcpath(art,'movies.png')
     elif filename is 'music':
          return_file = xbmcpath(art,'music.png')
     elif filename is 'tvshows':
          return_file = xbmcpath(art,'tvshows.png')
     elif filename is 'other':
          return_file = xbmcpath(art,'other.png')
     elif filename is 'search':
          return_file = xbmcpath(art,'search.png')
     elif filename is 'standup':
          return_file = xbmcpath(art,'standup.png')
     elif filename is 'megapic':
          return_file = xbmcpath(art,'megaupload.png')
     elif filename is 'shared2pic':
          return_file = xbmcpath(art,'2shared.png')

     if getmode is '':
          return return_file
     if getmode is 'open':
          try:
               opened_return_file=openfile(return_file)
               return opened_return_file
          except:
               print 'opening failed'


#get settings
selfAddon = xbmcaddon.Addon(id='plugin.video.icefilms')

#useful global strings:
iceurl = 'http://www.icefilms.info/'

def openfile(filename):
     fh = open(filename, 'r')
     contents=fh.read()
     fh.close()
     return contents

def save(filename,contents):  
     fh = open(filename, 'w')
     fh.write(contents)  
     fh.close()

def appendfile(filename,contents):  
     fh = open(filename, 'a')
     fh.write(contents)  
     fh.close()


def DLDirStartup():

  # Startup routines for handling and creating special download directory structure 
  SpecialDirs=selfAddon.getSetting('use-special-structure')

  if SpecialDirs == 'true':
     mypath=str(selfAddon.getSetting('download-folder'))

     if mypath is not '' or mypath is not None:
 
        if os.path.exists(mypath):
          initial_path=os.path.join(mypath,'Icefilms Downloaded Videos')
          tvpath=os.path.join(initial_path,'TV Shows')
          moviepath=os.path.join(initial_path,'Movies')

          tv_path_exists=os.path.exists(tvpath)
          movie_path_exists=os.path.exists(moviepath)

          if tv_path_exists == False or movie_path_exists == False:

            #IF BASE DIRECTORY STRUCTURE DOESN'T EXIST, CREATE IT
            #Also Add README files to TV Show and Movies direcories.
            #(readme files stops folders being deleted when running the DirCleaner)

            if tv_path_exists == False:
               os.makedirs(tvpath)
               tvreadme='Add this folder to your XBMC Library, and set it as TV to scan for metadata with TVDB.'
               tvreadmepath=os.path.join(tvpath,'README.txt')
               save(tvreadmepath,tvreadme)

            if movie_path_exists == False:
               os.makedirs(moviepath)
               moviereadme='Add this folder to your XBMC Library, and set it as Movies to scan for metadata with TheMovieDB.'
               moviereadmepath=os.path.join(moviepath,'README.txt')
               save(moviereadmepath,moviereadme)

          else:
              #IF DIRECTORIES EXIST, CLEAN DIRECTORY STRUCTURE (REMOVE EMPTY DIRECTORIES)
               cl=clean_dirs.DirCleaner()
               cl.DelEmptyFolders(tvpath)
               cl.DelEmptyFolders(moviepath)


def LoginStartup():
     #Get whether user has set an account to use.
     Account = selfAddon.getSetting('megaupload-account')
     
     if Account == 'false':
          print 'Account: '+'no account set'

     elif Account == 'true':
          #check for megaupload login and do it
          mu=megaroutines.megaupload(translatedicedatapath)
          
          megauser = selfAddon.getSetting('megaupload-username')
          megapass = selfAddon.getSetting('megaupload-password')

          login=mu.set_login(megauser,megapass)
                   
          if megapass is not '' and megauser is not '':
               if login is False:
                    print 'Account: '+'login failed'
                    Notify('big','Megaupload','Login failed. Megaupload will load with no account.','')
               elif login is True:
                    print 'Account: '+'login succeeded'
                    HideSuccessfulLogin = selfAddon.getSetting('hide-successful-login-messages')
                    if HideSuccessfulLogin == 'false':
                         Notify('small','Megaupload', 'Account login successful.','')
                         
          if megapass is '' or megauser is '':
               print 'no login details specified, using no account'
               Notify('big','Megaupload','Login failed. Megaupload will load with no account.','')
                                
def ContainerStartup():

     #delete zips from the 'downloaded meta zips' dir that have equivalent text files.
     #have to do this at startup because it is not possible to delete the original file
     #after extracting, because the file is extracted by a built in xbmc function not python
     # (python won't wait until file has finished extracting before going on to run next lines)

     #define dl directory
     dlzips=os.path.join(translatedicedatapath,'downloaded meta zips')
               
     try:
          thefiles=os.listdir(dlzips)
          for thefile in thefiles:
               filestring=str(thefile)
               if filestring.endswith('.txt'):
                    filestring=re.sub('.txt','.zip',filestring)
                    os.remove(os.path.join(dlzips,filestring))
     except:
          print 'could not delete original file!'
     else:
          print 'deleted unnecessary zip.'


                        
     #Quick hack for v1.0.0 --- only run if meta_caches does not exist

     metapath=os.path.join(translatedicedatapath,'meta_caches')
     if not os.path.exists(metapath):

          

          #Movie Meta Container Strings
          mv_date='9/Feb/2011'          
          mv_db='http://www.megaupload.com/?d=U1RTPGQS'
          mv_base='http://www.megaupload.com/?d=CE07S1EJ'
          mv_db_base_size=230
          mv_additional=''
          mv_additional_size=0

          #TV Meta Container Strings
          tv_date=''
          tv_db=''
          tv_base=''
          tv_db_base_size=0
          tv_additional=''
          tv_additional_size=0

          #Offer to download the metadata
     
          dialog = xbmcgui.Dialog()
          ret = dialog.yesno('Download Meta Containers '+mv_date+' ?', 'There is a metadata container avaliable.','Install it to get images and info for movies.', 'Would you like to get it? Its a large '+str(mv_db_base_size)+'MB download.','Remind me later', 'Install')
          if ret==True:
                 
               #download dem files
               get_db_zip=Zip_DL_and_Install(mv_db,'themoviedb','database')
               get_cover_zip=Zip_DL_and_Install(mv_base,'themoviedb','covers')

               #do nice notification
               if get_db_zip==True and get_cover_zip==True:
                    Notify('small','Metacontainer Installation Success','','')
               elif get_db_zip==False or get_cover_zip==False:
                    Notify('small','Metacontainer Installation Failure','','')


def Zip_DL_and_Install(url,dbtype,installtype):

               #define dl directory
               dlzips=os.path.join(translatedicedatapath,'downloaded meta zips')

               #get the download url
               mu=megaroutines.megaupload(translatedicedatapath)
               print 'URL:',url
               thefile=mu.resolve_megaup(url)

               #define the path to save it to
               filepath=os.path.normpath(os.path.join(dlzips,thefile[1]))
          
               print 'FILEPATH: ',filepath
               filepath_exists=os.path.exists(filepath)
               #if zip does not already exist, download from url, with nice display name.
               if filepath_exists==False:
                    print 'downloading zip'
                    Download(thefile[0],filepath,dbtype+' '+installtype)

                    #make a text file with the same name as zip, to act as a very simple download log.
                    textfile=re.sub('.zip','',thefile[1])
                    textfilepath=os.path.join(dlzips,textfile+'.txt')
                    save(textfilepath,' ')
                    
               elif filepath_exists==True:
                    print 'zip already downloaded, attempting extraction'

               print '!!!!handling meta install!!!!'
               mc=metahandlers.MetaContainer()
               install=mc.Install_Icefilms_Container(translatedicedatapath,filepath,dbtype,installtype)
               return install


def Startup_Routines():
     # avoid error on first run if no paths exists, by creating paths
     if not os.path.exists(translatedicedatapath):
          os.makedirs(translatedicedatapath)
     if not os.path.exists(transmetapath):
          os.makedirs(transmetapath)
     if not os.path.exists(transdowninfopath):
          os.makedirs(transdowninfopath)

     dlzips=os.path.join(translatedicedatapath,'downloaded meta zips')
     if not os.path.exists(dlzips):
          os.makedirs(dlzips)
          
     #force refresh addon repositories, to check for updates.
     #xbmc.executebuiltin('UpdateAddonRepos')
     
     # Run the startup routines for special download directory structure 
     DLDirStartup()

     # Run the login startup routines
     LoginStartup()

     # Run the container checking startup routines, if enable meta is set to true
     EnableMeta = selfAddon.getSetting('use-meta')
     if EnableMeta=='true':
          ContainerStartup()


def CATEGORIES():  #  (homescreen of addon)         
          #run startup stuff
          Startup_Routines()
          print 'Homescreen'

          #get necessary paths
          homepage=handle_file('homepage','')
          tvshows=handle_file('tvshows','')
          movies=handle_file('movies','')
          music=handle_file('music','')
          standup=handle_file('standup','')
          other=handle_file('other','')
          search=handle_file('search','')

          #add directories
          HideHomepage = selfAddon.getSetting('hide-homepage')
          
          addDir('TV Shows',iceurl+'tv/a-z/1',50,tvshows)
          addDir('Movies',iceurl+'movies/a-z/1',51,movies)
          addDir('Music',iceurl+'music/a-z/1',52,music)
          addDir('Stand Up Comedy',iceurl+'standup/a-z/1',53,standup)
          addDir('Other',iceurl+'other/a-z/1',54,other)
          if HideHomepage == 'false':
                addDir('Homepage',iceurl+'index',56,homepage)
          addDir('Favourites',iceurl,57,os.path.join(art,'favourites.png'))
          addDir('Search',iceurl,55,search)


def FAVOURITES(url):
          #Favourites folder. This function is not very neat code.
     
          favpath=os.path.join(translatedicedatapath,'Favourites')
          tvfav=os.path.join(favpath,'TV')
          moviefav=os.path.join(favpath,'Movies')
          try:
               tvdircontents=os.listdir(tvfav)
          except:
               tvdircontents=None
          try:
               moviedircontents=os.listdir(moviefav)
          except:
               moviedircontents=None
               
          if tvdircontents == None and moviedircontents == None:
               Notify('big','No Favourites Saved','To save a favourite press the C key on a movie or\n TV Show and select Add To Icefilms Favourites','')

          else:
               #add clear favourites entry
               addExecute('* Clear Favourites Folder *',url,58,os.path.join(art,'deletefavs.png'))

               
               #handler for all tv favourites
               if tvdircontents is not None:
                    #Open all files in tv dir
                    for thefile in tvdircontents:
                         try:
                              filecontents=openfile(os.path.join(tvfav,thefile))

                              splitter=re.split('\|+', filecontents)
                              name=splitter[0]
                              turl=splitter[1]
                              mode=int(splitter[2])

                              addDir(name,turl,mode,'',delfromfav=True)
                         except:
                                   print 'problem adding a tv favourites item'
                         

               #handler for all movie favourites
               if moviedircontents is not None:

                    meta_path=os.path.join(translatedicedatapath,'meta_caches')
                    use_meta=os.path.exists(meta_path)
                    meta_setting = selfAddon.getSetting('use-meta')

                    #add without metadata -- imdb is still passed for use with Add to Favourites
                    if use_meta==False or meta_setting=='false':

                         #Open all files in movie dir
                         for thefile in moviedircontents:
                              try:
                                   filecontents=openfile(os.path.join(moviefav,thefile))

                                   splitter=re.split('\|+', filecontents)
                                   name=splitter[0]
                                   turl=splitter[1]
                                   mode=int(splitter[2])
                                   imdb_id=splitter[3]
                              
                                   #don't add with meta
                                   addDir(name,turl,mode,'',delfromfav=True)
                              except:
                                   print 'problem adding a movie favourites item'

                    #add with metadata -- imdb is still passed for use with Add to Favourites
                    if use_meta==True or meta_setting=='true':

                         #initialise meta class before loop
                         metaget=metahandlers.MovieMetaData(translatedicedatapath)

                         #do these steps for all files in movie dir
                         for thefile in moviedircontents:
                              try:
                                   filecontents=openfile(os.path.join(moviefav,thefile))

                                   splitter=re.split('\|+', filecontents)

                                   name=splitter[0]
                                   turl=splitter[1]
                                   mode=int(splitter[2])
                                   imdb_id=splitter[3]

                                   #return the metadata dictionary  
                                   meta=metaget.get_movie_meta(imdb_id)

                                   if meta is None:
                                        #add directories without meta
                                        addDir(name,turl,mode,'',delfromfav=True)

                                   if meta is not None:
                                        #add directories with meta
                                        addDir(name,url,100,'',metainfo=meta,delfromfav=True,imdb='tt'+str(imdb_id))
                              except:
                                   print 'problem adding a movie favourites item'


def URL_TYPE(url):
     #Check whether url is a tv episode list or movie/mirrorpage
     if url.startswith(iceurl+'ip'):
               print 'url is a mirror page url'
               return 'mirrors'
     elif url.startswith(iceurl+'tv/series'):
               print 'url is a tv ep list url'
               return 'episodes'     

def METAFIXER(url):
     #Icefilms urls passed to me will have their imdb numbers returned.
     source=GetURL(url)

     url_type=URL_TYPE(url)

     if url_type=='mirrors':
               #Movie
               match=re.compile('<a class=iframe href=http://www.imdb.com/title/(.+?)/ ').findall(source)
               return match[0]

     elif url_type=='episodes':
               #TV
               match=re.compile('href="http://www.imdb.com/title/(.+?)/"').findall(source)
               return match[0]
     
     
def ADD_TO_FAVOURITES(name,url,imdbnum):
     #Creates a new text file in favourites folder. The text file is named after the items name, and contains the name, url and relevant mode.

     if name is not None and url is not None:

          #Set favourites path, and create it if it does'nt exist.
          favpath=os.path.join(translatedicedatapath,'Favourites')
          tvfav=os.path.join(favpath,'TV')
          moviefav=os.path.join(favpath,'Movies')
          
          try:
               os.makedirs(tvfav)
          except:
               pass
          try:
               os.makedirs(moviefav)
          except:
               pass

          print 'NAME:',name,'URL:',url,'IMDB NUMBER:',imdbnum

          #Check what kind of url it is and set themode and savepath (helpful for metadata) accordingly
          url_type=URL_TYPE(url)

          if url_type=='mirrors':
               themode='100'
               savepath=moviefav
               
               #currently only run metafixer on non-tv pages.
               if imdbnum == 'nothing':
                    imdbnum=METAFIXER(url)

          elif url_type=='episodes':
               themode='12'
               savepath=tvfav

          #Delete HD 720p entry from filename. using name as filename makes favourites appear alphabetically.
          adjustedname=re.sub(' \*HD 720p\*','', name)
         
          #Save the new favourite if it does not exist.
          NewFavFile=os.path.join(savepath,adjustedname+'.txt')
          if not os.path.exists(NewFavFile):

               #Use | as separators that can be used by re.split when reading favourites folder.
               favcontents=name+'|'+url+'|'+themode+'|'+imdbnum
               save(NewFavFile,favcontents)

     else:
          print 'name or url is none:'
          print 'NAME: ',name
          print 'URL: ',url


     
def DELETE_FROM_FAVOURITES(name,url):
     #Deletes HD 720p entry from filename
     name=re.sub(' \*HD 720p\*','', name)
          
     favpath=os.path.join(translatedicedatapath,'Favourites')

     url_type=URL_TYPE(url)

     if url_type=='mirrors':
          itempath=os.path.join(favpath,'Movies',name+'.txt')

     elif url_type=='episodes':
          itempath=os.path.join(favpath,'TV',name+'.txt')

     if os.path.exists(itempath):
          os.remove(itempath)

def CLEAR_FAVOURITES(url):
     
     dialog = xbmcgui.Dialog()
     ret = dialog.yesno('WARNING!', 'Delete all your favourites?','','','Cancel','Go Nuclear')
     if ret==True:
          import shutil
          favpath=os.path.join(translatedicedatapath,'Favourites')
          tvfav=os.path.join(favpath,'TV')
          moviefav=os.path.join(favpath,'Movies')
          try:
               shutil.rmtree(tvfav)
          except:
               pass
          try:
               shutil.rmtree(moviefav)
          except:
               pass

def ICEHOMEPAGE(url):
        addDir('Recently Added',iceurl+'index',60,os.path.join(art,'recently added.png'))
        addDir('Latest Releases',iceurl+'index',61,os.path.join(art,'latest releases.png'))
        addDir('Being Watched Now',iceurl+'index',62,os.path.join(art,'being watched now.png'))

        #delete tv show name file
        tvshowname=handle_file('mediatvshowname','')
        try:
               os.remove(tvshowname)
        except:
               pass

def RECENT(url):
        link=GetURL(url)
        homepage=re.compile('<h1>Recently Added</h1>(.+?)<h1>Statistics</h1>').findall(link)
        for scrape in homepage:
                scrape='<h1>Recently Added</h1>'+scrape+'<h1>Statistics</h1>'
                recadd=re.compile('<h1>Recently Added</h1>(.+?)<h1>Latest Releases</h1>').findall(scrape)
                for scraped in recadd:
                        mirlinks=re.compile('<a href=(.+?)>(.+?)</a>').findall(scraped)
                        for url,name in mirlinks:
                                url='http://www.icefilms.info'+url
                                name=CLEANUP(name)
                                addDir(name,url,100,'',disablefav=True)
    
def LATEST(url):
        link=GetURL(url)
        homepage=re.compile('<h1>Recently Added</h1>(.+?)<h1>Statistics</h1>').findall(link)
        for scrape in homepage:
                scrape='<h1>Recently Added</h1>'+scrape+'<h1>Statistics</h1>'
                latrel=re.compile('<h1>Latest Releases</h1>(.+?)<h1>Being Watched Now</h1>').findall(scrape)
                for scraped in latrel:
                        mirlinks=re.compile('<a href=(.+?)>(.+?)</a>').findall(scraped)
                        for url,name in mirlinks:
                                url='http://www.icefilms.info'+url
                                name=CLEANUP(name)
                                addDir(name,url,100,'',disablefav=True)

def WATCHINGNOW(url):
        link=GetURL(url)
        homepage=re.compile('<h1>Recently Added</h1>(.+?)<h1>Statistics</h1>').findall(link)
        for scrape in homepage:
                scrapy='<h1>Recently Added</h1>'+scrape+'<h1>Statistics</h1>'
                watnow=re.compile('<h1>Being Watched Now</h1>(.+?)<h1>Statistics</h1>').findall(scrapy)
                for scraped in watnow:
                        mirlinks=re.compile('href=(.+?)>(.+?)</a>').findall(scraped)
                        for url,name in mirlinks:
                                url='http://www.icefilms.info'+url
                                name=CLEANUP(name)
                                addDir(name,url,100,'',disablefav=True)    

def SEARCH(url):
     kb = xbmc.Keyboard('', 'Search Icefilms.info', False)
     kb.doModal()
     if (kb.isConfirmed()):
          search = kb.getText()
          if search is not '':
             tvshowname=handle_file('mediatvshowname','')
             seasonname=handle_file('mediatvseasonname','')
             DoEpListSearch(search)
             DoSearch(search,0)
             DoSearch(search,1)
             DoSearch(search,2)
             #delete tv show name file, do the same for season name file
             try:
                  os.remove(tvshowname)
             except:
                  pass
             try:
                  os.remove(seasonname)
             except:
                  pass
               
                               
def DoSearch(search,page):        
        gs = GoogleSearch('site:http://www.icefilms.info/ip '+search+'')
        gs.results_per_page = 25
        gs.page = page
        results = gs.get_results()
        for res in results:
                name=res.title.encode('utf8')
                name=CLEANSEARCH(name)
                url=res.url.encode('utf8')
                addDir(name,url,100,'')

def DoEpListSearch(search):
               tvurl='http://www.icefilms.info/tv/series'              

               # use urllib.quote_plus() on search instead of re.sub ?
               searcher=urllib.quote_plus(search)
               #searcher=re.sub(' ','+',search)
               url='http://www.google.com/search?hl=en&q=site:'+tvurl+'+'+searcher+'&btnG=Search&aq=f&aqi=&aql=&oq='
               link=GetURL(url)

               match=re.compile('<h3 class="r"><a href="'+tvurl+'(.+?)"(.+?)">(.+?)</h3>').findall(link)
               
               for myurl,interim,name in match:
                    if len(interim) < 80:
                         name=CLEANSEARCH(name)                              
                         hasnameintitle=re.search(search,name,re.IGNORECASE)
                         if hasnameintitle is not None:
                              myurl=tvurl+myurl
                              myurl=re.sub('&amp;','',myurl)
                              addDir(name,myurl,12,'')

     
def CLEANSEARCH(name):        
        name=re.sub('<em>','',name)
        name=re.sub('</em>','',name)
        name=re.sub('DivX - icefilms.info','',name)
        name=re.sub('</a>','',name)
        name=re.sub('<b>...</b>','',name)
        name=re.sub('- icefilms.info','',name)
        name=re.sub('.info','',name)
        name=re.sub('- icefilms','',name)
        name=re.sub(' -icefilms','',name)
        name=re.sub('-icefilms','',name)
        name=re.sub('icefilms','',name)
        name=re.sub('DivX','',name)
        name=re.sub('&#39;',"'",name)
        name=re.sub('&amp;','&',name)
        name=re.sub('-  Episode  List','- Episode List',name)
        name=re.sub('-Episode  List','- Episode List',name)
        return name

def TVCATEGORIES(url):
        caturl = iceurl+'tv/'        
        setmode = '11'
        addDir('A-Z Directories',caturl+'a-z/1',10,os.path.join(art,'az directories.png'))            
        ADDITIONALCATS(setmode,caturl)
        
def MOVIECATEGORIES(url):
        caturl = iceurl+'movies/'        
        setmode = '2'
        addDir('A-Z Directories',caturl+'a-z/1',1,os.path.join(art,'az directories.png'))
        ADDITIONALCATS(setmode,caturl)
        
def MUSICCATEGORIES(url):
        caturl = iceurl+'music/'        
        setmode = '2'
        addDir('A-Z List',caturl+'a-z/1',setmode,os.path.join(art,'az lists.png'))
        ADDITIONALCATS(setmode,caturl)


def STANDUPCATEGORIES(url):
        caturl = iceurl+'standup/'        
        setmode = '2'
        addDir('A-Z List',caturl+'a-z/1',setmode,os.path.join(art,'az lists.png'))
        ADDITIONALCATS(setmode,caturl)

def OTHERCATEGORIES(url):
        caturl = iceurl+'other/'        
        setmode = '2'
        addDir('A-Z List',caturl+'a-z/1',setmode,os.path.join(art,'az lists.png'))
        ADDITIONALCATS(setmode,caturl)

def ADDITIONALCATS(setmode,caturl):
        if caturl == iceurl+'movies/':
             addDir('HD 720p',caturl,63,os.path.join(art,'HD 720p.png'))
        PopRatLat(setmode,caturl,'1')
        addDir('Genres',caturl,64,os.path.join(art,'genres.png'))

def PopRatLat(modeset,caturl,genre):
        if caturl == iceurl+'tv/':
             setmode = '11'
        elif caturl is not iceurl+'tv/':
             setmode = '2'       
        addDir('Popular',caturl+'popular/'+genre,setmode,os.path.join(art,'popular.png'))
        addDir('Highly Rated',caturl+'rating/'+genre,setmode,os.path.join(art,'highly rated.png'))
        addDir('Latest Releases',caturl+'release/'+genre,setmode,os.path.join(art,'latest releases.png'))
        addDir('Recently Added',caturl+'added/'+genre,setmode,os.path.join(art,'recently added.png'))

def HD720pCat(url):
        PopRatLat('2',url,'hd')

def Genres(url):
        addDir('Action',url,70,'')
        addDir('Animation',url,71,'')
        addDir('Comedy',url,72,'')
        addDir('Documentary',url,73,'')
        addDir('Drama',url,74,'')
        addDir('Family',url,75,'')
        addDir('Horror',url,76,'')
        addDir('Romance',url,77,'')
        addDir('Sci-Fi',url,78,'')
        addDir('Thriller',url,79,'')
      

def Action(url):
     PopRatLat('2',url,'action')

def Animation(url):
     PopRatLat('2',url,'animation')

def Comedy(url):
     PopRatLat('2',url,'comedy')

def Documentary(url):
     PopRatLat('2',url,'documentary')

def Drama(url):
     PopRatLat('2',url,'drama')

def Family(url):
     PopRatLat('2',url,'family')

def Horror(url):
     PopRatLat('2',url,'horror')

def Romance(url):
     PopRatLat('2',url,'romance')

def SciFi(url):
     PopRatLat('2',url,'sci-fi')

def Thriller(url):
     PopRatLat('2',url,'thriller')

        
def MOVIEA2ZDirectories(url):
        setmode = '2'
        caturl = iceurl+'movies/a-z/'

        #Add number directory
        addDir ('#1234',caturl+'1',setmode,os.path.join(art,'letters','1.png'))

        #Generate A-Z list and add directories for all letters.
        A2Z=[chr(i) for i in xrange(ord('A'), ord('Z')+1)]
        for theletter in A2Z:
             addDir (theletter,caturl+theletter,setmode,os.path.join(art,'letters',theletter+'.png'))



def TVA2ZDirectories(url):
        setmode = '11'
        caturl = iceurl+'tv/a-z/'

        #Add number directory
        addDir ('#1234',caturl+'1',setmode,os.path.join(art,'letters','1.png'))

        #Generate A-Z list and add directories for all letters.
        A2Z=[chr(i) for i in xrange(ord('A'), ord('Z')+1)]
        for theletter in A2Z:
             addDir (theletter,caturl+theletter,setmode,os.path.join(art,'letters',theletter+'.png')) 
        


def CLEANUP(name):
# clean names of annoying garbled text
          name=re.sub('&#xC6;','AE',name)
          name=re.sub('&#x27;',"'",name)
          name=re.sub('&#xED;','i',name)
          name=re.sub('&frac12;',' 1/2',name)
          name=re.sub('&#xBD;',' 1/2',name)
          name=re.sub('&#x26;','&',name)
          name=re.sub('&#x22;','',name)
          name=re.sub('</a>','',name)
          name=re.sub('<b>HD</b>',' *HD 720p*',name)
          name=re.sub('&#xF4;','o',name)
          name=re.sub('&#xE9;',"e",name)
          name=re.sub('&#xEB;',"e",name)
          return name

     
def MOVIEINDEX(url):
#Indexer for most things. (Not just movies.) 

        # set content type so library shows more views and info
        xbmcplugin.setContent(int(sys.argv[1]), 'movies')

        meta_path=os.path.join(translatedicedatapath,'meta_caches')
        use_meta=os.path.exists(meta_path)
        meta_setting = selfAddon.getSetting('use-meta')

        link=GetURL(url)

        scrape=re.compile('<a name=i id=(.+?)></a><img class=star><a href=/(.+?)>(.+?)<br>').findall(link)

        #add without metadata -- imdb is still passed for use with Add to Favourites
        if use_meta==False or meta_setting=='false':
             for imdb_id,url,name in scrape:
                name=CLEANUP(name)
                addDir(name,iceurl+url,100,'',imdb='tt'+str(imdb_id))
                
        #add with metadata
        elif use_meta==True and meta_setting=='true':

             #initialise meta class before loop
             metaget=metahandlers.MovieMetaData(translatedicedatapath)

             for imdb_id,url,name in scrape:

                #clean name of unwanted stuff
                name=CLEANUP(name)
                url=iceurl+url

                #return the metadata dictionary  
                meta=metaget.get_movie_meta(imdb_id)

                #debugs
                #print 'meta_name:'+str(name)
                #print 'meta_imdb_id:'+str(imdb_id)
                #print 'meta_video_url:'+str(url)
                #print 'meta_data:'+str(meta)
                #print 'meta_imdb_id:',meta['imdb_id']
               
                if meta is None:
                     #add directories without meta
                     addDir(name,url,100,'')
                else:
                     #add directories with meta
                     addDir(name,url,100,'',metainfo=meta,imdb='tt'+str(imdb_id))


def TVINDEX(url):
#Indexer for TV Shows only.
     
        link=GetURL(url)
        match=re.compile('<a name=i id=(.+?)></a><img class=star><a href=/(.+?)>(.+?)</a>').findall(link)
        for imdb_id,url,name in match:
                name=CLEANUP(name)
                addDir(name,iceurl+url,12,'')


def TVSEASONS(url):
# displays by seasons. pays attention to settings.

        FlattenSingleSeasons = selfAddon.getSetting('flatten-single-season')
        source=GetURL(url)

        #Save the tv show name for use in special download directories.
        tvshowname=handle_file('mediatvshowname','')
        match=re.compile('<h1>(.+?)<a class').findall(source)
        save(tvshowname,match[0])  
        
        ep_list = str(BeautifulSoup(source).find("span", { "class" : "list" } ))

        season_list=re.compile('<h4>(.+?)</h4>').findall(ep_list)
        listlength=len(season_list)
        for seasons in season_list:
             if FlattenSingleSeasons==True and listlength <= 1:             

                 #proceed straight to adding episodes.
                 TVEPISODES(seasons,source=ep_list)
             else:
                 #save episode page source code
                 save(handle_file('episodesrc'),ep_list)

                 #add season directories
                 addDir(seasons,'',13,'') 


def TVEPISODES(name,url=None,source=None):
     #Save the season name for use in the special download directories.
     save(handle_file('mediatvseasonname'),name)

     #If source was'nt passed to function, open the file it should be saved to.
     if source is None:
         source = openfile(handle_file('episodesrc'))
         
     #special hack to deal with annoying re problems when recieving brackets ( )
     if re.search('\(',name) is not None:
         name = str((re.split('\(+', name))[0])
         #name=str(name[0])

     #quick hack of source code to simplfy scraping.
     source=re.sub('</span>','<h4>',source)

     #get all the source under season heading.
     #Use .+?/h4> not .+?</h4> for The Daily Show et al to work.
     match=re.compile('<h4>'+name+'.+?/h4>(.+?)<h4>').findall(source)
     for seasonSRC in match:
        TVEPLINKS(seasonSRC)

                
def TVEPLINKS(source):
# displays all episodes in the source it is passed.
        match=re.compile('<img class="star" /><a href="/(.+?)&amp;">(.+?)</a>').findall(source)
        for url,name in match:
                name=CLEANUP(name)
                addDir(name,iceurl+url,100,'')    

             
def LOADMIRRORS(url):
     # This proceeds from the file page to the separate frame where the mirrors can be found,
     # then executes code to scrape the mirrors
     link=GetURL(url)
     #print link
     posterfile=handle_file('poster','')
     videonamefile=handle_file('videoname','')
     descriptionfile=handle_file('description','')
     mpaafile=handle_file('mpaa','')
     mediapathfile=handle_file('mediapath','')
     
     
     #---------------Save metadata on page to files, for use when playing.
     # Also used for creating the download directory structures.
     
     try:
          os.remove(posterurl)
     except:
          print 'posterurl does not exist'

     try:
          os.remove(mpaafile)
     except:
          print 'mpaafile does not exist'        
     

     # get and save videoname
     namematch=re.compile('''<span style="font-size:large;color:white;">(.+?)</span>''').findall(link)
     save(videonamefile,namematch[0])

     # get and save description
     match2=re.compile('<th>Description:</th><td>(.+?)<').findall(link)
     try:
          save(descriptionfile,match2[0])
     except:
          pass
     
     # get and save poster link
     try:
          imgcheck1 = re.search('<img width=250 src=', link)
          imgcheck2 = re.search('/noref.php\?url=', link)
          if imgcheck1 is not None:
               match4=re.compile('<img width=250 src=(.+?) style').findall(link)
               save(posterfile,match4[0])
          if imgcheck2 is not None:
               match5=re.compile('/noref.php\?url=(.+?)>').findall(link)
               save(posterfile,match5[0])
     except:
          pass

     #get and save mpaa     
     mpaacheck = re.search('MPAA Rating:', link)         
     if mpaacheck is not None:     
          match4=re.compile('<th>MPAA Rating:</th><td>(.+?)</td>').findall(link)
          mpaa=re.sub('Rated ','',match4[0])
          try:
               save(mpaafile,mpaa)
          except:
               pass


     ########### get and save potential file path. This is for use in download function later on.
     epcheck1 = re.search('Episodes</a>', link)
     epcheck2 = re.search('Episode</a>', link)
     if epcheck1 is not None or epcheck2 is not None:
          shownamepath=handle_file('mediatvshowname','')
          if os.path.exists(shownamepath):
               #open media file if it exists, as that has show name with date.
               showname=openfile(shownamepath)
          else:
               #fall back to scraping show name without date from the page.
               print 'USING FALLBACK SHOW NAME'
               fallbackshowname=re.compile("alt\='Show series\: (.+?)'").findall(link)
               showname=fallbackshowname[0]
          try:
               #if season name file exists
               seasonnamepath=handle_file('mediatvseasonname','')
               if os.path.exists(seasonnamepath):
                    seasonname=openfile(seasonnamepath)
                    save(mediapathfile,'TV Shows/'+showname+'/'+seasonname)
               else:
                    save(mediapathfile,'TV Shows/'+showname)
          except:
               print "FAILED TO SAVE TV SHOW FILE PATH!"
     else:
          
          save(mediapathfile,'Movies/'+namematch[0])

     #---------------End metadata stuff --------------

     match=re.compile('/membersonly/components/com_iceplayer/(.+?)" width=').findall(link)
     match[0]=re.sub('%29',')',match[0])
     match[0]=re.sub('%28','(',match[0])
     for url in match:
          mirrorpageurl = iceurl+'membersonly/components/com_iceplayer/'+url

     mlink=GetURL(mirrorpageurl)

     #check for recaptcha
     has_recaptcha = re.search('recaptcha_challenge_field', mlink)

     if has_recaptcha is None:
          GETMIRRORS(mirrorpageurl,mlink)
     elif has_recaptcha is not None:
          RECAPTCHA(mirrorpageurl)


def RECAPTCHA(url):
     print 'initiating recaptcha passthrough'
     req = urllib2.Request(url)
     req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')       
     response = urllib2.urlopen(req)
     link=response.read()
     match=re.compile('<iframe src="http://www.google.com/recaptcha/api/noscript\?k\=(.+?)" height').findall(link)
     for token in match:
          surl = 'http://www.google.com/recaptcha/api/challenge?k=' + token
     tokenlink=GetURL(surl)
     matchy=re.compile("challenge : '(.+?)'").findall(tokenlink)
     for challenge in matchy:
          imageurl='http://www.google.com/recaptcha/api/image?c='+challenge

     captchafile=handle_file('captcha','')
     pageurlfile=handle_file('pageurl','')

     #hacky method --- save all captcha details and mirrorpageurl to file, to reopen in next step
     save(captchafile, challenge)
     save(pageurlfile, url)
     #addDir uses imageurl as url, to avoid xbmc displaying old cached image as the fresh captcha
     addDir('Enter Captcha - Type the letters',imageurl,99,imageurl)

def CATPCHAENTER(surl):
     
     url=handle_file('pageurl','open')
     kb = xbmc.Keyboard('', 'Type the letters in the captcha image', False)
     kb.doModal()
     if (kb.isConfirmed()):
          userInput = kb.getText()
          if userInput is not '':
               challengeToken=handle_file('captcha','open')
               print 'challenge token: '+challengeToken
               parameters = urllib.urlencode({'recaptcha_challenge_field': challengeToken, 'recaptcha_response_field': userInput})
               resp = urllib.urlopen(url, parameters)
               link=resp.read() 
               resp.close()
               has_recaptcha = CHECKForReCAPTCHA(link)
               if has_recaptcha is False:
                    GETMIRRORS(url,link)
               elif has_recaptcha is True:
                    Notify('big', 'Text does not match captcha image!', 'To try again, close this box and then: \n Press backspace twice, and reselect your video.', '')
          elif userInput is '':
               Notify('big', 'No text entered!', 'To try again, close this box and then: \n Press backspace twice, and reselect your video.', '')               

def GETMIRRORS(url,link):
# This scrapes the megaupload mirrors from the separate url used for the video frame.
# It also displays them in an informative fashion to user.
# Displays in three directory levels: HD / DVDRip etc , Source, PART

     #hacky method -- save page source to file
     mirrorfile=handle_file('mirror','')
     save(mirrorfile, link)

     #strings for checking the existence of categories      
     dvdrip=re.search('<div class=ripdiv><b>DVDRip / Standard Def</b>', link)
     hd720p=re.search('<div class=ripdiv><b>HD 720p</b>', link)
     dvdscreener=re.search('<div class=ripdiv><b>DVD Screener</b>', link)
     r5r6=re.search('<div class=ripdiv><b>R5/R6 DVDRip</b>', link)

     #check that these categories exist, if they do set values to true.
     if dvdrip is not None:
          dvdrip = 'true'
     if hd720p is not None:
          hd720p = 'true'
     if dvdscreener is not None:
          dvdscreener = 'true'
     if r5r6 is not None:
          r5r6 = 'true'
     #check that these categories exist, if they dont set values to false.
     if dvdrip is None:
          dvdrip = 'false'
     if hd720p is None:
          hd720p = 'false'
     if dvdscreener is None:
          dvdscreener = 'false'
     if r5r6 is None:
          r5r6 = 'false'

     FlattenSrcType = selfAddon.getSetting('flatten-source-type')        

     #only detect and proceed directly to adding sources if flatten sources setting is true
     if FlattenSrcType == 'true':
          #check if there is more than one directory
          if dvdrip == 'true' and hd720p == 'true':
               only1 = 'false'
          if dvdrip == 'true' and dvdscreener == 'true':
               only1 = 'false'
          if dvdrip == 'true' and r5r6 == 'true':
               only1 = 'false'
          if dvdscreener == 'false' and r5r6 == 'false':
               only1 = 'false'
          if hd720p == 'true' and dvdscreener == 'false':
               only1 = 'false'
          if r5r6 == 'true' and hd720p == 'true':
               only1 = 'false'
          #check if there is only one directory      
          if dvdrip == 'true' and hd720p == 'false' and dvdscreener == 'false' and r5r6 == 'false':
               only1 = 'true'
               DVDRip(url)
          if dvdrip == 'false' and hd720p == 'true' and dvdscreener == 'false' and r5r6 == 'false':
               only1 = 'true'
               HD720p(url)
          if dvdrip == 'false' and hd720p == 'false' and dvdscreener == 'true' and r5r6 == 'false':
               only1 = 'true'
               DVDScreener(url)
          if dvdrip == 'false' and hd720p == 'false' and dvdscreener == 'false' and r5r6 == 'true':
               only1 = 'true'
               R5R6(url)
          #add directories of source categories if only1 is false
          if only1 == 'false':
               addCatDir(url,dvdrip,hd720p,dvdscreener,r5r6)

     #if flattensources is set to false, don't flatten                
     elif FlattenSrcType == 'false':
          addCatDir(url,dvdrip,hd720p,dvdscreener,r5r6)


                
def addCatDir(url,dvdrip,hd720p,dvdscreener,r5r6):
        if dvdrip == 'true':
                addDir('DVDRip',url,101,'')
        if hd720p == 'true':
                addDir('HD 720p',url,102,'')
        if dvdscreener == 'true':
                addDir('DVD Screener',url,103,'')
        if r5r6 == 'true':
                addDir('R5/R6 DVDRip',url,104,'') 

def Add_Multi_Parts(name,url,icon):
     #StackMulti = selfAddon.getSetting('stack-multi-part')
     #StackMulti=='false'
     #if StackMulti=='true':
     #save list of urls to later be stacked when user selects part
          addExecute(name,url,200,icon)

     #elif StackMulti=='false':
     #     addExecute(name,url,200,icon)



def PART(scrap,sourcenumber,hide2shared,megapic,shared2pic):
     #check if source exists
     sourcestring='Source #'+sourcenumber
     checkforsource = re.search(sourcestring, scrap)
     
     #if source exists proceed.
     if checkforsource is not None:
          #print 'Source #'+sourcenumber+' exists'
          
          #check if source contains multiple parts
          multiple_part = re.search('<p>Source #'+sourcenumber+':', scrap)
          
          if multiple_part is not None:
               #print sourcestring+' has multiple parts'
               #get all text under source if it has multiple parts
               multi_part_source=re.compile('<p>Source #'+sourcenumber+': (.+?)PART 1(.+?)</i><p>').findall(scrap)

               #put scrape back together
               for sourcescrape1,sourcescrape2 in multi_part_source:
                    scrape=sourcescrape1+'PART 1'+sourcescrape2

                    #check if source is megaupload or 2shared, and add all parts as links
                    ismega = re.search('.megaupload.com/', scrape)
                    is2shared = re.search('.2shared.com/', scrape)
                    if ismega is not None:
                         #print sourcestring+' is hosted by megaupload'
                         part=re.compile('&url=http://www.megaupload.com/?(.+?)>PART (.+?)</a>').findall(scrape)
                         for url,name in part:
                              #print 'scrapedmegaurl: '+url
                              fullurl='http://www.megaupload.com/'+url
                              #print 'megafullurl: '+fullurl
                              partname='Part '+name
                              fullname=sourcestring+' | MU | '+partname
                              Add_Multi_Parts(fullname,fullurl,megapic)
                    elif is2shared is not None and hide2shared is 'false':
                         #print sourcestring+' is hosted by 2shared' 
                         part=re.compile('&url=http://www.2shared.com/(.+?)>PART (.+?)</a>').findall(scrape)
                         for url,name in part:
                              #print 'scraped2shared: '+url
                              fullurl='http://www.2shared.com/'+url
                              #print '2sharedfullurl: '+fullurl
                              partname='Part '+name
                              fullname=sourcestring+' | 2S  | '+partname
                              Add_Multi_Parts(fullname,fullurl,shared2pic) 

          #if source does not have multiple parts...
          elif multiple_part is None:
               #print sourcestring+' is single part'
               #find corresponding '<a rel=?' entry and add as a one-link source
               source5=re.compile('<a rel='+sourcenumber+'.+?&url=(.+?)>Source #'+sourcenumber+':').findall(scrap)
               #print source5
               for url in source5:
                    ismega = re.search('.megaupload.com/', url)
                    is2shared = re.search('.2shared.com/', url)
                    if ismega is not None:
                         #print 'Source #'+sourcenumber+' is hosted by megaupload'
                         fullname=sourcestring+' | MU | Full'
                         addExecute(fullname,url,200,megapic)
                    elif is2shared is not None and hide2shared is 'false':
                         #print 'Source #'+sourcenumber+' is hosted by 2shared' 
                         fullname=sourcestring+' | 2S  | Full'
                         addExecute(fullname,url,200,shared2pic)


def SOURCE(scrape):
#check for sources containing multiple parts or just one part
          hide2shared = selfAddon.getSetting('hide-2shared')
          megapic=handle_file('megapic','')
          shared2pic=handle_file('shared2pic','')

          #create a list of numbers 1-21
          num = 1
          numlist = list('1')
          while num < 21:
              num = num+1
              numlist.append(str(num))

          #for every number, run PART.
          #The first thing PART does is check whether that number source exists...
          #...so it's not as CPU intensive as you might think.    
          for thenumber in numlist: 
               PART(scrape,thenumber,hide2shared,megapic,shared2pic)

           
def DVDRip(url):
        link=handle_file('mirror','open')
#string for all text under standard def border
        defcat=re.compile('<div class=ripdiv><b>DVDRip / Standard Def</b>(.+?)</div>').findall(link)
        for scrape in defcat:
                SOURCE(scrape)

def HD720p(url):
        link=handle_file('mirror','open')
#string for all text under hd720p border
        defcat=re.compile('<div class=ripdiv><b>HD 720p</b>(.+?)</div>').findall(link)
        for scrape in defcat:
                SOURCE(scrape)

def DVDScreener(url):
        link=handle_file('mirror','open')
#string for all text under dvd screener border
        defcat=re.compile('<div class=ripdiv><b>DVD Screener</b>(.+?)</div>').findall(link)
        for scrape in defcat:
                SOURCE(scrape)

def R5R6(url):
        link=handle_file('mirror','open')
#string for all text under r5/r6 border
        defcat=re.compile('<div class=ripdiv><b>R5/R6 DVDRip</b>(.+?)</div>').findall(link)
        for scrape in defcat:
                SOURCE(scrape)

class TwoSharedDownloader:
     
     def __init__(self):
          self.cookieString = ""
          self.re2sUrl = re.compile('(?<=window.location \=\')([^\']+)')
     
     def returnLink(self, pageUrl):

          # Open the 2Shared page and read its source to htmlSource
          request = urllib2.Request(pageUrl)
          response = urllib2.urlopen(request)
          htmlSource = response.read()
     
          # Search the source for link to the video and store it for later use
          match = self.re2sUrl.search(htmlSource)
          fileUrl = match.group(0)
          
          # Extract the cookies set by visiting the 2Shared page
          cookies = cookielib.CookieJar()
          cookies.extract_cookies(response, request)
          
          # Format the cookies so they can be used in XBMC
          for item in cookies._cookies['.2shared.com']['/']:
               self.cookieString += str(item) + "=" + str(cookies._cookies['.2shared.com']['/'][item].value) + "; "
               self.cookieString += "WWW_JSESSIONID=" + str(cookies._cookies['www.2shared.com']['/']['JSESSIONID'].value)

          # Arrange the spoofed header string in a format XBMC can read
          headers = urllib.quote("User-Agent=Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)|Accept=text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8|Accept-Language=en-us,en;q=0.5|Accept-Encoding=gzip,deflate|Accept-Charset=ISO-8859-1,utf-8;q=0.7,*;q=0.7|Keep-Alive=115|Referer=" + pageUrl + "|Cookie=" + self.cookieString)
          
          # Append the header string to the file URL
          pathToPlay = fileUrl + "?" + headers
          
          # Return the valid link
          return pathToPlay 
     

     
          
def SHARED2_HANDLER(url):
          downloader2Shared = TwoSharedDownloader()
          vidFile = downloader2Shared.returnLink(url)
          #vidFile = TwoSharedDownloader.returnLink(url)
          
          print str(vodFile)
          match=re.compile('http\:\/\/(.+?).dc1').findall(vidFile)
          for urlbulk in match:
               finalurl='http://'+urlbulk+'.avi'
               print '2Shared Direct Link: '+finalurl
               return finalurl
          #req = urllib2.Request(url)
          #req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
          #req.add_header('Referer', url)
          #jar = cookielib.FileCookieJar("cookies")
          #opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))
          #response = opener.open(req)
          #link=response.read()
          #response.close()
          #dirlink=re.compile("window.location ='(.+?)';").findall(link)
          #for surl in dirlink:
          #    return surl
                

#def VIDEOLINKSWITHFILENAME(url):
# loads megaupload page and scrapes and adds videolink, and name of uploaded file from it
#        link=GetURL(url)
#        avimatch=re.compile('id="downloadlink"><a href="(.+?).avi" class=').findall(link)
#        for url in avimatch:
#                fullurl=url+'.avi'                          
#                #get filname
#                matchy=re.compile('id="downloadlink"><a href=".+?megaupload.com/files/.+?/(.+?).avi" class=').findall(link)
#                for urlfilename in matchy:
#                        addLink('VideoFile | '+urlfilename,fullurl,'')
#        #pretend to XBMC that divx is avi
#        match1=re.compile('id="downloadlink"><a href="(.+?).divx" class=').findall(link)
#        for surl in match1:
#                sullurl=surl+'.avi'
#                #get filename
#                matchy=re.compile('id="downloadlink"><a href=".+?megaupload.com/files/.+?/(.+?).divx" class=').findall(link)
#                for urlfilename in matchy:
#                        addLink('VideoFile | '+urlfilename,sullurl,'')
        
def GetURL(url):
     #print 'processing url: '+url
     req = urllib2.Request(url)
     req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')       
     response = urllib2.urlopen(req)
     link=response.read()
     response.close()
     return link


def WaitIf():
     #killing playback is necessary if switching playing of one megaup/2share stream to another
     if xbmc.Player().isPlayingVideo() == True:
               #currentvid=xbmc.Player().getPlayingFile()
               #isice = re.search('.megaupload', currentvid)
                xbmc.Player().stop()

def VIDLINK_HANDLER(name,url):
     #video link preflight, pays attention to settings / checks if url is mega or 2shared
     ismega = re.search('.megaupload.com/', url)
     is2shared = re.search('.2shared.com/', url)
     
     if ismega is not None:
          mu=megaroutines.megaupload(translatedicedatapath)
          source=mu.load_pagesrc(url)
          filelink=mu.get_filelink(source,aviget=True)
          
          FilePlay(name,filelink)

     elif is2shared is not None:
          Notify('big','2Shared','2Shared is not supported by this addon. (Yet)','')
          #shared2url=SHARED2_HANDLER(url)
          #return shared2url



def Get_Path(srcname,vidname):
     #get path for download
     mypath=os.path.normpath(str(selfAddon.getSetting('download-folder')))

     if os.path.exists(mypath):

          #if source is split into parts, attach part number to the videoname.
          if re.search('Part',srcname) is not None:
               srcname=(re.split('\|+', srcname))[-1]
               vidname=vidname+' part'+((re.split('\ +', srcname))[-1])
               #add file extension
               vidname = vidname+'.avi'
          else:
               #add file extension
               vidname = vidname+'.avi'

          initial_path=os.path.join(mypath,'Icefilms Downloaded Videos')

          #is use special directory structure set to true?
          SpecialDirs=selfAddon.getSetting('use-special-structure')

          if SpecialDirs == 'true':
               mediapath=os.path.normpath(handle_file('mediapath','open'))
               mediapath=os.path.join(initial_path,mediapath)              
               
               if not os.path.exists(mediapath):
                    os.makedirs(mediapath)
               finalpath=os.path.join(mediapath,vidname)
               return finalpath
     
          elif SpecialDirs == 'false':
               mypath=os.path.join(initial_path,vidname)
               return mypath
     else:
          return 'path not set'

def FilePlay(name,url):
          #stack all parts including and after selected part
     
          #print 'FileURL: '+fileurl

          #set name as metadata, for selected source
          vidname=handle_file('videoname','open')

          #set other metadata strings from strings saved earlier
          poster=handle_file('poster','open')
          description=handle_file('description','open')
          mpaafile=handle_file('mpaa','')
          
          #srcname=openfile(sourcenamefile)
          srcname=name
          listitem = xbmcgui.ListItem(srcname)
          if not os.path.exists(mpaafile):
               listitem.setInfo('video', {'Title': vidname, 'plotoutline': description, 'plot': description})
          if os.path.exists(mpaafile):
               mpaa=openfile(mpaafile)
               listitem.setInfo('video', {'Title': vidname, 'plotoutline': description, 'plot': description, 'mpaa': mpaa})
          listitem.setThumbnailImage(poster)
     
          dialog = xbmcgui.Dialog()
          playdialog = dialog.select('', ['Stream', 'Download', 'Check My Mega Limits', 'Kill Streaming', 'Cancel'])
          if playdialog == 0:

               WaitIf()
               print 'attempting to stream file'
               try:
                    xbmc.Player().play(url, listitem)
               except:
                    print 'file streaming failed'
                    Notify('megaalert','','','')

                    
          if playdialog == 1:

               WaitIf()
               mypath=Get_Path(srcname,vidname)
               print 'MYPATH: ',mypath
               if mypath is 'path not set':
                    Notify('Download Alert','You have not set the download folder.\n Please access the addon settings and set it.','','')
               else:
                    if os.path.isfile(mypath) is True:
                         Notify('Download Alert','The video you are trying to download already exists!','','')
                    else:     
                         print 'attempting to download file'
                         try:
                              Download(url, mypath, vidname)
                         except:
                              print 'download failed'
                         
               
          if playdialog == 2:
               WaitIf()
               mu=megaroutines.megaupload(translatedicedatapath)
               limit=mu.dls_limited()
               if limit is True:
                    Notify('megaalert1','','','')
               elif limit is False:
                    Notify('megaalert2','','','')

          if playdialog == 3:
               xbmc.Player().stop()
          

class StopDownloading(Exception): 
        def __init__(self, value): 
            self.value = value 
        def __str__(self): 
            return repr(self.value)
          
def Download(url, dest, displayname=False):
        if displayname == False:
             displayname=url
        DeleteIncomplete=selfAddon.getSetting('delete-incomplete-downloads')
        dp = xbmcgui.DialogProgress()
        dp.create('Downloading', '', displayname)
        start_time = time.time() 
        try: 
            urllib.urlretrieve(url, dest, lambda nb, bs, fs: _pbhook(nb, bs, fs, dp, start_time)) 
        except:
            if DeleteIncomplete == 'true':
                 #delete partially downloaded file if setting says to.
                 while os.path.exists(dest): 
                     try: 
                         os.remove(dest) 
                         break 
                     except: 
                          pass 
            #only handle StopDownloading (from cancel), ContentTooShort (from urlretrieve), and OS (from the race condition); let other exceptions bubble 
            if sys.exc_info()[0] in (urllib.ContentTooShortError, StopDownloading, OSError): 
                return 'false' 
            else: 
                raise 
        return 'downloaded'
     
def QuietDownload(url, dest):
#possibly useful in future addon versions
     
        #dp = xbmcgui.DialogProgress() 
        #dp.create('Downloading', '', name) 
        start_time = time.time() 
        try: 
            #urllib.urlretrieve(url, dest, lambda nb, bs, fs: _pbhook(nb, bs, fs, dp, start_time))
            urllib.urlretrieve(url, dest)
            #xbmc.Player().play(dest)
        except: 
            #delete partially downloaded file 
            while os.path.exists(dest): 
                try: 
                    #os.remove(dest) 
                    break 
                except: 
                     pass 
            #only handle StopDownloading (from cancel), ContentTooShort (from urlretrieve), and OS (from the race condition); let other exceptions bubble 
            if sys.exc_info()[0] in (urllib.ContentTooShortError, StopDownloading, OSError): 
                return 'false' 
            else: 
                raise 
        return 'downloaded' 
         

def _pbhook(numblocks, blocksize, filesize, dp, start_time):
        try: 
            percent = min(numblocks * blocksize * 100 / filesize, 100) 
            currently_downloaded = float(numblocks) * blocksize / (1024 * 1024) 
            kbps_speed = numblocks * blocksize / (time.time() - start_time) 
            if kbps_speed > 0: 
                eta = (filesize - numblocks * blocksize) / kbps_speed 
            else: 
                eta = 0 
            kbps_speed = kbps_speed / 1024 
            total = float(filesize) / (1024 * 1024) 
            # print ( 
                # percent, 
                # numblocks, 
                # blocksize, 
                # filesize, 
                # currently_downloaded, 
                # kbps_speed, 
                # eta, 
                # ) 
            mbs = '%.02f MB of %.02f MB' % (currently_downloaded, total) 
            e = 'Speed: %.02f Kb/s ' % kbps_speed 
            e += 'ETA: %02d:%02d' % divmod(eta, 60) 
            dp.update(percent, mbs, e)
            #print percent, mbs, e 
        except: 
            percent = 100 
            dp.update(percent) 
        if dp.iscanceled(): 
            dp.close() 
            raise StopDownloading('Stopped Downloading')

   
def addExecute(name,url,mode,iconimage):

     # A list item that executes the next mode, but does'nt clear the screen of current list items.

        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
        return ok



def addDir(name, url, mode, iconimage, metainfo=False, imdb=False, delfromfav=False, total=False, disablefav=False):
    meta = metainfo

    ###  addDir with context menus and meta support  ###

    #encode url and name, so they can pass through the sys.argv[0] related strings
    sysname = urllib.quote_plus(name)
    sysurl = urllib.quote_plus(url)       

    u = sys.argv[0] + "?url=" + sysurl + "&mode=" + str(mode) + "&name=" + sysname
    ok = True

    #handle adding meta
    if meta == False:
        liz = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
        liz.setInfo(type="Video", infoLabels={"Title": name})

    if meta is not False:
        liz = xbmcgui.ListItem(name, iconImage=str(meta['cover_url']), thumbnailImage=str(meta['cover_url']))
        liz.setInfo(type="Video",
                    infoLabels={'title':name,
                    'plot':meta['plot'],
                    'genre':meta['genres'],
                    'duration':str(meta['duration']),
                    'premiered':meta['premiered'],
                    'studio':meta['studios'],
                    'mpaa':str(meta['mpaa']),
                    'trailer':str(meta['trailer_url']),
                    'code':str(meta['imdb_id']),
                    'rating':float(meta['rating'])})

    ########
    #handle adding context menus
    contextMenuItems = []

    # add/delete favourite
    if disablefav==False: # disable fav is necessary for the scrapes in the homepage category.
        if delfromfav is True:
            #settings for when in the Favourites folder
            contextMenuItems.append(('Delete from Ice Favourites', 'XBMC.RunPlugin(%s?mode=111&name=%s&url=%s)' % (sys.argv[0], sysname, sysurl)))
        else:
            #if directory is an episode list or movie
            if mode == 100 or mode == 12:
                if imdb is not False:
                    sysimdb = urllib.quote_plus(imdb)
                else:
                    #if no imdb number, it will have no metadata in Favourites
                    sysimdb = urllib.quote_plus('nothing')
                contextMenuItems.append(('Add to Ice Favourites', 'XBMC.RunPlugin(%s?mode=110&name=%s&url=%s&imdbnum=%s)' % (sys.argv[0], sysname, sysurl, sysimdb)))

    # switch on/off library mode (have it appear in list after favourite options)
    if inLibraryMode():
        contextMenuItems.append(('Switch off Library mode', 'XBMC.RunPlugin(%s?mode=300)' % (sys.argv[0])))
    else:
        contextMenuItems.append(('Switch to Library Mode', 'XBMC.RunPlugin(%s?mode=300)' % (sys.argv[0])))
        
    if contextMenuItems:
        liz.addContextMenuItems(contextMenuItems, replaceItems=True)
    #########

    #Do some crucial stuff
    if total is False:
        ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    if total is not False:
        ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True, totalItems=int(total))
    return ok


     

#VANILLA ADDDIR (kept for reference)
def VaddDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

# switch in and out of library mode
def toggleLibraryMode():
    container_folder_path = xbmc.getInfoLabel('Container.FolderPath')
    if inLibraryMode():
        xbmc.executebuiltin("XBMC.ActivateWindow(VideoFiles,%s)" % container_folder_path)
        # do not cacheToDisc cuz we want this code rerun
        xbmcplugin.endOfDirectory( int(sys.argv[1]), succeeded=True, updateListing=False, cacheToDisc=False )
    else:
        xbmc.executebuiltin("XBMC.ActivateWindow(VideoLibrary,%s)" % container_folder_path)
        # do not cacheToDisc cuz we want this code rerun
        xbmcplugin.endOfDirectory( int(sys.argv[1]), succeeded=True, updateListing=False, cacheToDisc=False )

def inLibraryMode():
    return xbmc.getCondVisibility("[Window.IsActive(videolibrary)]")

def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                                
        return param

params=get_params()
url=None
name=None
mode=None
imdbnum=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        imdbnum=urllib.unquote_plus(params["imdbnum"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass


print '==========================PARAMS:\nURL: %s\nNAME: %s\nMODE: %s\nIMDBNUM: %s\nMYHANDLE: %s\nPARAMS: %s' % ( url, name, mode, imdbnum, sys.argv[1], params )

if mode==None: #or url==None or len(url)<1:
        print ""
        CATEGORIES()

elif mode==50:
        print ""+url
        TVCATEGORIES(url)

elif mode==51:
        print ""+url
        MOVIECATEGORIES(url)

elif mode==52:
        print ""+url
        MUSICCATEGORIES(url)

elif mode==53:
        print ""+url
        STANDUPCATEGORIES(url)

elif mode==54:
        print ""+url
        OTHERCATEGORIES(url)

elif mode==55:
        print ""+url
        SEARCH(url)

elif mode==56:
        print ""+url
        ICEHOMEPAGE(url)

elif mode==57:
        print ""+url
        FAVOURITES(url)

elif mode==58:
        print ""+url
        CLEAR_FAVOURITES(url)

elif mode==60:
        print ""+url
        RECENT(url)

elif mode==61:
        print ""+url
        LATEST(url)

elif mode==62:
        print ""+url
        WATCHINGNOW(url)

elif mode==63:
        print ""+url
        HD720pCat(url)
        
elif mode==64:
        print ""+url
        Genres(url)

elif mode==70:
        print ""+url
        Action(url)

elif mode==71:
        print ""+url
        Animation(url)

elif mode==72:
        print ""+url
        Comedy(url)

elif mode==73:
        print ""+url
        Documentary(url)

elif mode==74:
        print ""+url
        Drama(url)

elif mode==75:
        print ""+url
        Family(url)

elif mode==76:
        print ""+url
        Horror(url)

elif mode==77:
        print ""+url
        Romance(url)

elif mode==78:
        print ""+url
        SciFi(url)

elif mode==79:
        print ""+url
        Thriller(url)
    
elif mode==1:
        print ""+url
        MOVIEA2ZDirectories(url)

elif mode==2:
        print ""+url
        MOVIEINDEX(url)
        
elif mode==10:
        print ""+url
        TVA2ZDirectories(url)

elif mode==11:
        print ""+url
        TVINDEX(url)

elif mode==12:
        print ""+url
        TVSEASONS(url)

elif mode==13:
        print ""+url
        TVEPISODES(name,url)

elif mode==99:
        print ""+url
        CATPCHAENTER(url)
        
elif mode==100:
        print ""+url
        LOADMIRRORS(url)

elif mode==101:
        print ""+url
        DVDRip(url)

elif mode==102:
        print ""+url
        HD720p(url)

elif mode==103:
        print ""+url
        DVDScreener(url)

elif mode==104:
        print ""+url
        R5R6(url)

elif mode==110:
        # if you dont use the "url", "name" params() then you need to define the value# along with the other params.
        ADD_TO_FAVOURITES(name,url,imdbnum)

elif mode==111:
        print ""+url
        DELETE_FROM_FAVOURITES(name,url)

elif mode==200:
        print ""+url
        VIDLINK_HANDLER(name,url)

elif mode==300:
        toggleLibraryMode()

xbmcplugin.endOfDirectory(int(sys.argv[1]))
