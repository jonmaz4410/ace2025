require 'ffi-xattr'
require 'time'

require_relative 'filesystem'
require_relative '../utils'

POLL_SYNC_FILE_PERIOD = 0.0167

class LinuxFileSystem
  include HashEncoding
  include MetadataEncoding

  attr_reader :root_path

  def property_size
    256
  end

  def property_count
    10
  end

  def initialize(root_path)
    raise 'Invalid filesystem path provided!' unless File.directory?(root_path)

    root_path += '/' unless root_path.end_with?('/')
    @root_path = root_path
    super()
  end

  # FILESYSTEM SPECIFIC METHODS
  def get_all_files
    Dir.entries(@root_path)
       .select { |f| File.file?(File.join(@root_path, f)) }
       .map { |f| File.join(@root_path, f) }
       .sort
  end

  def read_content(filepath)
    File.binread(filepath)
  end

  def write_content(filepath, data)
    File.binwrite(filepath, data)
  end

  def write_properties(filepath, properties)
    xattr = Xattr.new(filepath)
    # Clear any old xattrs starting with user.hash
    xattr.list.each do |attr|
      xattr.remove(attr) if attr.start_with?('user.hash')
    end
    # Write new xattr values
    properties.each do |key, val|
      attr_name = "user.#{key}"
      xattr[attr_name] = val.encode('UTF-8')
    end
  end

  def read_properties(filepath)
    xattr = Xattr.new(filepath)
    out = {}
    xattr.each do |key, value|
      next unless key.start_with?('user.hash')

      out[key.sub('user.', '')] = value.force_encoding('UTF-8')
    end
    out
  end

  # Read signal from sync file using hash byte
  def read_signal
    sleep POLL_SYNC_FILE_PERIOD
    update_virtual_filesystem
    file_data = read_content(@sync_file)
    sig_val = get_hash_byte(file_data)
    Signal.from_i(sig_val)
  rescue StandardError
    Signal::CLEAR
  end

  def set_signal(sig)
    update_virtual_filesystem
    file_data = read_content(@sync_file)
    modified_data = set_hash_byte(file_data, sig.to_i)
    write_content(@sync_file, modified_data)
  end
end
