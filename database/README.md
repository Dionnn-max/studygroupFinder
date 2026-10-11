# Database setup

Folder contains the MySQL database files for the Study Group Finder

IMPORTANT PLS READD!

To make it easier on yall I recommend using

- Python with Flask
- mysql-connector-python for the MySQL connection
- i dont really know much about password hashing but I heard (from gpt) that Werkzeug is ez to use
- python-dotenv for the database credentials
- Flask sessions to remember which student is logged in
- Direct parameterized SQL queries just for Phase 1 (we don't need to add an ORM right now)

You can use the command below to install the backend packages:

pip install Flask mysql-connector-python python-dotenv

Alsoo please create a backend folder containing:

- app.py for Flask and the API routes
- db.py for opening MySQL connections
- requirements.txt (for the Python packages)
- .env.example (to show the required variables without real credentials)

Btw each developer should create their own local .env with variables like:

DB_HOST
DB_USER
DB_PASSWORD
DB_NAME=study_group_finder
SECRET_KEY

Don't push your actual .env (just add it to the .gitignore). Only .env.example should be committed.

For the passwords, use Werkzeug’s generate_password_hash() during signup and check_password_hash() during login.
The current sample accounts that I made only have placeholder hash values, so they wont be valid login accounts. We can create the working demo accounts through the signup page after registration is connected.

Last couple things, when creating a group, make sure to insesrt the group and add the creator to group_members. And then for joining, it MUST check capacity before inserting the membership. For the multi-step operations, they should be using database transactions.

P.S. pls use parameterized SQL queries rather than placing user input directly into query strings

I think what we need to get out of the way ASAP is getting Flask connected to MySQL and making a test route that properly retrieves the course list. After that, we can connect registration and login.

## Setup

1. Make sure to use MySQL Server 8.0 and MySQL Workbench.
2. Run `study_group_finder_schema.sql`.
3. Run `study_group_finder_sample_data.sql` once on a fresh database.
4. Connect Flask to the resulting study_group_finder schema.

