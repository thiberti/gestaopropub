from datetime import datetime


def formato_br(value):
    if not value or value == "":
        return ""

    try:
        data_obj = datetime.strptime(value, "%Y-%m-%d")
        return data_obj.strftime("%d/%m/%Y")
    except:
        return value