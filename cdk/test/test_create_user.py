import sys
import json
import os
import pytest
from unittest.mock import patch
from moto import mock_aws
import boto3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from lambdas.users.create_user import handler


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


def test_create_user_success(dynamodb_table):
    """Test successful creation of a user with valid email."""
    event = {"body": json.dumps({"email": "john.doe@example.com"})}
    response = handler(event, {})
    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert "userId" in body
    user_id = body["userId"]

    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table("CryptoPaymentTable")
    response = table.get_item(Key={"pk": user_id, "sk": f"USER#{user_id}"})
    assert "Item" in response
    item = response["Item"]
    assert item["pk"] == user_id
    assert item["sk"] == f"USER#{user_id}"
    assert item["email"] == "john.doe@example.com"
    assert "createdAt" in item
    assert "updatedAt" in item
    assert item["createdAt"] == item["updatedAt"]


def test_create_user_missing_email(dynamodb_table):
    """Test creation of a user without providing an email."""
    event = {
        "body": json.dumps(
            {
                # 'email' is missing
            }
        )
    }
    response = handler(event, {})
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "message" in body
    assert body["message"] == "Invalid email address."


def test_create_user_invalid_email_format(dynamodb_table):
    """Test creation of a user with an invalid email format."""
    event = {"body": json.dumps({"email": "invalid-email-format"})}
    response = handler(event, {})
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "message" in body
    assert body["message"] == "Invalid email address."


def test_create_user_dynamodb_failure(aws_credentials, dynamodb_table):
    """Test handling of DynamoDB put_item failure."""
    with patch("boto3.resource") as mock_resource:
        mock_dynamodb = mock_resource.return_value
        mock_table = mock_dynamodb.Table.return_value
        mock_table.put_item.side_effect = Exception("DynamoDB failure")

        event = {"body": json.dumps({"email": "jane.doe@example.com"})}
        response = handler(event, {})
        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "message" in body
        assert body["message"] == "Internal server error."
