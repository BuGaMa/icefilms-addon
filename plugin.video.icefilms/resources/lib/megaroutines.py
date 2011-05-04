'''
 _ ___ __  _   __  __    ____      ___ __ 
 /|/|(_  / _ /_| /__)/  )/  //  //| )(_  (   v0.3 Final -- Deprecated by videourlresolver
/   |/__(__)(  |/ ( (__/(__/(  (/ |/ /____)  Copyleft Anarchintosh.

Python link resolver for megaupload.
In the future it will support megavideo.
In the future it will support Megaporn+Megaporn/Video links.

Credits: Thank you Coolblaze,Voinage and PGuedes for the megavideo code.
         Also, thanks to the author of this code:
         http://stackoverflow.com/questions/4422389/use-mechanize-to-log-into-megaupload
'''

import re,sys,os
import urllib,urllib2,cookielib

def openfile(filename):
     fh = open(filename, 'r')
     contents=fh.read()
     fh.close()
     return contents

def save(filename,contents):  
     fh = open(filename, 'w')
     fh.write(contents)  
     fh.close()

def checkurl(url):
   #get necessary url details
        ismegaup = re.search('www.megaupload.com/', url)
        ismegavid = re.search('.megavideo.com/', url)
        isporn = re.search('.megaporn.com/', url)
   #second layer of porn url detection
        ispornvid = re.search('.megaporn.com/video/', url)
   # RETURN RESULTS:
        if ismegaup is not None:
           return 'megaup'
        elif ismegavid is not None:
           return 'megavid'
        elif isporn is not None:
           if ispornvid is not None:
              return 'pornvid'
           elif ispornvid is None:
              return 'pornup'


#set names of important files     
cookiefile='cookies.lwp' 
megaloginfile='MegaLogin.txt'
pornloginfile='PornLogin.txt'


def get_dir(mypath, dirname):
    #...creates sub-directories if they are not found.
    subpath = os.path.join(mypath, dirname)
    if not os.path.exists(subpath):
        os.makedirs(subpath)
    return subpath

          
class megaupload:
   def __init__(self,path):
        self.class_name='megaupload'
        self.path = get_dir(path,'megaroutine_files')
        self.classpath = get_dir(self.path,self.class_name)
        self.cookie = os.path.join(self.classpath,cookiefile)
        self.loginfile = os.path.join(self.path,megaloginfile)

   def megavid_force(self,url,disable_cookies=True):
        source=self.load_pagesrc(url,disable_cookies)
        megavidlink=self.get_megavid(source)
        return megavidlink
      
   def resolve_megaup(self,url,aviget=False,force_megavid=False):

        #bring together all the functions into a simple user-friendly function.

        source=self.load_pagesrc(url)

        #if source is a url (from a Direct Downloads re-direct) not pagesource
        if source.startswith('http://'):
             filelink=source

             #can't get megavid link if using direct download, however, can load megaup page without cookies, then scrape.
             #this is time consuming, hence the force_megavid flag needed to enable it.
             if force_megavid is False:
                  megavidlink=None
             elif force_megavid is True:
                  megavidlink=self.megavid_force(url)

             #speed patch (we know its premium, since we're getting a direct download)
             logincheck='premium'

        else: # if source is html page code...

             #scrape the direct filelink from page
             filelink=self.get_filelink(source,aviget)

             #scrape the megavideo link if there is one on the page
             megavidlink=self.get_megavid(source)

             logincheck=self.check_login(source)

        filename=self._get_filename(filelink)
        
        return filelink,filename,megavidlink,logincheck


   def load_pagesrc(self,url,disable_cookies=False):
     
     #loads page source code. redirect url is returned if Direct Downloads is enabled.
        
     urltype=checkurl(url)
     if urltype is 'megaup' or 'megaporn':
          link=GetURL(url,self,disable_cookies)
          return link
     else:
          return False


   def check_login(self,source):
        #feed me some megaupload page source
        #returns 'free' or 'premium' if logged in
        #returns 'none' if not logged in
        
        login = re.search('<b>Welcome</b>', source)
        premium = re.search('flashvars.status = "premium";', source)        

        if login is not None:
             if premium is not None:
                  return 'premium'
             elif premium is None:
                  return 'free'
        elif login is None:
             return 'none'

 
   def dls_limited(self):
     #returns True if download limit has been reached.

     truestring='Download limit exceeded'
     falsestring='Hooray Download Success'   

     #url to a special small text file that contains the words: Hooray Download Success        
     testurl='http://www.megaupload.com/?d=6PU2QD8U'

     source=self.load_pagesrc(testurl)
     fileurl=self.get_filelink(source)

     link=GetURL(fileurl,self)

     exceeded = re.search(truestring, link)
     #notexceeded = re.search(falsestring, link)

     if exceeded is not None:
          return True
     else:
          #if notexceeded is not None:
               return False


   def delete_login(self):
     #clears login and cookies
     try:
          os.remove(self.loginfile)
     except:
          pass
     try:
          os.remove(self.cookie)
     except:
          pass

        
   def set_login(self,megauser=False,megapass=False):
        #create a login file  
          loginstring='Username:'+megauser+' Password:'+megapass
          save(self.loginfile,loginstring)

          #refresh the cookies if successful
          login=Do_Login(self,megauser,megapass)

          #return whether login was successful
          return login
   
   def get_megavid ( self,source ):
        #verify source is megaupload 
        checker='<span class="down_txt3">Download link:</span> <a href="http://www.megaupload.com/'
        ismegaup=re.search(checker, source)

        if ismegaup is not None:
           #scrape for megavideo link (first check its there)
           megavidlink = re.search('View on Megavideo', source)
           if megavidlink is not None:
              megavidlink = re.compile('<a href="http://www.megavideo.(.+?)"').findall(source)
              megavid=megavidlink[0]
              megavid = 'http://www.megavideo.'+megavid
              return megavid
           if megavidlink is None:
              #no megavideo link on page
              return None
        if ismegaup is None:
           print 'not a megaupload url'
           return None


   def get_filelink(self,source,aviget=False):
          # load megaupload page and scrapes and adds videolink, passes through partname.  
          #print 'getting file link....'

          #try getting the premium link. if it returns none, use free link scraper.
          match1=re.compile('<a href="(.+?)" class="down_ad_butt1">').findall(source)
          if str(match1)=='[]':
               match2=re.compile('id="downloadlink"><a href="(.+?)" class=').findall(source)
               url=match2[0]
          else:
               url=match1[0]


          #aviget is an option where if a .divx file is found, it is renamed to .avi (necessary for XBMC)
          if aviget is True and url.endswith('divx'):
                    return url[:-4]+'avi'
          else:          
                    return url


   def _get_filename(self,url=False,source=False):
        #accept either source or url
        if url is False:
             if source is not False:
                  url=self.get_filelink(source)
        
        #get file name from url (ie my_vid.avi)
        name = re.split('\/+', url)
        return name[-1]

