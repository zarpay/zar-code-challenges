import json
import os
import boto3
from boto3.dynamodb.conditions import Key


def handler(event, context):
    try:
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(os.environ["MAIN_TABLE"])
        response = table.query(
            KeyConditionExpression=Key("pk").eq("RATE"),
            ScanIndexForward=False,  # Get latest first
        )
        items = response.get("Items", [])

        rates = {}
        for item in items:
            pair = item["pair"]
            if pair not in rates:
                rates[pair] = item["rate"]

        return {"statusCode": 200, "body": json.dumps(rates)}

    except Exception as e:
        print(str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Internal server error."}),
        }
