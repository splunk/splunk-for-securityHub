## 0.2.1 - 10/1/2019
* migrate to prefered push GDI path over olld poller via Splunk Project: Trumoet


## 0.1.1 - 2/5/2019

* Hostname parser updated to support arbitrary HTTP Event Collector port configuration. Default port when none is specified in the provided SPLUNK_HEC_HOST is 443
* Error handling and logging improved
* SecurityHubToSplunkLambdaVerbose.zip file added to enable verbose logging when debugging
* Lambda timeout set to 840 seconds
* Lambda memory size set to 256