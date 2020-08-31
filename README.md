# Automated Solution Testing Pipeline Readme

## Quick Start

<a href="https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=MyTestingPipeline=https://testing-pipeline-amc-sa.s3.amazonaws.com/Pipeline_Template.yml" target="_blank"><img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png"/></a>

Click the launch button above to begin the process of deploying an Automated Testing Pipeline on AWS CloudFormation. NOTE: This launch button already has the *US East* region pre-selected as part of the URL (i.e., &region=us-east-1), but once you click the button, you can change your preferred deployment region in AWS by selecting it from the top bar of the AWS Console, after which you may need to provide the Amazon S3 Template URL (https://testing-pipeline-amc-sa.s3.amazonaws.com/Pipeline_Template.yml).

## Summary

This repository allows you to quickly deploy a multi-user, scalable, and fault tolerant Automated Testing Pipeline for testing deployment and functionality of reusable solutions including OHDSI-on-AWS and REDCap environments on AWS. Click **Launch Stack** in the **Quick Start** section above to launch a new Automated Testing Pipeline. You can access resources associated with the pipeline in the AWS Management Console.

The code within this repository provides the opportunity to test either OHDSI-on-AWS or REDCap on AWS by configuring the pipeline accordingly. If you wish to test a different CloudFormation template, you can do so by providing your own custom test scripts and configuring the pipeline accordingly.

If you are interested in deploying OHDSI-on-AWS without a testing pipeline, see the [OHDSI-on-AWS GitHub page](https://github.com/OHDSI/OHDSIonAWS). If you are interested in deploying a REDCap environment on AWS without a testing pipeline, see the [REDCap environment on AWS GitHub page](https://github.com/vanderbilt-redcap/redcap-aws-cloudformation).

## Topics

* [Automated Testing Pipeline architecture and features](#auto-test-pipeline-architecture-and-features)
* [Automated Testing Pipeline deployment instructions](#auto-test-pipeline-deployment-instructions)
* [Uploading source files](#uploading-sources)
* [Troubleshooting Deployments](#troubleshooting-deployments)
* [Ongoing Operations](#on-going-operations)

## Automated Testing Pipeline architecture and features

The architecture can be extended to test any CloudFormation stack. For this particular use case, we wrote the test scripts specifically to test the urls output by the CloudFormation solutions. The Automated Testing Pipeline has the following features:

* Deployed in a single AWS Region, with the exception of the tested CloudFormation solution
* Has a [serverless architecture](https://aws.amazon.com/serverless/) operating at the AWS Region level
* Deploys a pipeline which can deploy and test the CloudFormation solution
* Creates CloudWatch events to activate the pipeline on a schedule or when the solution is updated
* Creates an SNS topic for notifying subscribers when there are errors
* Includes code for running [TaskCat](https://github.com/aws-quickstart/taskcat) and scripts to test solution functionality
* Built automatically in minutes
* Low in cost with free tier benefits ([ATP_Costs.xlsx](https://quip-amazon.com/-/blob/YXZ9AAUTCk9/hZ1k7KA2FcSxLvrLPTzeOA?name=ATP_Costs.xlsx))

A high-level diagram showing the overall architecture for the Automated Testing Pipeline is shown below.  
![alt-text](https://github.com/aws-samples/aws-cloudformation-automated-testing-taskcat-aws-codepipeline/blob/master/images/atp-architecture.png)

#### General Architecture Description
The Automated Testing Pipeline solution as a whole is designed to automatically deploy CloudFormation templates, run tests against the deployed environments, send notifications if an issue is discovered, and allow for insightful testing data to be easily explored.

The pipeline is triggered automatically when an event occurs. These events include a change to the CloudFormation solution template, a change to the code in the testing repository, and an alarm set off by a regular schedule. Additional events can be added in the CloudWatch console. 

When the pipeline is triggered, the testing environment is set up by CodeBuild. CodeBuild uses a [build specification](https://docs.aws.amazon.com/codebuild/latest/userguide/build-spec-ref.html) file kept within the CodeCommit [source repository](https://docs.aws.amazon.com/codebuild/latest/APIReference/API_ProjectSource.html) to set up the environment and run the test scripts. The build specification includes commands run [TaskCat](https://github.com/aws-quickstart/taskcat) — an open-source tool for testing the deployment of CloudFormation templates. If the template is successfully deployed, CodeBuild handles running test scripts against the CloudFormation solution environment.

The test results are stored in an S3 bucket. Information from these results are inserted into the dashboard generated by TaskCat to make it easy to find errors and access log files. Messages are published to [topics in SNS](https://docs.amazonaws.cn/en_us/sns/latest/dg/sns-tutorial-create-topic.html) whenever an error occurs which provide a link to this dashboard.

**AWS CloudFormation** is used to provision and deploy all resources listed below which are used as part of the pipeline. 

**Amazon CloudWatch** is used to activate the pipeline using event rules. This includes activating the pipline when the solution template is updated, when the test scripts are updated, or using a schedule.

**Amazon CodePipeline** is used to automate the testing of the cloudformation template.

**Amazon CodeBuild** is used to run taskcat to deploy the template and test the created stacks with internal scripts.

**Amazon Simple Notification Service (SNS)** is used to notify subscribers whenever the pipeline or internal scripts fail.

**Amazon S3** is used to store the test results and error dashboard.


## Automated Solution Testing Pipeline deployment instructions

Be sure to complete all prerequisite tasks before beginning deployment and all post-deployment tasks upon successful deployment of the Automated Testing Pipeline. See the **Troubleshooting Deployments** section if you experience any issues completing tasks to follow. 

#### Prerequisite tasks
0.1. Clone this repository.

0.2. [Create an EC2KeyPair](https://docs.aws.amazon.com/cli/latest/userguide/cli-services-ec2-keypairs.html) in the region you want to test the CloudFormation solution in. This will be used when TaskCat is run to deploy the CloudFormation solution template.

#### Ensure you have appropriate permissions and limits
0.3. This template must be run by an AWS IAM User who has sufficient permission to create the required resources. If you are not an Administrator of the AWS account you are using, please check with them before running this template to ensure you have sufficient permission.  

0.4. This template will create four S3 buckets. Additional buckets may be created depending on the CloudFormation solution being tested. By default, AWS accounts have a limit of 100 S3 buckets. If you are near that limit, please either delete some unused S3 buckets or [request a limit increase](https://console.aws.amazon.com/support/cases#/create?issueType=service-limit-increase) before running this template.

#### Begin deployment

1. Begin the deployment process by clicking the **Launch Stack** button at the top of this page. This will take you to the [CloudFormation Manage Console](https://console.aws.amazon.com/cloudformation/) and specify the Automated Testing Pipeline CloudFormation template.  Then click the **Next** button in the lower-right corner. 
	* You can also launch the CloudFormation Template by downloading the Pipeline_Template.yml from this repository and launching a stack with new resources.
2. The next screen will take in all of the parameters for your pipeline environment.  A description is provided for each parameter to help explain its function, but following is also a detailed description of how to use each parameter.  At the top, provide a unique **Stack Name**. The ResultBucketName and SourceBucketName will be used to modify the code later on.

#### General AWS parameters
|Parameter Name| Description|
|---------------|-----------|
| CodeBuildAccessSecretName|Name of the secret key used to perform tasks in codebuild|
| PipelineName|Name of the pipeline|
| ResultBucketName|S3 Bucket Name containing test results and dashboard|
| SourceBucketName|S3 Bucket Name containing clouformation template|
| SourceTemplateName|Name of solution template file|
| TestCodeRepositoryBranch|CodeCommit branch name|
| TestCodeRepositoryName|CodeCommit Repository name for containing test code|

*When you've provided appropriate values for the **Parameters**, choose **Next**.*

*3. On the next screen, you can provide some other optional information like Tags, alternative Permissions, etc. at your discretion.  This information isn't necessary for typical deployments. Then choose **Next**.*

*4. On the next screen, you can review what will be deployed. At the bottom of the screen, there is a check box for you to acknowledge that **AWS CloudFormation might create IAM resources with custom names** and **AWS CloudFormation might require the following capability: CAPABILITY_AUTO_EXPAND**. This is correct; the template being deployed creates four custom roles that give permission for the AWS services involved to communicate with each other. Details of these permissions are inside the CloudFormation template referenced in the URL given in the first step. Check the box acknowledging this and choose **Next**.*

*5. You can watch as CloudFormation builds out your pipeline environment. A CloudFormation deployment is called a *stack*. The parent stack creates several child stacks depending on the parameters you provided.  When all the stacks have reached the green CREATE_COMPLETE status, then the pipeline architecture has been deployed.*

#### Post-Deployment Tasks to Begin Testing 
1. [Create a secret](https://docs.aws.amazon.com/secretsmanager/latest/userguide/tutorials_basic.html) containing a username and password to be used for testing OHSDI-on-AWS or REDCap. The secret name and keys will be used to modify the code later on.\
![alt-text](https://github.com/aws-samples/aws-cloudformation-automated-testing-taskcat-aws-codepipeline/blob/master/images/secret-creation.png)

2. [Subscribe to the SNS topic](https://docs.amazonaws.cn/en_us/sns/latest/dg/sns-tutorial-create-subscribe-endpoint-to-topic.html) that was automatically created during deployment. 

3. Skip this step if you are testing OHDSI-on-AWS. Upload the CloudFormation template to be tested to the S3 bucket created with the parameter SourceBucketName.

4. Make the following changes in the .taskcat.yml file:
- [ ] Update the [EC2KeyName value](https://github.com/aws-samples/aws-cloudformation-automated-testing-taskcat-aws-codepipeline/blob/0f5bfaf203532f88386f4d5d0450d23d42c9239b/.taskcat.yml#L25) under test-scenario-1 to match the created EC2KeyPair name.
- [ ] Replace the [DatabaseMasterPassword placeholder](https://github.com/aws-samples/aws-cloudformation-automated-testing-taskcat-aws-codepipeline/blob/901407a079099d7f7061b47f1cc005c6023f4a93/.taskcat.yml#L28) value with a desired password value. Follow the instructions in the [comment](https://github.com/aws-samples/aws-cloudformation-automated-testing-taskcat-aws-codepipeline/blob/901407a079099d7f7061b47f1cc005c6023f4a93/.taskcat.yml#L27) describing how to create a valid password value.
- [ ] Replace the [](https://github.com/aws-samples/aws-cloudformation-automated-testing-taskcat-aws-codepipeline/blob/58f21e57a8f06599199087bd0617f2867c39723d/.taskcat.yml#L27)[EBEndpoint value](https://github.com/aws-samples/aws-cloudformation-automated-testing-taskcat-aws-codepipeline/blob/901407a079099d7f7061b47f1cc005c6023f4a93/.taskcat.yml#L26) with a unique ElasticBeanstalk endpoint name. This ElasticBenstalk endpoint name will be used to modify code later on.
- [ ] (Optional). Change the [region to deploy the template in](https://github.com/aws-samples/aws-cloudformation-automated-testing-taskcat-aws-codepipeline/blob/901407a079099d7f7061b47f1cc005c6023f4a93/.taskcat.yml#L39) to your desired region.

5. Make the following changes to the [environment in the buildspec.yml](https://github.com/aws-samples/aws-cloudformation-automated-testing-taskcat-aws-codepipeline/blob/901407a079099d7f7061b47f1cc005c6023f4a93/buildspec.yml#L2) file:
- [ ] Replace the RESULT_BUCKET variable placeholder with the ResultBucketName parameter value chosen
- [ ] Replace the SOURCE_BUCKET variable placeholder with the SourceBucketName parameter value chosen
- [ ] Replace the TEMPLATE_NAME variable placeholder with the desired CloudFormation template to be tested (e.g. 00-master-ohdsi.yaml)
- [ ] Replace the TOPIC_ARN variable placeholder with the ARN for the created SNS topic
- [ ] Replace the USER secrets-manager placeholder values with the secret name and username key you created in step 1 (eg. secret-name:userkey).
- [ ] Replace the PASSW secrets-manager placeholder values with the secret name and password key you created in step 1.
- [ ] Replace the REGION and/or EB_ENDPOINT to match the test scenario parameters you entered for the taskcat.yml

6. Go to CodeCommit repositorySet a new origin for the cloned repository to the newly created CodeCommit repository using the following command:

```
git remote set-url origin CODECOMMIT_URL_HERE
```

7. Pushing to CodeCommit will automatically activate the Pipeline. You can monitor the testing through the CodeBuild Logs.

#### Customizing Your Testing Solution
If you wish to alter the Automated Testing Pipeline solution to best meet your use case, there are several changes you can make. 

CloudWatch Events determine when the pipeline is automatically run. You can alter these rules to scale how frequently the pipeline runs. The pipeline is triggered every Monday by default under the schedule rule. Additionally, the pipeline is triggered when there is a change to the S3 bucket hosting the CloudFormation template or the TestCodeRepositoryBranch. Rules can be added, removed, or altered to meet your needs.

If you wish to test a different CloudFormation template, you can do so by uploading your template to the source S3 bucket. You will need to follow the above deployment instructions for configuring the pipeline to access this template. You will likely need to upload custom test scripts to test this deployed environment. The scripts can be pushed to the created CodeCommit repository, and you will need to update the buildspec.yml file to run the custom scripts. 

#### Using Dashboard
Once testing is complete, a static html object is stored in results S3 bucket that was created during deployment of the Automated Testing Pipeline. This object can be opened to view the test results dashboard. It can be accessed directly in S3 or via the link included in test failure notifications. Each test will be associated with one of three states: SUCCESS, FAILURE, and UNEXECUTED. For a more detailed look at the status of a test, click the **View Logs** link associated with it. Information including HTTP response codes, page response times, and error messages are stored within these logs to help discover causes of failures.\
![alt-text](https://github.com/aws-samples/aws-cloudformation-automated-testing-taskcat-aws-codepipeline/blob/master/images/dashboard.png)

## Troubleshooting Deployments

#### CloudFormation Events
A CloudFormation deployment is called a *stack*.  The Automated Testing Pipeline template deploys a number of child or *nested* stacks depending on which options you choose.  If one of the steps in any of these stacks fail during deployment, all of the stacks will be *rolled back*, meaning that they will be deleted in the reverse order that they were deployed.  In order to understand why a deployment rolled back, it can be helpful to look at the *events* that CloudFormation recorded during deployment.  You can do this by looking at the Events tab of each stack.  If a stack has already been rolled back, you will have to change the *filter* in the upper-left corner of the CloudFormation Management Console from it's default of *Active* to *Deleted* to see it's event log.

#### Build Log
If you are testing OHDSI-on-AWS, during the build process a temporary Linux instance is created that compiles WebAPI, combines it with Atlas, loads all of your OMOP data sets into Redshift, runs Achilles, and performs various other configuration functions.  You can see a log of the work that it did by looking in the [**CloudWatch Logs Management Console** under the *Log Group* ```ohdsi-temporary-ec2-instance-build-log```](https://console.aws.amazon.com/cloudwatch/home?logs%3A=#logStream:group=ohdsi-temporary-ec2-instance-build-log).\
![alt-text](https://github.com/OHDSI/OHDSIonAWS/blob/master/images/cloudwatch_logs.gif)


