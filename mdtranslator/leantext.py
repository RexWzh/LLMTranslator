# Translate Lean files

import re, os
from .longtext import splittext
from .mdtext import preprocess_slices, recover_slices
from typing import Callable, Union, List
from chattool import *
from .process_files import (
    _translate_file, _translate_folder,
    _async_translate_file, _async_translate_folder
)

def lean2blocks(leancode, splitline='---SPLITLINE---'):
    # remove the inline sorry
    leancode = leancode.replace("/- inline sorry -/", "")
    # convert comment to plain text
    comments = re.findall(r"/-+ *(.*?) *-+/", leancode, re.S) # get comments
    comments = [comment.strip('\n') for comment in comments]
    codetxt = re.sub(r"/-+ *(.*?) *-+/", splitline, leancode, flags=re.S) # convert comment to special token
    codes = [code.strip() for code in codetxt.split(splitline)]
    return comments, codes

def split_lean_text(leantext, splitline='---SPLITLINE---', lowerbound=800):
    """Split Lean text into slices with the number of tokens less than lowerbound.
    
    Args:
        leantext (str): Lean text
        splitline (str): split line
    Returns:
        slices (list): list of slices
    """
    comments, codes = lean2blocks(leantext, splitline)
    slices = []
    for comment in comments:
        slices.append(splittext(comment, lowerbound))
    return codes, slices

def process_long_leantext( text:str
                         , chkpoint:str
                         , lowerbound:int=800
                         , msg2chat:Union[Callable[[str], Chat], None]=None):
    """Process long Lean text.

    Args:
        text (str): Lean text
        chkpoint (str): checkpoint
        lowerbound (int): lowerbound
        msg2chat (Callable[[str], Chat]): function to convert message to chat
    
    Returns:
        str: processed Lean text
    """
    # split text into slices
    codes, slices = split_lean_text(text, lowerbound=lowerbound)
    lengths, isempty_slices, filtered_slices = preprocess_slices(slices)
    # process slices
    chats = process_chats(filtered_slices, msg2chat, chkpoint)
    nested_chats = recover_slices(lengths, isempty_slices, chats, emptyslice=Chat())
    # combine the chat log
    output_txt = ""
    for i, code in enumerate(codes):
        code = f"\n\n{code}\n\n" if code else "\n\n"
        newcomment = ""
        if i < len(nested_chats):
            newcomment = "\n".join([chat.last_message for chat in nested_chats[i]])
        output_txt += f"{code}/- {newcomment}\n-/"
    return output_txt

def translate_lean_file(source:str, target:str, chkpoint:str, **kwargs):
    """Translate Lean file.
    
    Args:
        source (str): source file
        target (str): target file
        chkpoint (str): checkpoint
        lowerbound (int): lowerbound
        msg2chat (Callable[[str], Chat]): function to convert message to chat
    """
    _translate_file( process_long_leantext, source, target, chkpoint, **kwargs)

def translate_lean_folder( source:str
                         , target:str
                         , chkpoint_path:str
                         , chkpoint_prefix:str=""
                         , ext:str='.md'
                         , skipexist:bool=True
                         , subpath:bool=True
                         , display:bool=True
                         , **kwargs):
    """Translate LEAN folder.

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
    _translate_folder( translate_lean_file
                     , source, target, chkpoint_path
                     , chkpoint_prefix, ext, skipexist
                     , subpath, display, **kwargs)

# async version
async def async_process_long_leantext( text:str
                                     , chkpoint:str
                                     , lowerbound:int=800
                                     , **kwargs):
        """Process long Lean text.
    
        Args:
            text (str): Lean text
            chkpoint (str): checkpoint
            lowerbound (int): lowerbound
            ncoroutines (int): number of coroutines
            msg2log (Callable): function to convert message to log
            max_tokens (Callable): function to get max tokens
            max_requests (int): maximum number of requests to make
            clearfile (bool): whether to clear the checkpoint file
        
        Returns:
            str: processed Lean text
        """
        # split text into slices
        codes, slices = split_lean_text(text, lowerbound=lowerbound)
        lengths, isempty_slices, filtered_slices = preprocess_slices(slices)
        # process slices
        kwargs['notrun'] = True
        await async_chat_completion(filtered_slices, chkpoint, **kwargs)
        chats = load_chats(chkpoint, withid=True)
        assert None not in chats, "Some slices are not translated."
        nested_chats = recover_slices(lengths, isempty_slices, chats, emptyslice=Chat())
        # combine the chat log
        output_txt = ""
        for i, code in enumerate(codes):
            code = f"\n\n{code}\n\n" if code else "\n\n"
            newcomment = ""
            if i < len(nested_chats):
                newcomment = "\n".join([chat.last_message for chat in nested_chats[i]])
            output_txt += f"{code}/- {newcomment}\n-/"
        return output_txt

async def async_translate_lean_file(source, target, chkpoint, **kwargs):
    """Translate lean file asynchronously.
    
    Args:
        source (str): source file
        target (str): target file
        chkpoint (str): checkpoint
        lowerbound (int): lowerbound of the number of tokens in each slice
        msg2log (Callable): function to convert message to log
        max_tokens (Callable): function to get max tokens
        max_requests (int): maximum number of requests to make
    """
    await _async_translate_file(async_process_long_leantext, source, target, chkpoint, **kwargs)

async def async_translate_lean_folder( source:str
                                     , target:str
                                     , chkpoint_path:str
                                     , chkpoint_prefix:str=""
                                     , ext:str='.md'
                                     , skipexist:bool=True
                                     , subpath:bool=True
                                     , display:bool=True
                                     , **kwargs):
    """Translate lean folder asynchronously.

    Args:
        source (str): source folder
        target (str): target folder
        chkpoint_path (str): checkpoint folder
        chkpoint_prefix (str): checkpoint prefix
        msg2log (Callable): function to convert message to log
        max_tokens (Callable): function to get max tokens
        max_requests (int): maximum number of requests to make
        ext (str): extension
        skipexist (bool): whether to skip existing files
        subpath (bool): whether to scan subpath
        display (bool): whether to display
    """
    await _async_translate_folder( async_translate_lean_file
                                 , source, target, chkpoint_path
                                 , chkpoint_prefix, ext, skipexist
                                 , subpath, display, **kwargs)
