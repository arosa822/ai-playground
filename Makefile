.PHONY: start stop restart

start:
	@echo "Starting services..."
	@python model_service.py & echo $$! > model_service.pid
	@python app.py & echo $$! > app.pid

stop:
	@echo "Stopping services..."
	@-kill `cat model_service.pid` || true
	@-kill `cat app.pid` || true
	@rm -f model_service.pid app.pid

restart: stop start
