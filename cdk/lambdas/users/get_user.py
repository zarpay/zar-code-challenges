import json
import os
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['MAIN_TABLE'])

def handler(event, context):
    user_id = event['pathParameters']['id']

    try:
        response = table.get_item(
            Key={
                'pk': user_id,
                'sk': f'USER#{user_id}'
            }
        )
        user = response.get('Item')
        if not user:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'User not found.'})
            }

        # Remove pk and sk before returning
        user.pop('pk', None)
        user.pop('sk', None)

        return {
            'statusCode': 200,
            'body': json.dumps(user)
        }

    except Exception as e:
        print(str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error.'})
        }
