import * as cdk from "aws-cdk-lib";
import { Template, Match } from "aws-cdk-lib/assertions";
import { CdkStack } from "../lib/cdk-stack";

describe("CdkStack", () => {
    let app: cdk.App;
    let stack: CdkStack;
    let template: Template;

    beforeAll(() => {
        app = new cdk.App();
        stack = new CdkStack(app, "TestStack", {
            env: { account: "390844783038", region: "us-east-1" },
        });
        template = Template.fromStack(stack);
    });

    test("DynamoDB Table Created with Correct Properties", () => {
        template.hasResourceProperties("AWS::DynamoDB::Table", {
            TableName: "CryptoPaymentTable",
            BillingMode: "PAY_PER_REQUEST",
            KeySchema: [
                { AttributeName: "pk", KeyType: "HASH" },
                { AttributeName: "sk", KeyType: "RANGE" },
            ],
            AttributeDefinitions: [
                { AttributeName: "pk", AttributeType: "S" },
                { AttributeName: "sk", AttributeType: "S" },
                { AttributeName: "paymentId", AttributeType: "S" },
            ],
            GlobalSecondaryIndexes: Match.arrayWith([
                {
                    IndexName: "paymentId-index",
                    KeySchema: [
                        { AttributeName: "paymentId", KeyType: "HASH" },
                        { AttributeName: "sk", KeyType: "RANGE" },
                    ],
                    Projection: { ProjectionType: "ALL" },
                },
            ]),
        });
    });

    test("Lambda Functions Created with Correct Properties", () => {
        const lambdaFunctions = [
            { funcName: "CreateUserFunction", handler: "create_user.handler" },
            { funcName: "GetUserFunction", handler: "get_user.handler" },
            {
                funcName: "GetUserPaymentsFunction",
                handler: "get_user_payments.handler",
            },
            {
                funcName: "CreatePaymentFunction",
                handler: "create_payment.handler",
            },
            { funcName: "GetPaymentFunction", handler: "get_payment.handler" },
            {
                funcName: "ListPaymentsFunction",
                handler: "list_payments.handler",
            },
            { funcName: "GetRatesFunction", handler: "get_rates.handler" },
            {
                funcName: "GetRatesHistoryFunction",
                handler: "get_rates_history.handler",
            },
        ];

        lambdaFunctions.forEach(({ funcName, handler }) => {
            template.hasResourceProperties("AWS::Lambda::Function", {
                FunctionName: funcName,
                Handler: handler,
                Runtime: "python3.9",
                Environment: {
                    Variables: {
                        MAIN_TABLE: {
                            Ref: Match.stringLikeRegexp("^MainTable.*"),
                        },
                    },
                },
            });
        });
    });

    test("API Methods Require API Key", () => {
        template.hasResourceProperties("AWS::ApiGateway::Method", {
            ApiKeyRequired: true,
        });
    });
});
