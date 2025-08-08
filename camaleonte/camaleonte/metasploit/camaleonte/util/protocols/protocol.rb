require 'time'

require_relative '../utils'
require_relative '../mediums/filesystem'

CONNECTION_POLL_DELAY = 0.1

module Protocol
  attr_reader :filesystem

  def initialize(filesystem)
    @filesystem = filesystem
  end

  # Abstract methods - should be overridden in subclass
  def encode_file(file, data)
    raise NotImplementedError, "#{self.class} must implement encode_file"
  end

  def decode_file(file)
    raise NotImplementedError, "#{self.class} must implement decode_file"
  end

  def data_per_file
    raise NotImplementedError, "#{self.class} must implement data_per_file"
  end

  # Initial connection methods
  def connect
    current_count = @filesystem.get_client_count
    @filesystem.set_client_count(current_count + 1)
    @filesystem.set_channel_pos(current_count)
    @filesystem.update_virtual_filesystem
    @filesystem.set_signal(Signal::CLEAR)
  end

  def wait_for_connection
    current_count = @filesystem.get_client_count
    sleep CONNECTION_POLL_DELAY while current_count == @filesystem.get_client_count
    @filesystem.set_channel_pos(current_count)
    @filesystem.update_virtual_filesystem
    @filesystem.set_signal(Signal::CLEAR)
  end

  # Transmission methods
  def read
    data = ''.b
    loop do
      # wait for a DONE signal
      while @filesystem.read_signal != Signal::DONE
      end
      # read curent batch
      current_batch = ''.b
      @filesystem.get_files.each do |file|
        current_batch << decode_file(file)
        break if current_batch.include?(TERMINATOR)
      end
      # puts "RECEIVED BATCH: #{current_batch.length}" # DEBUG
      # puts current_batch.inspect # DEBUG
      received_hash = current_batch.byteslice(0, CHECKSUM_HASH_SIZE)
      calculated_hash = checksum_hash(current_batch.byteslice(CHECKSUM_HASH_SIZE..-1))
      if received_hash == calculated_hash
        data << current_batch.byteslice(CHECKSUM_HASH_SIZE..-1)
        @filesystem.set_signal(Signal::ACK)
      else
        @filesystem.set_signal(Signal::NACK)
      end

      if data.include?(TERMINATOR)
        data = data.split(TERMINATOR, 2)[0]
        break
      end
    end
    data
  end

  def write(data)
    # wait until signal cleared
    while @filesystem.read_signal != Signal::CLEAR
    end

    payload = data + TERMINATOR
    files = @filesystem.get_files
    total_files = files.size

    data_per_batch = data_per_file * total_files - CHECKSUM_HASH_SIZE
    raise 'NOT ENOUGH FILES' if data_per_batch <= 0

    batches = []
    i = 0
    while i < payload.bytesize
      batches << payload.byteslice(i, data_per_batch)
      i += data_per_batch
    end

    cur_batch_i = 0
    while cur_batch_i < batches.size
      batch = batches[cur_batch_i]
      # puts "Sent Hash: #{checksum_hash(batch).inspect}" # DEBUG
      batch = checksum_hash(batch) + batch

      file_chunks = []
      i = 0
      while i < batch.bytesize
        file_chunks << batch.byteslice(i, data_per_file)
        i += data_per_file
      end

      file_chunks.each_with_index do |chunk, idx|
        # puts "writing #{chunk.inspect} to #{files[idx]}" # DEBUG
        encode_file(files[idx], chunk)
      end

      # puts "SENT BATCH: #{batch.bytesize}" # DEBUG
      # puts batch.inspect # DEBUG
      @filesystem.set_signal(Signal::DONE)

      loop do
        sig = @filesystem.read_signal
        if sig == Signal::ACK
          cur_batch_i += 1
          break
        elsif sig == Signal::NACK
          break
        end
      end
    end
    @filesystem.set_signal(Signal::CLEAR)
  end
end
