# -*- coding: utf-8 -*-

"""Singature2ByteGenerator will convert signature sequences to byte
sequences that can be written to a file.
"""

from __future__ import print_function

import logging
import random

FILL_RANDOM = "RAND"


class Sig2ByteGenerator:
    """Sig2ByteGenerator encapsulates our byte conversion operations.
    """

    def __init__(self):
        self.component_list = []
        self.open_syntax = ["{", "(", "[", "?", "*"]
        self.fillbyte = None

    def __del__(self):
        del self.component_list[:]

    @staticmethod
    def set_fillbyte(fillvalue):
        if fillvalue < 0 or fillvalue > 255:
            logging.debug("Fill byte set to RANDOM")
            fillbyte = FILL_RANDOM
            return fillbyte
        return fillvalue

    def check_syntax(self, signature):
        for i in self.open_syntax:
            if signature.find(i) > -1:
                return True
        return False

    def create_bytes(self, number):
        """Create 'n' bytes.

        :param number: number of bytes to create
        :return: True when done
        """
        for _ in range(number):
            if self.fillbyte == FILL_RANDOM:
                self.component_list.append(
                    hex(random.randint(0, 255))
                    .replace("0x", "")
                    .zfill(2)
                    .replace("L", "")
                )
            else:
                self.component_list.append(
                    hex(self.fillbyte).replace("0x", "").zfill(2).replace("L", "")
                )
        return True

    def process_curly(self, syn):
        """Process sequence with curly brackets."""
        syn = syn.replace("{", "")
        syn = syn.replace("}", "")
        if syn.find("-") == -1:
            self.create_bytes(int(syn))
        else:
            new_str = syn.split("-")
            if new_str[1] == "*":
                val = int(new_str[0])
                self.create_bytes(val + 10)
            else:
                val = (int(new_str[0]) + int(new_str[1])) / 2
                self.create_bytes(val)

    def process_square(self, syn):
        """Process sequence with square brackets."""
        if "-" in syn:
            logging.debug("Replacing dash '-' in '%s'", syn)
            syn = syn.replace("-", ":")
        syn = syn.replace("[", "")
        syn = syn.replace("]", "")
        # convert to ints and find mean value in range
        if syn.find(":") > -1:
            self.sqr_colon(syn)
        # convert to ints and -1 so don't equal hex in not clause
        elif syn.find("!") > -1:
            self.sqr_not(syn)

    def process_mask(self, syn, inverted=False):
        """Process sequence with mask."""
        syn = syn.replace("[", "")
        syn = syn.replace("]", "")
        val = 0
        # negate first, else, mask...
        if "!&" in syn and inverted is True:
            syn = syn.replace("!&", "")
            byte = int(syn, 16)
            mask = byte & 0
            val = mask
        elif "&" in syn and inverted is False:
            syn = syn.replace("&", "")
            byte = int(syn, 16)
            mask = byte & 255
            val = mask
        self.component_list.append(hex(val).replace("0x", "").zfill(2).replace("L", ""))

    def sqr_colon(self, syn):
        # convert to ints and find mean value in range
        if syn.find(":") > -1:
            new_str = syn.split(":")
            val = (int(new_str[0], 16) + int(new_str[1], 16)) / 2
            self.component_list.append(
                hex(val).replace("0x", "").zfill(2).replace("L", "")
            )

    def sqr_not(self, syn):
        syn = syn.replace("!", "")
        seq = list(map(ord, syn.decode("hex")))
        for idx, _ in enumerate(seq):
            if seq[idx] == 0:
                seq[idx] = seq[idx] + 1
            else:
                seq[idx] = seq[idx] - 1
            self.component_list.append(
                hex(seq[idx]).replace("0x", "").zfill(2).replace("L", "")
            )

    def process_thesis(self, syn):
        syn = syn.replace("(", "").replace(")", "")
        index = syn.find("|")
        syn = syn[0:index]
        if syn.find("[") != -1:
            self.process_square(syn)
        seq = list(map(ord, syn.decode("hex")))
        for idx in range(seq.__len__()):
            self.component_list.append(
                hex(seq[idx]).replace("0x", "").zfill(2).replace("L", "")
            )

    def detailed_check(self, signature):
        index = 0
        if signature.__len__() > 0:
            check_byte = signature[0]
            if check_byte == "{":
                index = signature.find("}")
                syn = signature[0 : index + 1]
                self.process_curly(syn)
            elif check_byte == "[":
                # We may have a bitmask... deal with it here...
                #
                # From matt palmer:
                # DROID 6 should, in fact, be capable of identifying bit-fields,
                # although there has not been a signature which uses this so far.
                # The byteseek library which DROID uses to process signatures has
                # an "all-bitmask" operator &, and an "any-bitmask" operator ~.
                # For example, if you wanted to specify that bit 4 must match
                # (but you don't care about the other bits), you could write
                # [&08].  Of if you wanted to specify that a byte must be odd,
                # then you could write [&01]. Or more complex multi-bit masks as
                # well. I guess you could also test for it not matching using the
                # DROID syntax for an inverted set !: [!&01].
                check_inverted = signature[1:3]
                if check_inverted == "!&":
                    index = signature.find("]")
                    syn = signature[1 : index + 1]
                    self.process_mask(syn, True)
                else:
                    check_mask = signature[1:2]
                    if check_mask == "&":
                        index = signature.find("]")
                        syn = signature[0 : index + 1]
                        self.process_mask(syn)
                index = signature.find("]")
                syn = signature[0 : index + 1]
                self.process_square(syn)
            elif check_byte == "?":
                syn = signature[0:index]
                index = 1
                self.create_bytes(1)
            elif check_byte == "(":
                index = signature.find(")")
                syn = signature[0 : index + 1]
                self.process_thesis(syn)
            elif check_byte == "*":
                self.create_bytes(20)

        return signature[index + 1 :]

    def process_signature(self, signature):
        """Process a given signature into byte sequences for writing
        to file.
        """
        if self.check_syntax(signature) is not True:
            self.component_list.append(signature)
            return
        for idx, val in enumerate(signature):
            if not val.isalnum():  # are all alphanumeric
                element = signature[0:idx]
                if element != "":  # may not be anything to append e.g. '??ab'
                    self.component_list.append(element)
                signature = self.detailed_check(signature[idx:])
                break
        self.process_signature(signature)

    def map_signature(self, bofoffset, signature, eofoffset, fillvalue=-1):
        """Map signature to byte sequences."""
        self.fillbyte = self.set_fillbyte(fillvalue)
        if bofoffset != "null":
            self.create_bytes(int(bofoffset))  # dangerous? need to check type?
        self.process_signature(signature)
        if eofoffset != "null":
            self.create_bytes(int(eofoffset))
        return self.component_list
