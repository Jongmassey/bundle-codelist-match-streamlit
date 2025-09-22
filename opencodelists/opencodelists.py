import requests as rq


ORGANISATIONS = [
    "ebm-datalab",
    "exeter",
    "lshtm",
    "guest",
    "ardens",
    "opensafely-collaborators",
    "opensafely",
    "qmul-multimorbidity",
    "primis-covid19-vacc-uptake-old",
    "primis-covid19-vacc-uptake",
    "qcovid",
    "nhsd-primary-care-domain-refsets",
    "openprescribing",
    "recovery",
    "pincer",
    "nhsbsa",
    "nhsd",
    "prescqipp",
    "bristol",
    "ons",
    "phc",
    "ukrr",
    "ukhsa",
    "multiply-qmul",
    "nhs-devon",
    "reducehf",
    "ihme",
]

AUTOMATED_UPLOAD_ORGS = [
    "nhsd-primary-care-domain-refsets",
    "primis-covid19-vacc-uptake-old",
    "primis-covid19-vacc-uptake",
]

BASE_URL = "https://www.opencodelists.org"
API_BASE_URL = BASE_URL + "/api/v1/codelist/"


def get_codelists(organisation):
    params = (
        {"description": True, "methodology": True}
        if organisation not in AUTOMATED_UPLOAD_ORGS
        else {}
    )
    if organisation not in ORGANISATIONS:
        raise ValueError(f"Unknown organisation {organisation}")
    response = rq.get(f"{API_BASE_URL}{organisation}/", params=params)
    response.raise_for_status()
    codelists = response.json()["codelists"]
    return [
        {
            "name": codelist["name"],
            "url": f"{BASE_URL}/codelist/{codelist['full_slug']}",
            "methodology": codelist["methodology"],
            "description": codelist["description"],
        }
        if params
        else {
            "name": codelist["name"],
            "url": f"{BASE_URL}/codelist/{codelist['full_slug']}",
        }
        for codelist in codelists
    ]
