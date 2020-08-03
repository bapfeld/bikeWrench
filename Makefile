.PHONY: css

css: bootstrap theme_css

bootstrap:
	curl -L https://github.com/twbs/bootstrap/releases/download/v4.5.0/bootstrap-4.5.0-dist.zip -o /tmp/bootstrap_files.zip
	unzip /tmp/bootstrap_files.zip -d /tmp/bootstrap_files
	cp -r /tmp/bootstrap_files/bootstrap-4.5.0-dist bikeGarage/static

theme_css:
	mkdir bikeGarage/static/scss
	curl https://bootswatch.com/4/superhero/bootstrap.min.css -o bikeGarage/static/css/bootstrap.min.css
	curl https://bootswatch.com/4/superhero/bootstrap.css -o bikeGarage/static/css/bootstrap.css
	curl https://bootswatch.com/4/superhero/_variables.scss -o bikeGarage/static/scss/_variables.scss
	curl https://bootswatch.com/4/superhero/_bootswatch.scss -o bikeGarage/static/scss/_bootswatch.scss
