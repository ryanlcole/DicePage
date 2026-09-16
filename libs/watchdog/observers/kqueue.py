""":module: watchdog.observers.kqueue
:synopsis: ``kqueue(2)`` based emitter implementation.
:author: yesudeep@google.com (Yesudeep Mangalapilly)
:author: contact@tiger-222.fr (Mickaël Schoentgen)
:platforms: macOS and BSD with kqueue(2).

.. WARNING:: kqueue is a very heavyweight way to monitor file systems.
             Each kqueue-detected directory modification triggers
             a full directory scan. Traversing the entire directory tree
             and opening file descriptors for all files will create
             performance problems. We need to find a way to re-scan
             only those directories which report changes and do a diff
             between two sub-DirectorySnapshots perhaps.

.. ADMONITION:: About OS X performance guidelines

    Quote from the `macOS File System Performance Guidelines`_:

        "When you only want to track changes on a file or directory, be sure to
        open it using the ``O_EVTONLY`` flag. This flag prevents the file or
        directory from being marked as open or in use. This is important
        if you are tracking files on a removable volume and the user tries to
        unmount the volume. With this flag in place, the system knows it can
        dismiss the volume. If you had opened the files or directories without
        this flag, the volume would be marked as busy and would not be
        unmounted."

    ``O_EVTONLY`` is defined as ``0x8000`` in the OS X header files.
    More information here: http://www.mlsite.net/blog/?p=2312

Classes
-------
.. autoclass:: KqueueEmitter
   :members:
   :show-inheritance:

Collections and Utility Classes
-------------------------------
.. autoclass:: KeventDescriptor
   :members:
   :show-inheritance:

.. autoclass:: KeventDescriptorSet
   :members:
   :show-inheritance:

.. _macOS File System Performance Guidelines:
    http://developer.apple.com/library/ios/#documentation/Performance/Conceptual/FileSystem/Articles/TrackingChanges.html#//apple_ref/doc/uid/20001993-CJBJFIDD

"""


# 045776.python.kqueue.line53.comment The `select` module varies between platforms.
# 045777.python.kqueue.line54.comment mypy may complain about missing module attributes depending on which platform it's running on.
# 045778.python.kqueue.line55.comment The comment below disables mypy's attribute check.
# 045779.python.kqueue.line56.comment mypy: disable-error-code="attr-defined, name-defined"

from __future__ import annotations

import contextlib
import errno
import os
import os.path
import select
import threading
from stat import S_ISDIR
from typing import TYPE_CHECKING

from watchdog.events import (
    EVENT_TYPE_CREATED,
    EVENT_TYPE_DELETED,
    EVENT_TYPE_MOVED,
    DirCreatedEvent,
    DirDeletedEvent,
    DirModifiedEvent,
    DirMovedEvent,
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileMovedEvent,
    generate_sub_moved_events,
)
from watchdog.observers.api import DEFAULT_EMITTER_TIMEOUT, DEFAULT_OBSERVER_TIMEOUT, BaseObserver, EventEmitter
from watchdog.utils import platform
from watchdog.utils.dirsnapshot import DirectorySnapshot

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import Callable

    from watchdog.events import FileSystemEvent
    from watchdog.observers.api import EventQueue, ObservedWatch

# 045780.python.kqueue.line94.comment Maximum number of events to process.
MAX_EVENTS = 4096

# 045781.python.kqueue.line97.comment O_EVTONLY value from the header files for OS X only.
O_EVTONLY = 0x8000

# 045782.python.kqueue.line100.comment Pre-calculated values for the kevent filter, flags, and fflags attributes.
WATCHDOG_OS_OPEN_FLAGS = O_EVTONLY if platform.is_darwin() else os.O_RDONLY | os.O_NONBLOCK
WATCHDOG_KQ_FILTER = select.KQ_FILTER_VNODE
WATCHDOG_KQ_EV_FLAGS = select.KQ_EV_ADD | select.KQ_EV_ENABLE | select.KQ_EV_CLEAR
WATCHDOG_KQ_FFLAGS = (
    select.KQ_NOTE_DELETE
    | select.KQ_NOTE_WRITE
    | select.KQ_NOTE_EXTEND
    | select.KQ_NOTE_ATTRIB
    | select.KQ_NOTE_LINK
    | select.KQ_NOTE_RENAME
    | select.KQ_NOTE_REVOKE
)


