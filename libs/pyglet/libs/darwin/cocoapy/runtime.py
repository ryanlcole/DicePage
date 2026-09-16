# 030827.python.runtime.line1.comment objective-ctypes
# 030828.python.runtime.line2.comment
# 030829.python.runtime.line3.comment Copyright (c) 2011, Phillip Nguyen
# 030830.python.runtime.line4.comment All rights reserved.
# 030831.python.runtime.line5.comment
# 030832.python.runtime.line6.comment Redistribution and use in source and binary forms, with or without
# 030833.python.runtime.line7.comment modification, are permitted provided that the following conditions
# 030834.python.runtime.line8.comment are met:
# 030835.python.runtime.line9.comment
# 030836.python.runtime.line10.comment Redistributions of source code must retain the above copyright
# 030837.python.runtime.line11.comment notice, this list of conditions and the following disclaimer.
# 030838.python.runtime.line12.comment Redistributions in binary form must reproduce the above copyright
# 030839.python.runtime.line13.comment notice, this list of conditions and the following disclaimer in the
# 030840.python.runtime.line14.comment documentation and/or other materials provided with the distribution.
# 030841.python.runtime.line15.comment Neither the name of objective-ctypes nor the names of its
# 030842.python.runtime.line16.comment contributors may be used to endorse or promote products derived from
# 030843.python.runtime.line17.comment this software without specific prior written permission.
# 030844.python.runtime.line18.comment
# 030845.python.runtime.line19.comment THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# 030846.python.runtime.line20.comment "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# 030847.python.runtime.line21.comment LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# 030848.python.runtime.line22.comment FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# 030849.python.runtime.line23.comment COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# 030850.python.runtime.line24.comment INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# 030851.python.runtime.line25.comment BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# 030852.python.runtime.line26.comment LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# 030853.python.runtime.line27.comment CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# 030854.python.runtime.line28.comment LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# 030855.python.runtime.line29.comment ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# 030856.python.runtime.line30.comment POSSIBILITY OF SUCH DAMAGE.
from __future__ import annotations

import sys
import platform
import struct
import weakref
from contextlib import contextmanager

from ctypes import *
from ctypes import util
from typing import Type, TypeVar, Sequence, Any

from .cocoatypes import *

__LP64__ = (8 * struct.calcsize("P") == 64)
__i386__ = (platform.machine() == 'i386')
__arm64__ = (platform.machine() == 'arm64')

if sizeof(c_void_p) == 4:
    c_ptrdiff_t = c_int32
elif sizeof(c_void_p) == 8:
    c_ptrdiff_t = c_int64

# 030857.python.runtime.line54.comment #####################################################################

lib = util.find_library('objc')

# 030858.python.runtime.line58.comment Hack for compatibility with macOS > 11.0
if lib is None:
    lib = '/usr/lib/libobjc.dylib'

objc = cdll.LoadLibrary(lib)
libc = cdll.LoadLibrary(util.find_library('c'))

# 030859.python.runtime.line65.comment void free(void *)
libc.free.restype = None
libc.free.argtypes = [c_void_p]

# 030860.python.runtime.line69.comment #####################################################################

# 030861.python.runtime.line71.comment BOOL class_addIvar(Class cls, const char *name, size_t size, uint8_t alignment, const char *types)
objc.class_addIvar.restype = c_bool
objc.class_addIvar.argtypes = [c_void_p, c_char_p, c_size_t, c_uint8, c_char_p]

# 030862.python.runtime.line75.comment BOOL class_addMethod(Class cls, SEL name, IMP imp, const char *types)
objc.class_addMethod.restype = c_bool

# 030863.python.runtime.line78.comment BOOL class_addProtocol(Class cls, Protocol *protocol)
objc.class_addProtocol.restype = c_bool
objc.class_addProtocol.argtypes = [c_void_p, c_void_p]

# 030864.python.runtime.line82.comment BOOL class_conformsToProtocol(Class cls, Protocol *protocol)
objc.class_conformsToProtocol.restype = c_bool
objc.class_conformsToProtocol.argtypes = [c_void_p, c_void_p]

# 030865.python.runtime.line86.comment Ivar * class_copyIvarList(Class cls, unsigned int *outCount)
# 030866.python.runtime.line87.comment Returns an array of pointers of type Ivar describing instance variables.
# 030867.python.runtime.line88.comment The array has *outCount pointers followed by a NULL terminator.
# 030868.python.runtime.line89.comment You must free() the returned array.
objc.class_copyIvarList.restype = POINTER(c_void_p)
objc.class_copyIvarList.argtypes = [c_void_p, POINTER(c_uint)]

# 030869.python.runtime.line93.comment Method * class_copyMethodList(Class cls, unsigned int *outCount)
# 030870.python.runtime.line94.comment Returns an array of pointers of type Method describing instance methods.
# 030871.python.runtime.line95.comment The array has *outCount pointers followed by a NULL terminator.
# 030872.python.runtime.line96.comment You must free() the returned array.
objc.class_copyMethodList.restype = POINTER(c_void_p)
objc.class_copyMethodList.argtypes = [c_void_p, POINTER(c_uint)]

# 030873.python.runtime.line100.comment objc_property_t * class_copyPropertyList(Class cls, unsigned int *outCount)
# 030874.python.runtime.line101.comment Returns an array of pointers of type objc_property_t describing properties.
# 030875.python.runtime.line102.comment The array has *outCount pointers followed by a NULL terminator.
# 030876.python.runtime.line103.comment You must free() the returned array.
objc.class_copyPropertyList.restype = POINTER(c_void_p)
objc.class_copyPropertyList.argtypes = [c_void_p, POINTER(c_uint)]

# 030877.python.runtime.line107.comment Protocol ** class_copyProtocolList(Class cls, unsigned int *outCount)
# 030878.python.runtime.line108.comment Returns an array of pointers of type Protocol* describing protocols.
# 030879.python.runtime.line109.comment The array has *outCount pointers followed by a NULL terminator.
# 030880.python.runtime.line110.comment You must free() the returned array.
objc.class_copyProtocolList.restype = POINTER(c_void_p)
objc.class_copyProtocolList.argtypes = [c_void_p, POINTER(c_uint)]

# 030881.python.runtime.line114.comment id class_createInstance(Class cls, size_t extraBytes)
objc.class_createInstance.restype = c_void_p
objc.class_createInstance.argtypes = [c_void_p, c_size_t]

# 030882.python.runtime.line118.comment Method class_getClassMethod(Class aClass, SEL aSelector)
# 030883.python.runtime.line119.comment Will also search superclass for implementations.
objc.class_getClassMethod.restype = c_void_p
objc.class_getClassMethod.argtypes = [c_void_p, c_void_p]

# 030884.python.runtime.line123.comment Ivar class_getClassVariable(Class cls, const char* name)
objc.class_getClassVariable.restype = c_void_p
objc.class_getClassVariable.argtypes = [c_void_p, c_char_p]

# 030885.python.runtime.line127.comment Method class_getInstanceMethod(Class aClass, SEL aSelector)
# 030886.python.runtime.line128.comment Will also search superclass for implementations.
objc.class_getInstanceMethod.restype = c_void_p
objc.class_getInstanceMethod.argtypes = [c_void_p, c_void_p]

# 030887.python.runtime.line132.comment size_t class_getInstanceSize(Class cls)
objc.class_getInstanceSize.restype = c_size_t
objc.class_getInstanceSize.argtypes = [c_void_p]

# 030888.python.runtime.line136.comment Ivar class_getInstanceVariable(Class cls, const char* name)
objc.class_getInstanceVariable.restype = c_void_p
objc.class_getInstanceVariable.argtypes = [c_void_p, c_char_p]

# 030889.python.runtime.line140.comment const char *class_getIvarLayout(Class cls)
objc.class_getIvarLayout.restype = c_char_p
objc.class_getIvarLayout.argtypes = [c_void_p]

# 030890.python.runtime.line144.comment IMP class_getMethodImplementation(Class cls, SEL name)
objc.class_getMethodImplementation.restype = c_void_p
objc.class_getMethodImplementation.argtypes = [c_void_p, c_void_p]

# 030891.python.runtime.line148.comment The function is marked as OBJC_ARM64_UNAVAILABLE.
if not __arm64__:
    # 030892.python.runtime.line150.comment IMP class_getMethodImplementation_stret(Class cls, SEL name)
    objc.class_getMethodImplementation_stret.restype = c_void_p
    objc.class_getMethodImplementation_stret.argtypes = [c_void_p, c_void_p]

# 030893.python.runtime.line154.comment const char * class_getName(Class cls)
objc.class_getName.restype = c_char_p
objc.class_getName.argtypes = [c_void_p]

# 030894.python.runtime.line158.comment objc_property_t class_getProperty(Class cls, const char *name)
objc.class_getProperty.restype = c_void_p
objc.class_getProperty.argtypes = [c_void_p, c_char_p]

# 030895.python.runtime.line162.comment Class class_getSuperclass(Class cls)
objc.class_getSuperclass.restype = c_void_p
objc.class_getSuperclass.argtypes = [c_void_p]

# 030896.python.runtime.line166.comment int class_getVersion(Class theClass)
objc.class_getVersion.restype = c_int
objc.class_getVersion.argtypes = [c_void_p]

# 030897.python.runtime.line170.comment const char *class_getWeakIvarLayout(Class cls)
objc.class_getWeakIvarLayout.restype = c_char_p
objc.class_getWeakIvarLayout.argtypes = [c_void_p]

