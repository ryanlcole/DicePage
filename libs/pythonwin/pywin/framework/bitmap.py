import os
import sys

import win32api
import win32con
import win32ui
from pywin.mfc import docview, window

bStretch = 1


class BitmapDocument(docview.Document):
    "A bitmap document.  Holds the bitmap data itself."

    def __init__(self, template):
        docview.Document.__init__(self, template)
        self.bitmap = None

    def OnNewDocument(self):
        # 037238.python.bitmap.line20.comment I can not create new bitmaps.
        win32ui.MessageBox("Bitmaps can not be created.")

    def OnOpenDocument(self, filename):
        self.bitmap = win32ui.CreateBitmap()
        # 037239.python.bitmap.line25.comment init data members
        f = open(filename, "rb")
        try:
            try:
                self.bitmap.LoadBitmapFile(f)
            except OSError:
                win32ui.MessageBox("Could not load the bitmap from %s" % filename)
                return 0
        finally:
            f.close()
        self.size = self.bitmap.GetSize()
        return 1

    def DeleteContents(self):
        self.bitmap = None


class BitmapView(docview.ScrollView):
    "A view of a bitmap.  Obtains data from document."

    def __init__(self, doc):
        docview.ScrollView.__init__(self, doc)
        self.width = self.height = 0
        # 037240.python.bitmap.line48.comment set up message handlers
        self.HookMessage(self.OnSize, win32con.WM_SIZE)

    def OnInitialUpdate(self):
        doc = self.GetDocument()
        if doc.bitmap:
            bitmapSize = doc.bitmap.GetSize()
            self.SetScrollSizes(win32con.MM_TEXT, bitmapSize)

    def OnSize(self, params):
        lParam = params[3]
        self.width = win32api.LOWORD(lParam)
        self.height = win32api.HIWORD(lParam)

    def OnDraw(self, dc):
        # 037241.python.bitmap.line63.comment set sizes used for "non stretch" mode.
        doc = self.GetDocument()
        if doc.bitmap is None:
            return
        bitmapSize = doc.bitmap.GetSize()
        if bStretch:
            # 037242.python.bitmap.line69.comment stretch BMP.
            viewRect = (0, 0, self.width, self.height)
            bitmapRect = (0, 0, bitmapSize[0], bitmapSize[1])
            doc.bitmap.Paint(dc, viewRect, bitmapRect)
        else:
            # 037243.python.bitmap.line74.comment non stretch.
            doc.bitmap.Paint(dc)


class BitmapFrame(window.MDIChildWnd):
    def OnCreateClient(self, createparams, context):
        borderX = win32api.GetSystemMetrics(win32con.SM_CXFRAME)
        borderY = win32api.GetSystemMetrics(win32con.SM_CYFRAME)
        titleY = win32api.GetSystemMetrics(win32con.SM_CYCAPTION)  # includes border
        # 037245.python.bitmap.line83.comment try and maintain default window pos, else adjust if can't fit
        # 037246.python.bitmap.line84.comment get the main client window dimensions.
        mdiClient = win32ui.GetMainFrame().GetWindow(win32con.GW_CHILD)
        clientWindowRect = mdiClient.ScreenToClient(mdiClient.GetWindowRect())
        clientWindowSize = (
            clientWindowRect[2] - clientWindowRect[0],
            clientWindowRect[3] - clientWindowRect[1],
        )
        left, top, right, bottom = mdiClient.ScreenToClient(self.GetWindowRect())
        # 037247.python.bitmap.line92.comment width, height=context.doc.size[0], context.doc.size[1]
        # 037248.python.bitmap.line93.comment width = width+borderX*2
        # 037249.python.bitmap.line94.comment height= height+titleY+borderY*2-1
        # 037250.python.bitmap.line95.comment if (left+width)>clientWindowSize[0]:
        # 037251.python.bitmap.line96.comment left = clientWindowSize[0] - width
        # 037252.python.bitmap.line97.comment if left<0:
        # 037253.python.bitmap.line98.comment left = 0
        # 037254.python.bitmap.line99.comment width = clientWindowSize[0]
        # 037255.python.bitmap.line100.comment if (top+height)>clientWindowSize[1]:
        # 037256.python.bitmap.line101.comment top = clientWindowSize[1] - height
        # 037257.python.bitmap.line102.comment if top<0:
        # 037258.python.bitmap.line103.comment top = 0
        # 037259.python.bitmap.line104.comment height = clientWindowSize[1]
        # 037260.python.bitmap.line105.comment self.frame.MoveWindow((left, top, left+width, top+height),0)
        window.MDIChildWnd.OnCreateClient(self, createparams, context)
        return 1


class BitmapTemplate(docview.DocTemplate):
    def __init__(self):
        docview.DocTemplate.__init__(
            self, win32ui.IDR_PYTHONTYPE, BitmapDocument, BitmapFrame, BitmapView
        )

    def MatchDocType(self, fileName, fileType):
        doc = self.FindOpenDocument(fileName)
        if doc:
            return doc
        ext = os.path.splitext(fileName)[1].lower()
        if ext == ".bmp":  # removed due to PIL! or ext=='.ppm':
            return win32ui.CDocTemplate_Confidence_yesAttemptNative
        return win32ui.CDocTemplate_Confidence_maybeAttemptForeign


# 037262.python.bitmap.line126.comment return win32ui.CDocTemplate_Confidence_noAttempt

# 037263.python.bitmap.line128.comment For debugging purposes, when this module may be reloaded many times.
try:
    win32ui.GetApp().RemoveDocTemplate(bitmapTemplate)  # type: ignore[has-type, used-before-def]
except NameError:
    pass

bitmapTemplate = BitmapTemplate()
bitmapTemplate.SetDocStrings(
    "\nBitmap\nBitmap\nBitmap (*.bmp)\n.bmp\nPythonBitmapFileType\nPython Bitmap File"
)
win32ui.GetApp().AddDocTemplate(bitmapTemplate)

# 037265.python.bitmap.line140.comment This works, but just didn't make it through the code reorg.
# 037266.python.bitmap.line141.comment class PPMBitmap(Bitmap):
# 037267.python.bitmap.line142.comment def LoadBitmapFile(self, file ):
# 037268.python.bitmap.line143.comment magic=file.readline()
# 037269.python.bitmap.line144.comment if magic <> "P6\n":
# 037270.python.bitmap.line145.comment raise TypeError, "The file is not a PPM format file"
# 037271.python.bitmap.line146.comment rowcollist=file.readline().split()
# 037272.python.bitmap.line147.comment cols=int(rowcollist[0])
# 037273.python.bitmap.line148.comment rows=int(rowcollist[1])
# 037274.python.bitmap.line149.comment file.readline()	# what's this one?
# 037275.python.bitmap.line150.comment self.bitmap.LoadPPMFile(file,(cols,rows))


def t():
    bitmapTemplate.OpenDocumentFile("d:\\winnt\\arcade.bmp")
    # 037276.python.bitmap.line155.comment OpenBMPFile( 'd:\\winnt\\arcade.bmp')


def demo():
    import glob

    winDir = win32api.GetWindowsDirectory()
    if sys.version_info >= (3, 10):
        fileNames = glob.glob("*.bmp", root_dir=winDir)[:2]
    else:
        fileNames = glob.glob1(winDir, "*.bmp")[:2]

    for fileName in fileNames:
        bitmapTemplate.OpenDocumentFile(os.path.join(winDir, fileName))
