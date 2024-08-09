## Usage

### Setup

To install the required packages, run `pip install -r requirements.txt` in the root of the project.

You will need to create a `.env` file in the root of the project, setting all the variables visible in `src/constant.py`.
To do so, you will need to get credentials from the Discord Developer Portal, Imgur, Reddit, and Twitch.

### Pibot

To run the bot, open a terminal at the root of the project and run `py src/main.py`.

### Database editor

To run the database editor, open a terminal at the root of the project and run `py src/database/database_editor.py`.

Current features:
- Visualisation of the database (use the arrows to expand/collapse the tree, and use `Alt+click` to expand/collapse all).
- Edit the current values by double-clicking on them. Press Enter to validate the changes. The changes are saved automatically.
- Delete list value, or a dictionary key/value pair by right-clicking on them and selecting `Delete item`.
- Delete a leaf value and its parent by right-clicking on them and selecting `Delete associated key`.
- Add a new key/value pair to a dictionary by right-clicking on the dictionary and selecting `Add key/value pair`. Similarly, add a new value to a list by right-clicking on the list and selecting `Add value before` or `Add value after`, depending on where in the list you want the new item to be.
- Clear a non-empty collection by right-clicking on its root and selecting `Empty`.
- If the database has changed outside of the editor, you can reload it by pressing `F5`, or by clicking the `Reload` button.
- Navigate an history of up to 100 changes by pressing `Ctrl+Z` to undo and `Ctrl+Shift + Z` to redo. You can also click the `Undo` and `Redo` buttons.

## Remote setup

### To create the Docker image:
1. Go to the directory containing the `Dockerfile`
2. Run `build_prod.cmd [tag]` with `[tag]` being the version of the image
3. To push the images, run `build_prod_finish [tag]`, with `[tag]` being the version of the image

### To use this on a QNAP NAS:
1. Install the Container Station app from the App Center
2. In `Containers`, click `Create`
3. Use image `lmulot/pibot:latest` (or replace `latest` with a specific version)
4. Click `Advanced Settings`, then `Storage`, then click the arrow next to `Add Volume` and select `Bind Mount Host Path`
5. For the `Host`, select the `Pibot` directory (where the database is located)
6. For the container path, enter `/app`
7. Click `Apply` and then create the container
8. Copy the python code, database, and .env file to the `Pibot` directory
9. Start the container

### To use in a dev environment:
1. Rename `.env` to `.env_prod` and `.env_dev` to `.env`
2. To build and run, use `build_dev.cmd`
3. To stop the container, either use `/reboot` on Discord, stop the container in the `Docker Desktop` app (`Containers` page), or run `docker stop devtest`

### Acknowledgements:
This project uses [data](https://github.com/ZeGmX/PiflouzBot/blob/master/src/events/assets/) from Boris New & Christophe Pallierthe's [`Lexique`](http://www.lexique.org/) database (which can be queried at [http://www.lexique.org/shiny/openlexicon/](http://www.lexique.org/shiny/openlexicon/)) and [Gutemberg french word list](https://github.com/chrplr/openlexicon/blob/master/datasets-info/Liste-de-mots-francais-Gutenberg/README-liste-francais-Gutenberg.md).
The authors of the databases are not responsible for the content of this project.