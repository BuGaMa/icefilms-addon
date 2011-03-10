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

import re,sys,os,os.path
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
        ismegaup = re.search('.megaupload.com/', url)
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

#-------Megavideo

#class to simplify usage of the functions. NOT YET WORKING!

#if megaupload directory exists it will use duplicate that login
class megavideo:
     def __init__(self,path):
        self.class_name='megavideo'
        self.path = handle_main_directory(path)
        self.classpath = handle_class_directory(path,self.class_name)
        self.cookie = os.path.normpath(self.classpath+cookiefile)
        self.loginfile = os.path.normpath(self.path+megaloginfile)

     def set_login(self,megauser=False,megapass=False,RefreshCookies=True):
          #create a login file  
          loginstring='Username:'+megauser+' Password:'+megapass
          save(self.loginfile,loginstring)

          #refresh the cookies if successful
          if RefreshCookies==True:
               #login=GetMegavideoUser(megauser, megapass, self.cookie)
               login=Do_Login(self,megauser,megapass)

               #return whether login was successful
               return login

     def get_flv(self,url):
          url = getcode(url)
          movielink = getlowurl(self,url)
          return movielink

     def get_original(self,url):
          #this option requires a premium login or it will return False
          mega = getcode(mega)
          movielink = gethighurl(self,mega)
     



# Esto funciona en todos, excepto plex y linux
#COOKIEFILE = xbmc.translatePath( "special://home/plugins/video/pelisalacarta/cookies.lwp" )

# Esto funciona en plex!
#COOKIEFILE = os.path.join( os.getcwd(), 'cookies.lwp' )
#print "Cookiefile="+COOKIEFILE

#Python Video Decryption and resolving routines.
#Courtesy of Voinage, Coolblaze.

#DEBUG = False

#Megavideo - Coolblaze # Part 1 put this below VIDEOLINKS function. Ctrl & C after highlighting.


     

def ajoin(arr):
	strtest = ''
	for num in range(len(arr)):
		strtest = strtest + str(arr[num])
	return strtest

def asplit(mystring):
	arr = []
	for num in range(len(mystring)):
		arr.append(mystring[num])
	return arr
		
