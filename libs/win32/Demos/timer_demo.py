# 046349.python.timer_demo.line1.comment -*- Mode: Python; tab-width: 4 -*-
# 046350.python.timer_demo.line2.comment

# 046351.python.timer_demo.line4.comment This module, and the timer.pyd core timer support, were written by
# 046352.python.timer_demo.line5.comment Sam Rushing (rushing@nightmare.com)

import time

# 046353.python.timer_demo.line9.comment Timers are based on Windows messages.  So we need
# 046354.python.timer_demo.line10.comment to do the event-loop thing!
import timer
import win32event
import win32gui

# 046355.python.timer_demo.line15.comment glork holds a simple counter for us.


class glork:
    def __init__(self, delay=1000, max=10):
        self.x = 0
        self.max = max
        self.id = timer.set_timer(delay, self.increment)
        # 046356.python.timer_demo.line23.comment Could use the threading module, but this is
        # 046357.python.timer_demo.line24.comment a win32 extension test after all! :-)
        self.event = win32event.CreateEvent(None, 0, 0, None)

    def increment(self, id, time):
        print("x = %d" % self.x)
        self.x += 1
        # 046358.python.timer_demo.line30.comment if we've reached the max count,
        # 046359.python.timer_demo.line31.comment kill off the timer.
        if self.x > self.max:
            # 046360.python.timer_demo.line33.comment we could have used 'self.id' here, too
            timer.kill_timer(id)
            win32event.SetEvent(self.event)


# 046361.python.timer_demo.line38.comment create a counter that will count from '1' thru '10', incrementing
# 046362.python.timer_demo.line39.comment once a second, and then stop.


def demo(delay=1000, stop=10):
    g = glork(delay, stop)
    # 046363.python.timer_demo.line44.comment Timers are message based - so we need
    # 046364.python.timer_demo.line45.comment To run a message loop while waiting for our timers
    # 046365.python.timer_demo.line46.comment to expire.
    start_time = time.time()
    while 1:
        # 046366.python.timer_demo.line49.comment We can't simply give a timeout of 30 seconds, as
        # 046367.python.timer_demo.line50.comment we may continouusly be recieving other input messages,
        # 046368.python.timer_demo.line51.comment and therefore never expire.
        rc = win32event.MsgWaitForMultipleObjects(
            (g.event,),  # list of objects
            0,  # wait all
            500,  # timeout
            win32event.QS_ALLEVENTS,  # type of input
        )
        if rc == win32event.WAIT_OBJECT_0:
            # 046373.python.timer_demo.line59.comment Event signalled.
            break
        elif rc == win32event.WAIT_OBJECT_0 + 1:
            # 046374.python.timer_demo.line62.comment Message waiting.
            if win32gui.PumpWaitingMessages():
                raise RuntimeError("We got an unexpected WM_QUIT message!")
        else:
            # 046375.python.timer_demo.line66.comment This wait timed-out.
            if time.time() - start_time > 30:
                raise RuntimeError("We timed out waiting for the timers to expire!")


if __name__ == "__main__":
    demo()
