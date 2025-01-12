# Daily Contribution Backend API

## Overview

The Daily Contribution Backend API is a RESTful service that provides endpoints for managing and accessing data for the Daily Contribution application. This backend is built using Python and Flask, and it connects to a MongoDB database.

## Features

- User authentication and authorization
- CRUD operations for user profiles
- Data management for Daily Contribution application
- Secure API endpoints with JWT

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Daily Contribution-org/backend.git
   ```
2. Navigate to the project directory:
   ```bash
   cd Daily Contribution-org/backend
   ```
3. Create a virtual environment:
   ```bash
   python3 -m venv venv
   ```
4. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
5. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Create a `.env` file in the root directory and add the following environment variables:

```
PORT=5000
MONGODB_URI=your_mongodb_uri
JWT_SECRET=your_jwt_secret
```

## Running the Application

To start the server make sure you're in backend directory, run:

```
python3 -m api.v1.app
```

The server will start on the port specified in the `.env` file.

## API Endpoints

### Authentication

- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login a user

### User Profiles

- `GET /api/users` - Get all user profiles
- `GET /api/users/:id` - Get a user profile by ID
- `PUT /api/users/:id` - Update a user profile by ID
- `DELETE /api/users/:id` - Delete a user profile by ID

## Contributing

We welcome from member of the organization for now

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contact

For any inquiries, please Contact:
Bilal Solih - bilalsolih60@gmail.com
