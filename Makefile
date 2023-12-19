racehorses :
	python3 main.py pipeline_config_RaceHorses.cfg

ornito :
	python3 main.py pipeline_config_Ornito.cfg

clean :
	rm -rf dataset/*/output/*
	rm -rf dataset/*/RLC_config.cfg