def absolute_path(path: bytes | str) -> bytes | str:
    return os.path.abspath(os.path.normpath(path))


# 045783.python.kqueue.line119.comment Flag tests.


def is_deleted(kev: select.kevent) -> bool:
    """Determines whether the given kevent represents deletion."""
    return kev.fflags & select.KQ_NOTE_DELETE > 0


def is_modified(kev: select.kevent) -> bool:
    """Determines whether the given kevent represents modification."""
    fflags = kev.fflags
    return (fflags & select.KQ_NOTE_EXTEND > 0) or (fflags & select.KQ_NOTE_WRITE > 0)


def is_attrib_modified(kev: select.kevent) -> bool:
    """Determines whether the given kevent represents attribute modification."""
    return kev.fflags & select.KQ_NOTE_ATTRIB > 0


def is_renamed(kev: select.kevent) -> bool:
    """Determines whether the given kevent represents movement."""
    return kev.fflags & select.KQ_NOTE_RENAME > 0


class KeventDescriptorSet:
    """Thread-safe kevent descriptor collection."""

    def __init__(self) -> None:
        self._descriptors: set[KeventDescriptor] = set()
        self._descriptor_for_path: dict[bytes | str, KeventDescriptor] = {}
        self._descriptor_for_fd: dict[int, KeventDescriptor] = {}
        self._kevents: list[select.kevent] = []
        self._lock = threading.Lock()

    @property
    def kevents(self) -> list[select.kevent]:
        """List of kevents monitored."""
        with self._lock:
            return self._kevents

    @property
    def paths(self) -> list[bytes | str]:
        """List of paths for which kevents have been created."""
        with self._lock:
            return list(self._descriptor_for_path.keys())

    def get_for_fd(self, fd: int) -> KeventDescriptor:
        """Given a file descriptor, returns the kevent descriptor object
        for it.

        :param fd:
            OS file descriptor.
        :type fd:
            ``int``
        :returns:
            A :class:`KeventDescriptor` object.
        """
        with self._lock:
            return self._descriptor_for_fd[fd]

    def get(self, path: bytes | str) -> KeventDescriptor:
        """Obtains a :class:`KeventDescriptor` object for the specified path.

        :param path:
            Path for which the descriptor will be obtained.
        """
        with self._lock:
            path = absolute_path(path)
            return self._get(path)

    def __contains__(self, path: bytes | str) -> bool:
        """Determines whether a :class:`KeventDescriptor has been registered
        for the specified path.

        :param path:
            Path for which the descriptor will be obtained.
        """
        with self._lock:
            path = absolute_path(path)
            return self._has_path(path)

    def add(self, path: bytes | str, *, is_directory: bool) -> None:
        """Adds a :class:`KeventDescriptor` to the collection for the given
        path.

        :param path:
            The path for which a :class:`KeventDescriptor` object will be
            added.
        :param is_directory:
            ``True`` if the path refers to a directory; ``False`` otherwise.
        :type is_directory:
            ``bool``
        """
        with self._lock:
            path = absolute_path(path)
            if not self._has_path(path):
                self._add_descriptor(KeventDescriptor(path, is_directory=is_directory))

    def remove(self, path: bytes | str) -> None:
        """Removes the :class:`KeventDescriptor` object for the given path
        if it already exists.

        :param path:
            Path for which the :class:`KeventDescriptor` object will be
            removed.
        """
        with self._lock:
            path = absolute_path(path)
            if self._has_path(path):
                self._remove_descriptor(self._get(path))

    def clear(self) -> None:
        """Clears the collection and closes all open descriptors."""
        with self._lock:
            for descriptor in self._descriptors:
                descriptor.close()
            self._descriptors.clear()
            self._descriptor_for_fd.clear()
            self._descriptor_for_path.clear()
            self._kevents = []

    # 045784.python.kqueue.line240.comment Thread-unsafe methods. Locking is provided at a higher level.
    def _get(self, path: bytes | str) -> KeventDescriptor:
        """Returns a kevent descriptor for a given path."""
        return self._descriptor_for_path[path]

    def _has_path(self, path: bytes | str) -> bool:
        """Determines whether a :class:`KeventDescriptor` for the specified
        path exists already in the collection.
        """
        return path in self._descriptor_for_path

    def _add_descriptor(self, descriptor: KeventDescriptor) -> None:
        """Adds a descriptor to the collection.

        :param descriptor:
            An instance of :class:`KeventDescriptor` to be added.
        """
        self._descriptors.add(descriptor)
        self._kevents.append(descriptor.kevent)
        self._descriptor_for_path[descriptor.path] = descriptor
        self._descriptor_for_fd[descriptor.fd] = descriptor

    def _remove_descriptor(self, descriptor: KeventDescriptor) -> None:
        """Removes a descriptor from the collection.

        :param descriptor:
            An instance of :class:`KeventDescriptor` to be removed.
        """
        self._descriptors.remove(descriptor)
        del self._descriptor_for_fd[descriptor.fd]
        del self._descriptor_for_path[descriptor.path]
        self._kevents.remove(descriptor.kevent)
        descriptor.close()


