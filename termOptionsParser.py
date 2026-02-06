from Configuration import ConfigurationDict
from Option import Option
from common import shorthand_for


def _count_initial_occurences(data: str, to_count: str) -> int:
    result = 0
    for c in data:
        if c != to_count:
            break
        result += 1
    return result


def _option_to_config_dict_key(option: str) -> str:
    return option.replace('-', '_')


_MISSING_DATA_ERROR = "Data missing for {option} option. Provide data in the form: --{option}=data or --{option} data. Exiting..."


def termOptionsParser(shorthands: dict[str, Option], argv: list[str]) -> tuple[ConfigurationDict, str | None]:
    result: ConfigurationDict = {}
    config_path = None

    parsed_options: set[str] = set()
    data_for: str | None = None

    for i, arg in enumerate(argv):
        hyphens = _count_initial_occurences(arg, '-')

        if data_for is not None:
            if hyphens > 0:
                raise Exception(_MISSING_DATA_ERROR.format(option=data_for))

            if data_for == "config-path":
                config_path = arg
            else:
                result[_option_to_config_dict_key(
                    data_for)] = shorthands[shorthand_for(data_for)].type_fn(arg)

            data_for = None
            continue

        if hyphens > 0:
            option_value = arg.split('=', 1)
            arg_option = option_value[0][hyphens:]

            if arg_option in parsed_options:
                raise Exception(
                    f"Option repeated: {arg}. Please specify each option only once! Exiting...")

            match hyphens:
                case 1:
                    if arg_option not in shorthands:
                        raise Exception(
                            f"Unrecognized shorthand: {arg}. Exiting...")
                    parsed_options.update(
                        [arg_option, shorthands[arg_option].long_name])
                    # arg_option must contain the full option name at the end
                    arg_shorthand = arg_option
                    arg_option = shorthands[arg_option].long_name

                case 2:
                    if shorthand_for(arg_option) not in shorthands:
                        raise Exception(
                            f"Unrecognized option: {arg}. Exiting...")
                    parsed_options.update(
                        [arg_option, shorthand_for(arg_option)])
                    arg_shorthand = shorthand_for(arg_option)

                case _:
                    raise Exception(
                        f"Unrecognized argument: {arg}. Too many '-'s in the beginning. Exiting...")

            # Second element in the list must be the value if it's present
            if len(option_value) < 2:
                data_for = arg_option
            elif arg_option == "config-path":
                config_path = option_value[1]
            else:
                result[_option_to_config_dict_key(
                    arg_option)] = shorthands[arg_shorthand].type_fn(option_value[1])

        elif i != 0:  # First argument can be the script name
            raise Exception(
                f"Unrecognized argument: {arg}. Did you forget the '--' or '-' before the option name? Exiting...")

    if data_for is not None:
        raise Exception(_MISSING_DATA_ERROR.format(option=data_for))

    return result, config_path
