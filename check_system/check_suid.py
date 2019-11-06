#!/usr/bin/env python3


from FileSystemCheck import FSCheck


def main():
    fs_check = FSCheck()

    with open("tmp", "w+") as file:
        fs_check.exec(file)


if __name__ == "__main__":
    main()
