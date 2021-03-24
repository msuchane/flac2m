#!/usr/bin/env python3

from typing import List, Tuple
import os

MusicDir = Tuple[str, List[str]]    # A tuple of dir name and all of its files
MusicMap = List[MusicDir]           # List of dirs containing music

def find_music(roots: List[str]) -> MusicMap:
    music_dirs = []

    for root in roots:
        # Use absolute paths otherwise first letter can be lost somewhere
        root_abs = os.path.abspath(root)

        for directory in os.walk(root_abs):
            dir_name, cont_dirs, cont_files = directory

            for f in cont_files:
                if f.endswith(".flac"):
                    # print("Music found: {} in {}".format(f, dir_name))
                    music_dirs.append((dir_name, cont_files))
                    break

    return music_dirs

# This function is similar to os.path.commonpath except for the 1-element case.
# I discovered os.path.common_path only after writing this, now too proud
# to replace it. It was a good excercise.
def greatest_common_dir(directories: List[str]) -> str:
    """
    Compares directory paths in list and returns the part that all of them
    have in common; i.e. ["/usr/bin", "/usr/share"] -> "/usr"

    If there is only one directory, returns all except the innermost element;
    i.e. ["/usr/share/man"] -> "/usr/share"
    """
    # The list of directories should never be empty
    assert len(directories) != 0, "No music directories to analyze"

    # If there is only one directory in the list, return the innermost
    # directory immediately containing music files
    if len(directories) == 1:
        split_dir = directories[0].split("/")
        all_except_containing_dir = split_dir[:-1]

        return "/".join(all_except_containing_dir)

    split_dirs = [d.split("/") for d in directories]
    common_elements = []

    common = True
    index = 0

    while common:
        first_dir = split_dirs[0]
        path_element = first_dir[index]

        for d in split_dirs:
            if d[index] != path_element:
                common = False
                break

        if common:
            common_elements.append(path_element)

        index += 1

    common_path = "/".join(common_elements)

    return common_path

def get_flac_files(all_files: List[str]) -> List[str]:
    flacs = [f for f in all_files if f.endswith("flac")]

    return flacs

def get_files_to_copy(all_files: List[str], c_template: List[str]) -> List[str]:
    # Not a list comprehension here because this can potentially be faster
    # considering there should only be a few covers / copy file templates
    # and many actual files
    to_copy = []

    for c in c_template:
        for f in all_files:
            if f == c:
                to_copy.append(f)

    return to_copy

def subtract_common_path(full_path: str, common_path: str) -> str:
    assert full_path.startswith(common_path), "No common path to subtract"

    common_length = len(common_path)
    subtracted = full_path[common_length+1:]

    return subtracted

SubsPair = Tuple[str, str]      # A pair of strings to use in substitution

def evaluate_substitution(subs: str) -> SubsPair:
    split_subs = subs.split("/")

    if len(split_subs) != 2:
        error_exit("‘{}’: invalid substitution format. "\
                 "Expected ‘old/new’.".format(subs))

    return (split_subs[0], split_subs[1])

InOutPair = Tuple[str, str]     # A pair of input path and output path
InOutList = List[InOutPair]     # A list of said in/out pairs

def create_in_out_paths(music_map: MusicMap, out_root: str,
                        subsf: SubsPair, subsd: SubsPair,
                        copy=False, c_template=None) -> InOutList:
    all_dirs = [t[0] for t in music_map]
    common_path = greatest_common_dir(all_dirs)

    in_out_list = []

    for music_dir in music_map:
        dir_path, files = music_dir

        if copy:
            sel_files = get_files_to_copy(files, c_template)
        else:
            sel_files = get_flac_files(files)

        unique_path = subtract_common_path(dir_path, common_path)

        # TODO: process substitutions in a separate function beforehand
        if subsd:
            old, new = subsd
            unique_path = unique_path.replace(old, new)

        for f in sel_files:
            if subsf:
                old, new = subsf
                f.replace(old, new)

            in_path = os.path.join(dir_path, f)
            out_path = os.path.join(out_root, unique_path, f)

            in_out_list.append((in_path, out_path))

    return in_out_list
