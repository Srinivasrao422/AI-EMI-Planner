import pandas as pd


def repayment_schedule_to_dataframe(schedule):
    """
    Convert repayment schedule list into Pandas DataFrame.
    """

    dataframe = pd.DataFrame(schedule)

    return dataframe