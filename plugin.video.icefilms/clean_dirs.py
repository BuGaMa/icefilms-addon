#!/usr/bin/env python
# Copyright (c) 2005 Marc Butler.

# Hacked by Anarchintosh to run as a class.
# Used in Icefilms plugin to keep the download dir tidy.

# Search for and delete empty directories. If deleting
# an empty directory 'empties' it's parent dir. The parent
# dir will also be deleted.

# Remove all empty directories under dir.

import re
import os
import sys
import shutil

def FindEmptyDirs (dirlist, dirname, filenames):
    if filenames == []:
        dirlist.append(dirname)

def IsEmpty (dir):
    return os.listdir(dir) == []

def UnwindingDelete (emptydir):
    if not os.path.isdir(emptydir):
        return

    if not IsEmpty(emptydir):
        return

    os.rmdir(emptydir)
    UnwindingDelete(os.path.split(emptydir)[0])

class DirCleaner:

     def DelEmptyFolders(self,mypath):
         leaves = []
         os.path.walk(mypath, FindEmptyDirs, leaves)
         print 'Found and deleted %d empty dirs.' % (len(leaves))

         for d in leaves:
             UnwindingDelete(d)

