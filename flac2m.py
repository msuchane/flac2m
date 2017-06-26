import os
import sys
import argparse
import subprocess as sp
from typing import Any, Dict, List, Tuple

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
    parser.add_argument("-s", "--substitutef",
                        help="Substitution in filenames; enter as \"old/new\"")
    parser.add_argument("-S", "--substituted",
                        help="Substitution in dir names; enter as \"old/new\"")
    parser.add_argument("-v", "--verbose", help="Show more progress messages",
                        action="store_true")

    return parser

CodecProps = Dict[str, Any]                 # Keywords as strings, their
                                            # values of any type
CodecsDict = Dict[str, CodecProps]          # Dict of codec names and their
                                            # respective properties (also dict)
CODECS = {
    "mp3": {
        "encoder": "lame",
        "bitrate_arg": ["--cbr", "-b"],
        "bitrate_max": 320,
        "bitrate_min": 32,
        "quality_arg": ["-V"],
        "quality_max": 0,
        "quality_min": 6,
        "preset_default": ["-V4"],      # ~165 kb/s
        "preset_high": ["-V0"],         # ~245 kb/s
        "preset_transparent": ["-V3"],  # ~175 kb/s
        "preset_low": ["-V5"],          # ~130 kb/s
        "additional_args": [],
        "output_arg": [],
        "suffix": "mp3",
        "version": None     # To be filled in at runtime
    },
    "oggvorbis": {
        "encoder": "oggenc",
        "bitrate_arg": ["-b"],
        "bitrate_max": 400,
        "bitrate_min": 16,
        "quality_arg": ["-q"],
        "quality_max": 10,
        "quality_min": -1,
        "preset_default": ["-q", "3"],      # ~112 kb/s
        "preset_high": ["-q", "7"],         # ~224 kb/s
        "preset_transparent": ["-q", "5"],  # ~160 kb/s
        "preset_low": ["-q", "3"],          # ~112 kb/s
        "additional_args": [],
        "output_arg": ["-o"],
        "suffix": "ogg",
        "version": None     # To be filled in at runtime
    },
    "opus": {
        "encoder": "opusenc",
        "bitrate_arg": ["--cvbr", "--bitrate"],
        "bitrate_max": 512,
        "bitrate_min": 12,
        "quality_arg": ["--vbr", "--bitrate"],
        "quality_max": 512,
        "quality_min": 12,
        "preset_default": ["--bitrate", "96"],
        "preset_high": ["--bitrate", "192"],
        "preset_transparent": ["--bitrate", "112"],
        "preset_low": ["--bitrate", "82"],
        "additional_args": ["--framesize=60"],
        "output_arg": [],
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
            enc_process = sp.run([encoder, "--version"], stdout=sp.PIPE)
        except FileNotFoundError:
            print("{} encoder not found".format(encoder))
            versions_result.append((codec, "MISSING"))
        else:
            version_str = enc_process.stdout.decode("utf-8")
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
                    # These arguments are stored as lists; concatenate them
                    " ".join(v["preset_default"]),
                    " ".join(v["preset_high"]),
                    " ".join(v["preset_transparent"]),
                    " ".join(v["preset_low"]))
            info.append(m)

    return "\n".join(info)

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
        sys.exit("‘{}’: invalid substitution format. "\
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

def create_conversion_command(infile: str, outfile: str,
                              args: argparse.Namespace,
                              codec_props: CodecProps) -> list:
    assert infile.endswith(".flac"), "Not a FLAC file: {}".format(infile)

    v = codec_props
    encoder = v["encoder"]
    out_arg = v["output_arg"]
    additional = v["additional_args"]
    suffix = v["suffix"]

    # Add suffix to output file stripped of '.flac'
    outfile = "{}.{}".format(outfile[:-5], suffix)

    # TODO: check min and max bitrate/quality bounds
    # TODO: possibly move this logic to another function
    if args.bitrate:
        quality_option = [v["bitrate_arg"], args.bitrate]
    elif args.quality:
        quality_option = [v["quality_arg"], args.quality]
    elif args.preset:
        # TODO: other presets
        quality_option = v["preset_transparent"]
    else:   # Default case
        quality_option = v["preset_transparent"]

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
    for infile, outfile in in_out_list:
        # Creating directories if necessary
        out_dir = os.path.split(outfile)[0]
        os.makedirs(out_dir, exist_ok=True)

        comm = create_conversion_command(infile, outfile, args, codec_props)
        process = sp.run(comm)


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()
    print(args.dirs)

    # Check whether encoders are present on the system
    ex_v = check_executables(CODECS)

    # Update codecs dict with encoder versions
    for c, v in ex_v:
        CODECS[c]["version"] = v

    if args.info:
        print(codecs_info(CODECS))
        sys.exit()

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
    print(music_map)
    in_out_list = create_in_out_paths(music_map, args.output, subsf, subsd)
    print(in_out_list)

    for infile, outfile in in_out_list:
        print(create_conversion_command(infile, outfile, args, codec_props))
    # print(greatest_common_dir([t[0] for t in m]))
    # print(create_conversion_command("/home/me/song.flac", "/usb/music/song", args))

    run_conversion_command(in_out_list, args, codec_props)

