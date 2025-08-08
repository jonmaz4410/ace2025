require 'googleauth'
require 'googleauth/stores/file_token_store'
require 'google/apis/drive_v3'
require 'stringio'
require 'time'

class GoogleDriveAPI
  SCOPES = [Google::Apis::DriveV3::AUTH_DRIVE]

  def initialize
    @service_worker = Google::Apis::DriveV3::DriveService.new
  end

  # --- Authentication ---
  def authenticate_drive(credentials_path, token_path, user_id = 'default')
    client_id = Google::Auth::ClientId.from_file(credentials_path)
    token_store = Google::Auth::Stores::FileTokenStore.new(file: token_path)
    authorizer = Google::Auth::UserAuthorizer.new(client_id, SCOPES, token_store)
    credentials = authorizer.get_credentials(user_id)

    if credentials.nil?
      url = authorizer.get_authorization_url(base_url: 'urn:ietf:wg:oauth:2.0:oob')
      puts "Open this URL in your browser and enter the code:\n#{url}"
      code = gets.chomp
      credentials = authorizer.get_and_store_credentials_from_code(
        user_id: user_id, code: code, base_url: 'urn:ietf:wg:oauth:2.0:oob'
      )
    end

    @service_worker.authorization = credentials
  end

  # --- File Upload/Download ---
  def upload_file_to_drive(file_path, destination_id)
    raise 'Authenticate first.' unless @service_worker
    raise "No such file: #{file_path}" unless File.exist?(file_path)

    metadata = Google::Apis::DriveV3::File.new(
      name: File.basename(file_path),
      parents: [destination_id]
    )

    @service_worker.create_file(
      metadata,
      upload_source: file_path,
      content_type: 'application/octet-stream'
    )
  end

  def download_file_from_drive_bytes(target_id)
    raise 'Authenticate first.' unless @service_worker

    buffer = StringIO.new
    @service_worker.get_file(target_id, download_dest: buffer)
    buffer.rewind
    buffer.read
  end

  def download_file_from_drive(destination, target_id)
    data = download_file_from_drive_bytes(target_id)
    File.open(destination, 'wb') { |f| f.write(data) }
  end

  # --- Metadata ---
  def get_file_properties(target_id)
    raise 'Authenticate first.' unless @service_worker

    file = @service_worker.get_file(target_id, fields: 'appProperties')
    file.app_properties || {}
  end

  def update_properties(file_id, properties)
    raise 'Authenticate first.' unless @service_worker

    file = Google::Apis::DriveV3::File.new(app_properties: properties)
    @service_worker.update_file(file_id, file, fields: 'id,appProperties')
  end

  def update_file_properties(file_id, properties)
    update_properties(file_id, properties)
  end

  def update_properties_batch(file_properties_map, batch_size: 500, max_retries: 3, delay: 1.0)
    raise 'Authenticate first.' unless @service_worker

    items = file_properties_map.to_a

    items.each_slice(batch_size).with_index(1) do |batch_items, batch_index|
      tries = 0
      begin
        tries += 1
        @service_worker.batch do |batch|
          batch_items.each do |file_id, props|
            file = Google::Apis::DriveV3::File.new(app_properties: props)
            batch.add(
              @service_worker.update_file(file_id, file, fields: 'id,appProperties'),
              request_id: file_id
            ) do |res, err|
              # puts "[ERROR] #{file_id}: #{err}" if err
            end
          end
        end
      rescue Google::Apis::ServerError => e
        if tries < max_retries
          # puts "[RETRY] Batch ##{batch_index} attempt #{tries} failed, retrying in #{delay}s..."
          sleep delay
          retry
        else
          # puts "[FAIL] Batch ##{batch_index} failed after #{max_retries} attempts."
        end
      end
    end
  end

  def get_properties_batch(file_ids)
    raise 'Authenticate first.' unless @service_worker

    out = {}
    @service_worker.batch do |batch|
      file_ids.each do |fid|
        batch.add(@service_worker.get_file(fid, fields: 'id,appProperties'), request_id: fid) do |file, err|
          out[file.id] = file.app_properties || {} if file && err.nil?
        end
      end
    end
    out
  end

  def clear_all_file_properties_in_folder(folder_id)
    raise 'Authenticate first.' unless @service_worker

    count = 0
    page_token = nil
    loop do
      resp = @service_worker.list_files(
        q: "'#{folder_id}' in parents and trashed=false",
        fields: 'nextPageToken, files(id,name,appProperties)',
        page_size: 1000,
        page_token: page_token
      )
      resp.files.each do |file|
        props = file.app_properties || {}
        unless props.empty?
          update_properties(file.id, {}) # clear all by overwriting
          count += 1
        end
      end
      page_token = resp.next_page_token
      break if page_token.nil?
    end
    count
  end

  # --- Listing and Watching ---
  def list_files(directory_id: nil, filename: nil, ignore_directories: false)
    raise 'Authenticate first.' unless @service_worker

    query_parts = ['trashed = false']
    query_parts << "'#{directory_id}' in parents" if directory_id
    query_parts << "name = '#{filename}'" if filename
    query_parts << "mimeType != 'application/vnd.google-apps.folder'" if ignore_directories
    query = query_parts.join(' and ')

    files = []
    page_token = nil
    loop do
      resp = @service_worker.list_files(
        q: query,
        order_by: 'name',
        page_size: 1000,
        fields: 'nextPageToken, files(id,name,mimeType,parents)',
        page_token: page_token
      )
      files.concat(resp.files)
      page_token = resp.next_page_token
      break if page_token.nil?
    end
    files
  end

  def watch_file(target_id, poll_interval = 0.1, timeout = 300)
    raise 'Authenticate first.' unless @service_worker

    start_time = Time.now
    meta = @service_worker.get_file(target_id, fields: 'modifiedTime,trashed')
    last_mod = meta.modified_time

    loop do
      return false if Time.now - start_time > timeout

      sleep(poll_interval)
      meta = @service_worker.get_file(target_id, fields: 'modifiedTime,trashed')
      return true if meta.trashed || meta.modified_time != last_mod
    end
  end

  # --- Edit Files ---
  def edit_file(target_id, new_file_path)
    raise 'Authenticate first.' unless @service_worker

    res = @service_worker.update_file(
      target_id,
      nil,
      upload_source: new_file_path,
      content_type: 'application/octet-stream',
      fields: 'id'
    )
  end

  def edit_file_bytes(target_id, bytes_)
    raise 'Authenticate first.' unless @service_worker

    buffer = bytes_.is_a?(StringIO) ? bytes_ : StringIO.new(bytes_)
    res = @service_worker.update_file(
      target_id,
      nil,
      upload_source: buffer,
      content_type: 'application/octet-stream',
      fields: 'id'
    )
  end

  # --- Delete/Restore/Trash ---
  def delete_file(target_id)
    raise 'Authenticate first.' unless @service_worker

    @service_worker.delete_file(target_id)
  end

  def restore_file(target_id)
    raise 'Authenticate first.' unless @service_worker

    file = Google::Apis::DriveV3::File.new(trashed: false)
    @service_worker.update_file(target_id, file, fields: 'id')
  end

  def empty_bin
    raise 'Authenticate first.' unless @service_worker

    @service_worker.empty_trash
  end
end
