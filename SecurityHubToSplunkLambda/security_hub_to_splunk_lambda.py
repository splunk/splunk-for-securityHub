import json
import datetime
import dateutil
import time
import os
import sys
from splunk_http_event_collector import http_event_collector

envLambdaTaskRoot = os.environ["LAMBDA_TASK_ROOT"]
sys.path.insert(0, envLambdaTaskRoot + "/NewBotoVersion")
import boto3

# Gets the time 30 minutes ago
def freshEventTimestampGenerator():
	tm = datetime.datetime.utcfromtimestamp(time.time())
	return time.mktime((tm - datetime.timedelta(minutes=60)).timetuple())

# Gets the epoch time of a UTC timestamp in a Security Hub finding
def findingTimestampGenerator(finding_time):
	d = dateutil.parser.parse(finding_time)
	d.astimezone(dateutil.tz.tzutc())
	
	return time.mktime(d.timetuple())

# Gets 20 most recent findings from securityhub
def getFindings(session, securityhub, filters={}):
	return securityhub.get_findings(
	    Filters=filters
	)

# Gets 20 most recent findings from securityhub
def updateFindingNote(session, securityhub, existing_note, principal, filters={}):
	return securityhub.update_findings(
	    Filters=filters,
	    Note={
	    	"Text": "SENT TO SPLUNK: %s" % existing_note,
	    	"UpdatedBy": principal
	    }
	)

# Gets 20 findings from securityhub using the NextToken from a previous request
def getFindingsWithToken(session, securityhub, token, filters={}):
	return securityhub.get_findings(
	    Filters=filters,
	    NextToken=token
	)

# Isolates host from the management scheme and port. WILL NOT WORK WITH PATHS
def hostIsolator(host):
	return (''.join(host.split('//')[1])).split(':')[0]

def lambda_handler(event, context):
	http_event_collector_token = os.environ['SPLUNK_HEC_TOKEN']
	http_event_collector_host = hostIsolator(os.environ['SPLUNK_HEC_HOST'])

	eventSenderJSON = http_event_collector(http_event_collector_token, http_event_collector_host,'json')
    
	session = boto3.session.Session()
	securityhub = session.client("securityhub",region_name=os.environ['AWS_REGION'])
	
	results = getFindings(session, securityhub)
	
	fresh_events_after_this_time = freshEventTimestampGenerator()
	fresh_events = True
	first_call = True
	sent_count = 0
	
	while ((first_call or "NextToken" in results) and fresh_events):
		# Loop through all findings (20 by default) returned by Security Hub API call
		# If finding has the string "SENT TO SPLUNK" in the finding note, the event is not sent but
		# loop will continue.
		# Fresh events will be sent to Splunk over HTTP Event Collector (HEC), "SENT TO SPLUNK" will
		# be prefixed to the finding's note.
		# Break out of the loop when we have looked back across the last hour of events (based on the
		# finding's LastObservedAt timestamp)
		first_call = False

		for finding in results["Findings"]:
			finding_timestamp = findingTimestampGenerator(finding["LastObservedAt"])
			already_sent = False
			existing_note = ""
			principal = "SplunkSecurityHubLambda"
			
			if "Note" in finding:
				if "SENT TO SPLUNK:" in finding["Note"]["Text"]:
					already_sent = True
				else:
					existing_note = finding["Note"]["Text"]
					principal = finding["Note"]["UpdatedBy"]
			
			if (finding_timestamp > fresh_events_after_this_time and not already_sent):
				payload = {}
				payload.update({"sourcetype":"aws:securityhub"})
				payload.update({"event":json.dumps(finding)})
				
				filters = {
					"Id": [ 
				         { 
				            "Comparison": "EQUALS",
				            "Value": finding["Id"]
				         }
				      ],
				    "LastObservedAt": [ 
				         { 
				            "Start": finding["LastObservedAt"],
				            "End": finding["LastObservedAt"]
				         }
				      ],
				}
				
				eventSenderJSON.sendEvent(payload)
				updateFindingNote(session, securityhub, existing_note, principal, filters)
				sent_count += 1 
			else:
				fresh_events = False
				break
		if (fresh_events):
			results = getFindingsWithToken(session, securityhub, results["NextToken"])
	
	print "%s findings sent to Splunk" % sent_count