"""Форми фільтрів адмінки з українськими підписами."""

from unfold.contrib.filters.forms import RangeDateForm


class ZamkyRangeDateForm(RangeDateForm):
    """Діапазон дат: «Від» / «До»."""

    def __init__(self, name: str, *args, **kwargs) -> None:
        super().__init__(name, *args, **kwargs)
        self.fields[self.name + '_from'].widget.attrs['placeholder'] = 'Від'
        self.fields[self.name + '_to'].widget.attrs['placeholder'] = 'До'
