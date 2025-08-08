require 'msf/core'
require 'rex/ui/text/shell'

require_relative 'util/server'

module Msf
  module Sessions
    class FilesystemSession
      include Msf::Session::Basic
      include Msf::Session::Interactive

      attr_accessor :shell, :interacting, :type, :desc,
                    :arch, :name, :platform, :tunnel_peer, :tunnel_local,
                    :alive, :sname

      # create a wrapper for Shell module so we can instantiate a class
      class FilesystemShell
        include Rex::Ui::Text::Shell
      end

      def initialize(client, opts)
        super
        @client = client
        @interacting = false
        @alive = true

        @type = "#{opts['filesystem']}-#{opts['protocol']}"
        @desc = 'Fileystem based covert channel'
        @arch = nil
        @platform = nil
        @tunnel_local = 'local'
        @tunnel_peer = opts['tunnel_peer']

        @name = "fscc-#{opts['filesystem']}#{rand(1000)}-#{@client.filesystem.channel_pos}"
        @sname = @name

        @in_stream = Rex::Ui::Text::Input::Stdio.new
        @out_stream = Rex::Ui::Text::Output::Stdio.new
        @shell = FilesystemShell.new(name)
        @shell.init_ui(@in_stream, @out_stream)
      end

      # Start the interactive shell loop
      def _interact
        self.interacting = true
        while interacting
          shell.run do |line|
            case line.strip
            when 'exit', 'quit'
              do_exit
              break
            when 'background', 'bg'
              do_background
              break
            else
              handle_command(line)
            end
            false # continue loop unless break above
          end
          print_line("\n")
        end
      end

      # Handle exiting the session
      def do_exit
        print_bad('Exiting session...')
        self.interacting = false
        self.alive = false
        framework.sessions.deregister(self) # this calls cleanup
      end

      def cleanup
        # send quit command to client that times out after 5 seconds
        Timeout.timeout(5) do
          @client.write('quit')
        end
      rescue Timeout::Error
        print_bad('Timeout while sending quit command.')
      end

      # Handle backgrounding the session
      def do_background
        print_status('Backgrounding session...')
        self.interacting = false
      end

      def _suspend
        print("Suspend: use the \'background\' command to suspend\n")
      end

      # Process user command
      def handle_command(line)
        args = line.strip.split
        case args[0]
        # send the command as it is, no extra processing needed
        when 'ls', 'cd', 'execute', 'cat', 'ps', 'pwd'
          out = execute_command(@client, args)
        when 'download'
          out = download(@client, args)
        when 'upload'
          out = upload(@client, args)
        else
          out = 'Invalid command!'
        end
        print_line(out)
      end

      ### Descriptive Methods
      def alive?
        @alive
      end

      def interactive?
        true
      end
    end
  end
end
