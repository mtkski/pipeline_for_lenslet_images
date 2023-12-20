ornito :
	python3 main.py cfg_files/pipeline_config_Ornito.cfg

origami:
	python3 main.py dataset/Origami/pipeline_config_Origami.cfg

clean :
	rm -rf dataset/*/output/*/*
	rm -rf dataset/*/ref_RLC_config.cfg
	rm -rf dataset/*/preproc_RLC_config.cfg
	rm -rf dataset/*/no_preproc_RLC_config.cfg
	rm -rf dataset/*/rlc_preproc/*
	rm -rf dataset/*/rlc_ref/*
	rm -rf dataset/*/rlc_no_preproc/*
	rm -rf *.png
	rm -rf str.bin
