#
# Kivy based chat application for NLIP project
#  sends and receives text messages with an optional image too
#
# For standalone development, set USE_MOCKS_ERVER=True to use mock server with canned responses
#


USE_MOCK_SERVER = False


from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.widget import Widget
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, BooleanProperty, ObjectProperty
from kivy.metrics import sp
from dataclasses import dataclass
from datetime import datetime
from typing import List, Callable, Optional
import random
import os
import asyncio

# local
import utils

# import NLIP
from nlip_client.nlip_client import NLIP_HTTPX_Client
from nlip_sdk.nlip import NLIP_Factory
from urllib.parse import urlparse

# Domain Models
@dataclass
class Message:
    """Domain entity: Represents a chat message"""
    id: str
    content: str
    message_type: str  # "text" or "image"
    image_path: Optional[str] = None
    role: str = "user" # user, assistant, system, status
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

#
# Mock Chat Bot Service delivers canned responses.
#

class MockChatBotService:
    """Service: Handles chatbot response generation"""
    
    def __init__(self):
        self.client = None
        
        self._text_responses = [
            "Thanks for your message!",
            "That's interesting. Tell me more.",
            "I understand what you're saying.",
            "Let me think about that for a moment...",
            "That's a great point!",
            "I see what you mean.",
            "Could you elaborate on that?",
            "That makes sense to me."
        ]
        
        self._image_responses = [
            "Nice image! Thanks for sharing.",
            "That's a great photo!",
            "I can see the image you shared.",
            "Interesting picture!",
            "Thanks for the visual!",
            "What a lovely image!",
            "Great shot!",
            "Beautiful picture!"
        ]

    #
    # Make a connection and return a status string
    #
    
    async def connect_to_server(self, url):
        """Connect to the server and return a message"""
        try:
            parsed_url = urlparse(url)
            host = parsed_url.hostname
            port = parsed_url.port
        except Exception as e:
            instance.text = f"Exception: {e}"
            return

        # Establish the URL and return a connection message
        await asyncio.sleep(1.0)
        self.client = NLIP_HTTPX_Client.create_from_url(f"http://{host}:{port}/nlip/")   
        return f"Connected to http://{host}:{port}/"
                
    
    def generate_response_to_text(self, user_message: Message) -> str:
        """Generate a response to a text message"""
        # Simple keyword-based responses (could be replaced with AI)
        content_lower = user_message.content.lower()
        
        if "hello" in content_lower or "hi" in content_lower:
            return "Hello! How are you doing today?"
        elif "how" in content_lower and "you" in content_lower:
            return "I'm doing well, thank you for asking!"
        elif "thank" in content_lower:
            return "You're very welcome!"
        elif "?" in user_message.content:
            return "That's a great question! Let me think about that."
        else:
            return random.choice(self._text_responses)
    
    def generate_response_to_image(self, user_message: Message) -> str:
        """Generate a response to an image message"""
        filename = os.path.basename(user_message.image_path) if user_message.image_path else ""
        file_ext = filename.split('.')[-1].lower() if '.' in filename else ""
        
        if file_ext in ['jpg', 'jpeg']:
            return "Nice JPEG image! The quality looks great."
        elif file_ext == 'png':
            return "PNG format - perfect for clear images!"
        elif file_ext == 'gif':
            return "A GIF! I love animated images."
        else:
            return random.choice(self._image_responses)

    # return text response and None image path
    async def generate_response(self, user_message: Message) -> (str, Optional[str]):
        """Generate appropriate response based on message type"""
        image_path = None
        await asyncio.sleep(1.0)

        if user_message.message_type == "text":
            return (self.generate_response_to_text(user_message), image_path)
        elif user_message.message_type == "image":
            return (self.generate_response_to_image(user_message), image_path)
        else:
            return ("I received your message!", image_path)


#
# NLIP Chat Bot Service sends/receives messages to an NLIP Server.
# Server credentials must be set before use.
#

