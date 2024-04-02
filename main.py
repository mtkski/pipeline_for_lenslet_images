# python3 main.py pipeline_config.cfg 
import sys
import subprocess
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

    # ______________ Execution ______________
    subprocess.run(RLC_command, shell=True)

def pre_processing_line(config_dico):
    # __________ Pre processing __________
    if config_dico['testReBlur'] :
        preproc_out_dir = f"{config_dico['preproc_line']}preprocessed_Rad{config_dico['rad']}Ring{config_dico['ring']}Bord{config_dico['border']}Sig{int(config_dico['sigma'])}CutOff{config_dico['cut_off']}TestReBlur/"

    else :
        preproc_out_dir = f"{config_dico['preproc_line']}preprocessed_Rad{config_dico['rad']}Ring{config_dico['ring']}Bord{config_dico['border']}Sig{int(config_dico['sigma'])}CutOff{config_dico['cut_off']}/"
    
    os.makedirs(preproc_out_dir, exist_ok=True)
    pre_process_output_name = preproc_out_dir + "image_%03d.png"

    for i in range(1, int(config_dico['frames_to_convert'])+1):
        input = config_dico['dataset_path'].replace('%03d', f"{i:03d}")
        output = pre_process_output_name.replace('%03d.png', f"{i:03d}.png")
        pre_process_command = f"python3 {config_dico['pre_processing_path']} -i {input} -cfg {config_filename} -o {output}"
        subprocess.run(pre_process_command, shell=True)

    # ______________ FFmpeg1 : png frames -> yuv420 video ______________    
    uncompressed_yuv_vid = config_dico['preproc_line'] + "uncompressed_yuv_vid.yuv" #here it's for the output of ffmpeg1

    ffmpeg_command1 = (
        f"ffmpeg -framerate {config_dico['framerate']} "
        f"-s {config_dico['width']}x{config_dico['height']} "
        f"-i {pre_process_output_name} "
        f"-c:v rawvideo "
        f"-crf 0 "
        f"-pix_fmt yuv420p "
        f"{uncompressed_yuv_vid}"
    )
    subprocess.run(ffmpeg_command1, shell=True)
    
    for qp in config_dico['qp_list']:
        # ______________ VTM ______________
        # WATCHOUT vtm only takes yuv420p and outputs only yuv420p10le
        vtm_output_yuv = f"{config_dico['preproc_line']}compressed_yuv_qp{qp}.yuv"
        bitstream_file = f"{config_dico['preproc_line']}bitstream_qp{qp}.bin"
        vtm_command = (f"{config_dico['vtm_path']}EncoderApp "
                    f"-i {uncompressed_yuv_vid} "
                    f"-q {qp} "
                    f"-wdt {config_dico['width']} "
                    f"-hgt {config_dico['height']} "
                    f"-c {config_dico['vtm_config_file']} "
                    f"-f {config_dico['frames_to_convert']} "
                    f"-fr {config_dico['framerate']} "
                    f"-o {vtm_output_yuv} "
                    f"-b {bitstream_file} > {config_dico['preproc_line']}vtm_out_qp{qp}.txt"
        )
        subprocess.run(vtm_command, shell=True)
    
        if not config_dico['break_after_vtm'] :
            # ______________ FFmpeg2 : yuv420p10le video -> png frames _____________
            out_dir_name = config_dico['preproc_line'] + "compressed_rgb_qp" + str(qp) + "/"
            os.makedirs(out_dir_name, exist_ok=True)
            vtm_output_rgb = out_dir_name + "frame%03d.png" #here it's for the output of ffmpeg2  
            ffmpeg_command2 = (
                f"ffmpeg -s {config_dico['width']}x{config_dico['height']} "
                f"-pix_fmt yuv420p10le "
                f"-i {vtm_output_yuv} "
                f"-vframes {config_dico['frames_to_convert']} "
                f"-f image2 "
                f"{vtm_output_rgb}"
            )
            subprocess.run(ffmpeg_command2, shell=True)

            # ______________ RLC ______________
            if (config_dico['generate_rlc_cfg'] == 'true') :
                no_preproc_RLC_config_name = f"{config_dico['preproc_line']}RLC_config.cfg"
                os.makedirs(config_dico['RLC_preproc_path']+f"qp{qp}", exist_ok=True)
                generate_RLC_config(config_dico, no_preproc_RLC_config_name, vtm_output_rgb, config_dico['RLC_preproc_path']+f"qp{qp}/Res_%03d")
            else : no_preproc_RLC_config_name = config_dico['RLC_config_file']
            
            RLC_command = f"{config_dico['RLC_path']} {no_preproc_RLC_config_name}"
            subprocess.run(RLC_command, shell=True)


