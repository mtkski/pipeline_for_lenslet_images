# python3 main.py pipeline_config.cfg 
import sys
import subprocess
import time 
from config_maker import get_config_dict

def generate_RLC_config(template_file, output_file, dico):
    try:
        with open(template_file, 'r') as file:
            filedata = file.read()

        filedata = filedata.replace('_CALIBRATIONFILE', dico['camera_calibration_file'])
        filedata = filedata.replace('_INPUTPATH', dico['filename_rgb_out'])
        filedata = filedata.replace('_OUTPUTPATH', dico['RLC_processed_path']+"qp"+dico['qp'])
        filedata = filedata.replace('_WIDTH', dico['width'])
        filedata = filedata.replace('_HEIGHT', dico['height'])
        # TODO: Add start frame and end frame replacements

        with open(output_file, 'w') as file:   
            file.write(filedata)

    except FileNotFoundError:
        print(f"File '{template_file}' not found.")
    except:
        print("An error occurred while opening or writing to the file.")

def pre_processing_line(config_dico):
    # __________ Pre processing __________
    if config_dico['testReBlur'] :
        pre_process_output_name = f"{config_dico['output_path']}{config_dico['filename_no_ext']}{config_dico['rad']}Ring{config_dico['ring']}Bord{config_dico['border']}Sig{int(config_dico['sigma'])}CutOff{config_dico['cut_off']}_TestReBlur.png"
    else :
        pre_process_output_name = f"{config_dico['output_path']}{config_dico['filename_no_ext']}{config_dico['rad']}Ring{config_dico['ring']}Bord{config_dico['border']}Sig{int(config_dico['sigma'])}CutOff{config_dico['cut_off']}.png"

    pre_process_command = f"python3 {config_dico['pre_processing_path']} -i {config_dico['file_name_rgb_in']} -cfg {config_filename} -o {pre_process_output_name}"
    print(pre_process_command)
    print("______________________________________")

    # ______________ FFmpeg1 ______________
    ffmpeg_command = f"ffmpeg -i {pre_process_output_name} -r {config_dico['framerate']} -vframes {config_dico['frames_to_convert']} -s {config_dico['width']}x{config_dico['height']} -pix_fmt yuv420p {config_dico['filename_yuv']}"
    print(ffmpeg_command)
    print("______________________________________")

    # ______________ VTM ______________
    # WATCHOUT vtm only takes yuv420p and outputs only yuv420p10le
    vtm_output = f"{config_dico['output_path']}vtm_out_qp{config_dico['qp']}.yuv"
    vtm_command = f"{config_dico['vtm_path']}EncoderApp -i {config_dico['filename_yuv']} -q {config_dico['qp']} -wdt {config_dico['width']} -hgt {config_dico['height']} -c {config_dico['vtm_config_file']} -f {config_dico['frames_to_convert']} -fr {config_dico['framerate']} -o {vtm_output}"
    print(vtm_command)
    print("______________________________________")

    # ______________ FFmpeg2 ______________
    ffmpeg_command2 = f"ffmpeg -s {config_dico['width']}x{config_dico['height']} -pix_fmt yuv420p10le -i {vtm_output} -vframes {config_dico['frames_to_convert']} {config_dico['filename_rgb_out']}"
    print(ffmpeg_command2)
    print("______________________________________")

    # ______________ RLC ______________
    if (config_dico['generate_rlc_cfg'] == 'true') :
        RLC_config = f"{config_dico['dataset_path']}RLC_config.cfg"
        generate_RLC_config(config_dico['rlc_cfg_template'], RLC_config, config_dico)
    else : RLC_config = config_dico['RLC_config_file']

    RLC_command = f"{config_dico['RLC_path']} {RLC_config}"
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
        RLC_config = f"{config_dico['dataset_path']}RLC_config.cfg"
        generate_RLC_config(config_dico['rlc_cfg_template'], RLC_config, config_dico)
    else : RLC_config = config_dico['RLC_config_file']

    RLC_command = f"{config_dico['RLC_path']} {RLC_config}"
    print(RLC_command)
    print("______________________________________")

    # ______________ Execution ______________
    subprocess.run(RLC_command, shell=True)

def no_pre_processing_line(config_dico):
    # ______________ FFmpeg1 ______________
    ffmpeg_command = f"ffmpeg -i {config_dico['file_name_rgb_in']} -r {config_dico['framerate']} -vframes {config_dico['frames_to_convert']} -s {config_dico['width']}x{config_dico['height']} -pix_fmt yuv420p {config_dico['filename_yuv']}"
    print(ffmpeg_command)
    print("______________________________________")

    # ______________ VTM ______________
    # WATCHOUT vtm only takes yuv420p and outputs only yuv420p10le
    vtm_command = f"{config_dico['vtm_path']}EncoderApp -i {config_dico['filename_yuv']} -wdt {config_dico['width']} -hgt {config_dico['height']} -c {config_dico['vtm_config_file']} -f {config_dico['frames_to_convert']} -fr {config_dico['framerate']} -o {config_dico['output_path']}vtm_out.yuv"
    print(vtm_command)
    print("______________________________________")

    # ______________ FFmpeg2 ______________
    ffmpeg_command2 = f"ffmpeg -s {config_dico['width']}x{config_dico['height']} -pix_fmt yuv420p10le -i {config_dico['output_path']}vtm_out.yuv -vframes {config_dico['frames_to_convert']} {config_dico['filename_rgb_out']}"
    print(ffmpeg_command2)
    print("______________________________________")

    # ______________ RLC ______________
    if (config_dico['generate_rlc_cfg'] == 'true') :
        RLC_config = f"{config_dico['dataset_path']}RLC_config.cfg"
        generate_RLC_config(config_dico['rlc_cfg_template'], RLC_config, config_dico)
    else : RLC_config = config_dico['RLC_config_file']

    RLC_command = f"{config_dico['RLC_path']} {RLC_config}"
    print(RLC_command)
    print("______________________________________")

    # ______________ Execution ______________
    subprocess.run(ffmpeg_command, shell=True)
    subprocess.run(vtm_command, shell=True)
    subprocess.run(ffmpeg_command2, shell=True)
    subprocess.run(RLC_command,shell=True)
                   

if __name__ == '__main__':
    start_time = time.time()
    if len(sys.argv) != 2:
        print("Usage: python Main.py <pipeline_config_file>")
        exit(1)

    config_filename = sys.argv[1]
    config_dico = get_config_dict(config_filename)

    # __________________Pre processing_____________
    pre_processing_line(config_dico)

    # ______________ Just RLC (ref) ______________
    # rlc_line(config_dico)

    # ______________ No pre processing ______________
    # no_pre_processing_line(config_dico)

    # ______________ PSNR ______________
    #python3 psnr_recon.py -r ./origami_ref.png -i ./origami.png -o ./origamipsnr.txt
    # between the ref dir created with rlc and the output dir created with the top line and the bottom line
    # RLC_files = config_dico['output_path']+"RLC_result"
    # psnr_command = f"python3 {config_dico['psnr_path']} -r {config_dico['file_name_rgb_in']} -i {RLC_files} -o {config_dico['output_path']}psnr.txt"
    # print(psnr_command)

    end_time = time.time()
    print(f"Execution time: {end_time - start_time} seconds")
    print(f"Execution time: {(end_time - start_time)/60} minutes")
