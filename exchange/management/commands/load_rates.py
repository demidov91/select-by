from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Loads last rates form http://select.by'

    def handle(self, *args, **options):
        pass

