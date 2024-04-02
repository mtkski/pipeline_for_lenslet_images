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

    os.makedirs(config_dico['ref_rlc_multiview'], exist_ok=True)
    os.makedirs(config_dico['no_preproc_rlc_multiview'], exist_ok=True)
    os.makedirs(config_dico['preproc_rlc_multiview'], exist_ok=True)


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

def rlc_ref_line(config_dico):
    run_RLC(config_dico, config_dico['ref_rlc_line'], config_dico['dataset_path'], config_dico['ref_rlc_multiview'])

def general_line(config_dico, line_dir, multiview_out_dir, preprocessing = None, postprocessing = None):
    if preprocessing != None:
        # __________ Pre processing __________
        if config_dico['testReBlur'] :
            preproc_out_dir = f"{line_dir}preprocessed_Rad{config_dico['rad']}Ring{config_dico['ring']}Bord{config_dico['border']}Sig{int(config_dico['sigma'])}CutOff{config_dico['cut_off']}TestReBlur/"
        else :
            preproc_out_dir = f"{line_dir}preprocessed_Rad{config_dico['rad']}Ring{config_dico['ring']}Bord{config_dico['border']}Sig{int(config_dico['sigma'])}CutOff{config_dico['cut_off']}/"
        
        os.makedirs(preproc_out_dir, exist_ok=True)
        ffmpeg1_input_dir = preproc_out_dir + "image_%03d.png"

        for i in range(1, int(config_dico['frames_to_convert'])+1):
            input = config_dico['dataset_path'].replace('%03d', f"{i:03d}")
            output = ffmpeg1_input_dir.replace('%03d.png', f"{i:03d}.png")
            pre_process_command = f"python3 {config_dico['pre_processing_path']} -i {input} -cfg {config_filename} -o {output}"
            subprocess.run(pre_process_command, shell=True)
    else:
        ffmpeg1_input_dir = config_dico['dataset_path']
    
    # ______________ FFmpeg1 : png frames -> yuv420 video ______________    
    uncompressed_yuv_vid = line_dir + "uncompressed_yuv_vid.yuv" #here it's for the output of ffmpeg1

    ffmpeg_command1 = (
        f"ffmpeg -framerate {config_dico['framerate']} "
        f"-s {config_dico['width']}x{config_dico['height']} "
        # f"-i {pre_process_output_name} "
        f"-i {ffmpeg1_input_dir} "
        f"-c:v rawvideo "
        f"-crf 0 "
        f"-pix_fmt yuv420p "
        f"{uncompressed_yuv_vid}"
    )
    subprocess.run(ffmpeg_command1, shell=True)
    
    for qp in config_dico['qp_list']:
        # ______________ VTM ______________
        # WATCHOUT vtm only takes yuv420p and outputs only yuv420p10le
        vtm_output_yuv = f"{line_dir}compressed_yuv_qp{qp}.yuv"
        bitstream_file = f"{line_dir}bitstream_qp{qp}.bin"
        vtm_command = (f"{config_dico['vtm_path']}EncoderApp "
                    f"-i {uncompressed_yuv_vid} "
                    f"-q {qp} "
                    f"-wdt {config_dico['width']} "
                    f"-hgt {config_dico['height']} "
                    f"-c {config_dico['vtm_config_file']} "
                    f"-f {config_dico['frames_to_convert']} "
                    f"-fr {config_dico['framerate']} "
                    f"-o {vtm_output_yuv} "
                    f"-b {bitstream_file} > {line_dir}vtm_out_qp{qp}.txt"
        )
        subprocess.run(vtm_command, shell=True)
    
        if config_dico['break_after_vtm'] != True :
            # ______________ FFmpeg2 : yuv420p10le video -> png frames _____________
            out_dir_name = line_dir + "compressed_rgb_qp" + str(qp) + "/"
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

            if postprocessing != None:
                # vtm_output_rgb est nommé comme il faut pour rentrer dans RLC
                print("Post processing")
                os.makedirs(config_dico['postproc_line'], exist_ok=True)
                os.makedirs(config_dico['postproc_rlc_multiview'], exist_ok=True)

                rlc_input = config_dico['postproc_line'] + "post/" + "frame%03d.png"
                # __________ Post processing __________
                post_process_command = f"python3 {config_dico['post_processing_path']} -i {vtm_output_rgb} -cfg {config_filename} -o {rlc_input}"
                subprocess.run(post_process_command, shell=True)
                rlc_input = vtm_output_rgb
                print("Post processing done")

            else : rlc_input = vtm_output_rgb
            
            rlc_out_dir_qp = multiview_out_dir+f"qp{qp}"
            os.makedirs(rlc_out_dir_qp, exist_ok=True)
            run_RLC(config_dico, line_dir, rlc_input, rlc_out_dir_qp+"/")

def pre_proc_line(config_dico):
    general_line(config_dico, config_dico['preproc_line'], config_dico['preproc_rlc_multiview'], preprocessing=config_dico['pre_processing_path'])

def no_pre_proc_line(config_dico):
    general_line(config_dico, config_dico['no_preproc_line'], config_dico['no_preproc_rlc_multiview'])

def post_proc_line(config_dico):
    general_line(config_dico, config_dico['postproc_line'], config_dico['postproc_rlc_multiview'], preprocessing = None, postprocessing = config_dico['post_processing_path'])

def run_RLC(config_dico, line_dir, input_dir, out_dir):
    RLC_configfile = f"{line_dir}RLC_config.cfg"
    os.makedirs(out_dir, exist_ok=True)
    generate_RLC_config(config_dico, RLC_configfile, input_dir, out_dir+"Res_%03d")
    
    RLC_command = f"{config_dico['RLC_path']} {RLC_configfile}"
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
    rlc_ref_line(config_dico)

    no_pre_proc_line(config_dico)

    pre_proc_line(config_dico)

    post_proc_line(config_dico) # pour l'instant ne fais rien du tout (run un script bidon post.py et run RLC comme les autres lignes)

    # ______________ PSNR ______________
    if not config_dico['break_after_vtm'] :
        calculate_psnr(config_dico)
