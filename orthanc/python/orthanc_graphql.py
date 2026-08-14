# pylint: disable=import-error
"""
Orthanc GraphQL endpoint implementation using Ariadne.
"""
import json

from ariadne import QueryType, graphql_sync, make_executable_schema

import orthanc

# 1. Define a GraphQL schema mirroring DICOM tags
TYPE_DEFS = """
    type Patient {
        id: ID!
        patientId: String!
        patientName: String!
        patientBirthDate: String
        patientSex: String
    }

    type Query {
        patients(limit: Int = 100, since: Int = 0): [Patient!]!
    }
"""

query = QueryType()


@query.field("patients")
def resolve_patients(_, _info, limit=100, since=0):
    """Resolver for the 'patients' query fetching from Orthanc API."""
    # Query Orthanc internal DB bypassing network overhead
    response = orthanc.RestApiGet(
        f'/patients?expand&limit={limit}&since={since}')

    # Parse the returned JSON string into python dicts
    patients_data = json.loads(response)

    results = []
    for p in patients_data:
        tags = p.get('MainDicomTags', {})
        results.append({
            'id': p.get('ID', ''),
            'patientId': tags.get('PatientID', ''),
            'patientName': tags.get('PatientName', ''),
            'patientBirthDate': tags.get('PatientBirthDate'),
            'patientSex': tags.get('PatientSex')
        })

    return results


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
