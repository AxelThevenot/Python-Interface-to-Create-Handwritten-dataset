import cv2
import numpy as np

class Designer:

    available_interpolation = [
     'INTER_NEAREST',
     'INTER_LINEAR',
     'INTER_AREA',
     'INTER_CUBIC',
     'INTER_LANCZOS4'
    ]

    def __init__(self, input_size,
                       output_size,
                       thickness,
                       range_value,
                       fading,
                       interpolation):
        self.input_size = input_size
        self.output_size = output_size
        # compute the thickness according to the diagonal
        diagonal = sum([x ** 2 for x in input_size]) ** 0.5
        self.thickness = int(thickness * diagonal)
        self.range_value = range_value
        self.fading = fading

        # catch random interpolation
        self.interpolation_method = interpolation
        if self.interpolation_method == 'RANDOM':
            interpolation = np.random.choice(Designer.available_interpolation)
        self.interpolation = eval(f'cv2.{interpolation}')

        # to store the current state
        self.img = None
        self.out_img = None

    def new_image(self):
        # create new input and output image with zeros
        input_shape = list(self.input_size)[::-1]
        output_shape = list(self.output_size)[::-1]
        self.img = np.zeros(input_shape)
        self.out_img = np.zeros(output_shape)

        # catch random interpolation
        if self.interpolation_method == 'RANDOM':
            interpolation = np.random.choice(Designer.available_interpolation)
            self.interpolation = eval(f'cv2.{interpolation}')

    def draw(self, pt_1, pt_2):
        value = np.random.randint(*self.range_value) # random pixel value
        line_img = self.img * 0 # create an image to draw the new linea
        # fade line
        if self.fading != 1:
            # superimposed sub-thickness-lines beginnig by the thicker one
            for t in range(self.thickness, 0, -1):
                # compute the linear fade ratio
                fade = (self.thickness - t - 1) / self.thickness
                fade = self.fading + fade * (1 - self.fading)
                fade_value = int(value * fade)
                # draw the sub thickness line
                line_img = cv2.line(line_img, pt_1, pt_2, fade_value, t)

        # update the current imgs
        self.img = self.img + (255 - self.img) / 255 * line_img
        self.out_img = cv2.resize(self.img, self.output_size, self.interpolation).astype(np.uint8)

    def get_output(self):
        return self.out_img
