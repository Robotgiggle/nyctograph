To set up the project:
- Run `python -m venv .venv` to create a virtual environment folder
- Your IDE may automatically activate the venv, if not you can manually activate it with `.venv\Scripts\Activate.ps1` on Windows or `source .venv/bin/activate` on Mac/Linux
- Run `python -m pip install -r requirements.txt` to install all the packages from `requirements.txt` into the venv
- You should now be set up and ready to run the project
- To deactivate the venv, run `deactivate`

To set up the database:
- The app currently expects to find a PostgreSQL database running locally on port 5432. You can download and install PostgreSQL [here](https://www.postgresql.org/download/).
- Once you have a PostgreSQL server running, you'll need to create a database named `nyctograph`, and ensure that it has a user named `postgresql` with the password `opensesame`.
- Assuming the above conditions are met, the app should be able to connect to the database. To set up the tables (and create an admin user account), run `python -m app.build_db` from *outside* the `app` directory. You can also run the same script to reset the database if you don't want to manually remove testing data.

To start the server:
- Move into the `app` directory with `cd app` (you may need to do this every time you start your IDE)
- Run `fastapi dev main.py` for developer mode
- Run `fastapi run main.py` for production mode
- The web app should then be accessible at http://127.0.0.1:8000