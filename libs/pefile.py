#!/usr/bin/python

"""pefile, Portable Executable reader module

All the PE file basic structures are available with their default names as
attributes of the instance returned.

Processed elements such as the import table are made available with lowercase
names, to differentiate them from the upper case basic structure names.

pefile has been tested against many edge cases such as corrupted and malformed
PEs as well as malware, which often attempts to abuse the format way beyond its
standard use. To the best of my knowledge most of the abuse is handled
gracefully.

Copyright (c) 2005-2023 Ero Carrera <ero.carrera@gmail.com>
"""

__author__ = "Ero Carrera"
__version__ = "2023.2.7"
__contact__ = "ero.carrera@gmail.com"

import collections
import os
import struct
import codecs
import time
import math
import string
import mmap
import uuid

from collections import Counter
from typing import Union
from hashlib import sha1
from hashlib import sha256
from hashlib import sha512
from hashlib import md5

import functools
import copy as copymod

import ordlookup

codecs.register_error("backslashreplace_", codecs.lookup_error("backslashreplace"))

long = int
# 022278.python.pefile.line48.comment lru_cache with a shallow copy of the objects returned (list, dicts, ..)
# 022279.python.pefile.line49.comment we don't use deepcopy as it's _really_ slow and the data we retrieved using
# 022280.python.pefile.line50.comment this is enough with copy.copy taken from
# 022281.python.pefile.line51.comment https://stackoverflow.com/questions/54909357
def lru_cache(maxsize=128, typed=False, copy=False):
    if not copy:
        return functools.lru_cache(maxsize, typed)

    def decorator(f):
        cached_func = functools.lru_cache(maxsize, typed)(f)

        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            # 022282.python.pefile.line61.comment return copymod.deepcopy(cached_func(*args, **kwargs))
            return copymod.copy(cached_func(*args, **kwargs))

        return wrapper

    return decorator


@lru_cache(maxsize=2048)
def cache_adjust_FileAlignment(val, file_alignment):
    if file_alignment < FILE_ALIGNMENT_HARDCODED_VALUE:
        return val
    return (int(val / 0x200)) * 0x200


@lru_cache(maxsize=2048)
def cache_adjust_SectionAlignment(val, section_alignment, file_alignment):
    if section_alignment < 0x1000:  # page size
        section_alignment = file_alignment

    # 022284.python.pefile.line81.comment 0x200 is the minimum valid FileAlignment according to the documentation
    # 022285.python.pefile.line82.comment although ntoskrnl.exe has an alignment of 0x80 in some Windows versions
    # 022286.python.pefile.line83.comment
    # 022287.python.pefile.line84.comment elif section_alignment < 0x80:
    # 022288.python.pefile.line85.comment section_alignment = 0x80

    if section_alignment and val % section_alignment:
        return section_alignment * (int(val / section_alignment))
    return val


def count_zeroes(data):
    return data.count(0)


fast_load = False

# 022289.python.pefile.line98.comment This will set a maximum length of a string to be retrieved from the file.
# 022290.python.pefile.line99.comment It's there to prevent loading massive amounts of data from memory mapped
# 022291.python.pefile.line100.comment files. Strings longer than 1MB should be rather rare.
MAX_STRING_LENGTH = 0x100000  # 2^20

# 022293.python.pefile.line103.comment Maximum number of imports to parse.
MAX_IMPORT_SYMBOLS = 0x2000

# 022294.python.pefile.line106.comment Limit maximum length for specific string types separately
MAX_IMPORT_NAME_LENGTH = 0x200
MAX_DLL_LENGTH = 0x200
MAX_SYMBOL_NAME_LENGTH = 0x200

# 022295.python.pefile.line111.comment Limit maximum number of sections before processing of sections will stop
MAX_SECTIONS = 0x800

# 022296.python.pefile.line114.comment The global maximum number of resource entries to parse per file
MAX_RESOURCE_ENTRIES = 0x8000

# 022297.python.pefile.line117.comment The maximum depth of nested resource tables
MAX_RESOURCE_DEPTH = 32

# 022298.python.pefile.line120.comment Limit number of exported symbols
MAX_SYMBOL_EXPORT_COUNT = 0x2000

IMAGE_DOS_SIGNATURE = 0x5A4D
IMAGE_DOSZM_SIGNATURE = 0x4D5A
IMAGE_NE_SIGNATURE = 0x454E
IMAGE_LE_SIGNATURE = 0x454C
IMAGE_LX_SIGNATURE = 0x584C
IMAGE_TE_SIGNATURE = 0x5A56  # Terse Executables have a 'VZ' signature

IMAGE_NT_SIGNATURE = 0x00004550
IMAGE_NUMBEROF_DIRECTORY_ENTRIES = 16
IMAGE_ORDINAL_FLAG = 0x80000000
IMAGE_ORDINAL_FLAG64 = 0x8000000000000000
OPTIONAL_HEADER_MAGIC_PE = 0x10B
OPTIONAL_HEADER_MAGIC_PE_PLUS = 0x20B


def two_way_dict(pairs):
    return dict([(e[1], e[0]) for e in pairs] + pairs)


directory_entry_types = [
    ("IMAGE_DIRECTORY_ENTRY_EXPORT", 0),
    ("IMAGE_DIRECTORY_ENTRY_IMPORT", 1),
    ("IMAGE_DIRECTORY_ENTRY_RESOURCE", 2),
    ("IMAGE_DIRECTORY_ENTRY_EXCEPTION", 3),
    ("IMAGE_DIRECTORY_ENTRY_SECURITY", 4),
    ("IMAGE_DIRECTORY_ENTRY_BASERELOC", 5),
    ("IMAGE_DIRECTORY_ENTRY_DEBUG", 6),
    # 022300.python.pefile.line150.comment Architecture on non-x86 platforms
    ("IMAGE_DIRECTORY_ENTRY_COPYRIGHT", 7),
    ("IMAGE_DIRECTORY_ENTRY_GLOBALPTR", 8),
    ("IMAGE_DIRECTORY_ENTRY_TLS", 9),
    ("IMAGE_DIRECTORY_ENTRY_LOAD_CONFIG", 10),
    ("IMAGE_DIRECTORY_ENTRY_BOUND_IMPORT", 11),
    ("IMAGE_DIRECTORY_ENTRY_IAT", 12),
    ("IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT", 13),
    ("IMAGE_DIRECTORY_ENTRY_COM_DESCRIPTOR", 14),
    ("IMAGE_DIRECTORY_ENTRY_RESERVED", 15),
]

DIRECTORY_ENTRY = two_way_dict(directory_entry_types)

image_characteristics = [
    ("IMAGE_FILE_RELOCS_STRIPPED", 0x0001),
    ("IMAGE_FILE_EXECUTABLE_IMAGE", 0x0002),
    ("IMAGE_FILE_LINE_NUMS_STRIPPED", 0x0004),
    ("IMAGE_FILE_LOCAL_SYMS_STRIPPED", 0x0008),
    ("IMAGE_FILE_AGGRESIVE_WS_TRIM", 0x0010),
    ("IMAGE_FILE_LARGE_ADDRESS_AWARE", 0x0020),
    ("IMAGE_FILE_16BIT_MACHINE", 0x0040),
    ("IMAGE_FILE_BYTES_REVERSED_LO", 0x0080),
    ("IMAGE_FILE_32BIT_MACHINE", 0x0100),
    ("IMAGE_FILE_DEBUG_STRIPPED", 0x0200),
    ("IMAGE_FILE_REMOVABLE_RUN_FROM_SWAP", 0x0400),
    ("IMAGE_FILE_NET_RUN_FROM_SWAP", 0x0800),
    ("IMAGE_FILE_SYSTEM", 0x1000),
    ("IMAGE_FILE_DLL", 0x2000),
    ("IMAGE_FILE_UP_SYSTEM_ONLY", 0x4000),
    ("IMAGE_FILE_BYTES_REVERSED_HI", 0x8000),
]

IMAGE_CHARACTERISTICS = two_way_dict(image_characteristics)


section_characteristics = [
    ("IMAGE_SCN_TYPE_REG", 0x00000000),  # reserved
    ("IMAGE_SCN_TYPE_DSECT", 0x00000001),  # reserved
    ("IMAGE_SCN_TYPE_NOLOAD", 0x00000002),  # reserved
    ("IMAGE_SCN_TYPE_GROUP", 0x00000004),  # reserved
    ("IMAGE_SCN_TYPE_NO_PAD", 0x00000008),  # reserved
    ("IMAGE_SCN_TYPE_COPY", 0x00000010),  # reserved
    ("IMAGE_SCN_CNT_CODE", 0x00000020),
    ("IMAGE_SCN_CNT_INITIALIZED_DATA", 0x00000040),
    ("IMAGE_SCN_CNT_UNINITIALIZED_DATA", 0x00000080),
    ("IMAGE_SCN_LNK_OTHER", 0x00000100),
    ("IMAGE_SCN_LNK_INFO", 0x00000200),
    ("IMAGE_SCN_LNK_OVER", 0x00000400),  # reserved
    ("IMAGE_SCN_LNK_REMOVE", 0x00000800),
    ("IMAGE_SCN_LNK_COMDAT", 0x00001000),
    ("IMAGE_SCN_MEM_PROTECTED", 0x00004000),  # obsolete
    ("IMAGE_SCN_NO_DEFER_SPEC_EXC", 0x00004000),
    ("IMAGE_SCN_GPREL", 0x00008000),
    ("IMAGE_SCN_MEM_FARDATA", 0x00008000),
    ("IMAGE_SCN_MEM_SYSHEAP", 0x00010000),  # obsolete
    ("IMAGE_SCN_MEM_PURGEABLE", 0x00020000),
    ("IMAGE_SCN_MEM_16BIT", 0x00020000),
    ("IMAGE_SCN_MEM_LOCKED", 0x00040000),
    ("IMAGE_SCN_MEM_PRELOAD", 0x00080000),
    ("IMAGE_SCN_ALIGN_1BYTES", 0x00100000),
    ("IMAGE_SCN_ALIGN_2BYTES", 0x00200000),
    ("IMAGE_SCN_ALIGN_4BYTES", 0x00300000),
    ("IMAGE_SCN_ALIGN_8BYTES", 0x00400000),
    ("IMAGE_SCN_ALIGN_16BYTES", 0x00500000),  # default alignment
    ("IMAGE_SCN_ALIGN_32BYTES", 0x00600000),
    ("IMAGE_SCN_ALIGN_64BYTES", 0x00700000),
    ("IMAGE_SCN_ALIGN_128BYTES", 0x00800000),
    ("IMAGE_SCN_ALIGN_256BYTES", 0x00900000),
    ("IMAGE_SCN_ALIGN_512BYTES", 0x00A00000),
    ("IMAGE_SCN_ALIGN_1024BYTES", 0x00B00000),
    ("IMAGE_SCN_ALIGN_2048BYTES", 0x00C00000),
    ("IMAGE_SCN_ALIGN_4096BYTES", 0x00D00000),
    ("IMAGE_SCN_ALIGN_8192BYTES", 0x00E00000),
    ("IMAGE_SCN_ALIGN_MASK", 0x00F00000),
    ("IMAGE_SCN_LNK_NRELOC_OVFL", 0x01000000),
    ("IMAGE_SCN_MEM_DISCARDABLE", 0x02000000),
    ("IMAGE_SCN_MEM_NOT_CACHED", 0x04000000),
    ("IMAGE_SCN_MEM_NOT_PAGED", 0x08000000),
    ("IMAGE_SCN_MEM_SHARED", 0x10000000),
    ("IMAGE_SCN_MEM_EXECUTE", 0x20000000),
    ("IMAGE_SCN_MEM_READ", 0x40000000),
    ("IMAGE_SCN_MEM_WRITE", 0x80000000),
]

SECTION_CHARACTERISTICS = two_way_dict(section_characteristics)


debug_types = [
    ("IMAGE_DEBUG_TYPE_UNKNOWN", 0),
    ("IMAGE_DEBUG_TYPE_COFF", 1),
    ("IMAGE_DEBUG_TYPE_CODEVIEW", 2),
    ("IMAGE_DEBUG_TYPE_FPO", 3),
    ("IMAGE_DEBUG_TYPE_MISC", 4),
    ("IMAGE_DEBUG_TYPE_EXCEPTION", 5),
    ("IMAGE_DEBUG_TYPE_FIXUP", 6),
    ("IMAGE_DEBUG_TYPE_OMAP_TO_SRC", 7),
    ("IMAGE_DEBUG_TYPE_OMAP_FROM_SRC", 8),
    ("IMAGE_DEBUG_TYPE_BORLAND", 9),
    ("IMAGE_DEBUG_TYPE_RESERVED10", 10),
    ("IMAGE_DEBUG_TYPE_CLSID", 11),
    ("IMAGE_DEBUG_TYPE_VC_FEATURE", 12),
    ("IMAGE_DEBUG_TYPE_POGO", 13),
    ("IMAGE_DEBUG_TYPE_ILTCG", 14),
    ("IMAGE_DEBUG_TYPE_MPX", 15),
    ("IMAGE_DEBUG_TYPE_REPRO", 16),
    ("IMAGE_DEBUG_TYPE_EX_DLLCHARACTERISTICS", 20),
]

DEBUG_TYPE = two_way_dict(debug_types)


subsystem_types = [
    ("IMAGE_SUBSYSTEM_UNKNOWN", 0),
    ("IMAGE_SUBSYSTEM_NATIVE", 1),
    ("IMAGE_SUBSYSTEM_WINDOWS_GUI", 2),
    ("IMAGE_SUBSYSTEM_WINDOWS_CUI", 3),
    ("IMAGE_SUBSYSTEM_OS2_CUI", 5),
    ("IMAGE_SUBSYSTEM_POSIX_CUI", 7),
    ("IMAGE_SUBSYSTEM_NATIVE_WINDOWS", 8),
    ("IMAGE_SUBSYSTEM_WINDOWS_CE_GUI", 9),
    ("IMAGE_SUBSYSTEM_EFI_APPLICATION", 10),
    ("IMAGE_SUBSYSTEM_EFI_BOOT_SERVICE_DRIVER", 11),
    ("IMAGE_SUBSYSTEM_EFI_RUNTIME_DRIVER", 12),
    ("IMAGE_SUBSYSTEM_EFI_ROM", 13),
    ("IMAGE_SUBSYSTEM_XBOX", 14),
    ("IMAGE_SUBSYSTEM_WINDOWS_BOOT_APPLICATION", 16),
]

SUBSYSTEM_TYPE = two_way_dict(subsystem_types)


machine_types = [
    ("IMAGE_FILE_MACHINE_UNKNOWN", 0x0),
    ("IMAGE_FILE_MACHINE_I386", 0x014C),
    ("IMAGE_FILE_MACHINE_R3000", 0x0162),
    ("IMAGE_FILE_MACHINE_R4000", 0x0166),
    ("IMAGE_FILE_MACHINE_R10000", 0x0168),
    ("IMAGE_FILE_MACHINE_WCEMIPSV2", 0x0169),
    ("IMAGE_FILE_MACHINE_ALPHA", 0x0184),
    ("IMAGE_FILE_MACHINE_SH3", 0x01A2),
    ("IMAGE_FILE_MACHINE_SH3DSP", 0x01A3),
    ("IMAGE_FILE_MACHINE_SH3E", 0x01A4),
    ("IMAGE_FILE_MACHINE_SH4", 0x01A6),
    ("IMAGE_FILE_MACHINE_SH5", 0x01A8),
    ("IMAGE_FILE_MACHINE_ARM", 0x01C0),
    ("IMAGE_FILE_MACHINE_THUMB", 0x01C2),
    ("IMAGE_FILE_MACHINE_ARMNT", 0x01C4),
    ("IMAGE_FILE_MACHINE_AM33", 0x01D3),
    ("IMAGE_FILE_MACHINE_POWERPC", 0x01F0),
    ("IMAGE_FILE_MACHINE_POWERPCFP", 0x01F1),
    ("IMAGE_FILE_MACHINE_IA64", 0x0200),
    ("IMAGE_FILE_MACHINE_MIPS16", 0x0266),
    ("IMAGE_FILE_MACHINE_ALPHA64", 0x0284),
    ("IMAGE_FILE_MACHINE_AXP64", 0x0284),  # same
    ("IMAGE_FILE_MACHINE_MIPSFPU", 0x0366),
    ("IMAGE_FILE_MACHINE_MIPSFPU16", 0x0466),
    ("IMAGE_FILE_MACHINE_TRICORE", 0x0520),
    ("IMAGE_FILE_MACHINE_CEF", 0x0CEF),
    ("IMAGE_FILE_MACHINE_EBC", 0x0EBC),
    ("IMAGE_FILE_MACHINE_RISCV32", 0x5032),
    ("IMAGE_FILE_MACHINE_RISCV64", 0x5064),
    ("IMAGE_FILE_MACHINE_RISCV128", 0x5128),
    ("IMAGE_FILE_MACHINE_LOONGARCH32", 0x6232),
    ("IMAGE_FILE_MACHINE_LOONGARCH64", 0x6264),
    ("IMAGE_FILE_MACHINE_AMD64", 0x8664),
    ("IMAGE_FILE_MACHINE_M32R", 0x9041),
    ("IMAGE_FILE_MACHINE_ARM64", 0xAA64),
    ("IMAGE_FILE_MACHINE_CEE", 0xC0EE),
]

MACHINE_TYPE = two_way_dict(machine_types)


relocation_types = [
    ("IMAGE_REL_BASED_ABSOLUTE", 0),
    ("IMAGE_REL_BASED_HIGH", 1),
    ("IMAGE_REL_BASED_LOW", 2),
    ("IMAGE_REL_BASED_HIGHLOW", 3),
    ("IMAGE_REL_BASED_HIGHADJ", 4),
    ("IMAGE_REL_BASED_MIPS_JMPADDR", 5),
    ("IMAGE_REL_BASED_SECTION", 6),
    ("IMAGE_REL_BASED_REL", 7),
    ("IMAGE_REL_BASED_MIPS_JMPADDR16", 9),
    ("IMAGE_REL_BASED_IA64_IMM64", 9),
    ("IMAGE_REL_BASED_DIR64", 10),
    ("IMAGE_REL_BASED_HIGH3ADJ", 11),
]

RELOCATION_TYPE = two_way_dict(relocation_types)


dll_characteristics = [
    ("IMAGE_LIBRARY_PROCESS_INIT", 0x0001),  # reserved
    ("IMAGE_LIBRARY_PROCESS_TERM", 0x0002),  # reserved
    ("IMAGE_LIBRARY_THREAD_INIT", 0x0004),  # reserved
    ("IMAGE_LIBRARY_THREAD_TERM", 0x0008),  # reserved
    ("IMAGE_DLLCHARACTERISTICS_HIGH_ENTROPY_VA", 0x0020),
    ("IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE", 0x0040),
    ("IMAGE_DLLCHARACTERISTICS_FORCE_INTEGRITY", 0x0080),
    ("IMAGE_DLLCHARACTERISTICS_NX_COMPAT", 0x0100),
    ("IMAGE_DLLCHARACTERISTICS_NO_ISOLATION", 0x0200),
    ("IMAGE_DLLCHARACTERISTICS_NO_SEH", 0x0400),
    ("IMAGE_DLLCHARACTERISTICS_NO_BIND", 0x0800),
    ("IMAGE_DLLCHARACTERISTICS_APPCONTAINER", 0x1000),
    ("IMAGE_DLLCHARACTERISTICS_WDM_DRIVER", 0x2000),
    ("IMAGE_DLLCHARACTERISTICS_GUARD_CF", 0x4000),
    ("IMAGE_DLLCHARACTERISTICS_TERMINAL_SERVER_AWARE", 0x8000),
]

DLL_CHARACTERISTICS = two_way_dict(dll_characteristics)

FILE_ALIGNMENT_HARDCODED_VALUE = 0x200


# 022316.python.pefile.line365.comment Unwind info-related enums

unwind_info_flags = [
    ("UNW_FLAG_EHANDLER", 0x01),
    ("UNW_FLAG_UHANDLER", 0x02),
    ("UNW_FLAG_CHAININFO", 0x04),
]

UNWIND_INFO_FLAGS = two_way_dict(unwind_info_flags)

registers = [
    ("RAX", 0),
    ("RCX", 1),
    ("RDX", 2),
    ("RBX", 3),
    ("RSP", 4),
    ("RBP", 5),
    ("RSI", 6),
    ("RDI", 7),
    ("R8", 8),
    ("R9", 9),
    ("R10", 10),
    ("R11", 11),
    ("R12", 12),
    ("R13", 13),
    ("R14", 14),
    ("R15", 15),
]

REGISTERS = two_way_dict(registers)

# 022317.python.pefile.line396.comment enum _UNWIND_OP_CODES
UWOP_PUSH_NONVOL = 0
UWOP_ALLOC_LARGE = 1
UWOP_ALLOC_SMALL = 2
UWOP_SET_FPREG = 3
UWOP_SAVE_NONVOL = 4
UWOP_SAVE_NONVOL_FAR = 5
UWOP_EPILOG = 6
UWOP_SAVE_XMM128 = 8
UWOP_SAVE_XMM128_FAR = 9
UWOP_PUSH_MACHFRAME = 10


# 022318.python.pefile.line409.comment Resource types
resource_type = [
    ("RT_CURSOR", 1),
    ("RT_BITMAP", 2),
    ("RT_ICON", 3),
    ("RT_MENU", 4),
    ("RT_DIALOG", 5),
    ("RT_STRING", 6),
    ("RT_FONTDIR", 7),
    ("RT_FONT", 8),
    ("RT_ACCELERATOR", 9),
    ("RT_RCDATA", 10),
    ("RT_MESSAGETABLE", 11),
    ("RT_GROUP_CURSOR", 12),
    ("RT_GROUP_ICON", 14),
    ("RT_VERSION", 16),
    ("RT_DLGINCLUDE", 17),
    ("RT_PLUGPLAY", 19),
    ("RT_VXD", 20),
    ("RT_ANICURSOR", 21),
    ("RT_ANIICON", 22),
    ("RT_HTML", 23),
    ("RT_MANIFEST", 24),
]

RESOURCE_TYPE = two_way_dict(resource_type)


# 022319.python.pefile.line437.comment Language definitions
lang = [
    ("LANG_NEUTRAL", 0x00),
    ("LANG_INVARIANT", 0x7F),
    ("LANG_AFRIKAANS", 0x36),
    ("LANG_ALBANIAN", 0x1C),
    ("LANG_ARABIC", 0x01),
    ("LANG_ARMENIAN", 0x2B),
    ("LANG_ASSAMESE", 0x4D),
    ("LANG_AZERI", 0x2C),
    ("LANG_BASQUE", 0x2D),
    ("LANG_BELARUSIAN", 0x23),
    ("LANG_BENGALI", 0x45),
    ("LANG_BULGARIAN", 0x02),
    ("LANG_CATALAN", 0x03),
    ("LANG_CHINESE", 0x04),
    ("LANG_CROATIAN", 0x1A),
    ("LANG_CZECH", 0x05),
    ("LANG_DANISH", 0x06),
    ("LANG_DIVEHI", 0x65),
    ("LANG_DUTCH", 0x13),
    ("LANG_ENGLISH", 0x09),
    ("LANG_ESTONIAN", 0x25),
    ("LANG_FAEROESE", 0x38),
    ("LANG_FARSI", 0x29),
    ("LANG_FINNISH", 0x0B),
    ("LANG_FRENCH", 0x0C),
    ("LANG_GALICIAN", 0x56),
    ("LANG_GEORGIAN", 0x37),
    ("LANG_GERMAN", 0x07),
    ("LANG_GREEK", 0x08),
    ("LANG_GUJARATI", 0x47),
    ("LANG_HEBREW", 0x0D),
    ("LANG_HINDI", 0x39),
    ("LANG_HUNGARIAN", 0x0E),
    ("LANG_ICELANDIC", 0x0F),
    ("LANG_INDONESIAN", 0x21),
    ("LANG_ITALIAN", 0x10),
    ("LANG_JAPANESE", 0x11),
    ("LANG_KANNADA", 0x4B),
    ("LANG_KASHMIRI", 0x60),
    ("LANG_KAZAK", 0x3F),
    ("LANG_KONKANI", 0x57),
    ("LANG_KOREAN", 0x12),
    ("LANG_KYRGYZ", 0x40),
    ("LANG_LATVIAN", 0x26),
    ("LANG_LITHUANIAN", 0x27),
    ("LANG_MACEDONIAN", 0x2F),
    ("LANG_MALAY", 0x3E),
    ("LANG_MALAYALAM", 0x4C),
    ("LANG_MANIPURI", 0x58),
    ("LANG_MARATHI", 0x4E),
    ("LANG_MONGOLIAN", 0x50),
    ("LANG_NEPALI", 0x61),
    ("LANG_NORWEGIAN", 0x14),
    ("LANG_ORIYA", 0x48),
    ("LANG_POLISH", 0x15),
    ("LANG_PORTUGUESE", 0x16),
    ("LANG_PUNJABI", 0x46),
    ("LANG_ROMANIAN", 0x18),
    ("LANG_RUSSIAN", 0x19),
    ("LANG_SANSKRIT", 0x4F),
    ("LANG_SERBIAN", 0x1A),
    ("LANG_SINDHI", 0x59),
    ("LANG_SLOVAK", 0x1B),
    ("LANG_SLOVENIAN", 0x24),
    ("LANG_SPANISH", 0x0A),
    ("LANG_SWAHILI", 0x41),
    ("LANG_SWEDISH", 0x1D),
    ("LANG_SYRIAC", 0x5A),
    ("LANG_TAMIL", 0x49),
    ("LANG_TATAR", 0x44),
    ("LANG_TELUGU", 0x4A),
    ("LANG_THAI", 0x1E),
    ("LANG_TURKISH", 0x1F),
    ("LANG_UKRAINIAN", 0x22),
    ("LANG_URDU", 0x20),
    ("LANG_UZBEK", 0x43),
    ("LANG_VIETNAMESE", 0x2A),
    ("LANG_GAELIC", 0x3C),
    ("LANG_MALTESE", 0x3A),
    ("LANG_MAORI", 0x28),
    ("LANG_RHAETO_ROMANCE", 0x17),
    ("LANG_SAAMI", 0x3B),
    ("LANG_SORBIAN", 0x2E),
    ("LANG_SUTU", 0x30),
    ("LANG_TSONGA", 0x31),
    ("LANG_TSWANA", 0x32),
    ("LANG_VENDA", 0x33),
    ("LANG_XHOSA", 0x34),
    ("LANG_ZULU", 0x35),
    ("LANG_ESPERANTO", 0x8F),
    ("LANG_WALON", 0x90),
    ("LANG_CORNISH", 0x91),
    ("LANG_WELSH", 0x92),
    ("LANG_BRETON", 0x93),
]

LANG = two_way_dict(lang)


# 022320.python.pefile.line538.comment Sublanguage definitions
sublang = [
    ("SUBLANG_NEUTRAL", 0x00),
    ("SUBLANG_DEFAULT", 0x01),
    ("SUBLANG_SYS_DEFAULT", 0x02),
    ("SUBLANG_ARABIC_SAUDI_ARABIA", 0x01),
    ("SUBLANG_ARABIC_IRAQ", 0x02),
    ("SUBLANG_ARABIC_EGYPT", 0x03),
    ("SUBLANG_ARABIC_LIBYA", 0x04),
    ("SUBLANG_ARABIC_ALGERIA", 0x05),
    ("SUBLANG_ARABIC_MOROCCO", 0x06),
    ("SUBLANG_ARABIC_TUNISIA", 0x07),
    ("SUBLANG_ARABIC_OMAN", 0x08),
    ("SUBLANG_ARABIC_YEMEN", 0x09),
    ("SUBLANG_ARABIC_SYRIA", 0x0A),
    ("SUBLANG_ARABIC_JORDAN", 0x0B),
    ("SUBLANG_ARABIC_LEBANON", 0x0C),
    ("SUBLANG_ARABIC_KUWAIT", 0x0D),
    ("SUBLANG_ARABIC_UAE", 0x0E),
    ("SUBLANG_ARABIC_BAHRAIN", 0x0F),
    ("SUBLANG_ARABIC_QATAR", 0x10),
    ("SUBLANG_AZERI_LATIN", 0x01),
    ("SUBLANG_AZERI_CYRILLIC", 0x02),
    ("SUBLANG_CHINESE_TRADITIONAL", 0x01),
    ("SUBLANG_CHINESE_SIMPLIFIED", 0x02),
    ("SUBLANG_CHINESE_HONGKONG", 0x03),
    ("SUBLANG_CHINESE_SINGAPORE", 0x04),
    ("SUBLANG_CHINESE_MACAU", 0x05),
    ("SUBLANG_DUTCH", 0x01),
    ("SUBLANG_DUTCH_BELGIAN", 0x02),
    ("SUBLANG_ENGLISH_US", 0x01),
    ("SUBLANG_ENGLISH_UK", 0x02),
    ("SUBLANG_ENGLISH_AUS", 0x03),
    ("SUBLANG_ENGLISH_CAN", 0x04),
    ("SUBLANG_ENGLISH_NZ", 0x05),
    ("SUBLANG_ENGLISH_EIRE", 0x06),
    ("SUBLANG_ENGLISH_SOUTH_AFRICA", 0x07),
    ("SUBLANG_ENGLISH_JAMAICA", 0x08),
    ("SUBLANG_ENGLISH_CARIBBEAN", 0x09),
    ("SUBLANG_ENGLISH_BELIZE", 0x0A),
    ("SUBLANG_ENGLISH_TRINIDAD", 0x0B),
    ("SUBLANG_ENGLISH_ZIMBABWE", 0x0C),
    ("SUBLANG_ENGLISH_PHILIPPINES", 0x0D),
    ("SUBLANG_FRENCH", 0x01),
    ("SUBLANG_FRENCH_BELGIAN", 0x02),
    ("SUBLANG_FRENCH_CANADIAN", 0x03),
    ("SUBLANG_FRENCH_SWISS", 0x04),
    ("SUBLANG_FRENCH_LUXEMBOURG", 0x05),
    ("SUBLANG_FRENCH_MONACO", 0x06),
    ("SUBLANG_GERMAN", 0x01),
    ("SUBLANG_GERMAN_SWISS", 0x02),
    ("SUBLANG_GERMAN_AUSTRIAN", 0x03),
    ("SUBLANG_GERMAN_LUXEMBOURG", 0x04),
    ("SUBLANG_GERMAN_LIECHTENSTEIN", 0x05),
    ("SUBLANG_ITALIAN", 0x01),
    ("SUBLANG_ITALIAN_SWISS", 0x02),
    ("SUBLANG_KASHMIRI_SASIA", 0x02),
    ("SUBLANG_KASHMIRI_INDIA", 0x02),
    ("SUBLANG_KOREAN", 0x01),
    ("SUBLANG_LITHUANIAN", 0x01),
    ("SUBLANG_MALAY_MALAYSIA", 0x01),
    ("SUBLANG_MALAY_BRUNEI_DARUSSALAM", 0x02),
    ("SUBLANG_NEPALI_INDIA", 0x02),
    ("SUBLANG_NORWEGIAN_BOKMAL", 0x01),
    ("SUBLANG_NORWEGIAN_NYNORSK", 0x02),
    ("SUBLANG_PORTUGUESE", 0x02),
    ("SUBLANG_PORTUGUESE_BRAZILIAN", 0x01),
    ("SUBLANG_SERBIAN_LATIN", 0x02),
    ("SUBLANG_SERBIAN_CYRILLIC", 0x03),
    ("SUBLANG_SPANISH", 0x01),
    ("SUBLANG_SPANISH_MEXICAN", 0x02),
    ("SUBLANG_SPANISH_MODERN", 0x03),
    ("SUBLANG_SPANISH_GUATEMALA", 0x04),
    ("SUBLANG_SPANISH_COSTA_RICA", 0x05),
    ("SUBLANG_SPANISH_PANAMA", 0x06),
    ("SUBLANG_SPANISH_DOMINICAN_REPUBLIC", 0x07),
    ("SUBLANG_SPANISH_VENEZUELA", 0x08),
    ("SUBLANG_SPANISH_COLOMBIA", 0x09),
    ("SUBLANG_SPANISH_PERU", 0x0A),
    ("SUBLANG_SPANISH_ARGENTINA", 0x0B),
    ("SUBLANG_SPANISH_ECUADOR", 0x0C),
    ("SUBLANG_SPANISH_CHILE", 0x0D),
    ("SUBLANG_SPANISH_URUGUAY", 0x0E),
    ("SUBLANG_SPANISH_PARAGUAY", 0x0F),
    ("SUBLANG_SPANISH_BOLIVIA", 0x10),
    ("SUBLANG_SPANISH_EL_SALVADOR", 0x11),
    ("SUBLANG_SPANISH_HONDURAS", 0x12),
    ("SUBLANG_SPANISH_NICARAGUA", 0x13),
    ("SUBLANG_SPANISH_PUERTO_RICO", 0x14),
    ("SUBLANG_SWEDISH", 0x01),
    ("SUBLANG_SWEDISH_FINLAND", 0x02),
    ("SUBLANG_URDU_PAKISTAN", 0x01),
    ("SUBLANG_URDU_INDIA", 0x02),
    ("SUBLANG_UZBEK_LATIN", 0x01),
    ("SUBLANG_UZBEK_CYRILLIC", 0x02),
    ("SUBLANG_DUTCH_SURINAM", 0x03),
    ("SUBLANG_ROMANIAN", 0x01),
    ("SUBLANG_ROMANIAN_MOLDAVIA", 0x02),
    ("SUBLANG_RUSSIAN", 0x01),
    ("SUBLANG_RUSSIAN_MOLDAVIA", 0x02),
    ("SUBLANG_CROATIAN", 0x01),
    ("SUBLANG_LITHUANIAN_CLASSIC", 0x02),
    ("SUBLANG_GAELIC", 0x01),
    ("SUBLANG_GAELIC_SCOTTISH", 0x02),
    ("SUBLANG_GAELIC_MANX", 0x03),
]

SUBLANG = two_way_dict(sublang)

# 022321.python.pefile.line647.comment Initialize the dictionary with all the name->value pairs
SUBLANG = dict(sublang)
# 022322.python.pefile.line649.comment Now add all the value->name information, handling duplicates appropriately
for sublang_name, sublang_value in sublang:
    if sublang_value in SUBLANG:
        SUBLANG[sublang_value].append(sublang_name)
    else:
        SUBLANG[sublang_value] = [sublang_name]

# 022323.python.pefile.line656.comment Resolve a sublang name given the main lang name
# 022324.python.pefile.line657.comment
def get_sublang_name_for_lang(lang_value, sublang_value):
    lang_name = LANG.get(lang_value, "*unknown*")
    for sublang_name in SUBLANG.get(sublang_value, []):
        # 022325.python.pefile.line661.comment if the main language is a substring of sublang's name, then
        # 022326.python.pefile.line662.comment return that
        if lang_name in sublang_name:
            return sublang_name
    # 022327.python.pefile.line665.comment otherwise return the first sublang name
    return SUBLANG.get(sublang_value, ["*unknown*"])[0]


# 022328.python.pefile.line669.comment Ange Albertini's code to process resources' strings
# 022329.python.pefile.line670.comment
def parse_strings(data, counter, l):
    i = 0
    error_count = 0
    while i < len(data):

        data_slice = data[i : i + 2]
        if len(data_slice) < 2:
            break

        len_ = struct.unpack("<h", data_slice)[0]
        i += 2
        if len_ != 0 and 0 <= len_ * 2 <= len(data):
            try:
                l[counter] = b(data[i : i + len_ * 2]).decode("utf-16le")
            except UnicodeDecodeError:
                error_count += 1
                pass
            if error_count >= 3:
                break
            i += len_ * 2
        counter += 1


def retrieve_flags(flag_dict, flag_filter):
    """Read the flags from a dictionary and return them in a usable form.

    Will return a list of (flag, value) for all flags in "flag_dict"
    matching the filter "flag_filter".
    """

    return [
        (flag, flag_dict[flag])
        for flag in flag_dict.keys()
        if isinstance(flag, (str, bytes)) and flag.startswith(flag_filter)
    ]


