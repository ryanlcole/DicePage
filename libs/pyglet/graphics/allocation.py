"""Memory allocation algorithm for vertex arrays and buffers.

The region allocator is used to allocate vertex indices within a vertex
domain's  multiple buffers.  ("Buffer" refers to any abstract buffer presented
by :py:mod:`pyglet.graphics.vertexbuffer`.

The allocator will at times request more space from the buffers. The current
policy is to double the buffer size when there is not enough room to fulfil an
allocation.  The buffer is never resized smaller.

The allocator maintains references to free space only; it is the caller's
responsibility to maintain the allocated regions.
"""

# 029989.python.allocation.line15.comment Common cases:
# 029990.python.allocation.line16.comment -regions will be the same size (instances of same object, e.g. sprites)
# 029991.python.allocation.line17.comment -regions will not usually be resized (only exception is text)
# 029992.python.allocation.line18.comment -alignment of 4 vertices (glyphs, sprites, images, ...)
# 029993.python.allocation.line19.comment
# 029994.python.allocation.line20.comment Optimise for:
# 029995.python.allocation.line21.comment -keeping regions adjacent, reduce the number of entries in glMultiDrawArrays
# 029996.python.allocation.line22.comment -finding large blocks of allocated regions quickly (for drawing)
# 029997.python.allocation.line23.comment -finding block of unallocated space is the _uncommon_ case!
# 029998.python.allocation.line24.comment
# 029999.python.allocation.line25.comment Decisions:
# 030000.python.allocation.line26.comment -don't over-allocate regions to any alignment -- this would require more
# 030001.python.allocation.line27.comment work in finding the allocated spaces (for drawing) and would result in
# 030002.python.allocation.line28.comment more entries in glMultiDrawArrays
# 030003.python.allocation.line29.comment -don't move blocks when they truncate themselves.  try not to allocate the
# 030004.python.allocation.line30.comment space they freed too soon (they will likely need grow back into it later,
# 030005.python.allocation.line31.comment and growing will usually require a reallocation).
# 030006.python.allocation.line32.comment -allocator does not track individual allocated regions.  Trusts caller
# 030007.python.allocation.line33.comment to provide accurate (start, size) tuple, which completely describes
# 030008.python.allocation.line34.comment a region from the allocator's point of view.
# 030009.python.allocation.line35.comment -this means that compacting is probably not feasible, or would be hideously
# 030010.python.allocation.line36.comment expensive
from __future__ import annotations


class AllocatorMemoryException(Exception):  # noqa: N818
    """The buffer is not large enough to fulfil an allocation.

    Raised by `Allocator` methods when the operation failed due to
    lack of buffer space.  The buffer should be increased to at least
    requested_capacity and then the operation retried (guaranteed to
    pass second time).
    """

    def __init__(self, requested_capacity: int) -> None:
        """Requested capacity failed to allocate."""
        self.requested_capacity = requested_capacity


