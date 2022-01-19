import argparse
import sys

from lxml import etree


def preprocessxml(containersig, standardsig):
    """blank def"""
    parser = etree.XMLParser(remove_blank_text=True)
    abc = etree.parse(containersig, parser)
    abc.write("output.xml", pretty_print=True, xml_declaration=True, encoding="utf-8")


def main():

    #    Usage:  --con [container signature file]
    #    Usage:  --sig [standard signature file]
    #    Handle command line arguments for the script
    parser = argparse.ArgumentParser(
        description="Generate skeleton container files from DROID container signatures."
    )

    # TODO: Consider optional and mandatory elements... behaviour might change depending on output...
    # other options droid csv and rosetta schema
    # NOTE: class on its own might be used to create a blank import csv with just static options
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

    #    Parse arguments into namespace object to reference later in the script
    global args
    args = parser.parse_args()

    if args.con and args.sig:
        preprocessxml(args.con, args.sig)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
