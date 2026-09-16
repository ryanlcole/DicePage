# 046904.python.pywin32_testutil.line1.comment Utilities for the pywin32 tests
import gc
import os
import site
import sys
import unittest

import winerror

# 046905.python.pywin32_testutil.line10.comment #
# 046906.python.pywin32_testutil.line11.comment # unittest related stuff
# 046907.python.pywin32_testutil.line12.comment #


# 046908.python.pywin32_testutil.line15.comment This is a specialized TestCase adaptor which wraps a real test.
class LeakTestCase(unittest.TestCase):
    """An 'adaptor' which takes another test.  In debug builds we execute the
    test once to remove one-off side-effects, then capture the total
    reference count, then execute the test a few times.  If the total
    refcount at the end is greater than we first captured, we have a leak!

    In release builds the test is executed just once, as normal.

    Generally used automatically by the test runner - you can safely
    ignore this.
    """

    def __init__(self, real_test):
        unittest.TestCase.__init__(self)
        self.real_test = real_test
        self.num_test_cases = 1
        self.num_leak_iters = 2  # seems to be enough!
        if hasattr(sys, "gettotalrefcount"):
            self.num_test_cases += self.num_leak_iters

    def countTestCases(self):
        return self.num_test_cases

    def __call__(self, result=None):
        # 046910.python.pywin32_testutil.line40.comment For the COM suite's sake, always ensure we don't leak
        # 046911.python.pywin32_testutil.line41.comment gateways/interfaces
        from pythoncom import _GetGatewayCount, _GetInterfaceCount

        gc.collect()
        ni = _GetInterfaceCount()
        ng = _GetGatewayCount()
        self.real_test(result)
        # 046912.python.pywin32_testutil.line48.comment Failed - no point checking anything else
        if result.shouldStop or not result.wasSuccessful():
            return
        self._do_leak_tests(result)
        gc.collect()
        lost_i = _GetInterfaceCount() - ni
        lost_g = _GetGatewayCount() - ng
        if lost_i or lost_g:
            msg = "%d interface objects and %d gateway objects leaked" % (
                lost_i,
                lost_g,
            )
            exc = AssertionError(msg)
            result.addFailure(self.real_test, (exc.__class__, exc, None))

    def runTest(self):
        raise NotImplementedError("not used")

    def _do_leak_tests(self, result=None):
        try:
            gtrc = sys.gettotalrefcount
        except AttributeError:
            return  # can't do leak tests in this build
        # 046914.python.pywin32_testutil.line71.comment Assume already called once, to prime any caches etc
        gc.collect()
        trc = gtrc()
        for i in range(self.num_leak_iters):
            self.real_test(result)
            if result.shouldStop:
                break
        del i  # created after we remembered the refcount!
        # 046916.python.pywin32_testutil.line79.comment int division here means one or 2 stray references won't force
        # 046917.python.pywin32_testutil.line80.comment failure, but one per loop
        gc.collect()
        lost = (gtrc() - trc) // self.num_leak_iters
        if lost < 0:
            msg = "LeakTest: %s appeared to gain %d references!!" % (
                self.real_test,
                -lost,
            )
            result.addFailure(self.real_test, (AssertionError, msg, None))
        if lost > 0:
            msg = "LeakTest: %s lost %d references" % (self.real_test, lost)
            exc = AssertionError(msg)
            result.addFailure(self.real_test, (exc.__class__, exc, None))


