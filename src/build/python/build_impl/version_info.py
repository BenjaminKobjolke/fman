def brand_version_info(source, app_name, display_name):
	for field in ('FileDescription', 'ProductName'):
		old_value = "StringStruct('%s', '%s')" % (field, app_name)
		new_value = "StringStruct('%s', '%s')" % (field, display_name)
		source = source.replace(old_value, new_value)
	return source
