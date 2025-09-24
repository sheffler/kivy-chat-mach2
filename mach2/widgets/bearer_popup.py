from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget

class BearerCredentials:
    """Domain model for bearer credentials"""
    def __init__(self, bearer: str = ""):
        self.bearer = bearer
    
    def is_valid(self) -> bool:
        """Basic validation - both fields must be non-empty"""
        return bool(self.bearer.strip())
    
    def __str__(self):
        return f"BearerCredentials(bearer='{self.username}')"


class BearerPopup(Popup):
    """Popup widget for collecting bearer credentials"""
    
    def __init__(self, on_bearer_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.on_bearer_callback = on_bearer_callback
        self.credentials = BearerCredentials()
        
        # Configure popup properties
        self.title = "Bearer Token Required"
        self.size_hint = (0.7, 0.5)
        self.auto_dismiss = False  # Prevent closing by clicking outside
        
        # Build the UI
        self._build_content()
    
    def _build_content(self):
        """Construct the popup's content layout"""
        # Main container
        main_layout = BoxLayout(
            orientation='vertical',
            padding=20,
            spacing=15
        )
        
        # Form container
        form_layout = GridLayout(
            cols=2,
            spacing=10,
            size_hint_y=0.7
        )
        
        # Bearer field
        form_layout.add_widget(Label(
            text='Bearer:',
            text_size=(None, None),
            halign='right',
            size_hint_x=0.3,
            # TOM:
            size_hint_y=None,
            height='25sp',
        ))
        
        self.bearer_input = TextInput(
            multiline=False,
            size_hint_x=0.7,
            # TOM:
            size_hint_y=None,
            height='25sp',
            write_tab=False,
        )
        self.bearer_input.bind(text=self._on_bearer_change)
        form_layout.add_widget(self.bearer_input)
        
        # Button container
        button_layout = BoxLayout(
            orientation='horizontal',
            spacing=10,
            size_hint_y=0.3
        )
        
        # Cancel button
        cancel_btn = Button(
            text='Cancel',
            size_hint_x=0.5
        )
        cancel_btn.bind(on_press=self._on_cancel)
        button_layout.add_widget(cancel_btn)
        
        # Login button
        self.login_btn = Button(
            text='Login',
            size_hint_x=0.5,
            disabled=True,  # Initially disabled
        )
        self.login_btn.bind(on_press=self._on_login)
        button_layout.add_widget(self.login_btn)
        
        # Assemble layout
        main_layout.add_widget(form_layout)
        main_layout.add_widget(button_layout)
        
        self.content = main_layout
        
        # Focus username field when popup opens
        self.bind(on_open=self._on_popup_open)
    
    def _on_popup_open(self, instance):
        """Focus the username field when popup opens"""
        self.bearer_input.focus = True
    
    def _on_bearer_change(self, instance, value):
        """Handle username input changes"""
        self.credentials.bearer = value
        self._update_login_button_state()
    
    def _update_login_button_state(self):
        """Enable/disable login button based on credential validity"""
        self.login_btn.disabled = not self.credentials.is_valid()
    
    def _on_cancel(self, instance):
        """Handle cancel button press"""
        self.dismiss()
    
    def _on_login(self, instance):
        """Handle login button press"""
        if self.credentials.is_valid():
            if self.on_bearer_callback:
                self.on_bearer_callback(self.credentials)
            self.dismiss()


#
# Standalone components testing.  Run this like
#   python -m mach2.widgets.login_popup
#


class BearerService:
    """Service for handling bearer operations"""
    
    @staticmethod
    def authenticate(credentials: BearerCredentials) -> bool:
        """
        Authenticate the provided credentials.
        In a real app, this would validate against a database or API.
        """
        # Demo implementation - accept any non-empty credentials
        return credentials.is_valid()


class MainApp(App):
    """Main application demonstrating the bearer popup"""
    
    def build(self):
        # Simple main layout with a button to show bearer
        layout = BoxLayout(
            orientation='vertical',
            padding=50,
            spacing=20
        )
        
        info_label = Label(
            text='Click the button below to show the bearer popup',
            size_hint_y=0.3
        )
        
        show_bearer_btn = Button(
            text='Show Bearer Popup',
            size_hint=(0.5, 0.3),
            pos_hint={'center_x': 0.5}
        )
        show_bearer_btn.bind(on_press=self._show_bearer_popup)
        
        self.result_label = Label(
            text='No bearer attempts yet',
            size_hint_y=0.4
        )
        
        layout.add_widget(info_label)
        layout.add_widget(show_bearer_btn)
        layout.add_widget(self.result_label)
        
        return layout
    
    def _show_bearer_popup(self, instance):
        """Show the bearer popup"""
        popup = BearerPopup(on_bearer_callback=self._handle_bearer_result)
        popup.open()
    
    def _handle_bearer_result(self, credentials: BearerCredentials):
        """Handle the bearer result"""
        if BearerService.authenticate(credentials):
            self.result_label.text = f'✓ Bearer successful!\nWelcome, {credentials.bearer}!'
        else:
            self.result_label.text = '✗ Bearer failed!'


if __name__ == '__main__':
    MainApp().run()
    
