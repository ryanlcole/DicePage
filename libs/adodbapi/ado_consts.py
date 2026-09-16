# 020390.python.ado_consts.line1.comment ADO enumerated constants documented on MSDN:
# 020391.python.ado_consts.line2.comment https://learn.microsoft.com/en-us/sql/ado/reference/ado-api/ado-enumerated-constants
# 020392.python.ado_consts.line3.comment TODO: Update to https://learn.microsoft.com/en-us/sql/ado/reference/ado-api/ado-enumerated-constants

# 020393.python.ado_consts.line5.comment IsolationLevelEnum
adXactUnspecified = -1
adXactBrowse = 0x100
adXactChaos = 0x10
adXactCursorStability = 0x1000
adXactIsolated = 0x100000
adXactReadCommitted = 0x1000
adXactReadUncommitted = 0x100
adXactRepeatableRead = 0x10000
adXactSerializable = 0x100000

# 020394.python.ado_consts.line16.comment CursorLocationEnum
adUseClient = 3
adUseServer = 2

# 020395.python.ado_consts.line20.comment CursorTypeEnum
adOpenDynamic = 2
adOpenForwardOnly = 0
adOpenKeyset = 1
adOpenStatic = 3
adOpenUnspecified = -1

# 020396.python.ado_consts.line27.comment CommandTypeEnum
adCmdText = 1
adCmdStoredProc = 4
adSchemaTables = 20

# 020397.python.ado_consts.line32.comment ParameterDirectionEnum
adParamInput = 1
adParamInputOutput = 3
adParamOutput = 2
adParamReturnValue = 4
adParamUnknown = 0
directions = {
    0: "Unknown",
    1: "Input",
    2: "Output",
    3: "InputOutput",
    4: "Return",
}


def ado_direction_name(ado_dir):
    try:
        return "adParam" + directions[ado_dir]
    except:
        return f"unknown direction ({ado_dir})"


# 020398.python.ado_consts.line54.comment ObjectStateEnum
adStateClosed = 0
adStateOpen = 1
adStateConnecting = 2
adStateExecuting = 4
adStateFetching = 8

# 020399.python.ado_consts.line61.comment FieldAttributeEnum
adFldMayBeNull = 0x40

# 020400.python.ado_consts.line64.comment ConnectModeEnum
adModeUnknown = 0
adModeRead = 1
adModeWrite = 2
adModeReadWrite = 3
adModeShareDenyRead = 4
adModeShareDenyWrite = 8
adModeShareExclusive = 12
adModeShareDenyNone = 16
adModeRecursive = 0x400000

# 020401.python.ado_consts.line75.comment XactAttributeEnum
adXactCommitRetaining = 131072
adXactAbortRetaining = 262144

ado_error_TIMEOUT = -2147217871

# 020402.python.ado_consts.line81.comment DataTypeEnum - ADO Data types documented at:
# 020403.python.ado_consts.line82.comment http://msdn2.microsoft.com/en-us/library/ms675318.aspx
# 020404.python.ado_consts.line83.comment TODO: Update to https://learn.microsoft.com/en-us/sql/ado/reference/ado-api/datatypeenum
adArray = 0x2000
adEmpty = 0x0
adBSTR = 0x8
adBigInt = 0x14
adBinary = 0x80
adBoolean = 0xB
adChapter = 0x88
adChar = 0x81
adCurrency = 0x6
adDBDate = 0x85
adDBTime = 0x86
adDBTimeStamp = 0x87
adDate = 0x7
adDecimal = 0xE
adDouble = 0x5
adError = 0xA
adFileTime = 0x40
adGUID = 0x48
adIDispatch = 0x9
adIUnknown = 0xD
adInteger = 0x3
adLongVarBinary = 0xCD
adLongVarChar = 0xC9
adLongVarWChar = 0xCB
adNumeric = 0x83
adPropVariant = 0x8A
adSingle = 0x4
adSmallInt = 0x2
adTinyInt = 0x10
adUnsignedBigInt = 0x15
adUnsignedInt = 0x13
adUnsignedSmallInt = 0x12
adUnsignedTinyInt = 0x11
adUserDefined = 0x84
adVarBinary = 0xCC
adVarChar = 0xC8
adVarNumeric = 0x8B
adVarWChar = 0xCA
adVariant = 0xC
adWChar = 0x82
# 020405.python.ado_consts.line124.comment Additional constants used by introspection but not ADO itself
AUTO_FIELD_MARKER = -1000

