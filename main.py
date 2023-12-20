# python3 main.py pipeline_config.cfg 
import sys
import configparser
import subprocess
import time 



def get_config_dict(filename):
    try:
            dico = {}
            config = configparser.ConfigParser()
            config.read(filename)
            dico['dataset_path'] = config['DEFAULT']['dataset_path']
            dico['output_path'] = config['DEFAULT']['output_path']
            dico['filename'] = config['DEFAULT']['file_name']
            dico['file_name_rgb_in'] = dico['dataset_path'] + config['DEFAULT']['file_name']
            dico['framerate'] = config['DEFAULT']['framerate']
            dico['frames_to_convert'] = config['DEFAULT']['frames_to_convert']
            dico['width'] = config['DEFAULT']['width']
            dico['height'] = config['DEFAULT']['height']
            dico['filename_yuv'] = dico['output_path'] + config['DEFAULT']['file_name']  + ".yuv" #config['DEFAULT']['filename_yuv']
            dico['filename_rgb_out'] = dico['output_path'] + "rgb_out_" + config['DEFAULT']['file_name']
            # dico['pix_fmt'] = config['DEFAULT']['pix_fmt']
            dico['vtm_path'] = config['APP_PATHS']['vtm_path']
            dico['vtm_config_file'] = config['VTM']['vtm_config_file']
            dico['pre_processing_path'] = config['APP_PATHS']['pre_processing_path']
            dico['RLC_path'] = config['APP_PATHS']['RLC_path']
            dico['RLC_config_file'] = config['RLC']['RLC_config_file']
            dico['camera_calibration_file'] = config['RLC']['camera_calibration_file']
            dico['generate_rlc_cfg'] = config['RLC']['generate_rlc_cfg']
            dico['rlc_cfg_template'] = config['RLC']['rlc_cfg_template']

            return dico
    except FileNotFoundError:
        print(f"File '{filename}' not found.")
    except:
        print("An error occurred while opening the file.")

def generate_RLC_config(template_file, output_file):
    with open(template_file, 'r') as file:
        filedata = file.read()

    filedata = filedata.replace('_CALIBRATIONFILE', config_dico['camera_calibration_file'])
    filedata = filedata.replace('_INPUTPATH', config_dico['filename_rgb_out'])
    filedata = filedata.replace('_OUTPUTPATH', config_dico['output_path']+"RLC_result")
    filedata = filedata.replace('_WIDTH', config_dico['width'])
    filedata = filedata.replace('_HEIGHT', config_dico['height'])
    # TODO faire start frame et end frame

    with open(output_file, 'w') as file:   
        file.write(filedata)


if __name__ == '__main__':
    start_time = time.time()
    if len(sys.argv) != 2:
        print("Usage: python Main.py <pipeline_config_file>")
        exit(1)

    filename = sys.argv[1]
    config_dico = get_config_dict(filename)

    # __________ Pre processing __________
    pre_process_command = f"python3 {config_dico['pre_processing_path']}"
    print(pre_process_command)
    
    # ______________ FFmpeg1 ______________
    ffmpeg_command = f"ffmpeg -i {config_dico['file_name_rgb_in']} -r {config_dico['framerate']} -vframes {config_dico['frames_to_convert']} -s {config_dico['width']}x{config_dico['height']} -pix_fmt yuv420p {config_dico['filename_yuv']}"
    print(ffmpeg_command)

    # ______________ VTM ______________
    # WATCHOUT vtm only takes yuv420p and outputs only yuv420p10le
    vtm_command = f"{config_dico['vtm_path']}EncoderApp -i {config_dico['filename_yuv']} -wdt {config_dico['width']} -hgt {config_dico['height']} -c {config_dico['vtm_config_file']} -f {config_dico['frames_to_convert']} -fr {config_dico['framerate']} -o {config_dico['output_path']}vtm_out.yuv"
    print(vtm_command)

    # ______________ FFmpeg2 ______________
    ffmpeg_command2 = f"ffmpeg -s {config_dico['width']}x{config_dico['height']} -pix_fmt yuv420p10le -i {config_dico['output_path']}vtm_out.yuv -vframes {config_dico['frames_to_convert']} {config_dico['filename_rgb_out']}"
    print(ffmpeg_command2)

    # ______________ RLC ______________
    # RLC_command = f"{config_dico['RLC_path']} {config_dico['RLC_config_file']}"

    if (config_dico['generate_rlc_cfg'] == 'true') :
        RLC_config = f"{config_dico['dataset_path']}RLC_config.cfg"
        generate_RLC_config(config_dico['rlc_cfg_template'], RLC_config)

    else : RLC_config = config_dico['RLC_config_file']

    RLC_command = f"{config_dico['RLC_path']} {RLC_config}"
    print(RLC_command)

    # ______________ Execution ______________
    subprocess.run(pre_process_command, shell=True)
    subprocess.run(ffmpeg_command, shell=True)
    subprocess.run(vtm_command, shell=True)
    subprocess.run(ffmpeg_command2, shell=True)
    subprocess.run(RLC_command, shell=True)
    
    end_time = time.time()
    print(f"Execution time: {end_time - start_time} seconds")
