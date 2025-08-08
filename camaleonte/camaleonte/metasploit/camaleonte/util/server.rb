require 'fileutils'
require 'pathname'
require 'base64'

require_relative 'mediums/linux_filesystem'
require_relative 'mediums/drive_filesystem'
require_relative 'protocols/hash_protocol'
require_relative 'protocols/metadata_protocol'

# can just send as it is
def execute_command(client, args)
  if args[1] == 'execute' && args.length < 2
    return 'Proper use: execute <command>'
  end

  # concat the args befoer sending to remote
  command = args.join(' ')
  client.write(command.encode)
  client.read
end

# have to do extra processing on the received data
def download(client, args)
  if args.length != 3
    return 'Proper use: download <remote-path> <local-path>'
  end

  # send the remote command
  command = args[0, 2].join(' ')
  filename = args[2]
  client.write(command.encode)

  # process received data
  recv_data = client.read.split

  # check if operation failed
  if recv_data[0] == 'failed'
    return 'failed to download file!'
  end

  # decode received data with base64 and write to file
  filedata = Base64.decode64(recv_data[1])
  File.binwrite(filename, filedata)
  return 'successfully downloaded file!'
end

# have to do extra processing to send data
def upload(client, args)
  if args.length != 3
    return 'Proper use: upload <local-path> <remote-path>'
  end

  # send cmd + filedata + outputfile
  filedata = Base64.encode64(File.binread(args[1]))
  command = "upload #{args[2]} #{filedata}"
  client.write(command.encode)

  # check if operation failed
  status = client.read
  if status == 'failed'
    return 'failed to upload file!'
  end

  return 'successfully uploaded file!'
end
