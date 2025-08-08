require 'base64'
require_relative 'protocol'
require_relative '../utils'

class MetadataProtocol
  include Protocol

  def initialize(filesystem)
    @filesystem = filesystem
  end

  def encode_file(file, data)
    property_size = @filesystem.property_size
    property_chunks = []
    (0...data.bytesize).step(property_size) do |i|
      property_chunks << data.byteslice(i, property_size)
    end

    properties = {}
    property_chunks.each_with_index do |chunk, i|
      properties["hash_#{i}"] = Base64.strict_encode64(chunk)
    end

    @filesystem.write_properties(file, properties)
  end

  def decode_file(file)
    decoded = ''.b
    properties = @filesystem.read_properties(file)
    property_count = @filesystem.property_count

    (0...property_count).each do |i|
      key = "hash_#{i}"
      break unless properties.key?(key)

      cur_chunk = Base64.decode64(properties[key])
      decoded << cur_chunk

      break if decoded.include?(TERMINATOR)
    end
    decoded
  end

  def data_per_file
    @filesystem.property_size * @filesystem.property_count
  end
end
