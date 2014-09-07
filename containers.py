import os
import sys
import xml.etree.ElementTree as etree
from DroidStandardSigFileClass import DroidStandardSigFileClass
import signature2bytegenerator

class SkeletonContainerGenerator:

	INTSIGCOLLECTIONOFFSET = 0

	#TODO Counts, e.g. no. container signatuers held in file

	def handlecreatedirectories(self, path):
		pathlist = path.split('/')
		filetocreate = pathlist.pop()	#return and remove filepart from filepath
		newpath = ""
		for folder in pathlist:
			newpath = newpath + folder + '/'
		if not os.path.exists('files/' + newpath):
			os.makedirs('files/' + newpath)	
		return filetocreate

	def handlecreatefile(self, path):
		skeletonfilepart = open(path, 'wb')
		skeletonfilepart.close()

	def convertbytesequence(self, sequence):
		#source; https://gist.github.com/richardlehane/f71a0e8f15c99c805ec4 
		#testsig = "10 00 00 00 'Word.Document.' ['6'-'7'] 00"
		l = sequence.split("'")
		ns = ""

		for i in range(len(l)):
			#split assumes a space if starts/terminates with delimeter
			#even number of single-quotes means every-other character needs converting
			#no delimiter no split...	
			if i % 2 != 0:			
				ns += "".join([hex(ord(x))[2:] for x in l[i]])
			else:
				ns += l[i]

		return ns.replace(" ", "")

	def __parse_xml__(self, xmlfile):
		f = open(xmlfile, 'rb')
		try:
			tree = etree.parse(f)
			f.close()		
			return tree.getroot()
		except IOError as (errno, strerror):
			sys.stderr.write("IO error({0}): {1}".format(errno, strerror) + '\n')
			f.close()

	#create a dictionary of puids based on ID
	def mapcontaineridstopuids(self, containertree):

		container_id_to_puid_map = {}

		formatmappings = containertree.find('FileFormatMappings')

		for i, y in enumerate(formatmappings.iter()):
			sigid = y.get('signatureId')
			puid = y.get('Puid')				
			if puid is not None:			#TODO: WHy None?
				container_id_to_puid_map[sigid] = puid			
				
		return container_id_to_puid_map

	#create a dictionary filenames to use beased on ID
	def createcontainerfilenamedict(self, container_id_to_puid_map):

		idfilenameict = {}

		StandardSignatureFileHandler = DroidStandardSigFileClass('sig-file.xml')
		puidmapping = StandardSignatureFileHandler.retrieve_ext_list(container_id_to_puid_map.values())

		# swap keys so we can access dict via puid value
		puid2idmapping = dict((value, key) for key, value in container_id_to_puid_map.iteritems())

		#retrieve filename...
		#fmt-x-sig-id-xxxx.ext	
		for x in puidmapping:
			if x in puid2idmapping:		
				fmtid = puid2idmapping[x]
				fmt = x
				idfilenameict[fmtid] = fmt.replace('/', '-') + '-container-signature-id-' + str(fmtid) + '.' + str(puidmapping[x])

		return idfilenameict

	def containersigfile(self, containertree):

		for topelements in iter(containertree):

			if topelements.tag == 'ContainerSignatures':			
				for containertags in topelements:

					containerid = containertags.get('Id')
					containertype = containertags.get('ContainerType')
					containerdesc = containertags.find('Description')
			
					files = containertags.find('Files').iter()
					for innerfile in files:
						if innerfile.tag == 'Path':
							self.handlecontainersignaturefilepaths(innerfile)

						if innerfile.tag == 'BinarySignatures':
							self.handlecontainersignaturefilesigs(innerfile)

	def handlecontainersignaturefilepaths(self, innerfile):

		if innerfile.text == '':
			sys.stderr.write('Empty path in container signature')						
		if innerfile.text.find('/') == -1:
			self.handlecreatefile('files/' + innerfile.text)
		else:
			self.handlecreatedirectories(innerfile.text)
			self.handlecreatefile('files/' + innerfile.text)

	def handlecontainersignaturefilesigs(self, innerfile):
		
		sigcoll = innerfile[self.INTSIGCOLLECTIONOFFSET]

		minoff = 0
		maxoff = 0
		offset = 0
		seq = ''
		for internalsig in sigcoll:
			signatureiter = internalsig.iter()
			for signaturecomponents in signatureiter:
				if signaturecomponents.tag == 'ByteSequence':
					offset = 0
					offset = signaturecomponents.get('Reference')  #note: treat none as BOF
				if signaturecomponents.tag == 'SubSequence':
					minoff = 0
					minoff = signaturecomponents.get('SubSeqMinOffset')
					maxoff = 0
					maxoff = signaturecomponents.get('SubSeqMaxOffset')
				if signaturecomponents.tag == 'Sequence':
					#note strange square brackets in open office sequences
					seq = ''
					seq = self.convertbytesequence(signaturecomponents.text)	

				if seq != '':
						#todo, output to file...
					sig2map = signature2bytegenerator.Sig2ByteGenerator()	#TODO: New instance or not?
					if offset == 'BOFoffset':
						bytes = sig2map.map_signature(minoff, seq, 0, 0)
					elif offset == 'EOFoffset':
						bytes = sig2map.map_signature(0, seq, minoff, 0)
					else:		#treat as BOF
						bytes = sig2map.map_signature(minoff, seq, 0, 0)
					#print seq
					#print bytes




skg = SkeletonContainerGenerator()
containertree = skg.__parse_xml__('container-signature.xml')
container_id_to_puid_map = skg.mapcontaineridstopuids(containertree)
filenamedict = skg.createcontainerfilenamedict(container_id_to_puid_map)
skg.containersigfile(containertree)