# 030898.python.runtime.line174.comment BOOL class_isMetaClass(Class cls)
objc.class_isMetaClass.restype = c_bool
objc.class_isMetaClass.argtypes = [c_void_p]

# 030899.python.runtime.line178.comment IMP class_replaceMethod(Class cls, SEL name, IMP imp, const char *types)
objc.class_replaceMethod.restype = c_void_p
objc.class_replaceMethod.argtypes = [c_void_p, c_void_p, c_void_p, c_char_p]

# 030900.python.runtime.line182.comment BOOL class_respondsToSelector(Class cls, SEL sel)
objc.class_respondsToSelector.restype = c_bool
objc.class_respondsToSelector.argtypes = [c_void_p, c_void_p]

# 030901.python.runtime.line186.comment void class_setIvarLayout(Class cls, const char *layout)
objc.class_setIvarLayout.restype = None
objc.class_setIvarLayout.argtypes = [c_void_p, c_char_p]

# 030902.python.runtime.line190.comment Class class_setSuperclass(Class cls, Class newSuper)
objc.class_setSuperclass.restype = c_void_p
objc.class_setSuperclass.argtypes = [c_void_p, c_void_p]

# 030903.python.runtime.line194.comment void class_setVersion(Class theClass, int version)
objc.class_setVersion.restype = None
objc.class_setVersion.argtypes = [c_void_p, c_int]

# 030904.python.runtime.line198.comment void class_setWeakIvarLayout(Class cls, const char *layout)
objc.class_setWeakIvarLayout.restype = None
objc.class_setWeakIvarLayout.argtypes = [c_void_p, c_char_p]

# 030905.python.runtime.line202.comment #####################################################################

# 030906.python.runtime.line204.comment const char * ivar_getName(Ivar ivar)
objc.ivar_getName.restype = c_char_p
objc.ivar_getName.argtypes = [c_void_p]

# 030907.python.runtime.line208.comment ptrdiff_t ivar_getOffset(Ivar ivar)
objc.ivar_getOffset.restype = c_ptrdiff_t
objc.ivar_getOffset.argtypes = [c_void_p]

# 030908.python.runtime.line212.comment const char * ivar_getTypeEncoding(Ivar ivar)
objc.ivar_getTypeEncoding.restype = c_char_p
objc.ivar_getTypeEncoding.argtypes = [c_void_p]

# 030909.python.runtime.line216.comment #####################################################################

# 030910.python.runtime.line218.comment char * method_copyArgumentType(Method method, unsigned int index)
# 030911.python.runtime.line219.comment You must free() the returned string.
objc.method_copyArgumentType.restype = c_char_p
objc.method_copyArgumentType.argtypes = [c_void_p, c_uint]

# 030912.python.runtime.line223.comment char * method_copyReturnType(Method method)
# 030913.python.runtime.line224.comment You must free() the returned string.
objc.method_copyReturnType.restype = POINTER(c_char)
objc.method_copyReturnType.argtypes = [c_void_p]

# 030914.python.runtime.line228.comment void method_exchangeImplementations(Method m1, Method m2)
objc.method_exchangeImplementations.restype = None
objc.method_exchangeImplementations.argtypes = [c_void_p, c_void_p]

# 030915.python.runtime.line232.comment void method_getArgumentType(Method method, unsigned int index, char *dst, size_t dst_len)
# 030916.python.runtime.line233.comment Functionally similar to strncpy(dst, parameter_type, dst_len).
objc.method_getArgumentType.restype = None
objc.method_getArgumentType.argtypes = [c_void_p, c_uint, c_char_p, c_size_t]

# 030917.python.runtime.line237.comment IMP method_getImplementation(Method method)
objc.method_getImplementation.restype = c_void_p
objc.method_getImplementation.argtypes = [c_void_p]

# 030918.python.runtime.line241.comment SEL method_getName(Method method)
objc.method_getName.restype = c_void_p
objc.method_getName.argtypes = [c_void_p]

# 030919.python.runtime.line245.comment unsigned method_getNumberOfArguments(Method method)
objc.method_getNumberOfArguments.restype = c_uint
objc.method_getNumberOfArguments.argtypes = [c_void_p]

# 030920.python.runtime.line249.comment void method_getReturnType(Method method, char *dst, size_t dst_len)
# 030921.python.runtime.line250.comment Functionally similar to strncpy(dst, return_type, dst_len)
objc.method_getReturnType.restype = None
objc.method_getReturnType.argtypes = [c_void_p, c_char_p, c_size_t]

# 030922.python.runtime.line254.comment const char * method_getTypeEncoding(Method method)
objc.method_getTypeEncoding.restype = c_char_p
objc.method_getTypeEncoding.argtypes = [c_void_p]

# 030923.python.runtime.line258.comment IMP method_setImplementation(Method method, IMP imp)
objc.method_setImplementation.restype = c_void_p
objc.method_setImplementation.argtypes = [c_void_p, c_void_p]

# 030924.python.runtime.line262.comment #####################################################################

# 030925.python.runtime.line264.comment Class objc_allocateClassPair(Class superclass, const char *name, size_t extraBytes)
objc.objc_allocateClassPair.restype = c_void_p
objc.objc_allocateClassPair.argtypes = [c_void_p, c_char_p, c_size_t]

# 030926.python.runtime.line268.comment Protocol **objc_copyProtocolList(unsigned int *outCount)
# 030927.python.runtime.line269.comment Returns an array of *outcount pointers followed by NULL terminator.
# 030928.python.runtime.line270.comment You must free() the array.
objc.objc_copyProtocolList.restype = POINTER(c_void_p)
objc.objc_copyProtocolList.argtypes = [POINTER(c_int)]

# 030929.python.runtime.line274.comment id objc_getAssociatedObject(id object, void *key)
objc.objc_getAssociatedObject.restype = c_void_p
objc.objc_getAssociatedObject.argtypes = [c_void_p, c_void_p]

# 030930.python.runtime.line278.comment id objc_getClass(const char *name)
objc.objc_getClass.restype = c_void_p
objc.objc_getClass.argtypes = [c_char_p]

# 030931.python.runtime.line282.comment int objc_getClassList(Class *buffer, int bufferLen)
# 030932.python.runtime.line283.comment Pass None for buffer to obtain just the total number of classes.
objc.objc_getClassList.restype = c_int
objc.objc_getClassList.argtypes = [c_void_p, c_int]

# 030933.python.runtime.line287.comment id objc_getMetaClass(const char *name)
objc.objc_getMetaClass.restype = c_void_p
objc.objc_getMetaClass.argtypes = [c_char_p]

# 030934.python.runtime.line291.comment Protocol *objc_getProtocol(const char *name)
objc.objc_getProtocol.restype = c_void_p
objc.objc_getProtocol.argtypes = [c_char_p]

# 030935.python.runtime.line295.comment You should set return and argument types depending on context.
# 030936.python.runtime.line296.comment id objc_msgSend(id theReceiver, SEL theSelector, ...)
# 030937.python.runtime.line297.comment id objc_msgSendSuper(struct objc_super *super, SEL op,  ...)

# 030938.python.runtime.line299.comment The function is marked as OBJC_ARM64_UNAVAILABLE.
if not __arm64__:
    # 030939.python.runtime.line301.comment void objc_msgSendSuper_stret(struct objc_super *super, SEL op, ...)
    objc.objc_msgSendSuper_stret.restype = None

# 030940.python.runtime.line304.comment double objc_msgSend_fpret(id self, SEL op, ...)
# 030941.python.runtime.line305.comment objc.objc_msgSend_fpret.restype = c_double

# 030942.python.runtime.line307.comment The function is marked as OBJC_ARM64_UNAVAILABLE.
if not __arm64__:
    # 030943.python.runtime.line309.comment void objc_msgSend_stret(void * stretAddr, id theReceiver, SEL theSelector,  ...)
    objc.objc_msgSend_stret.restype = None

# 030944.python.runtime.line312.comment void objc_registerClassPair(Class cls)
objc.objc_registerClassPair.restype = None
objc.objc_registerClassPair.argtypes = [c_void_p]

# 030945.python.runtime.line316.comment void objc_removeAssociatedObjects(id object)
objc.objc_removeAssociatedObjects.restype = None
objc.objc_removeAssociatedObjects.argtypes = [c_void_p]

# 030946.python.runtime.line320.comment void objc_setAssociatedObject(id object, void *key, id value, objc_AssociationPolicy policy)
objc.objc_setAssociatedObject.restype = None
objc.objc_setAssociatedObject.argtypes = [c_void_p, c_void_p, c_void_p, c_int]

# 030947.python.runtime.line324.comment #####################################################################

# 030948.python.runtime.line326.comment id object_copy(id obj, size_t size)
objc.object_copy.restype = c_void_p
objc.object_copy.argtypes = [c_void_p, c_size_t]

# 030949.python.runtime.line330.comment id object_dispose(id obj)
objc.object_dispose.restype = c_void_p
objc.object_dispose.argtypes = [c_void_p]

# 030950.python.runtime.line334.comment Class object_getClass(id object)
objc.object_getClass.restype = c_void_p
objc.object_getClass.argtypes = [c_void_p]

# 030951.python.runtime.line338.comment const char *object_getClassName(id obj)
objc.object_getClassName.restype = c_char_p
objc.object_getClassName.argtypes = [c_void_p]

