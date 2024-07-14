## flac2m (FLAC to Many)

A music library converter.

`flac2m` is a command-line tool that converts FLAC music files into a given lossy format. It preserves the original, nested directory structure. It is intended for converting a large FLAC library, such as when you want to copy it to a portable device with limited storage.

The conversion runs in parallel on all your CPUs.


### Usage

```
$ flac2m <flac-library> -o <output-directory> -c {mp3,oggvorbis,opus}
```

Other options:

* `-b, --bitrate <BITRATE>`

    Constant bitrate for lossy audio

* `-C, --copy <FILES>`

    Filenames to copy over unchanged (useful for cover images)

* `-i, --info`

    Show detailed info on codecs/qualities and quit

* `-p, --preset {default,low,transp,high}`

    Quality preset: default for encoder, low/OK, just transparent, high

* `-q, --quality QUALITY`

    Variable bitrate quality; 1=low, 5=high

* `-s, --substitutef <SUBSTITUTION>`

    Substitution in file names; enter as `old/new`

* `-S, --substituted <SUBSTITUTION>`

    Substitution in directory names; enter as `old/new`


### Supported codecs

Currently, `flac2m` supports creating MP3, OGG Vorbis, and Opus (default) files.

The program is easily extensible to recognize new codecs and their encoders. Further options can be added in the future.


### Dependencies

* Python 3.5 or higher

* Encoders:

    * `lame` for MP3
    * `oggenc` for OGG Vorbis
    * `opusenc` for Opus

    If the encoder is not present on your system, `flac2m` will not be able to convert to the given codec.

* Operating systems:

    * `flac2m` has only been tested on Linux.
    * It can probably run on macOS if the required encoders are available in `$PATH`.
