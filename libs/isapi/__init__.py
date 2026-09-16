# 021256.python.init.line1.comment The Python ISAPI package.


# 021257.python.init.line4.comment Exceptions thrown by the DLL framework.
class ISAPIError(Exception):
    def __init__(self, errno, strerror=None, funcname=None):
        # 021258.python.init.line7.comment named attributes match OSError etc.
        self.errno = errno
        self.strerror = strerror
        self.funcname = funcname
        Exception.__init__(self, errno, strerror, funcname)

    def __str__(self):
        if self.strerror is None:
            try:
                import win32api

                self.strerror = win32api.FormatMessage(self.errno).strip()
            except:
                self.strerror = "no error message is available"
        # 021259.python.init.line21.comment str() looks like a win32api error.
        return str((self.errno, self.strerror, self.funcname))


class FilterError(ISAPIError):
    pass


class ExtensionError(ISAPIError):
    pass


# 021260.python.init.line33.comment A little development aid - a filter or extension callback function can
# 021261.python.init.line34.comment raise one of these exceptions, and the handler module will be reloaded.
# 021262.python.init.line35.comment This means you can change your code without restarting IIS.
# 021263.python.init.line36.comment After a reload, your filter/extension will have the GetFilterVersion/
# 021264.python.init.line37.comment GetExtensionVersion function called, but with None as the first arg.
class InternalReloadException(Exception):
    pass
