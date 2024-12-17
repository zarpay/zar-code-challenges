# Crypto Payment Processing Service

Welcome to the **Crypto Payment Processing Service** repository. This service is built using AWS CDK (Cloud Development Kit) and provides APIs to handle cryptocurrency payments, manage users, and retrieve rates. The service leverages AWS Lambda, API Gateway, and DynamoDB to deliver a scalable and secure solution.

## Prerequisites

1. AWS Account
2. Node.js and npm
3. AWS CDK
4. Git

## Getting Started

1. Clone the repository

2. Install dependencies

3. Bootstrap the CDK environment

    ```bash
    cdk bootstrap
    ```

4. Deploy the stack

    ```bash
    cdk deploy
    ```

## API Documentation

### Authentication

All API endpoints require an API Key for authentication. Clients must include the API Key in the x-api-key header of each request.

### Header Example

```makefile
x-api-key: YOUR_API_KEY_HERE
```

### Endpoints

The API is organized into three main resources: Users, Payments, and Rates.

```makefile
https://<api-id>.execute-api.<region>.amazonaws.com/v1
```

Replace <api-id> and <region> with your API Gateway's ID and the AWS region where it's deployed.

## Users

Manage user information.

### 1. Create User

- **Endpoint:** `/users`
- **Method:** `POST`
- **Description:** Creates a new user.

#### Request Headers

- `Content-Type: application/json`
- `x-api-key: YOUR_API_KEY`

#### Request Body

```json
{
    "email": "john.doe@example.com"
}
```

#### Responses

- **201 Created**

    ```json
    {
        "userId": "12345"
    }
    ```

- **400 Bad Request**

    ```json
    {
        "error": "Invalid email address."
    }
    ```

### 2. Get User

- **Endpoint:** `/users/{id}`
- **Method:** `GET`
- **Description:** Retrieves user information by user ID.

#### Path Parameters

- `id` (string): The unique identifier of the user.

#### Request Headers

- `x-api-key: YOUR_API_KEY`

#### Responses

- **200 OK**

    ```json
    {
        "userId": "12345",
        "username": "john_doe",
        "email": "john.doe@example.com",
        "createdAt": "2024-04-01T12:34:56Z"
    }
    ```

- **404 Not Found**

    ```json
    {
        "error": "User not found."
    }
    ```

### 3. Get User Payments

- **Endpoint:** `/users/{id}/payments`
- **Method:** `GET`
- **Description:** Retrieves all payments made by a specific user.

#### Path Parameters

- `id` (string): The unique identifier of the user.

#### Request Headers

- `x-api-key: YOUR_API_KEY`

#### Responses

- **200 OK**

    ```json
    {
        "userId": "12345",
        "payments": [
            {
                "paymentId": "pay_001",
                "amount": 0.5,
                "currency": "BTC",
                "status": "Completed",
                "createdAt": "2024-04-02T10:20:30Z"
            },
            {
                "paymentId": "pay_002",
                "amount": 1.2,
                "currency": "ETH",
                "status": "Pending",
                "createdAt": "2024-04-03T11:25:35Z"
            }
        ]
    }
    ```

- **404 Not Found**

    ```json
    {
        "error": "User not found."
    }
    ```

## Payments

Manage cryptocurrency payments.

### 1. Create Payment

- **Endpoint:** `/payments`
- **Method:** `POST`
- **Description:** Creates a new cryptocurrency payment.

#### Request Headers

- `Content-Type: application/json`
- `x-api-key: YOUR_API_KEY`

#### Request Body

```json
{
  "userId": "123",
  "amount": "150.00",
  "currency": "USD",
  "metadata": {
    "description": "Payment for services"
  }
}
```

#### Responses

- **201 Created**

    ```json
        {
            "paymentId": "1234"
        }
    ```

- **400 Bad Request**

    ```json
    {
        "error": "Invalid payment details."
    }
    ```

### 2. Get Payment

- **Endpoint:** `/payments/{id}`
- **Method:** `GET`
- **Description:** Retrieves payment details by payment ID.

#### Path Parameters

- `id` (string): The unique identifier of the payment.

#### Request Headers

- `x-api-key: YOUR_API_KEY`

#### Responses

- **200 OK**

    ```json
    {
        "paymentId": "123",
        "metadata": {
            "description": "Payment for services"
        },
        "currency": "USD",
        "updatedAt": "2024-12-15T09:53:44.435946",
        "status": "pending",
        "createdAt": "2024-12-15T09:53:44.435946",
        "amount": "150.00"
    }
    ```

- **404 Not Found**

    ```json
    {
        "error": "Payment not found."
    }
    ```

### 3. List Payments

- **Endpoint:** `/payments`
- **Method:** `GET`
- **Description:** Retrieves a list of all payments.

#### Request Headers

- `x-api-key: YOUR_API_KEY`

#### Responses

- **200 OK**

    ```json
    [
        {
            "metadata": {
                "description": "Payment for services"
            },
            "paymentId": "f8cf2796-aaf5-42d7-bf2b-b4e01e4c3b3e",
            "currency": "USD",
            "updatedAt": "2024-12-15T09:53:44.435946",
            "status": "pending",
            "createdAt": "2024-12-15T09:53:44.435946",
            "amount": "150.00"
        },
        {
            "metadata": {
                "description": "Payment for services"
            },
            "paymentId": "7b07b1cc-5f26-402f-a71d-24d3bbe03c12",
            "currency": "USD",
            "updatedAt": "2024-12-17T18:46:18.235799",
            "status": "pending",
            "createdAt": "2024-12-17T18:46:18.235799",
            "amount": "151.00"
        }
        // More payments...
    ]
    ```

## Rates

Retrieve cryptocurrency rates information.

### 1. Get Current Rates

- **Endpoint:** `/rates`
- **Method:** `GET`
- **Description:** Retrieves the current cryptocurrency rates.

#### Request Headers

- `x-api-key: YOUR_API_KEY`

#### Responses

- **200 OK**

    ```json
    {
        "timestamp": "2024-04-05T14:30:00Z",
        "rates": {
            "BTC": 50000.00,
            "ETH": 4000.00,
            "LTC": 200.00
        }
    }
    ```

### 2. Get Rates History

- **Endpoint:** `/rates/history`
- **Method:** `GET`
- **Description:** Retrieves historical cryptocurrency rates.

#### Request Headers

- `x-api-key: YOUR_API_KEY`

#### Responses

- **200 OK**

    ```json
    {
        "currency": "BTC",
        "history": [
            {
                "date": "2024-04-01",
                "rate": 48000.00
            },
            {
                "date": "2024-04-02",
                "rate": 49000.00
            },
            {
                "date": "2024-04-03",
                "rate": 50000.00
            },
            {
                "date": "2024-04-04",
                "rate": 50500.00
            },
            {
                "date": "2024-04-05",
                "rate": 50000.00
            }
        ]
    }
    ```

- **400 Bad Request**

    ```json
    {
        "error": "Invalid query parameters."
    }
    ```
