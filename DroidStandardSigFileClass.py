# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

import logging
import xml.etree.ElementTree as etree


class DroidStandardSigFileClass:
    def __init__(self, sigfile):
        self.sigfile = open(sigfile, "rb")

    # def __iterate_xml__(self):

    # given a puid, return an extension from droid signature file
    def retrieve_single_ext_text(self, puidtxt):
        xml_iter = self.__parse_xml__()
        for topelements in xml_iter:
            if (
                topelements.tag
                == "{http://www.nationalarchives.gov.uk/pronom/SignatureFile}FileFormatCollection"
            ):
                for fileformats in topelements:
                    puid = fileformats.get("PUID")
                    if puid == puidtxt:
                        for mapping in fileformats:
                            if (
                                mapping.tag
                                == "{http://www.nationalarchives.gov.uk/pronom/SignatureFile}Extension"
                            ):
                                # return first format extension
                                return mapping.text
                                break

    # given a list of puids, return all extensions from droid signature file
    def retrieve_ext_list(self, puid_list):
        xml_iter = self.__parse_xml__()
        puiddict = {}
        for topelements in xml_iter:
            if (
                topelements.tag
                == "{http://www.nationalarchives.gov.uk/pronom/SignatureFile}FileFormatCollection"
            ):
                for fileformats in topelements:
                    puid = fileformats.get("PUID")
                    for puids in puid_list:
                        if puid == puids:
                            ext = fileformats.find(
                                "{http://www.nationalarchives.gov.uk/pronom/SignatureFile}Extension"
                            )
                            if ext is not None:
                                # return first format extension
                                puiddict[puids] = ext.text
                                break
                            else:
                                puiddict[puids] = None
                                break

            # TODO: consider placement of this check, should it be handled here?
            notfound = []
            for p in puid_list:
                if p not in puiddict.keys():
                    if p not in notfound:
                        notfound.append(p)

            if len(notfound) > 0:
                for p in notfound:
                    puiddict[p] = "notfound"

        return puiddict

    def __parse_xml__(self):
        # parsing has to begin from seekpoint zero
        self.sigfile.seek(0)
        try:
            tree = etree.parse(self.sigfile)
            root = tree.getroot()
            return iter(root)
        except IOError as err:
            logging.error(err)
        return

    def __del__(self):
        if not self.sigfile.closed:
            self.sigfile.close()
