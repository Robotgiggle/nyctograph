To set up the project:
- Run `python -m venv .venv` to create a virtual environment folder.
- Your IDE may automatically activate the venv, if not you can manually activate it with `.venv\Scripts\Activate.ps1` on Windows or `source .venv/bin/activate` on Mac/Linux.
- Run `python -m pip install -r requirements.txt` to install all the packages from `requirements.txt` into the venv.
- Set up your environment variables (more info can be found in `config.py`) and provide appropriate values.
- You should now be set up and ready to run the project.
- To deactivate the venv, run `deactivate`.

To set up the database:
- For local development, the app needs access to a PostgreSQL server. You can download and install PostgreSQL [here](https://www.postgresql.org/download/).
- Once you have the PostgreSQL server running, create a database and get the connection URL.
- Put the connection URL into the `DATABASE_URL` environment variable to allow the app to connect.
- On startup, the app will automatically run the database setup script (found in `build_db.py`) to set up the tables and create an admin account.
- You can also manually re-run the script (`python -m app.build_db`) to reset the database if you don't want to manually remove testing data.

To start the server:
- Run `fastapi dev app/main.py` for developer mode
- Run `fastapi run app/main.py` for production mode
- The web app should then be accessible at http://127.0.0.1:8000

To deploy the live site:
- Pushing changes to the `live` branch will automatically trigger a redeploy of the live site on Railway.
- For manual redeployment and other tweaks, the Railway dashboard can be found [here](<https://railway.com/project/bb597379-dfb0-47b8-80a8-d0b17b927329?environmentId=65ffdf9d-b41b-4189-8832-746fad699016>), assuming you have access.