class NlipChatBotService:
    """Service: Handles chatbot response generation"""
    
    def __init__(self):
        self.client = None
        
    #
    # Make a connection and return a status string
    #
    
    async def connect_to_server(self, url):
        """Connect to the server and return a message"""
        try:
            parsed_url = urlparse(url)
            host = parsed_url.hostname
            port = parsed_url.port
        except Exception as e:
            instance.text = f"Exception: {e}"
            return

        # Establish the URL and return a connection message
        await asyncio.sleep(1.0)
        self.client = NLIP_HTTPX_Client.create_from_url(f"http://{host}:{port}/nlip/")   
        return f"Connected to http://{host}:{port}/"

    def error_connection_response(self):
        msg = f"[b]No connection to server[/b].\nPlease enter http://hostname:port/ information"
        return msg
                
    
    async def generate_response(self, user_message: Message) -> (str, Optional[str]):

        # make sure the client is created
        if (self.client is None):
            msg = self.error_connection_response()
            return (msg, None)
        
        nlip_message = utils.messageToNlipMessage(user_message)
        # print(f"NLIP:{nlip_message}")
        resp = await self.client.async_send(nlip_message)
        # print(f"RESP:{resp}")
        (content, image_path) = utils.nlipMessageExtractParts(resp)
        return (content, image_path)

# Services
class MessageService:
    """Service: Manages message operations and state"""
    
    def __init__(self):
        self._messages: List[Message] = []
        self._message_counter = 0
        self._observers: List[Callable[[Message], None]] = []
    
    def add_observer(self, callback: Callable[[Message], None]):
        """Subscribe to message events"""
        self._observers.append(callback)
    
    def remove_observer(self, callback: Callable[[Message], None]):
        """Unsubscribe from message events"""
        if callback in self._observers:
            self._observers.remove(callback)
    
    def _notify_observers(self, message: Message):
        """Notify all observers of new messages"""
        for observer in self._observers:
            observer(message)
    
    def create_text_message(self, content: str, role:str = "user") -> Message:
        """Create a new text message"""
        self._message_counter += 1
        message = Message(
            id=f"msg_{self._message_counter}",
            content=content,
            message_type="text",
            role=role
        )
        self._messages.append(message)
        self._notify_observers(message)
        return message
    
    def create_image_message(self, content: str, image_path: str, role: str = "user") -> Message:
        """Create a new image message"""
        self._message_counter += 1
        message = Message(
            id=f"msg_{self._message_counter}",
            content=content,
            message_type="image",
            image_path=image_path,
            role=role
        )
        self._messages.append(message)
        self._notify_observers(message)
        return message
    
    def get_all_messages(self) -> List[Message]:
        """Get all messages"""
        return self._messages.copy()
    
    def get_message_by_id(self, message_id: str) -> Optional[Message]:
        """Get a specific message by ID"""
        return next((msg for msg in self._messages if msg.id == message_id), None)
    
    def clear_messages(self):
        """Clear all messages"""
        self._messages.clear()


