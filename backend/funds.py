MOCK_PORTFOLIO = [
    {"scheme_code": "120503", "name": "Axis Small Cap Fund", "weight": 0.60},
    {"scheme_code": "100172", "name": "Quant Dynamic Bond Fund", "weight": 0.25},
    {"scheme_code": "120594", "name": "ICICI Pru Balanced Advantage Fund", "weight": 0.15},
]


def get_fund(scheme_code: str):
    for fund in MOCK_PORTFOLIO:
        if fund["scheme_code"] == scheme_code:
            return fund
    return None
