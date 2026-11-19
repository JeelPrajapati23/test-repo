def total_pages(total_items: int, page_size: int) -> int:
    """Return the pages needed for all items, given a positive page size."""
    return total_items // page_size
