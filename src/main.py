#!/usr/bin/env python3

import os
import sys
import subprocess as sp
import argparse
from typing import List
from shutil import copyfile

from cmdline import create_parser
from audio_codecs import CODECS, \
    CodecProps, VersionList, \
    check_executables, codecs_info
from paths import InOutList, find_music, evaluate_substitution, create_in_out_paths


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

