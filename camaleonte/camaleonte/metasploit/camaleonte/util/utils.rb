# check if all the hashes are same on python/ruby

require 'zlib'
require 'base64'

TERMINATOR = "\x04".b
CHECKSUM_HASH_SIZE = 4

# Return least-significant byte of CRC32
def get_hash_byte(data)
  Zlib.crc32(data) % 256
end

# Modify data until its CRC32 % 256 == desired
# NOTE: This assumes data is binary-safe and whitespace-safe
def set_hash_byte(data, desired)
  data = data.dup
  data += ' '.b until get_hash_byte(data) == desired
  data
end

# Return CRC32 hash as 4-byte little-endian
def crc32_hash(data)
  [Zlib.crc32(data)].pack('V') # "V" = little-endian 32-bit unsigned int
end

# Return base64-encoded 4-byte CRC32 hash, truncated
def checksum_hash(data)
  Base64.strict_encode64(crc32_hash(data))[0...CHECKSUM_HASH_SIZE]
end
