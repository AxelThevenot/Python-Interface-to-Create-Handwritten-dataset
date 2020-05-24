import json
import argparse

import cv2

from controller import Controller
from utils import get_json

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config",
                    default="config.json",
                    help="path to the config file")
args = parser.parse_args()

if __name__ == '__main__':
    config = get_json(args.config)
    controller = Controller(config)
    controller.run()
