import os
import glob


def get_logs():
    logs = {}
    logs_files = glob.glob("rep*/*/scripts/recon-all-.log")
    for log in logs_files:
        rep = os.path.split(log)[0]
        logs[rep] = logs.get(rep, []) + [log]
    return logs


def get_last_line(filename):
    with open(filename, "rb") as file:
        try:
            file.seek(-2, os.SEEK_END)
            while file.read(1) != b"\n":
                file.seek(-2, os.SEEK_CUR)
        except OSError:
            file.seek(0)
        last_line = file.readline().decode()
    return last_line


def parse_log(logs):
    for rep, log_list in logs.items():
        print(rep)
        for log in log_list:
            last_line = get_last_line(log)
            if "finished without error" not in last_line:
                print(log)


def main():
    logs = get_logs()
    parse_log(logs)


if __name__ == "__main__":
    main()
