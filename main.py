import numpy as np
import hjson
import argparse
from pydub import AudioSegment
from scipy.fft import fft
from audio_renderer import get_renderer
from moviepy.editor import VideoClip, AudioFileClip

def make_frame(t, frames, fps):
    # Calculate the appropriate frame index
    frame_index = int(t * fps)
    if frame_index >= len(frames):
        frame_index = len(frames) - 1


    return frames[...,frame_index]

def save_video_with_audio(frames, audio_path, fps, output_path):
    # Create an AudioArrayClip from the PCM audio data
    audio_clip = AudioFileClip(audio_path)

    # Get the duration from the audio clip
    duration = audio_clip.duration

    # Create a VideoClip from the frames
    video_clip = VideoClip(lambda t:  make_frame(t, frames, fps), duration=duration)
    video_clip = video_clip.set_fps(fps)

    # Set the audio of the video clip
    video_clip = video_clip.set_audio(audio_clip)

    # Write the final video file
    video_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')


with open("config.json") as h:
    config = hjson.load(h)


parser = argparse.ArgumentParser(description='Makes cool animations from audio')

# Add the positional arguments
parser.add_argument('audio_file', type=str, help='The input AUDIO file path')
parser.add_argument('output_video', type=str, help='The output VIDEO file path (.mp4)')

# Parse the arguments
args = parser.parse_args()


audio_path = args.audio_file

audio = AudioSegment.from_file(audio_path)


if audio.channels == 1:
    channels = [audio]
else:
    channels = audio.split_to_mono()



single = np.sum([c.get_array_of_samples() for c in channels],axis=0)


frame_size = int(audio.frame_rate/config['fps'])

pad_size = frame_size - (len(single) % frame_size)

single = np.concatenate([single,np.full((pad_size,),single[-1])])

ffts = [ np.abs(fft(single[i*frame_size:(i+1)*frame_size])) for i in range(int(np.ceil(len(single)/frame_size))) ]
bins = [None] * len(ffts)
for i in range(len(ffts)):
    f = ffts[i]
    f = f[0:int(len(f)/2)]

    if config['log']:
        f = np.log(f)

    l = int(len(f)/config['bins'])

    bins[i] = [ np.max(f[j*l:(j+1)*l]) for j in range(config['bins']) ]


if (not config['band_norm'] ):
    m = max([np.max(b) for b in bins])

    bins = [b/m for b in bins]
else:


    matrix = np.stack( [np.asarray(b) for b in bins],axis=1)

    min_value = np.expand_dims(np.min(matrix,1),axis=1)
    max_value = np.expand_dims(np.max(matrix, 1),axis=1)

    matrix = (matrix - min_value) / (max_value-min_value)

    bins = [matrix[:,i] for i in range(matrix.shape[1])]



if ((smooth:=config['smooth']) > 1):
    smoothed_bins = [None] * len(bins)

    for i in range(len(bins)):
        window = bins[i:i+smooth]
        smoothed_bins[i] = np.mean(window,axis=0)

    bins = smoothed_bins



renderer = get_renderer(config['renderer']['name'])(width=config['width'],height=config['max_height'],margin=config['margin'])
frames = renderer(bins,**config['renderer']['args'])

save_video_with_audio(frames,audio_path,fps=config['fps'],output_path=args.output_video)



