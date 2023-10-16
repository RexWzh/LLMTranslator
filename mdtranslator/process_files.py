import os
from typing import Callable, Union

ishidden = lambda path: os.path.split(path)[-1].startswith('.')
def get_files_and_paths(path, ext='.md'):
    """Get files and paths relative to the `path`.

    Args:
        path (str): path
        ext (str): extension
    Returns:
        target_files (list): list of target files
        sub_paths (list): list of sub paths
    """
    target_files, sub_paths = [], []
    for root, _, files in os.walk(path):
        relative_path = os.path.relpath(root, path).lstrip('./')
        if ishidden(relative_path): continue
        sub_paths.append(relative_path)
        for file in files:
            if file.endswith(ext):
                target_files.append(os.path.join(relative_path, file))
    return target_files, sub_paths

def make_dirs(paths):
    """Make directories.

    Args:
        paths (list): list of paths
    """
    for path in paths:
        if not os.path.exists(path):
            os.mkdir(path)

def initialize_files( source:str
                    , target:str
                    , chkpoint_path:str
                    , chkpoint_prefix:str
                    , ext:str='.md'
                    , subpath:bool=True):
    """Initialize files.
    
    Args:
        source (str): source folder
        target (str): target folder
        chkpoint_path (str): checkpoint folder
        chkpoint_prefix (str): checkpoint prefix
        ext (str): extension
        subpath (bool): whether to scan subpath
    
    Returns:
        listinfiles (list): list of input files
        listoutfiles (list): list of output files
        listchatfiles (list): list of chat files(checkpoints)
    """
    make_dirs([target, chkpoint_path])
    if subpath: # scan subpath
        listfiles, subpaths = get_files_and_paths(source, ext)
        make_dirs([os.path.join(target, subpath) for subpath in subpaths])
        make_dirs([os.path.join(chkpoint_path, subpath) for subpath in subpaths])
    else:
        listfiles = [file for file in os.listdir(source) if file.endswith(ext)]
    listinfiles = [os.path.join(source, fname) for fname in listfiles]
    listoutfiles = [os.path.join(target, fname) for fname in listfiles]
    listchatfiles = []
    for fname in listfiles:
        path, file = os.path.split(fname)
        file = file.replace(ext, "")
        chkpoint = os.path.join(chkpoint_path, path, f"{chkpoint_prefix}{file}.jsonl")
        listchatfiles.append(chkpoint)
    return listinfiles, listoutfiles, listchatfiles

# translate single file
def _translate_file( func:Callable
                   , source:str
                   , target:str
                   , chkpoint:str
                   , **kwargs):
    """Translate file with a function."""
    with open(source, 'r') as f:
        intext = f.read()
    outtext = func(intext, chkpoint, **kwargs)
    with open(target, 'w') as f:
        f.write(outtext)

# translate a folder
def _translate_folder( func:Callable
                     , source:str
                     , target:str
                     , chkpoint_path:str
                     , checkpoint_prefix:str=""
                     , ext='.md'
                     , skipexist:bool=True
                     , subpath:bool=True
                     , display:bool=True
                     , **kwargs):
    """Translate folder with a function."""
    infiles, outfiles, chatfiles = initialize_files( source, target, chkpoint_path
                                                   , checkpoint_prefix, ext, subpath)
    for infname, outfname, chkpoint in zip(infiles, outfiles, chatfiles):
        if skipexist and os.path.exists(outfname):continue
        if display: print(f"Translating file: {infname}...")
        assert infname.endswith(ext), f"File {infname} does not end with {ext}."
        func(infname, outfname, chkpoint, **kwargs)

# async version
async def _async_translate_file( func:Callable
                               , source:str
                               , target:str
                               , chkpoint:str
                               , **kwargs):
    """Translate file with a function."""
    with open(source, 'r') as f:
        intext = f.read()
    outtext = await func(intext, chkpoint, **kwargs)
    with open(target, 'w') as f:
        f.write(outtext)

async def _async_translate_folder( func:Callable
                                 , source:str
                                 , target:str
                                 , chkpoint_path:str
                                 , chkpoint_prefix:str=""
                                 , ext='.md'
                                 , skipexist:bool=True
                                 , subpath:bool=True
                                 , display:bool=True
                                 , **kwargs):
    """Translate folder with a function."""
    infiles, outfiles, chatfiles = initialize_files( source, target, chkpoint_path
                                                   , chkpoint_prefix, ext, subpath)
    for infname, outfname, chkpoint in zip(infiles, outfiles, chatfiles):
        if skipexist and os.path.exists(outfname):continue
        if display: print(f"Translating file: {infname}...")
        assert infname.endswith(ext), f"File {infname} does not end with {ext}."
        await func(infname, outfname, chkpoint, **kwargs)
