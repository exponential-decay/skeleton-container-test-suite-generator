import os
import sys
import argparse
import xml.etree.ElementTree as etree
from DroidStandardSigFileClass import DroidStandardSigFileClass
import signature2bytegenerator
from io import BytesIO
from shutil import make_archive, rmtree

class SkeletonContainerGenerator:

	def __init__(self, containersig, standardsig, debug):

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
		self.debug = debug

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

		#invalid puids
		#cases seen where invalid puids have appeared in container signature file
		self.invalidpuids = []

		self.__createfolders__()

	def __del__(self):
		sys.stdout.write("No. container signatures identified: " + str(self.nocontainersigs) + "\n")
		sys.stdout.write("No. zip-based signatures identified: " + str(self.zipcount) + "\n")		
		sys.stdout.write("No. zip-based signatures written: " + str(self.zipwritten) + "\n")		
		sys.stdout.write("No. ole2-based signatures identified: " + str(self.ole2count) + "\n")
		sys.stdout.write("No. ole2-based signatures written: " + str(self.ole2written) + "\n")
		sys.stdout.write("No. other methods identified: " + str(self.othercount) + "\n")
		sys.stdout.write("No. container signatures written: " + str(self.ole2written + self.zipwritten) + "\n")

		if not self.debug:
			rmtree(self.skeletondebugfolder)

	def __runningjava__(self):
		import platform
		if platform.system() == 'Java':
			return True
		else:
			return False		

	def __createfolders__(self):
		self.skeletoncontainerdir = "skeleton-container-suite/"
		self.skeletondebugfolder = "skeleton-container-suite/skeleton-folders/"
		self.zipfolder = "skeleton-container-suite/zip/"
		self.ole2folder = "skeleton-container-suite/ole2/"
		if not os.path.exists(self.skeletoncontainerdir):
			os.mkdir(self.skeletoncontainerdir)  
		if not os.path.exists(self.skeletondebugfolder):
			os.mkdir(self.skeletondebugfolder)  
		if not os.path.exists(self.zipfolder):
			os.mkdir(self.zipfolder)  
		if not os.path.exists(self.ole2folder):
			os.mkdir(self.ole2folder)  

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
		if not os.path.exists(self.skeletondebugfolder + newpath):
			os.makedirs(self.skeletondebugfolder + newpath)	
		return filetocreate

	def handlecreatefile(self, path):
		skeletonfilepart = open(path, 'wb')
		return skeletonfilepart

	#TODO: make robust for multiple similar option syntax
	#TODO: unit tests will help understanding different scenarios
	def __replaceoptionsyntax__(self, ns):
		part1 = ns.find('[')
		part2 = ns.find(']') + 1
		replacement = ns[part1:part2].replace('[', '').replace(']', '').split('-',1)[0]
		ns = ns[0:part1] + replacement + ns[part2:]
		if '[' in ns:
			self.__replaceoptionsyntax__(ns)
		else:
			return ns

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

		#workaround for ['6'-'7'] issue
		if '[' in ns:
			ns = self.__replaceoptionsyntax__(ns)

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

		#cannot create a skeleton file for IDs attached to the same signature
		#list and warn...
		dupes_tmp = []
		dupes = []

		for i, y in enumerate(formatmappings.iter()):
			sigid = y.get('signatureId')
			puid = y.get('Puid')
			if sigid not in dupes_tmp:
				dupes_tmp.append(sigid)
			else:
				dupes.append(sigid)		
			if puid is not None:			#TODO: Why None?
				container_id_to_puid_map[sigid] = puid			

		if len(dupes) > 0:
			for d in dupes:
				sys.stderr.write("Cannot write a skeleton container file for duplicate IDs: " + str(d) + '\n')		

		return container_id_to_puid_map

	#non-existant puids might exist in signature file
	def removeinvalidpuidsfromextmapping(self, puiddict):
		puiddict_tmp = {}
		for p in puiddict:
			if puiddict[p] == 'notfound':
				self.invalidpuids.append(p)
				sys.stderr.write("PUID value/s not found in standard signature file: " + str(p) + "\n")
			else:
				puiddict_tmp[p] = puiddict[p]
		return puiddict_tmp

	#non-existant puids might exist in signature file
	def removeinvalidpuidsfromidpuidmapping(self, puid_id_map):
		for invalidpuid in self.invalidpuids:
			for id in puid_id_map:
				if puid_id_map[id] == invalidpuid:
					del puid_id_map[id]
					self.removeinvalidpuidsfromidpuidmapping(puid_id_map)
					break;
		return puid_id_map

	#create a dictionary filenames to use beased on ID
	def createcontainerfilenamedict(self, container_id_to_puid_map):

		puid_list = container_id_to_puid_map.values()

		idfilenamedict = {}

		StandardSignatureFileHandler = DroidStandardSigFileClass(self.standardsig)
		puidmapping = StandardSignatureFileHandler.retrieve_ext_list(puid_list)

		puidmapping = self.removeinvalidpuidsfromextmapping(puidmapping)

		if len(self.invalidpuids) > 0:
			container_id_to_puid_map = self.removeinvalidpuidsfromidpuidmapping(container_id_to_puid_map)

		import collections
		duplicate_list = [x for x, y in collections.Counter(puid_list).items() if y > 1]

		# swap keys so we can access dict via puid value
		puid2idmapping = dict((value, key) for key, value in container_id_to_puid_map.iteritems())

		#Note: False optimisation..?
		#if we have duplicate PUIDs handle these first and remove from lists...
		#duplicate puids can be written with different IDs, duplicate IDs can't
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
		fname = self.skeletondebugfolder + containerfilename
		zipname = make_archive(self.zipfolder + containerfilename, format="zip", root_dir=fname)   	
		os.rename(zipname, zipname.rsplit('.', 1)[0])
		#TODO: Actual gague of make_archive's success? 
		if zipname:
			self.zipwritten += 1

	def packageole2container(self, containerfilename):
		fname = self.skeletondebugfolder + containerfilename + '/'
		if self.java:
			ole2success = self.olewrite.writeContainer(fname, self.ole2folder, containerfilename)
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

						files = container.findall('Files/File')
						
						for f in files:
							path = f.find('Path')
							#E.g. ID 4060 Microsoft Project 2007 OLE2 has empty inner filename
       					#E.g. ID 10000 has directory encoded in path
							if path == None:
								#Q. if path is none, do we still need to make a file pointer...
								cf = self.handlecontainersignaturefilepaths('', containerfilename)
							else:
								cf = self.handlecontainersignaturefilepaths(path.text, containerfilename)					

							binarysigs = f.find('BinarySignatures')
							if binarysigs == None:
								cf.write("File empty. Data written by Skeleton Generator.")
								cf.close()
							else:
								filetowrite = self.handlecontainersignaturefilesigs(binarysigs)
								if cf is not None:
									cf.write(filetowrite.getvalue())									
									cf.close()
								
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
	
	def handlecontainersignaturefilepaths(self, innerfilename, containerfilename):
		containerfilename = containerfilename + '/'
		cf = None
		if innerfilename == '':
			sys.stderr.write("Cannot write file without a name: " + containerfilename + "\n")
			#self.handlecreatedirectories(containerfilename)
			#cf = self.handlecreatefile('files/' + containerfilename + '')
		else:
			containerfilename = containerfilename + innerfilename
			self.handlecreatedirectories(containerfilename)
			cf = self.handlecreatefile('skeleton-container-suite/skeleton-folders/' + containerfilename)
		return cf

	def dowriteseq(self, bio, bytes):
		for x in bytes:
			try:
				s = map(ord, x.decode('hex'))
				for y in s:
					bio.write(chr(y))
			except:
				sys.stderr.write("Sequence not mapped not mapped: " + str(bytes) + '\n\n')
		return bio

	def handlecontainersignaturefilesigs(self, innerfile):
			
		bio = BytesIO()
		sigcoll = innerfile.findall('InternalSignatureCollection/InternalSignature')

		minoff = 0
		maxoff = 0
		offset = 0
		seq = ''
		rightfrag = ''

		for sigs in sigcoll:
			offset = sigs.find('ByteSequence')
			if offset is not None:
				offset = offset.get('Reference')
			subseq = sigs.findall('ByteSequence/SubSequence')
			if subseq is not None:
				for sequences in subseq:		
					val = sequences.get('SubSeqMinOffset')
					minoff = 0 if val == None else val
					val = sequences.get('SubSeqMaxOffset')
					maxoff = 0 if val == None else val
					seq = ''
					sequence = sequences.find('Sequence')
					if sequence is not None:
						seq = sequence.text
					rightfrag = sequences.find('RightFragment')
					if rightfrag is not None:
						rminoff = 0 if rightfrag.attrib['MinOffset'] == None else rightfrag.attrib['MinOffset']
						seq = seq + '{' + rminoff + '}' + rightfrag.text

					seq = self.convertbytesequence(seq)
					bio = self.__writebytestream__(bio, offset, minoff, maxoff, seq)
		return bio

	def __writebytestream__(self, bio, offset, minoff, maxoff, seq):
		if seq != '':
			sig2map = signature2bytegenerator.Sig2ByteGenerator()	#TODO: New instance or not?
			if offset == 'BOFoffset':
				if int(maxoff) > 0:
					boffill = (int(maxoff) - int(minoff)) / 2
					seq = '{' + str(boffill) + '}' + seq
				bytes = sig2map.map_signature(minoff, seq, maxoff, 0)
				#bio.seek(0)	#TODO: Handle BOF sequences properly
				bio = self.dowriteseq(bio, bytes)
			elif offset == 'EOFoffset':
				bytes = sig2map.map_signature(0, seq, minoff, 0)
				bio.seek(0, os.SEEK_END)
				bio = self.dowriteseq(bio, bytes)
			else:		#treat as BOF
				bytes = sig2map.map_signature(minoff, seq, 0, 0)
				bio.seek(0)
				bio = self.dowriteseq(bio, bytes)
		return bio

