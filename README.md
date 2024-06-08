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

### To install the chess database 
This may require a bit of RAM to do the actual splitting.
This once step must be done before running the bot, it's a pre-processing step.
```
cd chess_database; python download_chess_database.py; cd ..
```

### Acknowledgements:
This project uses [data](https://github.com/ZeGmX/PiflouzBot/blob/master/src/events/assets/french_words.csv) from Boris New & Christophe Pallierthe's [`Lexique`](http://www.lexique.org/) database, which is licensed under the [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) license. The database can be queried at [http://www.lexique.org/shiny/openlexicon/](http://www.lexique.org/shiny/openlexicon/). The authors of the database are not responsible for the content of this project.

The chess database is the lichess open database, that can be found at https://database.lichess.org/#puzzles
