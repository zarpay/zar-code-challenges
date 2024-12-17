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
            ScanIndexForward=False,  # Latest first
        )
        items = response.get("Items", [])

        rates_history = []
        for item in items:
            rates_history.append(
                {
                    "pair": item["pair"],
                    "rate": item["rate"],
                    "timestamp": item["sk"].split("#")[1],
                }
            )

        return {"statusCode": 200, "body": json.dumps(rates_history)}

    except Exception as e:
        print(str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Internal server error."}),
        }
