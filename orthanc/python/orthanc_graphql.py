# pylint: disable=import-error
"""
Orthanc GraphQL endpoint implementation using Ariadne.
"""
import json

from ariadne import ObjectType, QueryType, graphql_sync, make_executable_schema

import orthanc

# 1. Define a GraphQL schema mirroring DICOM tags
TYPE_DEFS = """
    type Instance {
        id: ID!
        sopInstanceUID: String!
        instanceNumber: String
    }

    type Series {
        id: ID!
        seriesInstanceUID: String!
        modality: String!
        seriesDescription: String
        seriesNumber: String
        manufacturer: String
        instances(limit: Int = 100): [Instance!]!
    }

    type Study {
        id: ID!
        studyInstanceUID: String!
        studyDate: String
        studyTime: String
        accessionNumber: String
        referringPhysicianName: String
        studyDescription: String
        series(limit: Int = 100): [Series!]!
    }

    type Patient {
        id: ID!
        patientId: String!
        patientName: String!
        patientBirthDate: String
        patientSex: String
        studies(limit: Int = 100): [Study!]!
    }

    type Query {
        patients(limit: Int = 100, since: Int = 0): [Patient!]!
    }
"""

query = QueryType()
patient_type = ObjectType("Patient")
study_type = ObjectType("Study")
series_type = ObjectType("Series")


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


@patient_type.field("studies")
def resolve_patient_studies(patient_obj, _info, limit=100):
    """Resolver bringing nested Studies for a given Patient."""
    # We must fetch the given patient ID's studies
    patient_id = patient_obj['id']
    # If the user queries > 100 limit, make sure to respect it, but limit is standard at 100
    response = orthanc.RestApiGet(f'/patients/{patient_id}')
    patient_details = json.loads(response)

    study_ids = patient_details.get("Studies", [])[:limit]

    results = []
    for study_id in study_ids:
        # expand the study details using RestApiGet
        s_resp = orthanc.RestApiGet(f'/studies/{study_id}')
        s = json.loads(s_resp)
        tags = s.get('MainDicomTags', {})
        results.append({
            'id': s.get('ID', ''),
            'studyInstanceUID': tags.get('StudyInstanceUID', ''),
            'studyDate': tags.get('StudyDate'),
            'studyTime': tags.get('StudyTime'),
            'accessionNumber': tags.get('AccessionNumber'),
            'referringPhysicianName': tags.get('ReferringPhysicianName'),
            'studyDescription': tags.get('StudyDescription')
        })
    return results


@study_type.field("series")
def resolve_study_series(study_obj, _info, limit=100):
    """Resolver bringing nested Series for a given Study."""
    study_id = study_obj['id']
    response = orthanc.RestApiGet(f'/studies/{study_id}')
    study_details = json.loads(response)

    series_ids = study_details.get("Series", [])[:limit]

    results = []
    for series_id in series_ids:
        s_resp = orthanc.RestApiGet(f'/series/{series_id}')
        s = json.loads(s_resp)
        tags = s.get('MainDicomTags', {})
        results.append({
            'id': s.get('ID', ''),
            'seriesInstanceUID': tags.get('SeriesInstanceUID', ''),
            'modality': tags.get('Modality', ''),
            'seriesDescription': tags.get('SeriesDescription'),
            'seriesNumber': tags.get('SeriesNumber'),
            'manufacturer': tags.get('Manufacturer')
        })
    return results


@series_type.field("instances")
def resolve_series_instances(series_obj, _info, limit=100):
    """Resolver bringing nested Instances for a given Series."""
    series_id = series_obj['id']
    response = orthanc.RestApiGet(f'/series/{series_id}')
    series_details = json.loads(response)

    instance_ids = series_details.get("Instances", [])[:limit]

    results = []
    for instance_id in instance_ids:
        i_resp = orthanc.RestApiGet(f'/instances/{instance_id}')
        i = json.loads(i_resp)
        tags = i.get('MainDicomTags', {})
        results.append({
            'id': i.get('ID', ''),
            'sopInstanceUID': tags.get('SOPInstanceUID', ''),
            'instanceNumber': tags.get('InstanceNumber')
        })
    return results


schema = make_executable_schema(TYPE_DEFS, query, patient_type, study_type,
                                series_type)


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
