# Backend Local MySQL Setup

This project expects a MySQL 8 database running locally on port 3306.

## Reproduce the local MySQL server
Run the following command from any shell:

```bash
docker run -d \
  --name studygroup-mysql \
  -e MYSQL_ROOT_PASSWORD=rootpass \
  -e MYSQL_ROOT_HOST=% \
  -e MYSQL_DATABASE=study_group_finder \
  -p 3306:3306 \
  mysql:8.0
```

This creates a local MySQL instance that matches the values used in the project environment file.

## Project database environment

The app expects these values in `backend/.env`:

```env
DB_HOST=127.0.0.1
DB_USER=root
DB_PASSWORD=rootpass
DB_NAME=study_group_finder
DB_PORT=3306
SECRET_KEY=dev-secret-change-me
```

## Import the schema and sample data

Once the MySQL container is running, load the SQL files:

```bash
mysql -h 127.0.0.1 -u root -prootpass study_group_finder < database/study_group_finder_schema.sql
mysql -h 127.0.0.1 -u root -prootpass study_group_finder < database/study_group_finder_sample_data.sql
```

## Start the Flask backend

```bash
cd backend
python3 app.py
```

Then verify the app is running:

```bash
curl http://127.0.0.1:5000/api/health
```

Expected response:

```json
{"status":"ok","database":"connected"}
```
