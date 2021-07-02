import glob
import os
import re

import django
import yaml
from django.apps import apps
from django.conf import settings

django.setup()

STRINGS_FILE_NAME = "fix_strings.yaml"

app_config = apps.get_app_config("rules")
app_label = app_config.label
fixtures_dir = os.path.join(app_config.path, "fixtures")

language_code = settings.LANGUAGE_CODE
translated_language_codes = [tl[0] for tl in settings.LANGUAGES if tl[0] != language_code]
translated_language_keys_re = re.compile("|".join([f"^(.*)_{tl}$" for tl in translated_language_codes]))


def export_strings():
    print("Exporting fixture strings for translation")
    output = {language_code: {}}

    for fixture_path in glob.glob(os.path.join(fixtures_dir, "*.yaml")):
        with open(fixture_path, "r+") as fixture_file:
            fixture = yaml.safe_load(fixture_file)
            if not fixture:
                continue
            print(f"Found fixture at: {fixture_path}")

            for o in fixture:
                for k, v in o["fields"].items():
                    if (match := translated_language_keys_re.match(k)) is not None:
                        orig_key = f"{match.group(1)}_{language_code}"
                        orig_value = o["fields"][orig_key]
                        if orig_value:
                            output[language_code][f"{o['model']}.{o['pk']}.{match.group(1)}"] = orig_value

    output_path = os.path.join(settings.LOCALE_PATHS[0], language_code, STRINGS_FILE_NAME)
    with open(output_path, "w") as output_file:
        print(f"Exporting strings to: {output_path}")
        yaml.dump(output, output_file)


def import_translations():
    print("Importing fixture translations")
    for lc in translated_language_codes:
        print(f"Looking for {lc} translations")
        translated_strings_path = os.path.join(settings.LOCALE_PATHS[0], lc, STRINGS_FILE_NAME)
        if not os.path.exists(translated_strings_path):
            continue

        print(f"Found {lc} translations")
        with open(translated_strings_path, "r") as translated_strings_file:
            translated_strings = yaml.safe_load(translated_strings_file)[language_code]
            for fixture_path in glob.glob(os.path.join(fixtures_dir, "*.yaml")):
                with open(fixture_path, "r+") as fixture_file:
                    fixture = yaml.safe_load(fixture_file)
                    if not fixture:
                        continue
                    print(f"Found fixture at: {fixture_path}")
                    for o in fixture:
                        for k, v in o["fields"].items():
                            if (match := translated_language_keys_re.match(k)) is not None:
                                string_key = f"{o['model']}.{o['pk']}.{match.group(1)}"
                                if string_key in translated_strings and translated_strings[string_key]:
                                    print(f"Updating {string_key}")
                                    o["fields"][k] = translated_strings[string_key]
                    print(f"Updating fixture")
                    fixture_file.seek(0)
                    yaml.dump(fixture, fixture_file)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--export", action="store_true", help="Export strings from fixture files to be uploaded to translation service."
    )
    group.add_argument("--import", action="store_true", help="Import translations from translation setvice into fixture files.")
    args = parser.parse_args()

    if args.export:
        export_strings()
    else:
        import_translations()
