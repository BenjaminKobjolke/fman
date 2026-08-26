from build_impl import copy_python_library
from fbs import path
from fbs.cmdline import command
from fbs.freeze.windows import freeze_windows
from os.path import isdir
from shutil import copytree, rmtree
from subprocess import run

@command
def freeze():
	freeze_windows()
	_copy_release_notes()
	rmtree(path('${core_plugin_in_freeze_dir}/bin/mac'))
	rmtree(path('${core_plugin_in_freeze_dir}/bin/linux'))
	# Open Sans is only used on Linux. Further, it fails to load on some users'
	# Windows systems (see fman issue #480). Remove it to avoid problems,
	# improve startup performance and decrease fman's download size.
	# (Also note that a more elegant solution would be to only place
	# Open Sans in src/main/resources/*linux*/Plugins/Core. But the current
	# implementation cannot handle multiple dirs .../resources/main,
	# .../resources/linux for one plugin.)
	# The whole directory, so its LICENSE goes with the font it covers - a
	# licence left behind for a font that is not shipped is just confusing.
	rmtree(path('${core_plugin_in_freeze_dir}/Fonts/Open Sans'))
	copy_python_library('send2trash', path('${core_plugin_in_freeze_dir}'))
	# core.release_notes (Core plugin) imports this to detect the system
	# language for locale fallback - not scanned by PyInstaller since plugin
	# code is bundled as data, so it's copied in explicitly like send2trash:
	copy_python_library('python_localization', path('${core_plugin_in_freeze_dir}'))

def _copy_release_notes():
	# release_notes/<version>_<build>/<locale>.json (docs/CREATE_NEW_RELEASE.md)
	# lives at the project root, authored per release - not under
	# src/main/resources, so fbs doesn't bundle it automatically. Copied next
	# to Plugins/ in the frozen output so core.release_notes.release_notes_dir()
	# finds it there (docs/CREATE_NEW_RELEASE.md #4). Skipped entirely if no
	# release has been authored yet, so a checkout with an empty release_notes/
	# doesn't break freeze().
	src_dir = path('release_notes')
	if isdir(src_dir):
		copytree(src_dir, path('${freeze_dir}/release_notes'))

@command
def sign():
	# fbs's own sign() uses a local signtool + certificate.pfx that expired
	# 2022-07-03. Use the XIDA network-share signing handshake instead
	# (tools/sign_exe.bat -> release-tool's PreSigner).
	_sign_exe(path('${freeze_dir}/fman.exe'))

@command
def sign_installer():
	_sign_exe(path('target/fmanSetup.exe'))

def _sign_exe(exe_path):
	run([path('tools/sign_exe.bat'), exe_path], shell=True, check=True)

@command
def upload():
	# This fork does not have access to the original project's AWS account, and
	# doesn't publish to update.fman.io (that's Michael Herrmann's distribution
	# channel, not ours). Distribution instead goes through GitHub Releases —
	# see docs/CREATE_NEW_RELEASE.md step 4.5 / tools/github_release.bat.
	pass
