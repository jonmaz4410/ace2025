import os
import timeit

ITERATIONS = 50
TRIALS = 20

def time_crc32(test_cnt: int, file_size: str) -> float:
    res = timeit.timeit(
        stmt=f"zlib.crc32(FILES[\"{file_size}\"])",
        setup="import zlib; from __main__ import FILES",
        number=test_cnt
    )
    return res

def time_xxhash(test_cnt: int, file_size: str) -> float:
    res = timeit.timeit(
        stmt=f"xxhash.xxh3_64(FILES[\"{file_size}\"]).digest()",
        setup="import xxhash; from __main__ import FILES",
        number=test_cnt
    )
    return res

# hash benchmark
# FILE_SIZES = {
#     "1 BYTE": 1,
#     "1 KB": 1000,
#     "1 MB": 1000000,
#     "10 MB": 10000000,
#     "100 MB": 100000000,
#     "1 GB": 1000000000
# }
# FILES = {
#     file_size : os.urandom(FILE_SIZES[file_size])
#     for file_size in FILE_SIZES
# }
# print(f"Tests will be repeated: {ITERATIONS}\n")
# for size in FILE_SIZES:
#     print(f"TESTING {size} SIZED INPUT:")
#     for i in range(TRIALS):
#         res = time_crc32(ITERATIONS, size)
#         print(f"Test {i}: {res} seconds")
#     print()