def no_pre_processing_line(config_dico):
    # ______________ FFmpeg1 : png frames -> yuv420 video ______________    
    uncompressed_yuv_vid = config_dico['no_preproc_line'] + "uncompressed_yuv_vid_out.yuv" #here it's for the output of ffmpeg1

    ffmpeg_command1 = (
        f"ffmpeg -framerate {config_dico['framerate']} "
        f"-s {config_dico['width']}x{config_dico['height']} "
        f"-i {config_dico['dataset_path']} "
        f"-c:v rawvideo "
        f"-crf 0 "
        f"-pix_fmt yuv420p "
        f"{uncompressed_yuv_vid}"
    )
    subprocess.run(ffmpeg_command1, shell=True)


    # Loop for every qp in the qp_list
    for qp in config_dico['qp_list']:
        # ______________ VTM ______________
        # WATCHOUT vtm only takes yuv420p and outputs only yuv420p10le
        vtm_output_yuv = f"{config_dico['no_preproc_line']}compressed_yuv_qp{qp}.yuv"
        bitstream_file = f"{config_dico['no_preproc_line']}bitstream_qp{qp}.bin"
        vtm_command = (f"{config_dico['vtm_path']}EncoderApp "
                    f"-i {uncompressed_yuv_vid} "
                    f"-q {qp} "
                    f"-wdt {config_dico['width']} "
                    f"-hgt {config_dico['height']} "
                    f"-c {config_dico['vtm_config_file']} "
                    f"-f {config_dico['frames_to_convert']} "
                    f"-fr {config_dico['framerate']} "
                    f"-o {vtm_output_yuv} "
                    f"-b {bitstream_file} > {config_dico['no_preproc_line']}vtm_out_qp{qp}.txt"
        )
        subprocess.run(vtm_command, shell=True)

        if not config_dico['break_after_vtm'] :
            # ______________ FFmpeg2 : yuv420p10le video -> png frames _____________
            out_dir_name = config_dico['no_preproc_line'] + "compressed_rgb_qp" + str(qp) + "/"
            os.makedirs(out_dir_name, exist_ok=True)
            vtm_output_rgb = out_dir_name + "frame%03d.png"
            ffmpeg_command2 = (
                f"ffmpeg -s {config_dico['width']}x{config_dico['height']} "
                f"-pix_fmt yuv420p10le "
                f"-i {vtm_output_yuv} "
                f"-vframes {config_dico['frames_to_convert']} "
                f"-f image2 "
                f"{vtm_output_rgb}"
            )
            subprocess.run(ffmpeg_command2, shell=True)
            
            # ______________ RLC ______________
            if (config_dico['generate_rlc_cfg'] == 'true') :
                no_preproc_RLC_config_name = f"{config_dico['no_preproc_line']}RLC_config.cfg"
                os.makedirs(config_dico['RLC_no_preproc_path']+f"qp{qp}", exist_ok=True)
                generate_RLC_config(config_dico, no_preproc_RLC_config_name, vtm_output_rgb, config_dico['RLC_no_preproc_path']+f"qp{qp}/Res_%03d")
            else : no_preproc_RLC_config_name = config_dico['RLC_config_file']
            RLC_command = f"{config_dico['RLC_path']} {no_preproc_RLC_config_name}"
            subprocess.run(RLC_command, shell=True)


def calculate_psnr(config_dico):
    for i in range(1, int(config_dico['frames_to_convert'])+1):
        for qp in config_dico['qp_list']:
            psnr_command_no_preproc = f"python3 {config_dico['psnr_path']} -ref {config_dico['RLC_ref_path']}Res_{i:03d}/ -i {config_dico['RLC_no_preproc_path']}qp{qp}/Res_{i:03d}/ -o {config_dico['RLC_no_preproc_path']}qp{qp}/ -cfg {config_filename} -name no_preproc_qp{qp}_{i:03d}"
            psnr_command_preproc =    f"python3 {config_dico['psnr_path']} -ref {config_dico['RLC_ref_path']}Res_{i:03d}/ -i {config_dico['RLC_preproc_path']}qp{qp}/Res_{i:03d}/    -o {config_dico['RLC_preproc_path']}qp{qp}/    -cfg {config_filename} -name preproc_qp{qp}_{i:03d}"
            subprocess.run(psnr_command_no_preproc, shell=True)
            subprocess.run(psnr_command_preproc, shell=True)
        
if __name__ == '__main__':
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
    if not config_dico['break_after_vtm'] :
        calculate_psnr(config_dico)
