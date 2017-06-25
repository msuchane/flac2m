import os
import sys
import argparse
import subprocess as sp
from typing import Any, Dict, List, Tuple

parser = argparse.ArgumentParser()
exgroup = parser.add_mutually_exclusive_group()

exgroup.add_argument("-b", "--bitrate", type=int,
                     help="Constant bitrate for lossy audio")
parser.add_argument("-c", "--codec", choices=["mp3", "oggvorbis", "opus"],
                    help="Audio codec to convert FLAC files into")
parser.add_argument("-C", "--cover", nargs="*",
                    help="Cover image filenames to copy over")
parser.add_argument("dirs", nargs="*", default=["."],
                    help="Directories to search for FLAC files")
parser.add_argument("-i", "--info", action="store_true",
                    help="Show detailed info on codecs/qualities and quit")
parser.add_argument("-o", "--output", default="flac2m_output",
                    help="Output directory")
exgroup.add_argument("-p", "--preset",
                     choices=["default", "low", "transp", "high"],
                     help="Quality preset: default for encoder, low/OK, "
                          "just transparent, high")
exgroup.add_argument("-q", "--quality", type=int, choices=[1, 2, 3, 4, 5],
                     help="Variable bitrate quality; 1=low, 5=high")
parser.add_argument("-v", "--verbose", help="Show more progress messages",
                    action="store_true")

CodecProps = Dict[str, Any]                 # Keywords as strings, their
                                            # values of any type
CodecsDict = Dict[str, CodecProps]          # Dict of codec names and their
                                            # respective properties (also dict)
codecs = {
    "mp3": {
        "encoder": "lame",
        "bitrate_arg": "--cbr -b",
        "bitrate_max": 320,
        "bitrate_min": 32,
        "quality_arg": "-V",
        "quality_max": 0,
        "quality_min": 6,
        "preset_default": "-V 4",       # ~165 kb/s
        "preset_high": "-V 0",          # ~245 kb/s
        "preset_transparent": "-V 3",   # ~175 kb/s
        "preset_low": "-V 5",           # ~130 kb/s
        "additional_args": "",
        "suffix": "mp3",
        "version": None     # To be filled in at runtime
    },
    "oggvorbis": {
        "encoder": "oggenc",
        "bitrate_arg": "-b",
        "bitrate_max": 400,
        "bitrate_min": 16,
        "quality_arg": "-q",
        "quality_max": 10,
        "quality_min": -1,
        "preset_default": "-q 3",       # ~112 kb/s
        "preset_high": "-q 7",          # ~224 kb/s
        "preset_transparent": "-q 5",   # ~160 kb/s
        "preset_low": "-q 3",           # ~112 kb/s
        "additional_args": "",
        "suffix": "ogg",
        "version": None     # To be filled in at runtime
    },
    "opus": {
        "encoder": "opusenc",
        "bitrate_arg": "--cvbr --bitrate",
        "bitrate_max": 512,
        "bitrate_min": 12,
        "quality_arg": "--vbr --bitrate",
        "quality_max": 512,
        "quality_min": 12,
        "preset_default": "--bitrate 96",
        "preset_high": "--bitrate 192",
        "preset_transparent": "--bitrate 112",
        "preset_low": "--bitrate 82",
        "additional_args": "--framesize=60",
        "suffix": "opus",
        "version": None     # To be filled in at runtime
    }
}

VersionList = List[Tuple[str, str]]    # Tuples ofencoder name and its version
def check_executables(codecs: CodecsDict) -> VersionList:
    versions_result = []

    for codec in codecs:
        encoder = codecs.get(codec).get("encoder")

        try:
            enc_out = sp.Popen([encoder, "--version"], stdout=sp.PIPE)
        except FileNotFoundError:
            print("{} encoder not found".format(encoder))
            versions_result.append((codec, "MISSING"))
        else:
            version_bytes = enc_out.stdout.read()
            version_str = version_bytes.decode("utf-8")
            versions_result.append((codec, version_str.split("\n")[0]))

    return versions_result

MusicDir = Tuple[str, List[str]]    # A tuple of dir name and all of its files
MusicMap = List[MusicDir]           # List of dirs containing music
def find_music(roots: List[str]) -> MusicMap:
    music_dirs = []

    for root in roots:
        for directory in os.walk(root):
            dir_name, cont_dirs, cont_files = directory

            for f in cont_files:
                if f.endswith(".flac"):
                    print("Music found: {} in {}".format(f, dir_name))
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

    If there is only one directory, returns the innermost element; i.e.
    ["/usr/bin"] -> "bin"
    """
    # The list of directories should never be empty
    assert len(directories) != 0, "No music directories to analyze"

    # If there is only one directory in the list, return the innermost
    # directory immediately containing music files
    if len(directories) == 1:
        split_dir = directories[0].split("/")
        containing_dir = split_dir[-1]

        return containing_dir

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
            print("appending '{}'".format(path_element))
            common_elements.append(path_element)

        index += 1

    common_path = "/".join(common_elements)

    return common_path

def codecs_info(codecs_dict: CodecsDict) -> str:
    info = []

    for k in codecs_dict:
        v = codecs_dict.get(k)

        if v["version"] == "MISSING":
            m = "Codec: {}\n"\
                "Encoder not found. You need to install "\
                "the ‘{}’ program.\n".format(k, v["encoder"])
            info.append(m)
        else:
            m = "Codec: {}\n"\
                "Encoder: {}\n"\
                "Constant bitrate from {} to {} kb/s\n"\
                "Variable bitrate quality from {} (min) to {} (max)\n"\
                "Presets:\n"\
                "    encoder default: {}\n"\
                "    high:            {}\n"\
                "    transparent:     {}\n"\
                "    low:             {}\n".format(
                    k, v["version"], v["bitrate_min"], v["bitrate_max"],
                    v["quality_min"], v["quality_max"],
                    v["preset_default"], v["preset_high"],
                    v["preset_transparent"], v["preset_low"])
            info.append(m)

    return "\n".join(info)

def get_flac_files(all_files: List[str]) -> List[str]:
    flacs = [f for f in all_files if f.endswith("flac")]

    return flacs

def get_cover_files(all_files: List[str], c_template: List[str]) -> List[str]:
    # Not a list comprehension here because this can potentially be faster
    # considering there should only be a few covers and many different files
    covers = []

    for c in c_template:
        for f in all_files:
            if f == c:
                covers.append(f)

    return covers

if __name__ == "__main__":
    args = parser.parse_args()
    print(args.dirs)

    # Check whether encoders are present on the system
    ex_v = check_executables(codecs)

    # Update codecs dict with encoder versions
    for c, v in ex_v:
        codecs[c]["version"] = v

    if args.info:
        print(codecs_info(codecs))
        sys.exit()

    m = find_music(args.dirs)
    print(m)
    print(greatest_common_dir([t[0] for t in m]))

