import argparse
from vip_client import VipSession

apikey_filename = ".api_token.txt"


def login(api_key):
    VipSession.init(api_key=api_key)


def create_session(session_name):
    session = VipSession(session_name=session_name)
    return session


def download_outputs(session):
    session.download_outputs()


def show_pipeline():
    VipSession.show_pipeline()


def get_args():
    parser = argparse.ArgumentParser(description="Download Freesurfer Fuzzy Session")
    parser.add_argument(
        "--api-key", default=apikey_filename, type=str, help="API key for VIP"
    )
    parser.add_argument("--show-pipeline", action="store_true", help="Show pipeline")
    parser.add_argument(
        "--session-name", default="freesurfer-fuzzy", type=str, help="Session name"
    )
    return parser.parse_args()


def main():
    args = get_args()
    login(args.api_key)
    create_session(args.session_name)


if __name__ == "__main__":
    main()
