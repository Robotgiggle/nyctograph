To set up the project:
- Run `python -m venv .venv` to create a virtual environment folder
- Your IDE may automatically activate the venv, if not you can manually activate it with `.venv\Scripts\Activate.ps1` on Windows or `source .venv/bin/activate` on Mac/Linux
- Run `python -m pip install -r requirements.txt` to install all the packages from `requirements.txt` into the venv
- Move into the `app` directory with `cd app` (you will probably need to do this every time you start your IDE)
- You should now be set up and ready to run the project
- To deactivate the venv, run `deactivate`

To start the server:
- Run `fastapi dev main.py` for developer mode
- Run `fastapi run main.py` for production mode
- The web app should then be accessible at http://127.0.0.1:8000