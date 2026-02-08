#!/usr/bin/env python3
import subprocess
import time


def main():
    while True:
        try:
            subprocess.run(['python3', 'bot.py', '--no-posts'], check=True)
            time.sleep(10)
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