class KeventDescriptor:
    """A kevent descriptor convenience data structure to keep together:

        * kevent
        * directory status
        * path
        * file descriptor

    :param path:
        Path string for which a kevent descriptor will be created.
    :param is_directory:
        ``True`` if the path refers to a directory; ``False`` otherwise.
    :type is_directory:
        ``bool``
    """

    def __init__(self, path: bytes | str, *, is_directory: bool) -> None:
        self._path = absolute_path(path)
        self._is_directory = is_directory
        self._fd = os.open(path, WATCHDOG_OS_OPEN_FLAGS)
        self._kev = select.kevent(
            self._fd,
            filter=WATCHDOG_KQ_FILTER,
            flags=WATCHDOG_KQ_EV_FLAGS,
            fflags=WATCHDOG_KQ_FFLAGS,
        )

    @property
    def fd(self) -> int:
        """OS file descriptor for the kevent descriptor."""
        return self._fd

    @property
    def path(self) -> bytes | str:
        """The path associated with the kevent descriptor."""
        return self._path

    @property
    def kevent(self) -> select.kevent:
        """The kevent object associated with the kevent descriptor."""
        return self._kev

    @property
    def is_directory(self) -> bool:
        """Determines whether the kevent descriptor refers to a directory.

        :returns:
            ``True`` or ``False``
        """
        return self._is_directory

    def close(self) -> None:
        """Closes the file descriptor associated with a kevent descriptor."""
        with contextlib.suppress(OSError):
            os.close(self.fd)

    @property
    def key(self) -> tuple[bytes | str, bool]:
        return (self.path, self.is_directory)

    def __eq__(self, descriptor: object) -> bool:
        if not isinstance(descriptor, KeventDescriptor):
            return NotImplemented
        return self.key == descriptor.key

    def __ne__(self, descriptor: object) -> bool:
        if not isinstance(descriptor, KeventDescriptor):
            return NotImplemented
        return self.key != descriptor.key

    def __hash__(self) -> int:
        return hash(self.key)

    def __repr__(self) -> str:
        return f"<{type(self).__name__}: path={self.path!r}, is_directory={self.is_directory}>"


