import asyncio
import re
import logging
from decimal import Decimal
from typing import Iterable, Tuple

from aiohttp.client import ClientSession, TCPConnector, ClientTimeout
from django.db.models import Q

from exchange.defines import SELECTBY_EXCHANGE_OFFICE_PAGE_PATTERN
from exchange.models import ExchangeOffice


logger = logging.getLogger(__name__)
ymaps_coordinates_pattern = re.compile(
    'new ymaps\.Placemark\(\[(?P<latitude>-?\d+(\.\d+)?), (?P<longitude>-?\d+(\.\d+)?)\]'
)

def update_all_coordinates():
    multi_update_coordinates(
        ExchangeOffice.objects.filter(
            Q(no_coordinates=False),
            Q(is_removed=False),
            Q(latitude__isnull=True)|Q(longitude__isnull=True)
        )
    )


def multi_update_coordinates(offices: Iterable[ExchangeOffice]):
    asyncio.run(_multi_update_coordinates(offices))


async def _multi_update_coordinates(offices: Iterable[ExchangeOffice]):
    async with ClientSession(
            connector=TCPConnector(limit=3),
            timeout=ClientTimeout(
                total=30*60,        # connections are queued, so 30 minutes is ok.
                sock_connect=30,    # 30 seconds to really connect.
                sock_read=60,       # 1 minute to GET.
            )
    ) as client:
        await asyncio.gather(
            *(load_and_save_coordinates(x, client) for x in offices),
            return_exceptions=True
        )


def extract_coordinates_from_page(page_content: str) -> Tuple[Decimal, Decimal]:
    match = ymaps_coordinates_pattern.search(page_content)
    if match is None:
        raise ValueError('Coordinates were not found on the page.')

    return Decimal(match.group('latitude')), Decimal(match.group('longitude'))


async def load_coordinates(
        exchange_office: ExchangeOffice,
        client: ClientSession
) -> Tuple[Decimal, Decimal]:
    async with client.get(
        SELECTBY_EXCHANGE_OFFICE_PAGE_PATTERN % exchange_office.identifier
    ) as response:
        if response.status != 200:
            raise ValueError(
                f'Unexpected http status: {response.status} '
                f'for office {exchange_office.identifier}'
            )

        content = (await response.read()).decode('windows-1251')
        return extract_coordinates_from_page(content)


async def load_and_save_coordinates(office: ExchangeOffice, client: ClientSession):
    try:
        coordinates = await load_coordinates(office, client)
    except Exception as e:
        logger.exception(
            'Unexpected error on fetching %s coordinates.',
            office.identifier
        )
        if office.latitude is None or office.longitude is None:
            office.no_coordinates = True
            office.save(update_fields=['no_coordinates'])

    else:
        office.latitude, office.longitude = coordinates
        office.no_coordinates = False
        office.save()
        logger.info('Exchange office %s coordinates are updated.', office.identifier)
