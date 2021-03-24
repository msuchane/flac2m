#!/usr/bin/env python3

import argparse
import os
import subprocess as sp
from multiprocessing import Pool
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

def report_file(new: str, placing: int, total: int) -> str:
    file_name = os.path.basename(new)
    report = f"Converting file {placing}/{total}: {file_name}"

    return report

def convert_file(target: dict) -> None:
    # Notify about the processed file
    print(target["report"])

    # Create the output directories if necessary
    out_dir = os.path.dirname(target["new"])
    os.makedirs(out_dir, exist_ok=True)

    try:
        process = sp.run(target["command"],
                         stdout=sp.DEVNULL,
                         stderr=sp.PIPE,
                         check=True)
    except Exception as e:
        # Conversion failed somehow. Show the most recent encoder output
        # and the exception that happened.
        error_exit("{}\n\n{}".format(process.stderr.decode("utf-8"), e))

def convert_all_files(in_out_list: InOutList,
                      args: argparse.Namespace,
                      codec_props: CodecProps) -> None:
    file_count = len(in_out_list)
    quality_option = create_quality_option(args, codec_props)

    # Prepare the metadata for the whole conversion
    conversion_targets = []

    for index, in_out in enumerate(in_out_list):
        infile, outfile = in_out

        target = {
            "orig": infile,
            "new": outfile,
            "placing": index,
            "total": file_count,
            "quality": quality_option,
            "report": report_file(outfile, index, file_count),
            "command": create_conversion_command(infile,
                                                 outfile,
                                                 quality_option,
                                                 codec_props),
        }

        conversion_targets.append(target)

    # Run the conversion in parallel
    pool = Pool(4)
    pool.map(convert_file, conversion_targets)
