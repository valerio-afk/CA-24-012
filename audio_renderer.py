from abc import ABC, abstractmethod
from PIL import Image, ImageDraw
import numpy as np


def get_renderer(name):

    match (name):
        case "rectangle":
            return RectangleAudioRenderer
        case "led":
            return LEDAudioRenderer
        case "circle":
            return CircleAudioRenderer

class AudioRenderer(ABC):

    def __init__(this,width,height,margin):
        this.width = width
        this.height = height
        this.margin = margin

    def bin_width(this, n_bins):
        return int((this.width - ((n_bins + 1) * this.margin)) / n_bins)

    def get_bin_x(this,idx,n_bins):

        return (this.bin_width(n_bins)+this.margin) * idx + this.margin


    @abstractmethod
    def __call__(this, bins,**kwargs):
        ...


class RectangleAudioRenderer(AudioRenderer):

    def __call__(this, bins,**kwargs):
        rounded = kwargs.setdefault("rounded",0 )
        centred = kwargs.setdefault("centred", False)
        colour = kwargs.setdefault("colour", [255, 255, 255])

        n_frames = len(bins)

        frames = np.zeros((this.height,this.width,3,n_frames), dtype=np.dtype('B'))


        for i in range(n_frames):
            im = Image.new('RGB',(this.width,this.height))

            draw = ImageDraw.Draw(im)

            n_bins = len(bins[i])
            bar_width = this.bin_width(n_bins)

            for j in range(n_bins):
                x = this.get_bin_x(j,n_bins)
                height = int(this.height) * bins[i][j]

                if (centred):
                    y = int ((this.height - height)/2)
                    y = 0 if y<0 else y
                else:
                    y = 0


                coords = ((x,y),(x+bar_width,height+y))

                draw.rounded_rectangle(xy=coords,radius=rounded,fill=tuple(colour))

            frames[:,:,:,i] = np.asarray(im)[::-1,:,:]

        return frames

class LEDAudioRenderer(AudioRenderer):

    def __call__(this, bins,**kwargs):
        leds = kwargs.setdefault("leds",10)
        leds_spacing = kwargs.setdefault("leds_spacing", 10)
        colour1 = kwargs.setdefault("colour1", [255, 255, 255])
        colour2 = kwargs.setdefault("colour2", [255, 255, 255])
        colour3 = kwargs.setdefault("colour3", [255, 255, 255])

        n_frames = len(bins)

        frames = np.zeros((this.height,this.width,3,n_frames), dtype=np.dtype('B'))

        p1 = 0.5
        p2 = 0.9


        #for each frame i
        for i in range(n_frames):
            im = Image.new('RGB',(this.width,this.height))

            draw = ImageDraw.Draw(im)

            n_bins = len(bins[i])
            bar_width = this.bin_width(n_bins)


            #for each bin
            for j in range(n_bins):
                n_leds = int(np.round(bins[i][j]*leds))
                x = this.get_bin_x(j,n_bins)

                #for each led
                for k in range(n_leds):
                    p = (k+1) / leds

                    if p<=p1:
                        colour = colour1
                    elif (p1<p<p2):
                        colour = colour2
                    else:
                        colour = colour3

                    led_height = (this.height - (leds_spacing * (leds-1)))/leds

                    y = k*(led_height+leds_spacing)

                    coord1 = (x,y)
                    coord2 = (x+bar_width,y+led_height)

                    draw.rectangle([coord1,coord2],fill=tuple(colour))



            frames[:,:,:,i] = np.asarray(im)[::-1,:,:]

        return frames

class CircleAudioRenderer(AudioRenderer):

    def __call__(this, bins,**kwargs):

        min_size = min(this.width,this.height)

        centre = (this.width,this.height)
        centre = tuple([int(c/2) for c in centre])

        radius = kwargs.setdefault("radius", int(min_size/10) )
        colour = kwargs.setdefault("colour", [255, 255, 255])
        line_width = kwargs.setdefault("line_width", 3)
        phase = kwargs.setdefault("phase", 0)

        phase = np.deg2rad(phase)

        n_frames = len(bins)

        frames = np.zeros((this.height,this.width,3,n_frames), dtype=np.dtype('B'))


        for i in range(n_frames):
            im = Image.new('RGB',(this.width,this.height))

            draw = ImageDraw.Draw(im)

            n_bins = len(bins[i])

            angle = 2*np.pi / n_bins

            for j in range(n_bins):
                height = int(min_size/2 - radius) * bins[i][j]

                theta = (angle*j) + phase

                coords= [(int(radius*np.cos(theta)), int(radius*np.sin(theta))),
                         (int((height+radius)*np.cos(theta)), int((height+radius)*np.sin(theta)))]

                coords = [(x+centre[0],y+centre[1]) for (x,y) in coords]


                draw.line(xy=coords,width=line_width,fill=tuple(colour))

            frames[:,:,:,i] = np.asarray(im)

        return frames
