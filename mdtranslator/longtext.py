import os
from chattool import Chat, process_chats, async_chat_completion, load_chats
from typing import Callable, Union

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
        str: chat log
    """
    # split text into slices
    slices = splittext(text, lowerbound)
    # process each size
    chats = process_chats(slices, msg2chat, chkpoint)
    # combine the chat log
    return '\n'.join(chat.last_message for chat in chats)
        
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

    Returns:
        str: chat log
    """
    # split text into slices
    slices = splittext(text, lowerbound)
    # process each size
    kwargs['notrun'] = True
    await async_chat_completion(slices, chkpoint, **kwargs)
    chats = load_chats(chkpoint, withid=True)
    # combine the chat log
    return '\n'.join(chat.last_message for chat in chats)

def translate_file(source, target, chkpoint, **kwargs):
    with open(source, 'r') as f:
        text = f.read()
    zhtext = process_long_text(text, chkpoint, **kwargs)
    with open(target, 'w') as f:
        f.write(zhtext)

async def async_translate_file(source, target, chkpoint, **kwargs):
    with open(source, 'r') as f:
        text = f.read()
    zhtext = await async_process_long_text(text, chkpoint, **kwargs)
    with open(target, 'w') as f:
        f.write(zhtext)

def translate_folder(source, target, chkpoint_prefix, ext='.md', skipexist=True, **kwargs):
    if not os.path.exists(target):
        os.mkdir(target)
    for fname in os.listdir(source):
        infname, outfname = os.path.join(source, fname), os.path.join(target, fname)
        if skipexist and os.path.exists(outfname):continue
        if fname.endswith(ext):
            chkpoint = f"{chkpoint_prefix}{fname}.jsonl"
            translate_file(infname, outfname, chkpoint, **kwargs)

async def async_translate_folder(source, target, chkpoint_prefix, ext='.md', skipexist=True, **kwargs):
    if not os.path.exists(target):
        os.mkdir(target)
    for fname in os.listdir(source):
        infname, outfname = os.path.join(source, fname), os.path.join(target, fname)
        if skipexist and os.path.exists(outfname):continue
        if fname.endswith(ext):
            chkpoint = f"{chkpoint_prefix}{fname}.jsonl"
            await async_translate_file(infname, outfname, chkpoint, **kwargs)