def set_flags(obj, flag_field, flags):
    """Will process the flags and set attributes in the object accordingly.

    The object "obj" will gain attributes named after the flags provided in
    "flags" and valued True/False, matching the results of applying each
    flag value from "flags" to flag_field.
    """

    for flag, value in flags:
        if value & flag_field:
            obj.__dict__[flag] = True
        else:
            obj.__dict__[flag] = False


def power_of_two(val):
    return val != 0 and (val & (val - 1)) == 0


def b(x):
    if isinstance(x, bytes):
        return x
    elif isinstance(x, bytearray):
        return bytes(x)
    else:
        return codecs.encode(x, "cp1252")


class AddressSet(set):
    def __init__(self):
        super().__init__()
        self.min = None
        self.max = None

    def add(self, value):
        super().add(value)
        self.min = value if self.min is None else min(self.min, value)
        self.max = value if self.max is None else max(self.max, value)

    def diff(self):
        return 0 if self.min is None or self.max is None else self.max - self.min


class UnicodeStringWrapperPostProcessor:
    """This class attempts to help the process of identifying strings
    that might be plain Unicode or Pascal. A list of strings will be
    wrapped on it with the hope the overlappings will help make the
    decision about their type."""

    def __init__(self, pe, rva_ptr):
        self.pe = pe
        self.rva_ptr = rva_ptr
        self.string = None

    def get_rva(self):
        """Get the RVA of the string."""
        return self.rva_ptr

    def __str__(self):
        """Return the escaped UTF-8 representation of the string."""
        return self.decode("utf-8", "backslashreplace_")

    def decode(self, *args):
        if not self.string:
            return ""
        return self.string.decode(*args)

    def invalidate(self):
        """Make this instance None, to express it's no known string type."""
        self = None

    def render_pascal_16(self):
        try:
            self.string = self.pe.get_string_u_at_rva(
                self.rva_ptr + 2, max_length=self.get_pascal_16_length()
            )
        except PEFormatError:
            self.pe.get_warnings().append(
                "Failed rendering pascal string, "
                "attempting to read from RVA 0x{0:x}".format(self.rva_ptr + 2)
            )

    def get_pascal_16_length(self):
        return self.__get_word_value_at_rva(self.rva_ptr)

    def __get_word_value_at_rva(self, rva):
        try:
            data = self.pe.get_data(rva, 2)
        except PEFormatError:
            return False

        if len(data) < 2:
            return False

        return struct.unpack("<H", data)[0]

    def ask_unicode_16(self, next_rva_ptr):
        """The next RVA is taken to be the one immediately following this one.

        Such RVA could indicate the natural end of the string and will be checked
        to see if there's a Unicode NULL character there.
        """
        if self.__get_word_value_at_rva(next_rva_ptr - 2) == 0:
            self.length = next_rva_ptr - self.rva_ptr
            return True

        return False

    def render_unicode_16(self):
        try:
            self.string = self.pe.get_string_u_at_rva(self.rva_ptr)
        except PEFormatError:
            self.pe.get_warnings().append(
                "Failed rendering unicode string, "
                "attempting to read from RVA 0x{0:x}".format(self.rva_ptr)
            )


class PEFormatError(Exception):
    """Generic PE format error exception."""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Dump:
    """Convenience class for dumping the PE information."""

    def __init__(self):
        self.text = []

    def add_lines(self, txt, indent=0):
        """Adds a list of lines.

        The list can be indented with the optional argument 'indent'.
        """
        for line in txt:
            self.add_line(line, indent)

    def add_line(self, txt, indent=0):
        """Adds a line.

        The line can be indented with the optional argument 'indent'.
        """
        self.add(txt + "\n", indent)

    def add(self, txt, indent=0):
        """Adds some text, no newline will be appended.

        The text can be indented with the optional argument 'indent'.
        """
        self.text.append("{0}{1}".format(" " * indent, txt))

    def add_header(self, txt):
        """Adds a header element."""
        self.add_line("{0}{1}{0}\n".format("-" * 10, txt))

    def add_newline(self):
        """Adds a newline."""
        self.text.append("\n")

    def get_text(self):
        """Get the text in its current state."""
        return "".join("{0}".format(b) for b in self.text)


STRUCT_SIZEOF_TYPES = {
    "x": 1,
    "c": 1,
    "b": 1,
    "B": 1,
    "h": 2,
    "H": 2,
    "i": 4,
    "I": 4,
    "l": 4,
    "L": 4,
    "f": 4,
    "q": 8,
    "Q": 8,
    "d": 8,
    "s": 1,
}


@lru_cache(maxsize=2048)
def sizeof_type(t):
    count = 1
    _t = t
    if t[0] in string.digits:
        # 022330.python.pefile.line901.comment extract the count
        count = int("".join([d for d in t if d in string.digits]))
        _t = "".join([d for d in t if d not in string.digits])
    return STRUCT_SIZEOF_TYPES[_t] * count


@lru_cache(maxsize=2048, copy=True)
def set_format(format):

    __format_str__ = "<"
    __unpacked_data_elms__ = []
    __field_offsets__ = {}
    __keys__ = []
    __format_length__ = 0

    offset = 0
    for elm in format:
        if "," in elm:
            elm_type, elm_name = elm.split(",", 1)
            __format_str__ += elm_type
            __unpacked_data_elms__.append(None)

            elm_names = elm_name.split(",")
            names = []
            for elm_name in elm_names:
                if elm_name in __keys__:
                    search_list = [x[: len(elm_name)] for x in __keys__]
                    occ_count = search_list.count(elm_name)
                    elm_name = "{0}_{1:d}".format(elm_name, occ_count)
                names.append(elm_name)
                __field_offsets__[elm_name] = offset

            offset += sizeof_type(elm_type)

            # 022331.python.pefile.line935.comment Some PE header structures have unions on them, so a certain
            # 022332.python.pefile.line936.comment value might have different names, so each key has a list of
            # 022333.python.pefile.line937.comment all the possible members referring to the data.
            __keys__.append(names)

    __format_length__ = struct.calcsize(__format_str__)

    return (
        __format_str__,
        __unpacked_data_elms__,
        __field_offsets__,
        __keys__,
        __format_length__,
    )


class Structure:
    """Prepare structure object to extract members from data.

    Format is a list containing definitions for the elements
    of the structure.
    """

    def __init__(self, format, name=None, file_offset=None):
        # 022334.python.pefile.line959.comment Format is forced little endian, for big endian non Intel platforms
        self.__format_str__ = "<"
        self.__keys__ = []
        self.__format_length__ = 0
        self.__field_offsets__ = {}
        self.__unpacked_data_elms__ = []

        d = format[1]
        # 022335.python.pefile.line967.comment need a tuple to be hashable in set_format using lru cache
        if not isinstance(d, tuple):
            d = tuple(d)

        (
            self.__format_str__,
            self.__unpacked_data_elms__,
            self.__field_offsets__,
            self.__keys__,
            self.__format_length__,
        ) = set_format(d)

        self.__all_zeroes__ = False
        self.__file_offset__ = file_offset
        if name:
            self.name = name
        else:
            self.name = format[0]

    def __get_format__(self) -> str:
        return self.__format_str__

    def get_field_absolute_offset(self, field_name):
        """Return the offset within the field for the requested field in the structure."""
        return self.__file_offset__ + self.__field_offsets__[field_name]

    def get_field_relative_offset(self, field_name):
        """Return the offset within the structure for the requested field."""
        return self.__field_offsets__[field_name]

    def get_file_offset(self):
        return self.__file_offset__

    def set_file_offset(self, offset):
        self.__file_offset__ = offset

    def all_zeroes(self):
        """Returns true is the unpacked data is all zeros."""

        return self.__all_zeroes__

    def sizeof(self):
        """Return size of the structure."""

        return self.__format_length__

    def __unpack__(self, data):

        data = b(data)

        if len(data) > self.__format_length__:
            data = data[: self.__format_length__]

        # 022336.python.pefile.line1020.comment OC Patch:
        # 022337.python.pefile.line1021.comment Some malware have incorrect header lengths.
        # 022338.python.pefile.line1022.comment Fail gracefully if this occurs
        # 022339.python.pefile.line1023.comment Buggy malware: a29b0118af8b7408444df81701ad5a7f
        # 022340.python.pefile.line1024.comment
        elif len(data) < self.__format_length__:
            raise PEFormatError("Data length less than expected header length.")

        if count_zeroes(data) == len(data):
            self.__all_zeroes__ = True

        self.__unpacked_data_elms__ = struct.unpack(self.__format_str__, data)
        for idx, val in enumerate(self.__unpacked_data_elms__):
            for key in self.__keys__[idx]:
                setattr(self, key, val)

    def __pack__(self):

        new_values = []

        for idx, val in enumerate(self.__unpacked_data_elms__):
            new_val = None
            for key in self.__keys__[idx]:
                new_val = getattr(self, key)
                # 022341.python.pefile.line1044.comment In the case of unions, when the first changed value
                # 022342.python.pefile.line1045.comment is picked the loop is exited
                if new_val != val:
                    break
            new_values.append(new_val)

        return struct.pack(self.__format_str__, *new_values)

    def __str__(self):
        return "\n".join(self.dump())

    def __repr__(self):
        return "<Structure: %s>" % (
            " ".join([" ".join(s.split()) for s in self.dump()])
        )

    def dump(self, indentation=0):
        """Returns a string representation of the structure."""

        dump = []

        dump.append("[{0}]".format(self.name))

        printable_bytes = [
            ord(i) for i in string.printable if i not in string.whitespace
        ]

        # 022343.python.pefile.line1071.comment Refer to the __set_format__ method for an explanation
        # 022344.python.pefile.line1072.comment of the following construct.
        for keys in self.__keys__:
            for key in keys:

                val = getattr(self, key)
                if isinstance(val, (int, long)):
                    if key.startswith("Signature_"):
                        val_str = "{:<8X}".format(val)
                    else:
                        val_str = "0x{:<8X}".format(val)
                    if key == "TimeDateStamp" or key == "dwTimeStamp":
                        try:
                            val_str += " [%s UTC]" % time.asctime(time.gmtime(val))
                        except ValueError:
                            val_str += " [INVALID TIME]"
                else:
                    val_str = bytearray(val)
                    if key.startswith("Signature"):
                        val_str = "".join(
                            ["{:02X}".format(i) for i in val_str.rstrip(b"\x00")]
                        )
                    else:
                        val_str = "".join(
                            [
                                chr(i)
                                if (i in printable_bytes)
                                else "\\x{0:02x}".format(i)
                                for i in val_str.rstrip(b"\x00")
                            ]
                        )

                dump.append(
                    "0x%-8X 0x%-3X %-30s %s"
                    % (
                        self.__field_offsets__[key] + self.__file_offset__,
                        self.__field_offsets__[key],
                        key + ":",
                        val_str,
                    )
                )

        return dump

    def dump_dict(self):
        """Returns a dictionary representation of the structure."""

        dump_dict = {}

        dump_dict["Structure"] = self.name

        # 022345.python.pefile.line1122.comment Refer to the __set_format__ method for an explanation
        # 022346.python.pefile.line1123.comment of the following construct.
        for keys in self.__keys__:
            for key in keys:

                val = getattr(self, key)
                if isinstance(val, (int, long)):
                    if key == "TimeDateStamp" or key == "dwTimeStamp":
                        try:
                            val = "0x%-8X [%s UTC]" % (
                                val,
                                time.asctime(time.gmtime(val)),
                            )
                        except ValueError:
                            val = "0x%-8X [INVALID TIME]" % val
                else:
                    val = "".join(
                        chr(d) if chr(d) in string.printable else "\\x%02x" % d
                        for d in [ord(c) if not isinstance(c, int) else c for c in val]
                    )

                dump_dict[key] = {
                    "FileOffset": self.__field_offsets__[key] + self.__file_offset__,
                    "Offset": self.__field_offsets__[key],
                    "Value": val,
                }

        return dump_dict


class SectionStructure(Structure):
    """Convenience section handling class."""

    def __init__(self, *argl, **argd):
        if "pe" in argd:
            self.pe = argd["pe"]
            del argd["pe"]

        self.PointerToRawData = None
        self.VirtualAddress = None
        self.SizeOfRawData = None
        self.Misc_VirtualSize = None
        Structure.__init__(self, *argl, **argd)
        self.PointerToRawData_adj = None
        self.VirtualAddress_adj = None
        self.section_min_addr = None
        self.section_max_addr = None

    def get_PointerToRawData_adj(self):
        if self.PointerToRawData_adj is None:
            if self.PointerToRawData is not None:
                self.PointerToRawData_adj = self.pe.adjust_FileAlignment(
                    self.PointerToRawData, self.pe.OPTIONAL_HEADER.FileAlignment
                )
        return self.PointerToRawData_adj

    def get_VirtualAddress_adj(self):
        if self.VirtualAddress_adj is None:
            if self.VirtualAddress is not None:
                self.VirtualAddress_adj = self.pe.adjust_SectionAlignment(
                    self.VirtualAddress,
                    self.pe.OPTIONAL_HEADER.SectionAlignment,
                    self.pe.OPTIONAL_HEADER.FileAlignment,
                )
        return self.VirtualAddress_adj

    def get_data(self, start=None, length=None, ignore_padding=False):
        """Get data chunk from a section.

        Allows to query data from the section by passing the
        addresses where the PE file would be loaded by default.
        It is then possible to retrieve code and data by their real
        addresses as they would be if loaded.

        Note that sections on disk can include padding that would
        not be loaded to memory. That is the case if `section.SizeOfRawData`
        is greater than `section.Misc_VirtualSize`, and that means
        that data past `section.Misc_VirtualSize` is padding.
        In case you are not interested in this padding, passing
        `ignore_padding=True` will truncate the result in order
        not to return the padding (if any).

        Returns bytes() under Python 3.x and set() under Python 2.7
        """

        if start is None:
            offset = self.get_PointerToRawData_adj()
        else:
            offset = (
                start - self.get_VirtualAddress_adj()
            ) + self.get_PointerToRawData_adj()

        if length is not None:
            end = offset + length
        elif self.SizeOfRawData is not None:
            end = offset + self.SizeOfRawData
        else:
            end = offset

        if ignore_padding and end is not None and offset is not None:
            end = min(end, offset + self.Misc_VirtualSize)

        # 022347.python.pefile.line1224.comment PointerToRawData is not adjusted here as we might want to read any possible
        # 022348.python.pefile.line1225.comment extra bytes that might get cut off by aligning the start (and hence cutting
        # 022349.python.pefile.line1226.comment something off the end)
        if self.PointerToRawData is not None and self.SizeOfRawData is not None:
            if end > self.PointerToRawData + self.SizeOfRawData:
                end = self.PointerToRawData + self.SizeOfRawData
        return self.pe.__data__[offset:end]

    def __setattr__(self, name, val):

        if name == "Characteristics":
            section_flags = retrieve_flags(SECTION_CHARACTERISTICS, "IMAGE_SCN_")

            # 022350.python.pefile.line1237.comment Set the section's flags according to the Characteristics member
            set_flags(self, val, section_flags)

        elif "IMAGE_SCN_" in name and hasattr(self, name):
            if val:
                self.__dict__["Characteristics"] |= SECTION_CHARACTERISTICS[name]
            else:
                self.__dict__["Characteristics"] ^= SECTION_CHARACTERISTICS[name]

        self.__dict__[name] = val

    def get_rva_from_offset(self, offset):
        return offset - self.get_PointerToRawData_adj() + self.get_VirtualAddress_adj()

    def get_offset_from_rva(self, rva):
        return rva - self.get_VirtualAddress_adj() + self.get_PointerToRawData_adj()

    def contains_offset(self, offset):
        """Check whether the section contains the file offset provided."""

        if self.PointerToRawData is None:
            # 022351.python.pefile.line1258.comment bss and other sections containing only uninitialized data must have 0
            # 022352.python.pefile.line1259.comment and do not take space in the file
            return False
        PointerToRawData_adj = self.get_PointerToRawData_adj()
        return (
            PointerToRawData_adj <= offset < PointerToRawData_adj + self.SizeOfRawData
        )

    def contains_rva(self, rva):
        """Check whether the section contains the address provided."""

        # 022353.python.pefile.line1269.comment speedup
        if self.section_min_addr is not None and self.section_max_addr is not None:
            return self.section_min_addr <= rva < self.section_max_addr

        VirtualAddress_adj = self.get_VirtualAddress_adj()
        # 022354.python.pefile.line1274.comment Check if the SizeOfRawData is realistic. If it's bigger than the size of
        # 022355.python.pefile.line1275.comment the whole PE file minus the start address of the section it could be
        # 022356.python.pefile.line1276.comment either truncated or the SizeOfRawData contains a misleading value.
        # 022357.python.pefile.line1277.comment In either of those cases we take the VirtualSize
        # 022358.python.pefile.line1278.comment
        if len(self.pe.__data__) - self.get_PointerToRawData_adj() < self.SizeOfRawData:
            # 022359.python.pefile.line1280.comment PECOFF documentation v8 says:
            # 022360.python.pefile.line1281.comment VirtualSize: The total size of the section when loaded into memory.
            # 022361.python.pefile.line1282.comment If this value is greater than SizeOfRawData, the section is zero-padded.
            # 022362.python.pefile.line1283.comment This field is valid only for executable images and should be set to zero
            # 022363.python.pefile.line1284.comment for object files.
            # 022364.python.pefile.line1285.comment
            size = self.Misc_VirtualSize
        else:
            size = max(self.SizeOfRawData, self.Misc_VirtualSize)

        # 022365.python.pefile.line1290.comment Check whether there's any section after the current one that starts before
        # 022366.python.pefile.line1291.comment the calculated end for the current one. If so, cut the current section's size
        # 022367.python.pefile.line1292.comment to fit in the range up to where the next section starts.
        if (
            self.next_section_virtual_address is not None
            and self.next_section_virtual_address > self.VirtualAddress
            and VirtualAddress_adj + size > self.next_section_virtual_address
        ):
            size = self.next_section_virtual_address - VirtualAddress_adj

        self.section_min_addr = VirtualAddress_adj
        self.section_max_addr = VirtualAddress_adj + size
        return VirtualAddress_adj <= rva < VirtualAddress_adj + size

    def contains(self, rva):
        return self.contains_rva(rva)

    def get_entropy(self):
        """Calculate and return the entropy for the section."""

        return self.entropy_H(self.get_data())

    def get_hash_sha1(self):
        """Get the SHA-1 hex-digest of the section's data."""

        if sha1 is not None:
            return sha1(self.get_data()).hexdigest()

    def get_hash_sha256(self):
        """Get the SHA-256 hex-digest of the section's data."""

        if sha256 is not None:
            return sha256(self.get_data()).hexdigest()

    def get_hash_sha512(self):
        """Get the SHA-512 hex-digest of the section's data."""

        if sha512 is not None:
            return sha512(self.get_data()).hexdigest()

    def get_hash_md5(self):
        """Get the MD5 hex-digest of the section's data."""

        if md5 is not None:
            return md5(self.get_data()).hexdigest()

    def entropy_H(self, data):
        """Calculate the entropy of a chunk of data."""

        if not data:
            return 0.0

        occurences = Counter(bytearray(data))

        entropy = 0
        for x in occurences.values():
            p_x = float(x) / len(data)
            entropy -= p_x * math.log(p_x, 2)

        return entropy


@lru_cache(maxsize=2048, copy=False)
def set_bitfields_format(format):
    class Accumulator:
        def __init__(self, fmt, comp_fields):
            self._subfields = []
            # 022368.python.pefile.line1357.comment add a prefix to distinguish the artificially created compoud field
            # 022369.python.pefile.line1358.comment from regular fields
            self._name = "~"
            self._type = None
            self._bits_left = 0
            self._comp_fields = comp_fields
            self._format = fmt

        def wrap_up(self):
            if self._type is None:
                return
            self._format.append(self._type + "," + self._name)
            self._comp_fields[len(self._format) - 1] = (self._type, self._subfields)
            self._name = "~"
            self._type = None
            self._subfields = []

        def new_type(self, tp):
            self._bits_left = STRUCT_SIZEOF_TYPES[tp] * 8
            self._type = tp

        def add_subfield(self, name, bitcnt):
            self._name += name
            self._bits_left -= bitcnt
            self._subfields.append((name, bitcnt))

        def get_type(self):
            return self._type

        def get_name(self):
            return self._name

        def get_bits_left(self):
            return self._bits_left

    old_fmt = []
    comp_fields = {}
    ac = Accumulator(old_fmt, comp_fields)

    for elm in format[1]:
        if not ":" in elm:
            ac.wrap_up()
            old_fmt.append(elm)
            continue

        elm_type, elm_name = elm.split(",", 1)

        if "," in elm_name:
            raise NotImplementedError(
                "Structures with bitfields do not support unions yet"
            )

        elm_type, elm_bits = elm_type.split(":", 1)
        elm_bits = int(elm_bits)
        if elm_type != ac.get_type() or elm_bits > ac.get_bits_left():
            ac.wrap_up()
            ac.new_type(elm_type)

        ac.add_subfield(elm_name, elm_bits)
    ac.wrap_up()

    format_str, _, field_offsets, keys, format_length = set_format(tuple(old_fmt))

    extended_keys = []
    for idx, val in enumerate(keys):
        if not idx in comp_fields:
            extended_keys.append(val)
            continue
        _, sbf = comp_fields[idx]
        bf_names = [[f[StructureWithBitfields.BTF_NAME_IDX]] for f in sbf]
        extended_keys.extend(bf_names)
        for n in bf_names:
            field_offsets[n[0]] = field_offsets[val[0]]

    return (format_str, format_length, field_offsets, keys, extended_keys, comp_fields)


class StructureWithBitfields(Structure):
    """
    Extends Structure's functionality with support for bitfields such as:
        ('B:4,LowerHalf', 'B:4,UpperHalf')
    To this end, two lists are maintained:
        * self.__keys__ that contains compound fields, for example
          ('B,~LowerHalfUpperHalf'), and is used during packing/unpaking
        * self.__keys_ext__ containing a separate key for each field (ex., LowerHalf,
          UpperHalf) to simplify implementation of dump()
    This way the implementation of unpacking/packing and dump() from Structure can be
    reused.

    In addition, we create a dictionary:
        <comound_field_index_in_keys> -->
            (data type, [ (subfield name, length in bits)+ ] )
    that facilitates bitfield paking and unpacking.

    With lru_cache() creating only once instance per format string, the memory
    overhead is negligible.
    """

    BTF_NAME_IDX = 0
    BTF_BITCNT_IDX = 1
    CF_TYPE_IDX = 0
    CF_SUBFLD_IDX = 1

    def __init__(self, format, name=None, file_offset=None):
        (
            self.__format_str__,
            self.__format_length__,
            self.__field_offsets__,
            self.__keys__,
            self.__keys_ext__,
            self.__compound_fields__,
        ) = set_bitfields_format(format)
        # 022370.python.pefile.line1469.comment create our own unpacked_data_elms to ensure they are not shared among
        # 022371.python.pefile.line1470.comment StructureWithBitfields instances with the same format string
        self.__unpacked_data_elms__ = [None for i in range(self.__format_length__)]
        self.__all_zeroes__ = False
        self.__file_offset__ = file_offset
        self.name = name if name != None else format[0]

    def __unpack__(self, data):
        # 022372.python.pefile.line1477.comment calling the original routine to deal with special cases/spurious data
        # 022373.python.pefile.line1478.comment structures
        super(StructureWithBitfields, self).__unpack__(data)
        self._unpack_bitfield_attributes()

    def __pack__(self):
        self._pack_bitfield_attributes()
        try:
            data = super(StructureWithBitfields, self).__pack__()
        finally:
            self._unpack_bitfield_attributes()
        return data

    def dump(self, indentation=0):
        tk = self.__keys__
        self.__keys__ = self.__keys_ext__
        try:
            ret = super(StructureWithBitfields, self).dump(indentation)
        finally:
            self.__keys__ = tk
        return ret

    def dump_dict(self):
        tk = self.__keys__
        self.__keys__ = self.__keys_ext__
        try:
            ret = super(StructureWithBitfields, self).dump_dict()
        finally:
            self.__keys__ = tk
        return ret

    def _unpack_bitfield_attributes(self):
        """Replace compound attributes corresponding to bitfields with separate
        sub-fields.
        """
        for i in self.__compound_fields__.keys():
            cf_name = self.__keys__[i][0]
            cval = getattr(self, cf_name)
            delattr(self, cf_name)
            offst = 0
            for sf in self.__compound_fields__[i][StructureWithBitfields.CF_SUBFLD_IDX]:
                mask = (1 << sf[StructureWithBitfields.BTF_BITCNT_IDX]) - 1
                mask <<= offst
                setattr(
                    self,
                    sf[StructureWithBitfields.BTF_NAME_IDX],
                    (cval & mask) >> offst,
                )
                offst += sf[StructureWithBitfields.BTF_BITCNT_IDX]

    def _pack_bitfield_attributes(self):
        """Pack attributes into a compound bitfield"""
        for i in self.__compound_fields__.keys():
            cf_name = self.__keys__[i][0]
            offst, acc_val = 0, 0
            for sf in self.__compound_fields__[i][StructureWithBitfields.CF_SUBFLD_IDX]:
                mask = (1 << sf[StructureWithBitfields.BTF_BITCNT_IDX]) - 1
                field_val = (
                    getattr(self, sf[StructureWithBitfields.BTF_NAME_IDX]) & mask
                )
                acc_val |= field_val << offst
                offst += sf[StructureWithBitfields.BTF_BITCNT_IDX]
            setattr(self, cf_name, acc_val)


class DataContainer:
    """Generic data container."""

    def __init__(self, **args):
        bare_setattr = super(DataContainer, self).__setattr__
        for key, value in args.items():
            bare_setattr(key, value)


class ImportDescData(DataContainer):
    """Holds import descriptor information.

    dll:        name of the imported DLL
    imports:    list of imported symbols (ImportData instances)
    struct:     IMAGE_IMPORT_DESCRIPTOR structure
    """


class ImportData(DataContainer):
    """Holds imported symbol's information.

    ordinal:    Ordinal of the symbol
    name:       Name of the symbol
    bound:      If the symbol is bound, this contains
                the address.
    """

    def __setattr__(self, name, val):

        # 022374.python.pefile.line1571.comment If the instance doesn't yet have an ordinal attribute
        # 022375.python.pefile.line1572.comment it's not fully initialized so can't do any of the
        # 022376.python.pefile.line1573.comment following
        # 022377.python.pefile.line1574.comment
        if (
            hasattr(self, "ordinal")
            and hasattr(self, "bound")
            and hasattr(self, "name")
        ):

            if name == "ordinal":

                if self.pe.PE_TYPE == OPTIONAL_HEADER_MAGIC_PE:
                    ordinal_flag = IMAGE_ORDINAL_FLAG
                elif self.pe.PE_TYPE == OPTIONAL_HEADER_MAGIC_PE_PLUS:
                    ordinal_flag = IMAGE_ORDINAL_FLAG64

                # 022378.python.pefile.line1588.comment Set the ordinal and flag the entry as importing by ordinal
                self.struct_table.Ordinal = ordinal_flag | (val & 0xFFFF)
                self.struct_table.AddressOfData = self.struct_table.Ordinal
                self.struct_table.Function = self.struct_table.Ordinal
                self.struct_table.ForwarderString = self.struct_table.Ordinal
            elif name == "bound":
                if self.struct_iat is not None:
                    self.struct_iat.AddressOfData = val
                    self.struct_iat.AddressOfData = self.struct_iat.AddressOfData
                    self.struct_iat.Function = self.struct_iat.AddressOfData
                    self.struct_iat.ForwarderString = self.struct_iat.AddressOfData
            elif name == "address":
                self.struct_table.AddressOfData = val
                self.struct_table.Ordinal = self.struct_table.AddressOfData
                self.struct_table.Function = self.struct_table.AddressOfData
                self.struct_table.ForwarderString = self.struct_table.AddressOfData
            elif name == "name":
                # 022379.python.pefile.line1605.comment Make sure we reset the entry in case the import had been set to
                # 022380.python.pefile.line1606.comment import by ordinal
                if self.name_offset:

                    name_rva = self.pe.get_rva_from_offset(self.name_offset)
                    self.pe.set_dword_at_offset(
                        self.ordinal_offset, (0 << 31) | name_rva
                    )

                    # 022381.python.pefile.line1614.comment Complain if the length of the new name is longer than the
                    # 022382.python.pefile.line1615.comment existing one
                    if len(val) > len(self.name):
                        raise PEFormatError(
                            "The export name provided is longer than the existing one."
                        )
                        pass
                    self.pe.set_bytes_at_offset(self.name_offset, val)

        self.__dict__[name] = val


class ExportDirData(DataContainer):
    """Holds export directory information.

    struct:     IMAGE_EXPORT_DIRECTORY structure
    symbols:    list of exported symbols (ExportData instances)"""


class ExportData(DataContainer):
    """Holds exported symbols' information.

    ordinal:    ordinal of the symbol
    address:    address of the symbol
    name:       name of the symbol (None if the symbol is
                exported by ordinal only)
    forwarder:  if the symbol is forwarded it will
                contain the name of the target symbol,
                None otherwise.
    """

    def __setattr__(self, name, val):

        # 022383.python.pefile.line1647.comment If the instance doesn't yet have an ordinal attribute
        # 022384.python.pefile.line1648.comment it's not fully initialized so can't do any of the
        # 022385.python.pefile.line1649.comment following
        # 022386.python.pefile.line1650.comment
        if (
            hasattr(self, "ordinal")
            and hasattr(self, "address")
            and hasattr(self, "forwarder")
            and hasattr(self, "name")
        ):

            if name == "ordinal":
                self.pe.set_word_at_offset(self.ordinal_offset, val)
            elif name == "address":
                self.pe.set_dword_at_offset(self.address_offset, val)
            elif name == "name":
                # 022387.python.pefile.line1663.comment Complain if the length of the new name is longer than the
                # 022388.python.pefile.line1664.comment existing one
                if len(val) > len(self.name):
                    raise PEFormatError(
                        "The export name provided is longer than the existing one."
                    )
                self.pe.set_bytes_at_offset(self.name_offset, val)
            elif name == "forwarder":
                # 022389.python.pefile.line1671.comment Complain if the length of the new name is longer than the
                # 022390.python.pefile.line1672.comment existing one
                if len(val) > len(self.forwarder):
                    raise PEFormatError(
                        "The forwarder name provided is longer than the existing one."
                    )
                self.pe.set_bytes_at_offset(self.forwarder_offset, val)

        self.__dict__[name] = val


class ResourceDirData(DataContainer):
    """Holds resource directory information.

    struct:     IMAGE_RESOURCE_DIRECTORY structure
    entries:    list of entries (ResourceDirEntryData instances)
    """


class ResourceDirEntryData(DataContainer):
    """Holds resource directory entry data.

    struct:     IMAGE_RESOURCE_DIRECTORY_ENTRY structure
    name:       If the resource is identified by name this
                attribute will contain the name string. None
                otherwise. If identified by id, the id is
                available at 'struct.Id'
    id:         the id, also in struct.Id
    directory:  If this entry has a lower level directory
                this attribute will point to the
                ResourceDirData instance representing it.
    data:       If this entry has no further lower directories
                and points to the actual resource data, this
                attribute will reference the corresponding
                ResourceDataEntryData instance.
    (Either of the 'directory' or 'data' attribute will exist,
    but not both.)
    """


class ResourceDataEntryData(DataContainer):
    """Holds resource data entry information.

    struct:     IMAGE_RESOURCE_DATA_ENTRY structure
    lang:       Primary language ID
    sublang:    Sublanguage ID
    """


class DebugData(DataContainer):
    """Holds debug information.

    struct:     IMAGE_DEBUG_DIRECTORY structure
    entries:    list of entries (IMAGE_DEBUG_TYPE instances)
    """


class DynamicRelocationData(DataContainer):
    """Holds dynamic relocation information.

    struct:        IMAGE_DYNAMIC_RELOCATION structure
    symbol:        Symbol to which dynamic relocations must be applied
    relocations:   List of dynamic relocations for this symbol (BaseRelocationData instances)
    """


class BaseRelocationData(DataContainer):
    """Holds base relocation information.

    struct:     IMAGE_BASE_RELOCATION structure
    entries:    list of relocation data (RelocationData instances)
    """


class RelocationData(DataContainer):
    """Holds relocation information.

    type:       Type of relocation
                The type string can be obtained by
                RELOCATION_TYPE[type]
    rva:        RVA of the relocation
    """

    def __setattr__(self, name, val):

        # 022391.python.pefile.line1756.comment If the instance doesn't yet have a struct attribute
        # 022392.python.pefile.line1757.comment it's not fully initialized so can't do any of the
        # 022393.python.pefile.line1758.comment following
        # 022394.python.pefile.line1759.comment
        if hasattr(self, "struct"):
            # 022395.python.pefile.line1761.comment Get the word containing the type and data
            # 022396.python.pefile.line1762.comment
            word = self.struct.Data

            if name == "type":
                word = (val << 12) | (word & 0xFFF)
            elif name == "rva":
                offset = max(val - self.base_rva, 0)
                word = (word & 0xF000) | (offset & 0xFFF)

            # 022397.python.pefile.line1771.comment Store the modified data
            # 022398.python.pefile.line1772.comment
            self.struct.Data = word

        self.__dict__[name] = val


class TlsData(DataContainer):
    """Holds TLS information.

    struct:     IMAGE_TLS_DIRECTORY structure
    """


class BoundImportDescData(DataContainer):
    """Holds bound import descriptor data.

    This directory entry will provide information on the
    DLLs this PE file has been bound to (if bound at all).
    The structure will contain the name and timestamp of the
    DLL at the time of binding so that the loader can know
    whether it differs from the one currently present in the
    system and must, therefore, re-bind the PE's imports.

    struct:     IMAGE_BOUND_IMPORT_DESCRIPTOR structure
    name:       DLL name
    entries:    list of entries (BoundImportRefData instances)
                the entries will exist if this DLL has forwarded
                symbols. If so, the destination DLL will have an
                entry in this list.
    """


class LoadConfigData(DataContainer):
    """Holds Load Config data.

    struct:     IMAGE_LOAD_CONFIG_DIRECTORY structure
    name:       dll name
    dynamic_relocations: dynamic relocation information, if present
    """


class BoundImportRefData(DataContainer):
    """Holds bound import forwarder reference data.

    Contains the same information as the bound descriptor but
    for forwarded DLLs, if any.

    struct:     IMAGE_BOUND_FORWARDER_REF structure
    name:       dll name
    """


class ExceptionsDirEntryData(DataContainer):
    """Holds the data related to SEH (and stack unwinding, in particular)

    struct      an instance of RUNTIME_FUNTION
    unwindinfo  an instance of UNWIND_INFO
    """


