import pandas as pd
from pandas.tseries.offsets import CustomBusinessDay
from pandas.tseries.holiday import USFederalHolidayCalendar

def adjust_to_business_time(df, frequency='daily'):
    """
    Adjusts the DataFrame to the specified business time frequency: 'daily', 'hourly', or 'minute'.
    
    Parameters:
    - df: DataFrame to be adjusted.
    - frequency: The target frequency ('daily', 'hourly', or 'minute').
    
    Returns:
    - Adjusted DataFrame.
    """
    # Define the business day calendar
    us_business_day = CustomBusinessDay(calendar=USFederalHolidayCalendar())
    
    # Determine the start and end dates from the DataFrame
    start_date = df.index.min()
    end_date = df.index.max()
    
    # Generate the appropriate date range based on the specified frequency
    if frequency == 'daily':
        # Daily frequency, only business days
        target_range = pd.date_range(start_date, end_date, freq=us_business_day)
    elif frequency == 'hourly':
        # Generate hourly timestamps within business days
        business_days = pd.date_range(start_date, end_date, freq=us_business_day)
        target_range = pd.date_range(start_date, end_date, freq='H')
        target_range = target_range[target_range.date.isin(business_days.date)]
    elif frequency == 'minute':
        # Generate minute timestamps within business days, assuming 9:00 AM to 5:00 PM as business hours
        business_days = pd.date_range(start_date, end_date, freq=us_business_day)
        target_range = pd.date_range(start_date, end_date, freq='T')  # 1-minute frequency
        # Filter for business hours; adjust 'hour >= 9 & hour < 17' as needed for specific business hours
        target_range = target_range[(target_range.date.isin(business_days.date)) & (target_range.hour >= 9) & (target_range.hour < 17)]
    else:
        raise ValueError("Unsupported frequency specified. Choose 'daily', 'hourly', or 'minute'.")
    
    # Reindex the DataFrame to match the target range, forward-filling missing values
    adjusted_df = df.reindex(target_range).ffill()
    
    return adjusted_df
