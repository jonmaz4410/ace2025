# Camaleonte Covert Channel

<p align="center" width="100%">
    <img width="90%" src="images/LOGO.png"> 
</p>


## Overview

We have developed a proof-of-concept covert channel that supports C2 capabilities. We developed a transmission protoocl that can send messages of any size (within time constraints) over a filesystem medium. Our covert channel does not create any new files and only utilizes pre-existing files in a medium. Additionally, we also implemented multiple clients and rudimentary error correction.

We currently support 2 different encoding schemes: hash and metadata. Metadata based channels are already well established, but hash based encoding is novel (to our knowledge) and show promise if developed further.

Our intent was to design a channel that was filesystem agnostic, so we designed our code with abstraction in mind. Currently, we have developed for 2 mediums: Linux based shares (NFS, etc.) and Google Drive. Both of these mediums support the encoding schemes we implemented.

As for C2 capabilites,  we have `upload`, `download` and `execute` capabilites. You can utilize our covert channel C2 either by running our python code base or our custom metasploit module.

## Usage

### Metasploit Usage
Usage instructions for the metasploit can be found [here](metasploit-usage.md).

### Python Code Usage
Usage instructions for the python codebase can be found [here](python-usage.md)

### Compilation Instructions


## How it Works

### Overall View
An overview on how our covert channel works can be found [here](documentation.md).

### Python Code Overview
An overview on how our python code works can be found [here](python-documentation.md).

### Metasploit Code Overview
To implement metasploit functionalities, we translated our python codebase into ruby. The covert channel logic between the two codebases should be the same, as a metasploit server is able to interact with a python client. You can find an overview [here](metasploit-documentation.md).


## Future Work
- Cannot `cat` binary files (you can `download`/`upload` them though)
    - This is because we use a terminator `\x04` which might appear naturally in the binary file
- Google drive supports only 1 client
    - The reason for this is because we don't want to constantly poll the master config file while waiting (since API calls take a while), meaning we can't our sync file synchronization feature
- Google drive requests timeout, leading to the covert channel crashing

More detail on future work can be found [here](future-work.md).


## Contact Us
For future questions, feel free to contact the developers:

1. Salaj Rijal [Github](https://github.com/srijal30)
2. Jonathan Mazurkiewicz [Github](https://github.com/jonmaz4410)
3. Arif Meighan [Github](https://github.com/Peptidase)