# 030952.python.runtime.line342.comment Ivar object_getInstanceVariable(id obj, const char *name, void **outValue)
objc.object_getInstanceVariable.restype = c_void_p
objc.object_getInstanceVariable.argtypes = [c_void_p, c_char_p, c_void_p]

# 030953.python.runtime.line346.comment id object_getIvar(id object, Ivar ivar)
objc.object_getIvar.restype = c_void_p
objc.object_getIvar.argtypes = [c_void_p, c_void_p]

# 030954.python.runtime.line350.comment Class object_setClass(id object, Class cls)
objc.object_setClass.restype = c_void_p
objc.object_setClass.argtypes = [c_void_p, c_void_p]

# 030955.python.runtime.line354.comment Ivar object_setInstanceVariable(id obj, const char *name, void *value)
# 030956.python.runtime.line355.comment Set argtypes based on the data type of the instance variable.
objc.object_setInstanceVariable.restype = c_void_p

# 030957.python.runtime.line358.comment void object_setIvar(id object, Ivar ivar, id value)
objc.object_setIvar.restype = None
objc.object_setIvar.argtypes = [c_void_p, c_void_p, c_void_p]

# 030958.python.runtime.line362.comment #####################################################################

# 030959.python.runtime.line364.comment const char *property_getAttributes(objc_property_t property)
objc.property_getAttributes.restype = c_char_p
objc.property_getAttributes.argtypes = [c_void_p]

# 030960.python.runtime.line368.comment const char *property_getName(objc_property_t property)
objc.property_getName.restype = c_char_p
objc.property_getName.argtypes = [c_void_p]

# 030961.python.runtime.line372.comment #####################################################################

# 030962.python.runtime.line374.comment BOOL protocol_conformsToProtocol(Protocol *proto, Protocol *other)
objc.protocol_conformsToProtocol.restype = c_bool
objc.protocol_conformsToProtocol.argtypes = [c_void_p, c_void_p]


class OBJC_METHOD_DESCRIPTION(Structure):
    _fields_ = [("name", c_void_p), ("types", c_char_p)]


# 030963.python.runtime.line383.comment struct objc_method_description *protocol_copyMethodDescriptionList(Protocol *p, BOOL isRequiredMethod, BOOL isInstanceMethod, unsigned int *outCount)
# 030964.python.runtime.line384.comment You must free() the returned array.
objc.protocol_copyMethodDescriptionList.restype = POINTER(OBJC_METHOD_DESCRIPTION)
objc.protocol_copyMethodDescriptionList.argtypes = [c_void_p, c_bool, c_bool, POINTER(c_uint)]

# 030965.python.runtime.line388.comment objc_property_t * protocol_copyPropertyList(Protocol *protocol, unsigned int *outCount)
objc.protocol_copyPropertyList.restype = c_void_p
objc.protocol_copyPropertyList.argtypes = [c_void_p, POINTER(c_uint)]

# 030966.python.runtime.line392.comment Protocol **protocol_copyProtocolList(Protocol *proto, unsigned int *outCount)
objc.protocol_copyProtocolList = POINTER(c_void_p)
objc.protocol_copyProtocolList.argtypes = [c_void_p, POINTER(c_uint)]

# 030967.python.runtime.line396.comment struct objc_method_description protocol_getMethodDescription(Protocol *p, SEL aSel, BOOL isRequiredMethod, BOOL isInstanceMethod)
objc.protocol_getMethodDescription.restype = OBJC_METHOD_DESCRIPTION
objc.protocol_getMethodDescription.argtypes = [c_void_p, c_void_p, c_bool, c_bool]

# 030968.python.runtime.line400.comment const char *protocol_getName(Protocol *p)
objc.protocol_getName.restype = c_char_p
objc.protocol_getName.argtypes = [c_void_p]

# 030969.python.runtime.line404.comment #####################################################################

# 030970.python.runtime.line406.comment const char* sel_getName(SEL aSelector)
objc.sel_getName.restype = c_char_p
objc.sel_getName.argtypes = [c_void_p]

# 030971.python.runtime.line410.comment SEL sel_getUid(const char *str)
# 030972.python.runtime.line411.comment Use sel_registerName instead.

# 030973.python.runtime.line413.comment BOOL sel_isEqual(SEL lhs, SEL rhs)
objc.sel_isEqual.restype = c_bool
objc.sel_isEqual.argtypes = [c_void_p, c_void_p]

# 030974.python.runtime.line417.comment SEL sel_registerName(const char *str)
objc.sel_registerName.restype = c_void_p
objc.sel_registerName.argtypes = [c_char_p]


# 030975.python.runtime.line422.comment #####################################################################
# 030976.python.runtime.line423.comment void *objc_autoreleasePoolPush(void)
objc.objc_autoreleasePoolPush.restype = c_void_p
objc.objc_autoreleasePoolPush.argtypes = []

# 030977.python.runtime.line427.comment void objc_autoreleasePoolPop(void *pool)
objc.objc_autoreleasePoolPop.restype = None
objc.objc_autoreleasePoolPop.argtypes = [c_void_p]

# 030978.python.runtime.line431.comment #####################################################################
# 030979.python.runtime.line432.comment Constants
OBJC_ASSOCIATION_ASSIGN = 0  # Weak reference to the associated object.
OBJC_ASSOCIATION_RETAIN = 0x0301  # Strong reference to the associated object. The association is made atomically.
OBJC_ASSOCIATION_COPY = 0x0303  # Specifies that the associated object is copied. The association is made atomically.


def ensure_bytes(x: bytes | str) -> bytes:
    """Attempt to encode an object as :py:class:`bytes`.

    If it is already :py:class:`bytes`, it will be returned as-is.
    Otherwise, this function attempt to convert ``x`` by assuming it
    has a string-like :py:meth:`~str.encode` method supporting
    ``'ascii'`` as an argument.

    Args:
        x: A :py:class:`bytes` or object with a string-like
         :py:meth:`~str.encode` method.

    Returns:
        :py:class:`bytes`
    """
    if isinstance(x, bytes):
        return x
    return x.encode('ascii')


# 030983.python.runtime.line458.comment #####################################################################

def get_selector(name: str | bytes) -> c_void_p:
    """Return a void pointer for a named ObjectiveC selector.

    See Apple's developer documentation on ``sel_registerName``:
    https://developer.apple.com/documentation/objectivec/1418557-sel_registername

    Args:
        name:
            An ObjectiveC selector name as bytes or a str

    Returns:
        A void pointer for the ObjectiveC selector.
    """
    return c_void_p(objc.sel_registerName(ensure_bytes(name)))


def get_class(name: bytes | str) -> c_void_p | None:
    """Try to get a ctypes void pointer for the named ObjectiveC class.

    If no class with the name exists, this function returns None
    instead.

    See Apple's developer documentation for ``objc_getClass``:
    https://developer.apple.com/documentation/objectivec/1418952-objc_getclass

     Args:
        name:
            A name of an ObjectiveC class as a Python bytes or string
            object.

    Returns:
        A void pointer to the class or None if it wasn't found.
    """
    return c_void_p(objc.objc_getClass(ensure_bytes(name)))


def get_object_class(obj: c_void_p) -> c_void_p | None:
    """Get the ObjectiveC class for an object or None if it's nil.

    See Apple's developer documentation for ``object_GetClass``.
    https://developer.apple.com/documentation/objectivec/1418629-object_getclass/

    Args:
        obj:
            A void pointer to an ObjectiveC object.

    Returns:
         A void pointer to the ObjectiveC class object.
    """
    return c_void_p(objc.object_getClass(obj))


def get_metaclass(name: str | bytes) -> c_void_p | None:
    """Try to get a pointer to the metaclass for an ObjectiveC class name.

    If the class isn't registered with the ObjectiveC runtime, returns
    None.

    See the following to learn more:

    * Sealie Software's explanation of ObjectiveC metaclasses:
      https://www.sealiesoftware.com/blog/archive/2009/04/14/objc_explain_Classes_and_metaclasses.html
    * Apple's developer documentation for ``objc_getMetaClass``:
      https://developer.apple.com/documentation/objectivec/1418721-objc_getmetaclass/

    Args:
        name:
            The name of an ObjectiveC class as a Python string or
            bytes object.
    Returns:
         A void pointer if an ObjectiveC metaclass was found for the
         class name, or None if it wasn't.
    """
    return c_void_p(objc.objc_getMetaClass(ensure_bytes(name)))


def get_superclass_of_object(obj: c_void_p) -> c_void_p | None:
    """Try to get a pointer to the ObjectiveC superclass of an object.

    See the following to learn more:
    * https://developer.apple.com/documentation/objectivec/1418629-object_getclass/
    * https://developer.apple.com/documentation/objectivec/1418498-class_getsuperclass

    Args:
        obj:
            A pointer to an ObjectiveC object.

    Returns:
        * None if the object is Nil or an instance of a root class
        * Otherwise, a ctypes void pointer to ``obj``'s ObjectiveC superclass

    """
    cls = c_void_p(objc.object_getClass(obj))
    return c_void_p(objc.class_getSuperclass(cls))