class Allocator:
    """Buffer space allocation implementation."""
    sizes: list[int]
    starts: list[int]

    __slots__ = 'capacity', 'starts', 'sizes'

    def __init__(self, capacity: int) -> None:
        """Create an allocator for a buffer of the specified maximum capacity size."""
        self.capacity = capacity

        # 030012.python.allocation.line65.comment Allocated blocks.  Start index and size in parallel lists.
        # 030013.python.allocation.line66.comment
        # 030014.python.allocation.line67.comment # = allocated, - = free
        # 030015.python.allocation.line68.comment
        # 030016.python.allocation.line69.comment 0  3 5        15   20  24                    40
        # 030017.python.allocation.line70.comment |###--##########-----####----------------------|
        # 030018.python.allocation.line71.comment
        # 030019.python.allocation.line72.comment starts = [0, 5, 20]
        # 030020.python.allocation.line73.comment sizes = [3, 10, 4]
        # 030021.python.allocation.line74.comment
        # 030022.python.allocation.line75.comment To calculate free blocks:
        # 030023.python.allocation.line76.comment for i in range(0, len(starts)):
        # 030024.python.allocation.line77.comment free_start[i] = starts[i] + sizes[i]
        # 030025.python.allocation.line78.comment free_size[i] =  starts[i+1] - free_start[i]
        # 030026.python.allocation.line79.comment free_size[i+1] = self.capacity - free_start[-1]

        self.starts = []
        self.sizes = []

    def set_capacity(self, size: int) -> None:
        """Resize the maximum buffer size.

        The capacity cannot be reduced.
        """
        assert size > self.capacity
        self.capacity = size

    def alloc(self, size: int) -> int:
        """Allocate memory in the buffer.

        Raises `AllocatorMemoryException` if the allocation cannot be
        fulfilled.

        Args:
            size:
                Size of region to allocate.

        Returns:
            Starting index of the allocated region.
        """
        assert size >= 0

        if size == 0:
            return 0

        # 030027.python.allocation.line110.comment Return start, or raise AllocatorMemoryException
        if not self.starts:
            if size <= self.capacity:
                self.starts.append(0)
                self.sizes.append(size)
                return 0

            raise AllocatorMemoryException(size)

        # 030028.python.allocation.line119.comment Restart from zero if space exists
        if self.starts[0] > size:
            self.starts.insert(0, 0)
            self.sizes.insert(0, size)
            return 0

        # 030029.python.allocation.line125.comment Allocate in a free space
        free_start = self.starts[0] + self.sizes[0]
        for i, (alloc_start, alloc_size) in enumerate(zip(self.starts[1:], self.sizes[1:])):
            # 030030.python.allocation.line128.comment Danger!
            # 030031.python.allocation.line129.comment i is actually index - 1 because of slicing above...
            # 030032.python.allocation.line130.comment starts[i]   points to the block before this free space
            # 030033.python.allocation.line131.comment starts[i+1] points to the block after this free space, and is always valid.
            free_size = alloc_start - free_start
            if free_size == size:
                # 030034.python.allocation.line134.comment Merge previous block with this one (removing this free space)
                self.sizes[i] += free_size + alloc_size
                del self.starts[i + 1]
                del self.sizes[i + 1]
                return free_start
            elif free_size > size:  # noqa: RET505
                # 030036.python.allocation.line140.comment Increase size of previous block to intrude into this free
                # 030037.python.allocation.line141.comment space.
                self.sizes[i] += size
                return free_start
            free_start = alloc_start + alloc_size

        # 030038.python.allocation.line146.comment Allocate at end of capacity
        free_size = self.capacity - free_start
        if free_size >= size:
            self.sizes[-1] += size
            return free_start

        raise AllocatorMemoryException(self.capacity + size - free_size)

    def realloc(self, start: int, size: int, new_size: int) -> int:
        """Reallocate a region of the buffer.

        This is more efficient than separate `dealloc` and `alloc` calls, as
        the region can often be resized in-place.

        Raises `AllocatorMemoryException` if the allocation cannot be
        fulfilled.

        Args:
            start:
                Current starting index of the region.
            size:
                Current size of the region.
            new_size: int
                New size of the region.

        Returns:
            Starting index of the re-allocated region.
        """
        assert size >= 0 and new_size >= 0  # noqa: PT018

        if new_size == 0:
            if size != 0:
                self.dealloc(start, size)
            return 0
        if size == 0:
            return self.alloc(new_size)

        # 030040.python.allocation.line183.comment return start, or raise AllocatorMemoryException

        # 030041.python.allocation.line185.comment Truncation is the same as deallocating the tail cruft
        if new_size < size:
            self.dealloc(start + new_size, size - new_size)
            return start

        # 030042.python.allocation.line190.comment Find which block it lives in
        for i, (alloc_start, alloc_size) in enumerate(zip(*(self.starts, self.sizes))):
            p = start - alloc_start
            if p >= 0 and size <= alloc_size - p:
                break
        if not (p >= 0 and size <= alloc_size - p):
            print(list(zip(self.starts, self.sizes)))
            print(start, size, new_size)
            print(p, alloc_start, alloc_size)
        assert p >= 0 and size <= alloc_size - p, 'Region not allocated'  # noqa: PT018

        if size == alloc_size - p:
            # 030044.python.allocation.line202.comment Region is at end of block. Find how much free space is after it.
            is_final_block = i == len(self.starts) - 1
            if not is_final_block:
                free_size = self.starts[i + 1] - (start + size)
            else:
                free_size = self.capacity - (start + size)

            # 030045.python.allocation.line209.comment TODO If region is an entire block being an island in free space,
            # 030046.python.allocation.line210.comment can possibly extend in both directions.

            if free_size == new_size - size and not is_final_block:
                # 030047.python.allocation.line213.comment Merge block with next (region is expanded in place to
                # 030048.python.allocation.line214.comment exactly fill the free space)
                self.sizes[i] += free_size + self.sizes[i + 1]
                del self.starts[i + 1]
                del self.sizes[i + 1]
                return start

            if free_size > new_size - size:
                # 030049.python.allocation.line221.comment Expand region in place
                self.sizes[i] += new_size - size
                return start

        # 030050.python.allocation.line225.comment The block must be repositioned.  Dealloc then alloc.

        # 030051.python.allocation.line227.comment But don't do this!  If alloc fails, we've already silently dealloc'd
        # 030052.python.allocation.line228.comment the original block.
        # 030053.python.allocation.line229.comment self.dealloc(start, size)
        # 030054.python.allocation.line230.comment return self.alloc(new_size)

        # 030055.python.allocation.line232.comment It must be alloc'd first.  We're not missing an optimisation
        # 030056.python.allocation.line233.comment here, because if freeing the block would've allowed for the block to
        # 030057.python.allocation.line234.comment be placed in the resulting free space, one of the above in-place
        # 030058.python.allocation.line235.comment checks would've found it.
        result = self.alloc(new_size)
        self.dealloc(start, size)
        return result

    def dealloc(self, start: int, size: int) -> None:
        """Free a region of the buffer.

        Args:
            start:
                Starting index of the region.
            size:
                Size of the region.

        """
        assert size >= 0

        if size == 0:
            return

        assert self.starts

        # 030059.python.allocation.line257.comment Find which block needs to be split
        for i, (alloc_start, alloc_size) in enumerate(zip(*(self.starts, self.sizes))):
            p = start - alloc_start
            if p >= 0 and size <= alloc_size - p:
                break

        # 030060.python.allocation.line263.comment Assert we left via the break
        assert p >= 0 and size <= alloc_size - p, 'Region not allocated'  # noqa: PT018

        if p == 0 and size == alloc_size:
            # 030062.python.allocation.line267.comment Remove entire block
            del self.starts[i]
            del self.sizes[i]
        elif p == 0:
            # 030063.python.allocation.line271.comment Truncate beginning of block
            self.starts[i] += size
            self.sizes[i] -= size
        elif size == alloc_size - p:
            # 030064.python.allocation.line275.comment Truncate end of block
            self.sizes[i] -= size
        else:
            # 030065.python.allocation.line278.comment Reduce size of left side, insert block at right side
            # 030066.python.allocation.line279.comment $ = dealloc'd block, # = alloc'd region from same block
            # 030067.python.allocation.line280.comment
            # 030068.python.allocation.line281.comment <------8------>
            # 030069.python.allocation.line282.comment <-5-><-6-><-7->
            # 030070.python.allocation.line283.comment 1    2    3    4
            # 030071.python.allocation.line284.comment #####$$$$$#####
            # 030072.python.allocation.line285.comment
            # 030073.python.allocation.line286.comment 1 = alloc_start
            # 030074.python.allocation.line287.comment 2 = start
            # 030075.python.allocation.line288.comment 3 = start + size
            # 030076.python.allocation.line289.comment 4 = alloc_start + alloc_size
            # 030077.python.allocation.line290.comment 5 = start - alloc_start = p
            # 030078.python.allocation.line291.comment 6 = size
            # 030079.python.allocation.line292.comment 7 = {8} - ({5} + {6}) = alloc_size - (p + size)
            # 030080.python.allocation.line293.comment 8 = alloc_size
            # 030081.python.allocation.line294.comment
            self.sizes[i] = p
            self.starts.insert(i + 1, start + size)
            self.sizes.insert(i + 1, alloc_size - (p + size))

    def get_allocated_regions(self) -> tuple[list, list]:
        """Get a list of (aggregate) allocated regions.

        The result of this method is ``(starts, sizes)``, where ``starts`` is
        a list of starting indices of the regions and ``sizes`` their
        corresponding lengths.
        """
        return self.starts, self.sizes

    def get_fragmented_free_size(self) -> int:
        """Returns the amount of space unused, not including the final free block."""
        if not self.starts:
            return 0

        # 030082.python.allocation.line313.comment Variation of search for free block.
        total_free = 0
        free_start = self.starts[0] + self.sizes[0]
        for i, (alloc_start, alloc_size) in enumerate(zip(self.starts[1:], self.sizes[1:])):
            total_free += alloc_start - free_start
            free_start = alloc_start + alloc_size

        return total_free

    def get_free_size(self) -> int:
        """Return the amount of space unused."""
        if not self.starts:
            return self.capacity

        free_end = self.capacity - (self.starts[-1] + self.sizes[-1])
        return self.get_fragmented_free_size() + free_end

    def get_usage(self) -> float:
        """Return fraction of capacity currently allocated."""
        return 1. - self.get_free_size() / float(self.capacity)

    def get_fragmentation(self) -> float:
        """Return fraction of free space that is not expandable."""
        free_size = self.get_free_size()
        if free_size == 0:
            return 0.
        return self.get_fragmented_free_size() / float(self.get_free_size())

    def __str__(self) -> str:
        return 'allocs=' + repr(list(zip(self.starts, self.sizes)))

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} {self!s}>'
