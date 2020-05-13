# About the AWS Security Hub to Splunk integration.
The integration in this repository will send all findings in AWS Security Hub to Splunk for further analysis and correlation with relevant data sources (AWS CloudTrail, AWS CloudWatch, AWS Config, custom/on-prem data, etc.). Using automation provided by [Project Trumpet](https://github.com/splunk/splunk-aws-project-trumpet), AWS Security Hub Events are sent from AWS CloudWatch Events through a AWS Kinesis Data Firehose to a Splunk HTTP Event Collector. This is a much simpler path for "Getting Data In" than the older method of polling the AWS Security Hub API. 

# Setting up the AWS Security Hub to Splunk integration.

## Overview:
There are two parts to setting up the AWS Security Hub to Splunk integration.
	
#### Part 1: 
	
Follow the Trumpet instructions to build a Cloudformation template that will create a data pipeline for sending AWS Security Hub findings to Splunk.

#### Part 2: 
	
Load the `AWS_SecurityHub.spl` file in this repository containing the example dashboards for Security Hub. 

## Prerequisites:

- This step is **not** required. If AWS Security Hub is subscribed to AWS GuardDuty findings, check in the settings tab of the GuardDuty console that updated findings are sent the minimum of every 15 minutes through CloudWatch Events.

## Instructions:
#### Sending Security Hub Findings to Splunk:
        
Follow the [Trumpet Setup and Configuration guide](https://github.com/splunk/splunk-aws-project-trumpet). Be sure to select `Security Hub Findings` in the AWS CloudWatch Events dropdown.

#### Viewing Security Hub Findings in Splunk:

Install the `AWS_SecurityHub.spl` file in this repository containing the Splunk example app for AWS Security Hub. After Security Hub findings are received and indexed by Splunk, the dashboards will begin to populate.

## Troubleshooting

1.) Check if events are being sent to Splunk by searching `sourcetype="aws:securityhub"`. Make sure the time period is set to a range of time where you would expect events.

2.) Ensure the CloudFormation template was launched in an AWS region where AWS Security Hub is available.

3.) If there are no findings in the AWS Security Hub console, either wait for new findings, or generate sample findings from the GuardDuty -> Settings -> Generate Sample findings option.

4.) Refer to Project Trumpet's Troubleshooting Guide for more. 
