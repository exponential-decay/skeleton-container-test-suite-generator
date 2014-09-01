import os
import sys
import xml.etree.ElementTree as etree
from DroidStandardSigFileClass import DroidStandardSigFileClass
import signature2bytegenerator

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

StandardSignatureHandler = DroidStandardSigFileClass('sig-file.xml')

f = open('container-signature.xml', 'rb')

try:
	tree = etree.parse(f)
	root = tree.getroot()
	xml_iter = iter(root)

	id2puidmapping = {} 	#idmap
	puidmap = {}

	#list of puids in container signature file
	containerpuidlist = []

	formatmappings = root.find('FileFormatMappings')

	for i, y in enumerate(formatmappings.iter()):
		sigid = y.get('signatureId')
		puid = y.get('Puid')				
		id2puidmapping[sigid] = puid
		containerpuidlist.append(puid)	#len(puidlist) #one too many?
	
	puidmapping = StandardSignatureHandler.retrieve_ext_list(containerpuidlist)

	# swap keys so we can access dict via puid value
	puid2idmapping = dict((value, key) for key, value in id2puidmapping.iteritems())

	#retrieve filename...
	#fmt-x-sig-id-xxxx.ext	
	for x in puidmapping:
		if x in puid2idmapping:		
			fmtid = puid2idmapping[x]
			fmt = x
			#print fmt.replace('/', '-') + '-container-signature-id-' + str(fmtid) + '.' + str(puidmapping[x])

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
									seq = convertbytesequence(signaturecomponents.text)	

								if seq != '':
										#todo, output to file...
									sig2map = signature2bytegenerator.Sig2ByteGenerator()	#TODO: New instance or not?
									if offset == 'BOFoffset':
										bytes = sig2map.map_signature(minoff, seq, 0, 0)
									elif offset == 'EOFoffset':
										bytes = sig2map.map_signature(0, seq, minoff, 0)
									else:		#treat as BOF
										bytes = sig2map.map_signature(minoff, seq, 0, 0)
									print seq
									print bytes

									#for x in bof_sequence:
									#	try:
									#		s = map(ord, x.decode('hex'))
									#		for y in s:
									#			self.nt_file.write(chr(y))
									#	except:
									#		sys.stderr.write("BOF Signature not mapped: " + seq + '\n\n')


except IOError as (errno, strerror):
	sys.stderr.write("IO error({0}): {1}".format(errno, strerror) + '\n')

f.close()

