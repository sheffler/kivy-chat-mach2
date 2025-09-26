#
# Kivy based chat application for NLIP project
#  sends and receives text messages with an optional image too
#
# For standalone development, use the '-m' flag for the MOCK server.
#


from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.core.clipboard import Clipboard
from kivy.uix.widget import Widget
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, BooleanProperty, ObjectProperty
from kivy.metrics import sp
import random
import os
import asyncio
import webbrowser

# local
from . import utils
from .models import Message, Roles
from .widgets.text_input_with_shift_return import TextInputWithShiftReturn
from .services import MockChatBotService, NlipChatBotService, MessageService

# UI Components
class MessageBubble(BoxLayout):
    """UI Component: Visual representation of a message"""
    message_text = StringProperty("")
    message_formatted = StringProperty(None) # default value
    message_type = StringProperty("text")
    image_source = StringProperty("")
    role = StringProperty(Roles.USER)
    
    def __init__(self, message: Message, **kwargs):
        self.message_text = message.content
        if message.formatted:
            self.message_formatted = message.formatted
        self.message_type = message.message_type
        self.image_source = message.image_path or ""
        self.role = message.role
        super().__init__(**kwargs)
        self._setup_bubble()

        # remove the 'copy' button for non-assistant messages
        if message.role != 'assistant':
            copy = self.ids.click_to_copy
            copy.parent.remove_widget(copy)
            

    # Left spacer properties
    def left_size_hint_x(self):
        if self.role == Roles.USER:
            return 0.3
        elif self.role == Roles.ASSISTANT:
            return 0
        elif self.role == Roles.SYSTEM:
            return 0.25
        elif self.role == Roles.STATUS:
            return 0.25
        elif self.role == Roles.WARNING:
            return 0.25
        else:
            return 0.15

    def left_width(self):
        return self.left_size_hint_x()

    # Right space properties
    def right_size_hint_x(self):
        if self.role == Roles.USER:
            return 0
        elif self.role == Roles.ASSISTANT:
            return 0.3
        elif self.role == Roles.SYSTEM:
            return 0.25
        elif self.role == Roles.STATUS:
            return 0.25
        elif self.role == Roles.WARNING:
            return 0.25
        else:
            return 0.15

    def right_width(self):
        return self.right_size_hint_x()

    # Message
    def message_size_hint_x(self):
        if self.role == Roles.USER:
            return 0.7
        elif self.role == Roles.ASSISTANT:
            return 0.7
        elif self.role == Roles.SYSTEM:
            return 0.5
        elif self.role == Roles.STATUS:
            return 0.5
        elif self.role == Roles.WARNING:
            return 0.5
        else:
            return 0.7

    # Bubble color
    def bubble_color(self):
        if self.role == Roles.USER:
            return (0.85, 0.92, 1, 1)
        elif self.role == Roles.ASSISTANT:
            return (0.95, 0.95, 0.95, 1)
        elif self.role == Roles.SYSTEM:
            return (0.85, 0.95, 0.85, 1)
        elif self.role == Roles.STATUS:
            return (0.85, 0.95, 0.85, 1)
        elif self.role == Roles.WARNING:
            return (0.95, 0.85, 0.85, 1)
        else:
            return (0.85, 0.85, 0.85, 1)

    def bubble_halign(self):
        if self.role == Roles.USER:
            return "right"
        elif self.role == Roles.ASSISTANT:
            return "left"
        elif self.role == Roles.SYSTEM:
            return "center"
        elif self.role == Roles.STATUS:
            return "center"
        elif self.role == Roles.WARNING:
            return "center"
        else:
            return "center"

    
    
    def _setup_bubble(self):
        """Configure the message bubble appearance and behavior"""
        if self.message_type == "text":
            self._setup_text_message()
        elif self.message_type == "image":
            self._setup_image_message()
    
    def _setup_text_message(self):
        """Configure text message bubble"""
        message_label = self.ids.message_label
        
        def update_text_size(instance, *args):
            # TOM:
            # instance.text_size = (300, None)
            instance.text_size = (instance.width, None)
            instance.texture_update()
            container = self.ids.message_container
            padding_height = self.padding[1] + self.padding[3] if hasattr(self, 'padding') else 20
            status_height = sp(20)
            container.height = max(instance.texture_size[1] + padding_height + status_height, sp(40))
        
        message_label.bind(size=update_text_size)
        Clock.schedule_once(lambda dt: update_text_size(message_label), 0.1)
    
# TOM: replace with dynamic size calculations
#    def _setup_image_message(self):
#        """Configure image message bubble"""
#        container = self.ids.message_container
#        container.height = sp(200)

    def _setup_image_message(self):
        """Configure image message bubble"""
        message_label = self.ids.message_label
        
        def update_text_size(instance, *args):
            # instance.text_size = (300, None)  # Fixed max width
            instance.text_size = (instance.width, None)  # Fixed max width
            instance.texture_update()
            # Update container height based on text (fixed as per your requirements)
            container = self.ids.message_container
            padding_height = self.padding[1] + self.padding[3] if hasattr(self, 'padding') else 20
            status_height = sp(20)
            container.height = max(instance.texture_size[1] + padding_height + status_height + sp(150), sp(40))
        
        message_label.bind(size=update_text_size)
        Clock.schedule_once(lambda dt: update_text_size(message_label), 0.1)

    def on_copy_pressed(self, instance):
        Clipboard.copy(self.message_text)

    def on_link_press(self, instance, url:str):
        webbrowser.open(url)
        