# 030984.python.runtime.line556.comment executive summary: on x86-64, who knows?
def x86_should_use_stret(restype: Type) -> bool:
    """True when a message should be sent via struct-specific function.

    Usually, a message which returns a data structure should be sent via
    ``objc_msgSend_stret``. On some platforms, a data structure below a
    platform-specific size can instead be returned via the stack as a
    simple return value.

    This function returns ``True`` if the passed message result type
    seems big enough to use `obj_msgSend_stret` instead of other message
    sending functions.

    Note that this is a best guess based on available information. See
    the following to learn more:

    * Sealie Software's overview of objc_msgSend_stret
      http://www.sealiesoftware.com/blog/archive/2008/10/30/objc_explain_objc_msgSend_stret.html
    * Apple's developer documentation for objc_msgSend_stret
      http://www.sealiesoftware.com/blog/archive/2008/10/30/objc_explain_objc_msgSend_stret.html
    * Pages 20-27 of The System V ABI (The Stack Frame)
      https://cs61.seas.harvard.edu/site/pdf/x86-64-abi-20210928.pdf

    Args:
        restype:
            A :py:mod:`ctypes` representation of an ObjectiveC message
            result's type.
    Returns:
         ``True`` if it seems `objc_msgSend_stret` should be used;
         ``False`` if it shouldn't.
    """
    if type(restype) != type(Structure):
        return False
    if not __LP64__ and sizeof(restype) <= 8:  # type: ignore
        return False
    # 030986.python.runtime.line591.comment maybe? I don't know?
    if __LP64__ and sizeof(restype) <= 16:  # type: ignore
        return False
    return True


def should_use_fpret(restype: Type) -> bool:
    """True if the result type is known to need a non-integer call

    On Macs running on x86 or amd64 processors, ObjectiveC messages
    returning non-integer data types may need to be sent using
    `objc_msgSend_fpret`_. This function returns ``True`` if the
    current processor and platform features indicate this is the case.

    To learn more, see:

    * Sealie Software'e overview of objc_msgSend_fpret:
      http://www.sealiesoftware.com/blog/archive/2008/11/16/objc_explain_objc_msgSend_fpret.html
    * Apple's developer documentation on objc_msgSend_fpret:
      https://developer.apple.com/documentation/objectivec/1456697-objc_msgsend_fpret

    Args:
        restype: A :py:mod:`ctypes` type.

    Returns:
        ``True`` if `objc_msgSend_fpret`_ should be used, ``False``
        otherwise.
    """
    if not __i386__:
        # 030988.python.runtime.line620.comment Unneeded on non-intel processors
        return False
    if __LP64__ and restype == c_longdouble:
        # 030989.python.runtime.line623.comment Use only for long double on x86_64
        return True
    if not __LP64__ and restype in (c_float, c_double, c_longdouble):
        return True
    return False


# 030990.python.runtime.line630.comment There's no way to cleanly annotate a ctypes object right now.
# 030991.python.runtime.line631.comment For the moment, we'll use this to define message result types.
_CTypesResType = TypeVar('_CTypesResType')


def send_message(
        receiver: str | c_void_p | ObjCInstance,
        selector_name: str | bytes,
        *args,
        restype: Type[_CTypesResType] = c_void_p,
        argtypes: Sequence[Type] | None = None,
        **_  # For compatibility with the pre-annotation signature
) -> _CTypesResType | None:
    """Send an ObjectiveC message and return the result's value.

    **WARNING: On ARM64, ``argtypes`` is mandatory**!

    This function chooses the best known approach for sending the
    message based on:

    * Whether ``restype`` is a float or double type
    * ``sizeof(restype)``
    * Platform-specific stack behavior

    The ctypes objects passed to ``args`` must match the ctypes types in
    ``argytypes``. Unspecified ``argtypes`` are handled differently by
    different system architectures:

    * On ARM64, the function fails
    * On x86 / AMD64, all ``args`` assumed to be wrapped in c_void_p

    New code should specify the ``argtypes`` since all new Macs will be
    ARM64 for the foreseeable future.

    To learn more about ObjectiveC's message sending, see:

    * https://docs.python.org/3.8/library/ctypes.html#calling-variadic-functions
    * The x86_should_use_stret function in this file
    * The should_use_fpret function in this file
    * Apple's developer documentation on objc_msgSend:
      https://developer.apple.com/documentation/objectivec/1456712-objc_msgsend

    Args:
        receiver:
            A Python string for a class name or a c_void_p to an
            ObjectiveC class.
        selector_name:
            A selector name as Python string or bytes object
        *args:
            ctypes objects to send as the message arguments. These must
            match the types in ``argtypes`` if they're specified.
        restype:
            A ctypes representation of the message result's expected
            return type.
        argtypes:
            A list of ctypes types each of the arguments in *args must
            match. ARM64 fails if this is unspecified. Otherwise, they
            are all assumed to be c_void_p.
        **_:
            Backward compatibility with the original function signature.

    Returns:
       The result of the message, if any.

    """

    # 030993.python.runtime.line696.comment print('send_message', receiver, selector_name, args, restype, argtypes)

    # 030994.python.runtime.line698.comment Shared preprocessing & default filling
    if isinstance(receiver, str):
        receiver = get_class(receiver)
    if not argtypes:  # Skips casting for empty tuples
        argtypes = []
    selector = get_selector(selector_name)

    # 030996.python.runtime.line705.comment Use restype to select the correct version of objc_msgSend

    # 030997.python.runtime.line707.comment Non-integer numbers get special treatment
    # 030998.python.runtime.line708.comment https://developer.apple.com/documentation/objectivec/1456697-objc_msgsend_fpret
    if should_use_fpret(restype):
        # 030999.python.runtime.line710.comment Configure the message
        objc.objc_msgSend_fpret.restype = restype
        full_message_arg_types = [
            c_void_p,  # ObjectiveC self
            c_void_p   # ObjectiveC handler method
        ]
        full_message_arg_types.extend(argtypes)
        objc.objc_msgSend_fpret.argtypes = full_message_arg_types

        result = objc.objc_msgSend_fpret(receiver, selector, *args)

    # 031002.python.runtime.line721.comment Structs use a special call except for tiny ones on x86/AMD64
    # 031003.python.runtime.line722.comment https://developer.apple.com/documentation/objectivec/1456730-objc_msgsend_stret
    elif x86_should_use_stret(restype):
        full_message_arg_types = [
            POINTER(restype),  # ObjectiveC Struct instance
            c_void_p,  # Message receiver
            c_void_p  # Selector
        ]
        full_message_arg_types.extend(argtypes)
        objc.objc_msgSend_stret.argtypes = full_message_arg_types

        # 031007.python.runtime.line732.comment Allocate a struct instance to hold results & pass a pointer to it
        result = restype()
        objc.objc_msgSend_stret(byref(result), receiver, selector, *args)

    # 031008.python.runtime.line736.comment Default to objc_msgSend for "simple values"
    # 031009.python.runtime.line737.comment https://developer.apple.com/documentation/objectivec/1456712-objc_msgsend
    else:
        objc.objc_msgSend.restype = restype
        full_message_arg_types = [
            c_void_p,  # ObjectiveC self
            c_void_p  # Handler method
        ]
        full_message_arg_types.extend(argtypes)
        objc.objc_msgSend.argtypes = full_message_arg_types

        # 031012.python.runtime.line747.comment Unless restype is specified, wrap the result in a void pointer
        result = objc.objc_msgSend(receiver, selector, *args)
        if restype == c_void_p:
            result = c_void_p(result)

    return result


class OBJC_SUPER(Structure):
    _fields_ = [('receiver', c_void_p), ('class', c_void_p)]


OBJC_SUPER_PTR = POINTER(OBJC_SUPER)


# 031013.python.runtime.line762.comment http://stackoverflow.com/questions/3095360/what-exactly-is-super-in-objective-c
# 031014.python.runtime.line763.comment
# 031015.python.runtime.line764.comment `superclass_name` is optional and can be used to force finding the superclass
# 031016.python.runtime.line765.comment by name. It is used to circumvent a bug in which the superclass was resolved
# 031017.python.runtime.line766.comment incorrectly which lead to an infinite recursion:
# 031018.python.runtime.line767.comment https://github.com/pyglet/pyglet/issues/5
def send_super(receiver, selName, *args, superclass_name=None, **kwargs):
    if hasattr(receiver, '_as_parameter_'):
        receiver = receiver._as_parameter_
    if superclass_name is None:
        superclass = get_superclass_of_object(receiver)
    else:
        superclass = get_class(superclass_name)
    super_struct = OBJC_SUPER(receiver, superclass)
    selector = get_selector(selName)
    restype = kwargs.get('restype', c_void_p)
    argtypes = kwargs.get('argtypes', None)
    objc.objc_msgSendSuper.restype = restype
    if argtypes:
        objc.objc_msgSendSuper.argtypes = [OBJC_SUPER_PTR, c_void_p] + argtypes
    else:
        objc.objc_msgSendSuper.argtypes = None
    result = objc.objc_msgSendSuper(byref(super_struct), selector, *args)
    if restype == c_void_p:
        result = c_void_p(result)
    return result


# 031019.python.runtime.line790.comment #####################################################################

cfunctype_table = {}


