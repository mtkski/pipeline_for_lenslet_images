import os
import sys
import argparse
from config_maker import get_config_dict 
import shutil

def post(config_dico, input_dir, output_dir):
    # Copy every file inside the input_dir to the output_dir
    for file_name in os.listdir(input_dir):
        file_path = os.path.join(input_dir, file_name)
        if os.path.isfile(file_path):
            shutil.copy(file_path, output_dir)
    return 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-cfg', help='Path to the config file')
    parser.add_argument('-o', help='Output dir')
    parser.add_argument('-i', help='Input dir')
    args = parser.parse_args()

    input_dir = args.i
    config_file = args.cfg
    output_dir = args.o

    print(f"Input dir: {input_dir}")
    print(f"Output dir: {output_dir}")

    config_dico = get_config_dict(config_file)
    # post(config_dico, input_dir, output_dir)
