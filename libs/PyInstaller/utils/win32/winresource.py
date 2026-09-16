# 011268.python.winresource.line1.comment -----------------------------------------------------------------------------
# 011269.python.winresource.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 011270.python.winresource.line3.comment
# 011271.python.winresource.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 011272.python.winresource.line5.comment or later) with exception for distributing the bootloader.
# 011273.python.winresource.line6.comment
# 011274.python.winresource.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 011275.python.winresource.line8.comment
# 011276.python.winresource.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 011277.python.winresource.line10.comment -----------------------------------------------------------------------------
"""
Read and write resources from/to Win32 PE files.
"""

import PyInstaller.log as logging
from PyInstaller.compat import pywintypes, win32api

logger = logging.getLogger(__name__)

LOAD_LIBRARY_AS_DATAFILE = 2
ERROR_BAD_EXE_FORMAT = 193
ERROR_RESOURCE_DATA_NOT_FOUND = 1812
ERROR_RESOURCE_TYPE_NOT_FOUND = 1813
ERROR_RESOURCE_NAME_NOT_FOUND = 1814
ERROR_RESOURCE_LANG_NOT_FOUND = 1815


def get_resources(filename, types=None, names=None, languages=None):
    """
    Retrieve resources from the given PE file.

    filename: path to the PE file.
    types: a list of resource types (integers or strings) to search for (None = all).
    names: a list of resource names (integers or strings) to search for (None = all).
    languages: a list of resource languages (integers) to search for (None = all).

    Returns a dictionary of the form {type: {name: {language: data}}}, which might also be empty if no matching
    resources were found.
    """
    types = set(types) if types is not None else {"*"}
    names = set(names) if names is not None else {"*"}
    languages = set(languages) if languages is not None else {"*"}

    output = {}

    # 011278.python.winresource.line46.comment Errors codes for which we swallow exceptions
    _IGNORE_EXCEPTIONS = {
        ERROR_RESOURCE_DATA_NOT_FOUND,
        ERROR_RESOURCE_TYPE_NOT_FOUND,
        ERROR_RESOURCE_NAME_NOT_FOUND,
        ERROR_RESOURCE_LANG_NOT_FOUND,
    }

    # 011279.python.winresource.line54.comment Open file
    module_handle = win32api.LoadLibraryEx(filename, 0, LOAD_LIBRARY_AS_DATAFILE)

    # 011280.python.winresource.line57.comment Enumerate available resource types
    try:
        available_types = win32api.EnumResourceTypes(module_handle)
    except pywintypes.error as e:
        if e.args[0] not in _IGNORE_EXCEPTIONS:
            raise
        available_types = []

    if "*" not in types:
        available_types = [res_type for res_type in available_types if res_type in types]

    for res_type in available_types:
        # 011281.python.winresource.line69.comment Enumerate available names for the resource type.
        try:
            available_names = win32api.EnumResourceNames(module_handle, res_type)
        except pywintypes.error as e:
            if e.args[0] not in _IGNORE_EXCEPTIONS:
                raise
            continue

        if "*" not in names:
            available_names = [res_name for res_name in available_names if res_name in names]

        for res_name in available_names:
            # 011282.python.winresource.line81.comment Enumerate available languages for the resource type and name combination.
            try:
                available_languages = win32api.EnumResourceLanguages(module_handle, res_type, res_name)
            except pywintypes.error as e:
                if e.args[0] not in _IGNORE_EXCEPTIONS:
                    raise
                continue

            if "*" not in languages:
                available_languages = [res_lang for res_lang in available_languages if res_lang in languages]

            for res_lang in available_languages:
                # 011283.python.winresource.line93.comment Read data
                try:
                    data = win32api.LoadResource(module_handle, res_type, res_name, res_lang)
                except pywintypes.error as e:
                    if e.args[0] not in _IGNORE_EXCEPTIONS:
                        raise
                    continue

                if res_type not in output:
                    output[res_type] = {}
                if res_name not in output[res_type]:
                    output[res_type][res_name] = {}
                output[res_type][res_name][res_lang] = data

    # 011284.python.winresource.line107.comment Close file
    win32api.FreeLibrary(module_handle)

    return output


def add_or_update_resource(filename, data, res_type, names=None, languages=None):
    """
    Update or add a single resource in the PE file with the given binary data.

    filename: path to the PE file.
    data: binary data to write to the resource.
    res_type: resource type to add/update (integer or string).
    names: a list of resource names (integers or strings) to update (None = all).
    languages: a list of resource languages (integers) to update (None = all).
    """
    if res_type == "*":
        raise ValueError("res_type cannot be a wildcard (*)!")

    names = set(names) if names is not None else {"*"}
    languages = set(languages) if languages is not None else {"*"}

    # 011285.python.winresource.line129.comment Retrieve existing resources, filtered by the given resource type and given resource names and languages.
    resources = get_resources(filename, [res_type], names, languages)

    # 011286.python.winresource.line132.comment Add res_type, name, language combinations that are not already present
    resources = resources.get(res_type, {})  # This is now a {name: {language: data}} dictionary

    for res_name in names:
        if res_name == "*":
            continue
        if res_name not in resources:
            resources[res_name] = {}

        for res_lang in languages:
            if res_lang == "*":
                continue
            if res_lang not in resources[res_name]:
                resources[res_name][res_lang] = None  # Just an indicator

    # 011289.python.winresource.line147.comment Add resource to the target file, overwriting the existing resources with same type, name, language combinations.
    module_handle = win32api.BeginUpdateResource(filename, 0)
    for res_name in resources.keys():
        for res_lang in resources[res_name].keys():
            win32api.UpdateResource(module_handle, res_type, res_name, data, res_lang)
    win32api.EndUpdateResource(module_handle, 0)


def copy_resources_from_pe_file(filename, src_filename, types=None, names=None, languages=None):
    """
    Update or add resources in the given PE file by copying them over from the specified source PE file.

    filename: path to the PE file.
    src_filename: path to the source PE file.
    types: a list of resource types (integers or strings) to add/update via copy for (None = all).
    names: a list of resource names (integers or strings) to add/update via copy (None = all).
    languages: a list of resource languages (integers) to add/update via copy (None = all).
    """
    types = set(types) if types is not None else {"*"}
    names = set(names) if names is not None else {"*"}
    languages = set(languages) if languages is not None else {"*"}

    # 011290.python.winresource.line169.comment Retrieve existing resources, filtered by the given resource type and given resource names and languages.
    resources = get_resources(src_filename, types, names, languages)

    for res_type, resources_for_type in resources.items():
        if "*" not in types and res_type not in types:
            continue
        for res_name, resources_for_type_name in resources_for_type.items():
            if "*" not in names and res_name not in names:
                continue
            for res_lang, data in resources_for_type_name.items():
                if "*" not in languages and res_lang not in languages:
                    continue
                add_or_update_resource(filename, data, res_type, [res_name], [res_lang])


def remove_all_resources(filename):
    """
    Remove all resources from the given PE file:
    """
    module_handle = win32api.BeginUpdateResource(filename, True)  # bDeleteExistingResources=True
    win32api.EndUpdateResource(module_handle, False)
