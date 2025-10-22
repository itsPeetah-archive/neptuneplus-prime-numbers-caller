

setup:
	@echo "===== Setting up invoked and entrypoint functions... ====="
	kubectl apply -f invoked-functions
	kubectl apply -f entrypoint-functions
	@echo "===== Setup complete. ====="

clear:
	kubectl delete -f invoked-functions --ignore-not-found=true
	kubectl delete -f entrypoint-functions --ignore-not-found=true
	kubectl delete -f dags --ignore-not-found=true

seq-%: setup
	@echo "===== Setting up sequential($*) test... ====="
	kubectl apply -f dags/dag-sequential-$*.yaml
	@echo "===== Done. ====="

unseq:
	kubectl delete -f dags --ignore-not-found=true