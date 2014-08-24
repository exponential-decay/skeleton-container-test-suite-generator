import os
import sys
import xml.etree.ElementTree as etree
from DroidStandardSigFileClass import DroidStandardSigFileClass

def handlecreatedirectories(path):
	pathlist = path.split('/')
	filetocreate = pathlist.pop()	#return and remove filepart from filepath
	newpath = ""
	for folder in pathlist:
		newpath = newpath + folder + '/'
	if not os.path.exists('files/' + newpath):
		os.makedirs('files/' + newpath)	
	return filetocreate

def handlecreatefile(path):
	skeletonfilepart = open(path, 'wb')
	skeletonfilepart.close()

def convertbytesequence(sequence):
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


INTSIGCOLLECTIONOFFSET = 0

dclass = DroidStandardSigFileClass('sig-file.xml')

f = open('container-signature.xml', 'rb')

try:
	tree = etree.parse(f)
	root = tree.getroot()
	xml_iter = iter(root)

	fmtmap = {} 	#idmap
	puidmap = {}

	puidlist = []

	formatmappings = root.find('FileFormatMappings')

	for i, y in enumerate(formatmappings.iter()):
		sigid = y.get('signatureId')
		puid = y.get('Puid')				
		fmtmap[sigid] = puid
		puidlist.append(puid)	#len(puidlist) #one too many?

	print fmtmap
	puidmapping = dclass.retrieve_ext_list(puidlist)
	print len(puidmapping)
	print puidmapping

	#makefilenames()
	#fmt-x-sig-id-xxxx.ext
	#no ext in container sig file... process after std puids?-use sig file?!

	#need to feed filename and id into the parsing of container signatures
	#parse signature, read ID and filename, write file

	for topelements in xml_iter:

		if topelements.tag == 'ContainerSignatures':			
			for containertags in topelements:

				containerid = containertags.get('Id')
				containertype = containertags.get('ContainerType')
				containerdesc = containertags.find('Description')
				
				files = containertags.find('Files').iter()
				for innerfile in files:
					if innerfile.tag == 'Path':
						if innerfile.text == '':
							sys.stderr.write('Empty path in container signature')						
						if innerfile.text.find('/') == -1:
							handlecreatefile('files/' + innerfile.text)
						else:
							handlecreatedirectories(innerfile.text)
							handlecreatefile('files/' + innerfile.text)
					if innerfile.tag == 'BinarySignatures':
						sigcoll = innerfile[INTSIGCOLLECTIONOFFSET]
						for internalsig in sigcoll:
							signatureiter = internalsig.iter()
							for signaturecomponents in signatureiter:
								if signaturecomponents.tag == 'ByteSequence':
									offset = signaturecomponents.get('Reference')  #note: treat none as BOF
								if signaturecomponents.tag == 'SubSequence':
									minoff = signaturecomponents.get('SubSeqMinOffset')
									maxoff = signaturecomponents.get('SubSeqMaxOffset')
								if signaturecomponents.tag == 'Sequence':
									#note strange square brackets in open office sequences
									seq = convertbytesequence(signaturecomponents.text)									
									
except IOError as (errno, strerror):
	sys.stderr.write("IO error({0}): {1}".format(errno, strerror) + '\n')

f.close()

