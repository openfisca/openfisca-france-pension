import re

# This script fetches and prints the minimal versions of Openfisca-Core and Openfisca-France-Pension
# dependencies in order to ensure their compatibility during CI testing
with open('./setup.py') as file:
    for line in file:
        version = re.search(r'(Core|France-Pension)\s*>=\s*([\d\.]*)', line)  # Use when proper core version will be used
        # version = re.search(r'(France-Pension)\s*>=\s*([\d\.]*)', line)
        if version:
            print(f'Openfisca-{version[1]}=={version[2]}')  # noqa: T201 <- This is to avoid flake8 print detection.
