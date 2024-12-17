import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError


def handler(event, context):
    user_id = event["pathParameters"]["id"]
    try:
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(os.environ["MAIN_TABLE"])
        response = table.query(
            KeyConditionExpression=Key("pk").eq(user_id)
            & Key("sk").begins_with("PAYMENT#")
        )
        payments = response.get("Items", [])

        # Remove pk and sk from each payment
        for payment in payments:
            payment.pop("pk", None)
            payment.pop("sk", None)

        return {"statusCode": 200, "body": json.dumps(payments)}

    except Exception as e:
        print(str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Internal server error."}),
        }
