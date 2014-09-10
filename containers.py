import os
import sys
import argparse
import xml.etree.ElementTree as etree
from DroidStandardSigFileClass import DroidStandardSigFileClass
import signature2bytegenerator
from io import BytesIO
from shutil import make_archive

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

		for i, y in enumerate(formatmappings.iter()):
			sigid = y.get('signatureId')
			puid = y.get('Puid')				
			if puid is not None:			#TODO: WHy None?
				container_id_to_puid_map[sigid] = puid			
				
		return container_id_to_puid_map

	#create a dictionary filenames to use beased on ID
	def createcontainerfilenamedict(self, container_id_to_puid_map):

		idfilenamedict = {}

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
				idfilenamedict[fmtid] = fmt.replace('/', '-') + '-container-signature-id-' + str(fmtid) + '.' + str(puidmapping[x])

		return idfilenamedict

	def packagecontainer(self, containerfilename):
		# no more complicated mechanism needed for zip...
		fname = 'files/' + containerfilename
		zipname = make_archive('zips/' + containerfilename, format="zip", root_dir=fname)   	
		os.rename(zipname, zipname.rsplit('.', 1)[0])

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

								#clean-up pointers to write to again...
								cf = None
								filetowrite = None
						

						#print containertype
						if containertype == 'ZIP':
							self.packagecontainer(containerfilename)

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

	skg = SkeletonContainerGenerator()

	#TODO: provide both signature files as arguments... 
	#TODO: verify arguments provided are actual sig files...
	containertree = skg.__parse_xml__(containersig)


	container_id_to_puid_map = skg.mapcontaineridstopuids(containertree)
	filenamedict = skg.createcontainerfilenamedict(container_id_to_puid_map)
	skg.containersigfile(containertree, filenamedict)

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
		skeletonfilegeneration('container-signature.xml', 'sig-file.xml')
   else:
      parser.print_help()
      sys.exit(1)

if __name__ == "__main__":
   main()
