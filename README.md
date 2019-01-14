# About the AWS Security Hub to Splunk integration.
The integration in this repository will send all findings in AWS Security Hub to Splunk for further analysis and correlation with relevant data sources (CloudTrail, CloudWatch, Config, custom/on-prem data, etc.). Every 15 minutes, a Lambda will collect the last hour of Security Hub findings (This accounts for the delay between findings being generated/updated, and Security Hub actually having those findings available). It will send findings to Splunk and update the findings's "Note" section with a prefix of "SENT TO SPLUNK: ". If the finding already has the "SENT TO SPLUNK: " prefix, the finding will not be resent to Splunk.

# Setting up the AWS Security Hub to Splunk integration.

## Overview:
There are two parts to setting up the ingestion part of the AWS Security Hub to Splunk integration.
	
#### Part 1: 
	
Run an AWS CloudFormation template that generates a CloudWatch scheduled event (triggers every 15 minutes), an AWS Lambda function stub, and all the roles and permissions needed for them to run together.

#### Part 2: 
	
Lambda's boto3 python SDK has not yet been updated in Lambda to interact with AWS Security Hub. For now, this is solved by packaging the updated boto3 library (and dependencies) that the Lambda function needs to interact with AWS Security Hub in the zip.

## Prerequisites:

- A Splunk HTTP Event Collector endpoint that is accessible
- A Splunk HTTP Event Collector Token with the following settings
    - NO indexer acknowledgement
    - Enabled
    - Events will be sent and indexed with sourcetype `aws:securityhub` regardless of the sourcetype set in the token
    - All other settings are optional
    - Security Hub dashboards require the events to be in the default index (main)
- This step is **not** required. If AWS Security Hub is subscribed to AWS GuardDuty findings, check in the settings tab of the GuardDuty console that updated findings are sent the minimum of every 15 minutes through CloudWatch Events.

## Instructions:
#### Part 1:
        
1.) Download the security_hub_to_splunk.template file in this repository
        
2.) From the AWS CloudFormation console, click "Create Stack"
		
3.) In the choose a template section, select "Choose File" and upload the template from the first step. Click "Next"
		
4.) Name your stack as desired. Provide your enabled Splunk HTTP Event Collector (HEC) Token (NO indexer acknowledgement turned on) and the Splunk HEC endpoint. Click "Next"

5.) You do not need to configure any Options, click "Next"

6.) On the Review page, check the IAM capabilities checkbox. Click "Create"

7.) Once the template has completed, proceed to part 2

#### Part 2:
		
1.) Download the SecurityHubToSplunkLambda.zip file

2.) From the AWS CloudFormation console, click on the Resources tab, then click on the link to the "SecurityHubToSplunkLambda" Lambda function that was created, this should link to the AWS Lambda console. 

3.) Scroll down the console to the "Function code" section. In the "Code entry type" dropdown select "Upload a .zip file"

4.) Click on the "Upload" and upload the zip file from the first step

5.) Click "Save" at the top. The Lambda function is now properly configured and will begin sending new and updated AWS Security Hub findings to Splunk every 15 minutes.

6.) Confirm events are being sent to Splunk by searching `sourcetype="aws:securityhub"`. It may take 15-20 minutes for the Lambda to be scheduled and finish running.

Note: You will not be able to edit code inline in the Lambda console because the provided zipped Lambda function is too large. You can view the Lambda code locally by unzipping the `SecurityHubToSplunkLambda` directory and opening the `securityhub_to_splunk_lambda.py` file. All other dependencies (including the up to date boto3 package) are available in the zip file.

## Troubleshooting

1.) Check if events are being sent to Splunk by searching `sourcetype="aws:securityhub"`. Make sure the time period is set to a range of time where you would expect events.

2.) Ensure the CloudFormation template was launched in an AWS region where AWS Security Hub is available.

3.) Check that there are findings from after the CloudFormation template was launched and the Lambda updated in the AWS Security Hub console. Some services only send their findings on a 24 hour interval.

4.) If there are no findings in the AWS Security Hub console, either wait for new findings, or generate sample findings from the GuardDuty -> Settings -> Generate Sample findings option.

5.) If there are recent findings, there may be an issue with configuration on the Lambda or with the HEC Token. Go to the CloudFormation console, select the stack that was launched in part 1, then click on the `Resources` tab, and click the `SecurityHubToSplunkLambda` to go to the Lambda function. Scroll to the environment variable section and double check the HEC host and HEC token values. 

6.) Confirm that HEC is enabled on the endpoint, this is a global setting, (confirm in Splunk Web under `Settings -> Data Inputs -> HTTP Event Collector -> Global Settings`). Also confirm that the HEC token itself is enabled, and that indexer acknowledgement is turned off for the token.

7.) In the Lambda console for the `SecurityHubToSplunkLambda` function, check the `Monitoring` tab and confirm that the Lambda is being invoked every 15 minutes and that there are no errors.

8.) Click on the `View logs in CloudWatch` button under the `Monitoring` tab of the Lambda Console to see the raw logs generated by the Lambda. You may see stack traces associated with SSL errors (certificate issue), channel errors (indexer acknowledgement issue), timeouts (host error), or other errors (permissions issue, set up issue, or Lambda code bug).

9.) Check that the CloudWatch Event notification setting is set to every 15 minutes in the settings section of the GuardDuty console. (This should only affect updated findings)
