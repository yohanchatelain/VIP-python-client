import pandas as pd


class FSGDParser:
    """
    https://surfer.nmr.mgh.harvard.edu/fswiki/FsgdFormat
    Notes:
    * The first line must be "GroupDescriptorFile 1".
    * Title is not necessary. This will be used for display.
    * CLASS only needs the class name, the next two items (eg, "plus blue)" will be used in the display.
    * The third input is ignored because of the hash (#).
    * DefaultVariable is the default variable for display.
    * SomeTag is not a valid tag, so it will be ignored.
    General Rules:
    * Each subject is represented by an Input tag.
    * The order of the subjects is not important but you must make sure it is consistent with the input to mri_glmfit (--y).
    * Each subject must have values for all variables (no empty cells)
    * Tags are NOT case sensitive.
    * Labels are case sensitive.
    * When multiple items appear on a line, they can be separated by any white space (ie, blank or tab).
    * Any line where # appears as the first non-white space character is ignored (ie, it is treated as a comment).
    * The Variables line should appear before the first Input line.
    * All Class lines should appear before the first Input line.
    * Variable label replications are not allowed.
    * Class label replications are not allowed.
    * If a class label is not used, a warning is printed out.
    * The DefaultVariable must be a member of the Variable list.
    * No error is generated if a tag does not match an expected keyword.
    * Empty lines are OK.
    * A class label can optionally be followed by a class marker.
    * A class marker can optionally be followed by a class color.
    """

    def __init__(self, filename, input_name="input", class_name="class"):
        self.filename = filename
        self.classes = []
        self.columns = [input_name, class_name]
        self.data = {}

    def parse(self):
        with open(self.filename, "r", encoding="utf-8") as fi:
            self.parse_header(fi)
            self.parse_row(fi)

    def parse_class(self, line):
        fields = line.split()
        self.classes.append(fields[1])

    def parse_variables(self, line):
        fields = line.split()
        self.columns.extend(fields[1:])

    def parse_header(self, fi):
        while not (line := fi.readline().strip()).startswith("Input"):
            if line.startswith("GroupDescriptorFile"):
                continue
            if line.startswith("Title"):
                continue
            if line.startswith("Class"):
                self.parse_class(line)
            if line.startswith("Variables"):
                self.parse_variables(line)

        empty_list = [[] for _ in range(len(self.columns))]
        self.data.update(zip(self.columns, empty_list))

    def parse_row(self, fi):
        for line in fi:
            fields = line.split()[1:]
            for column, data in zip(self.columns, fields):
                self.data[column].append(data)

    def as_dataframe(self):
        return pd.DataFrame(data=self.data)


def _main():
    import sys

    if len(sys.argv) == 1:
        print("python3 fsgd_parser.py <filename> [input_name] [class_name]")
        sys.exit(0)

    argnames = ["filename", "input_name", "class_name"]
    kwargs = dict(zip(argnames, sys.argv[1:]))

    parser = FSGDParser(**kwargs)
    parser.parse()
    df = parser.as_dataframe()
    print(df)


if "__main__" == __name__:
    _main()
