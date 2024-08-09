import pendulum


def str_from_ms(epoch_milli_seconds: int) -> str:
    return (
        pendulum.from_timestamp(epoch_milli_seconds / 1000)
        .in_timezone("America/New_York")
        .format("YYYY-MM-DD HH:mm:ss.SSS")
        + " America/NY"
    )
