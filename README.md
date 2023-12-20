# Pipeline for the processing of lenslet images

The pipeline consists of the following steps:

Pre-processing $\implies$ ffmpeg (rgb to yuv) $\implies$ VTM (EncoderApp) $\implies$ ffmpeg (yuv back to rgb) $\implies$ RLC 

## Configuration

The pipeline configuration file has all the information needed to process an image.
The RLC config file is generated based on the ```RLC_config_template.cfg``` file.
Some parameters will be modified when running the code according to the pipeline config file (they are marked with an underscore).
These are the parameters :

- Calibration_xml
- RawImage_Path
- Output_Path
- height
- width
- TODO start_frame, end_frame

To change the other parameters, directly change the values in the template file, as they will be used to generate the correct RLC config file.

## Tools used

### Pre-processing

Consists of a python script that takes as input a folder containing the lenslet images and outputs a folder containing the pre-processed images.
TODO

### ffmpeg

ffmpeg is used to convert the rgb images to yuv420p and back to rgb.

### VTM

EncoderApp is used to compress and decompress the image.
**Important to note** : VTM takes as input the yuv420p pixel format and outputs yuv420p10le. This is important to note when using ffmpeg.

### RLC
RLC takes a rbg lenslet image and outputs the multiview images.