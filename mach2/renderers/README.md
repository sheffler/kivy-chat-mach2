# Renderers

Modules in this directory attempt to format markdown and code into Kivy markup format.  For code formatting with Pygments, this works pretty well.  Pygments has a `bbcode` formatter that is very close to Kivy markup.  For rendering Markdown, translating into Kivy gives some nice results for Heading styles, and inline Bold and Italics.  For elements that require block rendering, a more sophisticated approach would be needed.

Kivy markup does not do layout, only text formatting.

- Nested lists are handled by indenting the first line of the list.  Is ok when the elements of a list are short sentences.
- Tables are not recognized.  Handling them would require a more sophisticated approach.
- Code fences are recognized and are passed to Pygments for formatting.


## Description of Modules Here

**kivy_mistune_bbcode:**

Mistune is a Markdown parser and formatter.  We implemented a very simple Kivy markup emitter for some basic Markdown elements.

Fixed-Width font selection for code assumes that font `RobotoMono-Regular` is present in the Kivy installation.


**kivy_pygments_bbcode:**

Pygments is a code formatter.  It includes a BBCode formatter, which is very close to what Kivy expects as markup.  We needed to override one method to escape left-brackets appropriately.