class TestLoader(unittest.TestLoader):
    def loadTestsFromTestCase(self, testCaseClass):
        """Return a suite of all tests cases contained in testCaseClass"""
        leak_tests = []
        for name in self.getTestCaseNames(testCaseClass):
            real_test = testCaseClass(name)
            leak_test = self._getTestWrapper(real_test)
            leak_tests.append(leak_test)
        return self.suiteClass(leak_tests)

    def fixupTestsForLeakTests(self, test):
        if isinstance(test, unittest.TestSuite):
            test._tests = [self.fixupTestsForLeakTests(t) for t in test._tests]
            return test
        else:
            # 046918.python.pywin32_testutil.line110.comment just a normal test case.
            return self._getTestWrapper(test)

    def _getTestWrapper(self, test):
        # 046919.python.pywin32_testutil.line114.comment one or 2 tests in the COM test suite set this...
        no_leak_tests = getattr(test, "no_leak_tests", False)
        if no_leak_tests:
            print("Test says it doesn't want leak tests!")
            return test
        return LeakTestCase(test)

    def loadTestsFromModule(self, mod):
        if hasattr(mod, "suite"):
            tests = mod.suite()
        else:
            tests = unittest.TestLoader.loadTestsFromModule(self, mod)
        return self.fixupTestsForLeakTests(tests)

    def loadTestsFromName(self, name, module=None):
        test = unittest.TestLoader.loadTestsFromName(self, name, module)
        if isinstance(test, unittest.TestSuite):
            # 046920.python.pywin32_testutil.line131.comment print("Don't wrap suites yet!", test._tests)
            pass  # hmmm?
        elif isinstance(test, unittest.TestCase):
            test = self._getTestWrapper(test)
        else:
            print("XXX - what is", test)
        return test


# 046922.python.pywin32_testutil.line140.comment Lots of classes necessary to support one simple feature: we want a 3rd
# 046923.python.pywin32_testutil.line141.comment test result state - "SKIPPED" - to indicate that the test wasn't able
# 046924.python.pywin32_testutil.line142.comment to be executed for various reasons.  Inspired by bzr's tests, but it
# 046925.python.pywin32_testutil.line143.comment has other concepts, such as "Expected Failure", which we don't bother
# 046926.python.pywin32_testutil.line144.comment with.

# 046927.python.pywin32_testutil.line146.comment win32 error codes that probably mean we need to be elevated (ie, if we
# 046928.python.pywin32_testutil.line147.comment aren't elevated, we treat these error codes as 'skipped')
non_admin_error_codes = [
    winerror.ERROR_ACCESS_DENIED,
    winerror.ERROR_PRIVILEGE_NOT_HELD,
]

_is_admin = None


def check_is_admin():
    global _is_admin
    if _is_admin is None:
        import pythoncom
        from win32com.shell.shell import IsUserAnAdmin

        try:
            _is_admin = IsUserAnAdmin()
        except pythoncom.com_error as exc:
            if exc.hresult != winerror.E_NOTIMPL:
                raise
            # 046929.python.pywin32_testutil.line167.comment not impl on this platform - must be old - assume is admin
            _is_admin = True
    return _is_admin


# 046930.python.pywin32_testutil.line172.comment Find a test "fixture" (eg, binary test file) expected to be very close to
# 046931.python.pywin32_testutil.line173.comment the test being run.
# 046932.python.pywin32_testutil.line174.comment If the tests are being run from the "installed" version, then these fixtures
# 046933.python.pywin32_testutil.line175.comment probably don't exist - the test is "skipped".
# 046934.python.pywin32_testutil.line176.comment But it's fatal if we think we might be running from a pywin32 source tree.
def find_test_fixture(basename, extra_dir="."):
    # 046935.python.pywin32_testutil.line178.comment look for the test file in various places
    candidates = [
        os.path.dirname(sys.argv[0]),
        extra_dir,
        ".",
    ]
    for candidate in candidates:
        fname = os.path.join(candidate, basename)
        if os.path.isfile(fname):
            return fname
    else:
        # 046936.python.pywin32_testutil.line189.comment Can't find it - see if this is expected or not.
        # 046937.python.pywin32_testutil.line190.comment This module is typically always in the installed dir, so use argv[0]
        this_file = os.path.normcase(os.path.abspath(sys.argv[0]))
        dirs_to_check = site.getsitepackages()[:]
        if site.USER_SITE:
            dirs_to_check.append(site.USER_SITE)

        for d in dirs_to_check:
            d = os.path.normcase(d)
            if os.path.commonprefix([this_file, d]) == d:
                # 046938.python.pywin32_testutil.line199.comment looks like we are in an installed Python, so skip the text.
                raise TestSkipped(f"Can't find test fixture '{fname}'")
        # 046939.python.pywin32_testutil.line201.comment Looks like we are running from source, so this is fatal.
        raise RuntimeError(f"Can't find test fixture '{fname}'")


