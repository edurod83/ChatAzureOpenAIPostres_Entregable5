@echo off
REM Create directory structure for the project

cd /d "%~dp0"

mkdir app
mkdir app\core
mkdir app\db
mkdir app\models
mkdir app\schemas
mkdir app\services
mkdir app\routes
mkdir app\templates
mkdir app\static
mkdir app\static\css
mkdir app\static\js
mkdir alembic
mkdir alembic\versions

echo.
echo ✓ Directory structure created successfully!
pause
