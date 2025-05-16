import re
from datetime import datetime

def parse_log_line(log_line):
    """
    Parses a single line from the log file, adding a timestamp if one doesn't exist.

    Args:
        log_line (str): A single line from the log file.

    Returns:
        dict: A dictionary containing the parsed information, or None on error.
              Keys may include 'timestamp', 'level', 'message', 'test_name',
              'result', 'duration', etc., depending on the log line.
              Returns None if the line doesn't match any expected format.
    """

    timestamp_regex = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
    timestamp_match = re.search(timestamp_regex, log_line)
    if timestamp_match:
        timestamp = timestamp_match.group(0)
        # Remove the timestamp and any following spaces for consistent parsing
        log_line = log_line[len(timestamp):].lstrip()
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Adjusted regex patterns to handle various log formats *after* timestamp removal
    regex_patterns = [
        (r"=(?P<test_summary>.*)=$", "summary"),
        (r"^(?P<level>\w+) (?P<message>.*)$", "standard_no_timestamp"),
        (r"^(?P<result>PASS|FAIL|SKIP|ERROR)\s+(?P<test_name>[^ ]+)$", "test_result"),
        (r"^(?P<duration_message>.*in\s+(?P<duration>\d+\.\d+).*)", "duration"),
        (r"^(\s)?WARNING\s+(?P<warning_message>.*)$", "warning"),
        (r"^_+$", "stack_trace_start"),
        (r"^(?P<stack_trace_line>.*\/.*\.py:\d+.*)$", "stack_trace_line"),
        (r"^(-{10,}\s+live log\s+session\w+\s+-{10,})$", "live_log_session"),
        (r"^(?P<message>.*)$", "catch_all"),  # Catch-all
    ]

    parsed_data = {'timestamp': timestamp}  # Initialize with timestamp

    for regex, log_type in regex_patterns:
        match = re.search(regex, log_line)
        if match:
            if log_type == "standard_no_timestamp":
                parsed_data.update({
                    'level': match.group('level').strip(),
                    'message': match.group('message').strip(),
                })
            elif log_type == "test_result":
                parsed_data.update({
                    'result': match.group('result').strip(),
                    'test_name': match.group('test_name').strip(),
                })
            elif log_type == "summary":
                parsed_data.update({
                    'test_summary':  match.group('test_summary').strip()
                })
            elif log_type == "duration":
                parsed_data.update({
                    'duration_message': match.group('duration_message').strip(),
                    'duration': match.group('duration').strip()
                })
            elif log_type == "warning":
                parsed_data.update({
                    'warning_message': match.group('warning_message').strip()
                })
            elif log_type == "stack_trace_start":
                parsed_data['stack_trace_start'] = True
            elif log_type == "stack_trace_line":
                parsed_data['stack_trace_line'] = match.group('stack_trace_line').strip()
            elif log_type == "live_log_session":
                parsed_data['live_log_session'] = log_line.strip()
            elif log_type == "catch_all":
                parsed_data['message'] = log_line.strip()
            return parsed_data
    return {'timestamp': timestamp, 'message': log_line.strip()}  # If no pattern matches, return timestamp and original line

def read_log_file(file_path):
    """
    Reads the log file and parses each line.

    Args:
        file_path (str): The path to the log file.

    Returns:
        list: A list of dictionaries, where each dictionary represents a parsed
              log entry.  Returns an empty list if the file is empty or an error occurs.
    """
    parsed_logs = []
    try:
        with open(file_path, 'r') as f:
            current_stack_trace = []
            for line in f:
                parsed_line = parse_log_line(line.strip())
                if parsed_line:
                    if 'stack_trace_start' in parsed_line:
                        current_stack_trace = []
                    elif 'stack_trace_line' in parsed_line:
                        current_stack_trace.append(parsed_line['stack_trace_line'])
                    else:
                        if current_stack_trace:
                            parsed_line['stack_trace'] = current_stack_trace
                            current_stack_trace = []
                        parsed_logs.append(parsed_line)
                elif current_stack_trace:
                    #adds any leftover stack traces
                    parsed_logs.append({'stack_trace': current_stack_trace})
                    current_stack_trace = []

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return []
    except Exception as e:
        print(f"Error reading or parsing file: {e}")
        return []
    return parsed_logs

