"""Run a validated Robocopy plan while reporting progress and partial results."""

import os
from time import monotonic

import fman

from . import logs, planner, windows
from .jobs import Plan, exit_description


TRANSFER_TIMEOUT = 24 * 60 * 60
STATUS_TIMEOUT = 8


class Transfer(fman.Task):
	def __init__(self, title: str, plan: Plan, log_path: str | None,
			executable: str) -> None:
		super().__init__(title, size=max(1, len(plan.jobs)), fn=self._perform)
		self.plan = plan
		self.log_path = log_path
		self.executable = executable
		self.summary = ''
		self._last_text = 0.0

	def _check(self) -> None:
		self.check_canceled()
		now = monotonic()
		if now - self._last_text >= 1:
			verb = 'Moving' if self.plan.move else 'Copying'
			elapsed = int(now - self._started)
			self.set_text('%s with Robocopy — %02d:%02d:%02d elapsed' % (
				verb, elapsed // 3600, elapsed // 60 % 60, elapsed % 60))
			self._last_text = now

	def _perform(self) -> None:
		self._started = monotonic()
		self._last_text = 0
		transfer_log = None
		results: list[str] = []
		try:
			transfer_log = (
				logs.TransferLog(self.log_path, str(self))
				if self.log_path else None
			)
			for index, job in enumerate(self.plan.jobs, 1):
				self._check()
				planner.recheck(self.plan, job, self._check)
				code, output = windows.run(
					job.arguments(
						self.executable, self.plan.settings, self.plan.move,
						self.log_path
					),
					check=self._check, timeout=TRANSFER_TIMEOUT,
				)
				results.append(exit_description(code))
				self.set_progress(index)
				if code >= 8:
					details = output[-1500:].strip()
					message = '%s failed. %s' % (str(self), exit_description(code))
					if details:
						message += '\n\n' + details
					self.show_alert(message)
					break
			self.summary = '%s: %s' % (
				'Robocopy move' if self.plan.move else 'Robocopy copy',
				'; '.join(results) if results else 'No work was needed',
			)
			fman.show_status_message(self.summary, timeout_secs=STATUS_TIMEOUT)
		except fman.Task.Canceled:
			present, unknown, examples = planner.remaining(
				(entry for job in self.plan.jobs for entry in job.entries), lambda: None
			)
			self.summary = 'Canceled; partial changes may have been kept.'
			if present or unknown:
				self.summary += ' %d source item(s) remain%s.' % (
					present, ' or could not be checked' if unknown else '')
			if examples:
				self.summary += '\n' + '\n'.join(examples[:3])
			self.show_alert(self.summary)
		finally:
			if transfer_log:
				try:
					transfer_log.finish(
						self.summary or 'Transfer stopped before completion.'
					)
				except OSError as error:
					self.show_alert('Could not finish the Robocopy log: %s' % error)
				else:
					if self.plan.settings.open_log_on_finish:
						try:
							os.startfile(str(transfer_log.path))
						except OSError as error:
							self.show_alert('Could not open the Robocopy log: %s' % error)
					try:
						transfer_log.prune(self.plan.settings.log_retention_count)
					except OSError as error:
						self.show_alert('Could not prune Robocopy logs: %s' % error)

