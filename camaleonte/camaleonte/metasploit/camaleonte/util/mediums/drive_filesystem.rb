# REVIEW: this one

require_relative 'google_api'
require_relative 'filesystem'
require 'time'

POLL_SYNC_FILE_PERIOD = 0.0167

class GoogleDriveFilesystem
  include HashEncoding
  include MetadataEncoding

  attr_reader :covert_folder_id, :conn, :sync_file, :virtual_filesystem, :channel_pos

  # total of 30 properties per file
  def property_count
    30
  end

  # each property can hold 75 bytes
  def property_size
    75
  end

  # TODO: come up with cleaner way for someone to authenticate to google drive on metasploit
  def initialize(cred_path, covert_folder_id)
    @conn = GoogleDriveAPI.new
    @conn.authenticate_drive(cred_path, 'token.yaml') # Adjust token path if needed
    @covert_folder_id = covert_folder_id
    @channel_pos = -1
    super()
  end

  # override the abstract "update_virtual_filesystem" to clear properties of sync file
  def update_virtual_filesystem
    super
    existing = @conn.get_file_properties(@sync_file)
    if existing && !existing.empty?
      clear_payload = existing.keys.map { |k| [k, nil] }.to_h
      @conn.update_properties(@sync_file, clear_payload)
    end
  end

  def get_all_files
    files = @conn.list_files(directory_id: @covert_folder_id)
    ids = files.map { |f| f.id }
    ids.sort
  end

  def write_content(file, data)
    @conn.edit_file_bytes(file, data)
  end

  def read_content(file)
    @conn.download_file_from_drive_bytes(file)
  end

  def write_properties(file, properties)
    existing = @conn.get_file_properties(file)
    to_update = {}
    existing&.each_key { |k| to_update[k] = nil } if existing
    to_update.merge!(properties) if properties
    @conn.update_properties(file, to_update) unless to_update.empty?
  end

  def read_properties(file)
    @conn.get_file_properties(file) || {}
  end

  def read_signal
    sleep POLL_SYNC_FILE_PERIOD
    props = @conn.get_file_properties(@sync_file)
    status = props['sync_status'] if props
    if status
      Signal.from_s(status)
    else
      Signal::CLEAR
    end
  end

  def set_signal(sig)
    update_virtual_filesystem
    sig_name = Signal.to_s(sig)
    @conn.update_properties(@sync_file, { 'sync_status' => sig_name })
  end

end