def organize_log_data(parsed_logs):
    """
    Organizes the parsed log data into a structured format suitable for a RAG model.

    Args:
        parsed_logs (list): A list of dictionaries representing parsed log entries.

    Returns:
        dict: A dictionary containing organized log data.
    """
    organized_data = {
        'test_results_summary': [],
        'failures': [],
        'errors': [],
        'warnings': [],
        'api_requests': [],
        'long_running_tests': [],
        'stack_traces': [],
        'deselected_tests': [],
        'log_entries': [],  # Changed from 'timestamps' to 'log_entries'
        'other_info': []
    }

    for log_entry in parsed_logs:
        if 'test_summary' in log_entry:
            organized_data['test_results_summary'].append(log_entry['test_summary'])
        elif 'result' in log_entry:
            if log_entry['result'] == 'FAIL':
                organized_data['failures'].append(log_entry['test_name'])
            elif log_entry['result'] == 'ERROR':
                organized_data['errors'].append(log_entry['test_name'])
        elif 'warning_message' in log_entry:
            organized_data['warnings'].append(log_entry['warning_message'])
        elif 'duration' in log_entry and float(log_entry['duration']) > 10:
            organized_data['long_running_tests'].append(log_entry['duration_message'])
        elif 'stack_trace' in log_entry:
            organized_data['stack_traces'].append(log_entry['stack_trace'])
        elif 'message' in log_entry and 'deselected' in log_entry['message']:
            organized_data['deselected_tests'].append(log_entry['message'])
        elif 'message' in log_entry and 'REST:' in log_entry['message']:
            organized_data['api_requests'].append(log_entry['message'])
        elif 'timestamp' in log_entry:  # Capture the whole log entry
            organized_data['log_entries'].append(log_entry)
        else:
            organized_data['other_info'].append(log_entry)

    return organized_data

def print_organized_data(organized_data):
    """
    Prints the organized log data in a user-friendly format.

    Args:
        organized_data (dict): A dictionary containing organized log data.
    """
    print("Organized Log Data:")
    print("-" * 40)

    if organized_data['test_results_summary']:
        print("\nTest Results Summary:")
        for summary in organized_data['test_results_summary']:
            print(summary)

    if organized_data['failures']:
        print("\nFailures:")
        for failure in organized_data['failures']:
            print(failure)

    if organized_data['errors']:
        print("\nErrors:")
        for error in organized_data['errors']:
            print(error)

    if organized_data['warnings']:
        print("\nWarnings:")
        for warning in organized_data['warnings']:
            print(warning)

    if organized_data['api_requests']:
        print("\nAPI Requests:")
        for request in organized_data['api_requests']:
            print(request)

    if organized_data['long_running_tests']:
        print("\nLong-Running Tests:")
        for test in organized_data['long_running_tests']:
            print(test)
    
    if organized_data['stack_traces']:
        print("\nStack Traces:")
        for trace in organized_data['stack_traces']:
            for line in trace:
                print(line)

    if organized_data['deselected_tests']:
        print("\nDeselected Tests")
        for test in organized_data['deselected_tests']:
            print(test)
    
    if organized_data['other_info']:
        print("\nOther Information:")
        for info in organized_data['other_info']:
            print(info)
    
    if organized_data['log_entries']:  # Print the full log entries
        print("\nLog Entries:")
        for entry in organized_data['log_entries']:
            print(entry)

if __name__ == "__main__":
    log_file_path = 'sample_log.txt'
    parsed_logs = read_log_file(log_file_path)
    organized_data = organize_log_data(parsed_logs)
    print_organized_data(organized_data)