import logging
import threading

from datetime import datetime, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand

from iotaclient.iota_ import iota_utils

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Performs replays of unconfirmed transactions on a regular bases'

    def handle(self, *args, **options):
        logger.info('Starting replay daemon')
        self.start_replays()

    def start_replays(self):

        # perform initial replay
        iota_utils.replay_bundles()

        # start periodic execution
        self._schedule_replay()

    def _schedule_replay(self):
        # noinspection PyBroadException
        def perform_replay():
            try:
                iota_utils.replay_bundles()
            except Exception:
                logger.exception('Error while executing replay.')
            self._schedule_replay()

        next_time = datetime.now() + timedelta(seconds=settings.IOTA_REPLAY_INTERVAL)
        threading.Timer((next_time - datetime.now()).total_seconds(), perform_replay).start()
        logger.info('Scheduled next replay at {} (UTC)'.format(next_time))
