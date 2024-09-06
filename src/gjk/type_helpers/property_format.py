import uuid
from datetime import datetime, timezone
from typing import Annotated

from pydantic import BeforeValidator


def check_is_ads1115_i2c_address(v: str) -> None:
    """
    Ads1115I2cAddress: ToLower(v) in  ['0x48', '0x49', '0x4a', '0x4b'].

    One of the 4 allowable I2C addresses for Texas Instrument Ads1115 chips.

    Raises:
        ValueError: if not Ads1115I2cAddress format
    """
    if v.lower() not in ["0x48", "0x49", "0x4a", "0x4b"]:
        raise ValueError(f"Not Ads1115I2cAddress: <{v}>")


def check_is_handle_name(v: str) -> None:
    """Check HandleName Format.

    Validates if the provided string adheres to the HandleName format:
    words separated by periods, where the worlds are lowercase alphanumeric plus hyphens

    Args:
        candidate (str): The string to be validated.

    Raises:
        ValueError: If the provided string is not in HandleName format.
    """
    try:
        x = v.split(".")
    except Exception as e:
        raise ValueError(f"Failed to seperate <{v}> into words with split'.'") from e
    first_word = x[0]
    first_char = first_word[0]
    if not first_char.isalpha():
        raise ValueError(
            f"Most significant word of <{v}> must start with alphabet char."
        )
    for word in x:
        for char in word:
            if not (char.isalnum() or char == "-"):
                raise ValueError(
                    f"words of <{v}> split by by '.' must be alphanumeric or hyphen."
                )
    if not v.islower():
        raise ValueError(f" <{v}> must be lowercase.")


def check_is_hex_char(v: str) -> None:
    """Checks HexChar format

    HexChar format: single-char string in '0123456789abcdefABCDEF'

    Args:
        v (str): the candidate

    Raises:
        ValueError: if v is not HexChar format
    """
    if len(v) > 1:
        raise ValueError(f"<{v}> must be a hex char, but not of len 1")
    if v not in "0123456789abcdefABCDEF":
        raise ValueError(f"<{v}> must be one of '0123456789abcdefABCDEF'")


def check_is_left_right_dot(v: str) -> None:
    """Checks LeftRightDot Format

    LeftRightDot format: Lowercase alphanumeric words separated by periods, with
    the most significant word (on the left) starting with an alphabet character.

    Args:
        v (str): the candidate

    Raises:
        ValueError: if v is not LeftRightDot format
    """
    try:
        x = v.split(".")
    except Exception as e:
        raise ValueError(f"Failed to seperate <{v}> into words with split'.'") from e
    first_word = x[0]
    first_char = first_word[0]
    if not first_char.isalpha():
        raise ValueError(
            f"Most significant word of <{v}> must start with alphabet char."
        )
    for word in x:
        if not word.isalnum():
            raise ValueError(f"words of <{v}> split by by '.' must be alphanumeric.")
    if not v.islower():
        raise ValueError(f"All characters of <{v}> must be lowercase.")


def check_is_log_style_date_with_millis(v: str) -> None:
    """Checks LogStyleDateWithMillis format

    LogStyleDateWithMillis format:  YYYY-MM-DDTHH:mm:ss.SSS

    Args:
        v (str): the candidate

    Raises:
        ValueError: if v is not LogStyleDateWithMillis format.
        In particular the milliseconds must have exactly 3 digits.
    """
    correct_millisecond_part_length = 3
    try:
        datetime.fromisoformat(v)
    except ValueError as e:
        raise ValueError(f"{v} is not in LogStyleDateWithMillis format") from e
    # The python fromisoformat allows for either 3 digits (milli) or 6 (micro)
    # after the final period. Make sure its 3
    milliseconds_part = v.split(".")[1]
    if len(milliseconds_part) != correct_millisecond_part_length:
        raise ValueError(
            f"{v} is not in LogStyleDateWithMillis format."
            " Milliseconds must have exactly 3 digits"
        )


def check_is_near5(v: str) -> None:
    """
    4.5 <= v <= 5.5
    """
    min_pi_voltage = 4.5
    max_pi_voltage = 5.5
    if v < min_pi_voltage or v > max_pi_voltage:
        raise ValueError(f"<{v}> is not between 4.5 and 5.5, not Near5")


def check_is_positive_integer(v: int) -> None:
    """
    Must be positive when interpreted as an integer. Interpretation as an
    integer follows the pydantic rules for this - which will round down
    rational numbers. So 1.7 will be interpreted as 1 and is also fine,
    while 0.5 is interpreted as 0 and will raise an exception.

    Args:
        v (int): the candidate

    Raises:
        ValueError: if v < 1
    """
    v2 = int(v)
    if v2 < 1:
        raise ValueError(f"<{v}> is not PositiveInteger")


