import os
import random

FILESYSTEM_PATH = "fileshare/"

with open("helpers/wordlist.txt") as wordlist:
    words = wordlist.read().splitlines() + ['\n']

# delete all files in filesystem to refresh
paths = [FILESYSTEM_PATH + x for x in os.listdir(FILESYSTEM_PATH)]
to_remove = [x for x in paths if os.path.isfile(x)]
for path in to_remove:
    os.remove(path)

# loop through all letters 1-10
for i in range(10):
    for x in range(97, 123): # a-z
        file_path = FILESYSTEM_PATH + chr(x) + str(i) + ".txt"
        # generate random string
        data = " ".join(
            [
                random.choice(words)
                for i in range(random.randint(1, 256))
            ]
        )
        with open(file_path, 'w') as fil:
            fil.write(data)