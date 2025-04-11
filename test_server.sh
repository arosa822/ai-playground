#! /bin/bash
curl -X POST -F 'file=@logs/sample_pytest_log.txt' http://localhost:5000/upload
