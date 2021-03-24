#!/usr/bin/env python3

import os
import sys
from shutil import copyfile

from common import error_exit
from cmdline import create_parser
from audio_codecs import CODECS, VersionList, check_executables, codecs_info
from paths import find_music, evaluate_substitution, create_in_out_paths, \
    check_access
from conversion import run_conversion_command


def main() -> None:
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

if __name__ == "__main__":
    main()
