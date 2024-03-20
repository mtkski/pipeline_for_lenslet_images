import configparser

def get_config_dict(filename):
    try:
            dico = {}
            config = configparser.ConfigParser()
            config.read(filename)
            
            # __________ Pre processing __________
            dico['sigma'] = float(config['PRE_PROCESSING']['sigma'])
            dico['cut_off'] = int(config['PRE_PROCESSING']['cut_off']) # à check si c'est bien un int
            dico['rad'] = int(config['PRE_PROCESSING']['rad'])
            dico['border'] = int(config['PRE_PROCESSING']['border'])
            dico['testReBlur'] = config['PRE_PROCESSING']['testReBlur'].lower()
            dico['ring'] = int(config['PRE_PROCESSING']['ring'])
            dico['frames_to_convert'] = config['DEFAULT']['frames_to_convert']

            # ______________ DEFAULT ______________
            dico['dataset_path'] = str(config['DEFAULT']['dataset_path'])
            dico['output_path'] = config['DEFAULT']['output_path']

            dico['framerate'] = config['DEFAULT']['framerate']
            dico['width'] = config['DEFAULT']['width']
            dico['height'] = config['DEFAULT']['height']
            # dico['pix_fmt'] = config['DEFAULT']['pix_fmt']

            # ______________ VTM ______________
            dico['vtm_config_file'] = config['VTM']['vtm_config_file']
            dico['qp'] = config['VTM']['qp']
            
            # ______________ APP PATHS ______________
            dico['vtm_path'] = config['APP_PATHS']['vtm_path']
            dico['pre_processing_path'] = config['APP_PATHS']['pre_processing_path']
            dico['RLC_path'] = config['APP_PATHS']['RLC_path']
            dico['psnr_path'] = config['APP_PATHS']['psnr_path']

            # ______________ RLC ______________
            dico['RLC_config_file'] = config['RLC']['RLC_config_file']
            dico['camera_calibration_file'] = config['RLC']['camera_calibration_file']
            dico['generate_rlc_cfg'] = config['RLC']['generate_rlc_cfg'].lower()
            dico['rlc_cfg_template'] = config['RLC']['rlc_cfg_template']
                # Directories for files created while running the script
            dico['no_preproc_line'] = dico['output_path'] + "no_preproc_line/"
            dico['preproc_line'] = dico['output_path'] + "preproc_line/"
            dico['ref_rlc_line'] = dico['output_path'] + "ref_rlc_line/"
                # Output directories for RLC multiview images 
            dico['RLC_ref_path'] = dico['output_path'] + "ref_rlc_multiview/"
            dico['RLC_no_preproc_path'] = dico['output_path'] + "no_preproc_rlc_multiview/"
            dico['RLC_preproc_path'] = dico['output_path'] + "preproc_rlc_multiview/"

            return dico
    except FileNotFoundError:
        print(f"File '{filename}' not found.")
    except:
        print("An error occurred while opening the file. No config 4 u")