import xml.etree.ElementTree as etree

class DroidStandardSigFileClass:

	def __init__(self, sigfile):
		self.sigfile = open(sigfile, 'rb')
	#def __iterate_xml__(self):

	#given a puid, return an extension from droid signature file
	def retrieve_single_ext_text(self, puidtxt):
		xml_iter = self.__parse_xml__()
		for topelements in xml_iter:
			if topelements.tag == '{http://www.nationalarchives.gov.uk/pronom/SignatureFile}FileFormatCollection':
				for fileformats in topelements:
					puid = fileformats.get("PUID")
					if puid == puidtxt:
						for mapping in fileformats:
							if mapping.tag == '{http://www.nationalarchives.gov.uk/pronom/SignatureFile}Extension':
								#return first format extension								
								return mapping.text
								break

	#given a list of puids, return all extensions from droid signature file
	def retrieve_ext_list(self, puid_list):
		xml_iter = self.__parse_xml__()
		puiddict = {}
		for topelements in xml_iter:
			if topelements.tag == '{http://www.nationalarchives.gov.uk/pronom/SignatureFile}FileFormatCollection':
				for fileformats in topelements:
					puid = fileformats.get("PUID")
					for puids in puid_list:
						if puid == puids:
							for mapping in fileformats:
								if mapping.tag == '{http://www.nationalarchives.gov.uk/pronom/SignatureFile}Extension':
									#return first format extension								
									puiddict[puids] = mapping.text
									break
		return puiddict

	def __parse_xml__(self):
		#parsing has to begin from seekpoint zero
		self.sigfile.seek(0)
		try:
			tree = etree.parse(self.sigfile)
			root = tree.getroot()
			return iter(root)
		except IOError as (errno, strerror):
			sys.stderr.write("IO error({0}): {1}".format(errno, strerror) + '\n')

		return 0

	def __del__(self):
		self.sigfile.close()

