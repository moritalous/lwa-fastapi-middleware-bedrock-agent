import json
import logging
import typing
from urllib.parse import urlencode

from fastapi import Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, DispatchFunction
from starlette.types import ASGIApp

logger = logging.getLogger("bedrockagent-middleware")
logger.propagate = False

formatter = logging.Formatter("%(levelname)s:     %(message)s")
handler = logging.StreamHandler()
handler.setFormatter(formatter)


logger.addHandler(handler)


class BedrockAgentMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        dispatch: typing.Optional[DispatchFunction] = None,
        pass_through_path="/events",
    ):
        logger.info("pass_through_path: %s", pass_through_path)

        self.app = app
        self._pass_through_path = pass_through_path
        self.dispatch_func = self.dispatch if dispatch is None else dispatch

    async def dispatch(self, request, call_next):
        try:
            # Pass through any non-events requests
            if request.url.path != self._pass_through_path:
                return await call_next(request)

            # convert the request body to JSON object
            req_body = await request.body()
            req_body = json.loads(req_body)

            logger.debug(req_body)

            # Access request body keys with error handling
            api_path = req_body.get("apiPath")
            http_method = req_body.get("httpMethod")
            action_group = req_body.get("actionGroup")
            session_attributes = req_body.get("sessionAttributes")
            prompt_session_attributes = req_body.get("promptSessionAttributes")

            if None in (
                api_path,
                http_method,
                action_group,
                session_attributes,
                prompt_session_attributes,
            ):
                logger.error("Missing required keys in the request body")
                return JSONResponse(
                    content={"error": "Invalid request body"}, status_code=400
                )

            request.scope["path"] = api_path
            request.scope["method"] = http_method

            # Query params
            params = {}
            parameters = req_body.get("parameters", [])
            for item in parameters:
                params[item["name"]] = item["value"]
            request.scope["query_string"] = urlencode(params).encode()

            # Body
            content = req_body.get("requestBody", {}).get("content", None)
            if content:
                for key in content.keys():
                    content_type = key
                    break

                # Content type handling
                if not content_type:
                    logger.warning("Content type not found in request body")
                    return JSONResponse(
                        content={"error": "Content type not found"}, status_code=400
                    )

                data = {}
                content_val = content.get(content_type, {})
                for item in content_val.get("properties", []):
                    data[item["name"]] = item["value"]
                request._body = json.dumps(data).encode()

            # Pass the request to be processed by the rest of the application
            response = await call_next(request)

            # Process response body
            if isinstance(response, Response) and hasattr(response, "body"):
                res_body = response.body
            elif hasattr(response, "body_iterator"):
                res_body = b""
                async for chunk in response.body_iterator:
                    res_body += chunk
                response.body_iterator = self.recreate_iterator(res_body)
            else:
                res_body = None
            # Now you have the body, you can do whatever you want with it
            logger.debug("Response body: %s", res_body)

            res_status_code = response.status_code
            res_content_type = response.headers.get("content-type", "")

            # Build the response
            response = JSONResponse(
                content={
                    "messageVersion": "1.0",
                    "response": {
                        "actionGroup": action_group,
                        "apiPath": api_path,
                        "httpMethod": http_method,
                        "httpStatusCode": res_status_code,
                        "responseBody": {
                            res_content_type: {"body": res_body.decode("utf-8")}
                        },
                        "sessionAttributes": session_attributes,
                        "promptSessionAttributes": prompt_session_attributes,
                    },
                }
            )

            logger.debug("Response: %s", response)
            return response

        except Exception as e:
            logger.exception("An error occurred: %s", str(e))
            return JSONResponse(
                content={"error": "Internal Server Error"}, status_code=500
            )

    async def recreate_iterator(self, body):
        yield body
