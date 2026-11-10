import time
import logging
from django.core.management.base import BaseCommand
from apps.outbox.services.publisher import publish_pending_outbox_events

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Runs the Transactional Outbox Publisher service daemon'

    def add_arguments(self, parser):
        parser.add_argument(
            '--poll-interval',
            type=float,
            default=1.0,
            help='Polling interval in seconds (default: 1.0)'
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Run once and exit'
        )

    def handle(self, *args, **options):
        poll_interval = options['poll_interval']
        run_once = options['once']

        self.stdout.write(self.style.SUCCESS('HookSentry Transactional Outbox Publisher started.'))

        while True:
            try:
                count = publish_pending_outbox_events()
                if count > 0:
                    self.stdout.write(f"Published {count} event(s).")
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f"Error publishing outbox events: {exc}"))

            if run_once:
                break
            time.sleep(poll_interval)
