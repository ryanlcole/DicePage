# 052370.python.test_win32cred.line1.comment
# 052371.python.test_win32cred.line2.comment (C) Copyright 2014 Enthought, Inc., Austin, TX
# 052372.python.test_win32cred.line3.comment All right reserved.
# 052373.python.test_win32cred.line4.comment
# 052374.python.test_win32cred.line5.comment This file is open source software distributed according to the terms in
# 052375.python.test_win32cred.line6.comment LICENSE.txt
# 052376.python.test_win32cred.line7.comment
import os
import sys
import unittest

import win32cred

from win32ctypes.core._winerrors import ERROR_NOT_FOUND
from win32ctypes.pywin32.pywintypes import error
from win32ctypes.pywin32.win32cred import (
    CredDelete, CredRead, CredWrite, CredEnumerate,
    CRED_PERSIST_ENTERPRISE, CRED_TYPE_GENERIC,
    CRED_ENUMERATE_ALL_CREDENTIALS)

# 052377.python.test_win32cred.line21.comment find the pywin32 version
version_file = os.path.join(
    os.path.dirname(
        os.path.dirname(win32cred.__file__)), 'pywin32.version.txt')
if os.path.exists(version_file):
    with open(version_file) as handle:
        pywin32_build = handle.read().strip()
else:
    pywin32_build = None


