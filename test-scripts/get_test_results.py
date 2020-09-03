# This script parses the generated json test results and
# injects them into the taskcat generated html dashboard
# and publishes messages to the SNS topic when an error is found

import boto3
import sys
import re
from bs4 import BeautifulSoup
import json

region = sys.argv[1]
folder = sys.argv[2]
topic_arn = sys.argv[3]
result_bucket = sys.argv[4]

test_log_file = 'test-scripts/test_output_' + region + '.json'

with open('taskcat_outputs/index.html') as fp:
	soup = BeautifulSoup(fp, 'html.parser')
	stack_name = soup.find('td', text = re.compile(region)).parent.contents[5].string.strip()
	print(stack_name)

	with open(test_log_file) as f:
		test_results = json.load(f)
		for test in test_results["Page Access Info"]:
			test_name = test["tag"] + ": " + test["test"]
			test_results = test["status"]
			# create tags to append to dashboard
			new_row = soup.new_tag("tr")
			new_test_name = soup.new_tag("td", attrs={"class": "test-info"})
			new_h3_text = soup.new_tag("h3")
			new_h3_text.string = test_name
			new_test_name.append(new_h3_text)
			new_region = soup.new_tag("td", attrs={"class": "test-left"})
			new_region.string = region
			new_stack = soup.new_tag("td", attrs={"class": "test-left"})
			new_stack.string = stack_name
			new_test_result = None
			if(test_results == "SUCCESS"):
				new_test_result = soup.new_tag("td", attrs={"class": "test-green"})
			else:
				# Send an error message if a failure is found
				new_test_result = soup.new_tag("td", attrs={"class": "test-red"})
				print("FAILURE found")
				client = boto3.client('sns')
				response = client.publish(
					TopicArn = topic_arn,
					Message = test["message"] + "\n Extra information: \n" + json.dumps(test["extra"]) + "\n Dashboard: \n https://" + result_bucket +".s3.amazonaws.com/index2.html" ,
					Subject = 'Clouformation Testing Pipeline Internal Test Failure'
				)
			new_test_result.string = test_results
			new_logs = soup.new_tag("td", attrs={"class": "test-left"})
			new_link = soup.new_tag("a", href = "https://" + result_bucket + ".s3.amazonaws.com/" + folder + "/" + test_log_file)
			new_link.string = "View Logs"
			new_logs.append(new_link)

			new_row.append(new_test_name)
			new_row.append(new_region)
			new_row.append(new_stack)
			new_row.append(new_test_result)
			new_row.append(new_logs)
			soup.thread.append(new_row)

		with open("./taskcat_outputs/index2.html", "w") as file:
			file.write(str(soup))
