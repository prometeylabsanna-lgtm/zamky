from decimal import Decimal

from django.shortcuts import get_object_or_404

from catalog.models import Product
from pages.i18n_lib import tr

CART_SESSION_KEY = 'cart'
WISHLIST_SESSION_KEY = 'wishlist'


class CartError(Exception):
    """Помилка операції з кошиком."""


class CartService:
    def __init__(self, request):
        self.request = request
        self.session = request.session
        cart = self.session.get(CART_SESSION_KEY)
        if not isinstance(cart, dict):
            cart = {}
        self.cart = cart
        self.last_warnings: list[str] = []

    def save(self):
        self.session[CART_SESSION_KEY] = self.cart
        self.session.modified = True

    def clear(self):
        self.cart = {}
        self.save()

    @staticmethod
    def _parse_qty(quantity):
        try:
            return int(quantity)
        except (TypeError, ValueError) as exc:
            raise CartError(tr('Некоректна кількість.')) from exc

    def add(self, product_id, quantity=1):
        product = get_object_or_404(Product, pk=product_id, is_active=True)
        quantity = self._parse_qty(quantity)
        if quantity < 1:
            raise CartError(tr('Кількість має бути не менше 1.'))
        if product.stock <= 0:
            raise CartError(tr('Товару немає в наявності.'))
        key = str(product.pk)
        current = int(self.cart.get(key, {}).get('qty', 0))
        new_qty = current + quantity
        if new_qty > product.stock:
            raise CartError(tr('Доступно лише {n} шт.').format(n=product.stock))
        self.cart[key] = {'qty': new_qty}
        self.save()
        return product, new_qty

    def set_quantity(self, product_id, quantity):
        product = get_object_or_404(Product, pk=product_id, is_active=True)
        quantity = self._parse_qty(quantity)
        key = str(product.pk)
        if quantity <= 0:
            self.cart.pop(key, None)
            self.save()
            return product, 0
        if quantity > product.stock:
            raise CartError(tr('Доступно лише {n} шт.').format(n=product.stock))
        self.cart[key] = {'qty': quantity}
        self.save()
        return product, quantity

    def remove(self, product_id):
        key = str(product_id)
        self.cart.pop(key, None)
        self.save()

    def _products_map(self):
        ids = [int(k) for k in self.cart.keys()]
        if not ids:
            return {}
        return {
            p.pk: p
            for p in Product.objects.filter(pk__in=ids, is_active=True).prefetch_related('images')
        }

    def items(self):
        products = self._products_map()
        result = []
        dirty = False
        self.last_warnings = []
        for key, data in list(self.cart.items()):
            product = products.get(int(key))
            if not product:
                self.cart.pop(key, None)
                dirty = True
                continue
            qty = int(data.get('qty', 0))
            if qty < 1:
                self.cart.pop(key, None)
                dirty = True
                continue
            if qty > product.stock:
                qty = product.stock
                if qty < 1:
                    self.cart.pop(key, None)
                    dirty = True
                    self.last_warnings.append(
                        tr('«{name}» більше немає в наявності та видалено з кошика.').format(
                            name=tr(product.name)
                        )
                    )
                    continue
                self.cart[key] = {'qty': qty}
                dirty = True
                self.last_warnings.append(
                    tr('Кількість «{name}» зменшено до {n} шт.').format(
                        name=tr(product.name), n=qty
                    )
                )
            line_total = product.price * qty
            old_total = (product.old_price or product.price) * qty
            result.append(
                {
                    'product': product,
                    'quantity': qty,
                    'unit_price': product.price,
                    'line_total': line_total,
                    'old_total': old_total,
                }
            )
        if dirty:
            self.save()
        return result

    def warnings_text(self) -> str:
        return '; '.join(self.last_warnings)

    def total_quantity(self):
        return sum(int(v.get('qty', 0)) for v in self.cart.values())

    def subtotal(self):
        return sum((item['line_total'] for item in self.items()), Decimal('0'))

    def validate_stock(self):
        problems = []
        for item in self.items():
            product = item['product']
            if item['quantity'] > product.stock:
                problems.append(
                    tr('{name}: доступно {n} шт.').format(
                        name=tr(product.name), n=product.stock
                    )
                )
        return problems


class WishlistService:
    def __init__(self, request):
        self.session = request.session
        data = self.session.get(WISHLIST_SESSION_KEY)
        if not isinstance(data, list):
            data = []
        self.items_ids = [int(x) for x in data]

    def save(self):
        self.session[WISHLIST_SESSION_KEY] = self.items_ids
        self.session.modified = True

    def toggle(self, product_id):
        product_id = int(product_id)
        get_object_or_404(Product, pk=product_id, is_active=True)
        if product_id in self.items_ids:
            self.items_ids.remove(product_id)
            added = False
        else:
            self.items_ids.append(product_id)
            added = True
        self.save()
        return added

    def contains(self, product_id):
        return int(product_id) in self.items_ids

    def count(self):
        return len(self.items_ids)

    def products(self):
        """Активні товари в порядку додавання; прибирає зниклі id."""
        if not self.items_ids:
            return []
        by_id = {
            p.pk: p
            for p in Product.objects.filter(
                pk__in=self.items_ids, is_active=True
            ).prefetch_related('images')
        }
        result = []
        kept = []
        for pk in self.items_ids:
            product = by_id.get(pk)
            if product:
                result.append(product)
                kept.append(pk)
        if kept != self.items_ids:
            self.items_ids = kept
            self.save()
        return result
