from django.core.management.base import BaseCommand

from exchange.ideabank import IdeaBankLoader
from exchange.selectby import SelectbyLoader


class Command(BaseCommand):
    help = 'Loads last rates form http://select.by'

    def handle(self, *args, **options):
        for loader_class in (IdeaBankLoader, SelectbyLoader):
            loader_class().load()

