"""Validate a transfer's sources and destinations, then freeze its job plan."""

from contextlib import closing
import ntpath
import os
from pathlib import Path
import stat
from tempfile import TemporaryDirectory
from typing import Callable, Iterable

from . import windows
from .jobs import Job, Plan, Source, build_jobs
from .paths import (absolute_path, canonical, contains, from_url,
	identity, inspect_source, key, related)
from .settings import Settings


def check_names(
		source: str, entries: tuple[Source, ...], check: Callable[[], None]
) -> None:
	wanted = {entry.name.upper().casefold() for entry in entries}
	if len(wanted) != len(entries):
		raise ValueError('Ambiguous selected names differ only by case.')
	found: set[str] = set()
	with closing(windows.filenames(source, check)) as names:
		for name, alternate in names:
			folded = name.upper().casefold()
			if (
				alternate and alternate.upper().casefold() in wanted
				and alternate.upper().casefold() != folded
			):
				raise ValueError(
					'Select the long filename, not its 8.3 alias: ' + alternate
				)
			if folded in wanted:
				if folded in found:
					raise ValueError(
						'Ambiguous case-insensitive filename match: ' + name
					)
				found.add(folded)
	if found != wanted:
		raise ValueError(
			'A selected name is missing or is an 8.3 alias; '
			'select its long filename again.'
		)


def prepare(source_url: str, selected: Iterable[str], destination: str, executable: str,
		settings: Settings, move: bool = False, log: str | None = None,
		check: Callable[[], None] = lambda: None) -> Plan:
	source = from_url(source_url)
	destination = absolute_path(destination)
	check()
	parent = inspect_source(source)
	if not stat.S_ISDIR(parent.st_mode):
		raise ValueError('The source pane no longer shows a directory.')
	parent_identity = identity(parent)
	source_path, destination_path = canonical(source), canonical(destination)
	log_path = canonical(log) if log else None
	if log_path and related(log_path, destination_path):
		raise ValueError(
			'The destination overlaps the transfer log; '
			'disable logging for this operation.'
		)
	entries: list[Source] = []
	seen: set[str] = set()
	for url in selected:
		check()
		path = from_url(url)
		if key(ntpath.dirname(path)) != key(source):
			raise ValueError('The selection changed location; invoke Robocopy again.')
		if path in seen:
			continue
		seen.add(path)
		name = ntpath.basename(path)
		info = inspect_source(path)
		is_dir = stat.S_ISDIR(info.st_mode)
		if not is_dir and name.startswith('-'):
			raise ValueError(
				'Robocopy treats names beginning with a hyphen as switches: ' + name
			)
		entries.append(Source(path, name, is_dir, identity(info)))
	if not entries:
		raise ValueError('No file is selected.')
	if any(not entry.is_dir for entry in entries) and windows.case_sensitive(source):
		raise ValueError(
			'Exact loose-file selection in case-sensitive folders is not supported.'
		)
	check_names(source, tuple(entries), check)
	check()
	ancestor = Path(destination)
	while True:
		check()
		try:
			info = ancestor.stat()
		except FileNotFoundError:
			if ancestor.parent == ancestor:
				raise
			ancestor = ancestor.parent
		else:
			if not stat.S_ISDIR(info.st_mode):
				raise NotADirectoryError(str(ancestor))
			ancestor_identity = identity(info)
			break
	destination_exists = key(str(ancestor)) == key(destination)
	if (
		key(source_path) == key(destination_path)
		or destination_exists and ancestor_identity[:2] == parent_identity[:2]
	):
		raise ValueError('Cannot transfer entries onto themselves.')
	for entry in entries:
		check()
		target = ntpath.join(destination, entry.name)
		entry_path = ntpath.join(source_path, entry.name)
		if entry.is_dir:
			entry_path, target_path = canonical(entry.path), canonical(target)
			if contains(entry_path, target_path):
				raise ValueError(
					'Cannot transfer a directory into its own subtree: ' + entry.name
				)
		if destination_exists:
			try:
				target_info = os.stat(target)
			except FileNotFoundError:
				pass
			else:
				if identity(target_info)[:2] == entry.identity[:2]:
					raise ValueError(
						'Source and destination refer to the same entry: ' + entry.name
					)
		if log_path and (
				contains(entry_path, log_path)
				or entry.is_dir and related(log_path, target_path)
		):
			raise ValueError(
				'The transfer overlaps its own log; '
				'disable logging for this operation.'
			)
	jobs = build_jobs(
		source, destination, tuple(entries), executable, settings, move, log,
		check=check
	)
	return Plan(source, destination, parent_identity, jobs, settings, move)


def recheck(plan: Plan, job: Job, check: Callable[[], None] = lambda: None) -> None:
	check()
	if identity(inspect_source(plan.source)) != plan.source_identity:
		raise ValueError('The source folder changed; start a new transfer.')
	for entry in job.entries:
		check()
		info = inspect_source(entry.path)
		if (
			identity(info) != entry.identity
			or stat.S_ISDIR(info.st_mode) != entry.is_dir
		):
			raise ValueError('A selected source was replaced: ' + entry.name)


def remaining(
		entries: Iterable[Source], check: Callable[[], None] = lambda: None
) -> tuple[int, int, tuple[str, ...]]:
	present = unknown = 0
	examples: list[str] = []
	for entry in entries:
		check()
		try:
			os.lstat(entry.path)
		except FileNotFoundError:
			continue
		except OSError:
			unknown += 1
		else:
			present += 1
		if len(examples) < 10:
			examples.append(entry.path)
	return present, unknown, tuple(examples)


def probe(
		executable: str, settings: Settings,
		check: Callable[[], None] = lambda: None
) -> None:
	with TemporaryDirectory(prefix='robocopy-options-') as temporary:
		root = Path(temporary)
		source, destination = root / 'source', root / 'destination'
		source.mkdir()
		destination.mkdir()
		log = str(root / 'probe.txt') if settings.log_enabled else None
		if log:
			Path(log).write_bytes(b'\xff\xfe')
		for filenames in (('probe.txt',), ()):
			job = Job(str(source), str(destination), (), filenames)
			code, output = windows.run(
				(*job.arguments(executable, settings, True, log), '/L'),
				check=check, timeout=15
			)
			if not 0 <= code < 8:
				raise OSError(
					'Robocopy does not accept the required options '
					'(exit %d): %s' % (code, output[-1500:])
				)
		if log:
			text = Path(log).read_text(encoding='utf-16')
			if '\ufeff' in text:
				raise OSError('Robocopy does not append compatible Unicode logs.')
