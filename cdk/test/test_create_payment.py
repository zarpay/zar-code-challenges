import sys
import json
import os
import pytest
from unittest.mock import patch
from moto import mock_aws
import boto3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from lambdas.payments.create_payment import handler


@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    os.environ["MAIN_TABLE"] = "CryptoPaymentTable"


@pytest.fixture
def dynamodb_table(aws_credentials):
    """Create a mocked DynamoDB table."""
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.create_table(
            TableName="CryptoPaymentTable",
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "pk", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
                {"AttributeName": "paymentId", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "paymentId-index",
                    "KeySchema": [
                        {"AttributeName": "paymentId", "KeyType": "HASH"},
                        {"AttributeName": "sk", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        yield table


def test_create_payment_success(dynamodb_table):
    """Test successful creation of a payment with valid inputs."""
    user_id = "user-123"
    event = {
        "body": json.dumps(
            {
                "userId": user_id,
                "amount": "150.00",
                "currency": "USD",
                "metadata": {"description": "Payment for services"},
            }
        )
    }
    response = handler(event, {})

    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert "paymentId" in body
    payment_id = body["paymentId"]

    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table("CryptoPaymentTable")

    response = table.scan(
        FilterExpression=boto3.dynamodb.conditions.Attr("paymentId").eq(payment_id)
    )
    assert "Items" in response
    assert len(response["Items"]) == 1
    item = response["Items"][0]
    assert item["pk"] == user_id
    assert item["paymentId"] == payment_id
    assert item["amount"] == "150.00"
    assert item["currency"] == "USD"
    assert item["status"] == "pending"
    assert item["metadata"] == {"description": "Payment for services"}
    assert "createdAt" in item
    assert "updatedAt" in item


def test_create_payment_missing_user_id(dynamodb_table):
    """Test creation of a payment without providing userId."""
    event = {
        "body": json.dumps(
            {
                # 'userId' is missing
                "amount": "150.00",
                "currency": "USD",
                "metadata": {"description": "Payment for services"},
            }
        )
    }
    response = handler(event, {})
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "message" in body
    assert body["message"] == "Invalid or missing userId."


def test_create_payment_invalid_user_id(dynamodb_table):
    """Test creation of a payment with an invalid userId type."""
    event = {
        "body": json.dumps(
            {
                "userId": 123,  # Should be a string
                "amount": "150.00",
                "currency": "USD",
                "metadata": {"description": "Payment for services"},
            }
        )
    }
    response = handler(event, {})
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "message" in body
    assert body["message"] == "Invalid or missing userId."


def test_create_payment_missing_amount(dynamodb_table):
    """Test creation of a payment without providing amount."""
    event = {
        "body": json.dumps(
            {
                "userId": "user-123",
                # 'amount' is missing
                "currency": "USD",
                "metadata": {"description": "Payment for services"},
            }
        )
    }
    response = handler(event, {})
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "message" in body
    assert body["message"] == "Invalid or missing amount."


def test_create_payment_invalid_amount_type(dynamodb_table):
    """Test creation of a payment with an invalid amount type."""
    event = {
        "body": json.dumps(
            {
                "userId": "user-123",
                "amount": {"value": 150},  # Should be int, float, or str
                "currency": "USD",
                "metadata": {"description": "Payment for services"},
            }
        )
    }
    response = handler(event, {})
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "message" in body
    assert body["message"] == "Invalid or missing amount."


def test_create_payment_missing_currency(dynamodb_table):
    """Test creation of a payment without providing currency."""
    event = {
        "body": json.dumps(
            {
                "userId": "user-123",
                "amount": "150.00",
                # 'currency' is missing
                "metadata": {"description": "Payment for services"},
            }
        )
    }
    response = handler(event, {})
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "message" in body
    assert body["message"] == "Invalid or missing currency."


def test_create_payment_invalid_currency_type(dynamodb_table):
    """Test creation of a payment with an invalid currency type."""
    event = {
        "body": json.dumps(
            {
                "userId": "user-123",
                "amount": "150.00",
                "currency": 123,  # Should be a string
                "metadata": {"description": "Payment for services"},
            }
        )
    }
    response = handler(event, {})
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "message" in body
    assert body["message"] == "Invalid or missing currency."


def test_create_payment_invalid_currency_format(dynamodb_table):
    """Test creation of a payment with an invalid currency format."""
    event = {
        "body": json.dumps(
            {
                "userId": "user-123",
                "amount": "150.00",
                "currency": "US",  # Invalid format, should be 3 uppercase letters
                "metadata": {"description": "Payment for services"},
            }
        )
    }
    response = handler(event, {})
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "message" in body
    assert body["message"] == "Invalid currency format."


def test_create_payment_dynamodb_failure(aws_credentials, dynamodb_table):
    """Test handling of DynamoDB put_item failure."""
    with patch("boto3.resource") as mock_resource:
        mock_dynamodb = mock_resource.return_value
        mock_table = mock_dynamodb.Table.return_value
        mock_table.put_item.side_effect = Exception("DynamoDB failure")

        event = {
            "body": json.dumps(
                {
                    "userId": "user-123",
                    "amount": "150.00",
                    "currency": "USD",
                    "metadata": {"description": "Payment for services"},
                }
            )
        }
        response = handler(event, {})
        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "message" in body
        assert body["message"] == "Internal server error."
