import argparse

from mailchimp_image_processor.profiles import ProfileStore, resolve_profile


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default=None)
    args = parser.parse_args()

    store = ProfileStore()
    profiles = store.load()
    profile = resolve_profile(profiles, cli_name=args.profile)
    print(f"Using profile: {profile.name}")
