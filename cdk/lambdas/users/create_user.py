from datetime import datetime
import boto3
import json
import uuid
import os
import re


def handler(event, context):
    try:
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.Table(os.environ["MAIN_TABLE"])
        body = json.loads(event["body"])
        email = body.get("email")

        if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Invalid email address."}),
            }

        user_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        user = {
            "pk": user_id,
            "sk": f"USER#{user_id}",
            "email": email,
            "createdAt": timestamp,
            "updatedAt": timestamp,
        }

        table.put_item(Item=user)

        return {"statusCode": 201, "body": json.dumps({"userId": user_id})}

    except Exception as e:
        print(str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Internal server error."}),
        }