adTypeNames = {
    adBSTR: "adBSTR",
    adBigInt: "adBigInt",
    adBinary: "adBinary",
    adBoolean: "adBoolean",
    adChapter: "adChapter",
    adChar: "adChar",
    adCurrency: "adCurrency",
    adDBDate: "adDBDate",
    adDBTime: "adDBTime",
    adDBTimeStamp: "adDBTimeStamp",
    adDate: "adDate",
    adDecimal: "adDecimal",
    adDouble: "adDouble",
    adEmpty: "adEmpty",
    adError: "adError",
    adFileTime: "adFileTime",
    adGUID: "adGUID",
    adIDispatch: "adIDispatch",
    adIUnknown: "adIUnknown",
    adInteger: "adInteger",
    adLongVarBinary: "adLongVarBinary",
    adLongVarChar: "adLongVarChar",
    adLongVarWChar: "adLongVarWChar",
    adNumeric: "adNumeric",
    adPropVariant: "adPropVariant",
    adSingle: "adSingle",
    adSmallInt: "adSmallInt",
    adTinyInt: "adTinyInt",
    adUnsignedBigInt: "adUnsignedBigInt",
    adUnsignedInt: "adUnsignedInt",
    adUnsignedSmallInt: "adUnsignedSmallInt",
    adUnsignedTinyInt: "adUnsignedTinyInt",
    adUserDefined: "adUserDefined",
    adVarBinary: "adVarBinary",
    adVarChar: "adVarChar",
    adVarNumeric: "adVarNumeric",
    adVarWChar: "adVarWChar",
    adVariant: "adVariant",
    adWChar: "adWChar",
}


def ado_type_name(ado_type):
    return adTypeNames.get(ado_type, f"unknown type ({ado_type})")


