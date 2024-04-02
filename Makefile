ornito :
	python3 main.py dataset/Ornito/pipeline_config_Ornito.cfg

origami:
	python3 main.py dataset/Origami/pipeline_config_Origami.cfg

clean : clean_ornito clean_origami

clean_ornito :
	# rm -rf dataset/Ornito/output
	rm -rf dataset/Ornito/output/no_preproc_line
	rm -rf *.png
	rm -rf str.bin
	rm -rf Previous_patchmap000.png
	rm -rf Previous_patchmap001.png
	rm -rf Previous_patchmap002.png

clean_origami :
	# rm -rf dataset/Origami/output
	rm -rf dataset/Origami/output/no_preproc_line
	rm -rf *.png
	rm -rf str.bin
	rm -rf Previous_patchmap000.png
	rm -rf Previous_patchmap001.png
	rm -rf Previous_patchmap002.png