from fman.impl.theme import Theme
from fman.impl.themes import DEFAULT_COLORS
from os.path import join
from tempfile import TemporaryDirectory
from unittest import TestCase

_BASE_QSS = 'QTableView { background-color: $pane_bg; }\n'
# The declarations Theme._get_quicksearch_item_css() insists on. Every real
# Theme.css has them; a test one has to as well or load() raises.
_QUICKSEARCH_CSS = """
.quicksearch-item {
	padding-top: 1px;
	padding-left: 4px;
	padding-right: 4px;
	border-top: 1px solid $popup_divider_top;
	border-bottom: 1px solid $popup_divider_bottom;
}
.quicksearch-item-title { font-size: 10pt; color: $popup_item_fg; }
.quicksearch-item-title-highlight { color: $bright_fg; }
.quicksearch-item-hint { font-size: 8pt; color: $bright_fg; }
.quicksearch-item-description { font-size: 8pt; color: $muted_fg; }
"""

class StubApp:
	def __init__(self):
		self.stylesheet = None
	def set_style_sheet(self, stylesheet):
		self.stylesheet = stylesheet

class ThemeTest(TestCase):
	def test_base_qss_is_substituted(self):
		theme = self._make_theme()
		theme.enable_updates()
		self.assertIn(DEFAULT_COLORS['pane_bg'], self._app.stylesheet)
		self.assertNotIn('$pane_bg', self._app.stylesheet)
	def test_set_colors_restyles_base_qss(self):
		theme = self._make_theme()
		theme.enable_updates()
		theme.set_colors(dict(DEFAULT_COLORS, pane_bg='#123456'))
		self.assertIn('#123456', self._app.stylesheet)
	def test_set_colors_reparses_loaded_css(self):
		theme = self._make_theme()
		theme.load(self._write('Theme.css', _QUICKSEARCH_CSS))
		theme.enable_updates()
		theme.set_colors(dict(DEFAULT_COLORS, popup_item_fg='#abcdef'))
		title_color = theme.get_quicksearch_item_css()['title']['color']
		self.assertEqual('#abcdef', title_color.name())
	def test_css_layers_keep_their_order(self):
		# The user's own Theme.css loads last and must keep winning over the
		# theme's colors, also after a switch.
		theme = self._make_theme()
		theme.load(self._write('Theme.css', _QUICKSEARCH_CSS))
		theme.load(self._write('User.css', '* { font-size: 14pt; }'))
		theme.enable_updates()
		theme.set_colors(dict(DEFAULT_COLORS, pane_bg='#123456'))
		stylesheet = self._app.stylesheet
		self.assertLess(
			stylesheet.index('#123456'), stylesheet.index('font-size: 14pt')
		)
	def test_unload_forgets_the_source(self):
		theme = self._make_theme()
		path = self._write('Theme.css', _QUICKSEARCH_CSS)
		theme.load(path)
		theme.load(self._write('Other.css', _QUICKSEARCH_CSS))
		theme.unload(path)
		theme.enable_updates()
		# Would raise KeyError if unload had left the raw source behind:
		theme.set_colors(dict(DEFAULT_COLORS, popup_item_fg='#abcdef'))
	def setUp(self):
		super().setUp()
		self._app = StubApp()
		self._tmp_dir = TemporaryDirectory()
		self.addCleanup(self._tmp_dir.cleanup)
	def _make_theme(self):
		return Theme(self._app, [self._write('styles.qss', _BASE_QSS)])
	def _write(self, name, contents):
		result = join(self._tmp_dir.name, name)
		with open(result, 'w', encoding='utf-8') as f:
			f.write(contents)
		return result
