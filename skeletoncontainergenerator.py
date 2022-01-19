# -*- coding: utf-8 -*-
from __future__ import print_function

import argparse
import collections
from io import BytesIO
import logging
import os
from shutil import rmtree
import sys
import zipfile

import xml.etree.ElementTree as etree

from DroidStandardSigFileClass import DroidStandardSigFileClass
import signature2bytegenerator

LOGFORMAT = (
    "%(asctime)-15s %(levelname)s: %(filename)s:%(lineno)s:%(funcName)s(): %(message)s"
)
DATEFORMAT = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(format=LOGFORMAT, datefmt=DATEFORMAT, level="INFO")


class ContainerPart:
    """Maintain state amongst container parts."""

    pos = None
    offset = None
    minoff = None
    maxoff = None
    seq = None

    def __eq__(self, other):
        """Test for equivalent positioning."""
        return (
            self.pos == other.pos
            and self.offset == other.offset
            and self.minoff == other.minoff
            and self.maxoff == other.maxoff
        )


class SkeletonContainerGenerator:
    """Class concerned  with generating a skeleton file for a single container
    sequence in PRONOM.
    """

    def __init__(self, containersig, standardsig, debug):
        """Initialize stats."""

        self.java = self.__runningjava__()
        self.olewrite = None

        if not self.java:
            print("Not using Jython. Writing ZIP containers only.")
        else:
            from JWriteOLE2Containers import WriteOLE2Containers

            self.olewrite = WriteOLE2Containers()

        self.INTSIGCOLLECTIONOFFSET = 0

        self.standardsig = standardsig
        self.containersig = containersig
        self.debug = debug

        # TODO: verify arguments provided are actual sig files...
        self.containertree = self.__parse_xml__(self.containersig)

        # TODO: Counts, e.g. no. container signatuers held in file
        # TODO: If write folders don't exist, create...

        # stats
        self.nocontainersigs = 0
        self.zipcount = 0
        self.ole2count = 0
        self.zipwritten = 0
        self.ole2written = 0
        self.othercount = 0

        self.notwritten = []

        # Invalid PUIDS: Cases seen where invalid PUIDs have appeared in
        # container signature file
        self.invalidpuids = []

        self.__createfolders__()

    def __del__(self):
        print("No. container signatures identified: {}".format(self.nocontainersigs))
        print("No. zip-based signatures identified: {}".format(self.zipcount))
        print("No. zip-based signatures written: {}".format(self.zipwritten))
        print("No. ole2-based signatures identified: {}".format(self.ole2count))
        print("No. ole2-based signatures written: {}".format(self.ole2written))
        print("No. other methods identified: {}".format(self.othercount))
        print(
            "No. container signatures written: {}".format(
                self.ole2written + self.zipwritten
            )
        )
        if len(self.notwritten) > 0:
            print("Not written:")
            for nooutput in self.notwritten:
                print("  {}".format(nooutput))

        if not self.debug:
            rmtree(self.skeletondebugfolder)

    def __runningjava__(self):
        import platform

        if platform.system() == "Java":
            return True
        else:
            return False

    def __createfolders__(self):
        self.skeletoncontainerdir = os.path.join("skeleton-container-suite")
        self.skeletondebugfolder = os.path.join(
            "skeleton-container-suite", "skeleton-folders"
        )
        self.zipfolder = os.path.join("skeleton-container-suite", "zip")
        self.ole2folder = os.path.join("skeleton-container-suite", "ole2")
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
        pathlist = path.split(os.path.sep)
        filetocreate = pathlist.pop()  # remove filepart from filepath
        newpath = ""
        for folder in pathlist:
            newpath = os.path.join(newpath, folder)
        skeleton_debug_folder = os.path.join(self.skeletondebugfolder, newpath)
        if not os.path.exists(skeleton_debug_folder):
            os.makedirs(skeleton_debug_folder)
        return filetocreate

    def handlecreatefile(self, path_):
        skeletonfilepart = open(path_, "wb")
        return skeletonfilepart

    # TODO: make robust for multiple similar option syntax
    # TODO: unit tests will help understanding different scenarios
    def __replaceoptionsyntax__(self, ns):
        part1 = ns.find("[")
        part2 = ns.find("]") + 1
        replacement = ns[part1:part2].replace("[", "").replace("]", "").split("-", 1)[0]
        ns = "{}{}{}".format(ns[0:part1], replacement, ns[part2:])
        if "[" in ns:
            self.__replaceoptionsyntax__(ns)
        else:
            return ns

    def convertbytesequence(self, sequence):
        # source; https://gist.github.com/richardlehane/f71a0e8f15c99c805ec4
        # testsig = "10 00 00 00 'Word.Document.' ['6'-'7'] 00"

        if "'" in sequence:
            seqlist = sequence.split("'")
        else:
            sig2map = signature2bytegenerator.Sig2ByteGenerator()
            seqlist = sig2map.map_signature(0, sequence, 0, 0)
            # TODO: This feels like a bit of a hack, improve...
            seqlist = "".join(seqlist).replace(" ", "").split("'")

        ns = ""

        for i in range(len(seqlist)):
            # split assumes a space if starts/terminates with delimiter
            # even number of single-quotes means every-other character needs
            # converting no delimiter no split...
            if i % 2 != 0:
                ns += "".join([hex(ord(x))[2:] for x in seqlist[i]])
            else:
                # IF example:
                # ['', 'office:version=', ' [22 27] ', '1.0', ' [22 27]']
                if seqlist[i].find("[") != -1 and seqlist[i].find("]") != -1:
                    vallist = seqlist[i].replace("[", "").replace("]", "").split(" ")
                    for v in vallist:
                        if v != "":
                            ns += v
                            break
                else:
                    ns += seqlist[i]

        # workaround for ['6'-'7'] issue
        if "[" in ns:
            ns = self.__replaceoptionsyntax__(ns)

        return ns.replace(" ", "")

    def __parse_xml__(self, xmlfile):
        f = open(xmlfile, "rb")
        try:
            tree = etree.parse(f)
            f.close()
            return tree.getroot()
        except IOError as err:
            print("IO error: {}".format(err), file=sys.stderr)
            f.close()

    def mapcontaineridstopuids(self, containertree):
        """Create a dictionary of puids based on ID."""
        container_id_to_puid_map = {}
        formatmappings = containertree.find("FileFormatMappings")

        # no. items under format mappings, i.e. no. container formats listed
        self.nocontainersigs = len(formatmappings)

        # cannot create a skeleton file for IDs attached to the same signature
        # list and warn...
        dupes_tmp = []
        dupes = []

        for i, y in enumerate(formatmappings.iter()):
            sigid = y.get("signatureId")
            puid = y.get("Puid")
            if sigid not in dupes_tmp:
                dupes_tmp.append(sigid)
            else:
                dupes.append(sigid)
            if puid is not None:
                container_id_to_puid_map[sigid] = puid

        if len(dupes) > 0:
            for duplicate in dupes:
                out = "Cannot write a skeleton container file for duplicate IDs: {}".format(
                    duplicate
                )
                print(out, file=sys.stderr)

        return container_id_to_puid_map

    def removeinvalidpuidsfromextmapping(self, puiddict):
        """Non-existent puids might exist in signature file."""
        puiddict_tmp = {}
        for p in puiddict:
            if puiddict[p] == "notfound":
                self.invalidpuids.append(p)
                print(
                    "PUID values not found in standard signature file: {}".format(p),
                    file=sys.stderr,
                )
            else:
                puiddict_tmp[p] = puiddict[p]
        return puiddict_tmp

    def removeinvalidpuidsfromidpuidmapping(self, puid_id_map):
        """Non-existent puids might exist in signature file."""
        for invalidpuid in self.invalidpuids:
            for id in puid_id_map:
                if puid_id_map[id] == invalidpuid:
                    del puid_id_map[id]
                    self.removeinvalidpuidsfromidpuidmapping(puid_id_map)
                    break
        return puid_id_map

    def createcontainerfilenamedict(self, container_id_to_puid_map):
        """Create a dictionary filenames to use beased on ID."""
        puid_list = container_id_to_puid_map.values()
        idfilenamedict = {}
        StandardSignatureFileHandler = DroidStandardSigFileClass(self.standardsig)
        puidmapping = StandardSignatureFileHandler.retrieve_ext_list(puid_list)
        puidmapping = self.removeinvalidpuidsfromextmapping(puidmapping)
        if len(self.invalidpuids) > 0:
            container_id_to_puid_map = self.removeinvalidpuidsfromidpuidmapping(
                container_id_to_puid_map
            )

        duplicate_list = [x for x, y in collections.Counter(puid_list).items() if y > 1]

        # swap keys so we can access dict via puid value
        puid2idmapping = dict(
            (value, key) for key, value in container_id_to_puid_map.iteritems()
        )

        # Is this a false optimization?
        #
        # If we have duplicate PUIDs handle these first and remove from
        # lists. Duplicate puids can be written with different IDs,
        # duplicate IDs can't.
        for d in duplicate_list:
            for id in container_id_to_puid_map:
                if container_id_to_puid_map[id] == d:
                    fmtid = id
                    fmt = container_id_to_puid_map[id]
                    idfilenamedict[fmtid] = "{}-container-signature-id-{}.{}".format(
                        fmt.replace("/", "-"),
                        fmtid,
                        puidmapping[container_id_to_puid_map[id]],
                    )
                    container_id_to_puid_map[id] = "done"

        # Generate filename: fmt-x-sig-id-xxxx.ext
        for x in puid2idmapping:
            if x in puidmapping:
                fmtid = puid2idmapping[x]
                fmt = x
                idfilenamedict[fmtid] = "{}-container-signature-id-{}.{}".format(
                    fmt.replace("/", "-"), fmtid, puidmapping[x]
                )

        return idfilenamedict

    def packagezipcontainer(self, containerfilename):
        """Package up the contents we need in our zip."""
        fname = os.path.join(self.skeletondebugfolder, containerfilename)
        zip_name = os.path.join(self.zipfolder, containerfilename)
        self.write_zip_contents(fname, zip_name)
        self.zipwritten += 1

    @staticmethod
    def write_zip_contents(zip_root, zip_name):
        """Write the contents of our zip container directory to a file."""
        zip_contents = []
        for dir_, _, files in os.walk(zip_root):
            relative_dir = os.path.relpath(dir_, zip_root)
            # If we end up with just a '.' we're at the root of the
            # structure and so we don't want to write that.
            if relative_dir != ".":
                zip_contents.append(relative_dir)
            for file_name in files:
                relative_file = os.path.join(relative_dir, file_name)
                zip_contents.append(relative_file)
        with zipfile.ZipFile(zip_name, "w") as myzip:
            for file_ in set(zip_contents):
                myzip.write(filename=os.path.join(zip_root, file_), arcname=file_)

    def packageole2container(self, containerfilename):
        fname = os.path.join(self.skeletondebugfolder, containerfilename)
        if self.java:
            ole2success = self.olewrite.writeContainer(
                fname, self.ole2folder, containerfilename
            )
            if ole2success:
                self.ole2written += 1
            else:
                self.notwritten.append(containerfilename)

    def containersigfile(self, containertree, filenamedict):
        for topelements in iter(containertree):
            if topelements.tag == "ContainerSignatures":
                # Retrieving each container file type at this point...
                # create bytestream to write to and write to file...
                for container in topelements:
                    containerid = container.get("Id")
                    containertype = container.get("ContainerType")

                    # TODO: Use container description?
                    _ = container.find("Description")

                    cf = None
                    filetowrite = None

                    # TODO: Bug filtering too many filenames/ids out,
                    # e.g. 1030, fmt/412
                    if containerid not in filenamedict:
                        continue

                    containerfilename = filenamedict[containerid]

                    files = container.findall("Files/File")
                    for f in files:
                        path = f.find("Path")
                        # E.g. ID 4060 Microsoft Project 2007 OLE2 has
                        # empty inner filename.
                        # E.g. ID 10000 has directory encoded in path.
                        if path is None:
                            # Q. if path is none, do we still need to make
                            # a file pointer..?
                            cf = self.handlecontainersignaturefilepaths(
                                None, containerfilename
                            )
                        else:
                            cf = self.handlecontainersignaturefilepaths(
                                path.text, containerfilename
                            )
                        if cf:
                            binarysigs = f.find("BinarySignatures")
                            if binarysigs is None:
                                cf.write(
                                    "File empty. Data written by Skeleton Generator."
                                )
                                cf.close()
                            else:
                                if cf is not None:
                                    filetowrite = self.handlecontainersignaturefilesigs(
                                        binarysigs, containerfilename
                                    )
                                if cf is not None:
                                    cf.write(filetowrite.getvalue())
                                    cf.close()

                    # Print containertype
                    if containertype == "ZIP":
                        self.zipcount += 1
                        self.packagezipcontainer(containerfilename)
                    elif containertype == "OLE2":
                        self.ole2count += 1
                        self.packageole2container(containerfilename)
                    else:
                        self.othercount += 1
                        out = "Unknown container format discovered: {}".format(
                            containertype
                        )
                        print(out, file=sys.stderr)

    def handlecontainersignaturefilepaths(self, innerfilename, containerfilename):
        containerfilename = os.path.join(containerfilename)
        cf = None
        if innerfilename is None:
            print(
                "Cannot write file without a name: {}".format(containerfilename),
                file=sys.stderr,
            )
        else:
            containerfilename = os.path.join(containerfilename, innerfilename)
            self.handlecreatedirectories(containerfilename)
            try:
                path_ = os.path.join(
                    "skeleton-container-suite", "skeleton-folders", containerfilename
                )
                cf = self.handlecreatefile(path_)
            except IOError:
                return None
        return cf

    def dowriteseq(self, containerfilename, bio, bytes_):
        for byte in bytes_:
            try:
                string = map(ord, byte.replace("\n", "").decode("hex"))
                for char in string:
                    bio.write(chr(char))
            except TypeError as err:
                out = "Sequence for file {} not mapped: {} with err: {}".format(
                    containerfilename, str(byte), err
                )
                print(out, file=sys.stderr)
        return bio

    def handlecontainersignaturefilesigs(self, innerfile, containerfilename):

        bio = BytesIO()
        sigcoll = innerfile.findall("InternalSignatureCollection/InternalSignature")

        minoff = 0
        maxoff = 0
        offset = 0
        seq = ""
        rightfrag = ""

        subs = False
        parts = []

        for sigs in sigcoll:

            offset = sigs.find("ByteSequence")
            if offset is not None:
                offset = offset.get("Reference")
            subseq = sigs.findall("ByteSequence/SubSequence")
            if subseq is not None:

                subs = True

                for sequences in subseq:

                    cp = ContainerPart()

                    pos = sequences.get("Position")
                    val = sequences.get("SubSeqMinOffset")
                    minoff = 0 if val is None else val
                    val = sequences.get("SubSeqMaxOffset")
                    maxoff = 0 if val is None else val
                    seq = ""
                    sequence = sequences.find("Sequence")
                    if sequence is not None:
                        seq = sequence.text
                    rightfrag = sequences.find("RightFragment")
                    if rightfrag is not None:
                        rminoff = (
                            0
                            if rightfrag.attrib["MinOffset"] is None
                            else rightfrag.attrib["MinOffset"]
                        )
                        seq = "{}{{{}}}{}".format(seq, rminoff, rightfrag.text)

                    cp.seq = self.convertbytesequence(seq)
                    cp.pos = pos
                    cp.offset = offset
                    cp.minoff = minoff
                    cp.maxoff = maxoff

                    parts.append(cp)

        # We gotta do some pre-processing.
        if subs is True:
            if len(parts) > 0:
                if len(parts) > 1:

                    # Need to process the sequences for multiple BOF here.
                    bofcount = 0
                    for p in parts:
                        if "BOFoffset" in p.offset:
                            bofcount += 1

                    # this is a bit hacky but it's gonna work...
                    bio = self.__preprocessbofs__(bio, parts, containerfilename)

                    if bofcount > 2:
                        out = "Check: {}: Code might not yet handle more than two sequences...".format(
                            containerfilename
                        )
                        print(out, file=sys.stderr)

                    print("---", file=sys.stderr)

                else:
                    bio = self.__writebytestream__(
                        containerfilename,
                        bio,
                        parts[0].offset,
                        parts[0].minoff,
                        parts[0].maxoff,
                        parts[0].seq,
                    )

        return bio

    def __preprocessbofs__(self, bio, parts, containerfilename):
        """Pre-process BOF sequences where the PRONOM layout is confusing..."""
        equiv = False

        if parts[0] == parts[1]:
            equiv = True
            out = "{} has equivalent BOF sequences".format(containerfilename)
            print(out, file=sys.stderr)
            for p in parts:
                out = "{} {} {} {} {}".format(
                    p.offset, p.pos, p.minoff, p.maxoff, p.seq
                )
                print(out, file=sys.stderr)
            parts[0].maxoff = len(parts[0].seq) / 2 + 1
        elif int(parts[1].minoff) > 0:
            out = "{} BOF two offset greater than zero".format(containerfilename)
            print(out, file=sys.stderr)
            # create a new minimum offset...
            new_minoff = int(parts[1].minoff) - len(parts[0].seq) / 2
            parts[1].minoff = str(new_minoff)
            for p in parts:
                print("min: {} max: {}".format(p.minoff, p.maxoff))
                print("len: {}".format(len(p.seq) / 2))
        else:
            out = "{} has multiple BOF sequences".format(containerfilename)
            print(out, file=sys.stderr)
            for p in parts:
                out = "{} {} {} {} {}".format(
                    p.offset, p.pos, p.minoff, p.maxoff, p.seq
                )
                print(out, file=sys.stderr)

        for p in parts:
            bio = self.__writebytestream__(
                containerfilename, bio, p.offset, p.minoff, p.maxoff, p.seq, equiv
            )

        return bio

    def __writebytestream__(
        self, containerfilename, bio, offset, minoff, maxoff, seq, equiv=False
    ):
        if seq != "":
            sig2map = signature2bytegenerator.Sig2ByteGenerator()
            if offset == "BOFoffset":
                if equiv is False:
                    if int(maxoff) > 0:
                        boffill = (int(maxoff) - int(minoff)) / 2
                        seq = "{{{}}}{}".format(boffill, seq)
                bytes = sig2map.map_signature(minoff, seq, maxoff, 0)
                bio = self.dowriteseq(containerfilename, bio, bytes)
            elif offset == "EOFoffset":
                bytes = sig2map.map_signature(0, seq, minoff, 0)
                bio.seek(0, os.SEEK_END)
                bio = self.dowriteseq(containerfilename, bio, bytes)
            else:
                if int(maxoff) > 0:
                    boffill = (int(maxoff) - int(minoff)) / 2
                    seq = "{{{}}}{}".format(boffill, seq)
                bytes = sig2map.map_signature(minoff, seq, 0, 0)
                bio.seek(0)
                bio = self.dowriteseq(containerfilename, bio, bytes)
        return bio


def skeletonfilegeneration(containersig, standardsig, debug):

    skg = SkeletonContainerGenerator(containersig, standardsig, debug)
    skg.generateskeletonfiles()

    # Jython issues calling class destructor...
    if skg.java:  # TODO: Not appropriate way to invoke __del__()?
        skg.__del__()

    sys.exit(0)


def main():

    # Usage:  --con [container signature file]
    # Usage:  --sig [standard signature file]
    # Handle command line arguments for the script
    parser = argparse.ArgumentParser(
        description="Generate skeleton container files from DROID "
        "container signatures."
    )
    parser.add_argument(
        "--con", help="DROID Container Signature File.", default=False, required=True
    )
    parser.add_argument(
        "--sig", help="DROID Standard Signature File.", default=False, required=True
    )
    parser.add_argument(
        "--debug",
        help="Debug mode. Doesn't delete skeleton-folders directory.",
        default=False,
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    # Parse arguments into namespace object to reference later in the script
    global args
    args = parser.parse_args()

    if args.con and args.sig:
        skeletonfilegeneration(args.con, args.sig, args.debug)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
