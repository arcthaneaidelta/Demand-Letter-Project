from datetime import datetime


def format_date(date_str):
    """Format date from ISO format to Month Day, Year format"""
    if not date_str:
        return ''
    
    # List of possible date formats to try
    formats = [
        '%Y-%m-%d %H:%M:%S',  # 2025-04-19 00:00:00
        '%Y-%m-%d',           # 2025-04-19
        '%d/%m/%Y %H:%M',     # 19/09/2023 0:00
        '%d/%m/%Y',           # 19/09/2023
        '%m/%d/%Y %H:%M:%S',  # 04/19/2025 00:00:00
        '%m/%d/%Y %H:%M',     # 04/19/2025 00:00
        '%m/%d/%Y',           # 04/19/2025
        '%d-%m-%Y %H:%M:%S',  # 19-04-2025 00:00:00
        '%d-%m-%Y %H:%M',     # 19-04-2025 00:00
        '%d-%m-%Y',           # 19-04-2025
        '%Y/%m/%d %H:%M:%S',  # 2025/04/19 00:00:00
        '%Y/%m/%d',           # 2025/04/19
        '%d.%m.%Y %H:%M:%S',  # 19.04.2025 00:00:00
        '%d.%m.%Y',           # 19.04.2025
        '%b %d, %Y',          # Apr 19, 2025
        '%B %d, %Y',          # April 19, 2025
        '%d %b %Y',           # 19 Apr 2025
        '%d %B %Y'            # 19 April 2025
    ]
    
    for date_format in formats:
        try:
            # Try to parse with current format
            date_obj = datetime.strptime(date_str, date_format)
            # Format to Month Day, Year
            return date_obj.strftime('%B %d, %Y')
        except ValueError:
            continue
    
    # If no format matches, return the original
    return date_str


# Testing with different date formats
print("Standard ISO formats:")
print(format_date("2025-04-19 00:00:00"))  # ISO with time
print(format_date("2025-04-19"))           # ISO date only

print("\nDifferent separators:")
print(format_date("19/09/2023 0:00"))      # Day/Month with slash
print(format_date("19-09-2023"))           # Day/Month with hyphen
print(format_date("19.09.2023"))           # Day/Month with dots

print("\nDifferent ordering:")
print(format_date("04/19/2025"))           # Month/Day/Year (US format)
print(format_date("2025/04/19"))           # Year/Month/Day

print("\nText formats:")
print(format_date("Apr 19, 2025"))         # Short month name
print(format_date("April 19, 2025"))       # Full month name
print(format_date("19 Apr 2025"))          # Day short month
print(format_date("19 April 2025"))        # Day full month

print("\nInvalid formats should return original:")
print(format_date("Not a date"))           # Invalid input
print(format_date("2025.04"))              # Incomplete date

