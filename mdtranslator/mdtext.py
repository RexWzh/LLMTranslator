import re
from chattool import *
from typing import Callable, Union, List
from .process_files import (
    _translate_file, _translate_folder,
    _async_translate_file, _async_translate_folder
)
from .longtext import splittext, count_token

# write tools
def md2blocks(mdtxt, splitline='---SPLITLINE---'):
    """Split markdown text into code blocks and plain text blocks.
    
    Args:
        mdtxt (str): markdown text
        splitline (str): split line
    Returns:
        codetxts (list): list of code blocks
        plaintxts (list): list of plain text blocks
    """
    splitline='---SPLITLINE---'
    # get codes
    codetxts = re.findall(r"```(.*?)\n```", mdtxt, re.S)
    codetxts = [f"```{code}\n```" for code in codetxts]
    # replace code block to `splitline`
    plaintxt = re.sub(r"```(.*?)\n```", splitline, mdtxt, flags=re.S)
    plaintxts = [txt.strip('\n') for txt in plaintxt.split(splitline)]
    return codetxts, plaintxts

def splitmdtext(mdtxt, splitline='---SPLITLINE---', lowerbound=800):
    """Split markdown text into slices with the number of tokens less than lowerbound.
    
    Args:
        mdtxt (str): markdown text
        splitline (str): split line
    Returns:
        slices (list): list of slices
    """
    codetxts, plaintxts = md2blocks(mdtxt, splitline)
    slices = []
    for txt in plaintxts:
        slices.append(splittext(txt, lowerbound))
    return codetxts, slices

def preprocess_slices(slices:List[List]):
    """Preprocess slices.

    Args:
        slices (List[List]): list of slices
    Returns:
        List[List]: list of slices
    """
    lengths = [len(slice) for slice in slices]
    flattened_slices = [slice for slices in slices for slice in slices]
    isempty_slices = [len(slice.strip()) == 0 for slice in flattened_slices]
    filtered_slices = [slice for slice in flattened_slices if len(slice.strip())!=0]
    return lengths, isempty_slices, filtered_slices

def recover_slices(lengths, isempty_slices, filtered_slices, emptyslice=""):
    flattened_slices = []
    assert sum(isempty_slices) + len(filtered_slices) == sum(lengths), "The number of slices should be the same."
    for isempty in isempty_slices:
        if not isempty:
            flattened_slices.append(filtered_slices.pop(0))
        else:
            flattened_slices.append(emptyslice)
    nested_slices = []
    for length in lengths:
        nested_slices.append(flattened_slices[:length])
        flattened_slices = flattened_slices[length:]
    return nested_slices

# process files
def process_long_mdtext( text:str
                       , chkpoint:str
                       , lowerbound:int=300
                       , msg2chat:Union[Callable[[str], Chat], None]=None):
    """Process long markdown text.

    Args:
        text (str): text to process
        chkpoint (str): checkpoint
        lowerbound (int): lowerbound of the number of tokens in each slice
        msg2chat (Callable[[str], Chat]): function to convert message to chat
    Returns:
        str: translated text
    """
    # split text into slices
    codes, nested_slices = splitmdtext(text, lowerbound=lowerbound)
    lengths, isempty_slices, filtered_slices = preprocess_slices(nested_slices)
    # process each size
    chats = process_chats(filtered_slices, msg2chat, chkpoint)
    nested_chats = recover_slices(lengths, isempty_slices, chats, emptyslice=Chat(""))
    # combine the chat log
    output_txt = ""
    for i, chats in enumerate(nested_chats):
        newtxt = '\n'.join(chat.last_message for chat in chats)
        code = '\n\n' + codes[i] + '\n\n' if i < len(codes) else ''
        output_txt += newtxt + code
    return output_txt

def translate_mdfile(source, target, chkpoint, **kwargs):
    """Translate markdown file.
    
    Args:
        source (str): source file
        target (str): target file
        chkpoint (str): checkpoint
        lowerbound (int): lowerbound of the number of tokens in each slice
        msg2chat (Callable[[str], Chat]): function to convert message to chat
    """
    _translate_file(process_long_mdtext, source, target, chkpoint, **kwargs)

def translate_mdfolder( source:str
                    , target:str
                    , chkpoint_path:str
                    , checkpoint_prefix:str=""
                    , ext:str='.md'
                    , skipexist:bool=True
                    , subpath:bool=True
                    , display:bool=True
                    , **kwargs):
    """Translate markdown folder.

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
    _translate_folder( translate_mdfile
                     , source, target, chkpoint_path
                     , checkpoint_prefix, ext, skipexist
                     , subpath, display, **kwargs)

# async version
async def async_process_long_mdtext( text:str
                                   , chkpoint:str
                                   , lowerbound:int=300
                                   , **kwargs):
    """Process long markdown text asynchronously.

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
    codes, nested_slices = splitmdtext(text, lowerbound=lowerbound)
    lengths, isempty_slices, filtered_slices = preprocess_slices(nested_slices)
    # process each size
    kwargs['notrun'] = True
    await async_chat_completion(filtered_slices, chkpoint, **kwargs)
    chats = load_chats(chkpoint, withid=True)
    assert None not in chats, "Some chats are not completed."
    nested_chats = recover_slices(lengths, isempty_slices, chats, emptyslice=Chat(""))
    # combine the chat log
    output_txt = ""
    for i, chats in enumerate(nested_chats):
        newtxt = '\n'.join(chat.last_message for chat in chats)
        code = '\n\n' + codes[i] + '\n\n' if i < len(codes) else ''
        output_txt += newtxt + code
    return output_txt

async def async_translate_mdfile(source, target, chkpoint, **kwargs):
    """Translate markdown file asynchronously.
    
    Args:
        source (str): source file
        target (str): target file
        chkpoint (str): checkpoint
        lowerbound (int): lowerbound of the number of tokens in each slice
        msg2log (Callable): function to convert message to log
        max_tokens (Callable): function to get max tokens
        max_requests (int): maximum number of requests to make
    """
    await _async_translate_file(async_process_long_mdtext, source, target, chkpoint, **kwargs)

async def async_translate_mdfolder( source:str
                                  , target:str
                                  , chkpoint_path:str
                                  , checkpoint_prefix:str=""
                                  , ext:str='.md'
                                  , skipexist:bool=True
                                  , subpath:bool=True
                                  , display:bool=True
                                  , **kwargs):
    """Translate markdown folder asynchronously.

    Args:
        source (str): source folder
        target (str): target folder
        chkpoint_path (str): checkpoint folder
        checkpoint_prefix (str): checkpoint prefix
        msg2log (Callable): function to convert message to log
        max_tokens (Callable): function to get max tokens
        max_requests (int): maximum number of requests to make
        ext (str): extension
        skipexist (bool): whether to skip existing files
        subpath (bool): whether to scan subpath
        display (bool): whether to display
    """
    await _async_translate_folder( async_translate_mdfile
                                 , source, target, chkpoint_path
                                 , checkpoint_prefix, ext, skipexist
                                 , subpath, display, **kwargs)