def parse_type_encoding(encoding):
    """Takes a type encoding string and outputs a list of the separated type codes.
    Currently does not handle unions or bitfields and strips out any field width
    specifiers or type specifiers from the encoding.  For Python 3.2+, encoding is
    assumed to be a bytes object and not unicode.

    Examples:
    parse_type_encoding('^v16@0:8') --> ['^v', '@', ':']
    parse_type_encoding('{CGSize=dd}40@0:8{CGSize=dd}16Q32') --> ['{CGSize=dd}', '@', ':', '{CGSize=dd}', 'Q']
    """
    type_encodings = []
    brace_count = 0  # number of unclosed curly braces
    bracket_count = 0  # number of unclosed square brackets
    typecode = b''
    for c in encoding:
        # 031022.python.runtime.line810.comment In Python 3, c comes out as an integer in the range 0-255.  In Python 2, c is a single character string.
        # 031023.python.runtime.line811.comment To fix the disparity, we convert c to a bytes object if necessary.
        if isinstance(c, int):
            c = bytes([c])

        if c == b'{':
            # 031024.python.runtime.line816.comment Check if this marked the end of previous type code.
            if typecode and typecode[-1:] != b'^' and brace_count == 0 and bracket_count == 0:
                type_encodings.append(typecode)
                typecode = b''
            typecode += c
            brace_count += 1
        elif c == b'}':
            typecode += c
            brace_count -= 1
            assert (brace_count >= 0)
        elif c == b'[':
            # 031025.python.runtime.line827.comment Check if this marked the end of previous type code.
            if typecode and typecode[-1:] != b'^' and brace_count == 0 and bracket_count == 0:
                type_encodings.append(typecode)
                typecode = b''
            typecode += c
            bracket_count += 1
        elif c == b']':
            typecode += c
            bracket_count -= 1
            assert (bracket_count >= 0)
        elif brace_count or bracket_count:
            # 031026.python.runtime.line838.comment Anything encountered while inside braces or brackets gets stuck on.
            typecode += c
        elif c in b'0123456789':
            # 031027.python.runtime.line841.comment Ignore field width specifiers for now.
            pass
        elif c in b'rnNoORV':
            # 031028.python.runtime.line844.comment Also ignore type specifiers.
            pass
        elif c in b'^cislqCISLQfdBv*@#:b?':
            if typecode and typecode[-1:] == b'^':
                # 031029.python.runtime.line848.comment Previous char was pointer specifier, so keep going.
                typecode += c
            else:
                # 031030.python.runtime.line851.comment Add previous type code to the list.
                if typecode:
                    type_encodings.append(typecode)
                # 031031.python.runtime.line854.comment Start a new type code.
                typecode = c

    # 031032.python.runtime.line857.comment Add the last type code to the list
    if typecode:
        type_encodings.append(typecode)

    return type_encodings


# 031033.python.runtime.line864.comment Limited to basic types and pointers to basic types.
# 031034.python.runtime.line865.comment Does not try to handle arrays, arbitrary structs, unions, or bitfields.
# 031035.python.runtime.line866.comment Assume that encoding is a bytes object and not unicode.
def cfunctype_for_encoding(encoding):
    # 031036.python.runtime.line868.comment Check if we've already created a CFUNCTYPE for this encoding.
    # 031037.python.runtime.line869.comment If so, then return the cached CFUNCTYPE.
    if encoding in cfunctype_table:
        return cfunctype_table[encoding]

    # 031038.python.runtime.line873.comment Otherwise, create a new CFUNCTYPE for the encoding.
    typecodes = {b'c': c_char, b'i': c_int, b's': c_short, b'l': c_long, b'q': c_longlong,
                 b'C': c_ubyte, b'I': c_uint, b'S': c_ushort, b'L': c_ulong, b'Q': c_ulonglong,
                 b'f': c_float, b'd': c_double, b'B': c_bool, b'v': None, b'*': c_char_p,
                 b'@': c_void_p, b'#': c_void_p, b':': c_void_p, NSPointEncoding: NSPoint,
                 NSSizeEncoding: NSSize, NSRectEncoding: NSRect, NSRangeEncoding: NSRange,
                 PyObjectEncoding: py_object}
    argtypes = []
    for code in parse_type_encoding(encoding):
        if code in typecodes:
            argtypes.append(typecodes[code])
        elif code[0:1] == b'^' and code[1:] in typecodes:
            argtypes.append(POINTER(typecodes[code[1:]]))
        else:
            raise Exception('unknown type encoding: ' + code)

    cfunctype = CFUNCTYPE(*argtypes)

    # 031039.python.runtime.line891.comment Cache the new CFUNCTYPE in the cfunctype_table.
    # 031040.python.runtime.line892.comment We do this mainly because it prevents the CFUNCTYPE
    # 031041.python.runtime.line893.comment from being garbage-collected while we need it.
    cfunctype_table[encoding] = cfunctype
    return cfunctype


# 031042.python.runtime.line898.comment #####################################################################

# 031043.python.runtime.line900.comment After calling create_subclass, you must first register
# 031044.python.runtime.line901.comment it with register_subclass before you may use it.
# 031045.python.runtime.line902.comment You can add new methods after the class is registered,
# 031046.python.runtime.line903.comment but you cannot add any new ivars.
def create_subclass(superclass, name):
    if isinstance(superclass, str):
        superclass = get_class(superclass)
    return c_void_p(objc.objc_allocateClassPair(superclass, ensure_bytes(name), 0))


def register_subclass(subclass):
    objc.objc_registerClassPair(subclass)


# 031047.python.runtime.line914.comment types is a string encoding the argument types of the method.
# 031048.python.runtime.line915.comment The first type code of types is the return type (e.g. 'v' if void)
# 031049.python.runtime.line916.comment The second type code must be '@' for id self.
# 031050.python.runtime.line917.comment The third type code must be ':' for SEL cmd.
# 031051.python.runtime.line918.comment Additional type codes are for types of other arguments if any.
def add_method(cls, selName, method, types):
    type_encodings = parse_type_encoding(types)
    assert (type_encodings[1] == b'@')  # ensure id self typecode
    assert (type_encodings[2] == b':')  # ensure SEL cmd typecode
    selector = get_selector(selName)
    cfunctype = cfunctype_for_encoding(types)
    imp = cfunctype(method)
    objc.class_addMethod.argtypes = [c_void_p, c_void_p, cfunctype, c_char_p]
    objc.class_addMethod(cls, selector, imp, types)
    return imp


def add_ivar(cls, name, vartype):
    return objc.class_addIvar(cls, ensure_bytes(name), sizeof(vartype), alignment(vartype), encoding_for_ctype(vartype))


def set_instance_variable(obj, varname, value, vartype):
    objc.object_setInstanceVariable.argtypes = [c_void_p, c_char_p, vartype]
    objc.object_setInstanceVariable(obj, ensure_bytes(varname), value)


def get_instance_variable(obj, varname, vartype):
    variable = vartype()
    objc.object_getInstanceVariable(obj, ensure_bytes(varname), byref(variable))
    return variable.value


# 031054.python.runtime.line946.comment #####################################################################

