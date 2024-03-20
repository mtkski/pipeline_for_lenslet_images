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

def rlc_line(config_dico):
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

def pre_processing_line(config_dico):
    # __________ Pre processing __________
    preproc_out_dir = config_dico['preproc_line']+"preprocessed/"
    os.makedirs(preproc_out_dir, exist_ok=True)

    if config_dico['testReBlur'] :
        pre_process_output_name = f"{preproc_out_dir}Rad{config_dico['rad']}Ring{config_dico['ring']}Bord{config_dico['border']}Sig{int(config_dico['sigma'])}CutOff{config_dico['cut_off']}TestReBlur_%03d.png"
    else :
        pre_process_output_name = f"{preproc_out_dir}Rad{config_dico['rad']}Ring{config_dico['ring']}Bord{config_dico['border']}Sig{int(config_dico['sigma'])}CutOff{config_dico['cut_off']}_%03d.png"

    print("______________________________________")
    print(f"Pre processing output name: {pre_process_output_name}")
    print("______________________________________")

    for i in range(1, int(config_dico['frames_to_convert'])+1):
        input = config_dico['dataset_path'].replace('%03d', f"{i:03d}")
        output = pre_process_output_name.replace('%03d.png', f"{i:03d}.png")
        print(input)
        pre_process_command = f"python3 {config_dico['pre_processing_path']} -i {input} -cfg {config_filename} -o {output}"
        subprocess.run(pre_process_command, shell=True)

    # ______________ FFmpeg1 frames to video ______________
    uncompressed_yuv_dir_name = config_dico['preproc_line'] + "uncompressed_rgb/"
    os.makedirs(uncompressed_yuv_dir_name, exist_ok=True)
    
    filename_mp4_uncompressed = uncompressed_yuv_dir_name + 'mp4_vid_out.mp4'
    ffmpeg_command0 = (
        f"ffmpeg -framerate {config_dico['framerate']} "
        f"-s {config_dico['width']}x{config_dico['height']} "
        f"-i {pre_process_output_name} "
        f"-c:v libx264 "
        f"-crf 0 "
        f"-pix_fmt yuv420p "
        f"{filename_mp4_uncompressed}"
    )

    uncompressed_yuv_vid = uncompressed_yuv_dir_name + "yuv_vid_out.yuv" #here it's for the output of ffmpeg2  
    ffmpeg_command1 = (
    f"ffmpeg -i {filename_mp4_uncompressed} "
    # f"ffmpeg -i {filename_yuv_in} "
    # f"-vf \"scale={config_dico['width']}:{config_dico['height']}\" "
    f"-vframes {config_dico['frames_to_convert']} "
    f"{uncompressed_yuv_vid}"
    )
    
    # ______________ VTM ______________
    # WATCHOUT vtm only takes yuv420p and outputs only yuv420p10le
    vtm_output_yuv = f"{config_dico['preproc_line']}compressed_yuv_qp{config_dico['qp']}.yuv"
    vtm_command = (f"{config_dico['vtm_path']}EncoderApp "
                   f"-i {uncompressed_yuv_vid} "
                   f"-q {config_dico['qp']} "
                   f"-wdt {config_dico['width']} "
                   f"-hgt {config_dico['height']} "
                   f"-c {config_dico['vtm_config_file']} "
                   f"-f {config_dico['frames_to_convert']} "
                   f"-fr {config_dico['framerate']} "
                   f"-o {vtm_output_yuv} > {config_dico['preproc_line']}vtm_out_qp{config_dico['qp']}.txt")

    # # ______________ FFmpeg2 _____________
    out_dir_name = config_dico['preproc_line'] + "compressed_rgb_qp" + config_dico['qp'] + "/"
    os.makedirs(out_dir_name, exist_ok=True)
    vtm_output_rgb = out_dir_name + "frame%03d.png" #here it's for the output of ffmpeg2  
    ffmpeg_command2 = (
        f"ffmpeg -s {config_dico['width']}x{config_dico['height']} "
        f"-pix_fmt yuv420p10le "
        f"-i {vtm_output_yuv} "
        # f"-vf \"scale={config_dico['width']}:{config_dico['height']},format=yuv420p10le\" "
        f"-vframes {config_dico['frames_to_convert']} "
        f"-f image2 "
        f"{vtm_output_rgb}"
    )

    # ______________ RLC ______________
    if (config_dico['generate_rlc_cfg'] == 'true') :
        no_preproc_RLC_config_name = f"{config_dico['preproc_line']}RLC_config.cfg"
        os.makedirs(config_dico['RLC_preproc_path']+f"qp{config_dico['qp']}", exist_ok=True)
        generate_RLC_config(config_dico, no_preproc_RLC_config_name, vtm_output_rgb, config_dico['RLC_preproc_path']+f"qp{config_dico['qp']}/Res_%03d")
    else : no_preproc_RLC_config_name = config_dico['RLC_config_file']
    
    RLC_command = f"{config_dico['RLC_path']} {no_preproc_RLC_config_name}"

    # print("_____________Preprocessing line :_______________")
    # print(pre_process_command)
    # print("______________________________________")
    # print(ffmpeg_command0)
    # print("______________________________________")
    # print(ffmpeg_command1)
    # print("______________________________________")
    # print(vtm_command)
    # print("______________________________________")
    # print(ffmpeg_command2)
    # print("______________________________________")
    # print(RLC_command)
    # print("______________________________________")

    # ______________ Execution ______________
    # WATCHOUT preprocessing is done above inside a for loop
    subprocess.run(ffmpeg_command0, shell=True)
    subprocess.run(ffmpeg_command1, shell=True)
    subprocess.run(vtm_command, shell=True)
    subprocess.run(ffmpeg_command2, shell=True)
    subprocess.run(RLC_command, shell=True)

