"""runproc.py

start a process with three inherited pipes.
Try to write to and read from those.
"""

import msvcrt
import os

import win32api
import win32con
import win32file
import win32pipe
import win32process
import win32security


class Process:
    def run(self, cmdline):
        # 046077.python.runproc.line20.comment security attributes for pipes
        sAttrs = win32security.SECURITY_ATTRIBUTES()
        sAttrs.bInheritHandle = 1

        # 046078.python.runproc.line24.comment create pipes
        hStdin_r, self.hStdin_w = win32pipe.CreatePipe(sAttrs, 0)
        self.hStdout_r, hStdout_w = win32pipe.CreatePipe(sAttrs, 0)
        self.hStderr_r, hStderr_w = win32pipe.CreatePipe(sAttrs, 0)

        # 046079.python.runproc.line29.comment set the info structure for the new process.
        StartupInfo = win32process.STARTUPINFO()
        StartupInfo.hStdInput = hStdin_r
        StartupInfo.hStdOutput = hStdout_w
        StartupInfo.hStdError = hStderr_w
        StartupInfo.dwFlags = win32process.STARTF_USESTDHANDLES
        # 046080.python.runproc.line35.comment Mark doesn't support wShowWindow yet.
        # 046081.python.runproc.line36.comment StartupInfo.dwFlags = StartupInfo.dwFlags | win32process.STARTF_USESHOWWINDOW
        # 046082.python.runproc.line37.comment StartupInfo.wShowWindow = win32con.SW_HIDE

        # 046083.python.runproc.line39.comment Create new output read handles and the input write handle. Set
        # 046084.python.runproc.line40.comment the inheritance properties to FALSE. Otherwise, the child inherits
        # 046085.python.runproc.line41.comment the these handles; resulting in non-closeable handles to the pipes
        # 046086.python.runproc.line42.comment being created.
        pid = win32api.GetCurrentProcess()

        tmp = win32api.DuplicateHandle(
            pid,
            self.hStdin_w,
            pid,
            0,
            0,  # non-inheritable!!
            win32con.DUPLICATE_SAME_ACCESS,
        )
        # 046088.python.runproc.line53.comment Close the inhertible version of the handle
        win32file.CloseHandle(self.hStdin_w)
        self.hStdin_w = tmp
        tmp = win32api.DuplicateHandle(
            pid,
            self.hStdout_r,
            pid,
            0,
            0,  # non-inheritable!
            win32con.DUPLICATE_SAME_ACCESS,
        )
        # 046090.python.runproc.line64.comment Close the inhertible version of the handle
        win32file.CloseHandle(self.hStdout_r)
        self.hStdout_r = tmp

        # 046091.python.runproc.line68.comment start the process.
        hProcess, hThread, dwPid, dwTid = win32process.CreateProcess(
            None,  # program
            cmdline,  # command line
            None,  # process security attributes
            None,  # thread attributes
            1,  # inherit handles, or USESTDHANDLES won't work.
            # 046097.python.runproc.line75.comment creation flags. Don't access the console.
            0,  # Don't need anything here.
            # 046099.python.runproc.line77.comment If you're in a GUI app, you should use
            # 046100.python.runproc.line78.comment CREATE_NEW_CONSOLE here, or any subprocesses
            # 046101.python.runproc.line79.comment might fall victim to the problem described in:
            # 046102.python.runproc.line80.comment KB article: Q156755, cmd.exe requires
            # 046103.python.runproc.line81.comment an NT console in order to perform redirection..
            None,  # no new environment
            None,  # current directory (stay where we are)
            StartupInfo,
        )
        # 046106.python.runproc.line86.comment normally, we would save the pid etc. here...

        # 046107.python.runproc.line88.comment Child is launched. Close the parents copy of those pipe handles
        # 046108.python.runproc.line89.comment that only the child should have open.
        # 046109.python.runproc.line90.comment You need to make sure that no handles to the write end of the
        # 046110.python.runproc.line91.comment output pipe are maintained in this process or else the pipe will
        # 046111.python.runproc.line92.comment not close when the child process exits and the ReadFile will hang.
        win32file.CloseHandle(hStderr_w)
        win32file.CloseHandle(hStdout_w)
        win32file.CloseHandle(hStdin_r)

        self.stdin = os.fdopen(msvcrt.open_osfhandle(self.hStdin_w, 0), "wb")
        self.stdin.write("hmmmmm\r\n")
        self.stdin.flush()
        self.stdin.close()

        self.stdout = os.fdopen(msvcrt.open_osfhandle(self.hStdout_r, 0), "rb")
        print(f"Read on stdout: {self.stdout.read()!r}")

        self.stderr = os.fdopen(msvcrt.open_osfhandle(self.hStderr_r, 0), "rb")
        print(f"Read on stderr: {self.stderr.read()!r}")


if __name__ == "__main__":
    p = Process()
    exe = win32api.GetModuleFileName(0)
    p.run(exe + " cat.py")

# 046112.python.runproc.line114.comment end of runproc.py
