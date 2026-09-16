
"""peutils, Portable Executable utilities module


Copyright (c) 2005-2023 Ero Carrera <ero.carrera@gmail.com>

All rights reserved.
"""
import os
import re
import string
import urllib.request, urllib.parse, urllib.error
import pefile

__author__ = "Ero Carrera"
__version__ = pefile.__version__
__contact__ = "ero.carrera@gmail.com"


class SignatureDatabase(object):
    """This class loads and keeps a parsed PEiD signature database.

    Usage:

        sig_db = SignatureDatabase('/path/to/signature/file')

    and/or

        sig_db = SignatureDatabase()
        sig_db.load('/path/to/signature/file')

    Signature databases can be combined by performing multiple loads.

    The filename parameter can be a URL too. In that case the
    signature database will be downloaded from that location.
    """

    def __init__(self, filename=None, data=None):

        # 022916.python.peutils.line40.comment RegExp to match a signature block
        # 022917.python.peutils.line41.comment
        self.parse_sig = re.compile(
            "\[(.*?)\]\s+?signature\s*=\s*(.*?)(\s+\?\?)*\s*ep_only\s*=\s*(\w+)(?:\s*section_start_only\s*=\s*(\w+)|)",
            re.S,
        )

        # 022918.python.peutils.line47.comment Signature information
        # 022919.python.peutils.line48.comment
        # 022920.python.peutils.line49.comment Signatures are stored as trees using dictionaries
        # 022921.python.peutils.line50.comment The keys are the byte values while the values for
        # 022922.python.peutils.line51.comment each key are either:
        # 022923.python.peutils.line52.comment
        # 022924.python.peutils.line53.comment - Other dictionaries of the same form for further
        # 022925.python.peutils.line54.comment bytes in the signature
        # 022926.python.peutils.line55.comment
        # 022927.python.peutils.line56.comment - A dictionary with a string as a key (packer name)
        # 022928.python.peutils.line57.comment and None as value to indicate a full signature
        # 022929.python.peutils.line58.comment
        self.signature_tree_eponly_true = dict()
        self.signature_count_eponly_true = 0
        self.signature_tree_eponly_false = dict()
        self.signature_count_eponly_false = 0
        self.signature_tree_section_start = dict()
        self.signature_count_section_start = 0

        # 022930.python.peutils.line66.comment The depth (length) of the longest signature
        # 022931.python.peutils.line67.comment
        self.max_depth = 0

        self.__load(filename=filename, data=data)

    def generate_section_signatures(self, pe, name, sig_length=512):
        """Generates signatures for all the sections in a PE file.

        If the section contains any data a signature will be created
        for it. The signature name will be a combination of the
        parameter 'name' and the section number and its name.
        """

        section_signatures = list()

        for idx, section in enumerate(pe.sections):

            if section.SizeOfRawData < sig_length:
                continue

            # 022932.python.peutils.line87.comment offset = pe.get_offset_from_rva(section.VirtualAddress)
            offset = section.PointerToRawData

            sig_name = "%s Section(%d/%d,%s)" % (
                name,
                idx + 1,
                len(pe.sections),
                "".join([c for c in section.Name if c in string.printable]),
            )

            section_signatures.append(
                self.__generate_signature(
                    pe,
                    offset,
                    sig_name,
                    ep_only=False,
                    section_start_only=True,
                    sig_length=sig_length,
                )
            )

        return "\n".join(section_signatures) + "\n"

    def generate_ep_signature(self, pe, name, sig_length=512):
        """Generate signatures for the entry point of a PE file.

        Creates a signature whose name will be the parameter 'name'
        and the section number and its name.
        """

        offset = pe.get_offset_from_rva(pe.OPTIONAL_HEADER.AddressOfEntryPoint)

        return self.__generate_signature(
            pe, offset, name, ep_only=True, sig_length=sig_length
        )

    def __generate_signature(
        self, pe, offset, name, ep_only=False, section_start_only=False, sig_length=512
    ):

        data = pe.__data__[offset : offset + sig_length]

        signature_bytes = " ".join(["%02x" % ord(c) for c in data])

        if ep_only == True:
            ep_only = "true"
        else:
            ep_only = "false"

        if section_start_only == True:
            section_start_only = "true"
        else:
            section_start_only = "false"

        signature = "[%s]\nsignature = %s\nep_only = %s\nsection_start_only = %s\n" % (
            name,
            signature_bytes,
            ep_only,
            section_start_only,
        )

        return signature

    def match(self, pe, ep_only=True, section_start_only=False):
        """Matches and returns the exact match(es).

        If ep_only is True the result will be a string with
        the packer name. Otherwise it will be a list of the
        form (file_offset, packer_name) specifying where
        in the file the signature was found.
        """

        matches = self.__match(pe, ep_only, section_start_only)

        # 022933.python.peutils.line161.comment The last match (the most precise) from the
        # 022934.python.peutils.line162.comment list of matches (if any) is returned
        # 022935.python.peutils.line163.comment
        if matches:
            if ep_only == False:
                # 022936.python.peutils.line166.comment Get the most exact match for each list of matches
                # 022937.python.peutils.line167.comment at a given offset
                # 022938.python.peutils.line168.comment
                return [(match[0], match[1][-1]) for match in matches]

            return matches[1][-1]

        return None

    def match_all(self, pe, ep_only=True, section_start_only=False):
        """Matches and returns all the likely matches."""

        matches = self.__match(pe, ep_only, section_start_only)

        if matches:
            if ep_only == False:
                # 022939.python.peutils.line182.comment Get the most exact match for each list of matches
                # 022940.python.peutils.line183.comment at a given offset
                # 022941.python.peutils.line184.comment
                return matches

            return matches[1]

        return None

    def __match(self, pe, ep_only, section_start_only):

        # 022942.python.peutils.line193.comment Load the corresponding set of signatures
        # 022943.python.peutils.line194.comment Either the one for ep_only equal to True or
        # 022944.python.peutils.line195.comment to False
        # 022945.python.peutils.line196.comment
        if section_start_only is True:

            # 022946.python.peutils.line199.comment Fetch the data of the executable as it'd
            # 022947.python.peutils.line200.comment look once loaded in memory
            # 022948.python.peutils.line201.comment
            try:
                data = pe.__data__
            except Exception as excp:
                raise

            # 022949.python.peutils.line207.comment Load the corresponding tree of signatures
            # 022950.python.peutils.line208.comment
            signatures = self.signature_tree_section_start

            # 022951.python.peutils.line211.comment Set the starting address to start scanning from
            # 022952.python.peutils.line212.comment
            scan_addresses = [section.PointerToRawData for section in pe.sections]

        elif ep_only is True:

            # 022953.python.peutils.line217.comment Fetch the data of the executable as it'd
            # 022954.python.peutils.line218.comment look once loaded in memory
            # 022955.python.peutils.line219.comment
            try:
                data = pe.get_memory_mapped_image()
            except Exception as excp:
                raise

            # 022956.python.peutils.line225.comment Load the corresponding tree of signatures
            # 022957.python.peutils.line226.comment
            signatures = self.signature_tree_eponly_true

            # 022958.python.peutils.line229.comment Fetch the entry point of the PE file and the data
            # 022959.python.peutils.line230.comment at the entry point
            # 022960.python.peutils.line231.comment
            ep = pe.OPTIONAL_HEADER.AddressOfEntryPoint

            # 022961.python.peutils.line234.comment Set the starting address to start scanning from
            # 022962.python.peutils.line235.comment
            scan_addresses = [ep]

        else:

            data = pe.__data__

            signatures = self.signature_tree_eponly_false

            scan_addresses = range(len(data))

        # 022963.python.peutils.line246.comment For each start address, check if any signature matches
        # 022964.python.peutils.line247.comment
        matches = []
        for idx in scan_addresses:
            result = self.__match_signature_tree(
                signatures, data[idx : idx + self.max_depth]
            )
            if result:
                matches.append((idx, result))

        # 022965.python.peutils.line256.comment Return only the matched items found at the entry point if
        # 022966.python.peutils.line257.comment ep_only is True (matches will have only one element in that
        # 022967.python.peutils.line258.comment case)
        # 022968.python.peutils.line259.comment
        if ep_only is True:
            if matches:
                return matches[0]

        return matches

    def match_data(self, code_data, ep_only=True, section_start_only=False):

        data = code_data
        scan_addresses = [0]

        # 022969.python.peutils.line271.comment Load the corresponding set of signatures
        # 022970.python.peutils.line272.comment Either the one for ep_only equal to True or
        # 022971.python.peutils.line273.comment to False
        # 022972.python.peutils.line274.comment
        if section_start_only is True:

            # 022973.python.peutils.line277.comment Load the corresponding tree of signatures
            # 022974.python.peutils.line278.comment
            signatures = self.signature_tree_section_start

            # 022975.python.peutils.line281.comment Set the starting address to start scanning from
            # 022976.python.peutils.line282.comment

        elif ep_only is True:

            # 022977.python.peutils.line286.comment Load the corresponding tree of signatures
            # 022978.python.peutils.line287.comment
            signatures = self.signature_tree_eponly_true

        # 022979.python.peutils.line290.comment For each start address, check if any signature matches
        # 022980.python.peutils.line291.comment
        matches = []
        for idx in scan_addresses:
            result = self.__match_signature_tree(
                signatures, data[idx : idx + self.max_depth]
            )
            if result:
                matches.append((idx, result))

        # 022981.python.peutils.line300.comment Return only the matched items found at the entry point if
        # 022982.python.peutils.line301.comment ep_only is True (matches will have only one element in that
        # 022983.python.peutils.line302.comment case)
        # 022984.python.peutils.line303.comment
        if ep_only is True:
            if matches:
                return matches[0]

        return matches

    def __match_signature_tree(self, signature_tree, data, depth=0):
        """Recursive function to find matches along the signature tree.

        signature_tree  is the part of the tree left to walk
        data    is the data being checked against the signature tree
        depth   keeps track of how far we have gone down the tree
        """

        matched_names = list()
        match = signature_tree

        # 022985.python.peutils.line321.comment Walk the bytes in the data and match them
        # 022986.python.peutils.line322.comment against the signature
        # 022987.python.peutils.line323.comment
        for idx, byte in enumerate([b if isinstance(b, int) else ord(b) for b in data]):

            # 022988.python.peutils.line326.comment If the tree is exhausted...
            # 022989.python.peutils.line327.comment
            if match is None:
                break

            # 022990.python.peutils.line331.comment Get the next byte in the tree
            # 022991.python.peutils.line332.comment
            match_next = match.get(byte, None)

            # 022992.python.peutils.line335.comment If None is among the values for the key
            # 022993.python.peutils.line336.comment it means that a signature in the database
            # 022994.python.peutils.line337.comment ends here and that there's an exact match.
            # 022995.python.peutils.line338.comment
            if None in list(match.values()):
                # 022996.python.peutils.line340.comment idx represent how deep we are in the tree
                # 022997.python.peutils.line341.comment
                # 022998.python.peutils.line342.comment names = [idx+depth]
                names = list()

                # 022999.python.peutils.line345.comment For each of the item pairs we check
                # 023000.python.peutils.line346.comment if it has an element other than None,
                # 023001.python.peutils.line347.comment if not then we have an exact signature
                # 023002.python.peutils.line348.comment
                for item in list(match.items()):
                    if item[1] is None:
                        names.append(item[0])
                matched_names.append(names)

            # 023003.python.peutils.line354.comment If a wildcard is found keep scanning the signature
            # 023004.python.peutils.line355.comment ignoring the byte.
            # 023005.python.peutils.line356.comment
            if "??" in match:
                match_tree_alternate = match.get("??", None)
                data_remaining = data[idx + 1 :]
                if data_remaining:
                    matched_names.extend(
                        self.__match_signature_tree(
                            match_tree_alternate, data_remaining, idx + depth + 1
                        )
                    )

            match = match_next

        # 023006.python.peutils.line369.comment If we have any more packer name in the end of the signature tree
        # 023007.python.peutils.line370.comment add them to the matches
        # 023008.python.peutils.line371.comment
        if match is not None and None in list(match.values()):
            # 023009.python.peutils.line373.comment names = [idx + depth + 1]
            names = list()
            for item in list(match.items()):
                if item[1] is None:
                    names.append(item[0])
            matched_names.append(names)

        return matched_names

    def load(self, filename=None, data=None):
        """Load a PEiD signature file.

        Invoking this method on different files combines the signatures.
        """

        self.__load(filename=filename, data=data)

    def __load(self, filename=None, data=None):

        if filename is not None:
            # 023010.python.peutils.line393.comment If the path does not exist, attempt to open a URL
            # 023011.python.peutils.line394.comment
            if not os.path.exists(filename):
                try:
                    sig_f = urllib.request.urlopen(filename)
                    sig_data = sig_f.read()
                    sig_f.close()
                except IOError:
                    # 023012.python.peutils.line401.comment Let this be raised back to the user...
                    raise
            else:
                # 023013.python.peutils.line404.comment Get the data for a file
                # 023014.python.peutils.line405.comment
                try:
                    sig_f = open(filename, "rt")
                    sig_data = sig_f.read()
                    sig_f.close()
                except IOError:
                    # 023015.python.peutils.line411.comment Let this be raised back to the user...
                    raise
        else:
            sig_data = data

        # 023016.python.peutils.line416.comment If the file/URL could not be read or no "raw" data
        # 023017.python.peutils.line417.comment was provided there's nothing else to do
        # 023018.python.peutils.line418.comment
        if not sig_data:
            return

        # 023019.python.peutils.line422.comment Helper function to parse the signature bytes
        # 023020.python.peutils.line423.comment
        def to_byte(value):
            if "?" in value:
                return value
            return int(value, 16)

        # 023021.python.peutils.line429.comment Parse all the signatures in the file
        # 023022.python.peutils.line430.comment
        matches = self.parse_sig.findall(sig_data)

        # 023023.python.peutils.line433.comment For each signature, get the details and load it into the
        # 023024.python.peutils.line434.comment signature tree
        # 023025.python.peutils.line435.comment
        for (
            packer_name,
            signature,
            superfluous_wildcards,
            ep_only,
            section_start_only,
        ) in matches:

            ep_only = ep_only.strip().lower()

            signature = signature.replace("\\n", "").strip()

            signature_bytes = [to_byte(b) for b in signature.split()]

            if ep_only == "true":
                ep_only = True
            else:
                ep_only = False

            if section_start_only == "true":
                section_start_only = True
            else:
                section_start_only = False

            depth = 0

            if section_start_only is True:

                tree = self.signature_tree_section_start
                self.signature_count_section_start += 1

            else:
                if ep_only is True:
                    tree = self.signature_tree_eponly_true
                    self.signature_count_eponly_true += 1
                else:
                    tree = self.signature_tree_eponly_false
                    self.signature_count_eponly_false += 1

            for idx, byte in enumerate(signature_bytes):

                if idx + 1 == len(signature_bytes):

                    tree[byte] = tree.get(byte, dict())
                    tree[byte][packer_name] = None

                else:

                    tree[byte] = tree.get(byte, dict())

                tree = tree[byte]
                depth += 1

            if depth > self.max_depth:
                self.max_depth = depth