class ObjCMethod:
    """This represents an unbound Objective-C method (really an IMP)."""

    # 031055.python.runtime.line951.comment Note, need to map 'c' to c_byte rather than c_char, because otherwise
    # 031056.python.runtime.line952.comment ctypes converts the value into a one-character string which is generally
    # 031057.python.runtime.line953.comment not what we want at all, especially when the 'c' represents a bool var.
    typecodes = {b'c': c_byte, b'i': c_int, b's': c_short, b'l': c_long, b'q': c_longlong,
                 b'C': c_ubyte, b'I': c_uint, b'S': c_ushort, b'L': c_ulong, b'Q': c_ulonglong,
                 b'f': c_float, b'd': c_double, b'B': c_bool, b'v': None, b'Vv': None, b'*': c_char_p,
                 b'@': c_void_p, b'#': c_void_p, b':': c_void_p, b'^v': c_void_p, b'?': c_void_p,
                 NSPointEncoding: NSPoint, NSSizeEncoding: NSSize, NSRectEncoding: NSRect,
                 NSRangeEncoding: NSRange,
                 PyObjectEncoding: py_object}

    cfunctype_table = {}

    def __init__(self, method):
        """Initialize with an Objective-C Method pointer.  We then determine
        the return type and argument type information of the method."""
        self.selector = c_void_p(objc.method_getName(method))
        self.name = objc.sel_getName(self.selector)
        self.pyname = self.name.replace(b':', b'_')
        self.encoding = objc.method_getTypeEncoding(method)

        return_type_ptr = objc.method_copyReturnType(method)
        self.return_type = cast(return_type_ptr, c_char_p).value

        self.nargs = objc.method_getNumberOfArguments(method)
        self.imp = c_void_p(objc.method_getImplementation(method))
        self.argument_types = []
        for i in range(self.nargs):
            buffer = c_buffer(512)
            objc.method_getArgumentType(method, i, buffer, len(buffer))
            self.argument_types.append(buffer.value)

        # 031058.python.runtime.line983.comment Get types for all the arguments.
        try:
            self.argtypes = [self.ctype_for_encoding(t) for t in self.argument_types]
        except:
            # 031059.python.runtime.line987.comment print(f'no argtypes encoding for {self.name} ({self.argument_types})')
            self.argtypes = None
        # 031060.python.runtime.line989.comment Get types for the return type.

        try:
            if self.return_type == b'@':
                self.restype = ObjCInstance
            elif self.return_type == b'#':
                self.restype = ObjCClass
            else:
                self.restype = self.ctype_for_encoding(self.return_type)
        except:
            # 031061.python.runtime.line999.comment print(f'no restype encoding for {self.name} ({self.return_type})')
            self.restype = None

        self.func = None

        libc.free(return_type_ptr)


    def ctype_for_encoding(self, encoding):
        """Return ctypes type for an encoded Objective-C type."""
        if encoding in self.typecodes:
            return self.typecodes[encoding]
        elif encoding[0:1] == b'^' and encoding[1:] in self.typecodes:
            return POINTER(self.typecodes[encoding[1:]])
        elif encoding[0:1] == b'^' and encoding[1:] in [CGImageEncoding, NSZoneEncoding]:
            # 031062.python.runtime.line1014.comment special cases
            return c_void_p
        elif encoding[0:1] == b'r' and encoding[1:] in self.typecodes:
            # 031063.python.runtime.line1017.comment const decorator, don't care
            return self.typecodes[encoding[1:]]
        elif encoding[0:2] == b'r^' and encoding[2:] in self.typecodes:
            # 031064.python.runtime.line1020.comment const pointer, also don't care
            return POINTER(self.typecodes[encoding[2:]])
        else:
            raise Exception('unknown encoding for %s: %s' % (self.name, encoding))

    def get_prototype(self):
        """Returns a ctypes CFUNCTYPE for the method."""
        if self.restype == ObjCInstance or self.restype == ObjCClass:
            # 031065.python.runtime.line1028.comment Some hacky stuff to get around ctypes issues on 64-bit.  Can't let
            # 031066.python.runtime.line1029.comment ctypes convert the return value itself, because it truncates the pointer
            # 031067.python.runtime.line1030.comment along the way.  So instead, we must do set the return type to c_void_p to
            # 031068.python.runtime.line1031.comment ensure we get 64-bit addresses and then convert the return value manually.
            self.prototype = CFUNCTYPE(c_void_p, *self.argtypes)
        else:
            self.prototype = CFUNCTYPE(self.restype, *self.argtypes)
        return self.prototype

    def __repr__(self):
        return "<ObjCMethod: %s %s>" % (self.name, self.encoding)

    def get_callable(self):
        """Returns a python-callable version of the method's IMP."""
        if not self.func:
            prototype = self.get_prototype()
            self.func = cast(self.imp, prototype)
            if self.restype == ObjCInstance or self.restype == ObjCClass:
                self.func.restype = c_void_p
            else:
                self.func.restype = self.restype
            self.func.argtypes = self.argtypes
        return self.func

    def __call__(self, objc_id, *args):
        """Call the method with the given id and arguments.  You do not need
        to pass in the selector as an argument since it will be automatically
        provided."""
        f = self.get_callable()
        try:
            result = f(objc_id, self.selector, *args)

            # 031069.python.runtime.line1060.comment Convert result to python type if it is an instance or class pointer.
            if self.restype == ObjCInstance:
                result = ObjCInstance(result)
                # 031070.python.runtime.line1063.comment Only retain instances that have been allocated.
                if self.name.startswith((b'alloc', b'new', b'copy', b'mutableCopy')):
                    assert result._retained is False
                    result._retained = True
            elif self.restype == ObjCClass:
                result = ObjCClass(result)
            return result
        except ArgumentError as error:
            # 031071.python.runtime.line1071.comment Add more useful info to argument error exceptions, then reraise.
            error.args += ('selector = ' + str(self.name),
                           'argtypes =' + str(self.argtypes),
                           'encoding = ' + str(self.encoding))
            raise


# 031072.python.runtime.line1078.comment #####################################################################

class ObjCBoundMethod:
    """This represents an Objective-C method (an IMP) which has been bound
    to some id which will be passed as the first parameter to the method."""

    def __init__(self, method, objc_id):
        """Initialize with a method and ObjCInstance or ObjCClass object."""
        self.method = method
        self.objc_id = objc_id

    def __repr__(self):
        return '<ObjCBoundMethod %s (%s)>' % (self.method.name, self.objc_id)

    def __call__(self, *args):
        """Call the method with the given arguments."""
        return self.method(self.objc_id, *args)


# 031073.python.runtime.line1097.comment #####################################################################

class ObjCClass:
    """Python wrapper for an Objective-C class."""

    # 031074.python.runtime.line1102.comment We only create one Python object for each Objective-C class.
    # 031075.python.runtime.line1103.comment Any future calls with the same class will return the previously
    # 031076.python.runtime.line1104.comment created Python object.  Note that these aren't weak references.
    # 031077.python.runtime.line1105.comment After you create an ObjCClass, it will exist until the end of the
    # 031078.python.runtime.line1106.comment program.
    _registered_classes = {}

    def __new__(cls, class_name_or_ptr):
        """Create a new ObjCClass instance or return a previously created
        instance for the given Objective-C class.  The argument may be either
        the name of the class to retrieve, or a pointer to the class."""
        # 031079.python.runtime.line1113.comment Determine name and ptr values from passed in argument.
        if isinstance(class_name_or_ptr, str):
            name = class_name_or_ptr
            ptr = get_class(name)
        else:
            ptr = class_name_or_ptr
            # 031080.python.runtime.line1119.comment Make sure that ptr value is wrapped in c_void_p object
            # 031081.python.runtime.line1120.comment for safety when passing as ctypes argument.
            if not isinstance(ptr, c_void_p):
                ptr = c_void_p(ptr)
            name = objc.class_getName(ptr)

        # 031082.python.runtime.line1125.comment Check if we've already created a Python object for this class
        # 031083.python.runtime.line1126.comment and if so, return it rather than making a new one.
        if name in cls._registered_classes:
            return cls._registered_classes[name]

        # 031084.python.runtime.line1130.comment Otherwise create a new Python object and then initialize it.
        objc_class = super(ObjCClass, cls).__new__(cls)
        objc_class.ptr = ptr
        objc_class.name = name
        objc_class.instance_methods = {}  # mapping of name -> instance method
        objc_class.class_methods = {}  # mapping of name -> class method
        objc_class._as_parameter_ = ptr  # for ctypes argument passing

        # 031088.python.runtime.line1138.comment Store the new class in dictionary of registered classes.
        cls._registered_classes[name] = objc_class

        # 031089.python.runtime.line1141.comment Not sure this is necessary...
        objc_class.cache_instance_methods()
        objc_class.cache_class_methods()

        return objc_class

    def __repr__(self):
        return "<ObjCClass: %s at %s>" % (self.name, str(self.ptr.value))

    def cache_instance_methods(self):
        """Create and store python representations of all instance methods
        implemented by this class (but does not find methods of superclass)."""
        count = c_uint()
        method_array = objc.class_copyMethodList(self.ptr, byref(count))

        for i in range(count.value):
            method = c_void_p(method_array[i])
            objc_method = ObjCMethod(method)
            self.instance_methods[objc_method.pyname] = objc_method

        libc.free(method_array)

    def cache_class_methods(self):
        """Create and store python representations of all class methods
        implemented by this class (but does not find methods of superclass)."""
        count = c_uint()
        method_array = objc.class_copyMethodList(objc.object_getClass(self.ptr), byref(count))
        for i in range(count.value):
            method = c_void_p(method_array[i])
            objc_method = ObjCMethod(method)
            self.class_methods[objc_method.pyname] = objc_method

        libc.free(method_array)

    def get_instance_method(self, name):
        """Returns a python representation of the named instance method,
        either by looking it up in the cached list of methods or by searching
        for and creating a new method object."""
        if name in self.instance_methods:
            return self.instance_methods[name]
        else:
            # 031090.python.runtime.line1182.comment If method name isn't in the cached list, it might be a method of
            # 031091.python.runtime.line1183.comment the superclass, so call class_getInstanceMethod to check.
            selector = get_selector(name.replace(b'_', b':'))
            method = c_void_p(objc.class_getInstanceMethod(self.ptr, selector))
            if method.value:
                objc_method = ObjCMethod(method)
                self.instance_methods[name] = objc_method
                return objc_method
        return None

    def get_class_method(self, name):
        """Returns a python representation of the named class method,
        either by looking it up in the cached list of methods or by searching
        for and creating a new method object."""
        if name in self.class_methods:
            return self.class_methods[name]
        else:
            # 031092.python.runtime.line1199.comment If method name isn't in the cached list, it might be a method of
            # 031093.python.runtime.line1200.comment the superclass, so call class_getInstanceMethod to check.
            selector = get_selector(name.replace(b'_', b':'))
            method = c_void_p(objc.class_getClassMethod(self.ptr, selector))
            if method.value:
                objc_method = ObjCMethod(method)
                self.class_methods[name] = objc_method
                return objc_method
        return None

    def __getattr__(self, name):
        """Returns a callable method object with the given name."""
        # 031094.python.runtime.line1211.comment If name refers to a class method, then return a callable object
        # 031095.python.runtime.line1212.comment for the class method with self.ptr as hidden first parameter.
        name = ensure_bytes(name)
        method = self.get_class_method(name)
        if method:
            return ObjCBoundMethod(method, self.ptr)
        # 031096.python.runtime.line1217.comment If name refers to an instance method, then simply return the method.
        # 031097.python.runtime.line1218.comment The caller will need to supply an instance as the first parameter.
        method = self.get_instance_method(name)
        if method:
            return method

        # 031098.python.runtime.line1223.comment Otherwise, raise an exception.
        raise AttributeError('ObjCClass %s has no attribute %s' % (self.name, name))


# 031099.python.runtime.line1227.comment #####################################################################