def no_pre_processing_line(config_dico):
    # ______________ FFmpeg1 frames to video ______________
    uncompressed_yuv_dir_name = config_dico['no_preproc_line'] + "uncompressed_rgb/"
    os.makedirs(uncompressed_yuv_dir_name, exist_ok=True)
    
    filename_mp4_uncompressed = uncompressed_yuv_dir_name + 'mp4_vid_out.mp4'
    ffmpeg_command0 = (
        f"ffmpeg -framerate {config_dico['framerate']} "
        f"-s {config_dico['width']}x{config_dico['height']} "
        f"-i {config_dico['dataset_path']} "
        f"-c:v libx264 "
        f"-crf 0 "
        f"-pix_fmt yuv420p "
        f"{filename_mp4_uncompressed}"
    )

    uncompressed_yuv_vid = uncompressed_yuv_dir_name + "yuv_vid_out.yuv" #here it's for the output of ffmpeg2  
    ffmpeg_command1 = (
    f"ffmpeg -i {filename_mp4_uncompressed} "
    # f"ffmpeg -i {filename_yuv_in} "
    # f"-vf \"scale={config_dico['width']}:{config_dico['height']}\" "
    f"-vframes {config_dico['frames_to_convert']} "
    f"{uncompressed_yuv_vid}"
    )

    # ______________ VTM ______________
    # WATCHOUT vtm only takes yuv420p and outputs only yuv420p10le
    vtm_output_yuv = f"{config_dico['no_preproc_line']}compressed_yuv_qp{config_dico['qp']}.yuv"
    vtm_command = (f"{config_dico['vtm_path']}EncoderApp "
                   f"-i {uncompressed_yuv_vid} "
                   f"-q {config_dico['qp']} "
                   f"-wdt {config_dico['width']} "
                   f"-hgt {config_dico['height']} "
                   f"-c {config_dico['vtm_config_file']} "
                   f"-f {config_dico['frames_to_convert']} "
                   f"-fr {config_dico['framerate']} "
                   f"-o {vtm_output_yuv} > {config_dico['no_preproc_line']}vtm_out_qp{config_dico['qp']}.txt")

    # # ______________ FFmpeg2 _____________
    out_dir_name = config_dico['no_preproc_line'] + "compressed_rgb_qp" + config_dico['qp'] + "/"
    os.makedirs(out_dir_name, exist_ok=True)
    vtm_output_rgb = out_dir_name + "frame%03d.png" #here it's for the output of ffmpeg2  
    ffmpeg_command2 = (
        f"ffmpeg -s {config_dico['width']}x{config_dico['height']} "
        f"-pix_fmt yuv420p10le "
        f"-i {vtm_output_yuv} "
        # f"-vf \"scale={config_dico['width']}:{config_dico['height']},format=yuv420p10le\" "
        f"-vframes {config_dico['frames_to_convert']} "
        f"-f image2 "
        f"{vtm_output_rgb}"
    )

    # ______________ RLC ______________
    if (config_dico['generate_rlc_cfg'] == 'true') :
        no_preproc_RLC_config_name = f"{config_dico['no_preproc_line']}RLC_config.cfg"
        os.makedirs(config_dico['RLC_no_preproc_path']+f"qp{config_dico['qp']}", exist_ok=True)
        generate_RLC_config(config_dico, no_preproc_RLC_config_name, vtm_output_rgb, config_dico['RLC_no_preproc_path']+f"qp{config_dico['qp']}/Res_%03d")
    else : no_preproc_RLC_config_name = config_dico['RLC_config_file']
    
    RLC_command = f"{config_dico['RLC_path']} {no_preproc_RLC_config_name}"

    # print("_____________No preprocessing line :_______________")
    # print(ffmpeg_command0)
    # print("______________________________________")
    # print(ffmpeg_command1)
    # print("______________________________________")
    # print(vtm_command)
    # print("______________________________________")
    # print(ffmpeg_command2)
    # print("______________________________________")
    # print(RLC_command)
    # print("______________________________________")

    # ______________ Execution ______________
    subprocess.run(ffmpeg_command0, shell=True)
    subprocess.run(ffmpeg_command1, shell=True)
    subprocess.run(vtm_command, shell=True)
    subprocess.run(ffmpeg_command2, shell=True)
    subprocess.run(RLC_command, shell=True)

