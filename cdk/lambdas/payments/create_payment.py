from datetime import datetime
import json
import os
import uuid
import boto3
import re


def handler(event, context):
    try:
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(os.environ["MAIN_TABLE"])
        body = json.loads(event["body"])
        user_id = body.get("userId")
        amount = body.get("amount")
        currency = body.get("currency")
        metadata = body.get("metadata", {})

        # Basic validation
        if not user_id or not isinstance(user_id, str):
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Invalid or missing userId."}),
            }

        if not amount or not isinstance(amount, (int, float, str)):
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Invalid or missing amount."}),
            }

        if not currency or not isinstance(currency, str):
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Invalid or missing currency."}),
            }

        if not re.match(r"^[A-Z]{3}$", currency):
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Invalid currency format."}),
            }

        payment_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        payment = {
            "pk": user_id,
            "sk": f"PAYMENT#{timestamp}",
            "paymentId": payment_id,
            "amount": str(amount),
            "currency": currency,
            "status": "pending",
            "metadata": metadata,
            "createdAt": timestamp,
            "updatedAt": timestamp,
        }

        table.put_item(Item=payment)

        return {"statusCode": 201, "body": json.dumps({"paymentId": payment_id})}

    except Exception as e:
        print(str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Internal server error."}),
        }
