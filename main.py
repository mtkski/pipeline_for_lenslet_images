# python3 main.py pipeline_config.cfg 
import sys
import subprocess
import time 
from config_maker import get_config_dict
import os

def create_output_dirs(config_dico):
    os.makedirs(config_dico['output_path'], exist_ok=True)
    os.makedirs(config_dico['no_preproc_line'], exist_ok=True)
    os.makedirs(config_dico['preproc_line'], exist_ok=True)
    os.makedirs(config_dico['ref_rlc_line'], exist_ok=True)


    os.makedirs(config_dico['RLC_ref_path'], exist_ok=True)
    os.makedirs(config_dico['RLC_no_preproc_path'], exist_ok=True)
    os.makedirs(config_dico['RLC_preproc_path'], exist_ok=True)

def generate_RLC_config(config_dico, rlc_config_name, input, output):
    try:
        with open(config_dico['rlc_cfg_template'], 'r') as file:
            filedata = file.read()
        filedata = filedata.replace('_CALIBRATIONFILE', config_dico['camera_calibration_file'])
        filedata = filedata.replace('_INPUTPATH', input)
        filedata = filedata.replace('_OUTPUTPATH', output)
        filedata = filedata.replace('_WIDTH', config_dico['width'])
        filedata = filedata.replace('_HEIGHT', config_dico['height'])
        filedata = filedata.replace('_ENDFRAME', config_dico['frames_to_convert'])

        with open(rlc_config_name, 'w') as file:   
            file.write(filedata)

    except FileNotFoundError:
        print(f"File '{config_dico['rlc_cfg_template']}' not found.")
    except:
        print("An error occurred while opening or writing to the file.")

def pre_processing_line(config_dico):
    # __________ Pre processing __________
    if config_dico['testReBlur'] :
        pre_process_output_name = f"{config_dico['preproc_line']}{config_dico['filename'].split('.')[0]}{config_dico['rad']}Ring{config_dico['ring']}Bord{config_dico['border']}Sig{int(config_dico['sigma'])}CutOff{config_dico['cut_off']}_TestReBlur.png"
    else :
        pre_process_output_name = f"{config_dico['preproc_line']}{config_dico['filename'].split('.')[0]}{config_dico['rad']}Ring{config_dico['ring']}Bord{config_dico['border']}Sig{int(config_dico['sigma'])}CutOff{config_dico['cut_off']}.png"

    pre_process_command = f"python3 {config_dico['pre_processing_path']} -i {config_dico['filename_rgb_in']} -cfg {config_filename} -o {pre_process_output_name}"
    print(pre_process_command)
    print("______________________________________")

    # ______________ FFmpeg1 ______________
    config_dico['filename_yuv'] = config_dico['preproc_line'] + config_dico['filename'].split('.')[0] + ".yuv"
    ffmpeg_command = f"ffmpeg -i {pre_process_output_name} -r {config_dico['framerate']} -vframes {config_dico['frames_to_convert']} -s {config_dico['width']}x{config_dico['height']} -pix_fmt yuv420p {config_dico['filename_yuv']}"
    print(ffmpeg_command)
    print("______________________________________")

    # ______________ VTM ______________
    # WATCHOUT vtm only takes yuv420p and outputs only yuv420p10le
    vtm_output = f"{config_dico['preproc_line']}vtm_out_qp{config_dico['qp']}.yuv"
    vtm_command = f"{config_dico['vtm_path']}EncoderApp -i {config_dico['filename_yuv']} -q {config_dico['qp']} -wdt {config_dico['width']} -hgt {config_dico['height']} -c {config_dico['vtm_config_file']} -f {config_dico['frames_to_convert']} -fr {config_dico['framerate']} -o {vtm_output} > {config_dico['preproc_line']}vtm_out_qp{config_dico['qp']}.txt"
    print(vtm_command)
    print("______________________________________")

    # ______________ FFmpeg2 ______________
    config_dico['filename_rgb_out'] = config_dico['preproc_line'] + "qp_"+config_dico['qp'] + "_" +config_dico['filename'] #here it's for the output of ffmpeg2  
    ffmpeg_command2 = f"ffmpeg -s {config_dico['width']}x{config_dico['height']} -pix_fmt yuv420p10le -i {vtm_output} -vframes {config_dico['frames_to_convert']} {config_dico['filename_rgb_out']}"
    print(ffmpeg_command2)
    print("______________________________________")

    # ______________ RLC ______________
    if (config_dico['generate_rlc_cfg'] == 'true') :
        RLC_config_name = f"{config_dico['preproc_line']}RLC_config.cfg"
        generate_RLC_config(config_dico, RLC_config_name, inininin)
    else : RLC_config_name = config_dico['RLC_config_file']

    RLC_command = f"{config_dico['RLC_path']} {RLC_config_name}"
    print(RLC_command)
    print("______________________________________")

    # ______________ Execution ______________
    subprocess.run(pre_process_command, shell=True)
    subprocess.run(ffmpeg_command, shell=True)
    subprocess.run(vtm_command, shell=True)
    subprocess.run(ffmpeg_command2, shell=True)
    subprocess.run(RLC_command, shell=True)
    