def calculate_psnr(config_dico):
    for i in range(1, int(config_dico['frames_to_convert'])+1):
        qp = int(config_dico['qp'])
        psnr_command_no_preproc = f"python3 {config_dico['psnr_path']} -ref {config_dico['RLC_ref_path']}Res_{i:03d}/ -i {config_dico['RLC_no_preproc_path']}qp{qp}/Res_{i:03d}/ -o {config_dico['RLC_no_preproc_path']}qp{qp}/ -cfg {config_filename} -name no_preproc_qp{qp}_{i:03d}"
        psnr_command_preproc =    f"python3 {config_dico['psnr_path']} -ref {config_dico['RLC_ref_path']}Res_{i:03d}/ -i {config_dico['RLC_preproc_path']}qp{qp}/Res_{i:03d}/    -o {config_dico['RLC_preproc_path']}qp{qp}/    -cfg {config_filename} -name preproc_qp{qp}_{i:03d}"
        # print(psnr_command_no_preproc)
        # print(psnr_command_preproc)
        subprocess.run(psnr_command_no_preproc, shell=True)
        subprocess.run(psnr_command_preproc, shell=True)
        
if __name__ == '__main__':
    start_time = time.time()
    if len(sys.argv) != 2:
        print("Usage: python Main.py <pipeline_config_file>")
        exit(1)

    config_filename = sys.argv[1]
    config_dico = get_config_dict(config_filename)
    create_output_dirs(config_dico)

    # ______________ Running the lines ______________
    rlc_line(config_dico)
    pre_processing_line(config_dico)
    no_pre_processing_line(config_dico)

    # ______________ PSNR ______________
    calculate_psnr(config_dico)

    end_time = time.time()
    print(f"Execution time: {end_time - start_time} seconds")
    print(f"Execution time: {(end_time - start_time)/60} minutes")
    