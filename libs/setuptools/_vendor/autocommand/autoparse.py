# 041644.python.autoparse.line1.comment Copyright 2014-2015 Nathan West
# 041645.python.autoparse.line2.comment
# 041646.python.autoparse.line3.comment This file is part of autocommand.
# 041647.python.autoparse.line4.comment
# 041648.python.autoparse.line5.comment autocommand is free software: you can redistribute it and/or modify
# 041649.python.autoparse.line6.comment it under the terms of the GNU Lesser General Public License as published by
# 041650.python.autoparse.line7.comment the Free Software Foundation, either version 3 of the License, or
# 041651.python.autoparse.line8.comment (at your option) any later version.
# 041652.python.autoparse.line9.comment
# 041653.python.autoparse.line10.comment autocommand is distributed in the hope that it will be useful,
# 041654.python.autoparse.line11.comment but WITHOUT ANY WARRANTY; without even the implied warranty of
# 041655.python.autoparse.line12.comment MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# 041656.python.autoparse.line13.comment GNU Lesser General Public License for more details.
# 041657.python.autoparse.line14.comment
# 041658.python.autoparse.line15.comment You should have received a copy of the GNU Lesser General Public License
# 041659.python.autoparse.line16.comment along with autocommand.  If not, see <http://www.gnu.org/licenses/>.

import sys
from re import compile as compile_regex
from inspect import signature, getdoc, Parameter
from argparse import ArgumentParser
from contextlib import contextmanager
from functools import wraps
from io import IOBase
from autocommand.errors import AutocommandError


_empty = Parameter.empty


class AnnotationError(AutocommandError):
    '''Annotation error: annotation must be a string, type, or tuple of both'''


class PositionalArgError(AutocommandError):
    '''
    Postional Arg Error: autocommand can't handle postional-only parameters
    '''


class KWArgError(AutocommandError):
    '''kwarg Error: autocommand can't handle a **kwargs parameter'''


class DocstringError(AutocommandError):
    '''Docstring error'''


class TooManySplitsError(DocstringError):
    '''
    The docstring had too many ---- section splits. Currently we only support
    using up to a single split, to split the docstring into description and
    epilog parts.
    '''


def _get_type_description(annotation):
    '''
    Given an annotation, return the (type, description) for the parameter.
    If you provide an annotation that is somehow both a string and a callable,
    the behavior is undefined.
    '''
    if annotation is _empty:
        return None, None
    elif callable(annotation):
        return annotation, None
    elif isinstance(annotation, str):
        return None, annotation
    elif isinstance(annotation, tuple):
        try:
            arg1, arg2 = annotation
        except ValueError as e:
            raise AnnotationError(annotation) from e
        else:
            if callable(arg1) and isinstance(arg2, str):
                return arg1, arg2
            elif isinstance(arg1, str) and callable(arg2):
                return arg2, arg1

    raise AnnotationError(annotation)


