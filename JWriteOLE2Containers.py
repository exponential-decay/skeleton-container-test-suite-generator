import os

from jarray import zeros
from java.io import FileOutputStream, FileInputStream, ByteArrayOutputStream

from org.apache.poi.poifs.filesystem import NPOIFSFileSystem

class WriteOLE2Containers():

	def __debugfos__(fos, bufsize):
		buf = zeros(bufsize, 'b')
		fin.read(buf)
		print buf

	def writeContainer(self, containerfoldername, outputfolder, outputfilename):

		written = False

		#we have folder name, written earlier
		#foldername is filename!!	
		if os.path.isdir(containerfoldername):
	
			fname = outputfolder + outputfilename

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
				print fname
				fos = FileOutputStream(fname)
				fs.writeFilesystem(fos);
				fs.close()

		return written

