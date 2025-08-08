require_relative '../utils'

# enum like Signal object
module Signal
  CLEAR = 0
  ACK = 1
  NACK = 2
  DONE = 3

  VALUES = {
    clear: CLEAR,
    ack: ACK,
    nack: NACK,
    done: DONE
  }.freeze
  NAMES = VALUES.invert.freeze

  # converts numeric int value to signal value
  # (mostly pointless except any non signal number returns as CLEAR)
  def self.from_i(val)
    if val.between?(0, 3)
      return val
    else
      return 0 # default to returning clear
    end
  end

  # converts int value to string representation of signal (uppercase)
  def self.to_s(val)
    name = NAMES[val]
    return 'CLEAR' unless name # default to returning clear

    name.to_s.upcase
  end

  # converts string representation of signal to int value (for e.g. "CLEAR" -> 0)
  def self.from_s(val)
    return CLEAR unless val.is_a?(String) || val.is_a?(Symbol)

    key = val.to_s.downcase.to_sym
    VALUES[key] || CLEAR # default to returning clear
  end
end

# Abstract Filesystem base
module Filesystem
  attr_accessor :channel_pos, :config_file, :virtual_filesystem, :sync_file

  def initialize
    @channel_pos = -1
    @client_count = 0
    @config_file = get_all_files[0]
  end

  # VIRTUAL FILESYSTEM METHODS
  def get_files
    update_virtual_filesystem
    @virtual_filesystem[1..] || []
  end

  def get_client_count
    config_data = read_content(@config_file)
    get_hash_byte(config_data)
  end

  def set_client_count(cnt)
    config_data = read_content(@config_file)
    modified_config = set_hash_byte(config_data, cnt)
    write_content(@config_file, modified_config)
  end

  def set_channel_pos(pos)
    @channel_pos = pos
  end

  def update_virtual_filesystem
    raise 'Didn’t connect or wait for connection!' if @channel_pos == -1

    # only update if client count changes
    new_client_count = get_client_count
    if @client_count == new_client_count
      return
    end

    @client_count = new_client_count

    # calculate upper and lower bounds
    all_files = get_all_files
    a = 1
    r = 2
    geometric_sequence = if @client_count <= a
                           1
                         else
                           exponent = (Math.log(@client_count.to_f / a) / Math.log(r)).ceil
                           a * (r**exponent)
                         end

    files_per_vfs = (all_files.size - 1) / geometric_sequence
    files_per_vfs = files_per_vfs.floor
    start_index = @channel_pos * files_per_vfs + 1
    # puts "#{files_per_vfs}, #{start_index}, #{@channel_pos}" # DEBUG

    @virtual_filesystem = all_files[start_index...(start_index + files_per_vfs)]
    @sync_file = @virtual_filesystem[0]
    set_signal(Signal::CLEAR)
    # puts "SYNC FILE: #{@sync_file}" # DEBUG
  end

  # ABSTRACT METHODS (raise NotImplementedError)
  def get_all_files
    raise NotImplementedError, "#{self.class} must implement get_all_files"
  end

  def set_signal(_sig)
    # update_virtual_filesystem
    raise NotImplementedError, "#{self.class} must implement set_signal"
  end

  def read_signal
    # sleep POLL_SYNC_FILE_PERIOD
    # update_virtual_filesystem
    raise NotImplementedError, "#{self.class} must implement read_signal"
  end

  def write_content(_file, _data)
    raise NotImplementedError, "#{self.class} must implement write_content"
  end

  def read_content(_file)
    raise NotImplementedError, "#{self.class} must implement read_content"
  end
end

# Hash-based encoder inherits from Filesystem
module HashEncoding
  include Filesystem
  # implement protocol-specific methods later
end

# Metadata-based encoder
module MetadataEncoding
  include Filesystem
  def property_size
    raise NotImplementedError, "#{self.class} must define PROPERTY_SIZE"
  end

  def property_count
    raise NotImplementedError, "#{self.class} must define PROPERTY_COUNT"
  end

  def write_properties(_file, _props)
    raise NotImplementedError, "#{self.class} must implement write_properties"
  end

  def read_properties(_file)
    raise NotImplementedError, "#{self.class} must implement read_properties"
  end
end