# 046940.python.pywin32_testutil.line205.comment If this exception is raised by a test, the test is reported as a 'skip'
class TestSkipped(Exception):
    pass


# 046941.python.pywin32_testutil.line210.comment The 'TestResult' subclass that records the failures and has the special
# 046942.python.pywin32_testutil.line211.comment handling for the TestSkipped exception.
class TestResult(unittest.TextTestResult):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.skips = {}  # count of skips for each reason.

    def addError(self, test, err):
        """Called when an error has occurred. 'err' is a tuple of values as
        returned by sys.exc_info().
        """
        # 046944.python.pywin32_testutil.line221.comment translate a couple of 'well-known' exceptions into 'skipped'
        import pywintypes

        exc_val = err[1]
        # 046945.python.pywin32_testutil.line225.comment translate ERROR_ACCESS_DENIED for non-admin users to be skipped.
        # 046946.python.pywin32_testutil.line226.comment (access denied errors for an admin user aren't expected.)
        if (
            isinstance(exc_val, pywintypes.error)
            and exc_val.winerror in non_admin_error_codes
            and not check_is_admin()
        ):
            exc_val = TestSkipped(exc_val)
        # 046947.python.pywin32_testutil.line233.comment and COM errors due to objects not being registered (the com test
        # 046948.python.pywin32_testutil.line234.comment suite will attempt to catch this and handle it itself if the user
        # 046949.python.pywin32_testutil.line235.comment is admin)
        elif isinstance(exc_val, pywintypes.com_error) and exc_val.hresult in [
            winerror.CO_E_CLASSSTRING,
            winerror.REGDB_E_CLASSNOTREG,
            winerror.TYPE_E_LIBNOTREGISTERED,
        ]:
            exc_val = TestSkipped(exc_val)
        # 046950.python.pywin32_testutil.line242.comment NotImplemented generally means the platform doesn't support the
        # 046951.python.pywin32_testutil.line243.comment functionality.
        elif isinstance(exc_val, NotImplementedError):
            exc_val = TestSkipped(NotImplementedError)

        if isinstance(exc_val, TestSkipped):
            reason = exc_val.args[0]
            # 046952.python.pywin32_testutil.line249.comment if the reason itself is another exception, get its args.
            try:
                reason = tuple(reason.args)
            except (AttributeError, TypeError):
                pass
            self.skips.setdefault(reason, 0)
            self.skips[reason] += 1
            if self.showAll:
                self.stream.writeln(f"SKIP ({reason})")
            elif self.dots:
                self.stream.write("S")
                self.stream.flush()
            return
        super().addError(test, err)

    def printErrors(self):
        super().printErrors()
        for reason, num_skipped in self.skips.items():
            self.stream.writeln("SKIPPED: %d tests - %s" % (num_skipped, reason))


# 046953.python.pywin32_testutil.line270.comment TestRunner subclass necessary just to get our TestResult hooked up.
class TestRunner(unittest.TextTestRunner):
    def _makeResult(self):
        return TestResult(self.stream, self.descriptions, self.verbosity)


# 046954.python.pywin32_testutil.line276.comment TestProgram subclass necessary just to get our TestRunner hooked up,
# 046955.python.pywin32_testutil.line277.comment which is necessary to get our TestResult hooked up *sob*
class TestProgram(unittest.TestProgram):
    def runTests(self):
        # 046956.python.pywin32_testutil.line280.comment clobber existing runner - *sob* - it shouldn't be this hard
        self.testRunner = TestRunner(verbosity=self.verbosity)
        unittest.TestProgram.runTests(self)


# 046957.python.pywin32_testutil.line285.comment A convenient entry-point - if used, 'SKIPPED' exceptions will be suppressed.
def testmain(*args, **kw):
    new_kw = kw.copy()
    if "testLoader" not in new_kw:
        new_kw["testLoader"] = TestLoader()
    program_class = new_kw.get("testProgram", TestProgram)
    program_class(*args, **new_kw)
