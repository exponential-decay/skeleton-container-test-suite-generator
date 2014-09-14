import os

from jarray import zeros
from java.io import FileOutputStream, FileInputStream, ByteArrayOutputStream

from org.apache.poi.poifs.filesystem import NPOIFSFileSystem

class WriteOLE2Containers():

	def __debugfos__(fos, bufsize):
		buf = zeros(bufsize, 'b')
		fin.read(buf)
		print buf

	def writeContainer(self, containerfoldername, outputfolder):

		written = False

		#we have folder name, written earlier
		#foldername is filename!!	
		if os.path.isdir(containerfoldername):
	
			fname = outputfolder + '/' + containerfoldername.split('/',1)[1].replace('/', '')

			fs = NPOIFSFileSystem()
			root = fs.getRoot();

			#triplet ([Folder], [sub-dirs], [files])
			for folder, subs, files in os.walk(containerfoldername):
				if subs != []:
					#TODO: cant't yet write directories		
					break
				else:
					for f in files:
						fin = FileInputStream(folder + f)
						if fin.getChannel().size() == 0:
							fin.close()
							written = False
							break
						else:
							root.createDocument(f, fin)
							fin.close()
							written = True

			if written == True:
				fos = FileOutputStream(fname)
				fs.writeFilesystem(fos);
				fs.close()

		return written

WriteOLE2Containers().writeContainer('ole2-tmp/fmt-39-container-signature-id-1000.doc/', 'ole2s/')
WriteOLE2Containers().writeContainer('ole2-tmp/fmt-233-container-signature-id-15000.wps/', 'ole2s/')
