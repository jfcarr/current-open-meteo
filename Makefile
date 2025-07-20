default:
	@echo 'Targets:'
	@echo '  run      Example is for West Alexandria, Ohio'
	@echo '  deploy   Copy to users person bin directory'

run:
	@uv run current-weather-om.py --latitude 39.6142 --longitude -84.5560 --timezone "America/New_York"

deploy:
	cp current-weather-om.py ~/bin/current-weather-om
