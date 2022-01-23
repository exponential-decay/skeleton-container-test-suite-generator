# skeleton-container-test-suite-generator

Amendment to the [Skeleton Test Suite Generator][SKEL-1], creates OLE2 and ZIP
based container files invoking the container matching mechanisms in The
NationalvArchive, UK's DROID file format identification tool.

## Jython

Jython will generate OLE2 files, and ZIP based files.

Requires Jython with Apache POI on the CLASSPATH. Example command to run:

    jython -Dpython.path=$CLASSPATH skeletoncontainergenerator.py \
       --con container-signature-20140717.xml \
       --sig DROID_SignatureFile_V77.xml

Example CLASSPATH: `:/usr/bin/poi/poi-3.11-beta2/poi-3.11-beta2-20140822.jar`

**Warning:** Jython must be installed on the host system. Standalone won't
work. This [bug](http://bugs.jython.org/issue1422) in the Jython standalone
package seems to be the problem. If you manage to make it work, let me know!

## Python

Running the application in Python means that you can only output ZIP based
container objects. Jython is needed to output OLE2.

    python skeletoncontainergenerator.py \
      --con container-signature-20140717.xml
      --sig DROID_SignatureFile_V77.xml

## Debug

In either mode the `--debug` flag will let you see the files being written to
container objects. A folder will be left over after processing called
`skeleton-folders`.

## Results

The results will currently tell you how many objects should have been output,
plus a summary of the numbers actually output.

## Archive

All skeleton file suites should eventually be available in the (unofficial)
PRONOM archive: [here][ARCH-1].

## License

Copyright (c) 2014 Ross Spencer

This software is provided 'as-is', without any express or implied
warranty. In no event will the authors be held liable for any damages
arising from the use of this software.

Permission is granted to anyone to use this software for any purpose,
including commercial applications, and to alter it and redistribute it
freely, subject to the following restrictions:

   1. The origin of this software must not be misrepresented; you must not
   claim that you wrote the original software. If you use this software
   in a product, an acknowledgment in the product documentation would be
   appreciated but is not required.

   2. Altered source versions must be plainly marked as such, and must not be
   misrepresented as being the original software.

   3. This notice may not be removed or altered from any source
   distribution.

[SKEL-1]: https://github.com/exponential-decay/skeleton-test-suite-generator
[ARCH-1]: https://github.com/exponential-decay/pronom-archive-and-skeleton-test-suite
