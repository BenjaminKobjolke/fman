"""Typed source, job and transfer plan values plus Robocopy command building."""

from dataclasses import dataclass
import ntpath
import subprocess
from typing import Callable, Iterable

from .settings import Settings


COMMAND_UNITS = 24000


@dataclass(frozen=True, slots=True)
class Source:
	path: str
	name: str
	is_dir: bool
	identity: tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class Job:
	source: str
	destination: str
	entries: tuple[Source, ...]
	filenames: tuple[str, ...] = ()

	def arguments(self, executable: str, settings: Settings, move: bool = False,
			log: str | None = None) -> tuple[str, ...]:
		options = ('/NODCOPY',) if self.filenames else ('/E', '/DCOPY:DAT')
		if move:
			options += ('/MOV',) if self.filenames else ('/MOVE',)
		if log:
			options += ('/UNILOG+:' + log, '/TEE')
		return (
			executable, self.source, self.destination, *self.filenames,
			*settings.arguments(), *options
		)


@dataclass(frozen=True, slots=True)
class Plan:
	source: str
	destination: str
	source_identity: tuple[int, int, int]
	jobs: tuple[Job, ...]
	settings: Settings
	move: bool


def command_units(arguments: Iterable[str]) -> int:
	return len(subprocess.list2cmdline(list(arguments)).encode('utf-16-le')) // 2 + 1


def build_jobs(
		source: str, destination: str, entries: tuple[Source, ...],
		executable: str, settings: Settings, move: bool = False,
		log: str | None = None, limit: int = COMMAND_UNITS,
		check: Callable[[], None] = lambda: None
) -> tuple[Job, ...]:
	files = tuple(entry for entry in entries if not entry.is_dir)
	result: list[Job] = []
	batch: list[Source] = []
	base = Job(source, destination, (), ('placeholder',)).arguments(
		executable, settings, move, log
	)
	base_units = command_units(base) - len('placeholder') - 1
	units = base_units
	for entry in files:
		check()
		added = command_units((entry.name,))
		if base_units + added > limit:
			raise ValueError(
				'A selected filename cannot fit in a Robocopy command: ' + entry.name
			)
		if batch and units + added > limit:
			result.append(Job(
				source, destination, tuple(batch),
				tuple(item.name for item in batch)
			))
			batch, units = [], base_units
		batch.append(entry)
		units += added
	if batch:
		result.append(Job(
			source, destination, tuple(batch),
			tuple(item.name for item in batch)
		))
	for entry in entries:
		check()
		if entry.is_dir:
			result.append(Job(
				entry.path, ntpath.join(destination, entry.name), (entry,)
			))
	for job in result:
		if command_units(job.arguments(executable, settings, move, log)) > limit:
			raise ValueError(
				'Robocopy command exceeds its safe Windows argument limit.'
			)
	return tuple(result)


def exit_description(code: int) -> str:
	if type(code) is not int or not 0 <= code < 8:
		return 'Failed (exit %s)' % code
	parts = ['Copied files' if code & 1 else 'No files copied']
	if code & 2:
		parts.append('extra destination entries')
	if code & 4:
		parts.append('mismatches reported')
	return '; '.join(parts)
