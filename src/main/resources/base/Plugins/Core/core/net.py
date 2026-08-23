from requests import RequestException
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import requests

def get_bytes(url):
	try:
		return urlopen(url).read()
	except HTTPError:
		raise
	except URLError:
		# Fallback: Some users get "SSL: CERTIFICATE_VERIFY_FAILED" for urlopen.
		try:
			response = requests.get(url)
		except RequestException as e:
			raise URLError(e.__class__.__name__)
		if response.status_code != 200:
			raise HTTPError(
				url, response.status_code, response.reason, response.headers,
				None
			)
		return response.content
