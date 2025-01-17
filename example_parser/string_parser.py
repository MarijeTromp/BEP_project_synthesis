from common.environment import StringEnvironment
from common.experiment import TestCase, Example
from example_parser.parser import Parser
from pathlib import Path


class StringParser(Parser):
    test_path = "examples/e2-strings/data/test/"

    def __init__(self, path: str = None, result_folder_path: str = None):
        super().__init__(
            domain_name="string",
            path=path or "examples/e2-strings/data/train/",
            result_folder_path=result_folder_path or "results/e2-strings/"
        )

    def _parse_file_lines(self, file_name: str, lines: 'list[str]') -> (list[Example], list[Example]):
        path = Path(__file__).parent.parent.joinpath(self.test_path)
        with open(path.joinpath(file_name), 'r') as file:
            test_lines = file.readlines()

        return list(map(StringParser._parse_single_line, lines)), list(map(StringParser._parse_single_line, test_lines))

    @staticmethod
    def _parse_single_line(line: str) -> Example:
        # remove unneeded characters
        line = line[4:-1]

        # split input and output
        entries = line.split("w(")[1:]

        return Example(
            StringParser._parse_entry(entries[0]),
            StringParser._parse_entry(entries[1]),
        )

    @staticmethod
    def _parse_entry(entry: str) -> StringEnvironment:
        # first entry before ',' is pointer position.
        pos = entry.split(",")[0]

        if entry.split(",")[2] == "[])).":
            ar = []
        else:
            # gets data between ',[' and '])' and picks every fourth character starting at index 1, which is the string.
            ar = entry.split(",['")[1].split("'])")[0].split("','")

        # for output data the position is not defined, however Environment needs one.
        if not pos.isnumeric():
            pos = 1

        return StringEnvironment(string_array=ar, pos=int(pos) - 1)

if __name__ == "__main__":
    res = StringParser().parse_file("1-97-1.pl")

    print(res.training_examples[0].input_environment)
    print(res.training_examples[0].output_environment)

    print(res.test_examples[0].input_environment)
    print(res.test_examples[0].output_environment)
