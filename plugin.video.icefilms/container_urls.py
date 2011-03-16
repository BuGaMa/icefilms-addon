#!/usr/bin/env python

# Links and info about metacontainers.
# Update this file to update the containers.

# Size is in MB

#return dictionary of strings and integers
def get():
          containers = { 

          #date updated
          date : '9/Feb/2011',
          
          #--- Movie Meta Container ---# 

          #basic container        
          mv_db_url : 'http://www.megaupload.com/?d=U1RTPGQS',
          mv_covers_url : 'http://www.megaupload.com/?d=CE07S1EJ',
          mv_db_base_size :230,

          #additional container
          mv_add_url : '',
          mv_add_size : 0,


          #--- TV   Meta  Container ---#

          #basic container       
          tv_db : '',
          tv_base : '',
          tv_db_base_size : 0,

          #additional container
          tv_add_url : '',
          tv_add_size : 0,          

          }

          return containers
