#!/usr/bin/env python

# Links and info about metacontainers.
# Update this file to update the containers.

# Size is in MB

#return dictionary of strings and integers
def get():
          containers = {} 

          #date updated
          containers['date'] = '9/Feb/2011'
          
          #--- Movie Meta Container ---# 

          #basic container        
          containers['mv_db_url'] = 'http://www.megaupload.com/?d=U1RTPGQS'
          containers['mv_covers_url'] = 'http://www.megaupload.com/?d=CE07S1EJ'
          containers['mv_db_base_size'] = 230

          #additional container
          containers['mv_add_url'] = ''
          containers['mv_add_size'] = 0


          #--- TV   Meta  Container ---#

          #basic container       
          containers['tv_db'] = ''
          containers['tv_base'] = ''
          containers['tv_db_base_size'] = 0

          #additional container
          containers['tv_add_url'] = ''
          containers['tv_add_size'] = 0       


          return containers
