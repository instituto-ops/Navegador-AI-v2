"""Watchdog for handling wait events."""

import asyncio

from browser_use.browser.events import WaitEvent
from browser_use.browser.watchdogs.action_watchdog_base import ActionWatchdogBase
from browser_use.observability import observe_debug

# Rebuild event models
WaitEvent.model_rebuild()


class WaitWatchdog(ActionWatchdogBase):
	"""Handles wait browser actions."""

	@observe_debug(ignore_input=True, ignore_output=True, name='wait_event_handler')
	async def on_WaitEvent(self, event: WaitEvent) -> None:
		"""Handle wait request."""
		try:
			# Cap wait time at maximum
			actual_seconds = min(max(event.seconds, 0), event.max_seconds)
			if actual_seconds != event.seconds:
				self.logger.info(f'🕒 Waiting for {actual_seconds} seconds (capped from {event.seconds}s)')
			else:
				self.logger.info(f'🕒 Waiting for {actual_seconds} seconds')

			await asyncio.sleep(actual_seconds)
		except Exception as e:
			raise
