# About the AWS Security Hub to Splunk integration.
The integration in this repository will send all findings in AWS Security Hub to Splunk for further analysis and correlation with relevant data sources (AWS CloudTrail, AWS CloudWatch, AWS Config, custom/on-prem data, etc.). Using automation provided by [Project Trumpet](https://github.com/splunk/splunk-aws-project-trumpet) Security Hub Events are sent from CloudWatch Events though a AWS Kinesis Data Firehose to a Splunk HTTP Event Collector. This is a much simpler path for "Getting Data In"  that the older method of polling the Security Hub API. 

# Setting up the AWS Security Hub to Splunk integration.

## Overview:
There are two parts to setting up the ingestion part of the AWS Security Hub to Splunk integration.
	
#### Part 1: 
	
Use the Trumpet Instructions to build the Cloudformation Templete that will automation the GDI pipeline to Splunk 

#### Part 2: 
	
Load the SPL file for the example dashboards for Security Hub. 

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
        
Follow the [Trumpet Setup and Configuration guide](https://github.com/splunk/splunk-aws-project-trumpet)

## Troubleshooting

1.) Check if events are being sent to Splunk by searching `sourcetype="aws:securityhub"`. Make sure the time period is set to a range of time where you would expect events.

2.) Ensure the CloudFormation template was launched in an AWS region where AWS Security Hub is available.

3.) Check that there are findings from after the CloudFormation template was launched and the Lambda updated in the AWS Security Hub console. Some services only send their findings on a 24 hour interval.

4.) If there are no findings in the AWS Security Hub console, either wait for new findings, or generate sample findings from the GuardDuty -> Settings -> Generate Sample findings option.

5.) Confirm that HEC is enabled on the endpoint, this is a per token as well as a **global** setting, (confirm in Splunk Web under `Settings -> Data Inputs -> HTTP Event Collector -> Global Settings`). Also confirm that the HEC token itself is enabled, and that indexer acknowledgement is turned off for the token.

6.) Refer to Project Trumpet's Troubleshooting Guide for more. 