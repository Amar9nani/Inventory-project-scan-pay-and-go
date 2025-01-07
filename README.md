# Inventory Project

## Overview

This Django project is designed to manage an inventory system. The core functionality is housed within the `core` application.

## Project Structure

* `core/`: Contains the application logic including models, views, forms, and admin configurations for the inventory management.
* `inventory_project/`: Contains settings and configurations for the entire Django project.
* `templates/`: Holds the HTML templates for the application.
* `manage.py`: A command-line utility that lets you interact with this Django project.

## Requirements

The project dependencies are listed in `requirements.txt` . To install these dependencies, run:

```
pip install -r requirements.txt
```

## Setting Up

1. Set up your MongoDB database and update the `DATABASES` configuration in `settings.py` accordingly.

2. Run the following commands to set up the database tables:

    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

3. Optionally, create an administator user:

    ```bash
    python manage.py createsuperuser
    ```

## Running the Project

### Locally

To start the project, navigate to the project directory and run:

```
python manage.py runserver
```

This command starts a lightweight development Web server on the local machine.

### Docker Support

The project includes a `docker-compose.yml` for containerization and easy deployment. To use Docker, run:

```
docker-compose up
```

## Usage

Navigate to `http://127.0.0.1:8000` in your web browser to start using the application.

Use the admin panel to manage inventory by accessing `http://127.0.0.1:8000/admin` if you have created the root user.

## Testing

Run tests using:
```bash
python manage.py test
```

## Contributions

Contributions to this project are welcome. Please ensure to follow the established coding conventions and add tests for new features.
