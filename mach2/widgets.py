#
# A special TextInput that handles SHIFT-RETURN.  Normally a multiline TextInput
# enters a newline for RETURN.  This variant intercepts SHIFT-RETURN to send the message.
#

from kivy.uix.textinput import TextInput

class TextInputWithShiftReturn(TextInput):
    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        # Check if SHIFT is pressed and the key is RETURN
        if 'shift' in modifiers and keycode[1] == 'enter':
            self.dispatch('on_text_validate')
            return True  # Consume the event
        # If not SHIFT-RETURN, let the default TextInput behavior handle it
        return super().keyboard_on_key_down(window, keycode, text, modifiers)


