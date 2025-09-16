#
# Utilities for converting message types
#

from .models import Message
from nlip_sdk.nlip import NLIP_Message, NLIP_Factory
from nlip_sdk.nlip import AllowedFormats

import os
import tempfile
from base64 import b64encode, b64decode

def messageToNlipMessage(message: Message):

    # every message has text content
    content = message.content
    nlip_message = NLIP_Factory.create_text(content=content)
    

    if message.message_type == "image":
        image_path = message.image_path
        root, extension = os.path.splitext(image_path)
        basename = os.path.basename(image_path) # remove directory part and use as label
        extension = extension.replace(".", "") # remove any period

        fp = open(image_path, "rb")
        data = fp.read()
        fp.close()

        b64content=b64encode(data).decode("utf-8")
        nlip_message.add_binary(b64content, "image", extension, label=basename)

    return nlip_message

#
# Find a submessage with an image and store to an image path or return None
#

def nlipMessageExtractImagePath(nlip_message: NLIP_Message):

    temp_file_path = None

    if hasattr(nlip_message, 'submessages'):
        if (nlip_message.submessages is not None):
            for submsg in nlip_message.submessages:
                subformat = submsg.subformat

                # subformat="image/{encoding}
                if (subformat.startswith("image")):

                    # is assumed base64 encoded string                    
                    content = submsg.content
                    kind, encoding = subformat.split("/")

                    # base64 decode it
                    data = b64decode(content.encode('utf-8'))

                    # write it to a temp file
                    tf = tempfile.NamedTemporaryFile(suffix=encoding, mode='wb', delete=False)
                    tf.write(data)
                    tf.close()
                    temp_file_path = tf.name

                    break
    return temp_file_path
                

#
# Find text content in primary message and the first attached image.  Return
# a local file path for the saved image that can be used with Kivy.
#
# Apply simple Kivy formatting for special message parts.
#
# Our NLIP Agents format some parts in special ways.
#   - tool calls begin with: "[Calling ..."
#

def nlipMessageExtractParts(nlip_message: NLIP_Message):

    # find the text parts in the message and join
    if nlip_message.format == AllowedFormats.text:
        content = nlip_message.content # the main part
    else:
        content = ""

    if nlip_message.submessages:
        for msg in nlip_message.submessages: # sub-parts
            if msg.format == AllowedFormats.text:
                s = msg.content
                # Apply formatting to tools by recognizing basic_agent
                if s.startswith("Calling tool"):
                    content += f"\n\n**{s}**"
                else:
                    content += f"\n\n{s}"

    image_path = nlipMessageExtractImagePath(nlip_message)

    return (content, image_path)