# 020406.python.ado_consts.line174.comment here in decimal, sorted by value
# 020407.python.ado_consts.line175.comment adEmpty 0 Specifies no value (DBTYPE_EMPTY).
# 020408.python.ado_consts.line176.comment adSmallInt 2 Indicates a two-byte signed integer (DBTYPE_I2).
# 020409.python.ado_consts.line177.comment adInteger 3 Indicates a four-byte signed integer (DBTYPE_I4).
# 020410.python.ado_consts.line178.comment adSingle 4 Indicates a single-precision floating-point value (DBTYPE_R4).
# 020411.python.ado_consts.line179.comment adDouble 5 Indicates a double-precision floating-point value (DBTYPE_R8).
# 020412.python.ado_consts.line180.comment adCurrency 6 Indicates a currency value (DBTYPE_CY). Currency is a fixed-point number
# 020413.python.ado_consts.line181.comment with four digits to the right of the decimal point. It is stored in an eight-byte signed integer scaled by 10,000.
# 020414.python.ado_consts.line182.comment adDate 7 Indicates a date value (DBTYPE_DATE). A date is stored as a double, the whole part of which is
# 020415.python.ado_consts.line183.comment the number of days since December 30, 1899, and the fractional part of which is the fraction of a day.
# 020416.python.ado_consts.line184.comment adBSTR 8 Indicates a null-terminated character string (Unicode) (DBTYPE_BSTR).
# 020417.python.ado_consts.line185.comment adIDispatch 9 Indicates a pointer to an IDispatch interface on a COM object (DBTYPE_IDISPATCH).
# 020418.python.ado_consts.line186.comment adError 10 Indicates a 32-bit error code (DBTYPE_ERROR).
# 020419.python.ado_consts.line187.comment adBoolean 11 Indicates a boolean value (DBTYPE_BOOL).
# 020420.python.ado_consts.line188.comment adVariant 12 Indicates an Automation Variant (DBTYPE_VARIANT).
# 020421.python.ado_consts.line189.comment adIUnknown 13 Indicates a pointer to an IUnknown interface on a COM object (DBTYPE_IUNKNOWN).
# 020422.python.ado_consts.line190.comment adDecimal 14 Indicates an exact numeric value with a fixed precision and scale (DBTYPE_DECIMAL).
# 020423.python.ado_consts.line191.comment adTinyInt 16 Indicates a one-byte signed integer (DBTYPE_I1).
# 020424.python.ado_consts.line192.comment adUnsignedTinyInt 17 Indicates a one-byte unsigned integer (DBTYPE_UI1).
# 020425.python.ado_consts.line193.comment adUnsignedSmallInt 18 Indicates a two-byte unsigned integer (DBTYPE_UI2).
# 020426.python.ado_consts.line194.comment adUnsignedInt 19 Indicates a four-byte unsigned integer (DBTYPE_UI4).
# 020427.python.ado_consts.line195.comment adBigInt 20 Indicates an eight-byte signed integer (DBTYPE_I8).
# 020428.python.ado_consts.line196.comment adUnsignedBigInt 21 Indicates an eight-byte unsigned integer (DBTYPE_UI8).
# 020429.python.ado_consts.line197.comment adFileTime 64 Indicates a 64-bit value representing the number of 100-nanosecond intervals since
# 020430.python.ado_consts.line198.comment January 1, 1601 (DBTYPE_FILETIME).
# 020431.python.ado_consts.line199.comment adGUID 72 Indicates a globally unique identifier (GUID) (DBTYPE_GUID).
# 020432.python.ado_consts.line200.comment adBinary 128 Indicates a binary value (DBTYPE_BYTES).
# 020433.python.ado_consts.line201.comment adChar 129 Indicates a string value (DBTYPE_STR).
# 020434.python.ado_consts.line202.comment adWChar 130 Indicates a null-terminated Unicode character string (DBTYPE_WSTR).
# 020435.python.ado_consts.line203.comment adNumeric 131 Indicates an exact numeric value with a fixed precision and scale (DBTYPE_NUMERIC).
# 020436.python.ado_consts.line204.comment adUserDefined 132 Indicates a user-defined variable (DBTYPE_UDT).
# 020437.python.ado_consts.line205.comment adUserDefined 132 Indicates a user-defined variable (DBTYPE_UDT).
# 020438.python.ado_consts.line206.comment adDBDate 133 Indicates a date value (yyyymmdd) (DBTYPE_DBDATE).
# 020439.python.ado_consts.line207.comment adDBTime 134 Indicates a time value (hhmmss) (DBTYPE_DBTIME).
# 020440.python.ado_consts.line208.comment adDBTimeStamp 135 Indicates a date/time stamp (yyyymmddhhmmss plus a fraction in billionths) (DBTYPE_DBTIMESTAMP).
# 020441.python.ado_consts.line209.comment adChapter 136 Indicates a four-byte chapter value that identifies rows in a child rowset (DBTYPE_HCHAPTER).
# 020442.python.ado_consts.line210.comment adPropVariant 138 Indicates an Automation PROPVARIANT (DBTYPE_PROP_VARIANT).
# 020443.python.ado_consts.line211.comment adVarNumeric 139 Indicates a numeric value (Parameter object only).
# 020444.python.ado_consts.line212.comment adVarChar 200 Indicates a string value (Parameter object only).
# 020445.python.ado_consts.line213.comment adLongVarChar 201 Indicates a long string value (Parameter object only).
# 020446.python.ado_consts.line214.comment adVarWChar 202 Indicates a null-terminated Unicode character string (Parameter object only).
# 020447.python.ado_consts.line215.comment adLongVarWChar 203 Indicates a long null-terminated Unicode string value (Parameter object only).
# 020448.python.ado_consts.line216.comment adVarBinary 204 Indicates a binary value (Parameter object only).
# 020449.python.ado_consts.line217.comment adLongVarBinary 205 Indicates a long binary value (Parameter object only).
# 020450.python.ado_consts.line218.comment adArray (Does not apply to ADOX.) 0x2000 A flag value, always combined with another data type constant,
# 020451.python.ado_consts.line219.comment that indicates an array of that other data type.

