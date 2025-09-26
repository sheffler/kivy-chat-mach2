import os
import asyncio
from typing import List, Callable, Optional

# import NLIP
from nlip_sdk.nlip import NLIP_Factory
from urllib.parse import urlparse

# local
from . import utils
from .models import Message
from .nlip_async_client import NlipAsyncClient
from .authenticating_nlip_async_client import AuthenticatingNlipAsyncClient
from .processors.plain_processor import PlainProcessor
from .processors.mistune_processor import MistuneProcessor

# login popup
from .widgets.login_popup import LoginPopup, LoginCredentials
from .widgets.bearer_popup import BearerPopup, BearerCredentials

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
        parsed_url = urlparse(url)
        scheme = parsed_url.scheme
        netloc = parsed_url.netloc

        # Establish the URL and return a connection message
        await asyncio.sleep(1.0)
        # self.client = NlipAsyncClient.create_from_url(f"{scheme}://{netloc}/nlip/")   
        self.client = AuthenticatingNlipAsyncClient.create_from_url(f"{scheme}://{netloc}/nlip/")   
        return f"Connected to {scheme}://{netloc}/"
                
    
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

def on_login_elicitation(client):

    print(f"SERVICES: ON_BASIC_ELICIATION:{client}")

    from asyncio import Future
    future = Future()

    def handle_login_result(credentials: LoginCredentials):
        username = credentials.username
        password = credentials.password
        future.set_result((username, password))

    popup = LoginPopup(on_login_callback=handle_login_result)
    popup.open()

    return future

def on_bearer_elicitation(client):

    print(f"SERVICES: ON_BEARER_ELICIATION:{client}")

    from asyncio import Future
    future = Future()

    def handle_bearer_result(credentials: BearerCredentials):
        bearer = credentials.bearer
        future.set_result(bearer)

    popup = BearerPopup(on_bearer_callback=handle_bearer_result)
    popup.open()

    return future



class NlipChatBotService:
    """Service: Handles chatbot response generation"""
    
    def __init__(self):
        self.client = None
        
    #
    # Make a connection and return a status string
    #
    
    async def connect_to_server(self, url):
        """Connect to the server and return a message"""
        parsed_url = urlparse(url)
        print(f"PARSED:{parsed_url}")
        scheme = parsed_url.scheme
        netloc = parsed_url.netloc

        # Establish the URL and return a connection message
        await asyncio.sleep(1.0)
        # self.client = NlipAsyncClient.create_from_url(f"{scheme}://{netloc}/nlip/")   
        self.client = AuthenticatingNlipAsyncClient.create_from_url(f"{scheme}://{netloc}/nlip/")
        # register credential callbacks
        self.client.on_login_requested(on_login_elicitation)
        self.client.on_bearer_requested(on_bearer_elicitation)
        return f"Connected to {scheme}://{netloc}/"

    def error_connection_response(self):
        msg = f"[b]No connection to server[/b].\nPlease enter http://hostname:port/ information"
        return msg
                
    
    async def generate_response(self, user_message: Message) -> (str, Optional[str]):

        # make sure the client is created
        if (self.client is None):
            msg = self.error_connection_response()
            return (msg, None)
        
        nlip_message = utils.messageToNlipMessage(user_message)

        resp = None
        try:
            resp = await self.client.async_send(nlip_message)
        except Exception as e:
            err = f"Error:{e}"

        if resp:
            (content, image_path) = utils.nlipMessageExtractParts(resp)
        else:
            # TODO: use NLIP Parts more effectively to signify errors
            content = err
            image_path = None

        return (content, image_path)

# Services
class MessageService:
    """Service: Manages message operations and state"""
    
    def __init__(self, processor_name: str):
        self._messages: List[Message] = []
        self._message_counter = 0
        self._observers: List[Callable[[Message], None]] = []

        if processor_name == 'plain':
            self.processor = PlainProcessor()
        else:
            self.processor = MistuneProcessor()
    
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

        formatted = self.processor.process(content, role)

        message = Message(
            id=f"msg_{self._message_counter}",
            content=content,
            formatted=formatted,
            message_type="text",
            role=role
        )
        self._messages.append(message)
        self._notify_observers(message)
        return message
    
    def create_image_message(self, content: str, image_path: str, role: str = "user") -> Message:
        """Create a new image message"""
        self._message_counter += 1

        formatted = self.processor.process(content, role)

        message = Message(
            id=f"msg_{self._message_counter}",
            content=content,
            formatted=formatted,
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