def decrypt(str1, key1, key2):

	__reg1 = []
	__reg3 = 0
	while (__reg3 < len(str1)):
		__reg0 = str1[__reg3]
		holder = __reg0
		if (holder == "0"):
			__reg1.append("0000")
		else:
			if (__reg0 == "1"):
				__reg1.append("0001")
			else:
				if (__reg0 == "2"): 
					__reg1.append("0010")
				else: 
					if (__reg0 == "3"):
						__reg1.append("0011")
					else: 
						if (__reg0 == "4"):
							__reg1.append("0100")
						else: 
							if (__reg0 == "5"):
								__reg1.append("0101")
							else: 
								if (__reg0 == "6"):
									__reg1.append("0110")
								else: 
									if (__reg0 == "7"):
										__reg1.append("0111")
									else: 
										if (__reg0 == "8"):
											__reg1.append("1000")
										else: 
											if (__reg0 == "9"):
												__reg1.append("1001")
											else: 
												if (__reg0 == "a"):
													__reg1.append("1010")
												else: 
													if (__reg0 == "b"):
														__reg1.append("1011")
													else: 
														if (__reg0 == "c"):
															__reg1.append("1100")
														else: 
															if (__reg0 == "d"):
																__reg1.append("1101")
															else: 
																if (__reg0 == "e"):
																	__reg1.append("1110")
																else: 
																	if (__reg0 == "f"):
																		__reg1.append("1111")

		__reg3 = __reg3 + 1

	mtstr = ajoin(__reg1)
	__reg1 = asplit(mtstr)
	__reg6 = []
	__reg3 = 0
	while (__reg3 < 384):
	
		key1 = (int(key1) * 11 + 77213) % 81371
		key2 = (int(key2) * 17 + 92717) % 192811
		__reg6.append((int(key1) + int(key2)) % 128)
		__reg3 = __reg3 + 1
	
	__reg3 = 256
	while (__reg3 >= 0):

		__reg5 = __reg6[__reg3]
		__reg4 = __reg3 % 128
		__reg8 = __reg1[__reg5]
		__reg1[__reg5] = __reg1[__reg4]
		__reg1[__reg4] = __reg8
		__reg3 = __reg3 - 1
	
	__reg3 = 0
	while (__reg3 < 128):
	
		__reg1[__reg3] = int(__reg1[__reg3]) ^ int(__reg6[__reg3 + 256]) & 1
		__reg3 = __reg3 + 1

	__reg12 = ajoin(__reg1)
	__reg7 = []
	__reg3 = 0
	while (__reg3 < len(__reg12)):

		__reg9 = __reg12[__reg3:__reg3 + 4]
		__reg7.append(__reg9)
		__reg3 = __reg3 + 4
		
	
	__reg2 = []
	__reg3 = 0
	while (__reg3 < len(__reg7)):
		__reg0 = __reg7[__reg3]
		holder2 = __reg0
	
		if (holder2 == "0000"):
			__reg2.append("0")
		else: 
			if (__reg0 == "0001"):
				__reg2.append("1")
			else: 
				if (__reg0 == "0010"):
					__reg2.append("2")
				else: 
					if (__reg0 == "0011"):
						__reg2.append("3")
					else: 
						if (__reg0 == "0100"):
							__reg2.append("4")
						else: 
							if (__reg0 == "0101"): 
								__reg2.append("5")
							else: 
								if (__reg0 == "0110"): 
									__reg2.append("6")
								else: 
									if (__reg0 == "0111"): 
										__reg2.append("7")
									else: 
										if (__reg0 == "1000"): 
											__reg2.append("8")
										else: 
											if (__reg0 == "1001"): 
												__reg2.append("9")
											else: 
												if (__reg0 == "1010"): 
													__reg2.append("a")
												else: 
													if (__reg0 == "1011"): 
														__reg2.append("b")
													else: 
														if (__reg0 == "1100"): 
															__reg2.append("c")
														else: 
															if (__reg0 == "1101"): 
																__reg2.append("d")
															else: 
																if (__reg0 == "1110"): 
																	__reg2.append("e")
																else: 
																	if (__reg0 == "1111"): 
																		__reg2.append("f")
																	
		__reg3 = __reg3 + 1

	endstr = ajoin(__reg2)
	return endstr

########END OF PART 1

#Part 2
# Paste this into your Default.py
# To activate it just call Megavideo(url) - where url is your megavideo url.
def getcode(mega):
	if mega.startswith('http://www.megavideo.com/?d='):
		mega = mega[-8:]
	print mega
	return mega
     

#####END of part 2

def getlowurl(self,code):
	
	code=getcode(code)

	if os.path.exists(self.cookie) is False:
		req = urllib2.Request("http://www.megavideo.com/xml/videolink.php?v="+code)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14')
		req.add_header('Referer', 'http://www.megavideo.com/')
		page = urllib2.urlopen(req);response=page.read();page.close()
		errort = re.compile(' errortext="(.+?)"').findall(response)
		movielink = ""
		if len(errort) <= 0:
			s = re.compile(' s="(.+?)"').findall(response)
			k1 = re.compile(' k1="(.+?)"').findall(response)
			k2 = re.compile(' k2="(.+?)"').findall(response)
			un = re.compile(' un="(.+?)"').findall(response)
			sovielink = "http://www" + s[0] + ".megavideo.com/files/" + decrypt(un[0], k1[0], k2[0]) + "/?.flv"
			return sovielink

	elif os.path.exists(self.cookie) is True:
                #opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
		#urllib2.install_opener(opener)
		
		req = urllib2.Request("http://www.megavideo.com/xml/videolink.php?v="+code+"&u="+self.cookie)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14')
		req.add_header('Referer', 'http://www.megavideo.com/')
		page = urllib2.urlopen(req);response=page.read();page.close()
		print response
		errort = re.compile(' errortext="(.+?)"').findall(response)
		movielink = ""
		if len(errort) <= 0:
			s = re.compile(' s="(.+?)"').findall(response)
			k1 = re.compile(' k1="(.+?)"').findall(response)
			k2 = re.compile(' k2="(.+?)"').findall(response)
			un = re.compile(' un="(.+?)"').findall(response)
			movielink = "http://www" + s[0] + ".megavideo.com/files/" + decrypt(un[0], k1[0], k2[0]) + "/?.flv"
			return movielink

	
	

