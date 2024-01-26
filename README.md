# FastAPI Middleware for "Agents for Amazon Bedrock"

This is FastAPI Middleware for "Agents for Amazon Bedrock". Use with [AWS Lambda Web Adapter](https://github.com/awslabs/aws-lambda-web-adapter).

Agents for Amazon Bedrock requires:

* Lambda function that defines the business logic for the action that your agent will carry out. 
* OpenAPI schema with the API description, structure, and parameters for the action group.

By using this middleware, you can create Lambda as a FastAPI. OpenAPI schemas can also be easily generated.


## How to install

```shell
pip install lwa-fastapi-middleware-bedrock-agent
```

## How to use

```shell
from bedrock_agent.middleware import BedrockAgentMiddleware
from fastapi import FastAPI

app = FastAPI(
    description="This agent allows you to query the information.",
)
app.add_middleware(BedrockAgentMiddleware)
```

If you specified AWS_LWA_PASS_THROUGH_PATH, add the `pass_through_path` parameter. (Default is "/events")

```
app.add_middleware(BedrockAgentMiddleware, pass_through_path="/pass_through_path")
```

## Example

Examples are located in the [example](./example/) directory

## License

This project is licensed under the MIT License.
