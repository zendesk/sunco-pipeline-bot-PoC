# Using this code

## Pre-setup: be sure to

1. Install Python3.9 (+pip3)
    1. create & acitvate virtual environment: `python3 -m venv amb_venv && source amb_venv/bin/activate`
    1. install required python packages: `pip3 install smooch boto3`
1. Install Serverless Framework
    1. Be able to deploy a [sample project](https://serverless.com/framework/docs/providers/aws/examples/hello-world/) to AWS using serverless
    1. Install additional python-requirements package: `npm install -g serverless-python-requirements`
1. Deploy the project to aws: `sls deploy`
    * 📝 note your service's POST endpoints (used in the next API-call)
1. Setup your Smooch app: (most steps are commented out as part of `linkBot2App()`)
    1. Create your pipeline processor object (webhook):
        * `POST @ {{url}}/v1/middleware/processors`
        * Body: `{ "target" : "https://<UNIQUE-ID>.execute-api.us-west-2.amazonaws.com/dev/pipelineEvent","triggers": ["message:appUser", "postback"] }`
            * `<UNIQUE-ID>` [the full URL, actually] will come from the deploy step's output
        * 📝 Note the `processor._id` in the response (used in the next API-call)
        * 📝 Note the `processor.secret` in the response (used in the DynamoDB object)
    1. Read/Update to add your processor to the `appuser` pipeline
        * `PUT @ {{url}}/v1/middleware/pipelines/appuser`
        * Body: `[ "<processor._id>" ]`
    1. Create your Apple-interactive passthrough webhook
        * `POST @ {{url}}/v1.1/apps/{{appId}}/webhooks`
        * Body: `{ "target": "https://<UNIQUE-ID>.execute-api.us-west-2.amazonaws.com/dev/applePassthroughEvent", "triggers": ["passthrough:apple:interactive"] }`
        * 📝 Note the `webhook.secret` in the response (used in the DynamoDB object)
    1. create a webhook for events when customer blocks the business (`client:update`) as well as group, intent and `capabilityList` (`conversation:create`) for new contacts
        * `POST @ {{url}}/v2/apps/{{appId}}/integrations`
        * Body: `{ "webhooks": [{ "version": "v2", "target": "https://webhook.site/02707106-f7ac-4205-9ac7-c5fd5aa512bb", "triggers": ["client:update", "conversation:create"], }], "type": "custom" }`
1. Prepare your DynamoDb table+entry:
    1. [Default] Table name: `AMB-pipeline-bot-PoC-dev-integratedApps` (created by serverless.yml values) accessible from the [AWS console: DynamoDB](https://us-west-2.console.aws.amazon.com/dynamodbv2/home?region=us-west-2#tables)
    1. Create a new entry for your now-configured app (example below)
1. Setup AMB channel for testing
    * login to register.apple.com
        * get your BusinessId
        * copy your `Conversational link` e.g.: `https://register.apple.com/messages/<buinessId>/review`
    * integrate using app.smooch.io (dashboard or Advocacy assistance required)
1. click the link from a Mac or i-device to test

Your bot should now be functional and [auto-]responding!

You can customize/update your responses in responses.json file and then `sls deploy`

## Bot behaviour

### Hard-coded `>>do>>` commands

### Usage of responses.json

The responses file scripts the responses that the bot will send to unescalated users, when a match is found.
Key groups are:
<< COMING SOON >>

## Examples

### DynamoDB 'approved Apps' table entry

``` json
{
    "appId": "5da8xxxxxxxxxxxxxxxx2852",
    "JWT": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImFwcF81ZGE4eHh4eHh4eHh4eHh4eHh4eDg3YTIifQ.eyJzY29wZSI6ImFwcCIsImlhdCI6MTU3MTMxODg4Mn0.<signature>",
    "owner": "My-PoC",
    "processorId": "5da8xxxxxxxxxxxxxxxx626f",
    "processorSecret": "gUECxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxKyzw",
    "webhookSecret": "nth8xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxSG4A"
}
```

## Common issues

### My bot is replying multiple times for each user message sent

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

### "ERROR: No 'Item' in db response: ..." error in CloudWatch logs

...but there is an entry for my app in the table!
Is it in the same AWS region as the project is deployed to? (serverless.yml, `sls deploy` and `sls info` output include a line for `region`)
