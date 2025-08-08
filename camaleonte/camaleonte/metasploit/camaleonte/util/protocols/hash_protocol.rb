require_relative './protocol'
require_relative '../utils'

class HashProtocol
  include Protocol

  def initialize(filesystem)
    @filesystem = filesystem
  end

  # Modify filedata until first byte of hash is data
  def encode_file(filepath, data)
    filedata = @filesystem.read_content(filepath)
    # data is expected as bytes, get integer value of first byte
    desired_byte = data.bytes.first
    filedata = set_hash_byte(filedata, desired_byte)
    @filesystem.write_content(filepath, filedata)
  end

  # Decode byte from file data
  def decode_file(filepath)
    filedata = @filesystem.read_content(filepath)
    received_byte = get_hash_byte(filedata)
    # Return as single-byte string (Ruby String is byte sequence)
    received_byte.chr
  end

  # Only encoding/decoding one byte per file
  def data_per_file
    1
  end
end
