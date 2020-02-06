# Be sure to

1. Install Python3.7 (+pip3)
1. Install Serverless Framework
    1. Be able to deploy a sample project to AWS using serverless: https://serverless.com/framework/docs/providers/aws/examples/hello-world/
    1. Install additional python-requirements package: `npm install serverless-python-requirements`
1. Deploy the project to aws and note your service's POST endpoint
1. Setup your Smooch app: (most steps are commented out as part of `linkBot2App()`)
    1. Create your pipeline processor object (webhook)
        * `triggers: ["message:appUser", "postback"]`, and
        * the endpoint from the previous step as `target`
    1. Read/Update to add your processor to the `appuser` pipeline
1. Prepare your DynamoDb table+entry:
    1. [Default] Table name: `bot-selfserve-escalation-dev-integratedApps` (based on default serverless.yml values)
    1. Entry for your now-configured app (example below)
1. If you are using WebSDK as a channel via `minimial_widget.html`:
    * replace `<<smooch appId Here>>` with your smooch appId (it should still be within single-`'` or double-quotes`"`
    * for best results, serve the `minimal_widget.html` page via a server (e.g.: `python3 -m http.server 80`)

Your bot should now be functional and [auto-]responding!

You can customize/update your responses in responses.json file and then `sls deploy`

# Bot behaviour
## Hard-coded `>>do>>` commands
## Usage of responses.json
The responses file scripts the responses that the bot will send to unescalated users, when a match is found.
Key groups are:
<< COMING SOON >>

# Examples
## DynamoDB 'approved Apps' table entry
    {
    "appId": "5da8xxxxxxxxxxxxxxxx2852",
    "JWT": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImFwcF81ZGE4eHh4eHh4eHh4eHh4eHh4eDg3YTIifQ.eyJzY29wZSI6ImFwcCIsImlhdCI6MTU3MTMxODg4Mn0.<signature>",
    "owner": "My-PoC",
    "processorId": "5da8xxxxxxxxxxxxxxxx626f",
    "processorSecret": "gUECxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxKyzw"
    }

# Common issues
## My bot is replying multiple times for each user message sent
If the bot does not reply `200` to the SunCo pipeline webhook event, SunCo will auto-retry delivery of the message up to 5 times over the next 10-15 minutes - the bot will reply independently to each of these retries.
2 main causes for not replying `200` are
1. Execution timeout:
    * Lambda has a default timeout of 6 sec (configurable up to 5 mins)
    * API Gateway has a hard-timeout at 29 sec (!?)
    * sending multiple messages in response to a given trigger **take longer to process** (_**including**_ nested responses due to `>>react>>X`)
    * images/media also take longer (consider pre-uploading frequently-used files to media.smooch.io for best results)
    * `>>do>>sleepX` also adds `X` seconds of execution time
2. Runtime errors:
    * Check CloudWatch logs for details
    
## "ERROR: No 'Item' in db response: ..." error in CloudWatch logs
...but there is an entry for my app in the table!
Is it in the same AWS region as the project is deployed to? (serverless.yml, `sls deploy` and `sls info` output include a line for `region`)
