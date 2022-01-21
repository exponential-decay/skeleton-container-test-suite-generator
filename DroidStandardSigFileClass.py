# -*- coding: utf-8 -*-


"""Module for collecting information from the DROID signature files.
"""

from __future__ import print_function, unicode_literals

import logging
import xml.etree.ElementTree as etree


class DroidStandardSigFileClass:
    """Class encapsulating DROID signature file reading operations."""

    def __init__(self, sigfile):
        """Constructor for the DROID signature file handler class."""
        self.sigfile = open(sigfile, "rb")

    def __del__(self):
        """Deconstructor for the class object."""
        if not self.sigfile.closed:
            self.sigfile.close()

    def _parse_xml(self):
        """Parse an XML object and return its iterator."""
        self.sigfile.seek(0)  # Parsing has to begin from seek-point zero
        try:
            tree = etree.parse(self.sigfile)
            root = tree.getroot()
            return iter(root)
        except IOError as err:
            logging.error(err)
            return None
        return None

    def retrieve_single_ext_text(self, puid_txt):
        """Given a PUID return an extension from droid signature file.
        """
        xml_iter = self._parse_xml()
        mapping_text = None
        for topelements in xml_iter:
            if (
                topelements.tag
                == "{http://www.nationalarchives.gov.uk/pronom/SignatureFile}FileFormatCollection"
            ):
                for fileformats in topelements:
                    puid = fileformats.get("PUID")
                    if puid != puid_txt:
                        continue
                    for mapping in fileformats:
                        if (
                            mapping.tag
                            == "{http://www.nationalarchives.gov.uk/pronom/SignatureFile}Extension"
                        ):
                            # Return the first file format ext.
                            mapping_text = mapping.text
                            break
        return mapping_text

    def retrieve_ext_list(self, puid_list):
        """Given a list of PUIDS, return all extensions from droid
        signature file.
        """
        xml_iter = self._parse_xml()
        puiddict = {}
        for topelements in xml_iter:
            if (
                topelements.tag
                == "{http://www.nationalarchives.gov.uk/pronom/SignatureFile}FileFormatCollection"
            ):
                for fileformats in topelements:
                    puid = fileformats.get("PUID")
                    for puids in puid_list:
                        if puids != puid:
                            continue
                        ext = fileformats.find(
                            "{http://www.nationalarchives.gov.uk/pronom/SignatureFile}Extension"
                        )
                        if ext is not None:
                            # Return the first file format extension.
                            puiddict[puids] = ext.text
                            break
                        puiddict[puids] = None
                        break
            notfound = []
            for puid in puid_list:
                if puid not in puiddict:
                    if puid not in notfound:
                        notfound.append(puid)
            if len(notfound) > 0:
                for puid in notfound:
                    puiddict[puid] = "notfound"
        return puiddict
