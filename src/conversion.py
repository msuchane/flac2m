#!/usr/bin/env python3

import argparse
import os
import subprocess as sp
from typing import List

from common import error_exit
from audio_codecs import CodecProps
from paths import InOutList


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
