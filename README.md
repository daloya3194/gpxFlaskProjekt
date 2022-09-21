# gpxFlaskProjekt

Requirements: Python 3

How to launch the project:
- Open your terminal and navigate to the projekt folder (example: cd gpxFlaskProjekt)
- Create an environment: run the following command
  - (Mac/Linux) $ python3 -m venv venv
  - (Windows)   > py -3 -m venv venv
- Activate the environment: run the following command
  - (Mac/Linux) $ . venv/bin/activate
  - (Windows)   > venv\Scripts\activate
- Install Flask: run the following command
  - $ pip install Flask
- Install all necessary Python modules and packages: run the following command
  - $ pip install -r requirements.txt
- Database  
  - The database system used is SQLite and it's already set up (File name: database.db)
  - To use MySQL:
    - Open the app.py file
    - Uncomment the line 16 and set up you MySQL connection informations
    - Comment the line 19
- Run the projekt with the command
  - $ flask run
- Open the url: http://127.0.0.1:5000/ or http://localhost:5000/ on a web browser  
