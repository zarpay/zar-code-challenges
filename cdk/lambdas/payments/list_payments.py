import json
import os
import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["MAIN_TABLE"])


def handler(event, context):
    try:
        response = table.scan(FilterExpression=Attr("sk").begins_with("PAYMENT#"))
        payments = response.get("Items", [])

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
