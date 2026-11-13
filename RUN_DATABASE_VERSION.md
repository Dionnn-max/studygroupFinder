# Run the database-connected website

## 1. Start MySQL

Use MySQL Server 8.0 or the Docker command documented in `backend/README.md`.

## 2. Import the database

From the project root:

```bash
mysql -h 127.0.0.1 -u root -p study_group_finder < database/study_group_finder_schema.sql
mysql -h 127.0.0.1 -u root -p study_group_finder < database/study_group_finder_sample_data.sql
```

Run the sample data only once on a fresh database.

## 3. Create the environment file

Copy `backend/.env.example` to `backend/.env` and replace the password with your MySQL password.

## 4. Install Python packages

```bash
python3 -m pip install -r backend/requirements.txt
```

## 5. Start Flask

From the project root:

```bash
python3 backend/app.py
```

## 6. Open the website

Open this URL in the browser:

```text
http://127.0.0.1:5000/login.html
```

Do not double-click the HTML files and do not use a separate Live Server port. Flask must serve the pages so login sessions work correctly.

## 7. Test database persistence

Create a new account using an `@sdsu.edu` email, add a course, and create a group. Then refresh the page and check MySQL Workbench:

```sql
USE study_group_finder;
SELECT * FROM students;
SELECT * FROM enrollments;
SELECT * FROM study_groups;
SELECT * FROM group_members;
SELECT * FROM group_meeting_times;
```

## Connected Phase 1 functions

- Registration and login
- Student session and logout
- Add and remove courses
- Create a group and save meeting times
- Search database groups
- View group details and members
- Join and leave open groups
- View groups the student leads or joined
- Edit basic profile information

The existing Phase 2 preference controls remain visual-only because the current database schema has no preference tables or columns.
