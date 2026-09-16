# 030694.python.init.line1.comment objective-ctypes
# 030695.python.init.line2.comment
# 030696.python.init.line3.comment Copyright (c) 2011, Phillip Nguyen
# 030697.python.init.line4.comment All rights reserved.
# 030698.python.init.line5.comment
# 030699.python.init.line6.comment Redistribution and use in source and binary forms, with or without
# 030700.python.init.line7.comment modification, are permitted provided that the following conditions
# 030701.python.init.line8.comment are met:
# 030702.python.init.line9.comment
# 030703.python.init.line10.comment Redistributions of source code must retain the above copyright
# 030704.python.init.line11.comment notice, this list of conditions and the following disclaimer.
# 030705.python.init.line12.comment Redistributions in binary form must reproduce the above copyright
# 030706.python.init.line13.comment notice, this list of conditions and the following disclaimer in the
# 030707.python.init.line14.comment documentation and/or other materials provided with the distribution.
# 030708.python.init.line15.comment Neither the name of objective-ctypes nor the names of its
# 030709.python.init.line16.comment contributors may be used to endorse or promote products derived from
# 030710.python.init.line17.comment this software without specific prior written permission.
# 030711.python.init.line18.comment
# 030712.python.init.line19.comment THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# 030713.python.init.line20.comment "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# 030714.python.init.line21.comment LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# 030715.python.init.line22.comment FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# 030716.python.init.line23.comment COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# 030717.python.init.line24.comment INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# 030718.python.init.line25.comment BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# 030719.python.init.line26.comment LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# 030720.python.init.line27.comment CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# 030721.python.init.line28.comment LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# 030722.python.init.line29.comment ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# 030723.python.init.line30.comment POSSIBILITY OF SUCH DAMAGE.
from contextlib import contextmanager

from .runtime import objc, send_message, send_super, AutoReleasePool
from .runtime import get_selector
from .runtime import ObjCClass, ObjCInstance, ObjCSubclass

from .cocoatypes import *
from .cocoalibs import *

