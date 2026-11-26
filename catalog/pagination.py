from django.core.paginator import InvalidPage


class ClampPageMixin:
    """Невалідний або занадто великий ?page= → 200 на існуючій сторінці."""

    def paginate_queryset(self, queryset, page_size):
        paginator = self.get_paginator(
            queryset,
            page_size,
            orphans=self.get_paginate_orphans(),
            allow_empty_first_page=self.get_allow_empty(),
        )
        raw = self.kwargs.get(self.page_kwarg) or self.request.GET.get(self.page_kwarg) or 1
        try:
            page_number = int(raw)
        except (TypeError, ValueError):
            page_number = 1
        if page_number < 1:
            page_number = 1
        last = paginator.num_pages or 1
        if page_number > last:
            page_number = last
        try:
            page = paginator.page(page_number)
        except InvalidPage:
            page = paginator.page(1)
        return (paginator, page, page.object_list, page.has_other_pages())
