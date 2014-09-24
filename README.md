skeleton-container-test-suite-generator
=======================================

Work in progress. Adding container functionality to Skeleton Test Suite Generator

### Jython

Jython will generate OLE2 files, and ZIP based files. 

Requires Jython with Apache POI on the CLASSPATH. Example command to run:

jython -Dpython.path=$CLASSPATH skeletoncontainergenerator.py --con container-signature-20140717.xml --sig DROID_SignatureFile_V77.xml 

Example CLASSPATH: :/usr/bin/poi/poi-3.11-beta2/poi-3.11-beta2-20140822.jar

### Python

Running the application in Python means that you can only output ZIP based container objects. 

python skeletoncontainergenerator.py --con container-signature-20140717.xml --sig DROID_SignatureFile_V77.xml 

### Results

The results will currently tell you how many objects should have been output, plus a rough summary of the numbers actually output. To be improved somewhat. 

Container objects output should match 1:1 in DROID with all current signatures at time of writing. 

### Container Signature Findings

#### container-signature-20110114.xml

* fmt/60, ID 2000 identified as fmt/60 and fmt/61
* fmt/61 a catch-all for Excel, fmt/60 more specific

* x-fmt/259, ID 13000 identified as x-fmt/113, x-fmt/258, x-fmt/259
* x-fmt/113, x-fmt/258, x-fmt/259 all share same signature ID, therefore signature.

### container-signatute-20110204.xml

* fmt/60, ID 2000 identified as fmt/60 and fmt/61
* fmt/61 a catch-all for Excel, fmt/60 more specific

* x-fmt/259, ID 13000 identified as x-fmt/113, x-fmt/258, x-fmt/259
* x-fmt/113, x-fmt/258, x-fmt/259 all share same signature ID, therefore signature.

### container-signature-20120611.xml

* Cannot write file without a path: x-fmt-247-container-signature-id-4040.mpp/
* Cannot write file without a path: fmt-440-container-signature-id-4060.mpp/

* fmt/60, ID 2000 identified as fmt/60 and fmt/61
* fmt/61 a catch-all for Excel, fmt/60 more specific

* fmt/424, ID 9020 as fmt/140 and fmt/424
* fmt/140, ID 9010 is less specific signature with no version info, capturing both

* x-fmt/258, ID 13010 as x-fmt/258 and x-fmt/442
* x-fmt/442 less specific, missing 0x06 right fragment

* x-fmt/443, ID 13020 as x-fmt/443 and x-fmt/442
* x-fmt/442 less specific, missing 0x0B right fragment

* PUIDS mapped to standard signature file incorrectly
* x-fmt/442 is Form*Z Project File
* x-fmt/443 is Revit Family File
* These files should be Visio Documents

### container-signature-20120828.xml

* Cannot write file without a path: x-fmt-247-container-signature-id-4040.mpp/
* Cannot write file without a path: fmt-440-container-signature-id-4060.mpp/

* fmt/60, ID 2000 identified as fmt/60 and fmt/61
* fmt/61 a catch-all for Excel, fmt/60 more specific

### container-signature-20121218.xml

* Cannot write file without a path: x-fmt-247-container-signature-id-4040.mpp/
* Cannot write file without a path: fmt-440-container-signature-id-4060.mpp/

### container-signature-20130226.xml

* Cannot write file without a path: x-fmt-247-container-signature-id-4040.mpp/
* Cannot write file without a path: fmt-440-container-signature-id-4060.mpp/

### container-signature-20130501.xml

* Cannot write file without a path: x-fmt-247-container-signature-id-4040.mpp/
* Cannot write file without a path: fmt-440-container-signature-id-4060.mpp/

### container-signature-20131112.xml

* Cannot write file without a path: x-fmt-247-container-signature-id-4040.mpp/
* Cannot write file without a path: fmt-440-container-signature-id-4060.mpp/
