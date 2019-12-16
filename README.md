# Be sure to

1. deploy to aws and note your service's POST endpoint
1. setup your Smooch app: (most steps are commented out as part of `linkBot2App()`)
    1. create your pipeline processor object (webhook)
    1. add your processor to the `appuser` pipeline
1. create an entry in your DynamoDb table for your [configured] app, as in the example below
1. for `minimial_widget.html`:
    * replace `<<smooch appId Here>>` with your smooch appId (it should still be within single-`'` or double-quotes`"`
    * for best results, serve the `minimal_widget.html` page via a server (e.g.: `python -m SimpleHTTPServer 80`)
1. Keep track of execution times:
    * Lambda has a default timeout of 6 sec (configurable up to 5 mins)
    * API Gateway has a hard-timeout at 29 sec (!?)
    * lots of replies to a given trigger take longer to process (**including** nested responses due to `>>react>>X`)
    * images/media also take longer (consider pre-uploading files to media.smooch.io for best results)
    * `>>do>>sleepX` also adds `X` seconds of execution time

# Examples
## DynamoDB 'approved Apps' table entry
    {
    "appId": "5da8xxxxxxxxxxxxxxxx2852",
    "JWT": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImFwcF81ZGE4eHh4eHh4eHh4eHh4eHh4eDg3YTIifQ.eyJzY29wZSI6ImFwcCIsImlhdCI6MTU3MTMxODg4Mn0.<signature>",
    "owner": "My-PoC",
    "processorId": "5da8xxxxxxxxxxxxxxxx626f",
    "processorSecret": "gUECxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxKyzw"
    }

You can customize your responses in responses.json file and then `sls deploy`