class KqueueEmitter(EventEmitter):
    """kqueue(2)-based event emitter.

    .. ADMONITION:: About ``kqueue(2)`` behavior and this implementation

              ``kqueue(2)`` monitors file system events only for
              open descriptors, which means, this emitter does a lot of
              book-keeping behind the scenes to keep track of open
              descriptors for every entry in the monitored directory tree.

              This also means the number of maximum open file descriptors
              on your system must be increased **manually**.
              Usually, issuing a call to ``ulimit`` should suffice::

                  ulimit -n 1024

              Ensure that you pick a number that is larger than the
              number of files you expect to be monitored.

              ``kqueue(2)`` does not provide enough information about the
              following things:

              * The destination path of a file or directory that is renamed.
              * Creation of a file or directory within a directory; in this
                case, ``kqueue(2)`` only indicates a modified event on the
                parent directory.

              Therefore, this emitter takes a snapshot of the directory
              tree when ``kqueue(2)`` detects a change on the file system
              to be able to determine the above information.

    :param event_queue:
        The event queue to fill with events.
    :param watch:
        A watch object representing the directory to monitor.
    :type watch:
        :class:`watchdog.observers.api.ObservedWatch`
    :param timeout:
        Read events blocking timeout (in seconds).
    :type timeout:
        ``float``
    :param event_filter:
        Collection of event types to emit, or None for no filtering (default).
    :type event_filter:
        Iterable[:class:`watchdog.events.FileSystemEvent`] | None
    :param stat: stat function. See ``os.stat`` for details.
    """

    def __init__(
        self,
        event_queue: EventQueue,
        watch: ObservedWatch,
        *,
        timeout: float = DEFAULT_EMITTER_TIMEOUT,
        event_filter: list[type[FileSystemEvent]] | None = None,
        stat: Callable[[str], os.stat_result] = os.stat,
    ) -> None:
        super().__init__(event_queue, watch, timeout=timeout, event_filter=event_filter)

        self._kq = select.kqueue()
        self._lock = threading.RLock()

        # 045785.python.kqueue.line414.comment A collection of KeventDescriptor.
        self._descriptors = KeventDescriptorSet()

        def custom_stat(path: str, cls: KqueueEmitter = self) -> os.stat_result:
            stat_info = stat(path)
            cls._register_kevent(path, is_directory=S_ISDIR(stat_info.st_mode))
            return stat_info

        self._snapshot = DirectorySnapshot(watch.path, recursive=watch.is_recursive, stat=custom_stat)

    def _register_kevent(self, path: bytes | str, *, is_directory: bool) -> None:
        """Registers a kevent descriptor for the given path.

        :param path:
            Path for which a kevent descriptor will be created.
        :param is_directory:
            ``True`` if the path refers to a directory; ``False`` otherwise.
        :type is_directory:
            ``bool``
        """
        try:
            self._descriptors.add(path, is_directory=is_directory)
        except OSError as e:
            if e.errno == errno.ENOENT:
                # 045786.python.kqueue.line438.comment Probably dealing with a temporary file that was created
                # 045787.python.kqueue.line439.comment and then quickly deleted before we could open
                # 045788.python.kqueue.line440.comment a descriptor for it. Therefore, simply queue a sequence
                # 045789.python.kqueue.line441.comment of created and deleted events for the path.

                # 045790.python.kqueue.line443.comment TODO: We could simply ignore these files.
                # 045791.python.kqueue.line444.comment Locked files cause the python process to die with
                # 045792.python.kqueue.line445.comment a bus error when we handle temporary files.
                # 045793.python.kqueue.line446.comment eg. .git/index.lock when running tig operations.
                # 045794.python.kqueue.line447.comment I don't fully understand this at the moment.
                pass
            elif e.errno == errno.EOPNOTSUPP:
                # 045795.python.kqueue.line450.comment Probably dealing with the socket or special file
                # 045796.python.kqueue.line451.comment mounted through a file system that does not support
                # 045797.python.kqueue.line452.comment access to it (e.g. NFS). On BSD systems look at
                # 045798.python.kqueue.line453.comment EOPNOTSUPP in man 2 open.
                pass
            else:
                # 045799.python.kqueue.line456.comment All other errors are propagated.
                raise

    def _unregister_kevent(self, path: bytes | str) -> None:
        """Convenience function to close the kevent descriptor for a
        specified kqueue-monitored path.

        :param path:
            Path for which the kevent descriptor will be closed.
        """
        self._descriptors.remove(path)

    def queue_event(self, event: FileSystemEvent) -> None:
        """Handles queueing a single event object.

        :param event:
            An instance of :class:`watchdog.events.FileSystemEvent`
            or a subclass.
        """
        # 045800.python.kqueue.line475.comment Handles all the book keeping for queued events.
        # 045801.python.kqueue.line476.comment We do not need to fire moved/deleted events for all subitems in
        # 045802.python.kqueue.line477.comment a directory tree here, because this function is called by kqueue
        # 045803.python.kqueue.line478.comment for all those events anyway.
        EventEmitter.queue_event(self, event)
        if event.event_type == EVENT_TYPE_CREATED:
            self._register_kevent(event.src_path, is_directory=event.is_directory)
        elif event.event_type == EVENT_TYPE_MOVED:
            self._unregister_kevent(event.src_path)
            self._register_kevent(event.dest_path, is_directory=event.is_directory)
        elif event.event_type == EVENT_TYPE_DELETED:
            self._unregister_kevent(event.src_path)

    def _gen_kqueue_events(
        self, kev: select.kevent, ref_snapshot: DirectorySnapshot, new_snapshot: DirectorySnapshot
    ) -> Generator[FileSystemEvent]:
        """Generate events from the kevent list returned from the call to
        :meth:`select.kqueue.control`.

        .. NOTE:: kqueue only tells us about deletions, file modifications,
                  attribute modifications. The other events, namely,
                  file creation, directory modification, file rename,
                  directory rename, directory creation, etc. are
                  determined by comparing directory snapshots.
        """
        descriptor = self._descriptors.get_for_fd(kev.ident)
        src_path = descriptor.path

        if is_renamed(kev):
            # 045804.python.kqueue.line504.comment Kqueue does not specify the destination names for renames
            # 045805.python.kqueue.line505.comment to, so we have to process these using the a snapshot
            # 045806.python.kqueue.line506.comment of the directory.
            yield from self._gen_renamed_events(
                src_path,
                ref_snapshot,
                new_snapshot,
                is_directory=descriptor.is_directory,
            )
        elif is_attrib_modified(kev):
            if descriptor.is_directory:
                yield DirModifiedEvent(src_path)
            else:
                yield FileModifiedEvent(src_path)
        elif is_modified(kev):
            if descriptor.is_directory:
                if self.watch.is_recursive or self.watch.path == src_path:
                    # 045807.python.kqueue.line521.comment When a directory is modified, it may be due to
                    # 045808.python.kqueue.line522.comment sub-file/directory renames or new file/directory
                    # 045809.python.kqueue.line523.comment creation. We determine all this by comparing
                    # 045810.python.kqueue.line524.comment snapshots later.
                    yield DirModifiedEvent(src_path)
            else:
                yield FileModifiedEvent(src_path)
        elif is_deleted(kev):
            if descriptor.is_directory:
                yield DirDeletedEvent(src_path)
            else:
                yield FileDeletedEvent(src_path)

    def _parent_dir_modified(self, src_path: bytes | str) -> DirModifiedEvent:
        """Helper to generate a DirModifiedEvent on the parent of src_path."""
        return DirModifiedEvent(os.path.dirname(src_path))

    def _gen_renamed_events(
        self,
        src_path: bytes | str,
        ref_snapshot: DirectorySnapshot,
        new_snapshot: DirectorySnapshot,
        *,
        is_directory: bool,
    ) -> Generator[FileSystemEvent]:
        """Compares information from two directory snapshots (one taken before
        the rename operation and another taken right after) to determine the
        destination path of the file system object renamed, and yields
        the appropriate events to be queued.
        """
        try:
            f_inode = ref_snapshot.inode(src_path)
        except KeyError:
            # 045811.python.kqueue.line554.comment Probably caught a temporary file/directory that was renamed
            # 045812.python.kqueue.line555.comment and deleted. Fires a sequence of created and deleted events
            # 045813.python.kqueue.line556.comment for the path.
            if is_directory:
                yield DirCreatedEvent(src_path)
                yield DirDeletedEvent(src_path)
            else:
                yield FileCreatedEvent(src_path)
                yield FileDeletedEvent(src_path)
                # 045814.python.kqueue.line563.comment We don't process any further and bail out assuming
            # 045815.python.kqueue.line564.comment the event represents deletion/creation instead of movement.
            return

        dest_path = new_snapshot.path(f_inode)
        if dest_path is not None:
            dest_path = absolute_path(dest_path)
            if is_directory:
                yield DirMovedEvent(src_path, dest_path)
            else:
                yield FileMovedEvent(src_path, dest_path)
            yield self._parent_dir_modified(src_path)
            yield self._parent_dir_modified(dest_path)
            if is_directory and self.watch.is_recursive:
                # 045816.python.kqueue.line577.comment TODO: Do we need to fire moved events for the items
                # 045817.python.kqueue.line578.comment inside the directory tree? Does kqueue does this
                # 045818.python.kqueue.line579.comment all by itself? Check this and then enable this code
                # 045819.python.kqueue.line580.comment only if it doesn't already.
                # 045820.python.kqueue.line581.comment A: It doesn't. So I've enabled this block.
                yield from generate_sub_moved_events(src_path, dest_path)
        else:
            # 045821.python.kqueue.line584.comment If the new snapshot does not have an inode for the
            # 045822.python.kqueue.line585.comment old path, we haven't found the new name. Therefore,
            # 045823.python.kqueue.line586.comment we mark it as deleted and remove unregister the path.
            if is_directory:
                yield DirDeletedEvent(src_path)
            else:
                yield FileDeletedEvent(src_path)
            yield self._parent_dir_modified(src_path)

    def _read_events(self, timeout: float) -> list[select.kevent]:
        """Reads events from a call to the blocking
        :meth:`select.kqueue.control()` method.

        :param timeout:
            Blocking timeout for reading events.
        :type timeout:
            ``float`` (seconds)
        """
        return self._kq.control(self._descriptors.kevents, MAX_EVENTS, timeout)

    def queue_events(self, timeout: float) -> None:
        """Queues events by reading them from a call to the blocking
        :meth:`select.kqueue.control()` method.

        :param timeout:
            Blocking timeout for reading events.
        :type timeout:
            ``float`` (seconds)
        """
        with self._lock:
            try:
                event_list = self._read_events(timeout)
                # 045824.python.kqueue.line616.comment TODO: investigate why order appears to be reversed
                event_list.reverse()

                # 045825.python.kqueue.line619.comment Take a fresh snapshot of the directory and update the
                # 045826.python.kqueue.line620.comment saved snapshot.
                new_snapshot = DirectorySnapshot(self.watch.path, recursive=self.watch.is_recursive)
                ref_snapshot = self._snapshot
                self._snapshot = new_snapshot
                diff_events = new_snapshot - ref_snapshot

                # 045827.python.kqueue.line626.comment Process events
                for directory_created in diff_events.dirs_created:
                    self.queue_event(DirCreatedEvent(directory_created))
                for file_created in diff_events.files_created:
                    self.queue_event(FileCreatedEvent(file_created))
                for file_modified in diff_events.files_modified:
                    self.queue_event(FileModifiedEvent(file_modified))

                for kev in event_list:
                    for event in self._gen_kqueue_events(kev, ref_snapshot, new_snapshot):
                        self.queue_event(event)

            except OSError as e:
                if e.errno != errno.EBADF:
                    raise

    def on_thread_stop(self) -> None:
        # 045828.python.kqueue.line643.comment Clean up.
        with self._lock:
            self._descriptors.clear()
            self._kq.close()


class KqueueObserver(BaseObserver):
    """Observer thread that schedules watching directories and dispatches
    calls to event handlers.
    """

    def __init__(self, *, timeout: float = DEFAULT_OBSERVER_TIMEOUT) -> None:
        super().__init__(KqueueEmitter, timeout=timeout)
