import os

import cv2
import numpy as np

from designer import Designer
from utils import check_folder_path, order_filename_by_prefix

class Controller:

    def __init__(self, config):
        # extract first the parameters to create the designers
        # input
        self.input_size = (config["input"]["W"], config["input"]["H"])
        diagonal = sum([x ** 2 for x in self.input_size]) ** 0.5
        self.thickness = int(config["input"]["thickness"] * diagonal) + 1
        # output
        self.output_size = (config["output"]["W"], config["output"]["H"])
        # line
        thicknesses = self.to_list(config["line"]["thickness"])
        self.range_value = self.to_list(config["line"]["range_value"])
        self.fading = config["line"]["fading"]
        # interpolation
        interpolations = self.to_list(config["interpolation"]["method"])
        interpolations = [x.upper() for x in interpolations]
        # create the designers
        self.designers = self.get_designers(config, thicknesses, interpolations)

        # then extract the other parameters
        # process
        self.volume = config["process"]["volume"]
        self.selection = config["process"]["selection"].upper()
        self.display_output = config["process"]["display_output"]
        # storage
        self.root = config["storage"]["root"]
        check_folder_path(self.root)
        self.by_class_name = config["storage"]["by_class_name"]

        # then extract the classes and get the number of sample already made
        self.classes = config["classes"]
        self.classes_vol = {
            c:self.get_done_number(c) for c in self.classes
        }

        # to finish, set the dynamic part
        self.last_pos = None   # to draw lines between last and current mouse position
        self.left_button_down = False  # to draw only when the mouse is pressed
        # intialize the OpenCV windows with the ouput one if asked
        cv2.namedWindow('Writing Frame', cv2.WINDOW_NORMAL)
        cv2.setMouseCallback('Writing Frame', self.mouse_event) # catch mouse events
        if self.display_output:
            cv2.namedWindow('Output', cv2.WINDOW_NORMAL)

        self.img, self.current_class = self.set_new_image(init=True)

    def get_designers(self, config, thicknesses, interpolations):
        designers = []
        # create a thickness/interpolation matrix of designers
        for thickness in thicknesses:
            designers.append([])
            # change the range value according to the first thickness basis
            ratio = (thickness / thicknesses[0]) ** 0.5
            range_value = np.array(self.range_value) / ratio
            for interpolation in interpolations:
                designers[-1].append(Designer(
                    input_size=self.input_size,
                    output_size=self.output_size,
                    thickness=thickness,
                    range_value=range_value,
                    fading=self.fading,
                    interpolation=interpolation
                ))
        return np.array(designers)

    def mouse_event(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:  # activate draw
            self.left_button_down = True
            self.draw(x, y)
        elif event == cv2.EVENT_MOUSEMOVE and self.left_button_down:  # draw
            self.draw(x, y)
        elif event == cv2.EVENT_LBUTTONUP:  # deactivate draw
            self.last_pos = None
            self.left_button_down = False

    def not_finished(self):
        # not finished until all the classes are filled with de volume parameter
        n_uncompleted = sum([self.classes_vol[c] < self.volume for c in self.classes])
        return n_uncompleted

    def to_list(self, x):
        # convert to list if it is not yet
        x = x if isinstance(x, list) else [x]
        return x

    def get_done_number(self, class_name):
        # get the class folder path
        folder_path = self.root
        if self.by_class_name:
            folder_path = os.path.join(folder_path, class_name)
        # avoid missing folder
        check_folder_path(folder_path)
        # compute the prefix of all the images in this class
        prefix = os.path.join(folder_path, class_name + "_")
        # reorder the file names for this class in the folder
        n_done = order_filename_by_prefix(prefix)
        return n_done

    def set_new_image(self, init=False):
        new_current = 0
        shape = list(self.input_size)[::-1]
        # take the first one if it is the initialization
        if init:
            new_current = self.classes[0]
        # get a random next current class to draw
        elif self.selection == 'RANDOM':
            new_current = np.random.choice(self.classes)
        # continue drawing the current class until the volume is not reached
        elif self.selection == 'CLASSBYCLASS':
            class_done = self.classes_vol[self.current_class] >= self.volume
            idx = self.classes.index(self.current_class)
            idx = (idx + class_done) % len(self.classes)
            new_current = self.classes[idx]
        # get the next class to draw to rotate over the classes
        else: # default self.selection == 'ROTATE':
            idx = self.classes.index(self.current_class)
            idx = (idx + 1) % len(self.classes)
            new_current = self.classes[idx]

        # init the designers
        for designer in self.designers.flatten():
            designer.new_image()

        # if the choosen class to draw is already filled then repeat the process
        # (can happen with ROTATE and RANDOM selection method)
        if self.classes_vol[new_current] >= self.volume and self.not_finished():
            return self.set_new_image(init)

        # print the current state of the class to draw when it is choosen
        state = f'Current Class : {new_current} - '
        state += f'({self.classes_vol[new_current]}/{self.volume})'
        print(state)
        return np.zeros(shape), new_current

    def save(self, zfill=5):
        for designer in self.designers.flatten():
            out_img = designer.get_output()
            folder_path = self.root
            if self.by_class_name:
                folder_path = os.path.join(folder_path, self.current_class)

            str_number = str(self.classes_vol[self.current_class]).zfill(zfill)
            file_name = f'{self.current_class}_{str_number}.png'
            rgb_img = np.tile(out_img[:, :, None], [1, 1, 3])
            cv2.imwrite(os.path.join(folder_path, file_name), rgb_img)
            self.classes_vol[self.current_class] += 1

    def draw(self, x, y):
        # avoid last pos non existing
        if self.last_pos is None:
            self.last_pos = (x, y)
        # draw a line between the last mouse position and its current
        self.img = cv2.line(self.img, self.last_pos, (x, y), 255, self.thickness)
        # same process for the designers images
        for designer in self.designers.flatten():
            designer.draw(self.last_pos, (x, y))
        self.last_pos = (x, y)  # update the last pos

    def get_drawing_frame(self):
        # write the current state of the class to draw
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = f'Current Class : {self.current_class} - '
        text += f'({self.classes_vol[self.current_class]}/{self.volume})'
        # top center position for the text
        size = self.input_size[0] / 512
        textsize = cv2.getTextSize(text, font, size, 1)[0]
        x = int((self.input_size[0] - textsize[0]) / 2)
        y = textsize[1] * 2
        return cv2.putText(self.img, text, (x, y), font, size, 255, 1)

    def get_output_frame(self):
        # stacks the outputs images of the designer's matrix
        # horizontal for the thickness
        # vertical for the interpolation method
        imgs = [[y.get_output() for y in x] for x in self.designers]
        imgs = [np.hstack([*x]) for x in imgs]
        imgs = np.vstack([*imgs])
        # border only because I like it (can be removed :D )
        imgs = cv2.copyMakeBorder(imgs, 2, 2, 2, 2, cv2.BORDER_CONSTANT,value=255)
        return imgs

    def run(self):
        # draw classes until the volume is not reached
        while self.not_finished():
            # display the frames of the drawing part and ouput part if asked
            cv2.imshow('Writing Frame', self.get_drawing_frame())
            if self.display_output:
                cv2.imshow('Output', self.get_output_frame())

            key = cv2.waitKey(1000//30) & 0xff # 30 fps and catch key pressed
            if key == ord('q') or key == 27: # Q key of Esc to quit the program
                break
            elif key == 13:  # Enter key to save the draw and begin the next one
                self.save()
                self.img, self.current_class = self.set_new_image()
            elif key == ord('u'):  # U key to undo the draw
                self.img = self.img * 0
                for designer in self.designers.flatten():
                    designer.new_image()

        # Prevent if the program is closed because the volume is reached
        if not self.not_finished():
            print('Dataset Done !')
        cv2.destroyAllWindows()  # preferable
