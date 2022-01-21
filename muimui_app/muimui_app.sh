#!/bin/sh

export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
# 

while getopts ":v:" opt; do
  case $opt in
    a)
      echo "Invalid Argument: $OPTARG" >&2
      exit 1
      ;;
    \?)
      echo "Invalid option: -$OPTARG\nUsage: ./muimui_app.sh <-v>" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      echo "Runing in debug mode..."
      python main.py
      exit 1
      ;;
  esac
done

python main.py > /dev/null 2>&1 &