
# Future Work

This section details the potential future work that could be carried on in future development. We wanted to implement and fix majority of these issues but couldnt due to time constraints of ACE.  

## Analysis

There are several forms of analysis that need to be performed to see if the covert channel is beneficial to use in a red teaming enviroment:

- We need to calculate the probability of deadlocks when there is a small number of files in medium. Deadlocks occur when both the server and payload/client are waiting for the read signal. The reason a small number of files produces this effect is because when the writer is completed, it normally waits for a signal. In the timing of the writer sending the CLEAR to waiting, the reader would have already obtained the full message and sent a clear signal before the writer can begin watching the sync file for the signal. This makes both endpoints halt and wait for eachother which breaks communication.

- We need to measure the bandwidth based on number of files available and if there is an optimal number of files needed for transmission and if that depends on the protocol used. In the `evaluation` folder on the python code of the repository there is an `ipynb` file that has an outline of the code that automatically spings up a subprocess to send and recieve information.  

## General Areas of Improvement

The following points are areas that could use further development time. 

- Decrease the chance of a deadlock occuring
  - This happens when there less files in the filesystem
  - In other cases, use a sequence number + a timeout. When timeout is reached, client/server re-send signal depending on current seq number.
- Introduce a method to free filesystem space for clients who have disconnected. Currently we only add clients and are able to reset the filesystem by clearing the configuration file. Resetting everything through this lets us
  - Can possibly be implemented with a heartbeat system
- Introduce jitter (modulating file modification time) to increase covertness
- Update file modification for hash protocol
  - Introduce support for more types of files instead of just ASCII
  - Instead of infinitely adding whitespace, methodically add and remove to get desired hash
- Increase robustness by accounting for case where files are deleted in the middle of transmissions
- Recursively search inside directories for usable files instead of just in 1 directory
- Also add a timeout for command execution, it would be really bad to lose a session due to a hanging command.