class UnwindInfo(StructureWithBitfields):
    """Handles the complexities of UNWIND_INFO structure:
    * variable number of UWIND_CODEs
    * optional ExceptionHandler and FunctionEntry fields
    """

    def __init__(self, file_offset=0):
        super(UnwindInfo, self).__init__(
            (
                "UNWIND_INFO",
                (
                    "B:3,Version",
                    "B:5,Flags",
                    "B,SizeOfProlog",
                    "B,CountOfCodes",
                    "B:4,FrameRegister",
                    "B:4,FrameOffset",
                ),
            ),
            file_offset=file_offset,
        )
        self._full_size = super(UnwindInfo, self).sizeof()
        self._opt_field_name = None
        self._code_info = StructureWithBitfields(
            ("UNWIND_CODE", ("B,CodeOffset", "B:4,UnwindOp", "B:4,OpInfo")),
            file_offset=0,
        )
        self._chained_entry = None
        self._finished_unpacking = False

    def unpack_in_stages(self, data):
        """Unpacks the UNWIND_INFO "in two calls", with the first call establishing
        a full size of the structure and the second, performing the actual unpacking.
        """
        if self._finished_unpacking:
            return None

        super(UnwindInfo, self).__unpack__(data)
        codes_cnt_max = (self.CountOfCodes + 1) & ~1
        hdlr_offset = (
            super(UnwindInfo, self).sizeof() + codes_cnt_max * self._code_info.sizeof()
        )
        self._full_size = hdlr_offset + (
            0 if self.Flags == 0 else STRUCT_SIZEOF_TYPES["I"]
        )

        if len(data) < self._full_size:
            return None

        if self.Version != 1 and self.Version != 2:
            return "Unsupported version of UNWIND_INFO at " + hex(self.__file_offset__)

        self.UnwindCodes = []
        ro = super(UnwindInfo, self).sizeof()
        codes_left = self.CountOfCodes
        while codes_left > 0:
            self._code_info.__unpack__(data[ro : ro + self._code_info.sizeof()])
            ucode = PrologEpilogOpsFactory.create(self._code_info)
            if ucode is None:
                return "Unknown UNWIND_CODE at " + hex(self.__file_offset__ + ro)

            len_in_codes = ucode.length_in_code_structures(self._code_info, self)
            opc_size = self._code_info.sizeof() * len_in_codes
            ucode.initialize(
                self._code_info,
                data[ro : ro + opc_size],
                self,
                self.__file_offset__ + ro,
            )
            ro += opc_size
            codes_left -= len_in_codes
            self.UnwindCodes.append(ucode)

        if self.UNW_FLAG_EHANDLER or self.UNW_FLAG_UHANDLER:
            self._opt_field_name = "ExceptionHandler"

        if self.UNW_FLAG_CHAININFO:
            self._opt_field_name = "FunctionEntry"

        if self._opt_field_name != None:
            setattr(
                self,
                self._opt_field_name,
                struct.unpack(
                    "<I", data[hdlr_offset : hdlr_offset + STRUCT_SIZEOF_TYPES["I"]]
                )[0],
            )

        self._finished_unpacking = True

        return None

    def dump(self, indentation=0):
        # 022399.python.pefile.line1925.comment Because __keys_ext__ are shared among all the instances with the same
        # 022400.python.pefile.line1926.comment format string, we have to add and sunsequently remove the optional field
        # 022401.python.pefile.line1927.comment each time.
        # 022402.python.pefile.line1928.comment It saves space (as compared to keeping a copy self.__keys_ext__ per
        # 022403.python.pefile.line1929.comment UnwindInfo instance), but makes our dump() implementation thread-unsafe.
        if self._opt_field_name != None:
            self.__field_offsets__[self._opt_field_name] = (
                self._full_size - STRUCT_SIZEOF_TYPES["I"]
            )
            self.__keys_ext__.append([self._opt_field_name])
        try:
            dump = super(UnwindInfo, self).dump(indentation)
        finally:
            if self._opt_field_name != None:
                self.__keys_ext__.pop()

        dump.append(
            "Flags: "
            + ", ".join([s[0] for s in unwind_info_flags if getattr(self, s[0])])
        )
        dump.append(
            "Unwind codes: "
            + "; ".join([str(c) for c in self.UnwindCodes if c.is_valid()])
        )
        return dump

    def dump_dict(self):
        if self._opt_field_name != None:
            self.__field_offsets__[self._opt_field_name] = (
                self._full_size - STRUCT_SIZEOF_TYPES["I"]
            )
            self.__keys_ext__.append([self._opt_field_name])
        try:
            ret = super(UnwindInfo, self).dump_dict()
        finally:
            if self._opt_field_name != None:
                self.__keys_ext__.pop()
        return ret

    def __setattr__(self, name, val):
        if name == "Flags":
            set_flags(self, val, unwind_info_flags)
        elif "UNW_FLAG_" in name and hasattr(self, name):
            if val:
                self.__dict__["Flags"] |= UNWIND_INFO_FLAGS[name]
            else:
                self.__dict__["Flags"] ^= UNWIND_INFO_FLAGS[name]
        self.__dict__[name] = val

    def sizeof(self):
        return self._full_size

    def __pack__(self):
        data = bytearray(self._full_size)
        data[0 : super(UnwindInfo, self).sizeof()] = super(UnwindInfo, self).__pack__()
        cur_offset = super(UnwindInfo, self).sizeof()

        for uc in self.UnwindCodes:
            if cur_offset + uc.struct.sizeof() > self._full_size:
                break
            data[cur_offset : cur_offset + uc.struct.sizeof()] = uc.struct.__pack__()
            cur_offset += uc.struct.sizeof()

        if self._opt_field_name != None:
            data[
                self._full_size - STRUCT_SIZEOF_TYPES["I"] : self._full_size
            ] = struct.pack("<I", getattr(self, self._opt_field_name))

        return data

    def get_chained_function_entry(self):
        return self._chained_entry

    def set_chained_function_entry(self, entry):
        if self._chained_entry != None:
            raise PEFormatError("Chained function entry cannot be changed")
        self._chained_entry = entry


class PrologEpilogOp:
    """Meant as an abstract class representing a generic unwind code.
    There is a subclass of PrologEpilogOp for each member of UNWIND_OP_CODES enum.
    """

    def initialize(self, unw_code, data, unw_info, file_offset):
        self.struct = StructureWithBitfields(
            self._get_format(unw_code), file_offset=file_offset
        )
        self.struct.__unpack__(data)

    def length_in_code_structures(self, unw_code, unw_info):
        """Computes how many UNWIND_CODE structures UNWIND_CODE occupies.
        May be called before initialize() and, for that reason, should not rely on
        the values of intance attributes.
        """
        return 1

    def is_valid(self):
        return True

    def _get_format(self, unw_code):
        return ("UNWIND_CODE", ("B,CodeOffset", "B:4,UnwindOp", "B:4,OpInfo"))


class PrologEpilogOpPushReg(PrologEpilogOp):
    """UWOP_PUSH_NONVOL"""

    def _get_format(self, unw_code):
        return ("UNWIND_CODE_PUSH_NONVOL", ("B,CodeOffset", "B:4,UnwindOp", "B:4,Reg"))

    def __str__(self):
        return ".PUSHREG " + REGISTERS[self.struct.Reg]


class PrologEpilogOpAllocLarge(PrologEpilogOp):
    """UWOP_ALLOC_LARGE"""

    def _get_format(self, unw_code):
        return (
            "UNWIND_CODE_ALLOC_LARGE",
            (
                "B,CodeOffset",
                "B:4,UnwindOp",
                "B:4,OpInfo",
                "H,AllocSizeInQwords" if unw_code.OpInfo == 0 else "I,AllocSize",
            ),
        )

    def length_in_code_structures(self, unw_code, unw_info):
        return 2 if unw_code.OpInfo == 0 else 3

    def get_alloc_size(self):
        return (
            self.struct.AllocSizeInQwords * 8
            if self.struct.OpInfo == 0
            else self.struct.AllocSize
        )

    def __str__(self):
        return ".ALLOCSTACK " + hex(self.get_alloc_size())


class PrologEpilogOpAllocSmall(PrologEpilogOp):
    """UWOP_ALLOC_SMALL"""

    def _get_format(self, unw_code):
        return (
            "UNWIND_CODE_ALLOC_SMALL",
            ("B,CodeOffset", "B:4,UnwindOp", "B:4,AllocSizeInQwordsMinus8"),
        )

    def get_alloc_size(self):
        return self.struct.AllocSizeInQwordsMinus8 * 8 + 8

    def __str__(self):
        return ".ALLOCSTACK " + hex(self.get_alloc_size())


class PrologEpilogOpSetFP(PrologEpilogOp):
    """UWOP_SET_FPREG"""

    def initialize(self, unw_code, data, unw_info, file_offset):
        super(PrologEpilogOpSetFP, self).initialize(
            unw_code, data, unw_info, file_offset
        )
        self._frame_register = unw_info.FrameRegister
        self._frame_offset = unw_info.FrameOffset * 16

    def __str__(self):
        return (
            ".SETFRAME "
            + REGISTERS[self._frame_register]
            + ", "
            + hex(self._frame_offset)
        )


class PrologEpilogOpSaveReg(PrologEpilogOp):
    """UWOP_SAVE_NONVOL"""

    def length_in_code_structures(self, unwcode, unw_info):
        return 2

    def get_offset(self):
        return self.struct.OffsetInQwords * 8

    def _get_format(self, unw_code):
        return (
            "UNWIND_CODE_SAVE_NONVOL",
            ("B,CodeOffset", "B:4,UnwindOp", "B:4,Reg", "H,OffsetInQwords"),
        )

    def __str__(self):
        return ".SAVEREG " + REGISTERS[self.struct.Reg] + ", " + hex(self.get_offset())


class PrologEpilogOpSaveRegFar(PrologEpilogOp):
    """UWOP_SAVE_NONVOL_FAR"""

    def length_in_code_structures(self, unw_code, unw_info):
        return 3

    def get_offset(self):
        return self.struct.Offset

    def _get_format(self, unw_code):
        return (
            "UNWIND_CODE_SAVE_NONVOL_FAR",
            ("B,CodeOffset", "B:4,UnwindOp", "B:4,Reg", "I,Offset"),
        )

    def __str__(self):
        return ".SAVEREG " + REGISTERS[self.struct.Reg] + ", " + hex(self.struct.Offset)


class PrologEpilogOpSaveXMM(PrologEpilogOp):
    """UWOP_SAVE_XMM128"""

    def _get_format(self, unw_code):
        return (
            "UNWIND_CODE_SAVE_XMM128",
            ("B,CodeOffset", "B:4,UnwindOp", "B:4,Reg", "H,OffsetIn2Qwords"),
        )

    def length_in_code_structures(self, unw_code, unw_info):
        return 2

    def get_offset(self):
        return self.struct.OffsetIn2Qwords * 16

    def __str__(self):
        return ".SAVEXMM128 XMM" + str(self.struct.Reg) + ", " + hex(self.get_offset())


class PrologEpilogOpSaveXMMFar(PrologEpilogOp):
    """UWOP_SAVE_XMM128_FAR"""

    def _get_format(self, unw_code):
        return (
            "UNWIND_CODE_SAVE_XMM128_FAR",
            ("B,CodeOffset", "B:4,UnwindOp", "B:4,Reg", "I,Offset"),
        )

    def length_in_code_structures(self, unw_code, unw_info):
        return 3

    def get_offset(self):
        return self.struct.Offset

    def __str__(self):
        return ".SAVEXMM128 XMM" + str(self.struct.Reg) + ", " + hex(self.struct.Offset)


class PrologEpilogOpPushFrame(PrologEpilogOp):
    """UWOP_PUSH_MACHFRAME"""

    def __str__(self):
        return ".PUSHFRAME" + (" <code>" if self.struct.OpInfo else "")


class PrologEpilogOpEpilogMarker(PrologEpilogOp):
    """UWOP_EPILOG"""

    def initialize(self, unw_code, data, unw_info, file_offset):
        self._long_offst = True
        self._first = not hasattr(unw_info, "SizeOfEpilog")
        super(PrologEpilogOpEpilogMarker, self).initialize(
            unw_code, data, unw_info, file_offset
        )
        if self._first:
            setattr(unw_info, "SizeOfEpilog", self.struct.Size)
            self._long_offst = unw_code.OpInfo & 1 == 0
        self._epilog_size = unw_info.SizeOfEpilog

    def _get_format(self, unw_code):
        # 022404.python.pefile.line2200.comment check if it is the first epilog code among encountered; then its record
        # 022405.python.pefile.line2201.comment will contain size of the epilog
        if self._first:
            return (
                "UNWIND_CODE_EPILOG",
                ("B,OffsetLow,Size", "B:4,UnwindOp", "B:4,Flags")
                if unw_code.OpInfo & 1 == 1
                else (
                    "B,Size",
                    "B:4,UnwindOp",
                    "B:4,Flags",
                    "B,OffsetLow",
                    "B:4,Unused",
                    "B:4,OffsetHigh",
                ),
            )
        else:
            return (
                "UNWIND_CODE_EPILOG",
                ("B,OffsetLow", "B:4,UnwindOp", "B:4,OffsetHigh"),
            )

    def length_in_code_structures(self, unw_code, unw_info):
        return (
            2
            if not hasattr(unw_info, "SizeOfEpilog") and (unw_code.OpInfo & 1) == 0
            else 1
        )

    def get_offset(self):
        return self.struct.OffsetLow | (
            self.struct.OffsetHigh << 8 if self._long_offst else 0
        )

    def is_valid(self):
        return self.get_offset() > 0

    def __str__(self):
        # 022406.python.pefile.line2238.comment the EPILOG sequence may have a terminating all-zeros entry
        return (
            "EPILOG: size="
            + hex(self._epilog_size)
            + ", offset from the end=-"
            + hex(self.get_offset())
            if self.get_offset() > 0
            else ""
        )


class PrologEpilogOpsFactory:
    """A factory for creating unwind codes based on the value of UnwindOp"""

    _class_dict = {
        UWOP_PUSH_NONVOL: PrologEpilogOpPushReg,
        UWOP_ALLOC_LARGE: PrologEpilogOpAllocLarge,
        UWOP_ALLOC_SMALL: PrologEpilogOpAllocSmall,
        UWOP_SET_FPREG: PrologEpilogOpSetFP,
        UWOP_SAVE_NONVOL: PrologEpilogOpSaveReg,
        UWOP_SAVE_NONVOL_FAR: PrologEpilogOpSaveRegFar,
        UWOP_SAVE_XMM128: PrologEpilogOpSaveXMM,
        UWOP_SAVE_XMM128_FAR: PrologEpilogOpSaveXMMFar,
        UWOP_PUSH_MACHFRAME: PrologEpilogOpPushFrame,
        UWOP_EPILOG: PrologEpilogOpEpilogMarker,
    }

    @staticmethod
    def create(unwcode):
        code = unwcode.UnwindOp
        return (
            PrologEpilogOpsFactory._class_dict[code]()
            if code in PrologEpilogOpsFactory._class_dict
            else None
        )


# 022407.python.pefile.line2275.comment Valid FAT32 8.3 short filename characters according to:
# 022408.python.pefile.line2276.comment http://en.wikipedia.org/wiki/8.3_filename
# 022409.python.pefile.line2277.comment This will help decide whether DLL ASCII names are likely
# 022410.python.pefile.line2278.comment to be valid or otherwise corrupt data
# 022411.python.pefile.line2279.comment
# 022412.python.pefile.line2280.comment The filename length is not checked because the DLLs filename
# 022413.python.pefile.line2281.comment can be longer that the 8.3

allowed_filename = b(
    string.ascii_lowercase
    + string.ascii_uppercase
    + string.digits
    + "!#$%&'()-@^_`{}~+,.;=[]"
)


def is_valid_dos_filename(s):
    if s is None or not isinstance(s, (str, bytes, bytearray)):
        return False
    # 022414.python.pefile.line2294.comment Allow path separators as import names can contain directories.
    allowed = allowed_filename + b"\\/"
    return all(c in allowed for c in set(s))


# 022415.python.pefile.line2299.comment Check if an imported name uses the valid accepted characters expected in
# 022416.python.pefile.line2300.comment mangled function names. If the symbol's characters don't fall within this
# 022417.python.pefile.line2301.comment charset we will assume the name is invalid.
# 022418.python.pefile.line2302.comment The dot "." character comes from: https://github.com/erocarrera/pefile/pull/346
# 022419.python.pefile.line2303.comment All other symbols can be inserted by adding a name with that symbol to a .def file,
# 022420.python.pefile.line2304.comment and passing it to link.exe (See export_test.py)
allowed_function_name = b(
    string.ascii_lowercase + string.ascii_uppercase + string.digits
)


@lru_cache(maxsize=2048)
def is_valid_function_name(
    s: Union[str, bytes, bytearray], relax_allowed_characters: bool = False
) -> bool:
    allowed_extra = b"._?@$()<>"
    if relax_allowed_characters:
        allowed_extra = b"!\"#$%&'()*+,-./:<>?[\\]^_`{|}~@"
    return (
        s is not None
        and isinstance(s, (str, bytes, bytearray))
        and all((c in allowed_function_name or c in allowed_extra) for c in set(s))
    )


