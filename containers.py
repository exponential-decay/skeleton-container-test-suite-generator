import os
import sys
import argparse
import xml.etree.ElementTree as etree
from DroidStandardSigFileClass import DroidStandardSigFileClass
import signature2bytegenerator
from io import BytesIO
from shutil import make_archive

class SkeletonContainerGenerator:

	def __init__(self, containersig, standardsig):

		self.java = self.__runningjava__()		
		self.olewrite = None

		if not self.java:
			sys.stdout.write("Not using Jython. Writing ZIP containers only." + "\n")
		else:
			from JWriteOLE2Containers import WriteOLE2Containers
			self.olewrite = WriteOLE2Containers()

		self.INTSIGCOLLECTIONOFFSET = 0

		self.standardsig = standardsig
		self.containersig = containersig	

		#TODO: provide both signature files as arguments... 
		#TODO: verify arguments provided are actual sig files...
		self.containertree = self.__parse_xml__(self.containersig)

		#TODO: Counts, e.g. no. container signatuers held in file
		#TODO: If write folders don't exist, create...
		
		#stats
		self.nocontainersigs = 0
		self.zipcount = 0
		self.ole2count = 0
		self.zipwritten = 0
		self.ole2written = 0
		self.othercount = 0

	def __del__(self):
		sys.stdout.write("No. container signatures identified: " + str(self.nocontainersigs) + "\n")
		sys.stdout.write("No. zip-based signatures identified: " + str(self.zipcount) + "\n")		
		sys.stdout.write("No. zip-based signatures written: " + str(self.zipwritten) + "\n")		
		sys.stdout.write("No. ole2-based signatures identified: " + str(self.ole2count) + "\n")
		sys.stdout.write("No. ole2-based signatures written: " + str(self.ole2written) + "\n")
		sys.stdout.write("No. other methods identified: " + str(self.othercount) + "\n")

	def __runningjava__(self):
		import platform
		if platform.system() == 'Java':
			return True
		else:
			return False		

	def generateskeletonfiles(self):
		container_id_to_puid_map = self.mapcontaineridstopuids(self.containertree)
		filenamedict = self.createcontainerfilenamedict(container_id_to_puid_map)
		self.containersigfile(self.containertree, filenamedict)

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
		return skeletonfilepart

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
				if l[i].find('[') != -1 and l[i].find(']') != -1:
					vallist = l[i].replace('[', '').replace(']','').split(' ')
					for v in vallist:
						if v != '':
							ns += v
							break				
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

		#no. items under format mappings, i.e. no. container formats listed
		self.nocontainersigs = len(formatmappings)

		for i, y in enumerate(formatmappings.iter()):
			sigid = y.get('signatureId')
			puid = y.get('Puid')				
			if puid is not None:			#TODO: Why None?
				container_id_to_puid_map[sigid] = puid			
						
		return container_id_to_puid_map

	#create a dictionary filenames to use beased on ID
	def createcontainerfilenamedict(self, container_id_to_puid_map):

		puid_list = container_id_to_puid_map.values()

		idfilenamedict = {}

		StandardSignatureFileHandler = DroidStandardSigFileClass(self.standardsig)
		puidmapping = StandardSignatureFileHandler.retrieve_ext_list(puid_list)

		import collections
		duplicate_list = [x for x, y in collections.Counter(puid_list).items() if y > 1]

		# swap keys so we can access dict via puid value
		puid2idmapping = dict((value, key) for key, value in container_id_to_puid_map.iteritems())

		#Note: False optimisation..?
		for d in duplicate_list:
			for id in container_id_to_puid_map:
				if container_id_to_puid_map[id] == d:
					fmtid = id
					fmt = container_id_to_puid_map[id]
					idfilenamedict[fmtid] = fmt.replace('/', '-') + '-container-signature-id-' + str(fmtid) + '.' + str(puidmapping[container_id_to_puid_map[id]])
					container_id_to_puid_map[id] = 'done'

		#retrieve filename...
		#fmt-x-sig-id-xxxx.ext	
		for x in puid2idmapping:
			if x in puidmapping:	
				fmtid = puid2idmapping[x]
				fmt = x
				idfilenamedict[fmtid] = fmt.replace('/', '-') + '-container-signature-id-' + str(fmtid) + '.' + str(puidmapping[x])

		return idfilenamedict

	def packagezipcontainer(self, containerfilename):
		# do not need a complicated mechanism needed for zip it seems...
		fname = 'files/' + containerfilename
		zipname = make_archive('zips/' + containerfilename, format="zip", root_dir=fname)   	
		os.rename(zipname, zipname.rsplit('.', 1)[0])
		#TODO: Actual gague of make_archive's success? 
		if zipname:
			self.zipwritten += 1

	def packageole2container(self, containerfilename):
		fname = 'files/' + containerfilename + '/'
		if self.java:
			ole2success = self.olewrite.writeContainer(fname, 'ole2s/')
			if ole2success:
				self.ole2written += 1

	def containersigfile(self, containertree, filenamedict):

		for topelements in iter(containertree):
			if topelements.tag == 'ContainerSignatures':			
				#retrieving each container file type at this point...
				#create bytestream to write to and write to file... 				
				for container in topelements:
					containerid = container.get('Id')
					containertype = container.get('ContainerType')
					containerdesc = container.find('Description')

					cf = None
					filetowrite = None

					if containerid in filenamedict:	#TODO: Bug filtering too many filenmes/ids out, e.g. 1030, fmt/412
						containerfilename = filenamedict[containerid]	

						files = container.find('Files').iter()

						for innerfile in files:

							if innerfile.tag == 'Path':
								cf = self.handlecontainersignaturefilepaths(innerfile, containerfilename)

							if innerfile.tag == 'BinarySignatures':
								filetowrite = self.handlecontainersignaturefilesigs(innerfile)

							if cf != None and filetowrite != None:
								cf.write(filetowrite.getvalue())
								cf.close()

							elif cf != None and filetowrite == None:
								#Arbitrary data written so as to play well with POI OLE2 generation
								cf.write('Empty file. Data created by Skeleton Generator.')
								cf.close()

							#clean-up pointers to write to again...
							cf = None
							filetowrite = None
					
						#print containertype
						if containertype == 'ZIP':
							self.zipcount +=1
							self.packagezipcontainer(containerfilename)
						elif containertype == 'OLE2':
							self.ole2count+=1
							self.packageole2container(containerfilename)
						else:
							self.othercount+=1
							sys.stderr.write("Unknown container format discovered: " + str(containertype) + "\n")
	
	def handlecontainersignaturefilepaths(self, innerfile, containerfilename):
		containerfilename = containerfilename + '/'
		cf = None
		if innerfile.text == '':
			#self.handlecreatefile('files/')
			self.handlecreatedirectories(containerfilename)
		#if innerfile.text.find('/') == -1:
		#	self.handlecreatedirectories(containerfilename)
		#	self.handlecreatefile('files/' + innerfile.text)
		else:
			containerfilename = containerfilename + innerfile.text
			self.handlecreatedirectories(containerfilename)
			cf = self.handlecreatefile('files/' + containerfilename)
		return cf

	def dowriteseq(self, bio, bytes):
		for x in bytes:
			try:
				s = map(ord, x.decode('hex'))
				for y in s:
					bio.write(chr(y))
			except:
				sys.stderr.write("Sequence not mapped not mapped: " + seq + '\n\n')
		return bio

	def handlecontainersignaturefilesigs(self, innerfile):
			
		bio = BytesIO()
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
					val = signaturecomponents.get('SubSeqMinOffset')
					minoff = 0 if val == None else val
					maxoff = 0
					val = signaturecomponents.get('SubSeqMaxOffset')
					maxoff = 0 if val == None else val
				if signaturecomponents.tag == 'Sequence':
					#note strange square brackets in open office sequences
					seq = ''
					seq = self.convertbytesequence(signaturecomponents.text)	

				if seq != '':
					sig2map = signature2bytegenerator.Sig2ByteGenerator()	#TODO: New instance or not?
					if offset == 'BOFoffset':
						bytes = sig2map.map_signature(minoff, seq, maxoff, 0)
						#bio.seek(0)	#TODO: Handle BOF sequences properly
						bio = self.dowriteseq(bio, bytes)
					elif offset == 'EOFoffset':
						bytes = sig2map.map_signature(0, seq, minoff, 0)
						bio.seek(0, SEEK_END)
						bio = self.dowriteseq(bio, bytes)
					else:		#treat as BOF
						bytes = sig2map.map_signature(minoff, seq, 0, 0)
						bio.seek(0)
						bio = self.dowriteseq(bio, bytes)
		return bio

def skeletonfilegeneration(containersig, standardsig):

	skg = SkeletonContainerGenerator(containersig, standardsig)
	skg.generateskeletonfiles()

def main():

   #	Usage: 	--con [container signature file]
   #	Usage: 	--sig [standard signature file]
   #	Handle command line arguments for the script
   parser = argparse.ArgumentParser(description='Generate skeleton container files from DROID container signatures.')

   #TODO: Consider optional and mandatory elements... behaviour might change depending on output...
   #other options droid csv and rosetta schema
   #NOTE: class on its own might be used to create a blank import csv with just static options
   parser.add_argument('--con', help='Single DROID CSV to read.', default=False, required=False)
   parser.add_argument('--sig', help='Archway import schema to use.', default=False, required=False)

   if len(sys.argv)==1:
      parser.print_help()
      sys.exit(1)

   #	Parse arguments into namespace object to reference later in the script
   global args
   args = parser.parse_args()
   
   if args.con and args.sig:
		#TODO: Delete these once testing is complete...
		args.con = 'container-signature.xml'
		args.sig = 'sig-file.xml'
		skeletonfilegeneration(args.con, args.sig)
   else:
      parser.print_help()
      sys.exit(1)

if __name__ == "__main__":
   main()
