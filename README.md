# SwiftAza Backend API

## Overview

The SwiftAza Backend API is a RESTful service that provides endpoints for managing and accessing data for the SwiftAza application. This backend is built using Node.js and Express, and it connects to a MongoDB database.

## Features

- User authentication and authorization
- CRUD operations for user profiles
- Data management for SwiftAza application
- Secure API endpoints with JWT

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/SwiftAza-org/backend.git
   ```
2. Navigate to the project directory:
   ```bash
   cd backend
   ```
3. Install the dependencies:
   ```bash
   npm install
   ```

## Configuration

Create a `.env` file in the root directory and add the following environment variables:

```
PORT=3000
MONGODB_URI=your_mongodb_uri
JWT_SECRET=your_jwt_secret
```

## Running the Application

To start the server, run:

```bash
npm start
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

We welcome contributions! Please read our [Contributing Guidelines](CONTRIBUTING.md) for more details.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contact

For any inquiries, please Contact:
Bilal Solih - bilalsolih60@gmail.com
