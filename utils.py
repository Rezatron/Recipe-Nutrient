def clean_micro_nutrients(data):
    cleaned_micro_nutrients = {}
    for key, value in data.items():
        quantity = round(value['quantity'])
        cleaned_micro_nutrients[value['label']] = quantity
    return cleaned_micro_nutrients