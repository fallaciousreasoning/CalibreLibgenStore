version = 0.4.1
zip_file = releases/Libgen Fiction v$(version).zip
zip_contents = *.py LICENSE *.md *.txt

all: zip

zip:
	@ echo "creating new $(zip_file)" && zip "$(zip_file)" $(zip_contents) && echo "created new $(zip_file)"