def skeletonfilegeneration(containersig, standardsig, debug):

	skg = SkeletonContainerGenerator(containersig, standardsig, debug)
	skg.generateskeletonfiles()
	
	#Jython issues calling class destructor...
	if skg.java:		#TODO: Not appropriate way to invoke __del__()?
		skg.__del__()

	sys.exit(0)

def main():

   #	Usage: 	--con [container signature file]
   #	Usage: 	--sig [standard signature file]
   #	Handle command line arguments for the script
   parser = argparse.ArgumentParser(description='Generate skeleton container files from DROID container signatures.')

   #TODO: Consider optional and mandatory elements... behaviour might change depending on output...
   #other options droid csv and rosetta schema
   #NOTE: class on its own might be used to create a blank import csv with just static options
   parser.add_argument('--con', help='DROID Container Signature File.', default=False, required=True)
   parser.add_argument('--sig', help='DROID Standard Signature File.', default=False, required=True)
   parser.add_argument('--debug', help="Debug mode. Doesn't delete skeleton-folders directory.", default=False)

   if len(sys.argv)==1:
      parser.print_help()
      sys.exit(1)

   #	Parse arguments into namespace object to reference later in the script
   global args
   args = parser.parse_args()
   
   if args.con and args.sig:
		skeletonfilegeneration(args.con, args.sig, args.debug)
   else:
      parser.print_help()
      sys.exit(1)

if __name__ == "__main__":
   main()
