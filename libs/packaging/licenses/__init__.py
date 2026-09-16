# 021763.python.init.line1.comment ######################################################################################
# 021764.python.init.line2.comment
# 021765.python.init.line3.comment Adapted from:
# 021766.python.init.line4.comment https://github.com/pypa/hatch/blob/5352e44/backend/src/hatchling/licenses/parse.py
# 021767.python.init.line5.comment
# 021768.python.init.line6.comment MIT License
# 021769.python.init.line7.comment
# 021770.python.init.line8.comment Copyright (c) 2017-present Ofek Lev <oss@ofek.dev>
# 021771.python.init.line9.comment
# 021772.python.init.line10.comment Permission is hereby granted, free of charge, to any person obtaining a copy of this
# 021773.python.init.line11.comment software and associated documentation files (the "Software"), to deal in the Software
# 021774.python.init.line12.comment without restriction, including without limitation the rights to use, copy, modify,
# 021775.python.init.line13.comment merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# 021776.python.init.line14.comment permit persons to whom the Software is furnished to do so, subject to the following
# 021777.python.init.line15.comment conditions:
# 021778.python.init.line16.comment
# 021779.python.init.line17.comment The above copyright notice and this permission notice shall be included in all copies
# 021780.python.init.line18.comment or substantial portions of the Software.
# 021781.python.init.line19.comment
# 021782.python.init.line20.comment THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# 021783.python.init.line21.comment INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# 021784.python.init.line22.comment PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# 021785.python.init.line23.comment HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
# 021786.python.init.line24.comment CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# 021787.python.init.line25.comment OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 021788.python.init.line26.comment
# 021789.python.init.line27.comment
# 021790.python.init.line28.comment With additional allowance of arbitrary `LicenseRef-` identifiers, not just
# 021791.python.init.line29.comment `LicenseRef-Public-Domain` and `LicenseRef-Proprietary`.
# 021792.python.init.line30.comment
# 021793.python.init.line31.comment ######################################################################################
from __future__ import annotations

import re
from typing import NewType, cast

from packaging.licenses._spdx import EXCEPTIONS, LICENSES

__all__ = [
    "InvalidLicenseExpression",
    "NormalizedLicenseExpression",
    "canonicalize_license_expression",
]

license_ref_allowed = re.compile("^[A-Za-z0-9.-]*$")

NormalizedLicenseExpression = NewType("NormalizedLicenseExpression", str)


class InvalidLicenseExpression(ValueError):
    """Raised when a license-expression string is invalid

    >>> canonicalize_license_expression("invalid")
    Traceback (most recent call last):
        ...
    packaging.licenses.InvalidLicenseExpression: Invalid license expression: 'invalid'
    """


def canonicalize_license_expression(
    raw_license_expression: str,
) -> NormalizedLicenseExpression:
    if not raw_license_expression:
        message = f"Invalid license expression: {raw_license_expression!r}"
        raise InvalidLicenseExpression(message)

    # 021794.python.init.line67.comment Pad any parentheses so tokenization can be achieved by merely splitting on
    # 021795.python.init.line68.comment whitespace.
    license_expression = raw_license_expression.replace("(", " ( ").replace(")", " ) ")
    licenseref_prefix = "LicenseRef-"
    license_refs = {
        ref.lower(): "LicenseRef-" + ref[len(licenseref_prefix) :]
        for ref in license_expression.split()
        if ref.lower().startswith(licenseref_prefix.lower())
    }

    # 021796.python.init.line77.comment Normalize to lower case so we can look up licenses/exceptions
    # 021797.python.init.line78.comment and so boolean operators are Python-compatible.
    license_expression = license_expression.lower()

    tokens = license_expression.split()

    # 021798.python.init.line83.comment Rather than implementing boolean logic, we create an expression that Python can
    # 021799.python.init.line84.comment parse. Everything that is not involved with the grammar itself is treated as
    # 021800.python.init.line85.comment `False` and the expression should evaluate as such.
    python_tokens = []
    for token in tokens:
        if token not in {"or", "and", "with", "(", ")"}:
            python_tokens.append("False")
        elif token == "with":
            python_tokens.append("or")
        elif token == "(" and python_tokens and python_tokens[-1] not in {"or", "and"}:
            message = f"Invalid license expression: {raw_license_expression!r}"
            raise InvalidLicenseExpression(message)
        else:
            python_tokens.append(token)

    python_expression = " ".join(python_tokens)
    try:
        invalid = eval(python_expression, globals(), locals())
    except Exception:
        invalid = True

    if invalid is not False:
        message = f"Invalid license expression: {raw_license_expression!r}"
        raise InvalidLicenseExpression(message) from None

    # 021801.python.init.line108.comment Take a final pass to check for unknown licenses/exceptions.
    normalized_tokens = []
    for token in tokens:
        if token in {"or", "and", "with", "(", ")"}:
            normalized_tokens.append(token.upper())
            continue

        if normalized_tokens and normalized_tokens[-1] == "WITH":
            if token not in EXCEPTIONS:
                message = f"Unknown license exception: {token!r}"
                raise InvalidLicenseExpression(message)

            normalized_tokens.append(EXCEPTIONS[token]["id"])
        else:
            if token.endswith("+"):
                final_token = token[:-1]
                suffix = "+"
            else:
                final_token = token
                suffix = ""

            if final_token.startswith("licenseref-"):
                if not license_ref_allowed.match(final_token):
                    message = f"Invalid licenseref: {final_token!r}"
                    raise InvalidLicenseExpression(message)
                normalized_tokens.append(license_refs[final_token] + suffix)
            else:
                if final_token not in LICENSES:
                    message = f"Unknown license: {final_token!r}"
                    raise InvalidLicenseExpression(message)
                normalized_tokens.append(LICENSES[final_token]["id"] + suffix)

    normalized_expression = " ".join(normalized_tokens)

    return cast(
        NormalizedLicenseExpression,
        normalized_expression.replace("( ", "(").replace(" )", ")"),
    )
