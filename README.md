# discord-fury
A discord bot that creates custom voice channels and text channels on demand.

## Commands:
| Command | Description | Short |  
| ------ |   ------ | ------- | 
| `f!help` | Shows the help message with all modules | `f!h` |
|`f!setup-voice [id / mention (optional)]` | Quick setup for creation channels | - |
| `f!openroom [amount]` | Open breakout rooms with entered size | `f!opro [num]` |
| `f!closeroom` | Close breakout rooms | `f!cloro` |
| `f!set-voice [priv / pub] [channel id]` | Register a voice channel as creation channel | `f!svc [option] [id]`|
| `f!delete-settings [channel id]` | Removes a channel from the tracked list | `f!ds [id]` |

There are more commands and some more specific settings, please use the bots help command for more information.

## Functions:
### Create voice channels on demand
Watches custom configured voice channels and creates a new channel for each user that joins one of those channels._  
Supports two 'types' of channels:
* public channel - synced with category, everyone has the same rights  
* private channel - join is disabled for every member, the creator can edit the whole channel
This function also creates a 'linked' text channel which is only visible for the users that are currently in that voice chat.
* The text channel will be removed / archived - according to the set settings - when the voice channel is empty and gets deleted.

### Breakout Rooms
This bot simulates break out rooms like known from BigBlueButton or Zoom
#### Distribute members of a voice channel into smaller groups 
* All groups receive their own voice channel and linked text channel (behaviour as described above)
* Automatic creation of channels and member movement

Command: `f!openroom [amount]` - aliases: `f!opro [num]` / `f!brout [num]`

#### Collect all members
* Move all members back to your channel
* Automatic cleanup, text channels can be archived (see below)

Command: `f!closeroom` - aliases: `f!cbr` / `f!cloro`

### Customizable channel names and archive / log
There are settings to configure which channels should be watched and where text channels should be archived as well as where to log the whole process.  
Use `f!help settings` to learn more about the way configure the bot.  
`f!setup-voice [role-id (optional)]` triggers the creation of a ready configured voice category for you.

### Other useful commands
`Misc` contains some useful commands like get a ping or list all members with a certain role.
`Admin` contains a role backup command, and a few other admin commands.
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
    stdin_open: true
    tty: true
    restart: unless-stopped
```
* Start the bot with `docker-compose`
* Fill in the variables within the docker-compose file 
* The bot will restart within 30 seconds
