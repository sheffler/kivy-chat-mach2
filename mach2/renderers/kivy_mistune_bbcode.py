#
# Kivy Markup is similar to BBcode.  This renderer uses the Mistune Markdown parser and emits
# marked up text in Kivy Markup style.
#
# The Pygments code formatter is used to colorize code.
#
# This process is somewhat fragile.  Experimental for now.
# Run this file's self-test view from the root directory to see
# what it can do.
#
#    $ python -m mach2.renderers.kivy_mistune_bbcode
#
# Tom Sheffler (c) 2025

from typing import Any, Dict, List, Optional, cast
import mistune
from mistune import BaseRenderer
from mistune.core import BlockState, InlineState

# Use Pygments to format fenced code blocks
from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
# from pygments.formatters import BBCodeFormatter
from .kivy_pygments_bbcode import KivyBBCodeFormatter
from pygments.util import ClassNotFound

# likely Roboto special characters
#    https://www.fileformat.info/info/unicode/font/roboto/grid.htm

BULLET = "\u2022"
SQUAREROOT = "\u221A"
LOZENGE = "\u25CA"  # diamond
ENQUAD = "\u2000" # space
EMQUAD = "\u2001" # space
ENSP = "\u2002" # en space
EMSP = "\u2003" # em space

class BBCodeRenderer(BaseRenderer):
    """
    Custom renderer that converts parsed Markdown tokens to BBCode format.
    
    This acts as our 'translator' - it receives structured markdown tokens
    from mistune and converts them to their BBCode equivalents.
    
    BaseRenderer methods use (token, state) signature pattern.
    """

    level = 0
    ordered = [ False ]
    counter = [ 0 ]
    
    def render_children(self, token, state):
        """
        Helper method to render child tokens.
        BaseRenderer doesn't provide this, so we implement it ourselves.
        """
        if 'children' not in token:
            return ''
        
        children_output = []
        for child in token['children']:
            # Get the method name for this token type
            method_name = child['type']
            if hasattr(self, method_name):
                method = getattr(self, method_name)
                children_output.append(method(child, state))
            elif 'raw' in child:
                # Fallback for plain text tokens
                children_output.append(child['raw'])
        
        return ''.join(children_output)
    
    def text(self, token, state):
        """Render plain text"""
        return token['raw']

    def block_text(self, token, state):
        children = self.render_children(token, state)
        return f"{children}"
    
    def paragraph(self, token, state):
        """Convert paragraph to BBCode (just add newlines)"""
        children = self.render_children(token, state)
        return f"{children}\n"
    
    def heading(self, token, state, **attrs):
        """Convert headings to BBCode size tags"""
        level = token['attrs']['level']
        children = self.render_children(token, state)
        # BBCode uses size tags, typically 1-7 where 7 is largest
        size = max(1, 21 - level)  # h1=7, h2=6, h3=5, etc.
        return f"[size={size}sp][b]{children}[/b][/size]\n\n"
    
    def emphasis(self, token, state):
        """Convert *italic* to [i]italic[/i]"""
        children = self.render_children(token, state)
        return f"[i]{children}[/i]"
    
    def strong(self, token, state):
        """Convert **bold** to [b]bold[/b]"""
        children = self.render_children(token, state)
        return f"[b]{children}[/b]"
    
    def link(self, token, state):
        """Convert [text](url) to [url=url]text[/url]"""
        url = token['attrs']['url']
        children = self.render_children(token, state)
        return f"[u][ref={url}]{children}[/ref][/u]"
    
    def image(self, token, state):
        """Convert ![alt](url) to [img]url[/img]"""
        url = token['attrs']['url']
        return f"[img]{url}[/img]"
    
    def codespan(self, token, state):
        """Convert `code` to [code]code[/code]"""
        return f"[font=RobotoMono-Regular]{token['raw']}[/font]"
    
    def block_code(self, token, state):
        """Convert code blocks to [code] blocks"""
        attrs = token.get("attrs", {})
        info = cast(str, attrs.get("info", ""))
        code = token['raw']
        if info:
            try:
                lexer = get_lexer_by_name(info.strip())
            except ClassNotFound:
                lexer = TextLexer()
        else:
            lexer = TextLexer()
        
        formatter = KivyBBCodeFormatter(
            codetag=False,
            linenos=False
        )

        highlighted = highlight(code, lexer, formatter)
        return "[font=RobotoMono-Regular]" + highlighted + "[/font]\n"
    
    def block_quote(self, token, state):
        """Convert > quotes to [quote] blocks"""
        children = self.render_children(token, state)
        return f"[quote]\n{children.rstrip()}\n[/quote]\n"

    def _list_push(self, isOrdered):

        self.level = self.level + 1
        self.ordered.append(isOrdered)
        self.counter.append(0)

    def _list_pop(self):

        self.level = self.level -1
        self.ordered.pop()
        self.counter.pop()
        self.counter[-1] = 0

    def _list_indent_prefix(self):
        return ENSP * ((self.level-1) * 4)

    def _list_bullet(self):

        if self.ordered[-1]:
            count = self.counter[-1]
            if self.level == 1:
                return f"[b]{count}.[/b]"

            elif self.level == 2:
                caps = "ABCDEFGHIJKLMNOPqRSTUVWZYZ"
                letter = caps[count]
                return f"[b]{letter}.[/b]"

            elif self.level == 3:
                return f"[b]{count}.[/b]"

            elif self.level == 4:
                letters = "abcdefghijklmnopqrstuvwxyz"
                letter = letter[count]
                return f"[b]{letter}.[/b]"

            else:
                return f"[b]{count}.[/b]"

        else:

            # all levels use same bullet for now
            return "\u2022"

    
    def list_item(self, token, state, **attrs):
        """Convert list items to [*] format"""
        prefix = self._list_indent_prefix()
        self.counter[-1] = self.counter[-1] + 1 # increment list counter
        bullet = self._list_bullet()
        children = self.render_children(token, state)
        return f"{prefix}{bullet} {children.rstrip()}\n"
    
    def task_list_item(self, token, state):
        attrs = token.get("attrs", {})
        prefix = self._list_indent_prefix()
        self.counter[-1] = self.counter[-1] + 1
        checked = attrs.get('checked', False)
        children = self.render_children(token, state)
        if checked:
            return f"{prefix}[{SQUAREROOT}] {children.rstrip()}\n"
        else:
            return f"{prefix}[{ENQUAD}] {children.rstrip()}\n"  # enquad
            

    def list(self, token, state, **attrs):
        """Convert lists to BBCode list format"""
        ordered = token['attrs'].get('ordered', False)
        self._list_push(ordered)
        children = self.render_children(token, state)
        self._list_pop()
        return f"{children.rstrip()}\n\n"
        # return f"\n[list]\n{children.rstrip()}\n[/list]\n"
    
    def strikethrough(self, token, state):
        """Convert ~~strike~~ to [s]strike[/s]"""
        children = self.render_children(token, state)
        return f"~{children}~"
    
    def linebreak(self, token, state):
        """Convert line breaks"""
        return "\n"
    
    def softbreak(self, token, state):
        """Convert soft line breaks"""
        return "\n"
    
    def thematic_break(self, token, state):
        """Convert horizontal rules to separator"""
        return "================\n\n"
    
    def blank_line(self, token, state):
        """Handle blank lines"""
        return "\n"