def get_user(login):
     userget = re.compile('Username:(.+?) P').findall(login)
     for meguse in userget:
          return meguse
          

def get_pass(login):
     passget = re.compile('Password:(.+?)').findall(login)
     for megpas in passget:
          return megpas

def Do_Login(self,megauser=False,megapass=False):

     #if no user or pass are provided, open login file to get them. 
     if megauser is False or megapass is False:
          if os.path.exists(self.cookie):
               login=openfile(self.login)
               megauser=get_user(login)
               megapass=get_pass(login)

     try:
          os.remove(self.cookie)
     except:
          pass
     
     if megauser is not False or megapass is not False:
               

# --------------- Begin dirty backport of the new non-mechanize login code. ----------------
# backported from videourlresolver megaupload resolver

               newlogin = __doLogin('http://www.megaupload.com/',self.cookie,megauser,megapass)

               if newlogin is not None:
                    return True
                    
               elif newlogin is None:
                    try:
                         os.remove(self.loginfile)
                    except:
                         pass
                    return False
                    
def __doLogin(baseurl, cookiepath, username, password):

		#build the login code, from user, pass, baseurl and cookie
		login_data = urllib.urlencode({'username' : username, 'password' : password, 'login' : 1, 'redir' : 1})	
		req = urllib2.Request(baseurl + '?c=login', login_data)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
		cj = cookielib.LWPCookieJar()
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

		#do the login and get the response
		response = opener.open(req)
		source = response.read()
		response.close()

		login = new_check_login(source)

		if login == 'free' or login == 'premium':
			cj.save(cookiepath)

                        return login
                else:
                        return None

def new_check_login(source):
		#feed me some megaupload page source
		#returns 'free' or 'premium' if logged in
		#returns 'none' if not logged in

		login = re.search('Welcome', source)
		premium = re.search('flashvars.status = "premium";', source)		

		if login is not None:
			if premium is not None:
				return 'premium'
			elif premium is None:
				return 'free'
		elif login is None:
			return None

# --------------- End dirty backport of the new non-mechanize login code. ----------------

def GetURL(url,self=False,disable_cookies=False):
     #print 'processing url: '+url

     #logic to designate whether to handle cookies
     urltype=checkurl(url)
     if disable_cookies==False:
          if urltype is 'megaup' or 'megaporn' or 'megavid':
               if self is not False:
                    if os.path.exists(self.cookie):
                         use_cookie=True
                    else:
                         use_cookie=False  
               else:
                    use_cookie=False  
          else:
                    use_cookie=False  
     else:
          use_cookie=False

     # don't use cookie, if not logged in          
     if use_cookie is False:
          req = urllib2.Request(url)
          req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')       
          response = urllib2.urlopen(req)
          link=response.read()
          response.close()
          return link

     # use cookie, if logged in
     if use_cookie is True:
          cj = cookielib.LWPCookieJar()
          cj.load(self.cookie)
          req = urllib2.Request(url)
          req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')       
          opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
          response = opener.open(req)

          #check if we were redirected (megapremium Direct Downloads...)
          finalurl = response.geturl()
          if finalurl is url:
               link=response.read()
               response.close()
               return link
          elif finalurl is not url:
               #if we have been redirected, return the redirect url
               return finalurl



#---------------------END MEGAUPLOAD CODE--------------------------#
