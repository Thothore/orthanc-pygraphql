# pylint: disable=import-error
"""
Orthanc GraphQL endpoint implementation using Ariadne.
"""
import json

from ariadne import QueryType, graphql_sync, make_executable_schema

import orthanc

# 1. Define a simple GraphQL schema
TYPE_DEFS = """
    type Query {
        hello: String!
    }
"""

query = QueryType()


@query.field("hello")
def resolve_hello(_, _info):
    """Resolver for the 'hello' query."""
    return "Hello from Orthanc GraphQL!"


schema = make_executable_schema(TYPE_DEFS, query)


def graphql_endpoint(output, _url, **request):
    """REST callback injected into Orthanc for GraphQL endpoints."""
    if request['method'] != 'POST':
        output.SendMethodNotAllowed('POST')
        return

    try:
        # Parse the JSON body from the request
        data = json.loads(request['body'])

        # 2. Execute GraphQL query
        _, response = graphql_sync(schema,
                                   data,
                                   context_value=request,
                                   debug=True)

        # 3. Use AnswerBuffer to return HTTP 200 JSON response
        output.AnswerBuffer(json.dumps(response), 'application/json')

    except Exception as e:  # pylint: disable=broad-exception-caught
        # Fallback for parsing errors or other exceptions
        error_response = {"errors": [{"message": str(e)}]}
        output.AnswerBuffer(json.dumps(error_response), 'application/json')


orthanc.RegisterRestCallback('/graphql', graphql_endpoint)