def rlc_line(config_dico):    #CHOISIR NOM POUR PSNR, ICI C'EST LA REF
    # ______________ RLC ______________
    if (config_dico['generate_rlc_cfg'] == 'true') :
        ref_RLC_config_name = f"{config_dico['ref_rlc_line']}RLC_config.cfg"
        generate_RLC_config(config_dico, ref_RLC_config_name, config_dico['dataset_path'], output=config_dico['RLC_ref_path']+"Res_%03d")
    else : ref_RLC_config_name = config_dico['RLC_config_file']

    RLC_command = f"{config_dico['RLC_path']} {ref_RLC_config_name}"
    print(RLC_command)
    print("______________________________________")

    # ______________ Execution ______________
    subprocess.run(RLC_command, shell=True)

def no_pre_processing_line(config_dico):
    # ______________ FFmpeg1 frames to video ______________
    filename_yuv_in = config_dico['no_preproc_line'] + 'yuv_vid_out.mp4'
    ffmpeg_command1 = (
        f"ffmpeg -framerate {config_dico['framerate']} "
        f"-s {config_dico['width']}x{config_dico['height']} "
        f"-i {config_dico['dataset_path']} "
        f"-c:v libx264 "
        f"-crf 0 "
        f"-pix_fmt yuv420p "
        f"{filename_yuv_in}"
    )
    print(ffmpeg_command1)
    print("______________________________________")
    # at this stage, we have a mp4 video file in yuv420p format

    # ______________ VTM ______________
    # WATCHOUT vtm only takes yuv420p and outputs only yuv420p10le
    vtm_output_yuv = f"{config_dico['no_preproc_line']}compressed_yuv_qp{config_dico['qp']}.mp4"
    vtm_command = (f"{config_dico['vtm_path']}EncoderApp "
                   f"-i {filename_yuv_in} "
                   f"-q {config_dico['qp']} "
                   f"-wdt {config_dico['width']} "
                   f"-hgt {config_dico['height']} "
                   f"-c {config_dico['vtm_config_file']} "
                   f"-f {config_dico['frames_to_convert']} "
                   f"-fr {config_dico['framerate']} "
                   f"-o {vtm_output_yuv} > {config_dico['no_preproc_line']}vtm_out_qp{config_dico['qp']}.txt")
    print(vtm_command)
    print("______________________________________")

    # # ______________ FFmpeg2 ______________
    vtm_output_rgb = config_dico['no_preproc_line'] + "compressed_rgb_qp" + config_dico['qp'] + "/frame%03d.png" #here it's for the output of ffmpeg2  
    os.makedirs(config_dico['no_preproc_line'] + "compressed_rgb_qp" + config_dico['qp'], exist_ok=True)
    ffmpeg_command2 = (
        # f"ffmpeg -i {vtm_output_yuv} "
        f"ffmpeg -i {filename_yuv_in} "
        f"-vf \"scale={config_dico['width']}:{config_dico['height']},format=rgb24\" "
        f"-vframes {config_dico['frames_to_convert']} "
        f"{vtm_output_rgb}"
    )
    print(ffmpeg_command2)
    print("______________________________________")
    # at this stage we have indivual frames in rgb24 format

    # ______________ RLC ______________
    if (config_dico['generate_rlc_cfg'] == 'true') :
        no_preproc_RLC_config_name = f"{config_dico['no_preproc_line']}RLC_config.cfg"
        generate_RLC_config(config_dico, no_preproc_RLC_config_name, vtm_output_rgb, config_dico['RLC_no_preproc_path']+"Res_%03d")
    else : no_preproc_RLC_config_name = config_dico['RLC_config_file']
    
    RLC_command = f"{config_dico['RLC_path']} {no_preproc_RLC_config_name}"
    print(RLC_command)
    print("______________________________________")

    # ______________ Execution ______________
    subprocess.run(ffmpeg_command1, shell=True)
    # subprocess.run(vtm_command, shell=True)
    subprocess.run(ffmpeg_command2, shell=True)
    subprocess.run(RLC_command, shell=True)


if __name__ == '__main__':
    start_time = time.time()
    if len(sys.argv) != 2:
        print("Usage: python Main.py <pipeline_config_file>")
        exit(1)

    config_filename = sys.argv[1]
    config_dico = get_config_dict(config_filename)
    create_output_dirs(config_dico)
    # ______________ Just RLC (ref) ______________
    rlc_line(config_dico)
    
    # __________________Pre processing_____________
    # pre_processing_line(config_dico)

    # ______________ No pre processing ______________
    no_pre_processing_line(config_dico)

    # ______________ PSNR ______________
    # psnr_command_no_preproc = f"python3 {config_dico['psnr_path']} -ref {config_dico['RLC_ref_path']} -i {config_dico['RLC_no_preproc_path']} -o {config_dico['RLC_no_preproc_path']} -cfg {config_filename} -name no_pre_proc"
    # psnr_command_preproc = f"python3 {config_dico['psnr_path']} -ref {config_dico['RLC_ref_path']} -i {config_dico['RLC_preproc_path']} -o {config_dico['RLC_preproc_path']} -cfg {config_filename} -name pre_proc"
    # print(psnr_command_no_preproc)
    # print(psnr_command_preproc)
    # subprocess.run(psnr_command_no_preproc, shell=True)
    # subprocess.run(psnr_command_preproc, shell=True)

    end_time = time.time()
    print(f"Execution time: {end_time - start_time} seconds")
    print(f"Execution time: {(end_time - start_time)/60} minutes")
    