#!/usr/bin/env python3

import os
import sys
import subprocess as sp
import argparse
from typing import Any, Dict, List, Tuple
from shutil import copyfile

from cmdline import create_parser
from audio_codecs import CODECS, \
    CodecProps, VersionList, \
    check_executables, codecs_info


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

def create_quality_option(args: argparse.Namespace,
                          codec_props: CodecProps) -> List[str]:
    if args.bitrate:
        min_b = codec_props["bitrate_min"]
        max_b = codec_props["bitrate_max"]

        if args.bitrate < min_b or args.bitrate > max_b:
            error_exit("Bitrate must be between {} and {}.".format(
                min_b, max_b))

        quality_option = codec_props["bitrate_arg"] + args.bitrate
    elif args.quality:
        min_q = codec_props["quality_min"]
        max_q = codec_props["quality_max"]

        if args.quality < min_q or args.quality > max_q:
            error_exit("Quality must be between {} and {}.".format(
                min_q, max_q))

        quality_option = codec_props["quality_arg"] + args.quality
    elif args.preset:
        if args.preset == "high":
            quality_option = codec_props["preset_high"]
        elif args.preset == "low":
            quality_option = codec_props["preset_low"]
        else:
            quality_option = codec_props["preset_transparent"]
    else:   # Default case
        quality_option = codec_props["preset_transparent"]

    return quality_option

def create_conversion_command(infile: str, outfile: str,
                              quality_option: List[str],
                              codec_props: CodecProps) -> list:
    assert infile.endswith(".flac"), "Not a FLAC file: {}".format(infile)

    v = codec_props
    encoder = v["encoder"]
    out_arg = v["output_arg"]
    additional = v["additional_args"]
    suffix = v["suffix"]

    # Add suffix to output file stripped of '.flac'
    outfile = "{}.{}".format(outfile[:-5], suffix)

    # command = [encoder, quality_option, additional, infile, out_arg, outfile]
    command = [encoder]
    command.extend(quality_option)
    command.extend(additional)
    command.append(infile)
    command.extend(out_arg)
    command.append(outfile)

    return command

def check_access(path, write=False):
    acc = os.access

    if write:
        return acc(path, os.W_OK) and acc(path, os.X_OK)
    else:
        return acc(path, os.R_OK) and acc(path, os.X_OK)

def run_conversion_command(in_out_list: InOutList,
                           args: argparse.Namespace,
                           codec_props: CodecProps) -> None:
    file_count = len(in_out_list)

    for index, in_out in enumerate(in_out_list):
        infile, outfile = in_out
        print("Converting file {} out of {}…".format(index+1, file_count))

        # Creating directories if necessary
        out_dir = os.path.split(outfile)[0]
        quality_option = create_quality_option(args, codec_props)
        os.makedirs(out_dir, exist_ok=True)

        comm = create_conversion_command(infile, outfile,
                                         quality_option, codec_props)
        try:
            process = sp.run(comm, stdout=sp.DEVNULL, stderr=sp.PIPE)
        except Exception as e:
            # Conversion failed somehow. Show most recent encoder output
            # and the Python exception that happened.
            error_exit("{}\n\n{}".format(process.stderr.decode("utf-8"), e))

        # If the encoder itself failed, stop the conversion and show
        # its error message:
        if process.returncode != 0:
            error_exit("Encoding file ‘{}’ failed:\n\n{}".format(
                infile, process.stderr.decode("utf-8")))

def error_exit(message: str) -> None:
    sys.exit("{}: error: {}".format(sys.argv[0], message))


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()
    # print(args.dirs)

    # Check whether encoders are present on the system
    ex_v: VersionList = check_executables(CODECS)

    # Update codecs dict with encoder versions
    for c, v in ex_v:
        CODECS[c]["version"] = v

    if args.info:
        print(codecs_info(CODECS))
        sys.exit()

    # This will fail if the output directory cannot be created or it already
    # exists and is not a directory
    try:
        os.makedirs(args.output, exist_ok=True)
    except FileExistsError:
        error_exit("‘{}’ exists and is not a directory.".format(
            args.output))
    except PermissionError:
        error_exit("Cannot create output directory ‘{}’ "\
                   "(insufficient permission).".format(args.output))
    # Check whether the output dir is accesible for writes
    if not check_access(args.output, write=True):
        error_exit("Cannot write to output directory ‘{}’".format(
            args.output))

    # The selected codec to convert to
    sel_codec = args.codec
    # Relevant dict of type CodecProps
    codec_props = CODECS[sel_codec]

    if codec_props["version"] == "MISSING":
        sys.exit("Couldn't find the ‘{}’ encoder. You need to install it "\
                 "in order to use the ‘{}’ codec.".format(
                     codec_props["encoder"], sel_codec))

    # If the -s option has been selected, prepare substitution strings
    if args.substitutef:
        subsf = evaluate_substitution(args.substitutef)
    else:
        subsf = None

    # If the -S option has been selected, prepare substitution strings
    if args.substituted:
        subsd = evaluate_substitution(args.substituted)
    else:
        subsd = None

    music_map = find_music(args.dirs)
    # print(music_map)
    in_out_list = create_in_out_paths(music_map, args.output, subsf, subsd)
    # print(in_out_list)

    # for infile, outfile in in_out_list:
    #     print(create_conversion_command(infile, outfile, args, codec_props))
    # print(greatest_common_dir([t[0] for t in m]))
    # print(create_conversion_command("/home/me/song.flac", "/usb/music/song", args))

    run_conversion_command(in_out_list, args, codec_props)

    # If the --copy option has been selected, process files to copy
    if args.copy:
        print("Copying unmodified files…")
        in_out_list_copy = create_in_out_paths(music_map, args.output,
                                               subsf, subsd, copy=True,
                                               c_template=args.copy)

        for infile, outfile in in_out_list_copy:
            copyfile(infile, outfile)

