# discord-fury
* Create custom voice channels with linked text channels on demand.  
* Add breakout rooms for discord

## Commands channels and breakout rooms:
| Command | Description | Alternative |  
| ------ |   ------ | ------- | 
| `f!help [optional: module name]` | Shows the help message with all modules / for entered module | `f!h` |
| `f!setup [id / mention (optional)]` | Quick setup for creation channels | `setup-voice` |
| `f!open [members per room]` | Open breakout rooms | `opro`, `openroom`, `break-out`, `brout` |
| `f!close` | Close breakout rooms, move members to your current channel | `cloro`, `closeroom`, `collect`, `cl` |
| `f!add [public / private] [channel id]` | Register a voice channel as tracked creation channel | `svc`, `set-voice`|

## Settings
| Command | Description | Alternative |  
| ------ |   ------ | ------- | 
| `f!set [log channel / archive category]` | Add setting for archive category and log channel | `archive`, `log` |
| `f!delete-settings [channel id]` | Removes a channel from the tracked list | `f!ds [id]` |
| `f!settings` | Get a list of all configured settings | `gs`, `get-settings` |
| `f!allow-edit [yes / no]` | Allow the creator of a public channel to edit the name, default is no | `al`, `ae` |
| `f!ping` | Check if the bot is available | |

## Functions:
### Create voice channels on demand
Watches custom configured voice channels and creates a new channel for each user that joins one of those channels._  
Supports two 'types' of channels:
* public channel - synced with category, everyone has the same permissions  
* private channel - join is disabled for every member, the creator can edit the whole channel
This function also creates a 'linked' text channel which is only visible for the users that are currently in that voice chat.
* The text channel will be removed / archived - according to the set settings - when the voice channel is empty and gets deleted.

### Breakout Rooms
This bot simulates break out rooms like known from BigBlueButton or Zoom
#### Distribute members of a voice channel into smaller groups 
* All groups receive their own voice channel and linked text channel (behaviour as described above)
* Automatic creation of channels and member movement

Command: `f!open [members per channel]` - aliases: `f!opro [num]` / `f!brout [num]`

#### Collect all members
* Move all members back to your channel
* Automatic cleanup, text channels can be archived (see below)

Command: `f!close` - aliases: `f!cbr` / `f!cloro`

### Customizable channel names and archive / log
There are settings to configure which channels should be watched and where text channels should be archived as well as where to log the whole process.  
Use `f!help settings` to learn more about the way configure the bot.  
`f!setup [role-id (optional)]` triggers the creation of a ready to use voice category for you.

### Other useful commands
`Misc` contains some useful commands like get a ping or list all members with a certain role.
`Admin` contains a command for getting a role id by entering the roles name
Use `f!help` to learn more about all modules and commands.

### Setup
Create a docker-compose file
```yaml
version: '3'
services:
  python_runtime:
    container_name: discord-fury
    image: nonchris/discord-fury
    volumes:
      - "./data:/app/data"
    environment:
      - UID=1000 
      - GID=1000
      - TOKEN=
      - PREFIX=
      - VERSION=
      - OWNER_ID=
      - OWNER_NAME=
      - CHANNEL_TRACK_LIMIT=
    stdin_open: true
    tty: true
    restart: unless-stopped
```
* Start the bot with `docker-compose`