def is_valid(pe):
    """"""
    pass


def is_suspicious(pe):
    """
    unusual locations of import tables
    non recognized section names
    presence of long ASCII strings
    """

    relocations_overlap_entry_point = False
    sequential_relocs = 0

    # 023026.python.peutils.line508.comment If relocation data is found and the entries go over the entry point, and also are very
    # 023027.python.peutils.line509.comment continuous or point outside section's boundaries => it might imply that an obfuscation
    # 023028.python.peutils.line510.comment trick is being used or the relocations are corrupt (maybe intentionally)
    # 023029.python.peutils.line511.comment
    if hasattr(pe, "DIRECTORY_ENTRY_BASERELOC"):
        for base_reloc in pe.DIRECTORY_ENTRY_BASERELOC:
            last_reloc_rva = None
            for reloc in base_reloc.entries:
                if reloc.rva <= pe.OPTIONAL_HEADER.AddressOfEntryPoint <= reloc.rva + 4:
                    relocations_overlap_entry_point = True

                if (
                    last_reloc_rva is not None
                    and last_reloc_rva <= reloc.rva <= last_reloc_rva + 4
                ):
                    sequential_relocs += 1

                last_reloc_rva = reloc.rva

    # 023030.python.peutils.line527.comment If import tables or strings exist (are pointed to) to within the header or in the area
    # 023031.python.peutils.line528.comment between the PE header and the first section that's suspicious
    # 023032.python.peutils.line529.comment
    # 023033.python.peutils.line530.comment IMPLEMENT

    warnings_while_parsing = False
    # 023034.python.peutils.line533.comment If we have warnings, that's suspicious, some of those will be because of out-of-ordinary
    # 023035.python.peutils.line534.comment values are found in the PE header fields
    # 023036.python.peutils.line535.comment Things that are reported in warnings:
    # 023037.python.peutils.line536.comment (parsing problems, special section characteristics i.e. W & X, uncommon values of fields,
    # 023038.python.peutils.line537.comment unusual entrypoint, suspicious imports)
    # 023039.python.peutils.line538.comment
    warnings = pe.get_warnings()
    if warnings:
        warnings_while_parsing

    # 023040.python.peutils.line543.comment If there are few or none (should come with a standard "density" of strings/kilobytes of data) longer (>8)
    # 023041.python.peutils.line544.comment ascii sequences that might indicate packed data, (this is similar to the entropy test in some ways but
    # 023042.python.peutils.line545.comment might help to discard cases of legitimate installer or compressed data)

    # 023043.python.peutils.line547.comment If compressed data (high entropy) and is_driver => uuuuhhh, nasty

    pass


