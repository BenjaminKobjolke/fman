"""Validated Robocopy options and their command-line switches."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
	threads: int = 8
	retries: int = 1
	retry_wait_seconds: int = 1
	restartable: bool = False
	unbuffered: bool = False
	log_enabled: bool = False
	open_log_on_finish: bool = False
	log_retention_count: int = 20

	@classmethod
	def load(cls, value: dict[str, object]) -> 'Settings':
		if not isinstance(value, dict):
			raise ValueError('Robocopy.json must contain an object.')
		unknown = set(value) - set(cls.__dataclass_fields__)
		if unknown:
			raise ValueError('Unknown Robocopy setting: ' + ', '.join(sorted(unknown)))
		result = cls(**value)
		for name, minimum, maximum in (('threads', 1, 32), ('retries', 0, 10),
				('retry_wait_seconds', 0, 30), ('log_retention_count', 1, 100)):
			item = getattr(result, name)
			if type(item) is not int or not minimum <= item <= maximum:
				raise ValueError('%s must be an integer from %d to %d.' % (name, minimum, maximum))
		for name in ('restartable', 'unbuffered', 'log_enabled', 'open_log_on_finish'):
			if type(getattr(result, name)) is not bool:
				raise ValueError(name + ' must be boolean.')
		if result.open_log_on_finish and not result.log_enabled:
			raise ValueError('open_log_on_finish requires log_enabled.')
		return result

	def arguments(self) -> tuple[str, ...]:
		return ('/COPY:DAT', '/XJD', '/XJF', '/NP', '/UNICODE', '/FP', '/BYTES',
			'/MT:%d' % self.threads, '/R:%d' % self.retries, '/W:%d' % self.retry_wait_seconds) + \
			(('/Z',) if self.restartable else ()) + (('/J',) if self.unbuffered else ())