def _add_arguments(param, parser, used_char_args, add_nos):
    '''
    Add the argument(s) to an ArgumentParser (using add_argument) for a given
    parameter. used_char_args is the set of -short options currently already in
    use, and is updated (if necessary) by this function. If add_nos is True,
    this will also add an inverse switch for all boolean options. For
    instance, for the boolean parameter "verbose", this will create --verbose
    and --no-verbose.
    '''

    # 041660.python.autoparse.line93.comment Impl note: This function is kept separate from make_parser because it's
    # 041661.python.autoparse.line94.comment already very long and I wanted to separate out as much as possible into
    # 041662.python.autoparse.line95.comment its own call scope, to prevent even the possibility of suble mutation
    # 041663.python.autoparse.line96.comment bugs.
    if param.kind is param.POSITIONAL_ONLY:
        raise PositionalArgError(param)
    elif param.kind is param.VAR_KEYWORD:
        raise KWArgError(param)

    # 041664.python.autoparse.line102.comment These are the kwargs for the add_argument function.
    arg_spec = {}
    is_option = False

    # 041665.python.autoparse.line106.comment Get the type and default from the annotation.
    arg_type, description = _get_type_description(param.annotation)

    # 041666.python.autoparse.line109.comment Get the default value
    default = param.default

    # 041667.python.autoparse.line112.comment If there is no explicit type, and the default is present and not None,
    # 041668.python.autoparse.line113.comment infer the type from the default.
    if arg_type is None and default not in {_empty, None}:
        arg_type = type(default)

    # 041669.python.autoparse.line117.comment Add default. The presence of a default means this is an option, not an
    # 041670.python.autoparse.line118.comment argument.
    if default is not _empty:
        arg_spec['default'] = default
        is_option = True

    # 041671.python.autoparse.line123.comment Add the type
    if arg_type is not None:
        # 041672.python.autoparse.line125.comment Special case for bool: make it just a --switch
        if arg_type is bool:
            if not default or default is _empty:
                arg_spec['action'] = 'store_true'
            else:
                arg_spec['action'] = 'store_false'

            # 041673.python.autoparse.line132.comment Switches are always options
            is_option = True

        # 041674.python.autoparse.line135.comment Special case for file types: make it a string type, for filename
        elif isinstance(default, IOBase):
            arg_spec['type'] = str

        # 041675.python.autoparse.line139.comment TODO: special case for list type.
        # 041676.python.autoparse.line140.comment - How to specificy type of list members?
        # 041677.python.autoparse.line141.comment - param: [int]
        # 041678.python.autoparse.line142.comment - param: int =[]
        # 041679.python.autoparse.line143.comment - action='append' vs nargs='*'

        else:
            arg_spec['type'] = arg_type

    # 041680.python.autoparse.line148.comment nargs: if the signature includes *args, collect them as trailing CLI
    # 041681.python.autoparse.line149.comment arguments in a list. *args can't have a default value, so it can never be
    # 041682.python.autoparse.line150.comment an option.
    if param.kind is param.VAR_POSITIONAL:
        # 041683.python.autoparse.line152.comment TODO: consider depluralizing metavar/name here.
        arg_spec['nargs'] = '*'

    # 041684.python.autoparse.line155.comment Add description.
    if description is not None:
        arg_spec['help'] = description

    # 041685.python.autoparse.line159.comment Get the --flags
    flags = []
    name = param.name

    if is_option:
        # 041686.python.autoparse.line164.comment Add the first letter as a -short option.
        for letter in name[0], name[0].swapcase():
            if letter not in used_char_args:
                used_char_args.add(letter)
                flags.append('-{}'.format(letter))
                break

        # 041687.python.autoparse.line171.comment If the parameter is a --long option, or is a -short option that
        # 041688.python.autoparse.line172.comment somehow failed to get a flag, add it.
        if len(name) > 1 or not flags:
            flags.append('--{}'.format(name))

        arg_spec['dest'] = name
    else:
        flags.append(name)

    parser.add_argument(*flags, **arg_spec)

    # 041689.python.autoparse.line182.comment Create the --no- version for boolean switches
    if add_nos and arg_type is bool:
        parser.add_argument(
            '--no-{}'.format(name),
            action='store_const',
            dest=name,
            const=default if default is not _empty else False)


def make_parser(func_sig, description, epilog, add_nos):
    '''
    Given the signature of a function, create an ArgumentParser
    '''
    parser = ArgumentParser(description=description, epilog=epilog)

    used_char_args = {'h'}

    # 041690.python.autoparse.line199.comment Arange the params so that single-character arguments are first. This
    # 041691.python.autoparse.line200.comment esnures they don't have to get --long versions. sorted is stable, so the
    # 041692.python.autoparse.line201.comment parameters will otherwise still be in relative order.
    params = sorted(
        func_sig.parameters.values(),
        key=lambda param: len(param.name) > 1)

    for param in params:
        _add_arguments(param, parser, used_char_args, add_nos)

    return parser


_DOCSTRING_SPLIT = compile_regex(r'\n\s*-{4,}\s*\n')


