#
# The Mistune Processor recognizes Markdown and fenced code blocks and translates
# content into Kivy markup.
#

from ..renderers.kivy_mistune_bbcode import MarkdownToBBCodeParser

class MistuneProcessor:

    def __init__(self):
        self.renderer = MarkdownToBBCodeParser()

    def process(self, content: str, role: str):

        if role == 'assistant':

            processed = self.renderer.parse(content)

            try:
                processed = self.renderer.parse(content)
            except Exception as e:
                print(f"MistuneException")
                print(e)
                processed = None

            return processed

        else:
            return None
            
