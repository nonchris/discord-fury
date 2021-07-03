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
| `f!delete-settings [channel id]` | Removes a channel from the tracked list | `ds` |
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

## Setup
Run the bot using `docker-compose` using the image from Docker Hub `nonchris/discord-fury`.

### Environment variables
| Variable | Required | Function | Default |  
| ------ |   ------ | ------- | ------- | 
| TOKEN | yes | Token to run your bot with | - |
| POSTGRES_USER | yes | Username for database | - |
| POSTGRES_PASSWORD | yes | Password to database | - |
| POSTGRES_DB | yes | Name of the database | - |
| PREFIX | no | Prefix the bot listens to | f! |
| VERSION | no | Version displayed by bot | unknown |
| OWNER_ID | no | To mention the owner if on server | 100000000000000000 |
| OWNER_NAME | no | To give the owners name if not on server | unknown |
| CHANNEL_TRACK_LIMIT | no | Limit of tracked channels per server per type | 20 |


### Update from old v1.x.x database structure to v2.0.0
With the update to v2.0.0 the bots internal database structure was rewritten using SQLAlchemy.  
The new version also uses postgres instead of sqlite.  
It's suggested to upgrade since new features will only be developed for v2.

#### Migrate your database
Add those environment variables to your compose file.  
The container will start the script `migrate_to_alchemy.py` which handles the migration process.  
Stop the container when the script is finished and remove those parameters to run the container as usual. 
```yaml
      - run=migrate_to_alchemy.py
      - OLD_DB_PATH=data/fury1.db
```
You need to move the data/ folder if you copied the latest docker-compose file.
