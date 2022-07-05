import * as pulumi from "@pulumi/pulumi";
import * as awsx from "@pulumi/awsx";
import * as aws from "@pulumi/aws";

const stack = pulumi.getStack();

const vpc = new awsx.ec2.Vpc("ecs-vpc", {
    cidrBlock: "10.0.0.0/16"
}, {protect: true});

const allow_http = new aws.ec2.SecurityGroup("allow_http", {
    description: "Allow http access",
    egress: [{
        cidrBlocks: ["0.0.0.0/0"],
        fromPort: 0,
        protocol: "-1",
        toPort: 0,
    }],
    ingress: [{
        cidrBlocks: ["0.0.0.0/0"],
        fromPort: 80,
        protocol: "tcp",
        toPort: 80,
    }],
    name: "allow_http",
    vpcId: vpc.id,
});


const appName = "import-api"

// Step 1: Create an ECS Fargate cluster.
const cluster = new awsx.ecs.Cluster(`${appName}-cluster`, {vpc});


// Step 2: Define the Networking for our service.
const alb = new awsx.elasticloadbalancingv2.ApplicationLoadBalancer(`${appName}-lb`, {
    external: false,
    vpc: cluster.vpc,
    securityGroups: cluster.securityGroups,
    subnets: cluster.vpc.privateSubnetIds
});

const web = alb.createListener(`${appName}-tg`, {port: 80, external: false});

// Step 3: Build and publish a Docker image to a private ECR registry.
const img = awsx.ecs.Image.fromPath(appName, "../../");

// Step 4: Create a Fargate service task that can scale out.
const appService = new awsx.ecs.FargateService(`${appName}-service`, {
    cluster,
    taskDefinitionArgs: {
        container: {
            image: img,
            cpu: 1024 /*10% of 1024*/,
            memory: 1024 /*MB*/,
            portMappings: [web],
        },
    },
    desiredCount: 1,
});

const gateway = new aws.apigatewayv2.Api(`${appName}-gateway`, {
    protocolType: "HTTP",
    version: "v1",
});


const vpcLink = new aws.apigatewayv2.VpcLink(`${appName}-vpc-link`, {
    subnetIds: pulumi.output(vpc.privateSubnetIds),
    securityGroupIds: [allow_http.id]
});

// Step 6: Put all everything behind an API Gateway
const gatewayIntegration = new aws.apigatewayv2.Integration(`${appName}-integration`, {
    apiId: gateway.id,
    integrationType: "HTTP_PROXY",
    integrationMethod: "ANY",
    connectionType: "VPC_LINK",
    connectionId: vpcLink.id,
    integrationUri: web.listener.arn,
    requestParameters: {
        "overwrite:path": "$request.path"
    }
});

const route = new aws.apigatewayv2.Route(`${appName}-route`, {
    apiId: gateway.id,
    routeKey: "ANY /{proxy+}",
    target: pulumi.interpolate`integrations/${gatewayIntegration.id}`,
});

const stage = new aws.apigatewayv2.Stage(`${appName}-stage`, {
    apiId: gateway.id,
    name: stack,
    routeSettings: [
        {
            routeKey: route.routeKey,
            throttlingBurstLimit: 5000,
            throttlingRateLimit: 10000,
        },
    ],
    autoDeploy: true,
}, {dependsOn: [route]});

export const endpoint = pulumi.interpolate`${gateway.apiEndpoint}/${stage.name}`;