def check_is_reasonable_unix_time_ms(v: int) -> None:
    """Checks ReasonableUnixTimeMs format

    ReasonableUnixTimeMs format: unix milliseconds between Jan 1 2000 and Jan 1 3000

    Args:
        v (int): the candidate

    Raises:
        ValueError: if v is not ReasonableUnixTimeMs format
    """

    start_date = datetime(2000, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(3000, 1, 1, tzinfo=timezone.utc)

    start_timestamp_ms = int(start_date.timestamp() * 1000)
    end_timestamp_ms = int(end_date.timestamp() * 1000)

    if v < start_timestamp_ms:
        raise ValueError(f"{v} must be after Jan 1 2000")
    if v > end_timestamp_ms:
        raise ValueError(f"{v} must be before Jan 1 3000")


def check_is_reasonable_unix_time_s(v: int) -> None:
    """Checks ReasonableUnixTimeS format

    ReasonableUnixTimeS format: unix seconds between Jan 1 2000 and Jan 1 3000

    Args:
        v (int): the candidate

    Raises:
        ValueError: if v is not ReasonableUnixTimeS format
    """
    start_date = datetime(2000, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(3000, 1, 1, tzinfo=timezone.utc)

    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())

    if v < start_timestamp:
        raise ValueError(f"{v} must be after Jan 1 2000")
    if v > end_timestamp:
        raise ValueError(f"{v} must be before Jan 1 3000")


def check_is_spaceheat_name(v: str) -> None:
    """Check SpaceheatName Format.

    Validates if the provided string adheres to the SpaceheatName format:
    Lowercase alphanumeric words separated by hypens

    Args:
        candidate (str): The string to be validated.

    Raises:
        ValueError: If the provided string is not in SpaceheatName format.
    """
    try:
        x = v.split("-")
    except Exception as e:
        raise ValueError(f"Failed to seperate <{v}> into words with split'-'") from e
    first_word = x[0]
    first_char = first_word[0]
    if not first_char.isalpha():
        raise ValueError(
            f"Most significant word of <{v}> must start with alphabet char."
        )
    for word in x:
        if not word.isalnum():
            raise ValueError(f"words of <{v}> split by by '-' must be alphanumeric.")
    if not v.islower():
        raise ValueError(f"All characters of <{v}> must be lowercase.")


def check_is_world_instance_name_format(v: str) -> None:
    """Checks WorldInstanceName Format

    WorldInstanceName format: A single alphanumerical word starting
    with an alphabet char (the root GNodeAlias) and an integer,
    seperated by '__'. For example 'd1__1'

    Args:
        v (str): the candidate

    Raises:
        ValueError: if v is not WorldInstanceNameFormat format
    """
    try:
        words = v.split("__")
    except Exception as e:
        raise ValueError(f"<{v}> is not split by '__'") from e
    if len(words) != 2:
        raise ValueError(f"<{v}> not 2 words separated by '__'")
    try:
        int(words[1])
    except Exception as e:
        raise ValueError(f"<{v}> second word not an int") from e

    root_g_node_alias = words[0]
    first_char = root_g_node_alias[0]
    if not first_char.isalpha():
        raise ValueError(f"<{v}> first word must be alph char")
    if not root_g_node_alias.isalnum():
        raise ValueError(f"<{v}> first word must be alphanumeric")


def str_is_left_right_dot(v: str) -> str:
    """Checks LeftRightDot Format

    LeftRightDot format: Lowercase alphanumeric words separated by periods, with
    the most significant word (on the left) starting with an alphabet character.

    Args:
        v (str): the candidate

    Raises:
        ValueError: if v is not LeftRightDot format
    """
    try:
        x = v.split(".")
    except Exception as e:
        raise ValueError(
            f"<{v}>: Fails LeftRightDot format! Failed to seperate into words with split'.'"
        ) from e
    first_word = x[0]
    first_char = first_word[0]
    if not first_char.isalpha():
        raise ValueError(
            f"<{v}>: Fails LeftRightDot format! Most significant word of  must start with alphabet char."
        )
    for word in x:
        if not word.isalnum():
            raise ValueError(
                f"<{v}>: Fails LeftRightDot format! words split by by '.' must be alphanumeric."
            )
    if not v.islower():
        raise ValueError(
            f"<{v}>: Fails LeftRightDot format! All characters must be lowercase."
        )
    return v


def str_is_spaceheat_name(v: str) -> str:
    try:
        x = v.split("-")
    except Exception as e:
        raise ValueError(
            f"<{v}>: Fails SpaceheatName format! Failed to seperate into words with split'-'"
        ) from e
    first_word = x[0]
    first_char = first_word[0]
    if not first_char.isalpha():
        raise ValueError(
            f"<{v}>: Fails SpaceheatName format! Most significant word  must start with alphabet char."
        )
    for word in x:
        if not word.isalnum():
            raise ValueError(
                f"<{v}>: Fails SpaceheatName format! words of split by by '-' must be alphanumeric."
            )
    if not v.islower():
        raise ValueError(
            f"<{v}>: Fails SpaceheatName format! All characters of  must be lowercase."
        )
    return v


def str_is_uuid_canonical_textual(v: str) -> str:
    """
    UuidCanonicalTextual format:  A string of hex words separated by hyphens
    of length 8-4-4-4-12.
    """
    v = str(v)
    try:
        u = uuid.UUID(v)
    except Exception as e:
        raise ValueError(f"Invalid UUID4: {v}  <{e}>") from e
    if u.version != 4:
        raise ValueError(
            f"{v} is valid uid, but of version {u.version}. Fails UuidCanonicalTextual"
        )
    return str(u)


UUID4Str = Annotated[str, BeforeValidator(str_is_uuid_canonical_textual)]

SpaceheatNameStr = Annotated[str, BeforeValidator(str_is_spaceheat_name)]