class _AutoreleasepoolManager:
    def __init__(self):
        self.current = 0  # Current Pool ID. 0 is Global and not removed.
        self.pools = [None]  # List of NSAutoreleasePools.

    @property
    def count(self):
        """Number of total pools. Not including global."""
        return len(self.pools) - 1

    def create(self, pool):
        self.pools.append(pool)
        self.current = self.pools.index(pool)

    def delete(self, pool):
        self.pools.remove(pool)
        self.current = len(self.pools) - 1


_arp_manager = _AutoreleasepoolManager()

class ObjCInstance:
    """Python wrapper for an Objective-C instance."""
    pool = 0  # What pool id this belongs in.
    _retained = False  # If instance is kept even if pool is wiped.

    _cached_objects = weakref.WeakValueDictionary()

    def __new__(cls, object_ptr: int):
        """Create a new ObjCInstance or return a previously created one
        for the given object_ptr which should be an Objective-C id."""
        # 031104.python.runtime.line1261.comment Make sure that object_ptr is wrapped in a c_void_p.
        if not isinstance(object_ptr, c_void_p):
            object_ptr = c_void_p(object_ptr)

        # 031105.python.runtime.line1265.comment If given a nil pointer, return None.
        if not object_ptr.value:
            return None

        # 031106.python.runtime.line1269.comment Check if we've already created an python ObjCInstance for this
        # 031107.python.runtime.line1270.comment object_ptr id and if so, then return it.  A single ObjCInstance will
        # 031108.python.runtime.line1271.comment be created for any object pointer when it is first encountered.
        # 031109.python.runtime.line1272.comment This same ObjCInstance will then persist until the object is
        # 031110.python.runtime.line1273.comment deallocated.
        if object_ptr.value in cls._cached_objects:
            return cls._cached_objects[object_ptr.value]

        # 031111.python.runtime.line1277.comment Otherwise, create a new ObjCInstance.
        objc_instance = super(ObjCInstance, cls).__new__(cls)
        objc_instance.ptr = object_ptr
        objc_instance._as_parameter_ = object_ptr
        # 031112.python.runtime.line1281.comment Determine class of this object.
        class_ptr = c_void_p(objc.object_getClass(object_ptr))
        objc_instance.objc_class = ObjCClass(class_ptr)

        # 031113.python.runtime.line1285.comment Store new object in the dictionary of cached objects, keyed
        # 031114.python.runtime.line1286.comment by the (integer) memory address pointed to by the object_ptr.
        cls._cached_objects[object_ptr.value] = objc_instance
        return objc_instance

    def release(self):
        self._retained = False
        send_message(self, "release")

    def autorelease(self) -> ObjCInstance:
        """Release when object when the current pool is popped.

        Normally doesn't need to be called because the AutoReleasePool manager will do it automatically, which saves
        a lot of boilerplate.

        However, can be useful for debugging purposes.
        """
        self._retained = False
        ptr = send_message(self, "autorelease")
        return ObjCInstance(ptr)

    def __del__(self):
        """Instance was deleted either manually or through garbage collection.

        If we are retaining an allocation, release it.
        """
        if self._retained:
            send_message(self, "release")

    def associate(self, name: str, obj: Any):
        """Associate a Python object to the Objective-C instance with the given name.

        By associating python data with the instance, we end up keeping the instance from GCing on Pythons side until
        all associates are removed.
        """
        _set_dealloc_observer(self, name, obj)

    def __repr__(self):
        if self.objc_class.name == b'NSCFString':
            # 031115.python.runtime.line1324.comment Display contents of NSString objects
            from .cocoalibs import cfstring_to_string
            string = cfstring_to_string(self)
            return "<ObjCInstance %#x: %s (%s) at %s>" % (id(self), self.objc_class.name, string, str(self.ptr.value))

        return "<ObjCInstance %#x: %s at %s>" % (id(self), self.objc_class.name, str(self.ptr.value))

    def __getattr__(self, name):
        """Returns a callable method object with the given name.

        This is only called when the name doesn't exist in __dict__.
        """
        # 031116.python.runtime.line1336.comment Search for named instance method in the class object and if it
        # 031117.python.runtime.line1337.comment exists, return callable object with self as hidden argument.
        # 031118.python.runtime.line1338.comment Note: you should give self and not self.ptr as a parameter to
        # 031119.python.runtime.line1339.comment ObjCBoundMethod, so that it will be able to keep the ObjCInstance
        # 031120.python.runtime.line1340.comment alive for chained calls like MyClass.alloc().init() where the
        # 031121.python.runtime.line1341.comment object created by alloc() is not assigned to a variable.
        name_bytes = ensure_bytes(name)
        method = self.objc_class.get_instance_method(name_bytes)
        if method:
            return ObjCBoundMethod(method, self)
        # 031122.python.runtime.line1346.comment Else, search for class method with given name in the class object.
        # 031123.python.runtime.line1347.comment If it exists, return callable object with a pointer to the class
        # 031124.python.runtime.line1348.comment as a hidden argument.
        method = self.objc_class.get_class_method(name_bytes)
        if method:
            return ObjCBoundMethod(method, self.objc_class.ptr)
        # 031125.python.runtime.line1352.comment Otherwise raise an exception.

        internal_name = _assigned_internal_name(name)
        observer = objc.objc_getAssociatedObject(self, internal_name)

        if observer is None:
            msg = f'ObjCInstance {self.objc_class.name} ({self.ptr.value}) has no attribute {name}'
            raise AttributeError(msg)

        address = get_instance_variable(observer, "observed_object", c_void_p)
        py_ptr = cast(address, py_object)
        return py_ptr.value


def get_cached_instances():
    """For debug purposes, return a list of instance names.
    Useful for debugging if an object is leaking."""
    return [(obj.objc_class.name, obj._retained, obj.pool, obj) for obj in ObjCInstance._cached_objects.values()]


def convert_method_arguments(encoding, args):
    """Used by ObjCSubclass to convert Objective-C method arguments to
    Python values before passing them on to the Python-defined method."""
    new_args = []
    arg_encodings = parse_type_encoding(encoding)[3:]
    for e, a in zip(arg_encodings, args):
        if e == b'@':
            new_args.append(ObjCInstance(a))
        elif e == b'#':
            new_args.append(ObjCClass(a))
        else:
            new_args.append(a)
    return new_args


