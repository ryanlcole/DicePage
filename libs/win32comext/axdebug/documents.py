"""Management of documents for AXDebugging."""

import pythoncom
import win32api
from win32com.server.util import unwrap

from . import axdebug, gateways
from .util import _wrap, trace

# 050846.python.documents.line10.comment def trace(*args):
# 050847.python.documents.line11.comment pass


def GetGoodFileName(fname):
    if fname[0] != "<":
        return win32api.GetFullPathName(fname)
    return fname


class DebugDocumentProvider(gateways.DebugDocumentProvider):
    def __init__(self, doc):
        self.doc = doc

    def GetName(self, dnt):
        return self.doc.GetName(dnt)

    def GetDocumentClassId(self):
        return self.doc.GetDocumentClassId()

    def GetDocument(self):
        return self.doc


class DebugDocumentText(gateways.DebugDocumentText):
    _com_interfaces_ = (
        gateways.DebugDocumentInfo._com_interfaces_
        + gateways.DebugDocumentText._com_interfaces_
        + gateways.DebugDocument._com_interfaces_
    )
    _public_methods_ = (
        gateways.DebugDocumentInfo._public_methods_
        + gateways.DebugDocumentText._public_methods_
        + gateways.DebugDocument._public_methods_
    )

    # 050848.python.documents.line46.comment A class which implements a DebugDocumentText, using the functionality
    # 050849.python.documents.line47.comment provided by a codeContainer
    def __init__(self, codeContainer):
        gateways.DebugDocumentText.__init__(self)
        gateways.DebugDocumentInfo.__init__(self)
        gateways.DebugDocument.__init__(self)
        self.codeContainer = codeContainer

    def _Close(self):
        self.docContexts = None
        # 050850.python.documents.line56.comment self.codeContainer._Close()
        self.codeContainer = None

    # 050851.python.documents.line59.comment IDebugDocumentInfo
    def GetName(self, dnt):
        return self.codeContainer.GetName(dnt)

    def GetDocumentClassId(self):
        return "{DF630910-1C1D-11d0-AE36-8C0F5E000000}"

    # 050852.python.documents.line66.comment IDebugDocument has no methods!
    # 050853.python.documents.line67.comment

    # 050854.python.documents.line69.comment IDebugDocumentText methods.
    # 050855.python.documents.line70.comment def GetDocumentAttributes
    def GetSize(self):
        # 050856.python.documents.line72.comment trace("GetSize")
        return self.codeContainer.GetNumLines(), self.codeContainer.GetNumChars()

    def GetPositionOfLine(self, cLineNumber):
        return self.codeContainer.GetPositionOfLine(cLineNumber)

    def GetLineOfPosition(self, charPos):
        return self.codeContainer.GetLineOfPosition(charPos)

    def GetText(self, charPos, maxChars, wantAttr):
        # 050857.python.documents.line82.comment Get all the attributes, else the tokenizer will get upset.
        # 050858.python.documents.line83.comment XXX - not yet!
        # 050859.python.documents.line84.comment trace("GetText", charPos, maxChars, wantAttr)
        cont = self.codeContainer
        attr = cont.GetSyntaxColorAttributes()
        return cont.GetText(), attr

    def GetPositionOfContext(self, context):
        trace("GetPositionOfContext", context)
        context = unwrap(context)
        return context.offset, context.length

    # 050860.python.documents.line94.comment Return a DebugDocumentContext.
    def GetContextOfPosition(self, charPos, maxChars):
        # 050861.python.documents.line96.comment Make one
        doc = _wrap(self, axdebug.IID_IDebugDocument)
        rc = self.codeContainer.GetCodeContextAtPosition(charPos)
        return rc.QueryInterface(axdebug.IID_IDebugDocumentContext)


class CodeContainerProvider:
    """An abstract Python class which provides code containers!

    Given a Python file name (as the debugger knows it by) this will
    return a CodeContainer interface suitable for use.

    This provides a simple base implementation that simply supports
    a dictionary of nodes and providers.
    """

    def __init__(self):
        self.ccsAndNodes = {}

    def AddCodeContainer(self, cc, node=None):
        fname = GetGoodFileName(cc.fileName)
        self.ccsAndNodes[fname] = cc, node

    def FromFileName(self, fname):
        cc, node = self.ccsAndNodes.get(GetGoodFileName(fname), (None, None))
        # 050862.python.documents.line121.comment if cc is None:
        # 050863.python.documents.line122.comment print(f"FromFileName for {fname} returning None")
        return cc

    def Close(self):
        for cc, node in self.ccsAndNodes.values():
            try:
                # 050864.python.documents.line128.comment Must close the node before closing the provider
                # 050865.python.documents.line129.comment as node may make calls on provider (eg Reset breakpoints etc)
                if node is not None:
                    node.Close()
                cc._Close()
            except pythoncom.com_error:
                pass
        self.ccsAndNodes = {}
