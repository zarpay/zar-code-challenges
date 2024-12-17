import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["MAIN_TABLE"])


def handler(event, context):
    payment_id = event["pathParameters"]["id"]

    try:
        response = table.scan(
            IndexName="paymentId-index",
            FilterExpression=Key("paymentId").eq(payment_id),
        )
        payments = response.get("Items", [])
        if not payments:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "Payment not found."}),
            }

        payment = payments[0]
        payment.pop("pk", None)
        payment.pop("sk", None)

        return {"statusCode": 200, "body": json.dumps(payment)}

    except Exception as e:
        print(str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Internal server error."}),
        }
