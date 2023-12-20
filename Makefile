ornito :
	python3 main.py dataset/Ornito/pipeline_config_Ornito.cfg

origami:
	python3 main.py dataset/Origami/pipeline_config_Origami.cfg

clean :
	rm -rf dataset/*/output/*/*
	rm -rf dataset/*/output/no_preproc_RLC_config.cfg
	rm -rf dataset/*/output/preproc_RLC_config.cfg
	rm -rf dataset/*/output/ref_RLC_config.cfg

	rm -rf dataset/*/rlc_preproc/*
	rm -rf dataset/*/rlc_ref/*
	rm -rf dataset/*/rlc_no_preproc/*
	rm -rf *.png
	rm -rf str.bin