# UI Components
class MessageBubble(BoxLayout):
    """UI Component: Visual representation of a message"""
    message_text = StringProperty("")
    message_type = StringProperty("text")
    image_source = StringProperty("")
    role = StringProperty("user")
    
    def __init__(self, message: Message, **kwargs):
        self.message_text = message.content
        self.message_type = message.message_type
        self.image_source = message.image_path or ""
        self.role = message.role
        super().__init__(**kwargs)
        self._setup_bubble()

    # Left spacer properties
    def left_size_hint_x(self):
        if self.role == "user":
            return 0.3
        elif self.role == "assistant":
            return 0
        elif self.role == "system":
            return 0.25
        elif self.role == "status":
            return 0.25
        else:
            return 0.15

    def left_width(self):
        return self.left_size_hint_x()

    # Right space properties
    def right_size_hint_x(self):
        if self.role == "user":
            return 0
        elif self.role == "assistant":
            return 0.3
        elif self.role == "system":
            return 0.25
        elif self.role == "status":
            return 0.25
        else:
            return 0.15

    def right_width(self):
        return self.right_size_hint_x()

    # Message
    def message_size_hint_x(self):
        if self.role == "user":
            return 0.7
        elif self.role == "assistant":
            return 0.7
        elif self.role == "system":
            return 0.5
        elif self.role == "status":
            return 0.5
        else:
            return 0.7

    # Bubble color
    def bubble_color(self):
        if self.role == "user":
            return (0.85, 0.92, 1, 1)
        elif self.role == "assistant":
            return (0.95, 0.95, 0.95, 1)
        elif self.role == "system":
            return (0.85, 0.95, 0.85, 1)
        elif self.role == "status":
            return (0.85, 0.95, 0.85, 1)
        else:
            return (0.85, 0.85, 0.85, 1)

    def bubble_halign(self):
        if self.role == "user":
            return "right"
        elif self.role == "assistant":
            return "left"
        elif self.role == "system":
            return "center"
        elif self.role == "status":
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
            container.height = max(instance.texture_size[1] + padding_height, sp(40))
        
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
            container.height = max(instance.texture_size[1] + padding_height + sp(150), sp(40))
        
        message_label.bind(size=update_text_size)
        Clock.schedule_once(lambda dt: update_text_size(message_label), 0.1)

        
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
            await self.chatbot_service.connect_to_server(instance.text)
            self.message_service.create_text_message(f"Connected to {instance.text}", role="status")

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
    
    def __init__(self, **kwargs):
        # Initialize services BEFORE calling super() so they're available during KV loading
        self.message_service = MessageService()
        if USE_MOCK_SERVER:
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
        if USE_MOCK_SERVER:
            self._add_sample_messages()
    
    def handle_send_message(self, message_text: str):
        """Handle sending a new text message"""
        # Create user message through service
        user_message = self.message_service.create_text_message(message_text, role="user")

        async def doit():
            response_text , image_path = await self.chatbot_service.generate_response(user_message)
            if image_path == None:
                self.message_service.create_text_message(response_text, role="assistant")
            else:
                self.message_service.create_image_message(response_text, image_path, role="assistant")

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
            role="user"
        )

        async def doit():
            response_text, image_path = await self.chatbot_service.generate_response(user_message)
            if image_path == None:
                self.message_service.create_text_message(response_text, role="assistant")
            else:
                self.message_service.create_image_message(response_text, image_path, role="assistant")
        
        asyncio.create_task(doit())

    
    def _generate_bot_response(self, user_message: Message):
        """Generate and send bot response"""
        response_text = self.chatbot_service.generate_response(user_message)
        self.message_service.create_text_message(response_text, role="assistant")
    
    def _add_welcome_messages(self):
        """Add sample messages to demonstrate the interface"""
        sample_data = [
            ("Hello! Welcome to the chat interface.", "text", None, "assistant"),
        ]
        
        for content, msg_type, img_path, role in sample_data:
            if msg_type == "text":
                self.message_service.create_text_message(content, role)
            elif msg_type == "image":
                self.message_service.create_image_message(content, img_path, role)

    def _add_sample_messages(self):
        """Add sample messages to demonstrate the interface"""
        sample_data = [
            ("Connected to http://sample.com/", "text", None, "status"),
            ("Hi there! This looks great.", "text", None, "user"),
            ("This is a longer message to demonstrate how the text wrapping works in the message bubbles. As you can see, it automatically adjusts the height based on the content length.", "text", None, "assistant"),
            ("Perfect! The bubbles resize nicely and the text is easy to read.", "text", None, "user"),
        ]
        
        for content, msg_type, img_path, role in sample_data:
            if msg_type == "text":
                self.message_service.create_text_message(content, role)
            elif msg_type == "image":
                self.message_service.create_image_message(content, img_path, role)


class ChatApp(App):
    """Application entry point"""
    
    def build(self):
        return ChatInterface()
    
    def on_start(self):
        from kivy.core.window import Window
        Window.clearcolor = (1, 1, 1, 1)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(ChatApp().async_run(async_lib='asyncio'))
    loop.close()
    