class TestCred(unittest.TestCase):

    def setUp(self):
        from pywintypes import error
        try:
            win32cred.CredDelete(u'jone@doe', CRED_TYPE_GENERIC)
        except error:
            pass

    def _demo_credentials(self, UserName=u'jone'):
        return {
            "Type": CRED_TYPE_GENERIC,
            "TargetName": u'jone@doe',
            "UserName": UserName,
            "CredentialBlob": u"doefsajfsakfj",
            "Comment": u"Created by MiniPyWin32Cred test suite",
            "Persist": CRED_PERSIST_ENTERPRISE}

    @unittest.skipIf(
        pywin32_build == "223" and sys.version_info[:2] == (3, 7),
        "pywin32 version 223 bug with CredRead (mhammond/pywin32#1232)")
    def test_write_to_pywin32(self):
        # 052378.python.test_win32cred.line54.comment given
        target = u'jone@doe'
        r_credentials = self._demo_credentials()
        CredWrite(r_credentials)

        # 052379.python.test_win32cred.line59.comment when
        credentials = win32cred.CredRead(
            TargetName=target, Type=CRED_TYPE_GENERIC)

        # 052380.python.test_win32cred.line63.comment then
        self.assertEqual(credentials["Type"], CRED_TYPE_GENERIC)
        self.assertEqual(credentials["UserName"], u"jone")
        self.assertEqual(credentials["TargetName"], u'jone@doe')
        self.assertEqual(
            credentials["Comment"], u"Created by MiniPyWin32Cred test suite")
        # 052381.python.test_win32cred.line69.comment XXX: the fact that we have to decode the password when reading, but
        # 052382.python.test_win32cred.line70.comment not encode when writing is a bit strange, but that's what pywin32
        # 052383.python.test_win32cred.line71.comment seems to do and we try to be backward compatible here.
        self.assertEqual(
            credentials["CredentialBlob"].decode('utf-16'), u"doefsajfsakfj")

    def test_read_from_pywin32(self):
        # 052384.python.test_win32cred.line76.comment given
        target = u'jone@doe'
        r_credentials = self._demo_credentials()
        win32cred.CredWrite(r_credentials)

        # 052385.python.test_win32cred.line81.comment when
        credentials = CredRead(target, CRED_TYPE_GENERIC)

        # 052386.python.test_win32cred.line84.comment then
        self.assertEqual(credentials["UserName"], u"jone")
        self.assertEqual(credentials["TargetName"], u'jone@doe')
        self.assertEqual(
            credentials["Comment"], u"Created by MiniPyWin32Cred test suite")
        self.assertEqual(
            credentials["CredentialBlob"].decode('utf-16'), u"doefsajfsakfj")

    def test_read_from_pywin32_with_none_usename(self):
        # 052387.python.test_win32cred.line93.comment given
        target = u'jone@doe'
        r_credentials = self._demo_credentials(None)
        win32cred.CredWrite(r_credentials)

        # 052388.python.test_win32cred.line98.comment when
        credentials = CredRead(target, CRED_TYPE_GENERIC)

        self.assertEqual(credentials["UserName"], None)
        self.assertEqual(credentials["TargetName"], u'jone@doe')
        self.assertEqual(
            credentials["Comment"], u"Created by MiniPyWin32Cred test suite")
        self.assertEqual(
            credentials["CredentialBlob"].decode('utf-16'), u"doefsajfsakfj")

    def test_write_to_pywin32_with_none_usename(self):
        # 052389.python.test_win32cred.line109.comment given
        target = u'jone@doe'
        r_credentials = self._demo_credentials(None)
        CredWrite(r_credentials)

        # 052390.python.test_win32cred.line114.comment when
        credentials = win32cred.CredRead(target, CRED_TYPE_GENERIC)

        self.assertEqual(credentials["UserName"], None)
        self.assertEqual(credentials["TargetName"], u'jone@doe')
        self.assertEqual(
            credentials["Comment"], u"Created by MiniPyWin32Cred test suite")
        self.assertEqual(
            credentials["CredentialBlob"].decode('utf-16'), u"doefsajfsakfj")

    def test_read_write(self):
        # 052391.python.test_win32cred.line125.comment given
        target = u'jone@doe'
        r_credentials = self._demo_credentials()

        # 052392.python.test_win32cred.line129.comment when
        CredWrite(r_credentials)
        credentials = CredRead(target, CRED_TYPE_GENERIC)

        self.assertEqual(credentials["UserName"], u"jone")
        self.assertEqual(credentials["TargetName"], u'jone@doe')
        self.assertEqual(
            credentials["Comment"], u"Created by MiniPyWin32Cred test suite")
        self.assertEqual(
            credentials["CredentialBlob"].decode('utf-16'), u"doefsajfsakfj")

    def test_read_write_with_none_username(self):
        # 052393.python.test_win32cred.line141.comment given
        target = u'jone@doe'
        r_credentials = self._demo_credentials(None)

        # 052394.python.test_win32cred.line145.comment when
        CredWrite(r_credentials)
        credentials = CredRead(target, CRED_TYPE_GENERIC)

        # 052395.python.test_win32cred.line149.comment then
        self.assertEqual(credentials["UserName"], None)
        self.assertEqual(credentials["TargetName"], u'jone@doe')
        self.assertEqual(
            credentials["Comment"], u"Created by MiniPyWin32Cred test suite")
        self.assertEqual(
            credentials["CredentialBlob"].decode('utf-16'), u"doefsajfsakfj")

    def test_enumerate_filter(self):
        # 052396.python.test_win32cred.line158.comment given
        r_credentials = self._demo_credentials()
        CredWrite(r_credentials)

        # 052397.python.test_win32cred.line162.comment when
        credentials = CredEnumerate('jone*')[0]

        # 052398.python.test_win32cred.line165.comment then
        self.assertEqual(credentials["UserName"], u"jone")
        self.assertEqual(credentials["TargetName"], u'jone@doe')
        self.assertEqual(
            credentials["Comment"], u"Created by MiniPyWin32Cred test suite")
        self.assertEqual(
            credentials["CredentialBlob"].decode('utf-16'), u"doefsajfsakfj")

    def test_enumerate_no_filter(self):
        # 052399.python.test_win32cred.line174.comment given
        r_credentials = self._demo_credentials()
        CredWrite(r_credentials)

        # 052400.python.test_win32cred.line178.comment when
        pywin32_result = win32cred.CredEnumerate()
        credentials = CredEnumerate()

        # 052401.python.test_win32cred.line182.comment then
        self.assertEqual(len(credentials), len(pywin32_result))

    def test_enumerate_all(self):
        # 052402.python.test_win32cred.line186.comment when
        credentials = CredEnumerate(Flags=CRED_ENUMERATE_ALL_CREDENTIALS)

        # 052403.python.test_win32cred.line189.comment then
        self.assertGreater(len(credentials), 1)

    def test_read_doesnt_exists(self):
        # 052404.python.test_win32cred.line193.comment given
        target = "Floupi_dont_exists@MiniPyWin"

        # 052405.python.test_win32cred.line196.comment when/then
        with self.assertRaises(error) as ctx:
            CredRead(target, CRED_TYPE_GENERIC)
        self.assertTrue(ctx.exception.winerror, ERROR_NOT_FOUND)

    def test_delete_simple(self):
        # 052406.python.test_win32cred.line202.comment given
        target = u'jone@doe'
        r_credentials = self._demo_credentials()
        CredWrite(r_credentials, 0)
        credentials = CredRead(target, CRED_TYPE_GENERIC)
        self.assertTrue(credentials is not None)

        # 052407.python.test_win32cred.line209.comment when
        CredDelete(target, CRED_TYPE_GENERIC)

        # 052408.python.test_win32cred.line212.comment then
        with self.assertRaises(error) as ctx:
            CredRead(target, CRED_TYPE_GENERIC)
        self.assertEqual(ctx.exception.winerror, ERROR_NOT_FOUND)
        self.assertEqual(ctx.exception.funcname, "CredRead")

    def test_delete_doesnt_exists(self):
        # 052409.python.test_win32cred.line219.comment given
        target = u"Floupi_doesnt_exists@MiniPyWin32"

        # 052410.python.test_win32cred.line222.comment when/then
        with self.assertRaises(error) as ctx:
            CredDelete(target, CRED_TYPE_GENERIC)
        self.assertEqual(ctx.exception.winerror, ERROR_NOT_FOUND)
        self.assertEqual(ctx.exception.funcname, "CredDelete")


if __name__ == '__main__':
    unittest.main()