def parse_docstring(docstring):
    '''
    Given a docstring, parse it into a description and epilog part
    '''
    if docstring is None:
        return '', ''

    parts = _DOCSTRING_SPLIT.split(docstring)

    if len(parts) == 1:
        return docstring, ''
    elif len(parts) == 2:
        return parts[0], parts[1]
    else:
        raise TooManySplitsError()


def autoparse(
        func=None, *,
        description=None,
        epilog=None,
        add_nos=False,
        parser=None):
    '''
    This decorator converts a function that takes normal arguments into a
    function which takes a single optional argument, argv, parses it using an
    argparse.ArgumentParser, and calls the underlying function with the parsed
    arguments. If it is not given, sys.argv[1:] is used. This is so that the
    function can be used as a setuptools entry point, as well as a normal main
    function. sys.argv[1:] is not evaluated until the function is called, to
    allow injecting different arguments for testing.

    It uses the argument signature of the function to create an
    ArgumentParser. Parameters without defaults become positional parameters,
    while parameters *with* defaults become --options. Use annotations to set
    the type of the parameter.

    The `desctiption` and `epilog` parameters corrospond to the same respective
    argparse parameters. If no description is given, it defaults to the
    decorated functions's docstring, if present.

    If add_nos is True, every boolean option (that is, every parameter with a
    default of True/False or a type of bool) will have a --no- version created
    as well, which inverts the option. For instance, the --verbose option will
    have a --no-verbose counterpart. These are not mutually exclusive-
    whichever one appears last in the argument list will have precedence.

    If a parser is given, it is used instead of one generated from the function
    signature. In this case, no parser is created; instead, the given parser is
    used to parse the argv argument. The parser's results' argument names must
    match up with the parameter names of the decorated function.

    The decorated function is attached to the result as the `func` attribute,
    and the parser is attached as the `parser` attribute.
    '''

    # 041693.python.autoparse.line271.comment If @autoparse(...) is used instead of @autoparse
    if func is None:
        return lambda f: autoparse(
            f, description=description,
            epilog=epilog,
            add_nos=add_nos,
            parser=parser)

    func_sig = signature(func)

    docstr_description, docstr_epilog = parse_docstring(getdoc(func))

    if parser is None:
        parser = make_parser(
            func_sig,
            description or docstr_description,
            epilog or docstr_epilog,
            add_nos)

    @wraps(func)
    def autoparse_wrapper(argv=None):
        if argv is None:
            argv = sys.argv[1:]

        # 041694.python.autoparse.line295.comment Get empty argument binding, to fill with parsed arguments. This
        # 041695.python.autoparse.line296.comment object does all the heavy lifting of turning named arguments into
        # 041696.python.autoparse.line297.comment into correctly bound *args and **kwargs.
        parsed_args = func_sig.bind_partial()
        parsed_args.arguments.update(vars(parser.parse_args(argv)))

        return func(*parsed_args.args, **parsed_args.kwargs)

    # 041697.python.autoparse.line303.comment TODO: attach an updated __signature__ to autoparse_wrapper, just in case.

    # 041698.python.autoparse.line305.comment Attach the wrapped function and parser, and return the wrapper.
    autoparse_wrapper.func = func
    autoparse_wrapper.parser = parser
    return autoparse_wrapper


@contextmanager
def smart_open(filename_or_file, *args, **kwargs):
    '''
    This context manager allows you to open a filename, if you want to default
    some already-existing file object, like sys.stdout, which shouldn't be
    closed at the end of the context. If the filename argument is a str, bytes,
    or int, the file object is created via a call to open with the given *args
    and **kwargs, sent to the context, and closed at the end of the context,
    just like "with open(filename) as f:". If it isn't one of the openable
    types, the object simply sent to the context unchanged, and left unclosed
    at the end of the context. Example:

        def work_with_file(name=sys.stdout):
            with smart_open(name) as f:
                # Works correctly if name is a str filename or sys.stdout
                print("Some stuff", file=f)
                # If it was a filename, f is closed at the end here.
    '''
    if isinstance(filename_or_file, (str, bytes, int)):
        with open(filename_or_file, *args, **kwargs) as file:
            yield file
    else:
        yield filename_or_file
