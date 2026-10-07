from django.views.generic import TemplateView


INFO_PAGES = {
    'about': {
        'name': 'Про нас',
        'anchor': 'about',
    },
    'delivery': {
        'name': 'Доставка і оплата',
        'anchor': 'delivery',
    },
    'contacts': {
        'name': 'Контакти',
        'anchor': 'contacts',
    },
    'privacy': {
        'name': 'Політика конфіденційності',
        'anchor': 'privacy',
    },
    'offer': {
        'name': 'Договір оферти',
        'anchor': 'offer',
    },
}


class InfoView(TemplateView):
    template_name = 'pages/info.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        page_key = self.kwargs.get('page', 'about')
        if page_key not in INFO_PAGES:
            page_key = 'about'
        ctx.update(
            {
                'page_key': page_key,
                'page_name': INFO_PAGES[page_key]['name'],
                'info_pages': INFO_PAGES,
            }
        )
        return ctx
