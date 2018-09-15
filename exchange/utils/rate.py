from django.db.models import Max, Min

from exchange.models import Rate


def get_best_rates(currency: int, exchanger_offices, buy: bool):
    return Rate.objects.filter(
        rate=Rate.objects.filter(
            exchange_office__in=exchanger_offices,
            currency=currency,
            buy=buy
        ).aggregate(
            val=Max('rate') if buy else Min('rate')
        )['val'],
        exchange_office__in=exchanger_offices,
        currency=currency,
        buy=buy
    )