# 031126.python.runtime.line1387.comment ObjCSubclass is used to define an Objective-C subclass of an existing
# 031127.python.runtime.line1388.comment class registered with the runtime.  When you create an instance of
# 031128.python.runtime.line1389.comment ObjCSubclass, it registers the new subclass with the Objective-C
# 031129.python.runtime.line1390.comment runtime and creates a set of function decorators that you can use to
# 031130.python.runtime.line1391.comment add instance methods or class methods to the subclass.
# 031131.python.runtime.line1392.comment
# 031132.python.runtime.line1393.comment Typical usage would be to first create and register the subclass:
# 031133.python.runtime.line1394.comment
# 031134.python.runtime.line1395.comment MySubclass = ObjCSubclass('NSObject', 'MySubclassName')
# 031135.python.runtime.line1396.comment
# 031136.python.runtime.line1397.comment then add methods with:
# 031137.python.runtime.line1398.comment
# 031138.python.runtime.line1399.comment @MySubclass.method('v')
# 031139.python.runtime.line1400.comment def methodThatReturnsVoid(self):
# 031140.python.runtime.line1401.comment pass
# 031141.python.runtime.line1402.comment
# 031142.python.runtime.line1403.comment @MySubclass.method('Bi')
# 031143.python.runtime.line1404.comment def boolReturningMethodWithInt_(self, x):
# 031144.python.runtime.line1405.comment return True
# 031145.python.runtime.line1406.comment
# 031146.python.runtime.line1407.comment @MySubclass.classmethod('@')
# 031147.python.runtime.line1408.comment def classMethodThatReturnsId(self):
# 031148.python.runtime.line1409.comment return self
# 031149.python.runtime.line1410.comment
# 031150.python.runtime.line1411.comment It is probably a good idea to organize the code related to a single
# 031151.python.runtime.line1412.comment subclass by either putting it in its own module (note that you don't
# 031152.python.runtime.line1413.comment actually need to expose any of the method names or the ObjCSubclass)
# 031153.python.runtime.line1414.comment or by bundling it all up inside a python class definition, perhaps
# 031154.python.runtime.line1415.comment called MySubclassImplementation.
# 031155.python.runtime.line1416.comment
# 031156.python.runtime.line1417.comment It is also possible to add Objective-C ivars to the subclass, however
# 031157.python.runtime.line1418.comment if you do so, you must call the __init__ method with register=False,
# 031158.python.runtime.line1419.comment and then call the register method after the ivars have been added.
# 031159.python.runtime.line1420.comment But rather than creating the ivars in Objective-C land, it is easier
# 031160.python.runtime.line1421.comment to just define python-based instance variables in your subclass's init
# 031161.python.runtime.line1422.comment method.
# 031162.python.runtime.line1423.comment
# 031163.python.runtime.line1424.comment This class is used only to *define* the interface and implementation
# 031164.python.runtime.line1425.comment of an Objective-C subclass from python.  It should not be used in
# 031165.python.runtime.line1426.comment any other way.  If you want a python representation of the resulting
# 031166.python.runtime.line1427.comment class, create it with ObjCClass.
# 031167.python.runtime.line1428.comment
# 031168.python.runtime.line1429.comment Instances are created as a pointer to the objc object by using:
# 031169.python.runtime.line1430.comment
# 031170.python.runtime.line1431.comment myinstance = send_message('MySubclassName', 'alloc')
# 031171.python.runtime.line1432.comment myinstance = send_message(myinstance, 'init')
# 031172.python.runtime.line1433.comment
# 031173.python.runtime.line1434.comment or wrapped inside an ObjCInstance object by using:
# 031174.python.runtime.line1435.comment
# 031175.python.runtime.line1436.comment myclass = ObjCClass('MySubclassName')
# 031176.python.runtime.line1437.comment myinstance = myclass.alloc().init()
# 031177.python.runtime.line1438.comment
class ObjCSubclass:
    """Use this to create a subclass of an existing Objective-C class.
    It consists primarily of function decorators which you use to add methods
    to the subclass."""

    def __init__(self, superclass, name, register=True):
        self._imp_table = {}
        self.name = name
        self.objc_cls = create_subclass(superclass, name)
        self._as_parameter_ = self.objc_cls
        if register:
            self.register()

    def register(self):
        """Register the new class with the Objective-C runtime."""
        objc.objc_registerClassPair(self.objc_cls)
        # 031178.python.runtime.line1455.comment We can get the metaclass only after the class is registered.
        self.objc_metaclass = get_metaclass(self.name)

    def add_ivar(self, varname, vartype):
        """Add instance variable named varname to the subclass.
        varname should be a string.
        vartype is a ctypes type.
        The class must be registered AFTER adding instance variables."""
        return add_ivar(self.objc_cls, varname, vartype)

    def add_method(self, method, name, encoding):
        imp = add_method(self.objc_cls, name, method, encoding)
        self._imp_table[name] = imp

    # 031179.python.runtime.line1469.comment http://iphonedevelopment.blogspot.com/2008/08/dynamically-adding-class-objects.html
    def add_class_method(self, method, name, encoding):
        imp = add_method(self.objc_metaclass, name, method, encoding)
        self._imp_table[name] = imp

    def rawmethod(self, encoding):
        """Decorator for instance methods without any fancy shenanigans.
        The function must have the signature f(self, cmd, *args)
        where both self and cmd are just pointers to objc objects."""
        # 031180.python.runtime.line1478.comment Add encodings for hidden self and cmd arguments.
        encoding = ensure_bytes(encoding)
        typecodes = parse_type_encoding(encoding)
        typecodes.insert(1, b'@:')
        encoding = b''.join(typecodes)

        def decorator(f):
            name = f.__name__.replace('_', ':')
            self.add_method(f, name, encoding)
            return f

        return decorator

    def method(self, encoding):
        """Function decorator for instance methods."""
        # 031181.python.runtime.line1493.comment Add encodings for hidden self and cmd arguments.
        encoding = ensure_bytes(encoding)
        typecodes = parse_type_encoding(encoding)
        typecodes.insert(1, b'@:')
        encoding = b''.join(typecodes)

        def decorator(f):
            def objc_method(objc_self, objc_cmd, *args):
                py_self = ObjCInstance(objc_self)
                args = convert_method_arguments(encoding, args)
                result = f(py_self, *args)
                if isinstance(result, ObjCClass):
                    result = result.ptr.value
                elif isinstance(result, ObjCInstance):
                    result = result.ptr.value
                return result

            name = f.__name__.replace('_', ':')
            self.add_method(objc_method, name, encoding)
            return objc_method

        return decorator

    def classmethod(self, encoding):
        """Function decorator for class methods."""
        # 031182.python.runtime.line1518.comment Add encodings for hidden self and cmd arguments.
        encoding = ensure_bytes(encoding)
        typecodes = parse_type_encoding(encoding)
        typecodes.insert(1, b'@:')
        encoding = b''.join(typecodes)

        def decorator(f):
            def objc_class_method(objc_cls, objc_cmd, *args):
                py_cls = ObjCClass(objc_cls)
                args = convert_method_arguments(encoding, args)
                result = f(py_cls, *args)
                if isinstance(result, ObjCClass):
                    result = result.ptr.value
                elif isinstance(result, ObjCInstance):
                    result = result.ptr.value
                return result

            name = f.__name__.replace('_', ':')
            self.add_class_method(objc_class_method, name, encoding)
            return objc_class_method

        return decorator


# 031183.python.runtime.line1542.comment #####################################################################

_dealloc_argtype = [c_void_p]  # Just to prevent list creation every call.

# 031185.python.runtime.line1546.comment Cache Python objects we want to keep when associating with an instance.
_python_objects = {}

# 031186.python.runtime.line1549.comment Instances of DeallocationObserver are associated with every
# 031187.python.runtime.line1550.comment Objective-C object that gets wrapped inside an ObjCInstance.
# 031188.python.runtime.line1551.comment Their sole purpose is to watch for when the Objective-C object
# 031189.python.runtime.line1552.comment is deallocated, and then remove the object from the dictionary
# 031190.python.runtime.line1553.comment of cached ObjCInstance objects kept by the ObjCInstance class.
# 031191.python.runtime.line1554.comment
# 031192.python.runtime.line1555.comment The methods of the class defined below are decorated with
# 031193.python.runtime.line1556.comment rawmethod() instead of method() because DeallocationObservers
# 031194.python.runtime.line1557.comment are created inside of ObjCInstance's __new__ method and we have
# 031195.python.runtime.line1558.comment to be careful to not create another ObjCInstance here (which
# 031196.python.runtime.line1559.comment happens when the usual method decorator turns the self argument
# 031197.python.runtime.line1560.comment into an ObjCInstance), or else get trapped in an infinite recursion.
class DeallocationObserver_Implementation:
    DeallocationObserver = ObjCSubclass('NSObject', 'DeallocationObserver', register=False)
    DeallocationObserver.add_ivar('observed_object', c_void_p)
    DeallocationObserver.register()

    @DeallocationObserver.rawmethod('@@')
    def initWithObjectId_(self, cmd, objc_ptr):
        self = send_super(self, 'init')
        if self is not None:
            py_obj = cast(objc_ptr, py_object)
            _python_objects[(self.value, objc_ptr)] = py_obj.value
            set_instance_variable(self, 'observed_object', objc_ptr, c_void_p)
        return self.value

    @DeallocationObserver.rawmethod('v')
    def dealloc(self, cmd):
        if objc_ptr := get_instance_variable(self, 'observed_object', c_void_p):
            del _python_objects[(self, objc_ptr)]

        send_super(self, "dealloc")

    @DeallocationObserver.rawmethod('v')
    def finalize(self, cmd):
        # 031198.python.runtime.line1584.comment Called instead of dealloc if using garbage collection.
        # 031199.python.runtime.line1585.comment (which would have to be explicitly started with
        # 031200.python.runtime.line1586.comment objc_startCollectorThread(), so probably not too much reason
        # 031201.python.runtime.line1587.comment to have this here, but I guess it can't hurt.)
        # 031202.python.runtime.line1588.comment _obj_observer_dealloc(self, 'finalize')
        if objc_ptr := get_instance_variable(self, 'observed_object', c_void_p):
            del _python_objects[(self, objc_ptr.value)]

        send_super(self, 'finalize')

def _obj_observer_dealloc(objc_obs, selector_name):
    """Removes any cached ObjCInstances in Python to prevent memory leaks.
    Manually break association as it's not implicitly mentioned that dealloc would break an association,
    although we do not use the object after.
    """
    objc_ptr = get_instance_variable(objc_obs, 'observed_object', c_void_p)
    if objc_ptr:
        objc.objc_setAssociatedObject(objc_ptr, objc_obs, None, OBJC_ASSOCIATION_ASSIGN)
        ObjCInstance._cached_objects.pop(objc_ptr, None)

    send_super(objc_obs, selector_name)

def _assigned_internal_name(name: str):
    key = f'_internal.assign.{name}'
    return get_selector(key)

def _set_dealloc_observer(self, name, python_obj):
    # 031203.python.runtime.line1611.comment Create a DeallocationObserver and associate it with this object.
    # 031204.python.runtime.line1612.comment When the Objective-C object is deallocated, the observer will remove
    # 031205.python.runtime.line1613.comment the ObjCInstance corresponding to the object from the cached objects
    # 031206.python.runtime.line1614.comment dictionary, effectively destroying the ObjCInstance.
    observer = send_message('DeallocationObserver', 'alloc')
    observer = send_message(observer, 'initWithObjectId:', id(python_obj), argtypes=_dealloc_argtype)

    objc.objc_setAssociatedObject(self, _assigned_internal_name(name), observer, OBJC_ASSOCIATION_RETAIN)

    # 031207.python.runtime.line1620.comment The observer is retained by the object we associate it to.  We release
    # 031208.python.runtime.line1621.comment the observer now so that it will be deallocated when the associated
    # 031209.python.runtime.line1622.comment object is deallocated.
    send_message(observer, 'release')
    return observer


def _remove_dealloc_observer(objc_ptr):
    observer = objc_ptr._observer
    objc.objc_setAssociatedObject(objc_ptr, observer, None, OBJC_ASSOCIATION_RETAIN)


@contextmanager
def AutoReleasePool():
    """Use objc_autoreleasePoolPush/Pop because NSAutoreleasePool is no longer recommended:
        https://developer.apple.com/documentation/foundation/nsautoreleasepool
    @autoreleasepool blocks are compiled into the below function calls behind the scenes.
    Call them directly to mimic the Objective-C behavior.
    """
    pool = objc.objc_autoreleasePoolPush()

    try:
        yield
    finally:
        objc.objc_autoreleasePoolPop(pool)