class ChatHistory(ScrollView):
    """UI Component: Container for message history"""
    message_service = ObjectProperty(allownone=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._is_subscribed = False
    
    def on_message_service(self, instance, message_service):
        """Called when message_service property is set (property injection)"""
        if message_service and not self._is_subscribed:
            # Subscribe to message service events
            message_service.add_observer(self._on_new_message)
            self._is_subscribed = True
            # Load any existing messages
            self.load_existing_messages()
    
    def _on_new_message(self, message: Message):
        """Handle new message from service"""
        message_bubble = MessageBubble(message)
        self.ids.messages_layout.add_widget(message_bubble)
        # Auto-scroll to bottom
        Clock.schedule_once(lambda dt: setattr(self, 'scroll_y', 0), 0.1)
    
    def load_existing_messages(self):
        """Load any existing messages from the service"""
        if self.message_service:
            for message in self.message_service.get_all_messages():
                self._on_new_message(message)


class UrlInput(BoxLayout):
    """UI Component: Input area for composing messages"""
    chatbot_service = ObjectProperty(allownone=True)
    message_service = ObjectProperty(allownone=True)
    
    def on_enter_pressed(self, instance):
        """Handle Enter key press"""
        print(f"Connect to Server")
        if not instance.text.strip():
            return

        async def doit():
            instance.text = instance.text.strip()
            # await self.chatbot_service.connect_to_server(instance.text)
            try:
                await self.chatbot_service.connect_to_server(instance.text)
                self.message_service.create_text_message(f"Connected to {instance.text}", role=Roles.STATUS)
            except Exception as e:
                self.message_service.create_text_message(f"Exception: {e}", role=Roles.WARNING)

        asyncio.create_task(doit())

class MessageInput(BoxLayout):
    """UI Component: Input area for composing messages"""
    on_send_callback = ObjectProperty(allownone=True)
    on_image_callback = ObjectProperty(allownone=True)

    def on_enter_pressed(self, instance):
        """Handle Enter key press"""
        if not instance.text.strip():
            return
        self.send_message()
    
    def send_message(self, *args):
        """Send the current message"""
        text_input = self.ids.text_input
        message_text = text_input.text.strip()
        if message_text and self.on_send_callback:
            self.on_send_callback(message_text)
            text_input.text = ''
    
    def open_image_chooser(self, *args):
        """Open file chooser for image selection"""
        if self.on_image_callback:
            self.on_image_callback()

    # TOM: adding this to cut the text
    def cut_message(self, *args):
        """Remove the message to send with image"""
        text_input = self.ids.text_input
        message_text = text_input.text.strip()
        text_input.text = ''
        return message_text

class ImageChooserPopup(Popup):
    """UI Component: File chooser popup for selecting images"""
    on_image_selected = ObjectProperty(allownone=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Select an Image"
        self.size_hint = (0.9, 0.9)
        
        layout = BoxLayout(orientation='vertical', spacing='10sp', padding='10sp')
        
        self.file_chooser = FileChooserIconView(
            filters=['*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp'],
            path=os.path.expanduser('~')
        )
        
        button_layout = BoxLayout(size_hint_y=None, height='40sp', spacing='10sp')
        
        cancel_btn = Button(text='Cancel', size_hint_x=0.5)
        cancel_btn.bind(on_press=self.dismiss)
        
        select_btn = Button(text='Select', size_hint_x=0.5)
        select_btn.bind(on_press=self.select_image)
        
        button_layout.add_widget(cancel_btn)
        button_layout.add_widget(select_btn)
        
        layout.add_widget(self.file_chooser)
        layout.add_widget(button_layout)
        
        self.content = layout
    
    def select_image(self, *args):
        """Handle image selection"""
        if self.file_chooser.selection:
            selected_file = self.file_chooser.selection[0]
            if self.on_image_selected:
                self.on_image_selected(selected_file)
            self.dismiss()


class ChatInterface(BoxLayout):
    """Main Controller: Orchestrates services and UI components"""
    
    def __init__(self, cmdargs, **kwargs):
        # Initialize services BEFORE calling super() so they're available during KV loading
        self.cmdargs = cmdargs # argparse instance

        if self.cmdargs.plain:
            self.message_service = MessageService(processor_name='plain')
        else:
            self.message_service = MessageService(processor_name='mistune')

        if self.cmdargs.mock:
            self.chatbot_service = MockChatBotService()
        else:
            self.chatbot_service = NlipChatBotService()
        super().__init__(**kwargs)

    def on_kv_post(self, base_widget):
        """Called after the kv file is loaded"""
        # Inject message service dependency into chat history
        self.ids.chat_history.message_service = self.message_service

        # Inject chatbotservice into the url input
        self.ids.url_input.chatbot_service = self.chatbot_service
        self.ids.url_input.message_service = self.message_service
        
        # Set up message input callbacks
        self.ids.message_input.on_send_callback = self.handle_send_message
        self.ids.message_input.on_image_callback = self.handle_image_upload
        
        # Add sample messages
        self._add_welcome_messages()
        if self.cmdargs.mock:
            self._add_sample_messages()
    
    def handle_send_message(self, message_text: str):
        """Handle sending a new text message"""
        # Create user message through service
        user_message = self.message_service.create_text_message(message_text, role=Roles.USER)

        async def doit():
            response_text , image_path = await self.chatbot_service.generate_response(user_message)
            if image_path == None:
                self.message_service.create_text_message(response_text, role=Roles.ASSISTANT)
            else:
                self.message_service.create_image_message(response_text, image_path, role=Roles.ASSISTANT)

        asyncio.create_task(doit())
        
    
    def handle_image_upload(self, *args):
        """Handle image upload request"""
        popup = ImageChooserPopup()
        popup.on_image_selected = self.on_image_selected
        popup.open()
    
    def on_image_selected(self, image_path: str):
        """Handle when an image is selected"""
        filename = os.path.basename(image_path)
        default_content = f"Shared an image: {filename}"
        explicit_content = self.ids.message_input.cut_message()
        user_message = self.message_service.create_image_message(
            content= default_content if len(explicit_content) == 0 else explicit_content,
            image_path=image_path,
            role=Roles.USER
        )

        async def doit():
            response_text, image_path = await self.chatbot_service.generate_response(user_message)
            if image_path == None:
                self.message_service.create_text_message(response_text, role=Roles.ASSISTANT)
            else:
                self.message_service.create_image_message(response_text, image_path, role=Roles.ASSISTANT)
        
        asyncio.create_task(doit())

    
    def _generate_bot_response(self, user_message: Message):
        """Generate and send bot response"""
        response_text = self.chatbot_service.generate_response(user_message)
        self.message_service.create_text_message(response_text, role=Roles.ASSISTANT)
    
    def _add_welcome_messages(self):
        """Add sample messages to demonstrate the interface"""

        sample_data = [
            ("Hello! Welcome to the chat interface.", "text", None, Roles.ASSISTANT),
        ]
        
        for content, msg_type, img_path, role in sample_data:
            if msg_type == "text":
                self.message_service.create_text_message(content, role)
            elif msg_type == "image":
                self.message_service.create_image_message(content, img_path, role)

    def _add_sample_messages(self):
        """Add sample messages to demonstrate the interface"""

        multiline = """The Weather Agent has provided the forecast for Juneau, Alaska:

**Today:**
- Temperature: 57°F
- Wind: 10 to 15 mph from Southeast
- Conditions: Rainy and cloudy
- Precipitation: 90% chance with rainfall between 0.1-0.25 inches

**Tonight:**
- Temperature: Low around 50°F
- Wind: 10 to 15 mph from East
- Conditions: Rainy and cloudy
- Precipitation: 100% chance with rainfall between 0.5-0.75 inches

**Tuesday:**
- Temperature: High near 62°F
- Wind: 5 to 15 mph from East
- Conditions: Rainy and cloudy
- Precipitation: 100% chance with rainfall between 0.5-0.75 inches
"""
        multilinejson = """**Person:**
``` json
{
  "name":"Fred",
  "id": 1
}
```

**Place:**
``` json
{
  "location":"Madrid",
  "id": 45
}
```"""
        
        sample_data = [
            ("Connected to http://sample.com/", "text", None, Roles.STATUS),
            ("Hi there! This looks great.", "text", None, Roles.USER),
            ("This is a longer message to demonstrate how the text wrapping works in the message bubbles. As you can see, it automatically adjusts the height based on the content length.", "text", None, Roles.ASSISTANT),
            ("Perfect! The bubbles resize nicely and the text is easy to read.", "text", None, Roles.USER),
            ("What is the forecast for Juneau?", "text", None, Roles.USER),
            (multiline, "text", None, Roles.ASSISTANT),
            ("What are the Domain Objects?", "text", None, Roles.USER),
            (multilinejson, "text", None, Roles.ASSISTANT),
        ]
        
        for content, msg_type, img_path, role in sample_data:
            if msg_type == "text":
                self.message_service.create_text_message(content, role)
            elif msg_type == "image":
                self.message_service.create_image_message(content, img_path, role)

class ChatApp(App):
    """Application entry point"""

    def __init__(self, cmdargs, **kwargs):
        super().__init__(**kwargs)
        self.title = "Mach2" # the window title
        self.cmdargs = cmdargs
    
    def build(self):
        return ChatInterface(self.cmdargs)
    
    def on_start(self):
        from kivy.core.window import Window
        Window.clearcolor = (1, 1, 1, 1)

    
