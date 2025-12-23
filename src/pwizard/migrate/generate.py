from datetime import datetime
from pathlib import Path

from jinja2 import Template


def generate_new_migration(
    output_path: Path,
    template: Template,
    name: str,
    description: str | None = None,
):
    # build the data for the template
    data = {
        "generated_at": datetime.now(),
        "name": name,
        "description": description,
    }

    # generate the output
    with open(output_path, "w") as f:
        for s in template.generate(**data):
            f.write(s)
