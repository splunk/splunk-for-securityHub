import json
import datetime
import dateutil
import os
import sys
import time
from splunk_http_event_collector import http_event_collector

envLambdaTaskRoot = os.environ['LAMBDA_TASK_ROOT']
sys.path.insert(0, envLambdaTaskRoot + '/NewBotoVersion')
import boto3

# Gets the time 60 minutes ago
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
	    	'Text': 'SENT TO SPLUNK: %s' % existing_note,
	    	'UpdatedBy': principal
	    }
	)

# Gets 20 findings from securityhub using the NextToken from a previous request
def getFindingsWithToken(session, securityhub, token, filters={}):
	return securityhub.get_findings(
	    Filters=filters,
	    NextToken=token
	)

# Isolates host, port, and path from the provided host string. Default is port 443
def hostIsolator(host):
	parsed_port = 8088

	protocol_split = host.split('://')
	protocol = protocol_split[0]
	host_port_path = protocol_split[1]
	potential_host = host_port_path.split(':')

	# No port provided in url string
	if (len(potential_host) == 1):
		# Set default port
		if (protocol == 'https'):
			parsed_port = '443'
		potential_path = potential_host[0].split('/', 1)
		# No path provided in url string
		if (len(potential_path) == 1):
			parsed_host = potential_path[0]
			parsed_path = ''
		# Path provided in url string
		else:
			parsed_host = potential_path[0]
			parsed_path = '/' + potential_path[1]\
	# Port provided in url string
	else:
		parsed_host = potential_host[0]
		potential_port_path = potential_host[1].split('/', 1)
		# No path provided in url string
		if (len(potential_port_path) == 1):
			parsed_port = potential_port_path[0]
			parsed_path = ''
		# Path provided in url string
		else:
			parsed_port = potential_port_path[0]
			parsed_path = '/' + potential_port_path[1]

	return parsed_host, parsed_port, parsed_path

def lambda_handler(event, context):
	http_event_collector_token = os.environ['SPLUNK_HEC_TOKEN']
	http_event_collector_host, http_event_collector_port, http_event_collector_path = hostIsolator(os.environ['SPLUNK_HEC_HOST'])

	eventSenderJSON = http_event_collector(http_event_collector_token, http_event_collector_host, 'json', http_event_port=http_event_collector_port)
	eventSenderJSON.debug = True
    
	session = boto3.session.Session()
	securityhub = session.client('securityhub',region_name=os.environ['AWS_REGION'])
	
	results = getFindings(session, securityhub)
	
	fresh_events_after_this_time = freshEventTimestampGenerator()
	fresh_events = True
	first_call = True
	sent_count = 0
	
	while ((first_call or 'NextToken' in results) and fresh_events):
		# Loop through all findings (20 by default) returned by Security Hub API call
		# If finding has the string "SENT TO SPLUNK" in the finding note, the event is not sent but
		# loop will continue.
		# Fresh events will be sent to Splunk over HTTP Event Collector (HEC), "SENT TO SPLUNK" will
		# be prefixed to the finding's note.
		# Break out of the loop when we have looked back across the last hour of events (based on the
		# finding's LastObservedAt timestamp)
		first_call = False

		for finding in results['Findings']:
			finding_timestamp = findingTimestampGenerator(finding['LastObservedAt'])
			already_sent = False
			existing_note = ''
			principal = 'SplunkSecurityHubLambda'
			
			if 'Note' in finding:
				if 'SENT TO SPLUNK:' in finding['Note']['Text']:
					already_sent = True
				else:
					existing_note = finding['Note']['Text']
					principal = finding['Note']['UpdatedBy']
			
			if (finding_timestamp > fresh_events_after_this_time and not already_sent):
				payload = {}
				payload.update({'sourcetype':'aws:securityhub'})
				payload.update({'event':json.dumps(finding)})
				
				filters = {
					'Id': [
				         { 
				            'Comparison': 'EQUALS',
				            'Value': finding['Id']
				         }
				      ],
				    'LastObservedAt': [
				         { 
				            'Start': finding['LastObservedAt'],
				            'End': finding['LastObservedAt']
				         }
				      ],
				}

				eventSenderJSON.sendEvent(payload)

				if not eventSenderJSON.failedToSend:
					print('Event successfully sent to Splunk')
					eventSenderJSON.failedToSend = False
					updateFindingNote(session, securityhub, existing_note, principal, filters)
					sent_count += 1
				else:
					print('Event NOT successfully sent to Splunk')
			else:
				fresh_events = False
				break
		if (fresh_events):
			results = getFindingsWithToken(session, securityhub, results['NextToken'])

	print '%s findings sent to Splunk: %s' % (sent_count, eventSenderJSON.server_uri)