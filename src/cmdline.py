#!/usr/bin/env python3

import argparse

def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    exgroup = parser.add_mutually_exclusive_group()

    exgroup.add_argument("-b", "--bitrate", type=int,
                         help="Constant bitrate for lossy audio")
    parser.add_argument("-c", "--codec", choices=["mp3", "oggvorbis", "opus"],
                        default="opus",
                        help="Audio codec to convert FLAC files into")
    parser.add_argument("-C", "--copy", nargs="*",
                        help="Filenames to copy over unchanged "\
                             "(useful for cover images)")
    parser.add_argument("dirs", nargs="+",
                        help="Directories to search for FLAC files")
    parser.add_argument("-i", "--info", action="store_true",
                        help="Show detailed info on codecs/qualities and quit")
    parser.add_argument("-o", "--output", default="flac2m_output",
                        help="Output directory")
    exgroup.add_argument("-p", "--preset",
                         choices=["default", "low", "transp", "high"],
                         help="Quality preset: default for encoder, low/OK, "
                              "just transparent, high")
    exgroup.add_argument("-q", "--quality", type=int,
                         help="Variable bitrate quality; 1=low, 5=high")
    parser.add_argument("-s", "--substitutef",
                        help="Substitution in file names; enter as \"old/new\"")
    parser.add_argument("-S", "--substituted",
                        help="Substitution in directory names; enter as \"old/new\"")
    # TODO: actually implement verbosity
    parser.add_argument("-v", "--verbose", help="Show more progress messages",
                        action="store_true")

    return parser
