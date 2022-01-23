# -*- coding: utf-8 -*-

"""Module for collecting functions associated with writing OLE2 based
skeletons.
"""

from __future__ import print_function, unicode_literals

import logging
import os

try:
    from java.io import FileInputStream, FileOutputStream
    from org.apache.poi.poifs.filesystem import POIFSFileSystem
except ImportError as err:
    logging.error(
        "Problem importing Jython libraries, ensure Jython is being used: %s", err
    )
    raise err


class WriteOLE2Containers:
    """OLE2 Container writing class to encapsulate write functions for
    OLE2 based objects.
    """

    @staticmethod
    def writeContainer(containerfoldername, outputfolder, outputfilename):
        """Write OLE2 container file."""
        written = False
        # We have a folder name, written earlier, folder name is filename...
        if not os.path.isdir(containerfoldername):
            return written
        fname = os.path.join(outputfolder, outputfilename)
        fs = POIFSFileSystem()
        root = fs.getRoot()
        # Triplet ([Folder], [sub-dirs], [files]).
        for folder, subs, files in os.walk(containerfoldername):
            if subs != []:
                logging.error("Cannot yet write directories using this utility: %s", containerfoldername)
                break
            for file_ in files:
                fin = FileInputStream(os.path.join(folder, file_))
                if fin.getChannel().size() == 0:
                    fin.close()
                    written = False
                    break
                root.createDocument(file_, fin)
                fin.close()
                written = True
        if written is True:
            fos = FileOutputStream(fname)
            fs.writeFilesystem(fos)
            fs.close()
        return written
