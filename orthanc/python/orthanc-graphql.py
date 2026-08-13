import json
import orthanc
from ariadne import QueryType, make_executable_schema, graphql_sync

# 1. Define a simple GraphQL schema
type_defs = """
    type Query {
        hello: String!
    }
"""

query = QueryType()

@query.field("hello")
def resolve_hello(_, info):
    return "Hello from Orthanc GraphQL!"

schema = make_executable_schema(type_defs, query)

def graphql_endpoint(output, url, **request):
    if request['method'] != 'POST':
        output.SendMethodNotAllowed('POST')
        return

    try:
        # Parse the JSON body from the request
        data = json.loads(request['body'])
        
        # 2. Execute GraphQL query
        success, response = graphql_sync(
            schema,
            data,
            context_value=request,
            debug=True
        )
        
        # 3. Use AnswerBuffer to return HTTP 200 JSON response
        output.AnswerBuffer(json.dumps(response), 'application/json')
        
    except Exception as e:
        # Fallback for parsing errors or other exceptions
        error_response = {"errors": [{"message": str(e)}]}
        output.AnswerBuffer(json.dumps(error_response), 'application/json')

orthanc.RegisterRestCallback('/graphql', graphql_endpoint)