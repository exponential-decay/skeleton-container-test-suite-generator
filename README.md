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

### conttainer-signatute-20110204.xml

* fmt/60, ID 2000 identified as fmt/60 and fmt/61
* fmt/61 a catch-all for Excel, fmt/60 more specific

*x-fmt/259, ID 13000 identified as x-fmt/113, x-fmt/258, x-fmt/259
*x-fmt/113, x-fmt/258, x-fmt/259 all share same signature ID, therefore signature.

