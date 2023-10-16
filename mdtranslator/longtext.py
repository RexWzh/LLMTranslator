import os
from chattool import Chat, process_chats, async_chat_completion, load_chats
from typing import Callable, Union
from .process_files import (
    _translate_file, _translate_folder,
    _async_translate_file, _async_translate_folder
)

# write tools
count_token = lambda txt:Chat(txt).prompt_token()
def splittext(text:str, lowerbound:int=800):
    """Split text into slices with the number of tokens less than lowerbound.
    
    Args:
        text (str): text
        lowerbound (int): lowerbound of tokens
    Returns:
        slices (list): list of slices
    """
    slices = [""]
    for line in text.split('\n'):
        slices[-1] += line + '\n'
        if count_token(slices[-1]) >= lowerbound:
            slices.append("")
    if not slices[-1]:slices.pop()
    return slices

# process files
def process_long_text( text:str
                     , chkpoint:str
                     , lowerbound:int=300
                     , msg2chat:Union[Callable[[str], Chat], None]=None):
    """Process long text.
    
    Args:
        text (str): text to process
        chkpoint (str): checkpoint
        lowerbound (int): lowerbound of the number of tokens in each slice
        msg2chat (Callable[[str], Chat]): function to convert message to chat
    Returns:
        str: translated text
    """
    # split text into slices
    slices = splittext(text, lowerbound)
    # process each size
    chats = process_chats(slices, msg2chat, chkpoint)
    # combine the chat log
    return '\n'.join(chat.last_message for chat in chats)

def translate_file(source, target, chkpoint, **kwargs):
    """Translate file.
    
    Args:
        source (str): source file
        target (str): target file
        chkpoint (str): checkpoint
        lowerbound (int): lowerbound of the number of tokens in each slice
        msg2chat (Callable[[str], Chat]): function to convert message to chat
    """
    _translate_file(process_long_text, source, target, chkpoint, **kwargs)

def translate_folder( source:str
                    , target:str
                    , chkpoint_path:str
                    , checkpoint_prefix:str=""
                    , ext:str='.md'
                    , skipexist:bool=True
                    , subpath:bool=True
                    , display:bool=True
                    , **kwargs):
    """Translate folder.

    Args:
        source (str): source folder
        target (str): target folder
        chkpoint_path (str): checkpoint folder
        checkpoint_prefix (str): checkpoint prefix
        ext (str): extension
        skipexist (bool): whether to skip existing files
        subpath (bool): whether to scan subpath
        display (bool): whether to display
    """
    _translate_folder( translate_file
                     , source, target, chkpoint_path
                     , checkpoint_prefix, ext, skipexist
                     , subpath, display, **kwargs)

## async version
async def async_process_long_text( text:str
                                 , chkpoint:str
                                 , lowerbound:int=300
                                 , **kwargs):
    """Process long text asynchronously.
    
    Args:
        text (str): text to process
        chkpoint (str): checkpoint
        lowerbound (int): lowerbound of the number of tokens in each slice
        ncoroutines (int): number of coroutines
        msg2log (Callable): function to convert message to log
        max_tokens (Callable): function to get max tokens
        max_requests (int): maximum number of requests to make
        clearfile (bool): whether to clear the checkpoint file

    Returns:
        str: translated text
    """
    # split text into slices
    slices = splittext(text, lowerbound)
    # process each size
    kwargs['notrun'] = True
    await async_chat_completion(slices, chkpoint, **kwargs)
    chats = load_chats(chkpoint, withid=True)
    # combine the chat log
    return '\n'.join(chat.last_message for chat in chats)

async def async_translate_file( source, target, chkpoint, **kwargs):
    """Translate file asynchronously.
    
    Args:
        source (str): source file
        target (str): target file
        chkpoint (str): checkpoint
        lowerbound (int): lowerbound of the number of tokens in each slice
        msg2log (Callable): function to convert message to log
        max_tokens (Callable): function to get max tokens
        max_requests (int): maximum number of requests to make
    """
    await _async_translate_file( async_process_long_text
                               , source, target, chkpoint, **kwargs)

async def async_translate_folder( source:str
                                , target:str
                                , chkpoint_path:str
                                , checkpoint_prefix:str=""
                                , ext:str='.md'
                                , skipexist:bool=True
                                , subpath:bool=True
                                , display:bool=True
                                , **kwargs):
    """Translate folder asynchronously.

    Args:
        source (str): source folder
        target (str): target folder
        chkpoint_path (str): checkpoint folder
        checkpoint_prefix (str): checkpoint prefix
        ext (str): extension
        msg2log (Callable): function to convert message to log
        max_tokens (Callable): function to get max tokens
        max_requests (int): maximum number of requests to make
        skipexist (bool): whether to skip existing files
        subpath (bool): whether to scan subpath
        display (bool): whether to display
    """
    await _async_translate_folder( async_translate_file
                                 , source, target, chkpoint_path
                                 , checkpoint_prefix, ext, skipexist
                                 , subpath, display, **kwargs)