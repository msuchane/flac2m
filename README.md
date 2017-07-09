## flac2m (Flac to Many): A Music Library Converter ##

flac2m is a command-line tool written in Python that converts FLAC music files into a lossless format, preserving the directory structure.


### Usage ###

\<to be written\>


### Supported Codecs and Encoders ####

Currently, flac2m supports creating MP3, OGG Vorbis and Opus files using `lame`, `oggenc` and `opusenc`, respectively. The stand-alone command-line programs need to be installed (flac2m doesn't interface with their library API). If an encoder is not present on your system, flac2m will run but will not be able to convert to the respective codec.

flac2m is easily extensible to recognize new codecs and their encoders. Further options can be added in the future.


### Requirements ###

flac2m requires Python 3.5 or higher to run. It only utilizes the standard library. Encoders (at least one of `lame`, `oggenc` and `opusenc`) need to be installed for flac2m to be useful.

