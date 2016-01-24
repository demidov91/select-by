from django.core.management.base import BaseCommand


from exchange.utils import RatesLoader


class Command(BaseCommand):
    help = 'Loads last rates form http://select.by'

    def handle(self, *args, **options):
        RatesLoader.load()