class PE:
    """A Portable Executable representation.

    This class provides access to most of the information in a PE file.

    It expects to be supplied the name of the file to load or PE data
    to process and an optional argument 'fast_load' (False by default)
    which controls whether to load all the directories information,
    which can be quite time consuming.

    pe = pefile.PE('module.dll')
    pe = pefile.PE(name='module.dll')

    would load 'module.dll' and process it. If the data is already
    available in a buffer the same can be achieved with:

    pe = pefile.PE(data=module_dll_data)

    The "fast_load" can be set to a default by setting its value in the
    module itself by means, for instance, of a "pefile.fast_load = True".
    That will make all the subsequent instances not to load the
    whole PE structure. The "full_load" method can be used to parse
    the missing data at a later stage.

    Basic headers information will be available in the attributes:

    DOS_HEADER
    NT_HEADERS
    FILE_HEADER
    OPTIONAL_HEADER

    All of them will contain among their attributes the members of the
    corresponding structures as defined in WINNT.H

    The raw data corresponding to the header (from the beginning of the
    file up to the start of the first section) will be available in the
    instance's attribute 'header' as a string.

    The sections will be available as a list in the 'sections' attribute.
    Each entry will contain as attributes all the structure's members.

    Directory entries will be available as attributes (if they exist):
    (no other entries are processed at this point)

    DIRECTORY_ENTRY_IMPORT (list of ImportDescData instances)
    DIRECTORY_ENTRY_EXPORT (ExportDirData instance)
    DIRECTORY_ENTRY_RESOURCE (ResourceDirData instance)
    DIRECTORY_ENTRY_DEBUG (list of DebugData instances)
    DIRECTORY_ENTRY_BASERELOC (list of BaseRelocationData instances)
    DIRECTORY_ENTRY_TLS
    DIRECTORY_ENTRY_BOUND_IMPORT (list of BoundImportData instances)

    The following dictionary attributes provide ways of mapping different
    constants. They will accept the numeric value and return the string
    representation and the opposite, feed in the string and get the
    numeric constant:

    DIRECTORY_ENTRY
    IMAGE_CHARACTERISTICS
    SECTION_CHARACTERISTICS
    DEBUG_TYPE
    SUBSYSTEM_TYPE
    MACHINE_TYPE
    RELOCATION_TYPE
    RESOURCE_TYPE
    LANG
    SUBLANG
    """

    # 022421.python.pefile.line2393.comment
    # 022422.python.pefile.line2394.comment Format specifications for PE structures.
    # 022423.python.pefile.line2395.comment

    __IMAGE_DOS_HEADER_format__ = (
        "IMAGE_DOS_HEADER",
        (
            "H,e_magic",
            "H,e_cblp",
            "H,e_cp",
            "H,e_crlc",
            "H,e_cparhdr",
            "H,e_minalloc",
            "H,e_maxalloc",
            "H,e_ss",
            "H,e_sp",
            "H,e_csum",
            "H,e_ip",
            "H,e_cs",
            "H,e_lfarlc",
            "H,e_ovno",
            "8s,e_res",
            "H,e_oemid",
            "H,e_oeminfo",
            "20s,e_res2",
            "I,e_lfanew",
        ),
    )

    __IMAGE_FILE_HEADER_format__ = (
        "IMAGE_FILE_HEADER",
        (
            "H,Machine",
            "H,NumberOfSections",
            "I,TimeDateStamp",
            "I,PointerToSymbolTable",
            "I,NumberOfSymbols",
            "H,SizeOfOptionalHeader",
            "H,Characteristics",
        ),
    )

    __IMAGE_DATA_DIRECTORY_format__ = (
        "IMAGE_DATA_DIRECTORY",
        ("I,VirtualAddress", "I,Size"),
    )

    __IMAGE_OPTIONAL_HEADER_format__ = (
        "IMAGE_OPTIONAL_HEADER",
        (
            "H,Magic",
            "B,MajorLinkerVersion",
            "B,MinorLinkerVersion",
            "I,SizeOfCode",
            "I,SizeOfInitializedData",
            "I,SizeOfUninitializedData",
            "I,AddressOfEntryPoint",
            "I,BaseOfCode",
            "I,BaseOfData",
            "I,ImageBase",
            "I,SectionAlignment",
            "I,FileAlignment",
            "H,MajorOperatingSystemVersion",
            "H,MinorOperatingSystemVersion",
            "H,MajorImageVersion",
            "H,MinorImageVersion",
            "H,MajorSubsystemVersion",
            "H,MinorSubsystemVersion",
            "I,Reserved1",
            "I,SizeOfImage",
            "I,SizeOfHeaders",
            "I,CheckSum",
            "H,Subsystem",
            "H,DllCharacteristics",
            "I,SizeOfStackReserve",
            "I,SizeOfStackCommit",
            "I,SizeOfHeapReserve",
            "I,SizeOfHeapCommit",
            "I,LoaderFlags",
            "I,NumberOfRvaAndSizes",
        ),
    )

    __IMAGE_OPTIONAL_HEADER64_format__ = (
        "IMAGE_OPTIONAL_HEADER64",
        (
            "H,Magic",
            "B,MajorLinkerVersion",
            "B,MinorLinkerVersion",
            "I,SizeOfCode",
            "I,SizeOfInitializedData",
            "I,SizeOfUninitializedData",
            "I,AddressOfEntryPoint",
            "I,BaseOfCode",
            "Q,ImageBase",
            "I,SectionAlignment",
            "I,FileAlignment",
            "H,MajorOperatingSystemVersion",
            "H,MinorOperatingSystemVersion",
            "H,MajorImageVersion",
            "H,MinorImageVersion",
            "H,MajorSubsystemVersion",
            "H,MinorSubsystemVersion",
            "I,Reserved1",
            "I,SizeOfImage",
            "I,SizeOfHeaders",
            "I,CheckSum",
            "H,Subsystem",
            "H,DllCharacteristics",
            "Q,SizeOfStackReserve",
            "Q,SizeOfStackCommit",
            "Q,SizeOfHeapReserve",
            "Q,SizeOfHeapCommit",
            "I,LoaderFlags",
            "I,NumberOfRvaAndSizes",
        ),
    )

    __IMAGE_NT_HEADERS_format__ = ("IMAGE_NT_HEADERS", ("I,Signature",))

    __IMAGE_SECTION_HEADER_format__ = (
        "IMAGE_SECTION_HEADER",
        (
            "8s,Name",
            "I,Misc,Misc_PhysicalAddress,Misc_VirtualSize",
            "I,VirtualAddress",
            "I,SizeOfRawData",
            "I,PointerToRawData",
            "I,PointerToRelocations",
            "I,PointerToLinenumbers",
            "H,NumberOfRelocations",
            "H,NumberOfLinenumbers",
            "I,Characteristics",
        ),
    )

    __IMAGE_DELAY_IMPORT_DESCRIPTOR_format__ = (
        "IMAGE_DELAY_IMPORT_DESCRIPTOR",
        (
            "I,grAttrs",
            "I,szName",
            "I,phmod",
            "I,pIAT",
            "I,pINT",
            "I,pBoundIAT",
            "I,pUnloadIAT",
            "I,dwTimeStamp",
        ),
    )

    __IMAGE_IMPORT_DESCRIPTOR_format__ = (
        "IMAGE_IMPORT_DESCRIPTOR",
        (
            "I,OriginalFirstThunk,Characteristics",
            "I,TimeDateStamp",
            "I,ForwarderChain",
            "I,Name",
            "I,FirstThunk",
        ),
    )

    __IMAGE_EXPORT_DIRECTORY_format__ = (
        "IMAGE_EXPORT_DIRECTORY",
        (
            "I,Characteristics",
            "I,TimeDateStamp",
            "H,MajorVersion",
            "H,MinorVersion",
            "I,Name",
            "I,Base",
            "I,NumberOfFunctions",
            "I,NumberOfNames",
            "I,AddressOfFunctions",
            "I,AddressOfNames",
            "I,AddressOfNameOrdinals",
        ),
    )

    __IMAGE_RESOURCE_DIRECTORY_format__ = (
        "IMAGE_RESOURCE_DIRECTORY",
        (
            "I,Characteristics",
            "I,TimeDateStamp",
            "H,MajorVersion",
            "H,MinorVersion",
            "H,NumberOfNamedEntries",
            "H,NumberOfIdEntries",
        ),
    )

    __IMAGE_RESOURCE_DIRECTORY_ENTRY_format__ = (
        "IMAGE_RESOURCE_DIRECTORY_ENTRY",
        ("I,Name", "I,OffsetToData"),
    )

    __IMAGE_RESOURCE_DATA_ENTRY_format__ = (
        "IMAGE_RESOURCE_DATA_ENTRY",
        ("I,OffsetToData", "I,Size", "I,CodePage", "I,Reserved"),
    )

    __VS_VERSIONINFO_format__ = (
        "VS_VERSIONINFO",
        ("H,Length", "H,ValueLength", "H,Type"),
    )

    __VS_FIXEDFILEINFO_format__ = (
        "VS_FIXEDFILEINFO",
        (
            "I,Signature",
            "I,StrucVersion",
            "I,FileVersionMS",
            "I,FileVersionLS",
            "I,ProductVersionMS",
            "I,ProductVersionLS",
            "I,FileFlagsMask",
            "I,FileFlags",
            "I,FileOS",
            "I,FileType",
            "I,FileSubtype",
            "I,FileDateMS",
            "I,FileDateLS",
        ),
    )

    __StringFileInfo_format__ = (
        "StringFileInfo",
        ("H,Length", "H,ValueLength", "H,Type"),
    )

    __StringTable_format__ = ("StringTable", ("H,Length", "H,ValueLength", "H,Type"))

    __String_format__ = ("String", ("H,Length", "H,ValueLength", "H,Type"))

    __Var_format__ = ("Var", ("H,Length", "H,ValueLength", "H,Type"))

    __IMAGE_THUNK_DATA_format__ = (
        "IMAGE_THUNK_DATA",
        ("I,ForwarderString,Function,Ordinal,AddressOfData",),
    )

    __IMAGE_THUNK_DATA64_format__ = (
        "IMAGE_THUNK_DATA",
        ("Q,ForwarderString,Function,Ordinal,AddressOfData",),
    )

    __IMAGE_DEBUG_DIRECTORY_format__ = (
        "IMAGE_DEBUG_DIRECTORY",
        (
            "I,Characteristics",
            "I,TimeDateStamp",
            "H,MajorVersion",
            "H,MinorVersion",
            "I,Type",
            "I,SizeOfData",
            "I,AddressOfRawData",
            "I,PointerToRawData",
        ),
    )

    __IMAGE_BASE_RELOCATION_format__ = (
        "IMAGE_BASE_RELOCATION",
        ("I,VirtualAddress", "I,SizeOfBlock"),
    )

    __IMAGE_BASE_RELOCATION_ENTRY_format__ = (
        "IMAGE_BASE_RELOCATION_ENTRY",
        ("H,Data",),
    )

    __IMAGE_IMPORT_CONTROL_TRANSFER_DYNAMIC_RELOCATION_format__ = (
        "IMAGE_IMPORT_CONTROL_TRANSFER_DYNAMIC_RELOCATION",
        ("I:12,PageRelativeOffset", "I:1,IndirectCall", "I:19,IATIndex"),
    )

    __IMAGE_INDIR_CONTROL_TRANSFER_DYNAMIC_RELOCATION_format__ = (
        "IMAGE_INDIR_CONTROL_TRANSFER_DYNAMIC_RELOCATION",
        (
            "I:12,PageRelativeOffset",
            "I:1,IndirectCall",
            "I:1,RexWPrefix",
            "I:1,CfgCheck",
            "I:1,Reserved",
        ),
    )

    __IMAGE_SWITCHTABLE_BRANCH_DYNAMIC_RELOCATION_format__ = (
        "IMAGE_SWITCHTABLE_BRANCH_DYNAMIC_RELOCATION",
        ("I:12,PageRelativeOffset", "I:4,RegisterNumber"),
    )

    __IMAGE_TLS_DIRECTORY_format__ = (
        "IMAGE_TLS_DIRECTORY",
        (
            "I,StartAddressOfRawData",
            "I,EndAddressOfRawData",
            "I,AddressOfIndex",
            "I,AddressOfCallBacks",
            "I,SizeOfZeroFill",
            "I,Characteristics",
        ),
    )

    __IMAGE_TLS_DIRECTORY64_format__ = (
        "IMAGE_TLS_DIRECTORY",
        (
            "Q,StartAddressOfRawData",
            "Q,EndAddressOfRawData",
            "Q,AddressOfIndex",
            "Q,AddressOfCallBacks",
            "I,SizeOfZeroFill",
            "I,Characteristics",
        ),
    )

    __IMAGE_LOAD_CONFIG_DIRECTORY_format__ = (
        "IMAGE_LOAD_CONFIG_DIRECTORY",
        (
            "I,Size",
            "I,TimeDateStamp",
            "H,MajorVersion",
            "H,MinorVersion",
            "I,GlobalFlagsClear",
            "I,GlobalFlagsSet",
            "I,CriticalSectionDefaultTimeout",
            "I,DeCommitFreeBlockThreshold",
            "I,DeCommitTotalFreeThreshold",
            "I,LockPrefixTable",
            "I,MaximumAllocationSize",
            "I,VirtualMemoryThreshold",
            "I,ProcessHeapFlags",
            "I,ProcessAffinityMask",
            "H,CSDVersion",
            "H,Reserved1",
            "I,EditList",
            "I,SecurityCookie",
            "I,SEHandlerTable",
            "I,SEHandlerCount",
            "I,GuardCFCheckFunctionPointer",
            "I,GuardCFDispatchFunctionPointer",
            "I,GuardCFFunctionTable",
            "I,GuardCFFunctionCount",
            "I,GuardFlags",
            "H,CodeIntegrityFlags",
            "H,CodeIntegrityCatalog",
            "I,CodeIntegrityCatalogOffset",
            "I,CodeIntegrityReserved",
            "I,GuardAddressTakenIatEntryTable",
            "I,GuardAddressTakenIatEntryCount",
            "I,GuardLongJumpTargetTable",
            "I,GuardLongJumpTargetCount",
            "I,DynamicValueRelocTable",
            "I,CHPEMetadataPointer",
            "I,GuardRFFailureRoutine",
            "I,GuardRFFailureRoutineFunctionPointer",
            "I,DynamicValueRelocTableOffset",
            "H,DynamicValueRelocTableSection",
            "H,Reserved2",
            "I,GuardRFVerifyStackPointerFunctionPointer" "I,HotPatchTableOffset",
            "I,Reserved3",
            "I,EnclaveConfigurationPointer",
        ),
    )

    __IMAGE_LOAD_CONFIG_DIRECTORY64_format__ = (
        "IMAGE_LOAD_CONFIG_DIRECTORY",
        (
            "I,Size",
            "I,TimeDateStamp",
            "H,MajorVersion",
            "H,MinorVersion",
            "I,GlobalFlagsClear",
            "I,GlobalFlagsSet",
            "I,CriticalSectionDefaultTimeout",
            "Q,DeCommitFreeBlockThreshold",
            "Q,DeCommitTotalFreeThreshold",
            "Q,LockPrefixTable",
            "Q,MaximumAllocationSize",
            "Q,VirtualMemoryThreshold",
            "Q,ProcessAffinityMask",
            "I,ProcessHeapFlags",
            "H,CSDVersion",
            "H,Reserved1",
            "Q,EditList",
            "Q,SecurityCookie",
            "Q,SEHandlerTable",
            "Q,SEHandlerCount",
            "Q,GuardCFCheckFunctionPointer",
            "Q,GuardCFDispatchFunctionPointer",
            "Q,GuardCFFunctionTable",
            "Q,GuardCFFunctionCount",
            "I,GuardFlags",
            "H,CodeIntegrityFlags",
            "H,CodeIntegrityCatalog",
            "I,CodeIntegrityCatalogOffset",
            "I,CodeIntegrityReserved",
            "Q,GuardAddressTakenIatEntryTable",
            "Q,GuardAddressTakenIatEntryCount",
            "Q,GuardLongJumpTargetTable",
            "Q,GuardLongJumpTargetCount",
            "Q,DynamicValueRelocTable",
            "Q,CHPEMetadataPointer",
            "Q,GuardRFFailureRoutine",
            "Q,GuardRFFailureRoutineFunctionPointer",
            "I,DynamicValueRelocTableOffset",
            "H,DynamicValueRelocTableSection",
            "H,Reserved2",
            "Q,GuardRFVerifyStackPointerFunctionPointer",
            "I,HotPatchTableOffset",
            "I,Reserved3",
            "Q,EnclaveConfigurationPointer",
        ),
    )

    __IMAGE_DYNAMIC_RELOCATION_TABLE_format__ = (
        "IMAGE_DYNAMIC_RELOCATION_TABLE",
        ("I,Version", "I,Size"),
    )

    __IMAGE_DYNAMIC_RELOCATION_format__ = (
        "IMAGE_DYNAMIC_RELOCATION",
        ("I,Symbol", "I,BaseRelocSize"),
    )

    __IMAGE_DYNAMIC_RELOCATION64_format__ = (
        "IMAGE_DYNAMIC_RELOCATION64",
        ("Q,Symbol", "I,BaseRelocSize"),
    )

    __IMAGE_DYNAMIC_RELOCATION_V2_format__ = (
        "IMAGE_DYNAMIC_RELOCATION_V2",
        ("I,HeaderSize", "I,FixupInfoSize", "I,Symbol", "I,SymbolGroup", "I,Flags"),
    )

    __IMAGE_DYNAMIC_RELOCATION64_V2_format__ = (
        "IMAGE_DYNAMIC_RELOCATION64_V2",
        ("I,HeaderSize", "I,FixupInfoSize", "Q,Symbol", "I,SymbolGroup", "I,Flags"),
    )

    __IMAGE_BOUND_IMPORT_DESCRIPTOR_format__ = (
        "IMAGE_BOUND_IMPORT_DESCRIPTOR",
        ("I,TimeDateStamp", "H,OffsetModuleName", "H,NumberOfModuleForwarderRefs"),
    )

    __IMAGE_BOUND_FORWARDER_REF_format__ = (
        "IMAGE_BOUND_FORWARDER_REF",
        ("I,TimeDateStamp", "H,OffsetModuleName", "H,Reserved"),
    )

    __RUNTIME_FUNCTION_format__ = (
        "RUNTIME_FUNCTION",
        ("I,BeginAddress", "I,EndAddress", "I,UnwindData"),
    )

    def __init__(
        self,
        name=None,
        data=None,
        fast_load=None,
        max_symbol_exports=MAX_SYMBOL_EXPORT_COUNT,
        max_repeated_symbol=120,
    ):

        self.max_symbol_exports = max_symbol_exports
        self.max_repeated_symbol = max_repeated_symbol

        self._get_section_by_rva_last_used = None

        self.sections = []

        self.__warnings = []

        self.PE_TYPE = None

        if name is None and data is None:
            raise ValueError("Must supply either name or data")

        # 022424.python.pefile.line2869.comment This list will keep track of all the structures created.
        # 022425.python.pefile.line2870.comment That will allow for an easy iteration through the list
        # 022426.python.pefile.line2871.comment in order to save the modifications made
        self.__structures__ = []
        self.__from_file = None

        # 022427.python.pefile.line2875.comment We only want to print these warnings once
        self.FileAlignment_Warning = False
        self.SectionAlignment_Warning = False

        # 022428.python.pefile.line2879.comment Count of total resource entries across nested tables
        self.__total_resource_entries_count = 0
        # 022429.python.pefile.line2881.comment Sum of the size of all resource entries parsed, which should not
        # 022430.python.pefile.line2882.comment exceed the file size.
        self.__total_resource_bytes = 0
        # 022431.python.pefile.line2884.comment The number of imports parsed in this file
        self.__total_import_symbols = 0

        self.dynamic_relocation_format_by_symbol = {
            3: PE.__IMAGE_IMPORT_CONTROL_TRANSFER_DYNAMIC_RELOCATION_format__,
            4: PE.__IMAGE_INDIR_CONTROL_TRANSFER_DYNAMIC_RELOCATION_format__,
            5: PE.__IMAGE_SWITCHTABLE_BRANCH_DYNAMIC_RELOCATION_format__,
        }

        fast_load = fast_load if fast_load is not None else globals()["fast_load"]
        try:
            self.__parse__(name, data, fast_load)
        except:
            self.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        if (
            self.__from_file is True
            and hasattr(self, "__data__")
            and (
                (isinstance(mmap.mmap, type) and isinstance(self.__data__, mmap.mmap))
                or "mmap.mmap" in repr(type(self.__data__))
            )
        ):
            self.__data__.close()
            del self.__data__

    def __unpack_data__(self, format, data, file_offset):
        """Apply structure format to raw data.

        Returns an unpacked structure object if successful, None otherwise.
        """

        structure = Structure(format, file_offset=file_offset)

        try:
            structure.__unpack__(data)
        except PEFormatError as err:
            self.__warnings.append(
                'Corrupt header "{0}" at file offset {1}. Exception: {2}'.format(
                    format[0], file_offset, err
                )
            )
            return None

        self.__structures__.append(structure)

        return structure

    def __unpack_data_with_bitfields__(self, format, data, file_offset):
        """Apply structure format to raw data.

        Returns an unpacked structure object if successful, None otherwise.
        """

        structure = StructureWithBitfields(format, file_offset=file_offset)

        try:
            structure.__unpack__(data)
        except PEFormatError as err:
            self.__warnings.append(
                'Corrupt header "{0}" at file offset {1}. Exception: {2}'.format(
                    format[0], file_offset, err
                )
            )
            return None

        self.__structures__.append(structure)

        return structure

    def __parse__(self, fname, data, fast_load):
        """Parse a Portable Executable file.

        Loads a PE file, parsing all its structures and making them available
        through the instance's attributes.
        """

        if fname is not None:
            stat = os.stat(fname)
            if stat.st_size == 0:
                raise PEFormatError("The file is empty")
            fd = None
            try:
                fd = open(fname, "rb")
                self.fileno = fd.fileno()
                if hasattr(mmap, "MAP_PRIVATE"):
                    # 022432.python.pefile.line2978.comment Unix
                    self.__data__ = mmap.mmap(self.fileno, 0, mmap.MAP_PRIVATE)
                else:
                    # 022433.python.pefile.line2981.comment Windows
                    self.__data__ = mmap.mmap(self.fileno, 0, access=mmap.ACCESS_READ)
                self.__from_file = True
            except IOError as excp:
                exception_msg = "{0}".format(excp)
                exception_msg = exception_msg and (": %s" % exception_msg)
                raise Exception(
                    "Unable to access file '{0}'{1}".format(fname, exception_msg)
                )
            finally:
                if fd is not None:
                    fd.close()
        elif data is not None:
            self.__data__ = data
            self.__from_file = False

        # 022434.python.pefile.line2997.comment Resources should not overlap each other, so they should not exceed the
        # 022435.python.pefile.line2998.comment file size.
        self.__resource_size_limit_upperbounds = len(self.__data__)
        self.__resource_size_limit_reached = False

        if not fast_load:
            for byte, byte_count in Counter(bytearray(self.__data__)).items():
                # 022436.python.pefile.line3004.comment Only report the cases where a byte makes up for more than 50% (if
                # 022437.python.pefile.line3005.comment zero) or 15% (if non-zero) of the file's contents. There are
                # 022438.python.pefile.line3006.comment legitimate PEs where 0x00 bytes are close to 50% of the whole
                # 022439.python.pefile.line3007.comment file's contents.
                if (byte == 0 and byte_count / len(self.__data__) > 0.5) or (
                    byte != 0 and byte_count / len(self.__data__) > 0.15
                ):
                    self.__warnings.append(
                        (
                            "Byte 0x{0:02x} makes up {1:.4f}% of the file's contents."
                            " This may indicate truncation / malformation."
                        ).format(byte, 100.0 * byte_count / len(self.__data__))
                    )

        dos_header_data = self.__data__[:64]
        if len(dos_header_data) != 64:
            raise PEFormatError(
                "Unable to read the DOS Header, possibly a truncated file."
            )

        self.DOS_HEADER = self.__unpack_data__(
            self.__IMAGE_DOS_HEADER_format__, dos_header_data, file_offset=0
        )

        if self.DOS_HEADER.e_magic == IMAGE_DOSZM_SIGNATURE:
            raise PEFormatError("Probably a ZM Executable (not a PE file).")
        if not self.DOS_HEADER or self.DOS_HEADER.e_magic != IMAGE_DOS_SIGNATURE:
            raise PEFormatError("DOS Header magic not found.")

        # 022440.python.pefile.line3033.comment OC Patch:
        # 022441.python.pefile.line3034.comment Check for sane value in e_lfanew
        # 022442.python.pefile.line3035.comment
        if self.DOS_HEADER.e_lfanew > len(self.__data__):
            raise PEFormatError("Invalid e_lfanew value, probably not a PE file")

        nt_headers_offset = self.DOS_HEADER.e_lfanew

        self.NT_HEADERS = self.__unpack_data__(
            self.__IMAGE_NT_HEADERS_format__,
            self.__data__[nt_headers_offset : nt_headers_offset + 8],
            file_offset=nt_headers_offset,
        )

        # 022443.python.pefile.line3047.comment We better check the signature right here, before the file screws
        # 022444.python.pefile.line3048.comment around with sections:
        # 022445.python.pefile.line3049.comment OC Patch:
        # 022446.python.pefile.line3050.comment Some malware will cause the Signature value to not exist at all
        if not self.NT_HEADERS or not self.NT_HEADERS.Signature:
            raise PEFormatError("NT Headers not found.")

        if (0xFFFF & self.NT_HEADERS.Signature) == IMAGE_NE_SIGNATURE:
            raise PEFormatError("Invalid NT Headers signature. Probably a NE file")
        if (0xFFFF & self.NT_HEADERS.Signature) == IMAGE_LE_SIGNATURE:
            raise PEFormatError("Invalid NT Headers signature. Probably a LE file")
        if (0xFFFF & self.NT_HEADERS.Signature) == IMAGE_LX_SIGNATURE:
            raise PEFormatError("Invalid NT Headers signature. Probably a LX file")
        if (0xFFFF & self.NT_HEADERS.Signature) == IMAGE_TE_SIGNATURE:
            raise PEFormatError("Invalid NT Headers signature. Probably a TE file")
        if self.NT_HEADERS.Signature != IMAGE_NT_SIGNATURE:
            raise PEFormatError("Invalid NT Headers signature.")

        self.FILE_HEADER = self.__unpack_data__(
            self.__IMAGE_FILE_HEADER_format__,
            self.__data__[nt_headers_offset + 4 : nt_headers_offset + 4 + 32],
            file_offset=nt_headers_offset + 4,
        )
        image_flags = retrieve_flags(IMAGE_CHARACTERISTICS, "IMAGE_FILE_")

        if not self.FILE_HEADER:
            raise PEFormatError("File Header missing")

        # 022447.python.pefile.line3075.comment Set the image's flags according the the Characteristics member
        set_flags(self.FILE_HEADER, self.FILE_HEADER.Characteristics, image_flags)

        optional_header_offset = nt_headers_offset + 4 + self.FILE_HEADER.sizeof()

        # 022448.python.pefile.line3080.comment Note: location of sections can be controlled from PE header:
        sections_offset = optional_header_offset + self.FILE_HEADER.SizeOfOptionalHeader

        self.OPTIONAL_HEADER = self.__unpack_data__(
            self.__IMAGE_OPTIONAL_HEADER_format__,
            # 022449.python.pefile.line3085.comment Read up to 256 bytes to allow creating a copy of too much data
            self.__data__[optional_header_offset : optional_header_offset + 256],
            file_offset=optional_header_offset,
        )

        # 022450.python.pefile.line3090.comment According to solardesigner's findings for his
        # 022451.python.pefile.line3091.comment Tiny PE project, the optional header does not
        # 022452.python.pefile.line3092.comment need fields beyond "Subsystem" in order to be
        # 022453.python.pefile.line3093.comment loadable by the Windows loader (given that zeros
        # 022454.python.pefile.line3094.comment are acceptable values and the header is loaded
        # 022455.python.pefile.line3095.comment in a zeroed memory page)
        # 022456.python.pefile.line3096.comment If trying to parse a full Optional Header fails
        # 022457.python.pefile.line3097.comment we try to parse it again with some 0 padding
        # 022458.python.pefile.line3098.comment
        MINIMUM_VALID_OPTIONAL_HEADER_RAW_SIZE = 69

        if (
            self.OPTIONAL_HEADER is None
            and len(
                self.__data__[optional_header_offset : optional_header_offset + 0x200]
            )
            >= MINIMUM_VALID_OPTIONAL_HEADER_RAW_SIZE
        ):

            # 022459.python.pefile.line3109.comment Add enough zeros to make up for the unused fields
            # 022460.python.pefile.line3110.comment
            padding_length = 128

            # 022461.python.pefile.line3113.comment Create padding
            # 022462.python.pefile.line3114.comment
            padded_data = self.__data__[
                optional_header_offset : optional_header_offset + 0x200
            ] + (b"\0" * padding_length)

            self.OPTIONAL_HEADER = self.__unpack_data__(
                self.__IMAGE_OPTIONAL_HEADER_format__,
                padded_data,
                file_offset=optional_header_offset,
            )

        # 022463.python.pefile.line3125.comment Check the Magic in the OPTIONAL_HEADER and set the PE file
        # 022464.python.pefile.line3126.comment type accordingly
        # 022465.python.pefile.line3127.comment
        if self.OPTIONAL_HEADER is not None:

            if self.OPTIONAL_HEADER.Magic == OPTIONAL_HEADER_MAGIC_PE:

                self.PE_TYPE = OPTIONAL_HEADER_MAGIC_PE

            elif self.OPTIONAL_HEADER.Magic == OPTIONAL_HEADER_MAGIC_PE_PLUS:

                self.PE_TYPE = OPTIONAL_HEADER_MAGIC_PE_PLUS

                self.OPTIONAL_HEADER = self.__unpack_data__(
                    self.__IMAGE_OPTIONAL_HEADER64_format__,
                    self.__data__[
                        optional_header_offset : optional_header_offset + 0x200
                    ],
                    file_offset=optional_header_offset,
                )

                # 022466.python.pefile.line3146.comment Again, as explained above, we try to parse
                # 022467.python.pefile.line3147.comment a reduced form of the Optional Header which
                # 022468.python.pefile.line3148.comment is still valid despite not including all
                # 022469.python.pefile.line3149.comment structure members
                # 022470.python.pefile.line3150.comment
                MINIMUM_VALID_OPTIONAL_HEADER_RAW_SIZE = 69 + 4

                if (
                    self.OPTIONAL_HEADER is None
                    and len(
                        self.__data__[
                            optional_header_offset : optional_header_offset + 0x200
                        ]
                    )
                    >= MINIMUM_VALID_OPTIONAL_HEADER_RAW_SIZE
                ):

                    padding_length = 128
                    padded_data = self.__data__[
                        optional_header_offset : optional_header_offset + 0x200
                    ] + (b"\0" * padding_length)
                    self.OPTIONAL_HEADER = self.__unpack_data__(
                        self.__IMAGE_OPTIONAL_HEADER64_format__,
                        padded_data,
                        file_offset=optional_header_offset,
                    )

        if not self.FILE_HEADER:
            raise PEFormatError("File Header missing")

        # 022471.python.pefile.line3176.comment OC Patch:
        # 022472.python.pefile.line3177.comment Die gracefully if there is no OPTIONAL_HEADER field
        # 022473.python.pefile.line3178.comment 975440f5ad5e2e4a92c4d9a5f22f75c1
        if self.OPTIONAL_HEADER is None:
            raise PEFormatError("No Optional Header found, invalid PE32 or PE32+ file.")
        if self.PE_TYPE is None:
            self.__warnings.append(
                "Invalid type 0x{0:04x} in Optional Header.".format(
                    self.OPTIONAL_HEADER.Magic
                )
            )

        dll_characteristics_flags = retrieve_flags(
            DLL_CHARACTERISTICS, "IMAGE_DLLCHARACTERISTICS_"
        )

        # 022474.python.pefile.line3192.comment Set the Dll Characteristics flags according the the DllCharacteristics member
        set_flags(
            self.OPTIONAL_HEADER,
            self.OPTIONAL_HEADER.DllCharacteristics,
            dll_characteristics_flags,
        )

        self.OPTIONAL_HEADER.DATA_DIRECTORY = []
        # 022475.python.pefile.line3200.comment offset = (optional_header_offset + self.FILE_HEADER.SizeOfOptionalHeader)
        offset = optional_header_offset + self.OPTIONAL_HEADER.sizeof()

        self.NT_HEADERS.FILE_HEADER = self.FILE_HEADER
        self.NT_HEADERS.OPTIONAL_HEADER = self.OPTIONAL_HEADER

        # 022476.python.pefile.line3206.comment Windows 8 specific check
        # 022477.python.pefile.line3207.comment
        if (
            self.OPTIONAL_HEADER.AddressOfEntryPoint
            < self.OPTIONAL_HEADER.SizeOfHeaders
        ):
            self.__warnings.append(
                "SizeOfHeaders is smaller than AddressOfEntryPoint: this file "
                "cannot run under Windows 8."
            )

        # 022478.python.pefile.line3217.comment The NumberOfRvaAndSizes is sanitized to stay within
        # 022479.python.pefile.line3218.comment reasonable limits so can be casted to an int
        # 022480.python.pefile.line3219.comment
        if self.OPTIONAL_HEADER.NumberOfRvaAndSizes > 0x10:
            self.__warnings.append(
                "Suspicious NumberOfRvaAndSizes in the Optional Header. "
                "Normal values are never larger than 0x10, the value is: 0x%x"
                % self.OPTIONAL_HEADER.NumberOfRvaAndSizes
            )

        MAX_ASSUMED_VALID_NUMBER_OF_RVA_AND_SIZES = 0x100
        for i in range(int(0x7FFFFFFF & self.OPTIONAL_HEADER.NumberOfRvaAndSizes)):

            if len(self.__data__) - offset == 0:
                break

            if len(self.__data__) - offset < 8:
                data = self.__data__[offset:] + b"\0" * 8
            else:
                data = self.__data__[
                    offset : offset + MAX_ASSUMED_VALID_NUMBER_OF_RVA_AND_SIZES
                ]

            dir_entry = self.__unpack_data__(
                self.__IMAGE_DATA_DIRECTORY_format__, data, file_offset=offset
            )

            if dir_entry is None:
                break

            # 022481.python.pefile.line3247.comment Would fail if missing an entry
            # 022482.python.pefile.line3248.comment 1d4937b2fa4d84ad1bce0309857e70ca offending sample
            try:
                dir_entry.name = DIRECTORY_ENTRY[i]
            except (KeyError, AttributeError):
                break

            offset += dir_entry.sizeof()

            self.OPTIONAL_HEADER.DATA_DIRECTORY.append(dir_entry)

            # 022483.python.pefile.line3258.comment If the offset goes outside the optional header,
            # 022484.python.pefile.line3259.comment the loop is broken, regardless of how many directories
            # 022485.python.pefile.line3260.comment NumberOfRvaAndSizes says there are
            # 022486.python.pefile.line3261.comment
            # 022487.python.pefile.line3262.comment We assume a normally sized optional header, hence that we do
            # 022488.python.pefile.line3263.comment a sizeof() instead of reading SizeOfOptionalHeader.
            # 022489.python.pefile.line3264.comment Then we add a default number of directories times their size,
            # 022490.python.pefile.line3265.comment if we go beyond that, we assume the number of directories
            # 022491.python.pefile.line3266.comment is wrong and stop processing
            if offset >= (
                optional_header_offset + self.OPTIONAL_HEADER.sizeof() + 8 * 16
            ):

                break

        offset = self.parse_sections(sections_offset)

        # 022492.python.pefile.line3275.comment OC Patch:
        # 022493.python.pefile.line3276.comment There could be a problem if there are no raw data sections
        # 022494.python.pefile.line3277.comment greater than 0
        # 022495.python.pefile.line3278.comment fc91013eb72529da005110a3403541b6 example
        # 022496.python.pefile.line3279.comment Should this throw an exception in the minimum header offset
        # 022497.python.pefile.line3280.comment can't be found?
        # 022498.python.pefile.line3281.comment
        rawDataPointers = [
            self.adjust_FileAlignment(
                s.PointerToRawData, self.OPTIONAL_HEADER.FileAlignment
            )
            for s in self.sections
            if s.PointerToRawData > 0
        ]

        if len(rawDataPointers) > 0:
            lowest_section_offset = min(rawDataPointers)
        else:
            lowest_section_offset = None

        if not lowest_section_offset or lowest_section_offset < offset:
            self.header = self.__data__[:offset]
        else:
            self.header = self.__data__[:lowest_section_offset]

        # 022499.python.pefile.line3300.comment Check whether the entry point lies within a section
        # 022500.python.pefile.line3301.comment
        if (
            self.get_section_by_rva(self.OPTIONAL_HEADER.AddressOfEntryPoint)
            is not None
        ):

            # 022501.python.pefile.line3307.comment Check whether the entry point lies within the file
            # 022502.python.pefile.line3308.comment
            ep_offset = self.get_offset_from_rva(
                self.OPTIONAL_HEADER.AddressOfEntryPoint
            )
            if ep_offset > len(self.__data__):

                self.__warnings.append(
                    "Possibly corrupt file. AddressOfEntryPoint lies outside the"
                    " file. AddressOfEntryPoint: 0x%x"
                    % self.OPTIONAL_HEADER.AddressOfEntryPoint
                )

        else:

            self.__warnings.append(
                "AddressOfEntryPoint lies outside the sections' boundaries. "
                "AddressOfEntryPoint: 0x%x" % self.OPTIONAL_HEADER.AddressOfEntryPoint
            )

        if not fast_load:
            self.full_load()

    def parse_rich_header(self):
        """Parses the rich header
        see http://www.ntcore.com/files/richsign.htm for more information

        Structure:
        00 DanS ^ checksum, checksum, checksum, checksum
        10 Symbol RVA ^ checksum, Symbol size ^ checksum...
        ...
        XX Rich, checksum, 0, 0,...
        """

        # 022503.python.pefile.line3341.comment Rich Header constants
        # 022504.python.pefile.line3342.comment
        DANS = 0x536E6144  # 'DanS' as dword
        RICH = 0x68636952  # 'Rich' as dword

        rich_index = self.__data__.find(
            b"Rich", 0x80, self.OPTIONAL_HEADER.get_file_offset()
        )
        if rich_index == -1:
            return None

        # 022507.python.pefile.line3352.comment Read a block of data
        try:
            # 022508.python.pefile.line3354.comment The end of the structure is 8 bytes after the start of the Rich
            # 022509.python.pefile.line3355.comment string.
            rich_data = self.__data__[0x80 : rich_index + 8]
            # 022510.python.pefile.line3357.comment Make the data have length a multiple of 4, otherwise the
            # 022511.python.pefile.line3358.comment subsequent parsing will fail. It's not impossible that we retrieve
            # 022512.python.pefile.line3359.comment truncated data that it's not a multiple.
            rich_data = rich_data[: 4 * int(len(rich_data) / 4)]
            data = list(
                struct.unpack("<{0}I".format(int(len(rich_data) / 4)), rich_data)
            )
            if RICH not in data:
                return None
        except PEFormatError:
            return None

        # 022513.python.pefile.line3369.comment get key, raw_data and clear_data
        key = struct.pack("<L", data[data.index(RICH) + 1])
        result = {"key": key}

        raw_data = rich_data[: rich_data.find(b"Rich")]
        result["raw_data"] = raw_data

        ord_ = lambda c: ord(c) if not isinstance(c, int) else c

        clear_data = bytearray()
        for idx, val in enumerate(raw_data):
            clear_data.append((ord_(val) ^ ord_(key[idx % len(key)])))
        result["clear_data"] = bytes(clear_data)

        # 022514.python.pefile.line3383.comment the checksum should be present 3 times after the DanS signature
        # 022515.python.pefile.line3384.comment
        checksum = data[1]
        if data[0] ^ checksum != DANS or data[2] != checksum or data[3] != checksum:
            return None

        result["checksum"] = checksum
        headervalues = []
        result["values"] = headervalues

        data = data[4:]
        for i in range(int(len(data) / 2)):

            # 022516.python.pefile.line3396.comment Stop until the Rich footer signature is found
            # 022517.python.pefile.line3397.comment
            if data[2 * i] == RICH:

                # 022518.python.pefile.line3400.comment it should be followed by the checksum
                # 022519.python.pefile.line3401.comment
                if data[2 * i + 1] != checksum:
                    self.__warnings.append("Rich Header is malformed")
                break

            # 022520.python.pefile.line3406.comment header values come by pairs
            # 022521.python.pefile.line3407.comment
            headervalues += [data[2 * i] ^ checksum, data[2 * i + 1] ^ checksum]
        return result

    def get_warnings(self):
        """Return the list of warnings.

        Non-critical problems found when parsing the PE file are
        appended to a list of warnings. This method returns the
        full list.
        """

        return self.__warnings

    def show_warnings(self):
        """Print the list of warnings.

        Non-critical problems found when parsing the PE file are
        appended to a list of warnings. This method prints the
        full list to standard output.
        """

        for warning in self.__warnings:
            print(">", warning)

    def full_load(self):
        """Process the data directories.

        This method will load the data directories which might not have
        been loaded if the "fast_load" option was used.
        """

        self.parse_data_directories()

        class RichHeader:
            pass

        rich_header = self.parse_rich_header()
        if rich_header:
            self.RICH_HEADER = RichHeader()
            self.RICH_HEADER.checksum = rich_header.get("checksum", None)
            self.RICH_HEADER.values = rich_header.get("values", None)
            self.RICH_HEADER.key = rich_header.get("key", None)
            self.RICH_HEADER.raw_data = rich_header.get("raw_data", None)
            self.RICH_HEADER.clear_data = rich_header.get("clear_data", None)
        else:
            self.RICH_HEADER = None

    def write(self, filename=None):
        """Write the PE file.

        This function will process all headers and components
        of the PE file and include all changes made (by just
        assigning to attributes in the PE objects) and write
        the changes back to a file whose name is provided as
        an argument. The filename is optional, if not
        provided the data will be returned as a 'str' object.
        """

        file_data = bytearray(self.__data__)

        for structure in self.__structures__:
            struct_data = bytearray(structure.__pack__())
            offset = structure.get_file_offset()
            file_data[offset : offset + len(struct_data)] = struct_data

        if hasattr(self, "VS_VERSIONINFO"):
            if hasattr(self, "FileInfo"):
                for finfo in self.FileInfo:
                    for entry in finfo:
                        if hasattr(entry, "StringTable"):
                            for st_entry in entry.StringTable:
                                for key, entry in list(st_entry.entries.items()):

                                    # 022522.python.pefile.line3481.comment Offsets and lengths of the keys and values.
                                    # 022523.python.pefile.line3482.comment Each value in the dictionary is a tuple:
                                    # 022524.python.pefile.line3483.comment (key length, value length)
                                    # 022525.python.pefile.line3484.comment The lengths are in characters, not in bytes.
                                    offsets = st_entry.entries_offsets[key]
                                    lengths = st_entry.entries_lengths[key]

                                    if len(entry) > lengths[1]:
                                        l = entry.decode("utf-8").encode("utf-16le")
                                        file_data[
                                            offsets[1] : offsets[1] + lengths[1] * 2
                                        ] = l[: lengths[1] * 2]
                                    else:
                                        encoded_data = entry.decode("utf-8").encode(
                                            "utf-16le"
                                        )
                                        file_data[
                                            offsets[1] : offsets[1] + len(encoded_data)
                                        ] = encoded_data

        new_file_data = file_data
        if not filename:
            return new_file_data

        f = open(filename, "wb+")
        f.write(new_file_data)
        f.close()
        return

    def parse_sections(self, offset):
        """Fetch the PE file sections.

        The sections will be readily available in the "sections" attribute.
        Its attributes will contain all the section information plus "data"
        a buffer containing the section's data.

        The "Characteristics" member will be processed and attributes
        representing the section characteristics (with the 'IMAGE_SCN_'
        string trimmed from the constant's names) will be added to the
        section instance.

        Refer to the SectionStructure class for additional info.
        """

        self.sections = []
        MAX_SIMULTANEOUS_ERRORS = 3
        for i in range(self.FILE_HEADER.NumberOfSections):
            if i >= MAX_SECTIONS:
                self.__warnings.append(
                    "Too many sections {0} (>={1})".format(
                        self.FILE_HEADER.NumberOfSections, MAX_SECTIONS
                    )
                )
                break
            simultaneous_errors = 0
            section = SectionStructure(self.__IMAGE_SECTION_HEADER_format__, pe=self)
            if not section:
                break
            section_offset = offset + section.sizeof() * i
            section.set_file_offset(section_offset)
            section_data = self.__data__[
                section_offset : section_offset + section.sizeof()
            ]
            # 022526.python.pefile.line3544.comment Check if the section is all nulls and stop if so.
            if count_zeroes(section_data) == section.sizeof():
                self.__warnings.append(f"Invalid section {i}. Contents are null-bytes.")
                break
            if not section_data:
                self.__warnings.append(
                    f"Invalid section {i}. No data in the file (is this corkami's "
                    "virtsectblXP?)."
                )
                break
            section.__unpack__(section_data)
            self.__structures__.append(section)

            if section.SizeOfRawData + section.PointerToRawData > len(self.__data__):
                simultaneous_errors += 1
                self.__warnings.append(
                    f"Error parsing section {i}. SizeOfRawData is larger than file."
                )

            if self.adjust_FileAlignment(
                section.PointerToRawData, self.OPTIONAL_HEADER.FileAlignment
            ) > len(self.__data__):
                simultaneous_errors += 1
                self.__warnings.append(
                    f"Error parsing section {i}. PointerToRawData points beyond "
                    "the end of the file."
                )

            if section.Misc_VirtualSize > 0x10000000:
                simultaneous_errors += 1
                self.__warnings.append(
                    f"Suspicious value found parsing section {i}. VirtualSize is "
                    "extremely large > 256MiB."
                )

            if (
                self.adjust_SectionAlignment(
                    section.VirtualAddress,
                    self.OPTIONAL_HEADER.SectionAlignment,
                    self.OPTIONAL_HEADER.FileAlignment,
                )
                > 0x10000000
            ):
                simultaneous_errors += 1
                self.__warnings.append(
                    f"Suspicious value found parsing section {i}. VirtualAddress is "
                    "beyond 0x10000000."
                )

            if (
                self.OPTIONAL_HEADER.FileAlignment != 0
                and (section.PointerToRawData % self.OPTIONAL_HEADER.FileAlignment) != 0
            ):
                simultaneous_errors += 1
                self.__warnings.append(
                    (
                        f"Error parsing section {i}. "
                        "PointerToRawData should normally be "
                        "a multiple of FileAlignment, this might imply the file "
                        "is trying to confuse tools which parse this incorrectly."
                    )
                )

            if simultaneous_errors >= MAX_SIMULTANEOUS_ERRORS:
                self.__warnings.append("Too many warnings parsing section. Aborting.")
                break

            section_flags = retrieve_flags(SECTION_CHARACTERISTICS, "IMAGE_SCN_")

            # 022527.python.pefile.line3613.comment Set the section's flags according the the Characteristics member
            set_flags(section, section.Characteristics, section_flags)

            if section.__dict__.get(
                "IMAGE_SCN_MEM_WRITE", False
            ) and section.__dict__.get("IMAGE_SCN_MEM_EXECUTE", False):

                if section.Name.rstrip(b"\x00") == b"PAGE" and self.is_driver():
                    # 022528.python.pefile.line3621.comment Drivers can have a PAGE section with those flags set without
                    # 022529.python.pefile.line3622.comment implying that it is malicious
                    pass
                else:
                    self.__warnings.append(
                        f"Suspicious flags set for section {i}. "
                        "Both IMAGE_SCN_MEM_WRITE and IMAGE_SCN_MEM_EXECUTE are set. "
                        "This might indicate a packed executable."
                    )

            self.sections.append(section)

        # 022530.python.pefile.line3633.comment Sort the sections by their VirtualAddress and add a field to each of them
        # 022531.python.pefile.line3634.comment with the VirtualAddress of the next section. This will allow to check
        # 022532.python.pefile.line3635.comment for potentially overlapping sections in badly constructed PEs.
        self.sections.sort(key=lambda a: a.VirtualAddress)
        for idx, section in enumerate(self.sections):
            if idx == len(self.sections) - 1:
                section.next_section_virtual_address = None
            else:
                section.next_section_virtual_address = self.sections[
                    idx + 1
                ].VirtualAddress

        if self.FILE_HEADER.NumberOfSections > 0 and self.sections:
            return (
                offset + self.sections[0].sizeof() * self.FILE_HEADER.NumberOfSections
            )
        else:
            return offset

    def parse_data_directories(
        self, directories=None, forwarded_exports_only=False, import_dllnames_only=False
    ):
        """Parse and process the PE file's data directories.

        If the optional argument 'directories' is given, only
        the directories at the specified indexes will be parsed.
        Such functionality allows parsing of areas of interest
        without the burden of having to parse all others.
        The directories can then be specified as:

        For export / import only:

          directories = [ 0, 1 ]

        or (more verbosely):

          directories = [ DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT'],
            DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_EXPORT'] ]

        If 'directories' is a list, the ones that are processed will be removed,
        leaving only the ones that are not present in the image.

        If `forwarded_exports_only` is True, the IMAGE_DIRECTORY_ENTRY_EXPORT
        attribute will only contain exports that are forwarded to another DLL.

        If `import_dllnames_only` is True, symbols will not be parsed from
        the import table and the entries in the IMAGE_DIRECTORY_ENTRY_IMPORT
        attribute will not have a `symbols` attribute.
        """

        directory_parsing = (
            ("IMAGE_DIRECTORY_ENTRY_IMPORT", self.parse_import_directory),
            ("IMAGE_DIRECTORY_ENTRY_EXPORT", self.parse_export_directory),
            ("IMAGE_DIRECTORY_ENTRY_RESOURCE", self.parse_resources_directory),
            ("IMAGE_DIRECTORY_ENTRY_DEBUG", self.parse_debug_directory),
            ("IMAGE_DIRECTORY_ENTRY_BASERELOC", self.parse_relocations_directory),
            ("IMAGE_DIRECTORY_ENTRY_TLS", self.parse_directory_tls),
            ("IMAGE_DIRECTORY_ENTRY_LOAD_CONFIG", self.parse_directory_load_config),
            ("IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT", self.parse_delay_import_directory),
            ("IMAGE_DIRECTORY_ENTRY_BOUND_IMPORT", self.parse_directory_bound_imports),
            ("IMAGE_DIRECTORY_ENTRY_EXCEPTION", self.parse_exceptions_directory),
        )

        if directories is not None:
            if not isinstance(directories, (tuple, list)):
                directories = [directories]

        for entry in directory_parsing:
            # 022533.python.pefile.line3701.comment OC Patch:
            # 022534.python.pefile.line3702.comment
            try:
                directory_index = DIRECTORY_ENTRY[entry[0]]
                dir_entry = self.OPTIONAL_HEADER.DATA_DIRECTORY[directory_index]
            except IndexError:
                break

            # 022535.python.pefile.line3709.comment Only process all the directories if no individual ones have
            # 022536.python.pefile.line3710.comment been chosen
            # 022537.python.pefile.line3711.comment
            if directories is None or directory_index in directories:

                value = None
                if dir_entry.VirtualAddress:
                    if (
                        forwarded_exports_only
                        and entry[0] == "IMAGE_DIRECTORY_ENTRY_EXPORT"
                    ):
                        value = entry[1](
                            dir_entry.VirtualAddress,
                            dir_entry.Size,
                            forwarded_only=True,
                        )
                    elif (
                        import_dllnames_only
                        and entry[0] == "IMAGE_DIRECTORY_ENTRY_IMPORT"
                    ):
                        value = entry[1](
                            dir_entry.VirtualAddress, dir_entry.Size, dllnames_only=True
                        )

                    else:
                        try:
                            value = entry[1](dir_entry.VirtualAddress, dir_entry.Size)
                        except PEFormatError as excp:
                            self.__warnings.append(
                                f'Failed to process directoty "{entry[0]}": {excp}'
                            )
                    if value:
                        setattr(self, entry[0][6:], value)

            if (
                (directories is not None)
                and isinstance(directories, list)
                and (entry[0] in directories)
            ):
                directories.remove(directory_index)

    def parse_exceptions_directory(self, rva, size):
        """Parses exception directory

        All the code related to handling exception directories is documented in
        https://auscitte.github.io/systems%20blog/Exception-Directory-pefile#implementation-details
        """

        # 022538.python.pefile.line3757.comment "For x64 and Itanium platforms; the format is different for other platforms"
        if (
            self.FILE_HEADER.Machine != MACHINE_TYPE["IMAGE_FILE_MACHINE_AMD64"]
            and self.FILE_HEADER.Machine != MACHINE_TYPE["IMAGE_FILE_MACHINE_IA64"]
        ):
            return None

        rf = Structure(self.__RUNTIME_FUNCTION_format__)
        rf_size = rf.sizeof()
        rva2rt = {}
        rt_funcs = []
        rva2infos = {}
        for _ in range(size // rf_size):
            rf = self.__unpack_data__(
                self.__RUNTIME_FUNCTION_format__,
                self.get_data(rva, rf_size),
                file_offset=self.get_offset_from_rva(rva),
            )

            if rf is None:
                break

            ui = None

            if (rf.UnwindData & 0x1) == 0:
                # 022539.python.pefile.line3782.comment according to "Improving Automated Analysis of Windows x64 Binaries",
                # 022540.python.pefile.line3783.comment if the lowest bit is set, (UnwindData & ~0x1) should point to the
                # 022541.python.pefile.line3784.comment chained RUNTIME_FUNCTION instead of UNWIND_INFO

                if (
                    rf.UnwindData in rva2infos
                ):  # unwind info data structures can be shared among functions
                    ui = rva2infos[rf.UnwindData]
                else:
                    ui = UnwindInfo(file_offset=self.get_offset_from_rva(rf.UnwindData))
                    rva2infos[rf.UnwindData] = ui

                ws = ui.unpack_in_stages(self.get_data(rf.UnwindData, ui.sizeof()))
                if ws != None:
                    self.__warnings.append(ws)
                    break
                ws = ui.unpack_in_stages(self.get_data(rf.UnwindData, ui.sizeof()))
                if ws != None:
                    self.__warnings.append(ws)
                    break

                self.__structures__.append(ui)

            entry = ExceptionsDirEntryData(struct=rf, unwindinfo=ui)
            rt_funcs.append(entry)

            rva2rt[rf.BeginAddress] = entry
            rva += rf_size

        # 022543.python.pefile.line3811.comment each chained function entry holds a reference to the function first in chain
        for rf in rt_funcs:
            if rf.unwindinfo is None:
                # 022544.python.pefile.line3814.comment TODO: have not encountered such a binary yet;
                # 022545.python.pefile.line3815.comment in theory, (UnwindData & ~0x1) should point to the chained
                # 022546.python.pefile.line3816.comment RUNTIME_FUNCTION which could be used to locate the corresponding
                # 022547.python.pefile.line3817.comment ExceptionsDirEntryData and set_chained_function_entry()
                continue
            if not hasattr(rf.unwindinfo, "FunctionEntry"):
                continue
            if not rf.unwindinfo.FunctionEntry in rva2rt:
                self.__warnings.append(
                    f"FunctionEntry of UNWIND_INFO at {rf.struct.get_file_offset():x}"
                    " points to an entry that does not exist"
                )
                continue
            try:
                rf.unwindinfo.set_chained_function_entry(
                    rva2rt[rf.unwindinfo.FunctionEntry]
                )
            except PEFormatError as excp:
                self.__warnings.append(
                    "Failed parsing FunctionEntry of UNWIND_INFO at "
                    f"{rf.struct.get_file_offset():x}: {excp}"
                )
                continue

        return rt_funcs

    def parse_directory_bound_imports(self, rva, size):
        """"""

        bnd_descr = Structure(self.__IMAGE_BOUND_IMPORT_DESCRIPTOR_format__)
        bnd_descr_size = bnd_descr.sizeof()
        start = rva

        bound_imports = []
        while True:
            bnd_descr = self.__unpack_data__(
                self.__IMAGE_BOUND_IMPORT_DESCRIPTOR_format__,
                self.__data__[rva : rva + bnd_descr_size],
                file_offset=rva,
            )
            if bnd_descr is None:
                # 022548.python.pefile.line3855.comment If can't parse directory then silently return.
                # 022549.python.pefile.line3856.comment This directory does not necessarily have to be valid to
                # 022550.python.pefile.line3857.comment still have a valid PE file

                self.__warnings.append(
                    "The Bound Imports directory exists but can't be parsed."
                )

                return

            if bnd_descr.all_zeroes():
                break

            rva += bnd_descr.sizeof()

            section = self.get_section_by_offset(rva)
            file_offset = self.get_offset_from_rva(rva)
            if section is None:
                safety_boundary = len(self.__data__) - file_offset
                sections_after_offset = [
                    s.PointerToRawData
                    for s in self.sections
                    if s.PointerToRawData > file_offset
                ]
                if sections_after_offset:
                    # 022551.python.pefile.line3880.comment Find the first section starting at a later offset than that
                    # 022552.python.pefile.line3881.comment specified by 'rva'
                    first_section_after_offset = min(sections_after_offset)
                    section = self.get_section_by_offset(first_section_after_offset)
                    if section is not None:
                        safety_boundary = section.PointerToRawData - file_offset
            else:
                safety_boundary = (
                    section.PointerToRawData + len(section.get_data()) - file_offset
                )
            if not section:
                self.__warnings.append(
                    (
                        "RVA of IMAGE_BOUND_IMPORT_DESCRIPTOR points "
                        "to an invalid address: {0:x}"
                    ).format(rva)
                )
                return

            forwarder_refs = []
            # 022553.python.pefile.line3900.comment 8 is the size of __IMAGE_BOUND_IMPORT_DESCRIPTOR_format__
            for _ in range(
                min(bnd_descr.NumberOfModuleForwarderRefs, int(safety_boundary / 8))
            ):
                # 022554.python.pefile.line3904.comment Both structures IMAGE_BOUND_IMPORT_DESCRIPTOR and
                # 022555.python.pefile.line3905.comment IMAGE_BOUND_FORWARDER_REF have the same size.
                bnd_frwd_ref = self.__unpack_data__(
                    self.__IMAGE_BOUND_FORWARDER_REF_format__,
                    self.__data__[rva : rva + bnd_descr_size],
                    file_offset=rva,
                )
                # 022556.python.pefile.line3911.comment OC Patch:
                if not bnd_frwd_ref:
                    raise PEFormatError("IMAGE_BOUND_FORWARDER_REF cannot be read")
                rva += bnd_frwd_ref.sizeof()

                offset = start + bnd_frwd_ref.OffsetModuleName
                name_str = self.get_string_from_data(
                    0, self.__data__[offset : offset + MAX_STRING_LENGTH]
                )

                # 022557.python.pefile.line3921.comment OffsetModuleName points to a DLL name. These shouldn't be too long.
                # 022558.python.pefile.line3922.comment Anything longer than a safety length of 128 will be taken to indicate
                # 022559.python.pefile.line3923.comment a corrupt entry and abort the processing of these entries.
                # 022560.python.pefile.line3924.comment Names shorter than 4 characters will be taken as invalid as well.

                if name_str:
                    invalid_chars = [
                        c for c in bytearray(name_str) if chr(c) not in string.printable
                    ]
                    if len(name_str) > 256 or invalid_chars:
                        break

                forwarder_refs.append(
                    BoundImportRefData(struct=bnd_frwd_ref, name=name_str)
                )

            offset = start + bnd_descr.OffsetModuleName
            name_str = self.get_string_from_data(
                0, self.__data__[offset : offset + MAX_STRING_LENGTH]
            )

            if name_str:
                invalid_chars = [
                    c for c in bytearray(name_str) if chr(c) not in string.printable
                ]
                if len(name_str) > 256 or invalid_chars:
                    break

            if not name_str:
                break
            bound_imports.append(
                BoundImportDescData(
                    struct=bnd_descr, name=name_str, entries=forwarder_refs
                )
            )

        return bound_imports

    def parse_directory_tls(self, rva, size):
        """"""

        # 022561.python.pefile.line3962.comment By default let's pretend the format is a 32-bit PE. It may help
        # 022562.python.pefile.line3963.comment produce some output for files where the Magic in the Optional Header
        # 022563.python.pefile.line3964.comment is incorrect.
        format = self.__IMAGE_TLS_DIRECTORY_format__

        if self.PE_TYPE == OPTIONAL_HEADER_MAGIC_PE_PLUS:
            format = self.__IMAGE_TLS_DIRECTORY64_format__

        try:
            tls_struct = self.__unpack_data__(
                format,
                self.get_data(rva, Structure(format).sizeof()),
                file_offset=self.get_offset_from_rva(rva),
            )
        except PEFormatError:
            self.__warnings.append(
                "Invalid TLS information. Can't read " "data at RVA: 0x%x" % rva
            )
            tls_struct = None

        if not tls_struct:
            return None

        return TlsData(struct=tls_struct)

    def parse_directory_load_config(self, rva, size):
        """"""

        if self.PE_TYPE == OPTIONAL_HEADER_MAGIC_PE:
            load_config_dir_sz = self.get_dword_at_rva(rva)
            format = self.__IMAGE_LOAD_CONFIG_DIRECTORY_format__
        elif self.PE_TYPE == OPTIONAL_HEADER_MAGIC_PE_PLUS:
            load_config_dir_sz = self.get_dword_at_rva(rva)
            format = self.__IMAGE_LOAD_CONFIG_DIRECTORY64_format__
        else:
            self.__warnings.append(
                "Don't know how to parse LOAD_CONFIG information for non-PE32/"
                "PE32+ file"
            )
            return None

        # 022564.python.pefile.line4003.comment load config directory size can be less than represented by 'format' variable,
        # 022565.python.pefile.line4004.comment generate truncated format which correspond load config directory size
        fields_counter = 0
        cumulative_sz = 0
        for field in format[1]:
            fields_counter += 1
            cumulative_sz += STRUCT_SIZEOF_TYPES[field.split(",")[0]]
            if cumulative_sz == load_config_dir_sz:
                break
        format = (format[0], format[1][:fields_counter])

        load_config_struct = None
        try:
            load_config_struct = self.__unpack_data__(
                format,
                self.get_data(rva, Structure(format).sizeof()),
                file_offset=self.get_offset_from_rva(rva),
            )
        except PEFormatError:
            self.__warnings.append(
                "Invalid LOAD_CONFIG information. Can't read " "data at RVA: 0x%x" % rva
            )

        if not load_config_struct:
            return None

        dynamic_relocations = None
        if fields_counter > 35:
            dynamic_relocations = self.parse_dynamic_relocations(
                load_config_struct.DynamicValueRelocTableOffset,
                load_config_struct.DynamicValueRelocTableSection,
            )

        return LoadConfigData(
            struct=load_config_struct, dynamic_relocations=dynamic_relocations
        )

    def parse_dynamic_relocations(
        self, dynamic_value_reloc_table_offset, dynamic_value_reloc_table_section
    ):
        if not dynamic_value_reloc_table_offset:
            return None
        if not dynamic_value_reloc_table_section:
            return None

        if dynamic_value_reloc_table_section > len(self.sections):
            return None

        section = self.sections[dynamic_value_reloc_table_section - 1]
        rva = section.VirtualAddress + dynamic_value_reloc_table_offset
        image_dynamic_reloc_table_struct = None
        reloc_table_size = Structure(
            self.__IMAGE_DYNAMIC_RELOCATION_TABLE_format__
        ).sizeof()
        try:
            image_dynamic_reloc_table_struct = self.__unpack_data__(
                self.__IMAGE_DYNAMIC_RELOCATION_TABLE_format__,
                self.get_data(rva, reloc_table_size),
                file_offset=self.get_offset_from_rva(rva),
            )
        except PEFormatError:
            self.__warnings.append(
                "Invalid IMAGE_DYNAMIC_RELOCATION_TABLE information. Can't read "
                "data at RVA: 0x%x" % rva
            )

        if image_dynamic_reloc_table_struct.Version != 1:
            self.__warnings.append(
                "No pasring available for IMAGE_DYNAMIC_RELOCATION_TABLE.Version = %d",
                image_dynamic_reloc_table_struct.Version,
            )
            return None

        rva += reloc_table_size
        end = rva + image_dynamic_reloc_table_struct.Size
        dynamic_relocations = []

        while rva < end:
            format = self.__IMAGE_DYNAMIC_RELOCATION_format__

            if self.PE_TYPE == OPTIONAL_HEADER_MAGIC_PE_PLUS:
                format = self.__IMAGE_DYNAMIC_RELOCATION64_format__

            rlc_size = Structure(format).sizeof()

            try:
                dynamic_rlc = self.__unpack_data__(
                    format,
                    self.get_data(rva, rlc_size),
                    file_offset=self.get_offset_from_rva(rva),
                )
            except PEFormatError:
                self.__warnings.append(
                    "Invalid relocation information. Can't read "
                    "data at RVA: 0x%x" % rva
                )
                dynamic_rlc = None

            if not dynamic_rlc:
                break

            rva += rlc_size
            symbol = dynamic_rlc.Symbol
            size = dynamic_rlc.BaseRelocSize

            if 3 <= symbol <= 5:
                relocations = self.parse_image_base_relocation_list(
                    rva, size, self.dynamic_relocation_format_by_symbol[symbol]
                )
                dynamic_relocations.append(
                    DynamicRelocationData(
                        struct=dynamic_rlc, symbol=symbol, relocations=relocations
                    )
                )

            if symbol > 5:
                relocations = self.parse_image_base_relocation_list(rva, size)
                dynamic_relocations.append(
                    DynamicRelocationData(
                        struct=dynamic_rlc, symbol=symbol, relocations=relocations
                    )
                )

            rva += size

        return dynamic_relocations

    def parse_relocations_directory(self, rva, size):
        """"""

        return self.parse_image_base_relocation_list(rva, size)

    def parse_image_base_relocation_list(self, rva, size, fmt=None):
        rlc_size = Structure(self.__IMAGE_BASE_RELOCATION_format__).sizeof()
        end = rva + size

        relocations = []
        while rva < end:

            # 022566.python.pefile.line4142.comment OC Patch:
            # 022567.python.pefile.line4143.comment Malware that has bad RVA entries will cause an error.
            # 022568.python.pefile.line4144.comment Just continue on after an exception
            # 022569.python.pefile.line4145.comment
            try:
                rlc = self.__unpack_data__(
                    self.__IMAGE_BASE_RELOCATION_format__,
                    self.get_data(rva, rlc_size),
                    file_offset=self.get_offset_from_rva(rva),
                )
            except PEFormatError:
                self.__warnings.append(
                    "Invalid relocation information. Can't read "
                    "data at RVA: 0x%x" % rva
                )
                rlc = None

            if not rlc:
                break

            # 022570.python.pefile.line4162.comment rlc.VirtualAddress must lie within the Image
            if rlc.VirtualAddress > self.OPTIONAL_HEADER.SizeOfImage:
                self.__warnings.append(
                    "Invalid relocation information. VirtualAddress outside"
                    " of Image: 0x%x" % rlc.VirtualAddress
                )
                break

            # 022571.python.pefile.line4170.comment rlc.SizeOfBlock must be less or equal than the size of the image
            # 022572.python.pefile.line4171.comment (It's a rather loose sanity test)
            if rlc.SizeOfBlock > self.OPTIONAL_HEADER.SizeOfImage:
                self.__warnings.append(
                    "Invalid relocation information. SizeOfBlock too large"
                    ": %d" % rlc.SizeOfBlock
                )
                break

            if fmt is None:
                reloc_entries = self.parse_relocations(
                    rva + rlc_size, rlc.VirtualAddress, rlc.SizeOfBlock - rlc_size
                )
            else:
                reloc_entries = self.parse_relocations_with_format(
                    rva + rlc_size, rlc.VirtualAddress, rlc.SizeOfBlock - rlc_size, fmt
                )

            relocations.append(BaseRelocationData(struct=rlc, entries=reloc_entries))

            if not rlc.SizeOfBlock:
                break
            rva += rlc.SizeOfBlock

        return relocations

    def parse_relocations(self, data_rva, rva, size):
        """"""

        try:
            data = self.get_data(data_rva, size)
            file_offset = self.get_offset_from_rva(data_rva)
        except PEFormatError:
            self.__warnings.append(f"Bad RVA in relocation data: 0x{data_rva:x}")
            return []

        entries = []
        offsets_and_type = set()
        for idx in range(int(len(data) / 2)):

            entry = self.__unpack_data__(
                self.__IMAGE_BASE_RELOCATION_ENTRY_format__,
                data[idx * 2 : (idx + 1) * 2],
                file_offset=file_offset,
            )

            if not entry:
                break
            word = entry.Data

            reloc_type = word >> 12
            reloc_offset = word & 0x0FFF
            if (reloc_offset, reloc_type) in offsets_and_type:
                self.__warnings.append(
                    "Overlapping offsets in relocation data "
                    "at RVA: 0x%x" % (reloc_offset + rva)
                )
                break

            offsets_and_type.add((reloc_offset, reloc_type))

            entries.append(
                RelocationData(
                    struct=entry, type=reloc_type, base_rva=rva, rva=reloc_offset + rva
                )
            )
            file_offset += entry.sizeof()

        return entries

    def parse_relocations_with_format(self, data_rva, rva, size, format):
        """"""

        try:
            data = self.get_data(data_rva, size)
            file_offset = self.get_offset_from_rva(data_rva)
        except PEFormatError:
            self.__warnings.append(f"Bad RVA in relocation data: 0x{data_rva:x}")
            return []

        entry_size = StructureWithBitfields(format).sizeof()
        entries = []
        offsets = set()
        for idx in range(int(len(data) / entry_size)):

            entry = self.__unpack_data_with_bitfields__(
                format,
                data[idx * entry_size : (idx + 1) * entry_size],
                file_offset=file_offset,
            )

            if not entry:
                break

            reloc_offset = entry.PageRelativeOffset
            if reloc_offset in offsets:
                self.__warnings.append(
                    "Overlapping offsets in relocation data "
                    "at RVA: 0x%x" % (reloc_offset + rva)
                )
                break
            offsets.add(reloc_offset)

            entries.append(
                RelocationData(struct=entry, base_rva=rva, rva=reloc_offset + rva)
            )
            file_offset += entry_size

        return entries

    def parse_debug_directory(self, rva, size):
        """"""

        dbg_size = Structure(self.__IMAGE_DEBUG_DIRECTORY_format__).sizeof()

        debug = []
        for idx in range(int(size / dbg_size)):
            try:
                data = self.get_data(rva + dbg_size * idx, dbg_size)
            except PEFormatError:
                self.__warnings.append(
                    "Invalid debug information. Can't read " "data at RVA: 0x%x" % rva
                )
                return None

            dbg = self.__unpack_data__(
                self.__IMAGE_DEBUG_DIRECTORY_format__,
                data,
                file_offset=self.get_offset_from_rva(rva + dbg_size * idx),
            )

            if not dbg:
                return None

            # 022573.python.pefile.line4304.comment apply structure according to DEBUG_TYPE
            # 022574.python.pefile.line4305.comment http://www.debuginfo.com/articles/debuginfomatch.html
            # 022575.python.pefile.line4306.comment
            dbg_type = None

            if dbg.Type == 1:
                # 022576.python.pefile.line4310.comment IMAGE_DEBUG_TYPE_COFF
                pass

            elif dbg.Type == 2:
                # 022577.python.pefile.line4314.comment if IMAGE_DEBUG_TYPE_CODEVIEW
                dbg_type_offset = dbg.PointerToRawData
                dbg_type_size = dbg.SizeOfData
                dbg_type_data = self.__data__[
                    dbg_type_offset : dbg_type_offset + dbg_type_size
                ]

                if dbg_type_data[:4] == b"RSDS":
                    # 022578.python.pefile.line4322.comment pdb7.0
                    __CV_INFO_PDB70_format__ = [
                        "CV_INFO_PDB70",
                        [
                            "4s,CvSignature",
                            "I,Signature_Data1",  # Signature is of GUID type
                            "H,Signature_Data2",
                            "H,Signature_Data3",
                            "B,Signature_Data4",
                            "B,Signature_Data5",
                            "6s,Signature_Data6",
                            "I,Age",
                        ],
                    ]
                    pdbFileName_size = (
                        dbg_type_size - Structure(__CV_INFO_PDB70_format__).sizeof()
                    )

                    # 022580.python.pefile.line4340.comment pdbFileName_size can be negative here, as seen in the malware
                    # 022581.python.pefile.line4341.comment sample with hash
                    # 022582.python.pefile.line4342.comment MD5: 7c297600870d026c014d42596bb9b5fd
                    # 022583.python.pefile.line4343.comment SHA256:
                    # 022584.python.pefile.line4344.comment 83f4e63681fcba8a9d7bbb1688c71981b1837446514a1773597e0192bba9fac3
                    # 022585.python.pefile.line4345.comment Checking for positive size here to ensure proper parsing.
                    if pdbFileName_size > 0:
                        __CV_INFO_PDB70_format__[1].append(
                            "{0}s,PdbFileName".format(pdbFileName_size)
                        )
                    dbg_type = self.__unpack_data__(
                        __CV_INFO_PDB70_format__, dbg_type_data, dbg_type_offset
                    )
                    if dbg_type is not None:
                        dbg_type.Signature_Data6_value = struct.unpack(
                            ">Q", b"\0\0" + dbg_type.Signature_Data6
                        )[0]
                        dbg_type.Signature_String = (
                            str(
                                uuid.UUID(
                                    fields=(
                                        dbg_type.Signature_Data1,
                                        dbg_type.Signature_Data2,
                                        dbg_type.Signature_Data3,
                                        dbg_type.Signature_Data4,
                                        dbg_type.Signature_Data5,
                                        dbg_type.Signature_Data6_value,
                                    )
                                )
                            )
                            .replace("-", "")
                            .upper()
                            + f"{dbg_type.Age:X}"
                        )

                elif dbg_type_data[:4] == b"NB10":
                    # 022586.python.pefile.line4376.comment pdb2.0
                    __CV_INFO_PDB20_format__ = [
                        "CV_INFO_PDB20",
                        [
                            "I,CvHeaderSignature",
                            "I,CvHeaderOffset",
                            "I,Signature",
                            "I,Age",
                        ],
                    ]
                    pdbFileName_size = (
                        dbg_type_size - Structure(__CV_INFO_PDB20_format__).sizeof()
                    )

                    # 022587.python.pefile.line4390.comment As with the PDB 7.0 case, ensuring a positive size for
                    # 022588.python.pefile.line4391.comment pdbFileName_size to ensure proper parsing.
                    if pdbFileName_size > 0:
                        # 022589.python.pefile.line4393.comment Add the last variable-length string field.
                        __CV_INFO_PDB20_format__[1].append(
                            "{0}s,PdbFileName".format(pdbFileName_size)
                        )
                    dbg_type = self.__unpack_data__(
                        __CV_INFO_PDB20_format__, dbg_type_data, dbg_type_offset
                    )

            elif dbg.Type == 4:
                # 022590.python.pefile.line4402.comment IMAGE_DEBUG_TYPE_MISC
                dbg_type_offset = dbg.PointerToRawData
                dbg_type_size = dbg.SizeOfData
                dbg_type_data = self.__data__[
                    dbg_type_offset : dbg_type_offset + dbg_type_size
                ]
                ___IMAGE_DEBUG_MISC_format__ = [
                    "IMAGE_DEBUG_MISC",
                    [
                        "I,DataType",
                        "I,Length",
                        "B,Unicode",
                        "B,Reserved1",
                        "H,Reserved2",
                    ],
                ]
                dbg_type_partial = self.__unpack_data__(
                    ___IMAGE_DEBUG_MISC_format__, dbg_type_data, dbg_type_offset
                )

                # 022591.python.pefile.line4422.comment Need to check that dbg_type_partial contains a correctly unpacked data
                # 022592.python.pefile.line4423.comment structure, as the malware sample with the following hash
                # 022593.python.pefile.line4424.comment MD5:    5e7d6707d693108de5a303045c17d95b
                # 022594.python.pefile.line4425.comment SHA256:
                # 022595.python.pefile.line4426.comment 5dd94a95025f3b6e3dd440d52f7c6d2964fdd1aa119e0ee92e38c7bf83829e5c
                # 022596.python.pefile.line4427.comment contains a value of None for dbg_type_partial after unpacking,
                # 022597.python.pefile.line4428.comment presumably due to a malformed DEBUG entry.
                if dbg_type_partial:
                    # 022598.python.pefile.line4430.comment The Unicode bool should be set to 0 or 1.
                    if dbg_type_partial.Unicode in (0, 1):
                        data_size = (
                            dbg_type_size
                            - Structure(___IMAGE_DEBUG_MISC_format__).sizeof()
                        )

                        # 022599.python.pefile.line4437.comment As with the PDB case, ensuring a positive size for data_size
                        # 022600.python.pefile.line4438.comment here to ensure proper parsing.
                        if data_size > 0:
                            ___IMAGE_DEBUG_MISC_format__[1].append(
                                "{0}s,Data".format(data_size)
                            )
                        dbg_type = self.__unpack_data__(
                            ___IMAGE_DEBUG_MISC_format__, dbg_type_data, dbg_type_offset
                        )

            debug.append(DebugData(struct=dbg, entry=dbg_type))

        return debug

    def parse_resources_directory(self, rva, size=0, base_rva=None, level=0, dirs=None):
        """Parse the resources directory.

        Given the RVA of the resources directory, it will process all
        its entries.

        The root will have the corresponding member of its structure,
        IMAGE_RESOURCE_DIRECTORY plus 'entries', a list of all the
        entries in the directory.

        Those entries will have, correspondingly, all the structure's
        members (IMAGE_RESOURCE_DIRECTORY_ENTRY) and an additional one,
        "directory", pointing to the IMAGE_RESOURCE_DIRECTORY structure
        representing upper layers of the tree. This one will also have
        an 'entries' attribute, pointing to the 3rd, and last, level.
        Another directory with more entries. Those last entries will
        have a new attribute (both 'leaf' or 'data_entry' can be used to
        access it). This structure finally points to the resource data.
        All the members of this structure, IMAGE_RESOURCE_DATA_ENTRY,
        are available as its attributes.
        """

        # 022601.python.pefile.line4473.comment OC Patch:
        if dirs is None:
            dirs = [rva]

        if base_rva is None:
            base_rva = rva

        if level > MAX_RESOURCE_DEPTH:
            self.__warnings.append(
                "Error parsing the resources directory. "
                "Excessively nested table depth %d (>%s)" % (level, MAX_RESOURCE_DEPTH)
            )
            return None

        try:
            # 022602.python.pefile.line4488.comment If the RVA is invalid all would blow up. Some EXEs seem to be
            # 022603.python.pefile.line4489.comment specially nasty and have an invalid RVA.
            data = self.get_data(
                rva, Structure(self.__IMAGE_RESOURCE_DIRECTORY_format__).sizeof()
            )
        except PEFormatError:
            self.__warnings.append(
                "Invalid resources directory. Can't read "
                "directory data at RVA: 0x%x" % rva
            )
            return None

        # 022604.python.pefile.line4500.comment Get the resource directory structure, that is, the header
        # 022605.python.pefile.line4501.comment of the table preceding the actual entries
        # 022606.python.pefile.line4502.comment
        resource_dir = self.__unpack_data__(
            self.__IMAGE_RESOURCE_DIRECTORY_format__,
            data,
            file_offset=self.get_offset_from_rva(rva),
        )
        if resource_dir is None:
            # 022607.python.pefile.line4509.comment If we can't parse resources directory then silently return.
            # 022608.python.pefile.line4510.comment This directory does not necessarily have to be valid to
            # 022609.python.pefile.line4511.comment still have a valid PE file
            self.__warnings.append(
                "Invalid resources directory. Can't parse "
                "directory data at RVA: 0x%x" % rva
            )
            return None

        dir_entries = []

        # 022610.python.pefile.line4520.comment Advance the RVA to the position immediately following the directory
        # 022611.python.pefile.line4521.comment table header and pointing to the first entry in the table
        # 022612.python.pefile.line4522.comment
        rva += resource_dir.sizeof()

        number_of_entries = (
            resource_dir.NumberOfNamedEntries + resource_dir.NumberOfIdEntries
        )

        # 022613.python.pefile.line4529.comment Set a hard limit on the maximum reasonable number of entries
        MAX_ALLOWED_ENTRIES = 4096
        if number_of_entries > MAX_ALLOWED_ENTRIES:
            self.__warnings.append(
                "Error parsing the resources directory. "
                "The directory contains %d entries (>%s)"
                % (number_of_entries, MAX_ALLOWED_ENTRIES)
            )
            return None

        self.__total_resource_entries_count += number_of_entries
        if self.__total_resource_entries_count > MAX_RESOURCE_ENTRIES:
            self.__warnings.append(
                "Error parsing the resources directory. "
                "The file contains at least %d entries (>%d)"
                % (self.__total_resource_entries_count, MAX_RESOURCE_ENTRIES)
            )
            return None

        strings_to_postprocess = []

        # 022614.python.pefile.line4550.comment Keep track of the last name's start and end offsets in order
        # 022615.python.pefile.line4551.comment to be able to detect overlapping entries that might suggest
        # 022616.python.pefile.line4552.comment and invalid or corrupt directory.
        last_name_begin_end = None
        for idx in range(number_of_entries):
            if (
                not self.__resource_size_limit_reached
                and self.__total_resource_bytes > self.__resource_size_limit_upperbounds
            ):

                self.__resource_size_limit_reached = True
                self.__warnings.append(
                    "Resource size 0x%x exceeds file size 0x%x, overlapping "
                    "resources found."
                    % (
                        self.__total_resource_bytes,
                        self.__resource_size_limit_upperbounds,
                    )
                )

            res = self.parse_resource_entry(rva)
            if res is None:
                self.__warnings.append(
                    "Error parsing the resources directory, "
                    "Entry %d is invalid, RVA = 0x%x. " % (idx, rva)
                )
                break

            entry_name = None
            entry_id = None

            name_is_string = (res.Name & 0x80000000) >> 31
            if not name_is_string:
                entry_id = res.Name
            else:
                ustr_offset = base_rva + res.NameOffset
                try:
                    entry_name = UnicodeStringWrapperPostProcessor(self, ustr_offset)
                    self.__total_resource_bytes += entry_name.get_pascal_16_length()
                    # 022617.python.pefile.line4589.comment If the last entry's offset points before the current's but its end
                    # 022618.python.pefile.line4590.comment is past the current's beginning, assume the overlap indicates a
                    # 022619.python.pefile.line4591.comment corrupt name.
                    if last_name_begin_end and (
                        last_name_begin_end[0] < ustr_offset
                        and last_name_begin_end[1] >= ustr_offset
                    ):
                        # 022620.python.pefile.line4596.comment Remove the previous overlapping entry as it's likely to be
                        # 022621.python.pefile.line4597.comment already corrupt data.
                        strings_to_postprocess.pop()
                        self.__warnings.append(
                            "Error parsing the resources directory, "
                            "attempting to read entry name. "
                            "Entry names overlap 0x%x" % (ustr_offset)
                        )
                        break

                    last_name_begin_end = (
                        ustr_offset,
                        ustr_offset + entry_name.get_pascal_16_length(),
                    )

                    strings_to_postprocess.append(entry_name)

                except PEFormatError:
                    self.__warnings.append(
                        "Error parsing the resources directory, "
                        "attempting to read entry name. "
                        "Can't read unicode string at offset 0x%x" % (ustr_offset)
                    )

            if res.DataIsDirectory:
                # 022622.python.pefile.line4621.comment OC Patch:
                # 022623.python.pefile.line4622.comment
                # 022624.python.pefile.line4623.comment One trick malware can do is to recursively reference
                # 022625.python.pefile.line4624.comment the next directory. This causes hilarity to ensue when
                # 022626.python.pefile.line4625.comment trying to parse everything correctly.
                # 022627.python.pefile.line4626.comment If the original RVA given to this function is equal to
                # 022628.python.pefile.line4627.comment the next one to parse, we assume that it's a trick.
                # 022629.python.pefile.line4628.comment Instead of raising a PEFormatError this would skip some
                # 022630.python.pefile.line4629.comment reasonable data so we just break.
                # 022631.python.pefile.line4630.comment
                # 022632.python.pefile.line4631.comment 9ee4d0a0caf095314fd7041a3e4404dc is the offending sample
                if base_rva + res.OffsetToDirectory in dirs:
                    break

                entry_directory = self.parse_resources_directory(
                    base_rva + res.OffsetToDirectory,
                    size - (rva - base_rva),  # size
                    base_rva=base_rva,
                    level=level + 1,
                    dirs=dirs + [base_rva + res.OffsetToDirectory],
                )

                if not entry_directory:
                    break

                # 022634.python.pefile.line4646.comment Ange Albertini's code to process resources' strings
                # 022635.python.pefile.line4647.comment
                strings = None
                if entry_id == RESOURCE_TYPE["RT_STRING"]:
                    strings = {}
                    for resource_id in entry_directory.entries:
                        if hasattr(resource_id, "directory"):

                            resource_strings = {}

                            for resource_lang in resource_id.directory.entries:

                                if (
                                    resource_lang is None
                                    or not hasattr(resource_lang, "data")
                                    or resource_lang.data.struct.Size is None
                                    or resource_id.id is None
                                ):
                                    continue

                                string_entry_rva = (
                                    resource_lang.data.struct.OffsetToData
                                )
                                string_entry_size = resource_lang.data.struct.Size
                                string_entry_id = resource_id.id

                                # 022636.python.pefile.line4672.comment XXX: has been raising exceptions preventing parsing
                                try:
                                    string_entry_data = self.get_data(
                                        string_entry_rva, string_entry_size
                                    )
                                except PEFormatError:
                                    self.__warnings.append(
                                        f"Error parsing resource of type RT_STRING at "
                                        f"RVA 0x{string_entry_rva:x} with "
                                        f"size {string_entry_size}"
                                    )
                                    continue

                                parse_strings(
                                    string_entry_data,
                                    (int(string_entry_id) - 1) * 16,
                                    resource_strings,
                                )
                                strings.update(resource_strings)

                            resource_id.directory.strings = resource_strings

                dir_entries.append(
                    ResourceDirEntryData(
                        struct=res,
                        name=entry_name,
                        id=entry_id,
                        directory=entry_directory,
                    )
                )

            else:
                struct = self.parse_resource_data_entry(
                    base_rva + res.OffsetToDirectory
                )

                if struct:
                    self.__total_resource_bytes += struct.Size
                    entry_data = ResourceDataEntryData(
                        struct=struct, lang=res.Name & 0x3FF, sublang=res.Name >> 10
                    )

                    dir_entries.append(
                        ResourceDirEntryData(
                            struct=res, name=entry_name, id=entry_id, data=entry_data
                        )
                    )

                else:
                    break

            # 022637.python.pefile.line4723.comment Check if this entry contains version information
            # 022638.python.pefile.line4724.comment
            if level == 0 and res.Id == RESOURCE_TYPE["RT_VERSION"]:
                if dir_entries:
                    last_entry = dir_entries[-1]

                try:
                    version_entries = last_entry.directory.entries[0].directory.entries
                except:
                    # 022639.python.pefile.line4732.comment Maybe a malformed directory structure...?
                    # 022640.python.pefile.line4733.comment Let's ignore it
                    pass
                else:
                    for version_entry in version_entries:
                        rt_version_struct = None
                        try:
                            rt_version_struct = version_entry.data.struct
                        except:
                            # 022641.python.pefile.line4741.comment Maybe a malformed directory structure...?
                            # 022642.python.pefile.line4742.comment Let's ignore it
                            pass

                        if rt_version_struct is not None:
                            self.parse_version_information(rt_version_struct)

            rva += res.sizeof()

        string_rvas = [s.get_rva() for s in strings_to_postprocess]
        string_rvas.sort()

        for idx, s in enumerate(strings_to_postprocess):
            s.render_pascal_16()

        resource_directory_data = ResourceDirData(
            struct=resource_dir, entries=dir_entries
        )

        return resource_directory_data

    def parse_resource_data_entry(self, rva):
        """Parse a data entry from the resources directory."""

        try:
            # 022643.python.pefile.line4766.comment If the RVA is invalid all would blow up. Some EXEs seem to be
            # 022644.python.pefile.line4767.comment specially nasty and have an invalid RVA.
            data = self.get_data(
                rva, Structure(self.__IMAGE_RESOURCE_DATA_ENTRY_format__).sizeof()
            )
        except PEFormatError:
            self.__warnings.append(
                "Error parsing a resource directory data entry, "
                "the RVA is invalid: 0x%x" % (rva)
            )
            return None

        data_entry = self.__unpack_data__(
            self.__IMAGE_RESOURCE_DATA_ENTRY_format__,
            data,
            file_offset=self.get_offset_from_rva(rva),
        )

        return data_entry

    def parse_resource_entry(self, rva):
        """Parse a directory entry from the resources directory."""

        try:
            data = self.get_data(
                rva, Structure(self.__IMAGE_RESOURCE_DIRECTORY_ENTRY_format__).sizeof()
            )
        except PEFormatError:
            # 022645.python.pefile.line4794.comment A warning will be added by the caller if this method returns None
            return None

        resource = self.__unpack_data__(
            self.__IMAGE_RESOURCE_DIRECTORY_ENTRY_format__,
            data,
            file_offset=self.get_offset_from_rva(rva),
        )

        if resource is None:
            return None

        # 022646.python.pefile.line4806.comment resource.NameIsString = (resource.Name & 0x80000000L) >> 31
        resource.NameOffset = resource.Name & 0x7FFFFFFF

        resource.__pad = resource.Name & 0xFFFF0000
        resource.Id = resource.Name & 0x0000FFFF

        resource.DataIsDirectory = (resource.OffsetToData & 0x80000000) >> 31
        resource.OffsetToDirectory = resource.OffsetToData & 0x7FFFFFFF

        return resource

    def parse_version_information(self, version_struct):
        """Parse version information structure.

        The date will be made available in three attributes of the PE object.

        VS_VERSIONINFO   will contain the first three fields of the main structure:
            'Length', 'ValueLength', and 'Type'

        VS_FIXEDFILEINFO will hold the rest of the fields, accessible as sub-attributes:
            'Signature', 'StrucVersion', 'FileVersionMS', 'FileVersionLS',
            'ProductVersionMS', 'ProductVersionLS', 'FileFlagsMask', 'FileFlags',
            'FileOS', 'FileType', 'FileSubtype', 'FileDateMS', 'FileDateLS'

        FileInfo    is a list of all StringFileInfo and VarFileInfo structures.

        StringFileInfo structures will have a list as an attribute named 'StringTable'
        containing all the StringTable structures. Each of those structures contains a
        dictionary 'entries' with all the key / value version information string pairs.

        VarFileInfo structures will have a list as an attribute named 'Var' containing
        all Var structures. Each Var structure will have a dictionary as an attribute
        named 'entry' which will contain the name and value of the Var.
        """

        # 022647.python.pefile.line4841.comment Retrieve the data for the version info resource
        # 022648.python.pefile.line4842.comment
        try:
            start_offset = self.get_offset_from_rva(version_struct.OffsetToData)
        except PEFormatError:
            self.__warnings.append(
                "Error parsing the version information, "
                "attempting to read OffsetToData with RVA: 0x{:x}".format(
                    version_struct.OffsetToData
                )
            )
            return
        raw_data = self.__data__[start_offset : start_offset + version_struct.Size]

        # 022649.python.pefile.line4855.comment Map the main structure and the subsequent string
        # 022650.python.pefile.line4856.comment
        versioninfo_struct = self.__unpack_data__(
            self.__VS_VERSIONINFO_format__, raw_data, file_offset=start_offset
        )

        if versioninfo_struct is None:
            return

        ustr_offset = version_struct.OffsetToData + versioninfo_struct.sizeof()
        section = self.get_section_by_rva(ustr_offset)
        section_end = None
        if section:
            section_end = section.VirtualAddress + max(
                section.SizeOfRawData, section.Misc_VirtualSize
            )

        versioninfo_string = None
        # 022651.python.pefile.line4873.comment These should return 'ascii' decoded data. For the case when it's
        # 022652.python.pefile.line4874.comment garbled data the ascii string will retain the byte values while
        # 022653.python.pefile.line4875.comment encoding it to something else may yield values that don't match the
        # 022654.python.pefile.line4876.comment file's contents.
        try:
            if section_end is None:
                versioninfo_string = self.get_string_u_at_rva(
                    ustr_offset, encoding="ascii"
                )
            else:
                versioninfo_string = self.get_string_u_at_rva(
                    ustr_offset, (section_end - ustr_offset) >> 1, encoding="ascii"
                )
        except PEFormatError:
            self.__warnings.append(
                "Error parsing the version information, "
                "attempting to read VS_VERSION_INFO string. Can't "
                "read unicode string at offset 0x%x" % (ustr_offset)
            )

        if versioninfo_string is None:
            self.__warnings.append(
                "Invalid VS_VERSION_INFO block: {0}".format(versioninfo_string)
            )
            return

        # 022655.python.pefile.line4899.comment If the structure does not contain the expected name, it's assumed to
        # 022656.python.pefile.line4900.comment be invalid
        if versioninfo_string is not None and versioninfo_string != b"VS_VERSION_INFO":
            if len(versioninfo_string) > 128:
                excerpt = versioninfo_string[:128].decode("ascii")
                # 022657.python.pefile.line4904.comment Don't leave any half-escaped characters
                excerpt = excerpt[: excerpt.rfind("\\u")]
                versioninfo_string = b(
                    "{0} ... ({1} bytes, too long to display)".format(
                        excerpt, len(versioninfo_string)
                    )
                )
            self.__warnings.append(
                "Invalid VS_VERSION_INFO block: {0}".format(
                    versioninfo_string.decode("ascii").replace("\00", "\\00")
                )
            )
            return

        if not hasattr(self, "VS_VERSIONINFO"):
            self.VS_VERSIONINFO = []

        # 022658.python.pefile.line4921.comment Set the PE object's VS_VERSIONINFO to this one
        vinfo = versioninfo_struct

        # 022659.python.pefile.line4924.comment Set the Key attribute to point to the unicode string identifying the structure
        vinfo.Key = versioninfo_string

        self.VS_VERSIONINFO.append(vinfo)

        if versioninfo_string is None:
            versioninfo_string = ""
        # 022660.python.pefile.line4931.comment Process the fixed version information, get the offset and structure
        fixedfileinfo_offset = self.dword_align(
            versioninfo_struct.sizeof() + 2 * (len(versioninfo_string) + 1),
            version_struct.OffsetToData,
        )
        fixedfileinfo_struct = self.__unpack_data__(
            self.__VS_FIXEDFILEINFO_format__,
            raw_data[fixedfileinfo_offset:],
            file_offset=start_offset + fixedfileinfo_offset,
        )

        if not fixedfileinfo_struct:
            return

        if not hasattr(self, "VS_FIXEDFILEINFO"):
            self.VS_FIXEDFILEINFO = []

        # 022661.python.pefile.line4948.comment Set the PE object's VS_FIXEDFILEINFO to this one
        self.VS_FIXEDFILEINFO.append(fixedfileinfo_struct)

        # 022662.python.pefile.line4951.comment Start parsing all the StringFileInfo and VarFileInfo structures

        # 022663.python.pefile.line4953.comment Get the first one
        stringfileinfo_offset = self.dword_align(
            fixedfileinfo_offset + fixedfileinfo_struct.sizeof(),
            version_struct.OffsetToData,
        )

        # 022664.python.pefile.line4959.comment Set the PE object's attribute that will contain them all.
        if not hasattr(self, "FileInfo"):
            self.FileInfo = []

        finfo = []
        while True:

            # 022665.python.pefile.line4966.comment Process the StringFileInfo/VarFileInfo structure
            stringfileinfo_struct = self.__unpack_data__(
                self.__StringFileInfo_format__,
                raw_data[stringfileinfo_offset:],
                file_offset=start_offset + stringfileinfo_offset,
            )

            if stringfileinfo_struct is None:
                self.__warnings.append(
                    "Error parsing StringFileInfo/VarFileInfo struct"
                )
                return None

            # 022666.python.pefile.line4979.comment Get the subsequent string defining the structure.
            ustr_offset = (
                version_struct.OffsetToData
                + stringfileinfo_offset
                + versioninfo_struct.sizeof()
            )
            try:
                stringfileinfo_string = self.get_string_u_at_rva(ustr_offset)
            except PEFormatError:
                self.__warnings.append(
                    "Error parsing the version information, "
                    "attempting to read StringFileInfo string. Can't "
                    "read unicode string at offset 0x{0:x}".format(ustr_offset)
                )
                break

            # 022667.python.pefile.line4995.comment Set such string as the Key attribute
            stringfileinfo_struct.Key = stringfileinfo_string

            # 022668.python.pefile.line4998.comment Append the structure to the PE object's list
            finfo.append(stringfileinfo_struct)

            # 022669.python.pefile.line5001.comment Parse a StringFileInfo entry
            if stringfileinfo_string and stringfileinfo_string.startswith(
                b"StringFileInfo"
            ):

                if (
                    stringfileinfo_struct.Type in (0, 1)
                    and stringfileinfo_struct.ValueLength == 0
                ):

                    stringtable_offset = self.dword_align(
                        stringfileinfo_offset
                        + stringfileinfo_struct.sizeof()
                        + 2 * (len(stringfileinfo_string) + 1),
                        version_struct.OffsetToData,
                    )

                    stringfileinfo_struct.StringTable = []

                    # 022670.python.pefile.line5020.comment Process the String Table entries
                    while True:

                        stringtable_struct = self.__unpack_data__(
                            self.__StringTable_format__,
                            raw_data[stringtable_offset:],
                            file_offset=start_offset + stringtable_offset,
                        )

                        if not stringtable_struct:
                            break

                        ustr_offset = (
                            version_struct.OffsetToData
                            + stringtable_offset
                            + stringtable_struct.sizeof()
                        )
                        try:
                            stringtable_string = self.get_string_u_at_rva(ustr_offset)
                        except PEFormatError:
                            self.__warnings.append(
                                "Error parsing the version information, "
                                "attempting to read StringTable string. Can't "
                                "read unicode string at offset 0x{0:x}".format(
                                    ustr_offset
                                )
                            )
                            break

                        stringtable_struct.LangID = stringtable_string
                        stringtable_struct.entries = {}
                        stringtable_struct.entries_offsets = {}
                        stringtable_struct.entries_lengths = {}
                        stringfileinfo_struct.StringTable.append(stringtable_struct)

                        entry_offset = self.dword_align(
                            stringtable_offset
                            + stringtable_struct.sizeof()
                            + 2 * (len(stringtable_string) + 1),
                            version_struct.OffsetToData,
                        )

                        # 022671.python.pefile.line5062.comment Process all entries in the string table

                        while (
                            entry_offset
                            < stringtable_offset + stringtable_struct.Length
                        ):

                            string_struct = self.__unpack_data__(
                                self.__String_format__,
                                raw_data[entry_offset:],
                                file_offset=start_offset + entry_offset,
                            )

                            if not string_struct:
                                break

                            ustr_offset = (
                                version_struct.OffsetToData
                                + entry_offset
                                + string_struct.sizeof()
                            )
                            try:
                                key = self.get_string_u_at_rva(ustr_offset)
                                key_offset = self.get_offset_from_rva(ustr_offset)
                            except PEFormatError:
                                self.__warnings.append(
                                    "Error parsing the version information, "
                                    "attempting to read StringTable Key string. Can't "
                                    "read unicode string at offset 0x{0:x}".format(
                                        ustr_offset
                                    )
                                )
                                break

                            value_offset = self.dword_align(
                                2 * (len(key) + 1)
                                + entry_offset
                                + string_struct.sizeof(),
                                version_struct.OffsetToData,
                            )

                            ustr_offset = version_struct.OffsetToData + value_offset
                            try:
                                value = self.get_string_u_at_rva(
                                    ustr_offset, max_length=string_struct.ValueLength
                                )
                                value_offset = self.get_offset_from_rva(ustr_offset)
                            except PEFormatError:
                                self.__warnings.append(
                                    "Error parsing the version information, attempting "
                                    "to read StringTable Value string. Can't read "
                                    f"unicode string at offset 0x{ustr_offset:x}"
                                )
                                break

                            if string_struct.Length == 0:
                                entry_offset = (
                                    stringtable_offset + stringtable_struct.Length
                                )
                            else:
                                entry_offset = self.dword_align(
                                    string_struct.Length + entry_offset,
                                    version_struct.OffsetToData,
                                )

                            stringtable_struct.entries[key] = value
                            stringtable_struct.entries_offsets[key] = (
                                key_offset,
                                value_offset,
                            )
                            stringtable_struct.entries_lengths[key] = (
                                len(key),
                                len(value),
                            )

                        new_stringtable_offset = self.dword_align(
                            stringtable_struct.Length + stringtable_offset,
                            version_struct.OffsetToData,
                        )

                        # 022672.python.pefile.line5142.comment Check if the entry is crafted in a way that would lead
                        # 022673.python.pefile.line5143.comment to an infinite loop and break if so.
                        if new_stringtable_offset == stringtable_offset:
                            break
                        stringtable_offset = new_stringtable_offset

                        if stringtable_offset >= stringfileinfo_struct.Length:
                            break

            # 022674.python.pefile.line5151.comment Parse a VarFileInfo entry
            elif stringfileinfo_string and stringfileinfo_string.startswith(
                b"VarFileInfo"
            ):

                varfileinfo_struct = stringfileinfo_struct
                varfileinfo_struct.name = "VarFileInfo"

                if (
                    varfileinfo_struct.Type in (0, 1)
                    and varfileinfo_struct.ValueLength == 0
                ):

                    var_offset = self.dword_align(
                        stringfileinfo_offset
                        + varfileinfo_struct.sizeof()
                        + 2 * (len(stringfileinfo_string) + 1),
                        version_struct.OffsetToData,
                    )

                    varfileinfo_struct.Var = []

                    # 022675.python.pefile.line5173.comment Process all entries

                    while True:
                        var_struct = self.__unpack_data__(
                            self.__Var_format__,
                            raw_data[var_offset:],
                            file_offset=start_offset + var_offset,
                        )

                        if not var_struct:
                            break

                        ustr_offset = (
                            version_struct.OffsetToData
                            + var_offset
                            + var_struct.sizeof()
                        )
                        try:
                            var_string = self.get_string_u_at_rva(ustr_offset)
                        except PEFormatError:
                            self.__warnings.append(
                                "Error parsing the version information, "
                                "attempting to read VarFileInfo Var string. "
                                "Can't read unicode string at offset 0x{0:x}".format(
                                    ustr_offset
                                )
                            )
                            break

                        if var_string is None:
                            break

                        varfileinfo_struct.Var.append(var_struct)

                        varword_offset = self.dword_align(
                            2 * (len(var_string) + 1)
                            + var_offset
                            + var_struct.sizeof(),
                            version_struct.OffsetToData,
                        )
                        orig_varword_offset = varword_offset

                        while (
                            varword_offset
                            < orig_varword_offset + var_struct.ValueLength
                        ):
                            word1 = self.get_word_from_data(
                                raw_data[varword_offset : varword_offset + 2], 0
                            )
                            word2 = self.get_word_from_data(
                                raw_data[varword_offset + 2 : varword_offset + 4], 0
                            )
                            varword_offset += 4

                            if isinstance(word1, int) and isinstance(word2, int):
                                var_struct.entry = {
                                    var_string: "0x%04x 0x%04x" % (word1, word2)
                                }

                        var_offset = self.dword_align(
                            var_offset + var_struct.Length, version_struct.OffsetToData
                        )

                        if var_offset <= var_offset + var_struct.Length:
                            break

            # 022676.python.pefile.line5239.comment Increment and align the offset
            stringfileinfo_offset = self.dword_align(
                stringfileinfo_struct.Length + stringfileinfo_offset,
                version_struct.OffsetToData,
            )

            # 022677.python.pefile.line5245.comment Check if all the StringFileInfo and VarFileInfo items have been processed
            if (
                stringfileinfo_struct.Length == 0
                or stringfileinfo_offset >= versioninfo_struct.Length
            ):
                break

        self.FileInfo.append(finfo)

    def parse_export_directory(self, rva, size, forwarded_only=False):
        """Parse the export directory.

        Given the RVA of the export directory, it will process all
        its entries.

        The exports will be made available as a list of ExportData
        instances in the 'IMAGE_DIRECTORY_ENTRY_EXPORT' PE attribute.
        """

        try:
            export_dir = self.__unpack_data__(
                self.__IMAGE_EXPORT_DIRECTORY_format__,
                self.get_data(
                    rva, Structure(self.__IMAGE_EXPORT_DIRECTORY_format__).sizeof()
                ),
                file_offset=self.get_offset_from_rva(rva),
            )
        except PEFormatError:
            self.__warnings.append(
                "Error parsing export directory at RVA: 0x%x" % (rva)
            )
            return

        if not export_dir:
            return

        # 022678.python.pefile.line5281.comment We keep track of the bytes left in the file and use it to set a upper
        # 022679.python.pefile.line5282.comment bound in the number of items that can be read from the different
        # 022680.python.pefile.line5283.comment arrays.
        def length_until_eof(rva):
            return len(self.__data__) - self.get_offset_from_rva(rva)

        try:
            address_of_names = self.get_data(
                export_dir.AddressOfNames,
                min(
                    length_until_eof(export_dir.AddressOfNames),
                    export_dir.NumberOfNames * 4,
                ),
            )
            address_of_name_ordinals = self.get_data(
                export_dir.AddressOfNameOrdinals,
                min(
                    length_until_eof(export_dir.AddressOfNameOrdinals),
                    export_dir.NumberOfNames * 4,
                ),
            )
            address_of_functions = self.get_data(
                export_dir.AddressOfFunctions,
                min(
                    length_until_eof(export_dir.AddressOfFunctions),
                    export_dir.NumberOfFunctions * 4,
                ),
            )
        except PEFormatError:
            self.__warnings.append(
                "Error parsing export directory at RVA: 0x%x" % (rva)
            )
            return

        exports = []

        max_failed_entries_before_giving_up = 10

        section = self.get_section_by_rva(export_dir.AddressOfNames)
        # 022681.python.pefile.line5320.comment Overly generous upper bound
        safety_boundary = len(self.__data__)
        if section:
            safety_boundary = (
                section.VirtualAddress
                + len(section.get_data())
                - export_dir.AddressOfNames
            )

        symbol_counts = collections.defaultdict(int)
        export_parsing_loop_completed_normally = True
        for i in range(min(export_dir.NumberOfNames, int(safety_boundary / 4))):
            symbol_ordinal = self.get_word_from_data(address_of_name_ordinals, i)

            if symbol_ordinal is not None and symbol_ordinal * 4 < len(
                address_of_functions
            ):
                symbol_address = self.get_dword_from_data(
                    address_of_functions, symbol_ordinal
                )
            else:
                # 022682.python.pefile.line5341.comment Corrupt? a bad pointer... we assume it's all
                # 022683.python.pefile.line5342.comment useless, no exports
                return None
            if symbol_address is None or symbol_address == 0:
                continue

            # 022684.python.pefile.line5347.comment If the function's RVA points within the export directory
            # 022685.python.pefile.line5348.comment it will point to a string with the forwarded symbol's string
            # 022686.python.pefile.line5349.comment instead of pointing the the function start address.
            if symbol_address >= rva and symbol_address < rva + size:
                forwarder_str = self.get_string_at_rva(symbol_address)
                try:
                    forwarder_offset = self.get_offset_from_rva(symbol_address)
                except PEFormatError:
                    continue
            else:
                if forwarded_only:
                    continue
                forwarder_str = None
                forwarder_offset = None

            symbol_name_address = self.get_dword_from_data(address_of_names, i)
            if symbol_name_address is None:
                max_failed_entries_before_giving_up -= 1
                if max_failed_entries_before_giving_up <= 0:
                    export_parsing_loop_completed_normally = False
                    break

            symbol_name = self.get_string_at_rva(
                symbol_name_address, MAX_SYMBOL_NAME_LENGTH
            )
            if not is_valid_function_name(symbol_name, relax_allowed_characters=True):
                export_parsing_loop_completed_normally = False
                break
            try:
                symbol_name_offset = self.get_offset_from_rva(symbol_name_address)
            except PEFormatError:
                max_failed_entries_before_giving_up -= 1
                if max_failed_entries_before_giving_up <= 0:
                    export_parsing_loop_completed_normally = False
                    break
                try:
                    symbol_name_offset = self.get_offset_from_rva(symbol_name_address)
                except PEFormatError:
                    max_failed_entries_before_giving_up -= 1
                    if max_failed_entries_before_giving_up <= 0:
                        export_parsing_loop_completed_normally = False
                        break
                    continue

            # 022687.python.pefile.line5391.comment File 0b1d3d3664915577ab9a32188d29bbf3542b86c7b9ce333e245496c3018819f1
            # 022688.python.pefile.line5392.comment was being parsed as potentially containing millions of exports.
            # 022689.python.pefile.line5393.comment Checking for duplicates addresses the issue.
            symbol_counts[(symbol_name, symbol_address)] += 1
            if symbol_counts[(symbol_name, symbol_address)] > 10:
                self.__warnings.append(
                    f"Export directory contains more than 10 repeated entries "
                    f"({symbol_name}, {symbol_address:#02x}). Assuming corrupt."
                )
                break
            elif len(symbol_counts) > self.max_symbol_exports:
                self.__warnings.append(
                    "Export directory contains more than {} symbol entries. "
                    "Assuming corrupt.".format(self.max_symbol_exports)
                )
                break

            exports.append(
                ExportData(
                    pe=self,
                    ordinal=export_dir.Base + symbol_ordinal,
                    ordinal_offset=self.get_offset_from_rva(
                        export_dir.AddressOfNameOrdinals + 2 * i
                    ),
                    address=symbol_address,
                    address_offset=self.get_offset_from_rva(
                        export_dir.AddressOfFunctions + 4 * symbol_ordinal
                    ),
                    name=symbol_name,
                    name_offset=symbol_name_offset,
                    forwarder=forwarder_str,
                    forwarder_offset=forwarder_offset,
                )
            )

        if not export_parsing_loop_completed_normally:
            self.__warnings.append(
                f"RVA AddressOfNames in the export directory points to an invalid "
                f"address: {export_dir.AddressOfNames:x}"
            )

        ordinals = {exp.ordinal for exp in exports}

        max_failed_entries_before_giving_up = 10

        section = self.get_section_by_rva(export_dir.AddressOfFunctions)
        # 022690.python.pefile.line5437.comment Overly generous upper bound
        safety_boundary = len(self.__data__)
        if section:
            safety_boundary = (
                section.VirtualAddress
                + len(section.get_data())
                - export_dir.AddressOfFunctions
            )

        symbol_counts = collections.defaultdict(int)
        export_parsing_loop_completed_normally = True
        for idx in range(min(export_dir.NumberOfFunctions, int(safety_boundary / 4))):

            if not idx + export_dir.Base in ordinals:
                try:
                    symbol_address = self.get_dword_from_data(address_of_functions, idx)
                except PEFormatError:
                    symbol_address = None

                if symbol_address is None:
                    max_failed_entries_before_giving_up -= 1
                    if max_failed_entries_before_giving_up <= 0:
                        export_parsing_loop_completed_normally = False
                        break

                if symbol_address == 0:
                    continue

                # 022691.python.pefile.line5465.comment Checking for forwarder again.
                if (
                    symbol_address is not None
                    and symbol_address >= rva
                    and symbol_address < rva + size
                ):
                    forwarder_str = self.get_string_at_rva(symbol_address)
                else:
                    forwarder_str = None

                # 022692.python.pefile.line5475.comment File 0b1d3d3664915577ab9a32188d29bbf3542b86c7b9ce333e245496c3018819f1
                # 022693.python.pefile.line5476.comment was being parsed as potentially containing millions of exports.
                # 022694.python.pefile.line5477.comment Checking for duplicates addresses the issue.
                symbol_counts[symbol_address] += 1
                if symbol_counts[symbol_address] > self.max_repeated_symbol:
                    # 022695.python.pefile.line5480.comment if most_common and most_common[0][1] > 10:
                    self.__warnings.append(
                        "Export directory contains more than {} repeated "
                        "ordinal entries (0x{:x}). Assuming corrupt.".format(
                            self.max_repeated_symbol, symbol_address
                        )
                    )
                    break
                elif len(symbol_counts) > self.max_symbol_exports:
                    self.__warnings.append(
                        "Export directory contains more than "
                        f"{self.max_symbol_exports} ordinal entries. Assuming corrupt."
                    )
                    break

                exports.append(
                    ExportData(
                        ordinal=export_dir.Base + idx,
                        address=symbol_address,
                        name=None,
                        forwarder=forwarder_str,
                    )
                )

        if not export_parsing_loop_completed_normally:
            self.__warnings.append(
                "RVA AddressOfFunctions in the export directory points to an invalid "
                f"address: {export_dir.AddressOfFunctions:x}"
            )
            return

        if not exports and export_dir.all_zeroes():
            return None
        return ExportDirData(
            struct=export_dir,
            symbols=exports,
            name=self.get_string_at_rva(export_dir.Name),
        )

    def dword_align(self, offset, base):
        return ((offset + base + 3) & 0xFFFFFFFC) - (base & 0xFFFFFFFC)

    def normalize_import_va(self, va):

        # 022696.python.pefile.line5524.comment Setup image range
        begin_of_image = self.OPTIONAL_HEADER.ImageBase
        end_of_image = self.OPTIONAL_HEADER.ImageBase + self.OPTIONAL_HEADER.SizeOfImage

        # 022697.python.pefile.line5528.comment Try to avoid bogus VAs, which are out of the image.
        # 022698.python.pefile.line5529.comment This also filters out entries that are zero
        if begin_of_image <= va and va < end_of_image:
            va -= begin_of_image
        return va

    def parse_delay_import_directory(self, rva, size):
        """Walk and parse the delay import directory."""

        import_descs = []
        error_count = 0
        while True:
            try:
                # 022699.python.pefile.line5541.comment If the RVA is invalid all would blow up. Some PEs seem to be
                # 022700.python.pefile.line5542.comment specially nasty and have an invalid RVA.
                data = self.get_data(
                    rva,
                    Structure(self.__IMAGE_DELAY_IMPORT_DESCRIPTOR_format__).sizeof(),
                )
            except PEFormatError:
                self.__warnings.append(
                    "Error parsing the Delay import directory at RVA: 0x%x" % (rva)
                )
                break

            file_offset = self.get_offset_from_rva(rva)
            import_desc = self.__unpack_data__(
                self.__IMAGE_DELAY_IMPORT_DESCRIPTOR_format__,
                data,
                file_offset=file_offset,
            )

            # 022701.python.pefile.line5560.comment If the structure is all zeros, we reached the end of the list
            if not import_desc or import_desc.all_zeroes():
                break
            contains_addresses = False

            # 022702.python.pefile.line5565.comment Handle old import descriptor that has Virtual Addresses instead of RVAs
            # 022703.python.pefile.line5566.comment This version of import descriptor is created by old Visual Studio versions
            # 022704.python.pefile.line5567.comment (pre 6.0)
            # 022705.python.pefile.line5568.comment Can only be present in 32-bit binaries (no 64-bit compiler existed at the
            # 022706.python.pefile.line5569.comment time)
            # 022707.python.pefile.line5570.comment Sample: e8d3bff0c1a9a6955993f7a441121a2692261421e82fdfadaaded45d3bea9980
            if (
                import_desc.grAttrs == 0
                and self.FILE_HEADER.Machine == MACHINE_TYPE["IMAGE_FILE_MACHINE_I386"]
            ):
                import_desc.pBoundIAT = self.normalize_import_va(import_desc.pBoundIAT)
                import_desc.pIAT = self.normalize_import_va(import_desc.pIAT)
                import_desc.pINT = self.normalize_import_va(import_desc.pINT)
                import_desc.pUnloadIAT = self.normalize_import_va(
                    import_desc.pUnloadIAT
                )
                import_desc.phmod = self.normalize_import_va(import_desc.pUnloadIAT)
                import_desc.szName = self.normalize_import_va(import_desc.szName)
                contains_addresses = True

            rva += import_desc.sizeof()

            # 022708.python.pefile.line5587.comment If the array of thunks is somewhere earlier than the import
            # 022709.python.pefile.line5588.comment descriptor we can set a maximum length for the array. Otherwise
            # 022710.python.pefile.line5589.comment just set a maximum length of the size of the file
            max_len = len(self.__data__) - file_offset
            if rva > import_desc.pINT or rva > import_desc.pIAT:
                max_len = max(rva - import_desc.pINT, rva - import_desc.pIAT)

            import_data = []
            try:
                import_data = self.parse_imports(
                    import_desc.pINT,
                    import_desc.pIAT,
                    None,
                    max_len,
                    contains_addresses,
                )
            except PEFormatError as excp:
                self.__warnings.append(
                    "Error parsing the Delay import directory. "
                    "Invalid import data at RVA: 0x{0:x} ({1})".format(rva, excp.value)
                )

            if error_count > 5:
                self.__warnings.append(
                    "Too many errors parsing the Delay import directory. "
                    "Invalid import data at RVA: 0x{0:x}".format(rva)
                )
                break

            if not import_data:
                error_count += 1
                continue

            if self.__total_import_symbols > MAX_IMPORT_SYMBOLS:
                self.__warnings.append(
                    "Error, too many imported symbols %d (>%s)"
                    % (self.__total_import_symbols, MAX_IMPORT_SYMBOLS)
                )
                break

            dll = self.get_string_at_rva(import_desc.szName, MAX_DLL_LENGTH)
            if not is_valid_dos_filename(dll):
                dll = b("*invalid*")

            if dll:
                for symbol in import_data:
                    if symbol.name is None:
                        funcname = ordlookup.ordLookup(dll.lower(), symbol.ordinal)
                        if funcname:
                            symbol.name = funcname
                import_descs.append(
                    ImportDescData(struct=import_desc, imports=import_data, dll=dll)
                )

        return import_descs

    def get_rich_header_hash(self, algorithm="md5"):
        if not hasattr(self, "RICH_HEADER") or self.RICH_HEADER is None:
            return ""

        if algorithm == "md5":
            return md5(self.RICH_HEADER.clear_data).hexdigest()
        elif algorithm == "sha1":
            return sha1(self.RICH_HEADER.clear_data).hexdigest()
        elif algorithm == "sha256":
            return sha256(self.RICH_HEADER.clear_data).hexdigest()
        elif algorithm == "sha512":
            return sha512(self.RICH_HEADER.clear_data).hexdigest()

        raise Exception("Invalid hashing algorithm specified")

    def get_imphash(self):
        """Return the imphash of the PE file.

        Creates a hash based on imported symbol names and their specific order within
        the executable:
        https://www.mandiant.com/resources/blog/tracking-malware-import-hashing

        Returns:
            the hexdigest of the MD5 hash of the exported symbols.
        """

        impstrs = []
        exts = ["ocx", "sys", "dll"]
        if not hasattr(self, "DIRECTORY_ENTRY_IMPORT"):
            return ""
        for entry in self.DIRECTORY_ENTRY_IMPORT:
            if isinstance(entry.dll, bytes):
                libname = entry.dll.decode().lower()
            else:
                libname = entry.dll.lower()
            parts = libname.rsplit(".", 1)

            if len(parts) > 1 and parts[1] in exts:
                libname = parts[0]

            entry_dll_lower = entry.dll.lower()
            for imp in entry.imports:
                funcname = None
                if not imp.name:
                    funcname = ordlookup.ordLookup(
                        entry_dll_lower, imp.ordinal, make_name=True
                    )
                    if not funcname:
                        raise PEFormatError(
                            f"Unable to look up ordinal {entry.dll}:{imp.ordinal:04x}"
                        )
                else:
                    funcname = imp.name

                if not funcname:
                    continue

                if isinstance(funcname, bytes):
                    funcname = funcname.decode()
                impstrs.append("%s.%s" % (libname.lower(), funcname.lower()))

        return md5(",".join(impstrs).encode()).hexdigest()

    def get_exphash(self):
        """Return the exphash of the PE file.

        Similar to imphash, but based on exported symbol names and their specific order.

        Returns:
            the hexdigest of the SHA256 hash of the exported symbols.
        """

        if not hasattr(self, "DIRECTORY_ENTRY_EXPORT"):
            return ""

        if not hasattr(self.DIRECTORY_ENTRY_EXPORT, "symbols"):
            return ""

        export_list = [
            e.name.decode().lower()
            for e in self.DIRECTORY_ENTRY_EXPORT.symbols
            if e and e.name is not None
        ]
        if len(export_list) == 0:
            return ""

        return sha256(",".join(export_list).encode()).hexdigest()

    def parse_import_directory(self, rva, size, dllnames_only=False):
        """Walk and parse the import directory."""

        import_descs = []
        error_count = 0
        image_import_descriptor_size = Structure(
            self.__IMAGE_IMPORT_DESCRIPTOR_format__
        ).sizeof()
        while True:
            try:
                # 022711.python.pefile.line5741.comment If the RVA is invalid all would blow up. Some EXEs seem to be
                # 022712.python.pefile.line5742.comment specially nasty and have an invalid RVA.
                data = self.get_data(rva, image_import_descriptor_size)
            except PEFormatError:
                self.__warnings.append(
                    f"Error parsing the import directory at RVA: 0x{rva:x}"
                )
                break

            file_offset = self.get_offset_from_rva(rva)
            import_desc = self.__unpack_data__(
                self.__IMAGE_IMPORT_DESCRIPTOR_format__, data, file_offset=file_offset
            )

            # 022713.python.pefile.line5755.comment If the structure is all zeros, we reached the end of the list
            if not import_desc or import_desc.all_zeroes():
                break

            rva += import_desc.sizeof()

            # 022714.python.pefile.line5761.comment If the array of thunks is somewhere earlier than the import
            # 022715.python.pefile.line5762.comment descriptor we can set a maximum length for the array. Otherwise
            # 022716.python.pefile.line5763.comment just set a maximum length of the size of the file
            max_len = len(self.__data__) - file_offset
            if rva > import_desc.OriginalFirstThunk or rva > import_desc.FirstThunk:
                max_len = max(
                    rva - import_desc.OriginalFirstThunk, rva - import_desc.FirstThunk
                )

            import_data = []
            if not dllnames_only:
                try:
                    import_data = self.parse_imports(
                        import_desc.OriginalFirstThunk,
                        import_desc.FirstThunk,
                        import_desc.ForwarderChain,
                        max_length=max_len,
                    )
                except PEFormatError as e:
                    self.__warnings.append(
                        "Error parsing the import directory. "
                        f"Invalid Import data at RVA: 0x{rva:x} ({e.value})"
                    )

                if error_count > 5:
                    self.__warnings.append(
                        "Too many errors parsing the import directory. "
                        f"Invalid import data at RVA: 0x{rva:x}"
                    )
                    break

                if not import_data:
                    error_count += 1
                    # 022717.python.pefile.line5794.comment TODO: do not continue here
                    continue

            dll = self.get_string_at_rva(import_desc.Name, MAX_DLL_LENGTH)
            if not is_valid_dos_filename(dll):
                dll = b("*invalid*")

            if dll:
                for symbol in import_data:
                    if symbol.name is None:
                        funcname = ordlookup.ordLookup(dll.lower(), symbol.ordinal)
                        if funcname:
                            symbol.name = funcname
                import_descs.append(
                    ImportDescData(struct=import_desc, imports=import_data, dll=dll)
                )

        if not dllnames_only:
            suspicious_imports = set(["LoadLibrary", "GetProcAddress"])
            suspicious_imports_count = 0
            total_symbols = 0
            for imp_dll in import_descs:
                for symbol in imp_dll.imports:
                    for suspicious_symbol in suspicious_imports:
                        if not symbol or not symbol.name:
                            continue
                        name = symbol.name
                        if type(symbol.name) == bytes:
                            name = symbol.name.decode("utf-8")
                        if name.startswith(suspicious_symbol):
                            suspicious_imports_count += 1
                            break
                    total_symbols += 1
            if (
                suspicious_imports_count == len(suspicious_imports)
                and total_symbols < 20
            ):
                self.__warnings.append(
                    "Imported symbols contain entries typical of packed executables."
                )

        return import_descs

    def parse_imports(
        self,
        original_first_thunk,
        first_thunk,
        forwarder_chain,
        max_length=None,
        contains_addresses=False,
    ):
        """Parse the imported symbols.

        It will fill a list, which will be available as the dictionary
        attribute "imports". Its keys will be the DLL names and the values
        of all the symbols imported from that object.
        """

        imported_symbols = []

        # 022718.python.pefile.line5854.comment Import Lookup Table. Contains ordinals or pointers to strings.
        ilt = self.get_import_table(
            original_first_thunk, max_length, contains_addresses
        )
        # 022719.python.pefile.line5858.comment Import Address Table. May have identical content to ILT if
        # 022720.python.pefile.line5859.comment PE file is not bound. It will contain the address of the
        # 022721.python.pefile.line5860.comment imported symbols once the binary is loaded or if it is already
        # 022722.python.pefile.line5861.comment bound.
        iat = self.get_import_table(first_thunk, max_length, contains_addresses)

        # 022723.python.pefile.line5864.comment OC Patch:
        # 022724.python.pefile.line5865.comment Would crash if IAT or ILT had None type
        if (not iat or len(iat) == 0) and (not ilt or len(ilt) == 0):
            self.__warnings.append(
                "Damaged Import Table information. "
                "ILT and/or IAT appear to be broken. "
                f"OriginalFirstThunk: 0x{original_first_thunk:x} "
                f"FirstThunk: 0x{first_thunk:x}"
            )
            return []

        table = None
        if ilt:
            table = ilt
        elif iat:
            table = iat
        else:
            return None

        imp_offset = 4
        address_mask = 0x7FFFFFFF
        if self.PE_TYPE == OPTIONAL_HEADER_MAGIC_PE:
            ordinal_flag = IMAGE_ORDINAL_FLAG
        elif self.PE_TYPE == OPTIONAL_HEADER_MAGIC_PE_PLUS:
            ordinal_flag = IMAGE_ORDINAL_FLAG64
            imp_offset = 8
            address_mask = 0x7FFFFFFFFFFFFFFF
        else:
            # 022725.python.pefile.line5892.comment Some PEs may have an invalid value in the Magic field of the
            # 022726.python.pefile.line5893.comment Optional Header. Just in case the remaining file is parseable
            # 022727.python.pefile.line5894.comment let's pretend it's a 32bit PE32 by default.
            ordinal_flag = IMAGE_ORDINAL_FLAG

        num_invalid = 0
        for idx, tbl_entry in enumerate(table):
            imp_ord = None
            imp_hint = None
            imp_name = None
            name_offset = None
            hint_name_table_rva = None
            import_by_ordinal = False  # declare it here first

            if tbl_entry.AddressOfData:
                # 022729.python.pefile.line5907.comment If imported by ordinal, we will append the ordinal number
                # 022730.python.pefile.line5908.comment
                if tbl_entry.AddressOfData & ordinal_flag:
                    import_by_ordinal = True
                    imp_ord = tbl_entry.AddressOfData & 0xFFFF
                    imp_name = None
                    name_offset = None
                else:
                    import_by_ordinal = False
                    try:
                        hint_name_table_rva = tbl_entry.AddressOfData & address_mask
                        data = self.get_data(hint_name_table_rva, 2)
                        # 022731.python.pefile.line5919.comment Get the Hint
                        imp_hint = self.get_word_from_data(data, 0)
                        imp_name = self.get_string_at_rva(
                            tbl_entry.AddressOfData + 2, MAX_IMPORT_NAME_LENGTH
                        )
                        if not is_valid_function_name(imp_name):
                            imp_name = b("*invalid*")

                        name_offset = self.get_offset_from_rva(
                            tbl_entry.AddressOfData + 2
                        )
                    except PEFormatError:
                        pass

                # 022732.python.pefile.line5933.comment by nriva: we want the ThunkRVA and ThunkOffset
                thunk_offset = tbl_entry.get_file_offset()
                thunk_rva = self.get_rva_from_offset(thunk_offset)

            imp_address = (
                first_thunk + self.OPTIONAL_HEADER.ImageBase + idx * imp_offset
            )

            struct_iat = None
            try:
                if iat and ilt and ilt[idx].AddressOfData != iat[idx].AddressOfData:
                    imp_bound = iat[idx].AddressOfData
                    struct_iat = iat[idx]
                else:
                    imp_bound = None
            except IndexError:
                imp_bound = None

            # 022733.python.pefile.line5951.comment The file with hashes:
            # 022734.python.pefile.line5952.comment
            # 022735.python.pefile.line5953.comment MD5: bfe97192e8107d52dd7b4010d12b2924
            # 022736.python.pefile.line5954.comment SHA256: 3d22f8b001423cb460811ab4f4789f277b35838d45c62ec0454c877e7c82c7f5
            # 022737.python.pefile.line5955.comment
            # 022738.python.pefile.line5956.comment has an invalid table built in a way that it's parseable but contains
            # 022739.python.pefile.line5957.comment invalid entries that lead pefile to take extremely long amounts of time to
            # 022740.python.pefile.line5958.comment parse. It also leads to extreme memory consumption.
            # 022741.python.pefile.line5959.comment To prevent similar cases, if invalid entries are found in the middle of a
            # 022742.python.pefile.line5960.comment table the parsing will be aborted
            # 022743.python.pefile.line5961.comment
            if imp_ord is None and imp_name is None:
                raise PEFormatError("Invalid entries, aborting parsing.")

            # 022744.python.pefile.line5965.comment Some PEs appear to interleave valid and invalid imports. Instead of
            # 022745.python.pefile.line5966.comment aborting the parsing altogether we will simply skip the invalid entries.
            # 022746.python.pefile.line5967.comment Although if we see 1000 invalid entries and no legit ones, we abort.
            if imp_name == b("*invalid*"):
                if num_invalid > 1000 and num_invalid == idx:
                    raise PEFormatError("Too many invalid names, aborting parsing.")
                num_invalid += 1
                continue

            if imp_ord or imp_name:
                imported_symbols.append(
                    ImportData(
                        pe=self,
                        struct_table=tbl_entry,
                        struct_iat=struct_iat,  # for bound imports if any
                        import_by_ordinal=import_by_ordinal,
                        ordinal=imp_ord,
                        ordinal_offset=tbl_entry.get_file_offset(),
                        hint=imp_hint,
                        name=imp_name,
                        name_offset=name_offset,
                        bound=imp_bound,
                        address=imp_address,
                        hint_name_table_rva=hint_name_table_rva,
                        thunk_offset=thunk_offset,
                        thunk_rva=thunk_rva,
                    )
                )

        return imported_symbols

    def get_import_table(self, rva, max_length=None, contains_addresses=False):

        table = []

        # 022748.python.pefile.line6000.comment We need the ordinal flag for a simple heuristic
        # 022749.python.pefile.line6001.comment we're implementing within the loop
        # 022750.python.pefile.line6002.comment
        if self.PE_TYPE == OPTIONAL_HEADER_MAGIC_PE:
            ordinal_flag = IMAGE_ORDINAL_FLAG
            format = self.__IMAGE_THUNK_DATA_format__
        elif self.PE_TYPE == OPTIONAL_HEADER_MAGIC_PE_PLUS:
            ordinal_flag = IMAGE_ORDINAL_FLAG64
            format = self.__IMAGE_THUNK_DATA64_format__
        else:
            # 022751.python.pefile.line6010.comment Some PEs may have an invalid value in the Magic field of the
            # 022752.python.pefile.line6011.comment Optional Header. Just in case the remaining file is parseable
            # 022753.python.pefile.line6012.comment let's pretend it's a 32bit PE32 by default.
            ordinal_flag = IMAGE_ORDINAL_FLAG
            format = self.__IMAGE_THUNK_DATA_format__

        expected_size = Structure(format).sizeof()
        MAX_ADDRESS_SPREAD = 128 * 2**20  # 128 MB
        ADDR_4GB = 2**32
        MAX_REPEATED_ADDRESSES = 15
        repeated_address = 0
        addresses_of_data_set_64 = AddressSet()
        addresses_of_data_set_32 = AddressSet()
        start_rva = rva
        while rva:
            if max_length is not None and rva >= start_rva + max_length:
                self.__warnings.append(
                    "Error parsing the import table. Entries go beyond bounds."
                )
                break
            # 022755.python.pefile.line6030.comment Enforce an upper bounds on import symbols.
            if self.__total_import_symbols > MAX_IMPORT_SYMBOLS:
                self.__warnings.append(
                    "Excessive number of imports %d (>%s)"
                    % (self.__total_import_symbols, MAX_IMPORT_SYMBOLS)
                )
                break

            self.__total_import_symbols += 1

            # 022756.python.pefile.line6040.comment if we see too many times the same entry we assume it could be
            # 022757.python.pefile.line6041.comment a table containing bogus data (with malicious intent or otherwise)
            if repeated_address >= MAX_REPEATED_ADDRESSES:
                return []

            # 022758.python.pefile.line6045.comment if the addresses point somewhere but the difference between the highest
            # 022759.python.pefile.line6046.comment and lowest address is larger than MAX_ADDRESS_SPREAD we assume a bogus
            # 022760.python.pefile.line6047.comment table as the addresses should be contained within a module
            if addresses_of_data_set_32.diff() > MAX_ADDRESS_SPREAD:
                return []
            if addresses_of_data_set_64.diff() > MAX_ADDRESS_SPREAD:
                return []

            failed = False
            try:
                data = self.get_data(rva, expected_size)
            except PEFormatError:
                failed = True

            if failed or len(data) != expected_size:
                self.__warnings.append(
                    "Error parsing the import table. " "Invalid data at RVA: 0x%x" % rva
                )
                return None

            thunk_data = self.__unpack_data__(
                format, data, file_offset=self.get_offset_from_rva(rva)
            )

            # 022761.python.pefile.line6069.comment If the thunk data contains VAs instead of RVAs, we need to normalize them
            if contains_addresses:
                thunk_data.AddressOfData = self.normalize_import_va(
                    thunk_data.AddressOfData
                )
                thunk_data.ForwarderString = self.normalize_import_va(
                    thunk_data.ForwarderString
                )
                thunk_data.Function = self.normalize_import_va(thunk_data.Function)
                thunk_data.Ordinal = self.normalize_import_va(thunk_data.Ordinal)

            # 022762.python.pefile.line6080.comment Check if the AddressOfData lies within the range of RVAs that it's
            # 022763.python.pefile.line6081.comment being scanned, abort if that is the case, as it is very unlikely
            # 022764.python.pefile.line6082.comment to be legitimate data.
            # 022765.python.pefile.line6083.comment Seen in PE with SHA256:
            # 022766.python.pefile.line6084.comment 5945bb6f0ac879ddf61b1c284f3b8d20c06b228e75ae4f571fa87f5b9512902c
            if (
                thunk_data
                and thunk_data.AddressOfData >= start_rva
                and thunk_data.AddressOfData <= rva
            ):
                self.__warnings.append(
                    "Error parsing the import table. "
                    "AddressOfData overlaps with THUNK_DATA for "
                    "THUNK at RVA 0x%x" % (rva)
                )
                break

            if thunk_data and thunk_data.AddressOfData:
                addr_of_data = thunk_data.AddressOfData
                # 022767.python.pefile.line6099.comment If the entry looks like could be an ordinal...
                if addr_of_data & ordinal_flag:
                    # 022768.python.pefile.line6101.comment but its value is beyond 2^16, we will assume it's a
                    # 022769.python.pefile.line6102.comment corrupted and ignore it altogether
                    if addr_of_data & 0x7FFFFFFF > 0xFFFF:
                        return []
                # 022770.python.pefile.line6105.comment and if it looks like it should be an RVA
                else:
                    # 022771.python.pefile.line6107.comment keep track of the RVAs seen and store them to study their
                    # 022772.python.pefile.line6108.comment properties. When certain non-standard features are detected
                    # 022773.python.pefile.line6109.comment the parsing will be aborted
                    if addr_of_data >= ADDR_4GB:
                        the_set = addresses_of_data_set_64
                    else:
                        the_set = addresses_of_data_set_32

                    if addr_of_data in the_set:
                        repeated_address += 1
                    the_set.add(addr_of_data)

            if not thunk_data or thunk_data.all_zeroes():
                break

            rva += thunk_data.sizeof()

            table.append(thunk_data)

        return table

    def get_memory_mapped_image(self, max_virtual_address=0x10000000, ImageBase=None):
        """Returns the data corresponding to the memory layout of the PE file.

        The data includes the PE header and the sections loaded at offsets
        corresponding to their relative virtual addresses. (the VirtualAddress
        section header member).
        Any offset in this data corresponds to the absolute memory address
        ImageBase+offset.

        The optional argument 'max_virtual_address' provides with means of limiting
        which sections are processed.
        Any section with their VirtualAddress beyond this value will be skipped.
        Normally, sections with values beyond this range are just there to confuse
        tools. It's a common trick to see in packed executables.

        If the 'ImageBase' optional argument is supplied, the file's relocations
        will be applied to the image by calling the 'relocate_image()' method. Beware
        that the relocation information is applied permanently.
        """

        # 022774.python.pefile.line6148.comment Rebase if requested
        # 022775.python.pefile.line6149.comment
        if ImageBase is not None:

            # 022776.python.pefile.line6152.comment Keep a copy of the image's data before modifying it by rebasing it
            # 022777.python.pefile.line6153.comment
            original_data = self.__data__

            self.relocate_image(ImageBase)

        # 022778.python.pefile.line6158.comment Collect all sections in one code block
        mapped_data = self.__data__[:]
        for section in self.sections:

            # 022779.python.pefile.line6162.comment Miscellaneous integrity tests.
            # 022780.python.pefile.line6163.comment Some packer will set these to bogus values to make tools go nuts.
            if section.Misc_VirtualSize == 0 and section.SizeOfRawData == 0:
                continue

            srd = section.SizeOfRawData
            prd = self.adjust_FileAlignment(
                section.PointerToRawData, self.OPTIONAL_HEADER.FileAlignment
            )
            VirtualAddress_adj = self.adjust_SectionAlignment(
                section.VirtualAddress,
                self.OPTIONAL_HEADER.SectionAlignment,
                self.OPTIONAL_HEADER.FileAlignment,
            )

            if (
                srd > len(self.__data__)
                or prd > len(self.__data__)
                or srd + prd > len(self.__data__)
                or VirtualAddress_adj >= max_virtual_address
            ):
                continue

            padding_length = VirtualAddress_adj - len(mapped_data)

            if padding_length > 0:
                mapped_data += b"\0" * padding_length
            elif padding_length < 0:
                mapped_data = mapped_data[:padding_length]

            mapped_data += section.get_data()

        # 022781.python.pefile.line6194.comment If the image was rebased, restore it to its original form
        # 022782.python.pefile.line6195.comment
        if ImageBase is not None:
            self.__data__ = original_data

        return mapped_data

    def get_resources_strings(self):
        """Returns a list of all the strings found withing the resources (if any).

        This method will scan all entries in the resources directory of the PE, if
        there is one, and will return a [] with the strings.

        An empty list will be returned otherwise.
        """

        resources_strings = []

        if hasattr(self, "DIRECTORY_ENTRY_RESOURCE"):

            for res_type in self.DIRECTORY_ENTRY_RESOURCE.entries:
                if hasattr(res_type, "directory"):
                    for resource_id in res_type.directory.entries:
                        if hasattr(resource_id, "directory"):
                            if (
                                hasattr(resource_id.directory, "strings")
                                and resource_id.directory.strings
                            ):
                                for res_string in list(
                                    resource_id.directory.strings.values()
                                ):
                                    resources_strings.append(res_string)

        return resources_strings

    def get_data(self, rva=0, length=None):
        """Get data regardless of the section where it lies on.

        Given a RVA and the size of the chunk to retrieve, this method
        will find the section where the data lies and return the data.
        """

        s = self.get_section_by_rva(rva)

        if length:
            end = rva + length
        else:
            end = None

        if not s:
            if rva < len(self.header):
                return self.header[rva:end]

            # 022783.python.pefile.line6247.comment Before we give up we check whether the file might
            # 022784.python.pefile.line6248.comment contain the data anyway. There are cases of PE files
            # 022785.python.pefile.line6249.comment without sections that rely on windows loading the first
            # 022786.python.pefile.line6250.comment 8291 bytes into memory and assume the data will be
            # 022787.python.pefile.line6251.comment there
            # 022788.python.pefile.line6252.comment A functional file with these characteristics is:
            # 022789.python.pefile.line6253.comment MD5: 0008892cdfbc3bda5ce047c565e52295
            # 022790.python.pefile.line6254.comment SHA-1: c7116b9ff950f86af256defb95b5d4859d4752a9
            # 022791.python.pefile.line6255.comment
            if rva < len(self.__data__):
                return self.__data__[rva:end]

            raise PEFormatError("data at RVA can't be fetched. Corrupt header?")

        return s.get_data(rva, length)

    def get_rva_from_offset(self, offset):
        """Get the RVA corresponding to this file offset."""

        s = self.get_section_by_offset(offset)
        if not s:
            if self.sections:
                lowest_rva = min(
                    [
                        self.adjust_SectionAlignment(
                            s.VirtualAddress,
                            self.OPTIONAL_HEADER.SectionAlignment,
                            self.OPTIONAL_HEADER.FileAlignment,
                        )
                        for s in self.sections
                    ]
                )
                if offset < lowest_rva:
                    # 022792.python.pefile.line6280.comment We will assume that the offset lies within the headers, or
                    # 022793.python.pefile.line6281.comment at least points before where the earliest section starts
                    # 022794.python.pefile.line6282.comment and we will simply return the offset as the RVA
                    # 022795.python.pefile.line6283.comment
                    # 022796.python.pefile.line6284.comment The case illustrating this behavior can be found at:
                    # 022797.python.pefile.line6285.comment http://corkami.blogspot.com/2010/01/hey-hey-hey-whats-in-your-head.html
                    # 022798.python.pefile.line6286.comment where the import table is not contained by any section
                    # 022799.python.pefile.line6287.comment hence the RVA needs to be resolved to a raw offset
                    return offset
                return None
            else:
                return offset
        return s.get_rva_from_offset(offset)

    def get_offset_from_rva(self, rva):
        """Get the file offset corresponding to this RVA.

        Given a RVA , this method will find the section where the
        data lies and return the offset within the file.
        """

        s = self.get_section_by_rva(rva)
        if not s:

            # 022800.python.pefile.line6304.comment If not found within a section assume it might
            # 022801.python.pefile.line6305.comment point to overlay data or otherwise data present
            # 022802.python.pefile.line6306.comment but not contained in any section. In those
            # 022803.python.pefile.line6307.comment cases the RVA should equal the offset
            if rva < len(self.__data__):
                return rva

            raise PEFormatError(f"data at RVA 0x{rva:x} can't be fetched")

        return s.get_offset_from_rva(rva)

    def get_string_at_rva(self, rva, max_length=MAX_STRING_LENGTH):
        """Get an ASCII string located at the given address."""

        if rva is None:
            return None

        s = self.get_section_by_rva(rva)
        if not s:
            return self.get_string_from_data(0, self.__data__[rva : rva + max_length])
        return self.get_string_from_data(0, s.get_data(rva, length=max_length))

    def get_bytes_from_data(self, offset, data):
        """."""
        if offset > len(data):
            return b""
        d = data[offset:]
        if isinstance(d, bytearray):
            return bytes(d)
        return d

    def get_string_from_data(self, offset, data):
        """Get an ASCII string from data."""
        s = self.get_bytes_from_data(offset, data)
        end = s.find(b"\0")
        if end >= 0:
            s = s[:end]
        return s

    def get_string_u_at_rva(self, rva, max_length=2**16, encoding=None):
        """Get an Unicode string located at the given address."""

        if max_length == 0:
            return b""

        # 022804.python.pefile.line6349.comment If the RVA is invalid let the exception reach the callers. All
        # 022805.python.pefile.line6350.comment call-sites of get_string_u_at_rva() will handle it.
        data = self.get_data(rva, 2)
        # 022806.python.pefile.line6352.comment max_length is the maximum count of 16bit characters needs to be
        # 022807.python.pefile.line6353.comment doubled to get size in bytes
        max_length <<= 1

        requested = min(max_length, 256)
        data = self.get_data(rva, requested)
        # 022808.python.pefile.line6358.comment try to find null-termination
        null_index = -1
        while True:
            null_index = data.find(b"\x00\x00", null_index + 1)
            if null_index == -1:
                data_length = len(data)
                if data_length < requested or data_length == max_length:
                    null_index = len(data) >> 1
                    break

                # 022809.python.pefile.line6368.comment Request remaining part of data limited by max_length
                data += self.get_data(rva + data_length, max_length - data_length)
                null_index = requested - 1
                requested = max_length

            elif null_index % 2 == 0:
                null_index >>= 1
                break

        # 022810.python.pefile.line6377.comment convert selected part of the string to unicode
        uchrs = struct.unpack("<{:d}H".format(null_index), data[: null_index * 2])
        s = "".join(map(chr, uchrs))

        if encoding:
            return b(s.encode(encoding, "backslashreplace_"))

        return b(s.encode("utf-8", "backslashreplace_"))

    def get_section_by_offset(self, offset):
        """Get the section containing the given file offset."""

        for section in self.sections:
            if section.contains_offset(offset):
                return section

        return None

    def get_section_by_rva(self, rva):
        """Get the section containing the given address."""

        # 022811.python.pefile.line6398.comment if we look a lot of times at RVA in the same section, "cache" the last used section
        # 022812.python.pefile.line6399.comment to speedup lookups (very useful when parsing import table)
        if self._get_section_by_rva_last_used is not None:
            if self._get_section_by_rva_last_used.contains_rva(rva):
                return self._get_section_by_rva_last_used

        for section in self.sections:
            if section.contains_rva(rva):
                self._get_section_by_rva_last_used = section
                return section

        return None

    def __str__(self):
        return self.dump_info()

    def has_relocs(self):
        """Checks if the PE file has relocation directory"""
        return hasattr(self, "DIRECTORY_ENTRY_BASERELOC")

    def has_dynamic_relocs(self):
        if hasattr(self, "DIRECTORY_ENTRY_LOAD_CONFIG"):
            if self.DIRECTORY_ENTRY_LOAD_CONFIG.dynamic_relocations:
                return True

        return False

    def print_info(self, encoding="utf-8"):
        """Print all the PE header information in a human readable from."""
        print(self.dump_info(encoding=encoding))

    def dump_info(self, dump=None, encoding="ascii"):
        """Dump all the PE header information into human readable string."""

        if dump is None:
            dump = Dump()

        warnings = self.get_warnings()
        if warnings:
            dump.add_header("Parsing Warnings")
            for warning in warnings:
                dump.add_line(warning)
                dump.add_newline()

        dump.add_header("DOS_HEADER")
        dump.add_lines(self.DOS_HEADER.dump())
        dump.add_newline()

        dump.add_header("NT_HEADERS")
        dump.add_lines(self.NT_HEADERS.dump())
        dump.add_newline()

        dump.add_header("FILE_HEADER")
        dump.add_lines(self.FILE_HEADER.dump())

        image_flags = retrieve_flags(IMAGE_CHARACTERISTICS, "IMAGE_FILE_")

        dump.add("Flags: ")
        flags = []
        for flag in sorted(image_flags):
            if getattr(self.FILE_HEADER, flag[0]):
                flags.append(flag[0])
        dump.add_line(", ".join(flags))
        dump.add_newline()

        if hasattr(self, "OPTIONAL_HEADER") and self.OPTIONAL_HEADER is not None:
            dump.add_header("OPTIONAL_HEADER")
            dump.add_lines(self.OPTIONAL_HEADER.dump())

        dll_characteristics_flags = retrieve_flags(
            DLL_CHARACTERISTICS, "IMAGE_DLLCHARACTERISTICS_"
        )

        dump.add("DllCharacteristics: ")
        flags = []
        for flag in sorted(dll_characteristics_flags):
            if getattr(self.OPTIONAL_HEADER, flag[0]):
                flags.append(flag[0])
        dump.add_line(", ".join(flags))
        dump.add_newline()

        dump.add_header("PE Sections")

        section_flags = retrieve_flags(SECTION_CHARACTERISTICS, "IMAGE_SCN_")

        for section in self.sections:
            dump.add_lines(section.dump())
            dump.add("Flags: ")
            flags = []
            for flag in sorted(section_flags):
                if getattr(section, flag[0]):
                    flags.append(flag[0])
            dump.add_line(", ".join(flags))
            dump.add_line(
                "Entropy: {0:f} (Min=0.0, Max=8.0)".format(section.get_entropy())
            )
            if md5 is not None:
                dump.add_line("MD5     hash: {0}".format(section.get_hash_md5()))
            if sha1 is not None:
                dump.add_line("SHA-1   hash: %s" % section.get_hash_sha1())
            if sha256 is not None:
                dump.add_line("SHA-256 hash: %s" % section.get_hash_sha256())
            if sha512 is not None:
                dump.add_line("SHA-512 hash: %s" % section.get_hash_sha512())
            dump.add_newline()

        if hasattr(self, "OPTIONAL_HEADER") and hasattr(
            self.OPTIONAL_HEADER, "DATA_DIRECTORY"
        ):

            dump.add_header("Directories")
            for directory in self.OPTIONAL_HEADER.DATA_DIRECTORY:
                if directory is not None:
                    dump.add_lines(directory.dump())
            dump.add_newline()

        if hasattr(self, "VS_VERSIONINFO"):
            for idx, vinfo_entry in enumerate(self.VS_VERSIONINFO):
                if len(self.VS_VERSIONINFO) > 1:
                    dump.add_header(f"Version Information {idx + 1}")
                else:
                    dump.add_header("Version Information")
                if vinfo_entry is not None:
                    dump.add_lines(vinfo_entry.dump())
                dump.add_newline()

                if hasattr(self, "VS_FIXEDFILEINFO"):
                    dump.add_lines(self.VS_FIXEDFILEINFO[idx].dump())
                    dump.add_newline()

                if hasattr(self, "FileInfo") and len(self.FileInfo) > idx:
                    for entry in self.FileInfo[idx]:
                        dump.add_lines(entry.dump())
                        dump.add_newline()

                        if hasattr(entry, "StringTable"):
                            for st_entry in entry.StringTable:
                                [dump.add_line("  " + line) for line in st_entry.dump()]
                                dump.add_line(
                                    "  LangID: {0}".format(
                                        st_entry.LangID.decode(
                                            encoding, "backslashreplace_"
                                        )
                                    )
                                )
                                dump.add_newline()
                                for str_entry in sorted(list(st_entry.entries.items())):
                                    # 022813.python.pefile.line6545.comment try:
                                    dump.add_line(
                                        "    {0}: {1}".format(
                                            str_entry[0].decode(
                                                encoding, "backslashreplace_"
                                            ),
                                            str_entry[1].decode(
                                                encoding, "backslashreplace_"
                                            ),
                                        )
                                    )

                            dump.add_newline()

                        elif hasattr(entry, "Var"):
                            for var_entry in entry.Var:
                                if hasattr(var_entry, "entry"):
                                    [
                                        dump.add_line("  " + line)
                                        for line in var_entry.dump()
                                    ]
                                    dump.add_line(
                                        "    {0}: {1}".format(
                                            list(var_entry.entry.keys())[0].decode(
                                                "utf-8", "backslashreplace_"
                                            ),
                                            list(var_entry.entry.values())[0],
                                        )
                                    )

                            dump.add_newline()

        if hasattr(self, "DIRECTORY_ENTRY_EXPORT"):
            dump.add_header("Exported symbols")
            dump.add_lines(self.DIRECTORY_ENTRY_EXPORT.struct.dump())
            dump.add_newline()
            dump.add_line("%-10s   %-10s  %s" % ("Ordinal", "RVA", "Name"))
            for export in self.DIRECTORY_ENTRY_EXPORT.symbols:
                if export.address is not None:
                    name = b("None")
                    if export.name:
                        name = export.name
                    dump.add(
                        "%-10d 0x%08X    %s"
                        % (export.ordinal, export.address, name.decode(encoding))
                    )
                    if export.forwarder:
                        dump.add_line(
                            " forwarder: {0}".format(
                                export.forwarder.decode(encoding, "backslashreplace_")
                            )
                        )
                    else:
                        dump.add_newline()

            dump.add_newline()

        if hasattr(self, "DIRECTORY_ENTRY_IMPORT"):
            dump.add_header("Imported symbols")
            for module in self.DIRECTORY_ENTRY_IMPORT:
                dump.add_lines(module.struct.dump())
                # 022814.python.pefile.line6606.comment Print the name of the DLL if there are no imports.
                if not module.imports:
                    dump.add(
                        "  Name -> {0}".format(
                            self.get_string_at_rva(module.struct.Name).decode(
                                encoding, "backslashreplace_"
                            )
                        )
                    )
                    dump.add_newline()
                dump.add_newline()
                for symbol in module.imports:
                    if symbol.import_by_ordinal is True:
                        if symbol.name is not None:
                            dump.add(
                                "{0}.{1} Ordinal[{2}] (Imported by Ordinal)".format(
                                    module.dll.decode("utf-8"),
                                    symbol.name.decode("utf-8"),
                                    symbol.ordinal,
                                )
                            )
                        else:
                            dump.add(
                                "{0} Ordinal[{1}] (Imported by Ordinal)".format(
                                    module.dll.decode("utf-8"), symbol.ordinal
                                )
                            )
                    else:
                        dump.add(
                            "{0}.{1} Hint[{2:d}]".format(
                                module.dll.decode(encoding, "backslashreplace_"),
                                symbol.name.decode(encoding, "backslashreplace_"),
                                symbol.hint,
                            )
                        )

                    if symbol.bound:
                        dump.add_line(" Bound: 0x{0:08X}".format(symbol.bound))
                    else:
                        dump.add_newline()
                dump.add_newline()

        if hasattr(self, "DIRECTORY_ENTRY_BOUND_IMPORT"):
            dump.add_header("Bound imports")
            for bound_imp_desc in self.DIRECTORY_ENTRY_BOUND_IMPORT:

                dump.add_lines(bound_imp_desc.struct.dump())
                dump.add_line(
                    "DLL: {0}".format(
                        bound_imp_desc.name.decode(encoding, "backslashreplace_")
                    )
                )
                dump.add_newline()

                for bound_imp_ref in bound_imp_desc.entries:
                    dump.add_lines(bound_imp_ref.struct.dump(), 4)
                    dump.add_line(
                        "DLL: {0}".format(
                            bound_imp_ref.name.decode(encoding, "backslashreplace_")
                        ),
                        4,
                    )
                    dump.add_newline()

        if hasattr(self, "DIRECTORY_ENTRY_DELAY_IMPORT"):
            dump.add_header("Delay Imported symbols")
            for module in self.DIRECTORY_ENTRY_DELAY_IMPORT:

                dump.add_lines(module.struct.dump())
                dump.add_newline()

                for symbol in module.imports:
                    if symbol.import_by_ordinal is True:
                        dump.add(
                            "{0} Ordinal[{1:d}] (Imported by Ordinal)".format(
                                module.dll.decode(encoding, "backslashreplace_"),
                                symbol.ordinal,
                            )
                        )
                    else:
                        dump.add(
                            "{0}.{1} Hint[{2}]".format(
                                module.dll.decode(encoding, "backslashreplace_"),
                                symbol.name.decode(encoding, "backslashreplace_"),
                                symbol.hint,
                            )
                        )

                    if symbol.bound:
                        dump.add_line(" Bound: 0x{0:08X}".format(symbol.bound))
                    else:
                        dump.add_newline()
                dump.add_newline()

        if hasattr(self, "DIRECTORY_ENTRY_RESOURCE"):
            dump.add_header("Resource directory")

            dump.add_lines(self.DIRECTORY_ENTRY_RESOURCE.struct.dump())

            for res_type in self.DIRECTORY_ENTRY_RESOURCE.entries:

                if res_type.name is not None:
                    name = res_type.name.decode(encoding, "backslashreplace_")
                    dump.add_line(
                        f"Name: [{name}]",
                        2,
                    )
                else:
                    res_type_id = RESOURCE_TYPE.get(res_type.struct.Id, "-")
                    dump.add_line(
                        f"Id: [0x{res_type.struct.Id:X}] ({res_type_id})",
                        2,
                    )

                dump.add_lines(res_type.struct.dump(), 2)

                if hasattr(res_type, "directory"):

                    dump.add_lines(res_type.directory.struct.dump(), 4)

                    for resource_id in res_type.directory.entries:

                        if resource_id.name is not None:
                            name = resource_id.name.decode("utf-8", "backslashreplace_")
                            dump.add_line(
                                f"Name: [{name}]",
                                6,
                            )
                        else:
                            dump.add_line(f"Id: [0x{resource_id.struct.Id:X}]", 6)

                        dump.add_lines(resource_id.struct.dump(), 6)

                        if hasattr(resource_id, "directory"):
                            dump.add_lines(resource_id.directory.struct.dump(), 8)

                            for resource_lang in resource_id.directory.entries:
                                if hasattr(resource_lang, "data"):
                                    dump.add_line(
                                        "\\--- LANG [%d,%d][%s,%s]"
                                        % (
                                            resource_lang.data.lang,
                                            resource_lang.data.sublang,
                                            LANG.get(
                                                resource_lang.data.lang, "*unknown*"
                                            ),
                                            get_sublang_name_for_lang(
                                                resource_lang.data.lang,
                                                resource_lang.data.sublang,
                                            ),
                                        ),
                                        8,
                                    )
                                    dump.add_lines(resource_lang.struct.dump(), 10)
                                    dump.add_lines(resource_lang.data.struct.dump(), 12)
                            if (
                                hasattr(resource_id.directory, "strings")
                                and resource_id.directory.strings
                            ):
                                dump.add_line("[STRINGS]", 10)
                                for idx, res_string in list(
                                    sorted(resource_id.directory.strings.items())
                                ):
                                    dump.add_line(
                                        "{0:6d}: {1}".format(
                                            idx,
                                            res_string.encode(
                                                "unicode-escape", "backslashreplace"
                                            ).decode("ascii"),
                                        ),
                                        12,
                                    )

                dump.add_newline()

            dump.add_newline()

        if (
            hasattr(self, "DIRECTORY_ENTRY_TLS")
            and self.DIRECTORY_ENTRY_TLS
            and self.DIRECTORY_ENTRY_TLS.struct
        ):

            dump.add_header("TLS")
            dump.add_lines(self.DIRECTORY_ENTRY_TLS.struct.dump())
            dump.add_newline()

        if (
            hasattr(self, "DIRECTORY_ENTRY_LOAD_CONFIG")
            and self.DIRECTORY_ENTRY_LOAD_CONFIG
            and self.DIRECTORY_ENTRY_LOAD_CONFIG.struct
        ):

            dump.add_header("LOAD_CONFIG")
            dump.add_lines(self.DIRECTORY_ENTRY_LOAD_CONFIG.struct.dump())
            dump.add_newline()

        if hasattr(self, "DIRECTORY_ENTRY_DEBUG"):
            dump.add_header("Debug information")
            for dbg in self.DIRECTORY_ENTRY_DEBUG:
                dump.add_lines(dbg.struct.dump())
                try:
                    dump.add_line("Type: " + DEBUG_TYPE[dbg.struct.Type])
                except KeyError:
                    dump.add_line("Type: 0x{0:x}(Unknown)".format(dbg.struct.Type))
                dump.add_newline()
                if dbg.entry:
                    dump.add_lines(dbg.entry.dump(), 4)
                    dump.add_newline()

        if self.has_relocs():
            dump.add_header("Base relocations")
            for base_reloc in self.DIRECTORY_ENTRY_BASERELOC:
                dump.add_lines(base_reloc.struct.dump())
                for reloc in base_reloc.entries:
                    try:
                        dump.add_line(
                            "%08Xh %s" % (reloc.rva, RELOCATION_TYPE[reloc.type][16:]),
                            4,
                        )
                    except KeyError:
                        dump.add_line(
                            "0x%08X 0x%x(Unknown)" % (reloc.rva, reloc.type), 4
                        )
                dump.add_newline()

        if (
            hasattr(self, "DIRECTORY_ENTRY_EXCEPTION")
            and len(self.DIRECTORY_ENTRY_EXCEPTION) > 0
        ):
            dump.add_header("Unwind data for exception handling")
            for rf in self.DIRECTORY_ENTRY_EXCEPTION:
                dump.add_lines(rf.struct.dump())
                if hasattr(rf, "unwindinfo") and rf.unwindinfo is not None:
                    dump.add_lines(rf.unwindinfo.dump(), 4)

        return dump.get_text()

    def dump_dict(self):
        """Dump all the PE header information into a dictionary."""

        dump_dict = {}

        warnings = self.get_warnings()
        if warnings:
            dump_dict["Parsing Warnings"] = warnings

        dump_dict["DOS_HEADER"] = self.DOS_HEADER.dump_dict()
        dump_dict["NT_HEADERS"] = self.NT_HEADERS.dump_dict()
        dump_dict["FILE_HEADER"] = self.FILE_HEADER.dump_dict()

        image_flags = retrieve_flags(IMAGE_CHARACTERISTICS, "IMAGE_FILE_")

        dump_dict["Flags"] = []
        for flag in image_flags:
            if getattr(self.FILE_HEADER, flag[0]):
                dump_dict["Flags"].append(flag[0])

        if hasattr(self, "OPTIONAL_HEADER") and self.OPTIONAL_HEADER is not None:
            dump_dict["OPTIONAL_HEADER"] = self.OPTIONAL_HEADER.dump_dict()

        dll_characteristics_flags = retrieve_flags(
            DLL_CHARACTERISTICS, "IMAGE_DLLCHARACTERISTICS_"
        )

        dump_dict["DllCharacteristics"] = []
        for flag in dll_characteristics_flags:
            if getattr(self.OPTIONAL_HEADER, flag[0]):
                dump_dict["DllCharacteristics"].append(flag[0])

        dump_dict["PE Sections"] = []

        section_flags = retrieve_flags(SECTION_CHARACTERISTICS, "IMAGE_SCN_")
        for section in self.sections:
            section_dict = section.dump_dict()
            dump_dict["PE Sections"].append(section_dict)
            section_dict["Flags"] = []
            for flag in section_flags:
                if getattr(section, flag[0]):
                    section_dict["Flags"].append(flag[0])

            section_dict["Entropy"] = section.get_entropy()
            if md5 is not None:
                section_dict["MD5"] = section.get_hash_md5()
            if sha1 is not None:
                section_dict["SHA1"] = section.get_hash_sha1()
            if sha256 is not None:
                section_dict["SHA256"] = section.get_hash_sha256()
            if sha512 is not None:
                section_dict["SHA512"] = section.get_hash_sha512()

        if hasattr(self, "OPTIONAL_HEADER") and hasattr(
            self.OPTIONAL_HEADER, "DATA_DIRECTORY"
        ):

            dump_dict["Directories"] = []

            for idx, directory in enumerate(self.OPTIONAL_HEADER.DATA_DIRECTORY):
                if directory is not None:
                    dump_dict["Directories"].append(directory.dump_dict())

        if hasattr(self, "VS_VERSIONINFO"):
            dump_dict["Version Information"] = []
            for idx, vs_vinfo in enumerate(self.VS_VERSIONINFO):
                version_info_list = []
                version_info_list.append(vs_vinfo.dump_dict())

                if hasattr(self, "VS_FIXEDFILEINFO"):
                    version_info_list.append(self.VS_FIXEDFILEINFO[idx].dump_dict())

                if hasattr(self, "FileInfo") and len(self.FileInfo) > idx:
                    fileinfo_list = []
                    version_info_list.append(fileinfo_list)
                    for entry in self.FileInfo[idx]:
                        fileinfo_list.append(entry.dump_dict())

                        if hasattr(entry, "StringTable"):
                            stringtable_dict = {}
                            for st_entry in entry.StringTable:
                                fileinfo_list.extend(st_entry.dump_dict())
                                stringtable_dict["LangID"] = st_entry.LangID
                                for str_entry in list(st_entry.entries.items()):
                                    stringtable_dict[str_entry[0]] = str_entry[1]
                            fileinfo_list.append(stringtable_dict)

                        elif hasattr(entry, "Var"):
                            for var_entry in entry.Var:
                                var_dict = {}
                                if hasattr(var_entry, "entry"):
                                    fileinfo_list.extend(var_entry.dump_dict())
                                    var_dict[list(var_entry.entry.keys())[0]] = list(
                                        var_entry.entry.values()
                                    )[0]
                                    fileinfo_list.append(var_dict)

                dump_dict["Version Information"].append(version_info_list)

        if hasattr(self, "DIRECTORY_ENTRY_EXPORT"):
            dump_dict["Exported symbols"] = []
            dump_dict["Exported symbols"].append(
                self.DIRECTORY_ENTRY_EXPORT.struct.dump_dict()
            )
            for export in self.DIRECTORY_ENTRY_EXPORT.symbols:
                export_dict = {}
                if export.address is not None:
                    export_dict.update(
                        {
                            "Ordinal": export.ordinal,
                            "RVA": export.address,
                            "Name": export.name,
                        }
                    )
                    if export.forwarder:
                        export_dict["forwarder"] = export.forwarder
                dump_dict["Exported symbols"].append(export_dict)

        if hasattr(self, "DIRECTORY_ENTRY_IMPORT"):
            dump_dict["Imported symbols"] = []
            for module in self.DIRECTORY_ENTRY_IMPORT:
                import_list = []
                dump_dict["Imported symbols"].append(import_list)
                import_list.append(module.struct.dump_dict())
                for symbol in module.imports:
                    symbol_dict = {}
                    if symbol.import_by_ordinal is True:
                        symbol_dict["DLL"] = module.dll
                        symbol_dict["Ordinal"] = symbol.ordinal
                    else:
                        symbol_dict["DLL"] = module.dll
                        symbol_dict["Name"] = symbol.name
                        symbol_dict["Hint"] = symbol.hint

                    if symbol.bound:
                        symbol_dict["Bound"] = symbol.bound
                    import_list.append(symbol_dict)

        if hasattr(self, "DIRECTORY_ENTRY_BOUND_IMPORT"):
            dump_dict["Bound imports"] = []
            for bound_imp_desc in self.DIRECTORY_ENTRY_BOUND_IMPORT:
                bound_imp_desc_dict = {}
                dump_dict["Bound imports"].append(bound_imp_desc_dict)

                bound_imp_desc_dict.update(bound_imp_desc.struct.dump_dict())
                bound_imp_desc_dict["DLL"] = bound_imp_desc.name

                for bound_imp_ref in bound_imp_desc.entries:
                    bound_imp_ref_dict = {}
                    bound_imp_ref_dict.update(bound_imp_ref.struct.dump_dict())
                    bound_imp_ref_dict["DLL"] = bound_imp_ref.name

        if hasattr(self, "DIRECTORY_ENTRY_DELAY_IMPORT"):
            dump_dict["Delay Imported symbols"] = []
            for module in self.DIRECTORY_ENTRY_DELAY_IMPORT:
                module_list = []
                dump_dict["Delay Imported symbols"].append(module_list)
                module_list.append(module.struct.dump_dict())

                for symbol in module.imports:
                    symbol_dict = {}
                    if symbol.import_by_ordinal is True:
                        symbol_dict["DLL"] = module.dll
                        symbol_dict["Ordinal"] = symbol.ordinal
                    else:
                        symbol_dict["DLL"] = module.dll
                        symbol_dict["Name"] = symbol.name
                        symbol_dict["Hint"] = symbol.hint

                    if symbol.bound:
                        symbol_dict["Bound"] = symbol.bound
                    module_list.append(symbol_dict)

        if hasattr(self, "DIRECTORY_ENTRY_RESOURCE"):
            dump_dict["Resource directory"] = []
            dump_dict["Resource directory"].append(
                self.DIRECTORY_ENTRY_RESOURCE.struct.dump_dict()
            )

            for res_type in self.DIRECTORY_ENTRY_RESOURCE.entries:
                resource_type_dict = {}

                if res_type.name is not None:
                    resource_type_dict["Name"] = res_type.name
                else:
                    resource_type_dict["Id"] = (
                        res_type.struct.Id,
                        RESOURCE_TYPE.get(res_type.struct.Id, "-"),
                    )

                resource_type_dict.update(res_type.struct.dump_dict())
                dump_dict["Resource directory"].append(resource_type_dict)

                if hasattr(res_type, "directory"):
                    directory_list = []
                    directory_list.append(res_type.directory.struct.dump_dict())
                    dump_dict["Resource directory"].append(directory_list)

                    for resource_id in res_type.directory.entries:
                        resource_id_dict = {}

                        if resource_id.name is not None:
                            resource_id_dict["Name"] = resource_id.name
                        else:
                            resource_id_dict["Id"] = resource_id.struct.Id

                        resource_id_dict.update(resource_id.struct.dump_dict())
                        directory_list.append(resource_id_dict)

                        if hasattr(resource_id, "directory"):
                            resource_id_list = []
                            resource_id_list.append(
                                resource_id.directory.struct.dump_dict()
                            )
                            directory_list.append(resource_id_list)

                            for resource_lang in resource_id.directory.entries:
                                if hasattr(resource_lang, "data"):
                                    resource_lang_dict = {}
                                    resource_lang_dict["LANG"] = resource_lang.data.lang
                                    resource_lang_dict[
                                        "SUBLANG"
                                    ] = resource_lang.data.sublang
                                    resource_lang_dict["LANG_NAME"] = LANG.get(
                                        resource_lang.data.lang, "*unknown*"
                                    )
                                    resource_lang_dict[
                                        "SUBLANG_NAME"
                                    ] = get_sublang_name_for_lang(
                                        resource_lang.data.lang,
                                        resource_lang.data.sublang,
                                    )
                                    resource_lang_dict.update(
                                        resource_lang.struct.dump_dict()
                                    )
                                    resource_lang_dict.update(
                                        resource_lang.data.struct.dump_dict()
                                    )
                                    resource_id_list.append(resource_lang_dict)
                            if (
                                hasattr(resource_id.directory, "strings")
                                and resource_id.directory.strings
                            ):
                                for idx, res_string in list(
                                    resource_id.directory.strings.items()
                                ):
                                    resource_id_list.append(
                                        res_string.encode(
                                            "unicode-escape", "backslashreplace"
                                        ).decode("ascii")
                                    )

        if (
            hasattr(self, "DIRECTORY_ENTRY_TLS")
            and self.DIRECTORY_ENTRY_TLS
            and self.DIRECTORY_ENTRY_TLS.struct
        ):
            dump_dict["TLS"] = self.DIRECTORY_ENTRY_TLS.struct.dump_dict()

        if (
            hasattr(self, "DIRECTORY_ENTRY_LOAD_CONFIG")
            and self.DIRECTORY_ENTRY_LOAD_CONFIG
            and self.DIRECTORY_ENTRY_LOAD_CONFIG.struct
        ):
            dump_dict[
                "LOAD_CONFIG"
            ] = self.DIRECTORY_ENTRY_LOAD_CONFIG.struct.dump_dict()

        if hasattr(self, "DIRECTORY_ENTRY_DEBUG"):
            dump_dict["Debug information"] = []
            for dbg in self.DIRECTORY_ENTRY_DEBUG:
                dbg_dict = {}
                dump_dict["Debug information"].append(dbg_dict)
                dbg_dict.update(dbg.struct.dump_dict())
                dbg_dict["Type"] = DEBUG_TYPE.get(dbg.struct.Type, dbg.struct.Type)

        if self.has_relocs():
            dump_dict["Base relocations"] = []
            for base_reloc in self.DIRECTORY_ENTRY_BASERELOC:
                base_reloc_list = []
                dump_dict["Base relocations"].append(base_reloc_list)
                base_reloc_list.append(base_reloc.struct.dump_dict())
                for reloc in base_reloc.entries:
                    reloc_dict = {}
                    base_reloc_list.append(reloc_dict)
                    reloc_dict["RVA"] = reloc.rva
                    try:
                        reloc_dict["Type"] = RELOCATION_TYPE[reloc.type][16:]
                    except KeyError:
                        reloc_dict["Type"] = reloc.type

        return dump_dict

    # 022815.python.pefile.line7137.comment OC Patch
    def get_physical_by_rva(self, rva):
        """Gets the physical address in the PE file from an RVA value."""
        try:
            return self.get_offset_from_rva(rva)
        except Exception:
            return None

    # 022816.python.pefile.line7145.comment #
    # 022817.python.pefile.line7146.comment Double-Word get / set
    # 022818.python.pefile.line7147.comment #

    def get_data_from_dword(self, dword):
        """Return a four byte string representing the double word value (little endian)."""
        return struct.pack("<L", dword & 0xFFFFFFFF)

    def get_dword_from_data(self, data, offset):
        """Convert four bytes of data to a double word (little endian)

        'offset' is assumed to index into a dword array. So setting it to
        N will return a dword out of the data starting at offset N*4.

        Returns None if the data can't be turned into a double word.
        """

        if (offset + 1) * 4 > len(data):
            return None

        return struct.unpack("<I", data[offset * 4 : (offset + 1) * 4])[0]

    def get_dword_at_rva(self, rva):
        """Return the double word value at the given RVA.

        Returns None if the value can't be read, i.e. the RVA can't be mapped
        to a file offset.
        """

        try:
            return self.get_dword_from_data(self.get_data(rva, 4), 0)
        except PEFormatError:
            return None

    def get_dword_from_offset(self, offset):
        """Return the double word value at the given file offset. (little endian)"""

        if offset + 4 > len(self.__data__):
            return None

        return self.get_dword_from_data(self.__data__[offset : offset + 4], 0)

    def set_dword_at_rva(self, rva, dword):
        """Set the double word value at the file offset corresponding to the given RVA."""
        return self.set_bytes_at_rva(rva, self.get_data_from_dword(dword))

    def set_dword_at_offset(self, offset, dword):
        """Set the double word value at the given file offset."""
        return self.set_bytes_at_offset(offset, self.get_data_from_dword(dword))

    # 022819.python.pefile.line7195.comment #
    # 022820.python.pefile.line7196.comment Word get / set
    # 022821.python.pefile.line7197.comment #

    def get_data_from_word(self, word):
        """Return a two byte string representing the word value. (little endian)."""
        return struct.pack("<H", word)

    def get_word_from_data(self, data, offset):
        """Convert two bytes of data to a word (little endian)

        'offset' is assumed to index into a word array. So setting it to
        N will return a dword out of the data starting at offset N*2.

        Returns None if the data can't be turned into a word.
        """

        if (offset + 1) * 2 > len(data):
            return None

        return struct.unpack("<H", data[offset * 2 : (offset + 1) * 2])[0]

    def get_word_at_rva(self, rva):
        """Return the word value at the given RVA.

        Returns None if the value can't be read, i.e. the RVA can't be mapped
        to a file offset.
        """

        try:
            return self.get_word_from_data(self.get_data(rva)[:2], 0)
        except PEFormatError:
            return None

    def get_word_from_offset(self, offset):
        """Return the word value at the given file offset. (little endian)"""

        if offset + 2 > len(self.__data__):
            return None

        return self.get_word_from_data(self.__data__[offset : offset + 2], 0)

    def set_word_at_rva(self, rva, word):
        """Set the word value at the file offset corresponding to the given RVA."""
        return self.set_bytes_at_rva(rva, self.get_data_from_word(word))

    def set_word_at_offset(self, offset, word):
        """Set the word value at the given file offset."""
        return self.set_bytes_at_offset(offset, self.get_data_from_word(word))

    # 022822.python.pefile.line7245.comment #
    # 022823.python.pefile.line7246.comment Quad-Word get / set
    # 022824.python.pefile.line7247.comment #

    def get_data_from_qword(self, word):
        """Return an eight byte string representing the quad-word value (little endian)."""
        return struct.pack("<Q", word)

    def get_qword_from_data(self, data, offset):
        """Convert eight bytes of data to a word (little endian)

        'offset' is assumed to index into a word array. So setting it to
        N will return a dword out of the data starting at offset N*8.

        Returns None if the data can't be turned into a quad word.
        """

        if (offset + 1) * 8 > len(data):
            return None

        return struct.unpack("<Q", data[offset * 8 : (offset + 1) * 8])[0]

    def get_qword_at_rva(self, rva):
        """Return the quad-word value at the given RVA.

        Returns None if the value can't be read, i.e. the RVA can't be mapped
        to a file offset.
        """

        try:
            return self.get_qword_from_data(self.get_data(rva)[:8], 0)
        except PEFormatError:
            return None

    def get_qword_from_offset(self, offset):
        """Return the quad-word value at the given file offset. (little endian)"""

        if offset + 8 > len(self.__data__):
            return None

        return self.get_qword_from_data(self.__data__[offset : offset + 8], 0)

    def set_qword_at_rva(self, rva, qword):
        """Set the quad-word value at the file offset corresponding to the given RVA."""
        return self.set_bytes_at_rva(rva, self.get_data_from_qword(qword))

    def set_qword_at_offset(self, offset, qword):
        """Set the quad-word value at the given file offset."""
        return self.set_bytes_at_offset(offset, self.get_data_from_qword(qword))

    # 022825.python.pefile.line7295.comment #
    # 022826.python.pefile.line7296.comment Set bytes
    # 022827.python.pefile.line7297.comment #

    def set_bytes_at_rva(self, rva, data):
        """Overwrite, with the given string, the bytes at the file offset corresponding
        to the given RVA.

        Return True if successful, False otherwise. It can fail if the
        offset is outside the file's boundaries.
        """

        if not isinstance(data, bytes):
            raise TypeError("data should be of type: bytes")

        offset = self.get_physical_by_rva(rva)
        if not offset:
            return False

        return self.set_bytes_at_offset(offset, data)

    def set_bytes_at_offset(self, offset, data):
        """Overwrite the bytes at the given file offset with the given string.

        Return True if successful, False otherwise. It can fail if the
        offset is outside the file's boundaries.
        """

        if not isinstance(data, bytes):
            raise TypeError("data should be of type: bytes")

        if 0 <= offset < len(self.__data__):
            self.set_data_bytes(offset, data)
        else:
            return False

        return True

    def set_data_bytes(self, offset: int, data: bytes):
        if not isinstance(self.__data__, bytearray):
            self.__data__ = bytearray(self.__data__)

        self.__data__[offset : offset + len(data)] = data

    def merge_modified_section_data(self):
        """Update the PE image content with any individual section data that has been
        modified.
        """

        for section in self.sections:
            section_data_start = self.adjust_FileAlignment(
                section.PointerToRawData, self.OPTIONAL_HEADER.FileAlignment
            )
            section_data_end = section_data_start + section.SizeOfRawData
            if section_data_start < len(self.__data__) and section_data_end < len(
                self.__data__
            ):
                self.set_data_bytes(section_data_start, section.get_data())

    def relocate_image(self, new_ImageBase):
        """Apply the relocation information to the image using the provided image base.

        This method will apply the relocation information to the image. Given the new
        base, all the relocations will be processed and both the raw data and the
        section's data will be fixed accordingly.
        The resulting image can be retrieved as well through the method:

            get_memory_mapped_image()

        In order to get something that would more closely match what could be found in
        memory once the Windows loader finished its work.
        """

        relocation_difference = new_ImageBase - self.OPTIONAL_HEADER.ImageBase

        if (
            len(self.OPTIONAL_HEADER.DATA_DIRECTORY) >= 6
            and self.OPTIONAL_HEADER.DATA_DIRECTORY[5].Size
        ):
            if not hasattr(self, "DIRECTORY_ENTRY_BASERELOC"):
                self.parse_data_directories(
                    directories=[DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_BASERELOC"]]
                )
            if not hasattr(self, "DIRECTORY_ENTRY_BASERELOC"):
                self.__warnings.append(
                    "Relocating image but PE does not have (or pefile cannot "
                    "parse) a DIRECTORY_ENTRY_BASERELOC"
                )
            else:
                for reloc in self.DIRECTORY_ENTRY_BASERELOC:

                    # 022828.python.pefile.line7386.comment We iterate with an index because if the relocation is of type
                    # 022829.python.pefile.line7387.comment IMAGE_REL_BASED_HIGHADJ we need to also process the next entry
                    # 022830.python.pefile.line7388.comment at once and skip it for the next iteration
                    # 022831.python.pefile.line7389.comment
                    entry_idx = 0
                    while entry_idx < len(reloc.entries):

                        entry = reloc.entries[entry_idx]
                        entry_idx += 1

                        if entry.type == RELOCATION_TYPE["IMAGE_REL_BASED_ABSOLUTE"]:
                            # 022832.python.pefile.line7397.comment Nothing to do for this type of relocation
                            pass

                        elif entry.type == RELOCATION_TYPE["IMAGE_REL_BASED_HIGH"]:
                            # 022833.python.pefile.line7401.comment Fix the high 16-bits of a relocation
                            # 022834.python.pefile.line7402.comment
                            # 022835.python.pefile.line7403.comment Add high 16-bits of relocation_difference to the
                            # 022836.python.pefile.line7404.comment 16-bit value at RVA=entry.rva

                            self.set_word_at_rva(
                                entry.rva,
                                (
                                    self.get_word_at_rva(entry.rva)
                                    + relocation_difference
                                    >> 16
                                )
                                & 0xFFFF,
                            )

                        elif entry.type == RELOCATION_TYPE["IMAGE_REL_BASED_LOW"]:
                            # 022837.python.pefile.line7417.comment Fix the low 16-bits of a relocation
                            # 022838.python.pefile.line7418.comment
                            # 022839.python.pefile.line7419.comment Add low 16 bits of relocation_difference to the 16-bit
                            # 022840.python.pefile.line7420.comment value at RVA=entry.rva

                            self.set_word_at_rva(
                                entry.rva,
                                (
                                    self.get_word_at_rva(entry.rva)
                                    + relocation_difference
                                )
                                & 0xFFFF,
                            )

                        elif entry.type == RELOCATION_TYPE["IMAGE_REL_BASED_HIGHLOW"]:
                            # 022841.python.pefile.line7432.comment Handle all high and low parts of a 32-bit relocation
                            # 022842.python.pefile.line7433.comment
                            # 022843.python.pefile.line7434.comment Add relocation_difference to the value at RVA=entry.rva

                            self.set_dword_at_rva(
                                entry.rva,
                                self.get_dword_at_rva(entry.rva)
                                + relocation_difference,
                            )

                        elif entry.type == RELOCATION_TYPE["IMAGE_REL_BASED_HIGHADJ"]:
                            # 022844.python.pefile.line7443.comment Fix the high 16-bits of a relocation and adjust
                            # 022845.python.pefile.line7444.comment
                            # 022846.python.pefile.line7445.comment Add high 16-bits of relocation_difference to the 32-bit
                            # 022847.python.pefile.line7446.comment value composed from the (16-bit value at
                            # 022848.python.pefile.line7447.comment RVA=entry.rva)<<16 plus the 16-bit value at the next
                            # 022849.python.pefile.line7448.comment relocation entry.

                            # 022850.python.pefile.line7450.comment If the next entry is beyond the array's limits,
                            # 022851.python.pefile.line7451.comment abort... the table is corrupt
                            if entry_idx == len(reloc.entries):
                                break

                            next_entry = reloc.entries[entry_idx]
                            entry_idx += 1
                            self.set_word_at_rva(
                                entry.rva,
                                (
                                    (self.get_word_at_rva(entry.rva) << 16)
                                    + next_entry.rva
                                    + relocation_difference
                                    & 0xFFFF0000
                                )
                                >> 16,
                            )

                        elif entry.type == RELOCATION_TYPE["IMAGE_REL_BASED_DIR64"]:
                            # 022852.python.pefile.line7469.comment Apply the difference to the 64-bit value at the offset
                            # 022853.python.pefile.line7470.comment RVA=entry.rva

                            self.set_qword_at_rva(
                                entry.rva,
                                self.get_qword_at_rva(entry.rva)
                                + relocation_difference,
                            )

            self.OPTIONAL_HEADER.ImageBase = new_ImageBase

            # 022854.python.pefile.line7480.comment correct VAs(virtual addresses) occurrences in directory information
            if hasattr(self, "DIRECTORY_ENTRY_IMPORT"):
                for dll in self.DIRECTORY_ENTRY_IMPORT:
                    for func in dll.imports:
                        func.address += relocation_difference
            if hasattr(self, "DIRECTORY_ENTRY_TLS"):
                self.DIRECTORY_ENTRY_TLS.struct.StartAddressOfRawData += (
                    relocation_difference
                )
                self.DIRECTORY_ENTRY_TLS.struct.EndAddressOfRawData += (
                    relocation_difference
                )
                self.DIRECTORY_ENTRY_TLS.struct.AddressOfIndex += relocation_difference
                self.DIRECTORY_ENTRY_TLS.struct.AddressOfCallBacks += (
                    relocation_difference
                )
            if hasattr(self, "DIRECTORY_ENTRY_LOAD_CONFIG"):
                load_config = self.DIRECTORY_ENTRY_LOAD_CONFIG.struct
                if (
                    hasattr(load_config, "LockPrefixTable")
                    and load_config.LockPrefixTable
                ):
                    load_config.LockPrefixTable += relocation_difference
                if hasattr(load_config, "EditList") and load_config.EditList:
                    load_config.EditList += relocation_difference
                if (
                    hasattr(load_config, "SecurityCookie")
                    and load_config.SecurityCookie
                ):
                    load_config.SecurityCookie += relocation_difference
                if (
                    hasattr(load_config, "SEHandlerTable")
                    and load_config.SEHandlerTable
                ):
                    load_config.SEHandlerTable += relocation_difference
                if (
                    hasattr(load_config, "GuardCFCheckFunctionPointer")
                    and load_config.GuardCFCheckFunctionPointer
                ):
                    load_config.GuardCFCheckFunctionPointer += relocation_difference
                if (
                    hasattr(load_config, "GuardCFDispatchFunctionPointer")
                    and load_config.GuardCFDispatchFunctionPointer
                ):
                    load_config.GuardCFDispatchFunctionPointer += relocation_difference
                if (
                    hasattr(load_config, "GuardCFFunctionTable")
                    and load_config.GuardCFFunctionTable
                ):
                    load_config.GuardCFFunctionTable += relocation_difference
                if (
                    hasattr(load_config, "GuardAddressTakenIatEntryTable")
                    and load_config.GuardAddressTakenIatEntryTable
                ):
                    load_config.GuardAddressTakenIatEntryTable += relocation_difference
                if (
                    hasattr(load_config, "GuardLongJumpTargetTable")
                    and load_config.GuardLongJumpTargetTable
                ):
                    load_config.GuardLongJumpTargetTable += relocation_difference
                if (
                    hasattr(load_config, "DynamicValueRelocTable")
                    and load_config.DynamicValueRelocTable
                ):
                    load_config.DynamicValueRelocTable += relocation_difference
                if (
                    self.PE_TYPE == OPTIONAL_HEADER_MAGIC_PE_PLUS
                    and hasattr(load_config, "CHPEMetadataPointer")
                    and load_config.CHPEMetadataPointer
                ):
                    load_config.CHPEMetadataPointer += relocation_difference
                if (
                    hasattr(load_config, "GuardRFFailureRoutine")
                    and load_config.GuardRFFailureRoutine
                ):
                    load_config.GuardRFFailureRoutine += relocation_difference
                if (
                    hasattr(load_config, "GuardRFFailureRoutineFunctionPointer")
                    and load_config.GuardRFFailureRoutineFunctionPointer
                ):
                    load_config.GuardRFVerifyStackPointerFunctionPointer += (
                        relocation_difference
                    )
                if (
                    hasattr(load_config, "GuardRFVerifyStackPointerFunctionPointer")
                    and load_config.GuardRFVerifyStackPointerFunctionPointer
                ):
                    load_config.GuardRFVerifyStackPointerFunctionPointer += (
                        relocation_difference
                    )
                if (
                    hasattr(load_config, "EnclaveConfigurationPointer")
                    and load_config.EnclaveConfigurationPointer
                ):
                    load_config.EnclaveConfigurationPointer += relocation_difference

    def verify_checksum(self):

        return self.OPTIONAL_HEADER.CheckSum == self.generate_checksum()

    def generate_checksum(self):
        # 022855.python.pefile.line7581.comment This will make sure that the data representing the PE image
        # 022856.python.pefile.line7582.comment is updated with any changes that might have been made by
        # 022857.python.pefile.line7583.comment assigning values to header fields as those are not automatically
        # 022858.python.pefile.line7584.comment updated upon assignment.
        # 022859.python.pefile.line7585.comment
        # 022860.python.pefile.line7586.comment data = self.write()
        # 022861.python.pefile.line7587.comment print('{0}'.format(len(data)))
        # 022862.python.pefile.line7588.comment for idx, b in enumerate(data):
        # 022863.python.pefile.line7589.comment if b != ord(self.__data__[idx]) or (idx > 1244440 and idx < 1244460):
        # 022864.python.pefile.line7590.comment print('Idx: {0} G {1:02x} {3} B {2:02x}'.format(
        # 022865.python.pefile.line7591.comment idx, ord(self.__data__[idx]), b,
        # 022866.python.pefile.line7592.comment self.__data__[idx], chr(b)))
        self.__data__ = self.write()

        # 022867.python.pefile.line7595.comment Get the offset to the CheckSum field in the OptionalHeader
        # 022868.python.pefile.line7596.comment (The offset is the same in PE32 and PE32+)
        checksum_offset = self.OPTIONAL_HEADER.get_file_offset() + 0x40  # 64

        checksum = 0
        # 022870.python.pefile.line7600.comment Verify the data is dword-aligned. Add padding if needed
        # 022871.python.pefile.line7601.comment
        remainder = len(self.__data__) % 4
        data_len = len(self.__data__) + ((4 - remainder) * (remainder != 0))

        for i in range(int(data_len / 4)):
            # 022872.python.pefile.line7606.comment Skip the checksum field
            if i == int(checksum_offset / 4):
                continue
            if i + 1 == (int(data_len / 4)) and remainder:
                dword = struct.unpack(
                    "I", self.__data__[i * 4 :] + (b"\0" * (4 - remainder))
                )[0]
            else:
                dword = struct.unpack("I", self.__data__[i * 4 : i * 4 + 4])[0]
            # 022873.python.pefile.line7615.comment Optimized the calculation (thanks to Emmanuel Bourg for pointing it out!)
            checksum += dword
            if checksum >= 2**32:
                checksum = (checksum & 0xFFFFFFFF) + (checksum >> 32)

        checksum = (checksum & 0xFFFF) + (checksum >> 16)
        checksum = (checksum) + (checksum >> 16)
        checksum = checksum & 0xFFFF

        # 022874.python.pefile.line7624.comment The length is the one of the original data, not the padded one
        # 022875.python.pefile.line7625.comment
        return checksum + len(self.__data__)

    def is_exe(self):
        """Check whether the file is a standard executable.

        This will return true only if the file has the IMAGE_FILE_EXECUTABLE_IMAGE flag
        set and the IMAGE_FILE_DLL not set and the file does not appear to be a driver
        either.
        """

        EXE_flag = IMAGE_CHARACTERISTICS["IMAGE_FILE_EXECUTABLE_IMAGE"]

        if (
            (not self.is_dll())
            and (not self.is_driver())
            and (EXE_flag & self.FILE_HEADER.Characteristics) == EXE_flag
        ):
            return True

        return False

    def is_dll(self):
        """Check whether the file is a standard DLL.

        This will return true only if the image has the IMAGE_FILE_DLL flag set.
        """

        DLL_flag = IMAGE_CHARACTERISTICS["IMAGE_FILE_DLL"]

        if (DLL_flag & self.FILE_HEADER.Characteristics) == DLL_flag:
            return True

        return False

    def is_driver(self):
        """Check whether the file is a Windows driver.

        This will return true only if there are reliable indicators of the image
        being a driver.
        """

        # 022876.python.pefile.line7667.comment Checking that the ImageBase field of the OptionalHeader is above or
        # 022877.python.pefile.line7668.comment equal to 0x80000000 (that is, whether it lies in the upper 2GB of
        # 022878.python.pefile.line7669.comment the address space, normally belonging to the kernel) is not a
        # 022879.python.pefile.line7670.comment reliable enough indicator.  For instance, PEs that play the invalid
        # 022880.python.pefile.line7671.comment ImageBase trick to get relocated could be incorrectly assumed to be
        # 022881.python.pefile.line7672.comment drivers.

        # 022882.python.pefile.line7674.comment This is not reliable either...
        # 022883.python.pefile.line7675.comment
        # 022884.python.pefile.line7676.comment if any((section.Characteristics &
        # 022885.python.pefile.line7677.comment SECTION_CHARACTERISTICS['IMAGE_SCN_MEM_NOT_PAGED']) for
        # 022886.python.pefile.line7678.comment section in self.sections ):
        # 022887.python.pefile.line7679.comment return True

        # 022888.python.pefile.line7681.comment If the import directory was not parsed (fast_load = True); do it now.
        if not hasattr(self, "DIRECTORY_ENTRY_IMPORT"):
            self.parse_data_directories(
                directories=[DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]]
            )

        # 022889.python.pefile.line7687.comment If there's still no import directory (the PE doesn't have one or it's
        # 022890.python.pefile.line7688.comment malformed), give up.
        if not hasattr(self, "DIRECTORY_ENTRY_IMPORT"):
            return False

        # 022891.python.pefile.line7692.comment self.DIRECTORY_ENTRY_IMPORT will now exist, although it may be empty.
        # 022892.python.pefile.line7693.comment If it imports from "ntoskrnl.exe" or other kernel components it should
        # 022893.python.pefile.line7694.comment be a driver
        # 022894.python.pefile.line7695.comment
        system_DLLs = set(
            (b"ntoskrnl.exe", b"hal.dll", b"ndis.sys", b"bootvid.dll", b"kdcom.dll")
        )
        if system_DLLs.intersection(
            [imp.dll.lower() for imp in self.DIRECTORY_ENTRY_IMPORT]
        ):
            return True

        driver_like_section_names = set((b"page", b"paged"))
        if driver_like_section_names.intersection(
            [section.Name.lower().rstrip(b"\x00") for section in self.sections]
        ) and (
            self.OPTIONAL_HEADER.Subsystem
            in (
                SUBSYSTEM_TYPE["IMAGE_SUBSYSTEM_NATIVE"],
                SUBSYSTEM_TYPE["IMAGE_SUBSYSTEM_NATIVE_WINDOWS"],
            )
        ):
            return True

        return False

    def get_overlay_data_start_offset(self):
        """Get the offset of data appended to the file and not contained within
        the area described in the headers."""

        largest_offset_and_size = (0, 0)

        def update_if_sum_is_larger_and_within_file(
            offset_and_size, file_size=len(self.__data__)
        ):
            if sum(offset_and_size) <= file_size and sum(offset_and_size) > sum(
                largest_offset_and_size
            ):
                return offset_and_size
            return largest_offset_and_size

        if hasattr(self, "OPTIONAL_HEADER"):
            largest_offset_and_size = update_if_sum_is_larger_and_within_file(
                (
                    self.OPTIONAL_HEADER.get_file_offset(),
                    self.FILE_HEADER.SizeOfOptionalHeader,
                )
            )

        for section in self.sections:
            largest_offset_and_size = update_if_sum_is_larger_and_within_file(
                (section.PointerToRawData, section.SizeOfRawData)
            )

        skip_directories = [DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_SECURITY"]]

        for idx, directory in enumerate(self.OPTIONAL_HEADER.DATA_DIRECTORY):
            if idx in skip_directories:
                continue
            try:
                largest_offset_and_size = update_if_sum_is_larger_and_within_file(
                    (self.get_offset_from_rva(directory.VirtualAddress), directory.Size)
                )
            # 022895.python.pefile.line7755.comment Ignore directories with RVA out of file
            except PEFormatError:
                continue

        if len(self.__data__) > sum(largest_offset_and_size):
            return sum(largest_offset_and_size)

        return None

    def get_overlay(self):
        """Get the data appended to the file and not contained within the area described
        in the headers."""

        overlay_data_offset = self.get_overlay_data_start_offset()

        if overlay_data_offset is not None:
            return self.__data__[overlay_data_offset:]

        return None

    def trim(self):
        """Return the just data defined by the PE headers, removing any overlaid data."""

        overlay_data_offset = self.get_overlay_data_start_offset()

        if overlay_data_offset is not None:
            return self.__data__[:overlay_data_offset]

        return self.__data__[:]

    # 022896.python.pefile.line7785.comment According to http://corkami.blogspot.com/2010/01/parce-que-la-planche-aura-brule.html
    # 022897.python.pefile.line7786.comment if PointerToRawData is less that 0x200 it's rounded to zero. Loading the test file
    # 022898.python.pefile.line7787.comment in a debugger it's easy to verify that the PointerToRawData value of 1 is rounded
    # 022899.python.pefile.line7788.comment to zero. Hence we reproduce the behavior
    # 022900.python.pefile.line7789.comment
    # 022901.python.pefile.line7790.comment According to the document:
    # 022902.python.pefile.line7791.comment [ Microsoft Portable Executable and Common Object File Format Specification ]
    # 022903.python.pefile.line7792.comment "The alignment factor (in bytes) that is used to align the raw data of sections in
    # 022904.python.pefile.line7793.comment the image file. The value should be a power of 2 between 512 and 64 K, inclusive.
    # 022905.python.pefile.line7794.comment The default is 512. If the SectionAlignment is less than the architecture's page
    # 022906.python.pefile.line7795.comment size, then FileAlignment must match SectionAlignment."
    # 022907.python.pefile.line7796.comment
    # 022908.python.pefile.line7797.comment The following is a hard-coded constant if the Windows loader
    def adjust_FileAlignment(self, val, file_alignment):
        if file_alignment > FILE_ALIGNMENT_HARDCODED_VALUE:
            # 022909.python.pefile.line7800.comment If it's not a power of two, report it:
            if self.FileAlignment_Warning is False and not power_of_two(file_alignment):
                self.__warnings.append(
                    "If FileAlignment > 0x200 it should be a power of 2. Value: %x"
                    % (file_alignment)
                )
                self.FileAlignment_Warning = True

        return cache_adjust_FileAlignment(val, file_alignment)

    # 022910.python.pefile.line7810.comment According to the document:
    # 022911.python.pefile.line7811.comment [ Microsoft Portable Executable and Common Object File Format Specification ]
    # 022912.python.pefile.line7812.comment "The alignment (in bytes) of sections when they are loaded into memory. It must be
    # 022913.python.pefile.line7813.comment greater than or equal to FileAlignment. The default is the page size for the
    # 022914.python.pefile.line7814.comment architecture."
    # 022915.python.pefile.line7815.comment
    def adjust_SectionAlignment(self, val, section_alignment, file_alignment):
        if file_alignment < FILE_ALIGNMENT_HARDCODED_VALUE:
            if (
                file_alignment != section_alignment
                and self.SectionAlignment_Warning is False
            ):
                self.__warnings.append(
                    "If FileAlignment(%x) < 0x200 it should equal SectionAlignment(%x)"
                    % (file_alignment, section_alignment)
                )
                self.SectionAlignment_Warning = True

        return cache_adjust_SectionAlignment(val, section_alignment, file_alignment)


def main():
    import sys

    usage = """\
pefile.py <filename>
pefile.py exports <filename>"""

    if not sys.argv[1:]:
        print(usage)
    elif sys.argv[1] == "exports":
        if not sys.argv[2:]:
            sys.exit("error: <filename> required")
        pe = PE(sys.argv[2])
        for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
            print(
                hex(pe.OPTIONAL_HEADER.ImageBase + exp.address), exp.name, exp.ordinal
            )
    else:
        print(PE(sys.argv[1]).dump_info())


if __name__ == "__main__":
    main()
