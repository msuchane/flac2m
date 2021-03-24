#!/usr/bin/env python3

import subprocess as sp
from typing import Any, Dict, List, Tuple

CodecProps = Dict[str, Any]                 # Keywords as strings, their
                                            # values of any type
CodecsDict = Dict[str, CodecProps]          # Dict of codec names and their
                                            # respective properties (also dict)
VersionList = List[Tuple[str, str]]         # Tuples of encoder name and its version

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
