from build_impl import copy_python_library
from fbs import path
from shutil import rmtree

def postprocess_exe():
	rmtree(path('${core_plugin_in_freeze_dir}/bin/mac'))
	rmtree(path('${core_plugin_in_freeze_dir}/bin/windows'))
	# Roboto is only used on Windows. For reasons not yet known, loading
	# fonts sometimes fails. (A known case is that Open Sans fails to load on
	# some user's Windows systems - see fman issue #480). Remove the unused font
	# to avoid potential problems, improve startup performance and decrease
	# fman's download size.
	# (Also note that a more elegant solution would be to only place
	# Open Sans in src/main/resources/*linux*/Plugins/Core. But the current
	# implementation cannot handle multiple dirs .../resources/main,
	# .../resources/linux for one plugin.)
	# The whole directory, so its LICENSE goes with the font it covers - a
	# licence left behind for a font that is not shipped is just confusing.
	rmtree(path('${core_plugin_in_freeze_dir}/Fonts/Roboto'))
	copy_python_library('send2trash', path('${core_plugin_in_freeze_dir}'))