def gethighurl(self,code):
	code = getcode(code)

	megavideocookie = xbmcplugin.getSetting("megavideocookie")

	megavideologin = xbmcplugin.getSetting("megavideouser")

	megavideopassword = xbmcplugin.getSetting("megavideopassword")

	megavideocookie = GetMegavideoUser(megavideologin, megavideopassword)

	#xbmcplugin.setSetting("megavideocookie",megavideocookie)

	req = urllib2.Request("http://www.megavideo.com/xml/player_login.php?u="+megavideocookie+"&v="+code)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	data=response.read()
	response.close()
	
	# saca los enlaces
	patronvideos  = 'downloadurl="([^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	movielink = matches[0]
	movielink = movielink.replace("%3A",":")
	movielink = movielink.replace("%2F","/")
	movielink = movielink.replace("%20"," ")
	
	return movielink

def GetMegavideoUser(login, password, megavidcookiepath):
        #New Login code derived from old code by Voinage etc. Makes no need for mechanize module.
     

	#if no user or pass are provided, open login file to get them. 
	if login is False or password is False:
             if os.path.exists(megavidcookiepath):
               loginf=openfile(self.login)
               login=get_user(loginf)
               password=get_pass(loginf)

	# ---------------------------------------
	#  Cookie stuff
	# ---------------------------------------
	ficherocookies = megavidcookiepath
	# the path and filename to save your cookies in

	cj = None
	ClientCookie = None
	cookielib = None

	# Let's see if cookielib is available
	try:
		import cookielib
	except ImportError:
		# If importing cookielib fails
		# let's try ClientCookie
		try:
			import ClientCookie
		except ImportError:
			# ClientCookie isn't available either
			urlopen = urllib2.urlopen
			Request = urllib2.Request
		else:
			# imported ClientCookie
			urlopen = ClientCookie.urlopen
			Request = ClientCookie.Request
			cj = ClientCookie.LWPCookieJar()

	else:
		# importing cookielib worked
		urlopen = urllib2.urlopen
		Request = urllib2.Request
		cj = cookielib.LWPCookieJar()
		# This is a subclass of FileCookieJar
		# that has useful load and save methods

	# ---------------------------------
	# install the cookies
	# ---------------------------------

	if cj is not None:
	# we successfully imported
	# one of the two cookie handling modules

		if os.path.isfile(ficherocookies):
			# if we have a cookie file already saved
			# then load the cookies into the Cookie Jar
			cj.load(ficherocookies)

		# Now we need to get our Cookie Jar
		# installed in the opener;
		# for fetching URLs
		if cookielib is not None:
			# if we use cookielib
			# then we get the HTTPCookieProcessor
			# and install the opener in urllib2
			opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
			urllib2.install_opener(opener)

		else:
			# if we use ClientCookie
			# then we get the HTTPCookieProcessor
			# and install the opener in ClientCookie
			opener = ClientCookie.build_opener(ClientCookie.HTTPCookieProcessor(cj))
			ClientCookie.install_opener(opener)

	#print "-------------------------------------------------------"
	url="http://www.megavideo.com/?s=signup"
	#print url
	#print "-------------------------------------------------------"
	theurl = url
	# an example url that sets a cookie,
	# try different urls here and see the cookie collection you can make !

	txdata = "action=login&cnext=&snext=&touser=&user=&nickname="+login+"&password="+password
	# if we were making a POST type request,
	# we could encode a dictionary of values here,
	# using urllib.urlencode(somedict)

	txheaders =  {'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3',
				  'Referer':'http://www.megavideo.com/?s=signup'}
	# fake a user agent, some websites (like google) don't like automated exploration

	req = Request(theurl, txdata, txheaders)
	handle = urlopen(req)
	cj.save(ficherocookies)                     # save the cookies again    

	data=handle.read()

	handle.close()

	cookiedatafile = open(ficherocookies,'r')
	cookiedata = cookiedatafile.read()
	cookiedatafile.close();

	patronvideos  = 'user="([^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(cookiedata)
	if len(matches)==0:
		patronvideos  = 'user=([^\;]+);'
		matches = re.compile(patronvideos,re.DOTALL).findall(cookiedata)
	
	if len(matches)==0:
		print 'something bad happened'

	return matches[0]



