// Copyright 2016-2019, Pulumi Corporation.  All rights reserved.

import * as awsx from "@pulumi/awsx";

const appName = "import-api"
// Step 1: Create an ECS Fargate cluster.
const cluster = new awsx.ecs.Cluster(`${appName}-cluster`);

// Step 2: Define the Networking for our service.
const alb = new awsx.elasticloadbalancingv2.ApplicationLoadBalancer(
    `${appName}-lb`, {external: true, securityGroups: cluster.securityGroups});

const web = alb.createListener(`${appName}-tg`, {port: 5000, external: true, protocol: "HTTP"});

// Step 3: Build and publish a Docker image to a private ECR registry.
const img = awsx.ecs.Image.fromPath(appName, "../");

// Step 4: Create a Fargate service task that can scale out.
const appService = new awsx.ecs.FargateService(`${appName}-service`, {
    cluster,
    taskDefinitionArgs: {
        container: {
            image: img,
            cpu: 256 /*10% of 1024*/,
            memory: 128 /*MB*/,
            portMappings: [web],
        },
    },
    desiredCount: 1,
});

// Step 5: Export the Internet address for the service.
export const url = web.endpoint.hostname;
