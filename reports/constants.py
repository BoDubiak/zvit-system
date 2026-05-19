SMALL_REPORT_SCHEMA = "S0110014"
FULL_REQUIRED_REPORT_SCHEMAS = ["S0100115", "S0100215"]
FULL_OPTIONAL_REPORT_SCHEMAS = ["S0100311", "S0104010", "S0105009"]
FULL_REPORT_SCHEMAS = [*FULL_REQUIRED_REPORT_SCHEMAS, *FULL_OPTIONAL_REPORT_SCHEMAS]

DEFAULT_REPORT_FORMS = [
    {
        "code": "J0901107",
        "xml_schema": "S0110014",
        "name": "Фінансова звітність малого підприємства",
    },
    {"code": "J0900108", "xml_schema": "S0100115", "name": "Баланс, форма №1"},
    {"code": "J0900207", "xml_schema": "S0100215", "name": "Звіт про фінансові результати, форма №2"},
    {"code": "J0900904", "xml_schema": "S0100311", "name": "Звіт про рух грошових коштів, форма №3"},
    {"code": "J0901005", "xml_schema": "S0104010", "name": "Звіт про власний капітал, форма №4"},
    {"code": "J0901301", "xml_schema": "S0105009", "name": "Примітки до річної фінансової звітності, форма №5"},
]

QUARTER_BY_MONTH = {
    "3": "Q1",
    "03": "Q1",
    "6": "Q2",
    "06": "Q2",
    "9": "Q3",
    "09": "Q3",
    "12": "Q4",
}