# 020452.python.ado_consts.line221.comment Error codes to names
adoErrors = {
    0xE7B: "adErrBoundToCommand",
    0xE94: "adErrCannotComplete",
    0xEA4: "adErrCantChangeConnection",
    0xC94: "adErrCantChangeProvider",
    0xE8C: "adErrCantConvertvalue",
    0xE8D: "adErrCantCreate",
    0xEA3: "adErrCatalogNotSet",
    0xE8E: "adErrColumnNotOnThisRow",
    0xD5D: "adErrDataConversion",
    0xE89: "adErrDataOverflow",
    0xE9A: "adErrDelResOutOfScope",
    0xEA6: "adErrDenyNotSupported",
    0xEA7: "adErrDenyTypeNotSupported",
    0xCB3: "adErrFeatureNotAvailable",
    0xEA5: "adErrFieldsUpdateFailed",
    0xC93: "adErrIllegalOperation",
    0xCAE: "adErrInTransaction",
    0xE87: "adErrIntegrityViolation",
    0xBB9: "adErrInvalidArgument",
    0xE7D: "adErrInvalidConnection",
    0xE7C: "adErrInvalidParamInfo",
    0xE82: "adErrInvalidTransaction",
    0xE91: "adErrInvalidURL",
    0xCC1: "adErrItemNotFound",
    0xBCD: "adErrNoCurrentRecord",
    0xE83: "adErrNotExecuting",
    0xE7E: "adErrNotReentrant",
    0xE78: "adErrObjectClosed",
    0xD27: "adErrObjectInCollection",
    0xD5C: "adErrObjectNotSet",
    0xE79: "adErrObjectOpen",
    0xBBA: "adErrOpeningFile",
    0xE80: "adErrOperationCancelled",
    0xE96: "adErrOutOfSpace",
    0xE88: "adErrPermissionDenied",
    0xE9E: "adErrPropConflicting",
    0xE9B: "adErrPropInvalidColumn",
    0xE9C: "adErrPropInvalidOption",
    0xE9D: "adErrPropInvalidValue",
    0xE9F: "adErrPropNotAllSettable",
    0xEA0: "adErrPropNotSet",
    0xEA1: "adErrPropNotSettable",
    0xEA2: "adErrPropNotSupported",
    0xBB8: "adErrProviderFailed",
    0xE7A: "adErrProviderNotFound",
    0xBBB: "adErrReadFile",
    0xE93: "adErrResourceExists",
    0xE92: "adErrResourceLocked",
    0xE97: "adErrResourceOutOfScope",
    0xE8A: "adErrSchemaViolation",
    0xE8B: "adErrSignMismatch",
    0xE81: "adErrStillConnecting",
    0xE7F: "adErrStillExecuting",
    0xE90: "adErrTreePermissionDenied",
    0xE8F: "adErrURLDoesNotExist",
    0xE99: "adErrURLNamedRowDoesNotExist",
    0xE98: "adErrUnavailable",
    0xE84: "adErrUnsafeOperation",
    0xE95: "adErrVolumeNotFound",
    0xBBC: "adErrWriteFile",
}