def is_probably_packed(pe):
    """Returns True is there is a high likelihood that a file is packed or contains compressed data.

    The sections of the PE file will be analyzed, if enough sections
    look like containing compressed data and the data makes
    up for more than 20% of the total file size, the function will
    return True.
    """

    # 023044.python.peutils.line561.comment Calculate the length of the data up to the end of the last section in the
    # 023045.python.peutils.line562.comment file. Overlay data won't be taken into account
    # 023046.python.peutils.line563.comment
    total_pe_data_length = len(pe.trim())
    # 023047.python.peutils.line565.comment Assume that the file is packed when no data is available
    if not total_pe_data_length:
        return True
    has_significant_amount_of_compressed_data = False

    # 023048.python.peutils.line570.comment If some of the sections have high entropy and they make for more than 20% of the file's size
    # 023049.python.peutils.line571.comment it's assumed that it could be an installer or a packed file

    total_compressed_data = 0
    for section in pe.sections:
        s_entropy = section.get_entropy()
        s_length = len(section.get_data())
        # 023050.python.peutils.line577.comment The value of 7.4 is empirical, based on looking at a few files packed
        # 023051.python.peutils.line578.comment by different packers
        if s_entropy > 7.4:
            total_compressed_data += s_length

    if (total_compressed_data / total_pe_data_length) > 0.2:
        has_significant_amount_of_compressed_data = True

    return has_significant_amount_of_compressed_data
