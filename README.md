# Purpose

This project takes a Dropbox share URL, downloads its content, and puts
it into an AWS S3 bucket.  It then exposes a public URL for the S3 bucket
and returns to the user.

The frontend is Slack's slash command.

The backend runs as an AWS lambda function.

# Configuration

## AWS Lambda

### Create a lambda function

I manually created a lambda function first instead of using the deploy.yml
to create one.  It's possible to automate the lambda function creation,
but the deploy.yml wasn't tested that way.

- go to AWS lambda and click "create a lambda function"
- under "select blueprint", select "blank function"
- click "Next"
- In "configure function"
    * name = max
    * runtime = python 2.7
    * handler = max.lambda_handler
    * role = I think this is what I did
    
        * select "create a custom role"
        * this brings you to another page
        * IAM role = create a new IAM Role
        * role name = fill in the role name, this is the role name to 
        be used in deploy.yml later
        * click "Allow"
    * click "Next"
    * click "create function"

### Configure a trigger

- go to the Lambda function page for max
- click on the "triggers tab" 
- click "add a trigger"
- click on the dotted box and select "API gateway"
- I think the first time around, you'll have to create a "deployment stage"

## Configure the API Gateway

- go to the AWS API Gateway page
- In the left most panel, select APIs -> LambdaMicroService -> Resources
- In the 2nd left most panel,
    * select /max, 
    * from the "actions" dropdown, 
    * select "create method"
    * select "POST"
- click on "POST", this brings the up the configuration for the "POST" 
  method in the right panel
  
  * click on "integration request" (right, top)
  * expand "body mapping templates"
  * for "request body passthrough", select "when there are no templates defined"
  * under "content-type", add a mapping template
  
    * name = aplication/x-www-form-urlencoded, this what slack uses
    * I got a mapping template from https://gist.github.com/ryanray/668022ad2432e38493df
    to translate the request to json.
- scroll down and click on "save"
- deploy the changes we made to the API gateway
    * In the 2nd left most panel, next to max, click on the "Actions" dropdown,
    * select "Deploy API"

## Slack

- Visit https://your_team_name.slack.com/services/new
- in the search bar, look for slash command
- click on "add configuration"
    * command = enter the name of your slash command, for example,
      /dropbox-download
    * URL = your lambda's URL
    * method = post
    * token = make a note of your token, you'll need it later
    * customize name = this is the name that will show up when the response
      is sent to you.  For example, Dropbox Download
    * click on "Save integration"
- go back to your slack message, now you should be able to type 
    /dropbox-download 

## Deploy

We use Ansible to automate deploy.

- Use ansible vault to create key.yml
  
  ansible-vault create key.yml
  
  It should one line:
  
  key: your_slack_token
  
- install python modules pytz and requests if not already installed
    These packages are needed for the function to run in lambda

    cd max      # this is the main directory
    pip install pytz -t .
    pip install requests -t .       # -t means to install into the given directory

    I have these version:
    
    pytz (2016.10)
    requests (2.12.4)

- install boto3 
    This is needed for Ansible to run locally. 
    This is not needed in lambda as AWS supplies this module.
   
    pip install boto3
    
    I have
    
    boto3 (1.4.4)

- This is not tested, but I suspect the "role" in the "deploy aws" task
of the ansible playbook needs to be created ahead of time.

- Deploy to AWS

    ansible-playbook -i localhost deploy.yml

# Try out the slash command

- From your slack message, type /dropbox-download and copy/paste the 
Dropbox share URL.