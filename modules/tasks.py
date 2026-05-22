import json
from modules import db_engine

def get_template_names():
    templates = db_engine.load_templates()
    return list(templates.keys())

def get_tasks_from_template(template_name):
    templates = db_engine.load_templates()
    return [dict(task) for task in templates.get(template_name, [])]

def parse_sub_tasks(sub_tasks_str):
    try:
        return json.loads(sub_tasks_str)
    except:
        return []
