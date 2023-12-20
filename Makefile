ornito :
	python3 main.py cfg_files/pipeline_config_Ornito.cfg

clean :
	rm -rf dataset/*/output/*
	rm -rf dataset/*/RLC_config.cfg
	rm -rf dataset/*/ref_RLC_config.cfg
	rm -rf dataset/*/rlc_preprocessed
	rm -rf dataset/*/rlc_ref
	rm -rf *.png
	rm -rf str.bin