class MarkdownToBBCodeParser:
    """
    Main parser class that orchestrates the conversion process.
    
    Think of this as the 'translation service manager' that coordinates
    between the markdown reader (mistune) and our BBCode translator.
    """
    
    def __init__(self):
        """Initialize the parser with our custom BBCode renderer"""
        self.renderer = BBCodeRenderer()
        self.markdown = mistune.create_markdown(
            renderer=self.renderer,
            plugins=[
                'strikethrough',  # Support ~~text~~
                'task_lists',     # Support - [ ] and - [x]
                'url',           # Auto-link URLs
                'abbr',          # Abbreviations (if needed)
            ]
        )
    
    def parse(self, markdown_text: str) -> str:
        """
        Convert markdown text to BBCode format.
        
        Args:
            markdown_text: Raw markdown string
            
        Returns:
            Formatted BBCode string
        """
        bbcode_output = self.markdown(markdown_text)
        return self._clean_output(bbcode_output)
    
    def _clean_output(self, bbcode_text: str) -> str:
        """Clean up the BBCode output by removing extra whitespace"""
        # Remove excessive newlines while preserving intentional spacing
        lines = bbcode_text.split('\n')
        cleaned_lines = []
        consecutive_empty = 0
        
        for line in lines:
            if line.strip() == '':
                consecutive_empty += 1
                if consecutive_empty <= 2:  # Allow max 2 consecutive empty lines
                    cleaned_lines.append(line)
            else:
                consecutive_empty = 0
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def parse_file(self, filepath: str, encoding: str = 'utf-8') -> str:
        """
        Parse a markdown file and return BBCode.
        
        Args:
            filepath: Path to markdown file
            encoding: File encoding (default: utf-8)
            
        Returns:
            BBCode formatted string
        """
        with open(filepath, 'r', encoding=encoding) as f:
            markdown_content = f.read()
        return self.parse(markdown_content)
    
    def save_bbcode(self, bbcode_text: str, output_path: str, encoding: str = 'utf-8'):
        """
        Save BBCode output to a file.
        
        Args:
            bbcode_text: The BBCode formatted text
            output_path: Where to save the file
            encoding: File encoding (default: utf-8)
        """
        with open(output_path, 'w', encoding=encoding) as f:
            f.write(bbcode_text)

