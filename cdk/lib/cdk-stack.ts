import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as apigateway from "aws-cdk-lib/aws-apigateway";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as path from "path";

export class CdkStack extends cdk.Stack {
    constructor(scope: Construct, id: string, props?: cdk.StackProps) {
        super(scope, id, props);

        // DynamoDB Table - Single Table Design with GSI for paymentId
        const mainTable = new dynamodb.Table(this, "MainTable", {
            partitionKey: { name: "pk", type: dynamodb.AttributeType.STRING },
            sortKey: { name: "sk", type: dynamodb.AttributeType.STRING },
            billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
            tableName: "CryptoPaymentTable",
            removalPolicy: cdk.RemovalPolicy.DESTROY,
        });

        mainTable.addGlobalSecondaryIndex({
            indexName: "paymentId-index",
            partitionKey: {
                name: "paymentId",
                type: dynamodb.AttributeType.STRING,
            },
            sortKey: { name: "sk", type: dynamodb.AttributeType.STRING },
            projectionType: dynamodb.ProjectionType.ALL,
        });

        const commonEnv = {
            MAIN_TABLE: mainTable.tableName,
        };

        // Users Lambdas
        const createUserFunction = new lambda.Function(
            this,
            "CreateUserFunction",
            {
                functionName: "CreateUserFunction",
                runtime: lambda.Runtime.PYTHON_3_9,
                handler: "create_user.handler",
                code: lambda.Code.fromAsset(
                    path.join(__dirname, "../lambdas/users")
                ),
                environment: commonEnv,
            }
        );

        const getUserFunction = new lambda.Function(this, "GetUserFunction", {
            functionName: "GetUserFunction",
            runtime: lambda.Runtime.PYTHON_3_9,
            handler: "get_user.handler",
            code: lambda.Code.fromAsset(
                path.join(__dirname, "../lambdas/users")
            ),
            environment: commonEnv,
        });

        const getUserPaymentsFunction = new lambda.Function(
            this,
            "GetUserPaymentsFunction",
            {
                functionName: "GetUserPaymentsFunction",
                runtime: lambda.Runtime.PYTHON_3_9,
                handler: "get_user_payments.handler",
                code: lambda.Code.fromAsset(
                    path.join(__dirname, "../lambdas/users")
                ),
                environment: commonEnv,
            }
        );

        // Payments Lambdas
        const createPaymentFunction = new lambda.Function(
            this,
            "CreatePaymentFunction",
            {
                functionName: "CreatePaymentFunction",
                runtime: lambda.Runtime.PYTHON_3_9,
                handler: "create_payment.handler",
                code: lambda.Code.fromAsset(
                    path.join(__dirname, "../lambdas/payments")
                ),
                environment: commonEnv,
            }
        );

        const getPaymentFunction = new lambda.Function(
            this,
            "GetPaymentFunction",
            {
                functionName: "GetPaymentFunction",
                runtime: lambda.Runtime.PYTHON_3_9,
                handler: "get_payment.handler",
                code: lambda.Code.fromAsset(
                    path.join(__dirname, "../lambdas/payments")
                ),
                environment: commonEnv,
            }
        );

        const listPaymentsFunction = new lambda.Function(
            this,
            "ListPaymentsFunction",
            {
                functionName: "ListPaymentsFunction",
                runtime: lambda.Runtime.PYTHON_3_9,
                handler: "list_payments.handler",
                code: lambda.Code.fromAsset(
                    path.join(__dirname, "../lambdas/payments")
                ),
                environment: commonEnv,
            }
        );

        // Rates Lambdas
        const getRatesFunction = new lambda.Function(this, "GetRatesFunction", {
            functionName: "GetRatesFunction",
            runtime: lambda.Runtime.PYTHON_3_9,
            handler: "get_rates.handler",
            code: lambda.Code.fromAsset(
                path.join(__dirname, "../lambdas/rates")
            ),
            environment: commonEnv,
        });

        const getRatesHistoryFunction = new lambda.Function(
            this,
            "GetRatesHistoryFunction",
            {
                functionName: "GetRatesHistoryFunction",
                runtime: lambda.Runtime.PYTHON_3_9,
                handler: "get_rates_history.handler",
                code: lambda.Code.fromAsset(
                    path.join(__dirname, "../lambdas/rates")
                ),
                environment: commonEnv,
            }
        );

        // Grant Lambda functions access to DynamoDB
        mainTable.grantReadWriteData(createUserFunction);
        mainTable.grantReadData(getUserFunction);
        mainTable.grantReadData(getUserPaymentsFunction);
        mainTable.grantReadWriteData(createPaymentFunction);
        mainTable.grantReadData(getPaymentFunction);
        mainTable.grantReadData(listPaymentsFunction);
        mainTable.grantReadData(getRatesFunction);
        mainTable.grantReadData(getRatesHistoryFunction);

        // API Gateway
        const api = new apigateway.RestApi(this, "CryptoPaymentApi", {
            restApiName: "Crypto Payment Processing Service",
            description: "This service handles cryptocurrency payments.",
            deployOptions: {
                stageName: "v1",
                throttlingRateLimit: 100,
                throttlingBurstLimit: 200,
            },
        });

        const apiKey = api.addApiKey("ApiKey", {
            apiKeyName: "CryptoPaymentApiKey",
            description: "API Key for CryptoPaymentApi",
        });

        const usagePlan = api.addUsagePlan("UsagePlan", {
            name: "DefaultUsagePlan",
            throttle: {
                rateLimit: 100, // requests per second
                burstLimit: 200, // maximum burst
            },
            apiStages: [
                {
                    api: api,
                    stage: api.deploymentStage,
                },
            ],
        });

        usagePlan.addApiKey(apiKey);

        const requireApiKey = {
            apiKeyRequired: true,
        };

        // Users Resource
        const users = api.root.addResource("users");
        users.addMethod(
            "POST",
            new apigateway.LambdaIntegration(createUserFunction),
            {
                requestModels: {
                    "application/json": apigateway.Model.EMPTY_MODEL,
                },
                methodResponses: [{ statusCode: "201" }],
                ...requireApiKey,
            }
        );

        const userId = users.addResource("{id}");
        userId.addMethod(
            "GET",
            new apigateway.LambdaIntegration(getUserFunction),
            {
                methodResponses: [{ statusCode: "200" }],
                ...requireApiKey,
            }
        );

        const userPayments = userId.addResource("payments");
        userPayments.addMethod(
            "GET",
            new apigateway.LambdaIntegration(getUserPaymentsFunction),
            {
                methodResponses: [{ statusCode: "200" }],
                ...requireApiKey,
            }
        );

        // Payments Resource
        const payments = api.root.addResource("payments");
        payments.addMethod(
            "POST",
            new apigateway.LambdaIntegration(createPaymentFunction),
            {
                requestModels: {
                    "application/json": apigateway.Model.EMPTY_MODEL,
                },
                methodResponses: [{ statusCode: "201" }],
                ...requireApiKey,
            }
        );

        const paymentId = payments.addResource("{id}");
        paymentId.addMethod(
            "GET",
            new apigateway.LambdaIntegration(getPaymentFunction),
            {
                methodResponses: [{ statusCode: "200" }],
                ...requireApiKey,
            }
        );

        payments.addMethod(
            "GET",
            new apigateway.LambdaIntegration(listPaymentsFunction),
            {
                methodResponses: [{ statusCode: "200" }],
                ...requireApiKey,
            }
        );

        // Rates Resource
        const rates = api.root.addResource("rates");
        rates.addMethod(
            "GET",
            new apigateway.LambdaIntegration(getRatesFunction),
            {
                methodResponses: [{ statusCode: "200" }],
                ...requireApiKey,
            }
        );

        const ratesHistory = rates.addResource("history");
        ratesHistory.addMethod(
            "GET",
            new apigateway.LambdaIntegration(getRatesHistoryFunction),
            {
                methodResponses: [{ statusCode: "200" }],
                ...requireApiKey,
            }
        );
    }
}
