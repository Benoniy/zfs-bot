import json
import log_report


def save_json(file_name, json_dict):
    json_data = json.dumps(json_dict, indent=4)
    file = open(file_name, "w")
    file.write(json_data)
    file.close()
    log_report.log_info("{} Saved json configuration".format(file_name))


def load_json(file_name):
    file = open(file_name, "r")
    content = '\r'.join(file.readlines())
    json_data = json.loads(content)
    file.close()
    log_report.log_info("{} Loaded stored json configuration".format(file_name))
    return json_data