#
# SAMPLE TEXT
#

sample = """
# Main Title

This is a **bold statement** with *italic text* and `inline code`.

## Subtitle

Here's a [link to Google](https://google.com) and an image:
![Alt text](https://example.com/image.jpg)

### Code Block

```python
def hello_world():
    print("Hello, World!")
```

> This is a blockquote
> with multiple lines

```
def foo():
    return "thing"
```    

### Lists

- First item
- Second item with **bold**
    - list item a
    - list item b
    - list item c
- Third item

1. Numbered item
2. Another numbered item
3. And a sub numbered list
    1. this is an item
    2. this is an item
    3. this is an item

---

A checkmark: \u2713
A bullet: \u2022 \N{BULLET}

That's all folks! ~~This is crossed out~~.

- [ ] task list
- [x] is done
- [ ] still to do


```json
{
  "firstName": "John",
  "lastName": "Doe",
  "age": 30,
  "isStudent": false,
  "courses": [
    {
      "title": "History 101",
      "credits": 3
    },
    {
      "title": "Math 205",
      "credits": 4
    }
  ],
  "address": {
    "street": "123 Main St",
    "city": "Anytown",
    "zipCode": "12345"
  }
}
```


This was a structure I saw emitted by an LLM that did not work very well when the code wasn't indented.
With the code indented, the list works as expected.

1. This is the first step in the program.
    ``` c
    int x = 2;
    ```

2. This is the second step in the program.

    ``` c
    x *= 4;
    ```
3. This is the third step in the program.

    ``` c
    printf("The Number is:%d", x);
    ```

"""

if __name__ == '__main__':

    # This worked perfectly to create the Label that sizes and scrolls in the window.

    from kivy.app import App
    from kivy.uix.label import Label
    from kivy.uix.scrollview import ScrollView


    # Create parser instance
    parser = MarkdownToBBCodeParser()
    bbcode = parser.parse(sample)

    print(f"BBCODE:\n{bbcode}")

    class HelloWorldApp(App):

        def build(self):
            # Set window background to light color
            from kivy.core.window import Window
            Window.clearcolor = (0.9, 0.9, 0.9, 1)  # Light gray background (R, G, B, A)

            label = Label(
                text=bbcode,
                markup=True,       # Enable markup processing
                font_size='13sp',  # Slightly smaller for readability
                halign='left',     # Left align for better readability
                valign='top',      # Align to top for scrolling
                color=(0, 0, 0, 1), # Black text color (R, G, B, A)
                text_size=(400, None),  # Initial width, height auto
                size_hint_y=None    # Don't use size hints for height
            )
        
            # Bind texture size to actual size so ScrollView knows the content height
            label.bind(texture_size=label.setter('size'))
        
            # Create ScrollView and add the label
            scroll = ScrollView(
                do_scroll_x=False,  # Disable horizontal scrolling
                do_scroll_y=True    # Enable vertical scrolling
            )
            scroll.add_widget(label)
        
            # Function to update label width when scroll view width changes
            def update_label_width(instance, value):
                label.text_size = (value, None)
            
            # Bind scroll view width to label text_size width
            scroll.bind(width=update_label_width)
        
            return scroll

    HelloWorldApp().run()
    
    
