#
# The Pygments BBCode formatter works very well to generate Kivy Markup with the exception
# of the lack of escaping "[" characters in emitted code.  The solution is to use
# the kivy escape_markup function to escape characters properly.
#
# This specialization of Pygments BBCodeFormatter overrides one method to insert the
# necessary escaping.
#
# Tom Sheffler 2025
#

from pygments.formatters import BBCodeFormatter
from pygments.util import get_bool_opt
from kivy.utils import escape_markup # "[" to "&lb;"

__all__ = ['KivyBBCodeFormatter']


class KivyBBCodeFormatter(BBCodeFormatter):

    def format_unencoded(self, tokensource, outfile):
        if self._code:
            outfile.write('[code]')
        if self._mono:
            outfile.write('[font=monospace]')

        lastval = ''
        lasttype = None

        for ttype, value in tokensource:
            while ttype not in self.styles:
                ttype = ttype.parent
            if ttype == lasttype:
                lastval += value
            else:
                if lastval:
                    # lastval = lastval.replace("[", "&bl;")
                    lastval = escape_markup(lastval)
                    start, end = self.styles[lasttype]
                    outfile.write(''.join((start, lastval, end)))
                lastval = value
                lasttype = ttype

        if lastval:
            start, end = self.styles[lasttype]
            outfile.write(''.join((start, lastval, end)))

        if self._mono:
            outfile.write('[/font]')
        if self._code:
            outfile.write('[/code]')
        if self._code or self._mono:
            outfile.write('\n')
