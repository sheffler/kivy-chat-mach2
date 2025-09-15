# Processors

A processor receives message content, and the role for which the content is for, and optionally produces a Kivy Markup version of the content.

There are two initial processors.  It is envisioned that other processors may be created that translate LLM out into Kivy Markup in other ways, perhaps using ad-hoc methods.

**Plain:**

The plain processor performs no markup processing.

**Mistune:**

The mistune processor uses Mistune to process the entire response as a Markdown document.  It uses the Kivy BBcode renderer that is part of this project.  It also recognizes code fences and formats them with Pygments.
